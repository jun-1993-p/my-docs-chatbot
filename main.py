import rag_pipeline
import text_embedding
import text_chunks
import text_ingestion

# [실행 흐름 예시]
if __name__ == "__main__":
  # 1. 가공된 list[str]을 단 한 번만 임베딩 함수로 전달.
  features_tensor = text_embedding.get_embedding_tensor()

  # 2. ChromaDB 적재 파이프라인 구동 (배치 임베딩 적용형)
  lua_collection = text_embedding.ingest_chunks_to_chromadb(features_tensor, collection_name="lua_gadget_guide")
  
  # 3. 실시간 질의 및 최종 RAG 답변 추출
  user_query = "How can I access object properties in Lua scripts?"
  final_answer = rag_pipeline.generate_rag_answer(lua_collection, query=user_query, top_k=3)
  
  print("\n🤖 [AI 최종 RAG 답변]")
  print("-" * 60)
  print(final_answer)
  print("-" * 60)