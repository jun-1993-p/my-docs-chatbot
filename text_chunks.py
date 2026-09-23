import re

from langchain_text_splitters import (
    CharacterTextSplitter,
    MarkdownHeaderTextSplitter,
    RecursiveCharacterTextSplitter,
)

import text_ingestion

"""
Text Chunking 전략.
(1) Fixed-Size Chunking. (고정 크기 분할)
- 256, 512, 1024 단위로 분할.

(2) Recursive Character Splitting. (재귀 문자 분할)

(3) Document-Structure-Based Chunking. (문서 구조 기반)
"""

# Fixed-Size Chunking.
def splite_fixed_size(raw: str, chunk_size: int = 512) -> list[str]:
      text_splitter = CharacterTextSplitter(
            separator = '',
            chunk_size = chunk_size,
            chunk_overlap  = 50,
            length_function = len,
      )

      return text_splitter.split_text(raw)

# Recursive Character Splitting.
def split_recursive_char(raw: str) -> list[str]:
      recursive_splitter = RecursiveCharacterTextSplitter(
            chunk_size=512,
            chunk_overlap=50,
            separators=["\n\n", "\n", ". ", " "]
      )

      return recursive_splitter.split_text(raw)

# Document-Structure-Based Chunking.
def splite_docs_based_texts(raw: str):
      headers = [("color #1f497d", "h1"), ("color #365f91", "h1"), ("color #4f81bd", "h2"),] 
      md_splitter = MarkdownHeaderTextSplitter(
      headers_to_split_on=headers
      )

      # 큰 섹션은 다시 Recursive로 2차 분할
      chunks = md_splitter.split_text(raw)
      # for chunk in chunks:
      #       if len(chunk) > 512:
      #             sub_chunks = split_recursive_char(chunk)

      return chunks
      

# pdf에서 텍스트 추출. 결과 : 인스턴스 객체.
ingested_pdf = text_ingestion.ingest_pdf()
texts_fixed_size = splite_fixed_size(ingested_pdf.pdf_raw)



recursive_char_dict = {}

for k, v in ingested_pdf.pdf_parts.items():
      texts_recursive_char = split_recursive_char(v)
      recursive_char_dict[k] = texts_recursive_char

print(texts_fixed_size[0])
print(recursive_char_dict["DocumentVariable"])
print(splite_docs_based_texts(ingested_pdf.pdf_raw_with_color))















# QUICK = True   # True: 비교 전략 2개(빠름) / False: 5개 전부

# # def split_into_sentences(text: str) -> list[str]:
# #     """정규식을 사용하여 텍스트를 깨지지 않는 독립된 문장 단위 리스트로 분리합니다."""
# #     sentences = []
# #     start_idx = 0
# #     # 문장 종결 기호와 그 뒤에 붙는 닫는 괄호, 따옴표 및 공백까지 포함하여 매칭
# #     for match in re.finditer(r"[.!?][\"')\]]*\s*", text):
# #         end_idx = match.end()
# #         sentence = text[start_idx:end_idx].strip()
# #         if sentence:
# #             sentences.append(sentence)
# #         start_idx = end_idx
        
# #     # 남은 텍스트가 있다면 마지막 문장으로 추가
# #     remainder = text[start_idx:].strip()
# #     if remainder:
# #         sentences.append(remainder)
        
# #     return sentences

# # def chunk_text(text: str, max_len: int = 512, overlap: int = 50, use_sentence_boundary: bool = True) -> list[str]:
# #     """
# #     설정된 조건에 따라 텍스트를 청크 리스트로 분할합니다.
# #     use_sentence_boundary (bool): True이면 문장 단위 분할(On), False이면 고정 크기 분할(Off)
# #     """
# #     chunks = []
# #     text_len = len(text)
    
# #     # 예외 처리: 오버랩 크기가 max_len보다 크거나 같으면 제한
# #     if overlap >= max_len:
# #         overlap = max_len - 1

# #     # 모드 1: 문장 경계 찾기 기능 On (split_into_sentences 함수 연동)
# #     if use_sentence_boundary:
# #         sentences = split_into_sentences(text)
# #         if not sentences:
# #             return chunks

# #         current_chunk = ""
# #         current_sentences = []
        
# #         for sentence in sentences:
# #             # 단일 문장 자체가 이미 max_len을 초과하는 특이 케이스는 고정 크기 슬라이싱으로 처리
# #             if len(sentence) > max_len:
# #                 if current_chunk:
# #                     chunks.append(current_chunk)
# #                     current_chunk = ""
# #                     current_sentences = []
                
# #                 s_start = 0
# #                 while s_start < len(sentence):
# #                     sub_chunk = sentence[s_start:s_start + max_len]
# #                     if sub_chunk.strip():
# #                         chunks.append(sub_chunk)
# #                     s_start += max_len - overlap
# #                 continue

# #             test_chunk = f"{current_chunk} {sentence}".strip() if current_chunk else sentence

# #             if len(test_chunk) <= max_len:
# #                 current_chunk = test_chunk
# #                 current_sentences.append(sentence)
# #             else:
# #                 if current_chunk:
# #                     chunks.append(current_chunk)
                
