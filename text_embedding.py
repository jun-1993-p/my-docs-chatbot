import os
import uuid
import torch
import chromadb
from chromadb.config import Settings

# 이전 단계에서 지적된 가동 코드 연결 및 예외 처리
# openai_survice 모듈이 실제 프로젝트에 존재하는 파일명이라고 가정하고 연동합니다.
import openai_survice
from text_chunks import chunk_by_article
import text_ingestion 


def get_embedding_tensor(text_list: list[str], model: str = "nvidia/nemotron-3-embed-1b") -> list[list[float]]:
    """
    텍스트 리스트를 안전한 크기로 배치 분할하여 임베딩 벡터로 변환합니다.
    (최대 배치가 256개이므로 안정성을 위해 기본값 200개 단위로 나눕니다.)
    """
    if not text_list:
        return []
        
    for item in text_list:
        if not isinstance(item, str):
            raise ValueError("text_list의 요소는 반드시 str 타입이어야 합니다.")

    all_embeddings = []
    batch_size = 200  # API 최대 허용량(256)보다 안전하게 설정
    
    # 텍스트 리스트를 batch_size 단위로 슬라이싱하여 순차 호출
    for i in range(0, len(text_list), batch_size):
        batch_text = text_list[i:i + batch_size]
        print(f"임베딩 진행 중... ({i} ~ {min(i + batch_size, len(text_list))} / 총 {len(text_list)}개)")
        
        # API 호출
        response = openai_survice.client.embeddings.create(input=batch_text, model=model)
        
        # 결과 임베딩을 순차적으로 축적
        batch_embeddings = [data.embedding for data in response.data]
        all_embeddings.extend(batch_embeddings)
    
    # PyTorch 텐서 변환 연산 (원래 파이프라인의 구조 유지를 위함)
    embedding_tensor = torch.tensor(all_embeddings, dtype=torch.float32)
    
    # ChromaDB 호환을 위해 최종 list[list[float]]로 반환
    return embedding_tensor.tolist()

def ingest_chunks_to_chromadb(collection, clean_text_list: list[str], features_tensor: torch.Tensor, raw_chunks: list[dict] = None):
    """
    미리 생성된 임베딩 텐서와 텍스트 리스트를 받아 ChromaDB 컬렉션에 원샷으로 적재합니다.
    """
    if len(clean_text_list) == 0:
        print("적재할 데이터가 없습니다.")
        return
        
    # 1. PyTorch 텐서를 ChromaDB가 허용하는 list[list[float]] 구조로 변환
    if isinstance(features_tensor, torch.Tensor):
        embeddings_list = features_tensor.tolist()
    else:
        embeddings_list = features_tensor  # 이미 리스트 형태인 경우 대비

    # 2. 유일한 ID 배열 생성 (청크 수와 동일하게)
    ids = [str(uuid.uuid4()) for _ in range(len(clean_text_list))]

    # 3. (선택사항) 메타데이터 가공 - 원본 raw_chunks에 다른 정보(예: page, file_name)가 있다면 주입
    metadatas = []
    if raw_chunks and len(raw_chunks) == len(clean_text_list):
        for chunk in raw_chunks:
            # ChromaDB 메타데이터는 오직 str, int, float, bool 타입만 허용합니다.
            metadata = {k: v for k, v in chunk.items() if isinstance(v, (str, int, float, bool))}
            metadatas.append(metadata)
    else:
        # 메타데이터가 없을 경우 빈 값 처리
        metadatas = [{"source": "pdf_chunk"} for _ in range(len(clean_text_list))]

    # 4. ChromaDB 적재 작업 실행 (단 한 번의 요청으로 배치 처리)
    print(f"ChromaDB '{collection.name}' 컬렉션에 {len(embeddings_list)}개의 벡터 데이터를 적재 중입니다...")
    
    collection.add(
        ids=ids,
        embeddings=embeddings_list,
        documents=clean_text_list,  # 실제 검색 시 리턴받을 컨텍스트 텍스트들
        metadatas=metadatas
    )
    
    print(f"--- 적재 완료: 총 {collection.count()}개의 벡터가 컬렉션에 저장되었습니다. ---")
    
# 1단계: chunk_by_article을 통해 타이틀별 청크 딕셔너리 획득
# input_data = {'Introduction': '...', 'Objects': '...'}
processed_chunks_dict = chunk_by_article(text_ingestion.pdf_parts, max_len=800)

# 2단계: ChromaDB 파이프라인에 대입하여 임베딩 및 Vector DB 최종 적재 완료
lua_collection = ingest_chunks_to_chromadb(processed_chunks_dict, collection_name="lua_gadget_guide")
