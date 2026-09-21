import rag_pipeline
import text_embedding
import text_chunks
import text_ingestion

# [실행 흐름 예시]
if __name__ == "__main__":   
  # main.py (청크 데이터 준비 프로세스)

  # 예시: 원본 데이터가 list[dict] 형태인 경우
  raw_chunks = [{"title": "Introduction", "body": "The Script interface..."}, ...]

  # 1. 임베딩 함수에 넣기 전에 '딱 한 번만' 문자열로 가공합니다.
  processed_sentences = [
      f"제목: {item['title']}\n본문: {item['body']}" if isinstance(item, dict) else item 
      for item in raw_chunks
  ]

  # 2. 가공된 list[str]을 단 한 번만 임베딩 함수로 전달합니다.
  features_tensor = text_embedding.get_embedding_tensor(processed_sentences)

  # 3. ChromaDB 적재 파이프라인 구동 (배치 임베딩 적용형)
  lua_collection = text_embedding.ingest_chunks_to_chromadb(features_tensor, collection_name="lua_gadget_guide")
  
  # 4. 실시간 질의 및 최종 RAG 답변 추출
  user_query = "How can I access object properties in Lua scripts?"
  final_answer = rag_pipeline.generate_rag_answer(lua_collection, query=user_query, top_k=3)
  
  print("\n🤖 [AI 최종 RAG 답변]")
  print("-" * 60)
  print(final_answer)
  print("-" * 60)