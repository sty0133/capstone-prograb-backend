from sentence_transformers import SentenceTransformer

# import requests
# import os
def embedding_model(docs):
    # 허깅페이스 KURE-v1 임베딩 모델 사용
    model = SentenceTransformer("nlpai-lab/KURE-v1")

    # GPU 사용 시 주석 해제
    # model = SentenceTransformer("nlpai-lab/KURE-v1", device='cuda')

    embeddings = model.encode(docs)

    # 외부에서 임베딩 모델 사용시 주석 해제
    # url = os.getenv('EMBEDDING_MODEL_URL')
    # data = {
    #             "docs": docs,
    #         }
    # response = requests.post(url, json=data)
    # if response.status_code == 200:
    #     embeddings = response.json()
    #     embeddings = embeddings['data']
    # else:
    #     print(f"Error: {response.status_code}, {response.message}")
    #     return None
    return embeddings

# https://velog.io/@autorag/RAG-대표적인-청킹-방법-5가지
# 청크 사이즈와 오버랩 조절로 문서 유사도 조절
def load_and_retrieve_docs_sliding_window(docs, chunk_size=200, chunk_overlap=100):
    def sliding_window_split(text, size, overlap):
        chunks = []
        start = 0
        while start < len(text):
            end = min(start + size, len(text))
            chunks.append(text[start:end])
            # 겹침 구간 처리
            start += (size - overlap)
        return chunks

    # 문자가 chunk_size 이상인 경우 슬라이딩 윈도우로 분할
    if len(docs) >= chunk_size:
        # 슬라이딩 윈도우로 텍스트 분할
        sentences = sliding_window_split(docs, chunk_size, chunk_overlap)

        embeddings = embedding_model(sentences)
        # if embeddings is None:
        #     return exit()
        return embeddings, sentences
    
    # 텍스트가 chunk_size 미만일 경우 전체 텍스트로 처리
    embeddings = embedding_model([docs])
    # if embeddings is None:
    #     return exit()
    return embeddings, [docs]