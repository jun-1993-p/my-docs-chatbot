import fitz  # PyMuPDF
# import re

# def extract_text_from_pdf(pdf_path: str) -> str:
#       """PDF에서 텍스트 추출"""
#       doc = fitz.open(pdf_path)
#       pdf_text = ""

#       for page_num in range(35,len(doc)):
#             page = doc[page_num]
#             blocks = page.get_text("dict", flags=11)["blocks"]
#             for b in blocks:  
#                   for l in b["lines"]:
#                         s = l["spans"][0]  
#                         print("")
#                         s_color = s['color']
#                         print(f"Text: '{s['text']}'")  
#                         print(f"color #{s_color:06x}")
#             pdf_text += page.get_text("text", flags=11)

#       return pdf_text

# def clean_text(raw: str) -> str:
#       """PDF에서 추출한 텍스트를 정리"""
#       out = []

#       for line in raw.splitlines():
#             s = line.strip()
#             if not s:
#                   continue
#             if re.match(r"\d", line):
#                   continue
#             out.append(line.rstrip())
#       return "\n".join(out)

# def split_parts(text: str) -> dict[str, str]:
#       """일반 근로자용 / 별첨 괴롭힘 규정 / 단시간 근로자용으로 분리. [별지] 서식은 버린다."""
#       parts, current = {}, None
#       for line in text.splitlines():
#             s = line.strip()
#             if s == "일반 근로자용":
#                   current = "일반 근로자용"
#             elif s == "단시간 근로자용":
#                   current = "단시간 근로자용"
#             elif s.startswith("[별첨]"):
#                   current = "별첨 괴롭힘 규정"
#             elif s.startswith("[별지"):
#                   current = None
#             elif current:
#                   parts.setdefault(current, []).append(line)
#       return {k: "\n".join(v) for k, v in parts.items()}

pdf_path = r'C:\Users\302\my-docs-chatbot\docs\Vectric Lua Interface Documentation.pdf'
# pdf_text = extract_text_from_pdf(pdf_path)
# pdf_text_cleaned = clean_text(pdf_text)
# pdf_parts = split_parts(pdf_text_cleaned)







doc = fitz.open(pdf_path)
page = doc[35]

blocks = page.get_text("dict", flags=11)["blocks"]

print(blocks)