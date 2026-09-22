import fitz  # PyMuPDF
import re

"""
Test Ingestion 시나리오.
1. 데이터 추출.
      * format : pdf
      * start_index : 35 - 1
      * end_index : en(doc)
      * output : text, color
      * toolkit : PyMuPDF (fitz)

2. 데이터 유효성 검사 : PASS

3. 불필요한 데이터 제거.
      * 불필요한 blank 제거
      * 불필요한 color_data 제거
      * 불필요한 page_number 제거

4. 데이터 변환.
      * title_keyword : "color #1f497d", "color #365f91"
      * def func() -> dict[str,str]:
"""

# 데이터 추출.
def extract_text_from_pdf(pdf_path: str) -> str:
      """PDF에서 텍스트 추출"""
      doc = fitz.open(pdf_path)
      pdf_text = ""
      color = ""
      pre_color = ""

      for page_num in range(35 - 1, len(doc)):
            page = doc[page_num]
            blocks = page.get_text("dict", flags=11)["blocks"]
            for b in blocks:  
                  for l in b["lines"]:
                        for s in l["spans"]: 
                              text = s['text'].strip() + "\n"
                              color = s['color']

                              if pre_color != color:
                                    color = f"color #{color:06x}" + "\n"
                                    pdf_text +=  color + text
                              else:
                                    pdf_text += text
                              
                              pre_color = s['color']

      return pdf_text

# 데이터 변환 1. 불필요한 정보 제거.
def clean_text(raw: str) -> str:
      """PDF에서 추출한 텍스트를 정리"""
      out = []

      for line in raw.splitlines():
            s = line.strip()
            if not s:
                  continue
            if s in ("color #000000", "color #943634", "color #4f81bd"):
                  continue
            if re.match(r"\d", line):
                  continue
            out.append(line.rstrip())

      return "\n".join(out)

# 데이터 변환 2. 섹션별로 나누기.
def split_parts(text: str) -> dict[str,str]:
      """텍스트를 섹션별로 나누어 리스트로 반환"""
      parts = {}
      current_title = None
      current_color = None

      for line in text.splitlines():
            s = line.strip()
            if not s:
                  continue
            if s in ("color #1f497d", "color #365f91"):
                  current_color = s
            elif current_color:
                  current_title = s
                  current_color = None
            elif current_title:
                  parts.setdefault(current_title, []).append(line) 

      return {k: "\n".join(v) for k, v in parts.items()}

# 목적지로 적재
def pdf_ingest():
      # PDF 경로 설정.
      pdf_path = r'C:\Users\302\my-docs-chatbot\docs\Vectric Lua Interface Documentation.pdf'

      # PDF 추출.
      pdf_raw = extract_text_from_pdf(pdf_path)

      # PDF 변환.
      pdf_clean = clean_text(pdf_raw)
      pdf_parts = split_parts(pdf_clean)
    
      return pdf_parts

# PDF 추출 및 가공 실행 테스트.
# pdf_parts = pdf_ingest()
# print(f"PDF 추출 완료: {len(pdf_parts)}개의 섹션")
# print(f"첫 번째 섹션 예시: {pdf_parts.items()}")
