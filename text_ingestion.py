import fitz  # PyMuPDF
import re

def extract_text_from_pdf(pdf_path: str) -> str:
      """PDF에서 텍스트 추출"""
      doc = fitz.open(pdf_path)
      # print(len(doc))
      pdf_text = ""

      for page_num in range(34,len(doc)):
            page = doc[page_num]
            blocks = page.get_text("dict", flags=11)["blocks"]
            for b in blocks:  
                  for l in b["lines"]:
                        for s in l["spans"]: 
                              pdf_text += s['text'] + "\n" + f"color #{s['color']:06x}" + "\n"
                              # print(f"Text: '{s['text']}'")  
                              # print(f"color #{s['color']:06x}")

      return pdf_text

def clean_text(raw: str) -> str:
      """PDF에서 추출한 텍스트를 정리"""
      out = []
      pre_s = ''

      for line in raw.splitlines():
            s = line.strip()
            if not s:
                  continue
            if s in ("color #000000", "color #943634", "color #4f81bd"):
                  continue
            if re.match(r"\d", line):
                  continue
            if s in ("color #1f497d", "color #365f91"):
                  out.append(line.rstrip())
                  out.append(pre_s)
                  pre_s = ''
                  continue
            out.append(pre_s)
            pre_s = line.rstrip()

      out.append(pre_s)
      return "\n".join(out)

def split_parts(text: str) -> list[dict]:
    results = []
    
    current_title = None
    buffer_lines = []
    
    # 현재 읽고 있는 줄이 description 영역인지 여부
    # (title 색상이 나오기 전까지의 모든 텍스트/서브타이틀은 desc로 취급)
    is_desc_zone = False 

    def commit_section():
        nonlocal current_title, buffer_lines
        if current_title and buffer_lines:
            content = " ".join(buffer_lines).strip()
            if content:
                # 기존 리스트에서 현재 타이틀을 가진 딕셔너리가 있는지 확인
                title_dict = next((d for d in results if current_title in d), None)
                
                if title_dict:
                    # 이미 존재한다면 공백으로 내용 누적 (중복 방지)
                    title_dict[current_title] += " " + content
                else:
                    # 없으면 신규 딕셔너리 생성 후 추가
                    results.append({current_title: content})
        buffer_lines = []

    for line in text.splitlines():
        s = line.strip()
        
        # 1. Title 색상 감지 -> 새로운 섹션 시작
        if s in ("color #1f497d", "color #365f91"):
            commit_section()  # 이전까지 쌓인 desc 저장
            current_title = None
            is_desc_zone = False
            continue
            
        # 2. 텍스트 처리
        if not is_desc_zone:
            # Title 색상 아래에 나오는 첫 줄들을 타이틀명으로 누적
            if current_title:
                current_title += " " + line
            else:
                current_title = line
            is_desc_zone = True  # 타이틀 아래의 텍스트는 desc 영역으로 간주
        else:
            # 그 외의 모든 텍스트(subtitle 포함)는 desc 버퍼에 누적
            buffer_lines.append(line)

    # 루프 종료 후 남아있는 마지막 섹션 저장
    commit_section()
    return results


pdf_path = r'C:\Users\302\my-docs-chatbot\docs\Vectric Lua Interface Documentation.pdf'
pdf_text = extract_text_from_pdf(pdf_path)
# print(pdf_text)
pdf_text_cleaned = clean_text(pdf_text)
# print(pdf_text_cleaned)
pdf_parts = split_parts(pdf_text_cleaned)
print(pdf_parts)