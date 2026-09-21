import re
import numpy as np
import text_ingestion

QUICK = True   # True: 비교 전략 2개(빠름) / False: 5개 전부

def chunk_text(text: str, chunk_size: int = 500, overlap: int = 50) -> list[str]:
    """글자 수 기준 고정 청킹"""
    chunks, start = [], 0
    while start < len(text):
        chunk = text[start:start + chunk_size]
        if chunk.strip():
            chunks.append(chunk)
        start += chunk_size - overlap
    return chunks

def chunk_text_article(text: str, max_len: int, overlap: int = 100) -> list[str]:
    """max_len을 넘지 않으면서 문장 단위(., !, ?)로 텍스트를 분할합니다."""
    chunks = []
    while text:
        text = text.strip()
        if not text:
            break
            
        # 남은 텍스트가 max_len 이내이고 문장으로 잘 끝나면 통째로 추가
        if len(text) <= max_len and text.endswith(('.', '!', '?')):
            chunks.append(text)
            break
            
        # max_len 범위 안에서 가장 마지막 문장 종결 기호(. ! ?) 위치 찾기
        boundary_match = None
        for match in re.finditer(r"[.!?][\"')\]]*\s*", text[:max_len]):
            boundary_match = match
        
        if boundary_match:
            split_idx = boundary_match.end()
            p = text[:split_idx].strip()
            # 다음 루프를 위해 overlap 크기만큼 겹쳐서 남겨둠
            text = text[split_idx - overlap:] if len(text) > split_idx and split_idx > overlap else text[split_idx:]
        else:
            # 범위 내에 문장 기호가 없는 긴 문장은 글자 수로 분할
            p = text[:max_len].strip()
            text = text[max_len - overlap:] if len(text) > max_len else ""
            
        chunks.append(p)
    return chunks

def chunk_by_article(data_list: list[dict], max_len: int = 800) -> list[str]:
    """딕셔너리를 순회하며 chunk_text를 호출합니다."""
    chunks, seen = [], set()
    for d in data_list:
        for title, body in d.items():
            body = body.strip()
            if len(body) < 20 or body in seen:
                continue
            seen.add(body)
            
            if len(body) <= max_len and body.endswith(('.', '!', '?')):
                chunks.append(body)
            else:
                # 변경된 chunk_text 함수를 기존과 동일한 방식으로 호출합니다.
                for p in chunk_text_article(body, max_len, 100):
                    chunks.append(p if p.startswith(title) else f"{title} (계속)\n{p}")
    return chunks

def noise_tags(chunk: str) -> list[str]:
    """청크에 섞인 노이즈 종류를 판별합니다."""
    tags = []
    
    # 1. 기존 조건들 (예시용 유지)
    # if len(ARTICLE.findall(chunk)) >= 2: tags.append("여러 조항 섞임")
    # ...
    
    # 2. 새로운 조건: 청크의 마지막이 올바른 문장 기호로 끝나지 않는가?
    # 우측 공백(개행, 띄어쓰기 등)을 제거한 후 마침표(.), 물음표(?), 느낌표(!)로 끝나지 않으면 노이즈로 판단
    cleaned_chunk = chunk.rstrip()
    if not cleaned_chunk.endswith(('.', '!', '?')):
        tags.append("불완전한 문장으로 끝남")
        
    return tags

all_strategies = {
    "fixed_500":   chunk_text(text_ingestion.pdf_raw, 500, 50),
    "article":     chunk_by_article(text_ingestion.pdf_parts),
}

for name, chunks in all_strategies.items():
    print(np.mean([len(c) for c in chunks]))

    noisy = sum(1 for c in chunks if noise_tags(c))
    print(f"{name:12s} 청크 {len(chunks):4d}개 / 평균 {int(np.mean([len(c) for c in chunks])):4d}자 / 노이즈 청크 {noisy / len(chunks):.0%}")

keep = ("fixed_500", "article") if QUICK else tuple(all_strategies)
strategies = {k: all_strategies[k] for k in keep}
print("\n임베딩 비교 대상:", list(strategies), f"(총 {sum(map(len, strategies.values()))}개)")

print("\n--- fixed_500 예시 ---")
print(all_strategies["fixed_500"][40])
print("\n--- article 예시 ---")
print(next(c for c in all_strategies["article"] if c.startswith("Introduction")))