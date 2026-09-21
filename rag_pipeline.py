import re
import torch
import numpy as np
import openai_survice
import text_chunks
from text_embedding import get_embedding_tensor
import text_embedding

# rag_pipeline.py 내부의 search_vectordb 함수 수정
def search_vectordb(collection, query: str, top_k: int = 3) -> list[dict]:
    import text_embedding
    
    # get_embedding_tensor는 이미 [[...]] 형태의 2차원 리스트를 반환합니다.
    q_emb = text_embedding.get_embedding_tensor([query])
    
    # [오류 교정]: [q_emb]로 감싸지 않고 q_emb를 그대로 대입하여 2차원 규격을 유지합니다.
    res = collection.query(
        query_embeddings=q_emb,  # <-- 대괄호 제거 완료
        n_results=top_k
    )
    
    if not res or not res["ids"] or not res["ids"][0]:
        return []
        
    search_results = []
    # ChromaDB 결과가 2차원 리스트 형식이므로 [0] 인덱스로 접근하여 언패킹합니다.
    for i, t, m, d in zip(res["ids"][0], res["documents"][0], res["metadatas"][0], res["distances"][0]):
        search_results.append({
            "id": i,
            "text": t,
            "metadata": m,
            "similarity": 1.0 - d
        })
    return search_results

def get_strategy_matrices(strategies: dict, model: str = "nvidia/nemotron-3-embed-1b") -> dict:
    """
    각 전략별 청크 리스트를 받아 메모리 내 연산이 가능한 임베딩 행렬(Tensor)로 미리 변환합니다.
    (실행 시 한 번만 캐싱하여 재사용하는 용도)
    """
    strategy_vecs = {}
    print("--- 두 전략의 메모리 내 행렬 연산용 벡터 캐싱 시작 ---")
    
    for name, chunks in strategies.items():
        if not chunks:
            print(f"[{name}] 청크 데이터가 비어 있어 행렬 생성을 건너뜁니다.")
            continue
            
        # 앞서 구현한 배치 처리형 get_embedding_tensor 활용
        # ChromaDB 호환을 위해 최종 변환 전, 이 함수 내에서 직접 PyTorch Tensor로 다룹니다.
        embeddings = get_embedding_tensor(chunks, model=model)
        
        # 행렬 연산(@) 및 Cosine Similarity 계산을 위해 Unit Vector(정규화) 형태로 변환하여 저장
        tensor_vecs = torch.tensor(embeddings, dtype=torch.float32)
        norm = tensor_vecs.norm(p=2, dim=1, keepdim=True)
        # 0 나누기 방지 처리 포함하여 정규화
        strategy_vecs[name] = tensor_vecs / torch.where(norm == 0, torch.ones_like(norm), norm)
        print(f"   > 전략 [{name}]: 행렬 크기 {strategy_vecs[name].shape} 캐싱 완료")
        
    return strategy_vecs

