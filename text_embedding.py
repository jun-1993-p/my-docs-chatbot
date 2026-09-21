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

def ingest_chunks_to_chromadb(chunks_dict: dict, collection_name: str = "vectric_lua_guide") -> chromadb.Collection:
    """
    chunk_by_article에서 생성된 {타이틀: [청크 리스트]} 구조의 딕셔너리를 
    ChromaDB의 특정 컬렉션에 적재합니다.
    """
    # 1. 크로마 DB 클라이언트 초기화 (로컬 영구 저장소 모드 설정)
    # 2026년 크로마DB 표준 규격에 부합하는 PersistentClient 객체 사용
    client = chromadb.PersistentClient(path="./chroma_db_storage")
    
    # 2. 컬렉션 생성 또는 기존 컬렉션 로드 (동일 이름이 있으면 가져옴)
    collection = client.get_or_create_collection(
        name=collection_name,
        metadata={"description": "Vectric Lua Script Documentation Chunks"}
    )
    
    # 3. 딕셔너리 데이터를 순회하며 적재용 평탄화 데이터 생성
    all_documents = []
    all_metadatas = []
    all_ids = []
    
    for title, chunk_list in chunks_dict.items():
        for idx, chunk in enumerate(chunk_list):
            all_documents.append(chunk)
            
            # 메타데이터 구조화: RAG 검색 시 필터링이 가능하도록 타이틀과 순번 저장
            all_metadatas.append({
                "source_title": title,
                "chunk_index": idx
            })
            
            # 고유 ID 생성 (중복 적재 방지 및 추적용)
            all_ids.append(f"id_{title}_{idx}_{str(uuid.uuid4())[:8]}")
            
    if not all_documents:
        print("적재할 청크 데이터가 존재하지 않습니다.")
        return collection
        
    # 4. 일괄 임베딩 생성 (앞서 리팩토링한 함수 호출)
    print(f"총 {len(all_documents)}개의 청크에 대한 임베딩 벡터 생성을 시작합니다...")
    all_embeddings = get_embedding_tensor(all_documents)
    
    # 5. ChromaDB 대량 적재 (Upsert 수행으로 안전성 확보)
    print(f"ChromaDB '{collection_name}' 컬렉션에 데이터를 적재 중입니다...")
    collection.upsert(
        ids=all_ids,
        embeddings=all_embeddings,
        metadatas=all_metadatas,
        documents=all_documents
    )
    
    print(f"--- 적재 완료: 총 {collection.count()}개의 벡터가 컬렉션에 저장되었습니다. ---")
    return collection


# 1단계: chunk_by_article을 통해 타이틀별 청크 딕셔너리 획득
# input_data = {'Introduction': '...', 'Objects': '...'}
processed_chunks_dict = chunk_by_article(text_ingestion.pdf_parts, max_len=800)

# 2단계: ChromaDB 파이프라인에 대입하여 임베딩 및 Vector DB 최종 적재 완료
lua_collection = ingest_chunks_to_chromadb(processed_chunks_dict, collection_name="lua_gadget_guide")