# #                 # Overlap 구현: 역순으로 문장을 더해가며 설정된 overlap 길이를 만족할 때까지 수집
# #                 overlap_chunk = ""
# #                 overlap_sentences = []
# #                 for prev_sent in reversed(current_sentences):
# #                     test_overlap = f"{prev_sent} {overlap_chunk}".strip() if overlap_chunk else prev_sent
# #                     if len(test_overlap) <= overlap:
# #                         overlap_chunk = test_overlap
# #                         overlap_sentences.insert(0, prev_sent)
# #                     else:
# #                         break
                
# #                 current_sentences = overlap_sentences + [sentence]
# #                 current_chunk = f"{overlap_chunk} {sentence}".strip() if overlap_chunk else sentence

# #         if current_chunk:
# #             chunks.append(current_chunk)

# #     # 모드 2: 문장 경계 찾기 기능 Off (순수 글자 수 기준 고정 청킹)
# #     else:
# #         start_idx = 0
# #         while start_idx < text_len:
# #             end_idx = start_idx + max_len
# #             chunk = text[start_idx:end_idx]
            
# #             if chunk.strip():
# #                 chunks.append(chunk)
                
# #             start_idx += max_len - overlap
            
# #             if start_idx >= text_len or (max_len - overlap) <= 0:
# #                 break
                
# #     return chunks


# def noise_tags(chunk: str) -> list[str]:
#     """청크에 섞인 노이즈 종류를 판별합니다."""        
#     tags = []
    
#     # 우측 공백(개행, 띄어쓰기 등)을 제거하여 실제 끝나는 문자열 확인
#     cleaned_chunk = chunk.rstrip()
    
#     if not cleaned_chunk:
#         tags.append("빈 청크")
#         return tags
        
#     # 새로운 조건: 청크의 마지막이 올바른 문장 기호나 문장 종결 괄호/따옴표로 끝나지 않는가?
#     # 정규식 설명: 마침표, 느낌표, 물음표 뒤에 닫는 따옴표나 괄호가 올 수 있는 구조인지 검사
#     if not re.search(r"[.!?][\"')\]]*$", cleaned_chunk):
#         tags.append("불완전한 문장으로 끝남")
        
#     return tags

# # 1. 벤치마크 대상 전략 데이터 구축
# # 기존에 정의된 text_ingestion.pdf_raw(전체 텍스트)와 text_ingestion.pdf_parts(딕셔너리) 구조를 활용합니다.
# article_result_dict = chunk_by_article(text_ingestion.pdf_parts, max_len=512)

# # 통계 검증 및 비교를 위해 딕셔너리 내부의 모든 청크 리스트를 하나의 단일 리스트로 병합(Flatten)합니다.
# article_flattened_chunks = []
# for title, chunk_list in article_result_dict.items():
#     article_flattened_chunks.extend(chunk_list)

# def d():
#     pass

# all_strategies = {
#       "fixed_256": chunk_text(ingested_pdf.pdf_raw, max_len=256, use_sentence_boundary=False),
#       "fixed_512": chunk_text(ingested_pdf.pdf_raw, use_sentence_boundary=False),
#       "fixed_1024": chunk_text(ingested_pdf.pdf_raw, max_len=1024, use_sentence_boundary=False),      
#       "article":   article_flattened_chunks,
#       "docs_based" : d()
# }

# # # 2. 전략별 통계 및 노이즈 비율 출력 루프
# # for name, chunks in all_strategies.items():
# #     if not chunks:
# #         print(f"{name:12s} 청크가 비어 있습니다.")
# #         continue
        
# #     # 각 청크 리스트를 순회하며 noise_tags의 결과 리스트가 비어있지 않은(노이즈가 감지된) 개수 합산
# #     noisy = sum(1 for c in chunks if noise_tags(c))
# #     avg_len = int(np.mean([len(c) for c in chunks]))
# #     noise_ratio = noisy / len(chunks)
    
# #     print(f"{name:12s} 청크 {len(chunks):4d}개 / 평균 {avg_len:4d}자 / 노이즈 청크 {noise_ratio:.0%}")

# # 3. QUICK 플래그 기반의 임베딩 비교 대상 필터링
# keep = ("fixed_500", "article") if QUICK else tuple(all_strategies.keys())
# strategies = {k: all_strategies[k] for k in keep}

# total_chunks_count = sum(len(chunks_list) for chunks_list in strategies.values())
# print("\n임베딩 비교 대상:", list(strategies.keys()), f"(총 {total_chunks_count}개)")

# # 4. 각 청킹 결과의 예시 데이터 출력 (인덱스 에러 방지 예외 처리 포함)
# print("\n--- fixed_500 예시 ---")
# if len(all_strategies["fixed_500"]) > 40:
#     print(all_strategies["fixed_500"][40])
# else:
#     print(all_strategies["fixed_500"][0] if all_strategies["fixed_500"] else "청크 데이터 없음")

# # print("\n--- article 예시 ---")
# # try:
# #     # "Introduction" 문구로 시작하는 청크 예시 검색 및 출력
# #     intro_example = next(c for c in all_strategies["article"] if c.startswith("Introduction"))
# #     print(intro_example)
# # except StopIteration:
# #     print(all_strategies["article"][0] if all_strategies["article"] else "Introduction 청크 데이터 없음")