def compare_chunking(query: str, strategies: dict, strategy_vecs: dict, top_k: int = 3, model: str = "nvidia/nemotron-3-embed-1b") -> None:
    """
    ChromaDB를 거치지 않고, 메모리 내 정규화 행렬 연산(@)으로 
    두 전략의 코사인 유사도를 직접 비교 출력합니다.
    """
    print(f"\n" + "=" * 60)
    print(f"📊 [전략 비교 벤치마크] 질문: {query}")
    print("=" * 60)
    
    # 1. 질문 임베딩 생성 및 정규화
    q_emb = get_embedding_tensor([query], model=model)
    q_tensor = torch.tensor(q_emb, dtype=torch.float32).squeeze(0) # 1D 벡터로 변환
    q_norm = q_tensor.norm(p=2)
    q_unit = q_tensor / (q_norm if q_norm > 0 else 1.0)
    
    # 2. 각 전략별 유사도 연산 및 시각화
    for name, chunks in strategies.items():
        if name not in strategy_vecs:
            continue
            
        matrix = strategy_vecs[name] # 이미 정규화된 청크 행렬 [청크개수, 차원]
        
        # 행렬 곱(@) 연산 수행 -> 각 청크별 코사인 유사도 1D 텐서 반환
        scores_tensor = matrix @ q_unit
        scores = scores_tensor.cpu().numpy()
        
        print(f"\n##### 전략: {name} (총 {len(chunks)}개 청크)")
        print("-" * 50)
        
        # 높은 유사도 순으로 정렬 인덱스 추출
        top_indices = np.argsort(scores)[::-1][:top_k]
        
        for rank, idx in enumerate(top_indices, 1):
            chunk_text_data = chunks[idx]
            score = scores[idx]
            
            # 이전에 통합 완료한 noise_tags 진단 함수 연동
            noise_list = text_chunks.noise_tags(chunk_text_data)
            noise_status = ", ".join(noise_list) if noise_list else "없음(정상 문장 종결)"
            
            # 텍스트 가독성을 위해 줄바꿈 및 연속 공백 정제
            cleaned_chunk = re.sub(r"\s+", " ", chunk_text_data).strip()
            preview = cleaned_chunk[:100] + ("..." if len(cleaned_chunk) > 100 else "")
            
            print(f"[{rank}위] 유사도: {score:.4f}  |  ❌ 노이즈: {noise_status}")
            print(f"      {preview}")

def generate_rag_answer(collection, query: str, top_k: int = 3, model: str = "gpt-4o") -> str:
    """
    Vector DB에서 최고 유사도 청크들을 검색하여 컨텍스트로 삼고,
    OpenAI Chat Completion API를 통해 최종 답변을 생성합니다.
    """
    # 1. 앞서 정의한 Vector DB 함수를 호출하여 상위 문서(Context) 추출
    search_results = search_vectordb(collection, query, top_k=top_k)
    
    if not search_results:
        return "죄송합니다. 관련 문서를 데이터베이스에서 찾을 수 없어 답변을 생성할 수 없습니다."
        
    # 2. 검색된 청크들을 하나의 참조용 컨텍스트 텍스트 블록으로 결합
    context_blocks = []
    for rank, res in enumerate(search_results, 1):
        source = res["metadata"].get("source_title", "알 수 없는 섹션")
        context_blocks.append(f"[참조 {rank} | 출처: {source}]\n{res['text']}")
        
    context_str = "\n\n".join(context_blocks)
    
    # 3. LLM의 왜곡(Hallucination)을 방지하고 컨텍스트에 기반하도록 엄격한 지시문 구성
    system_prompt = (
        "당신은 영문 기술 문서 및 가이드라인(Vectric Lua Script/Gadget) 전문 AI 어시스턴트입니다.\n"
        "반드시 아래 제공된 [참조 컨텍스트]의 정보만을 바탕으로 사용자의 질문에 친절하고 정확하게 답변하세요.\n"
        "만약 질문에 대한 답을 주어진 컨텍스트에서 유추할 수 없거나 관련이 없다면, "
        "'제공된 문서 내에서 해당 내용을 찾을 수 없습니다'라고 답변하고 거짓 정보를 지어내지 마세요.\n"
        "답변은 한국어로 명확하게 작성하되, 코드 스니펫이나 API 메서드명 등은 원문(영어) 그대로 유지하세요."
    )
    
    user_prompt = (
        f"[참조 컨텍스트]\n{context_str}\n\n"
        f"[사용자 질문]\n{query}\n\n"
        f"답변:"
    )
    
    print(f"\n💬 컨텍스트 조립 완료 (참조 청크: {len(search_results)}개) -> LLM 호출 중...")
    
    try:
        # 4. openai_survice 모듈 클라이언트를 통한 Chat Completion API 호출
        response = openai_survice.client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.2,      # RAG의 안정적인 팩트 기반 답변을 위해 낮은 창의성 설정
            max_tokens=1024
        )
        
        # 5. 완성된 최종 답변 텍스트 반환
        return response.choices[0].message.content
        
    except Exception as e:
        return f"답변 생성 중 API 에러가 발생했습니다: {str(e)}"