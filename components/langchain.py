import numpy as np
# from langchain.text_splitter import RecursiveCharacterTextSplitter
# from langchain.schema import Document

from sentence_transformers import SentenceTransformer

from components.mongodb import *
from components.faiss import *

from utils.list_utils import *
from utils.model_utils import *

# def convert_to_tosil(doc):

#     # numpy 배열로 변환 후 tolist() 호출
#     array = np.array(doc)
#     converted_list = array.tolist()
#     return converted_list

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

        # 허깅페이스 KURE-v1 임베딩 모델 사용
        model = SentenceTransformer("nlpai-lab/KURE-v1")
        embeddings = model.encode(sentences)
        return embeddings
    
    # 텍스트가 chunk_size 미만일 경우 전체 텍스트로 처리
    model = SentenceTransformer("nlpai-lab/KURE-v1")
    embeddings = (model.encode([docs]))
    return embeddings

# # 리스트에서 문서 검색하는 함수
# def retrieve_docs(question):

#     global embeddings_docs
#     embeddings_docs = EmbeddedVector.get_all_embeddings() if not 'embeddings_docs' in globals() else embeddings_docs

#     model = SentenceTransformer("nlpai-lab/KURE-v1")
#     question_embedding = model.encode(question)
    
#     retrieved_docs = []
#     for doc in embeddings_docs:
#         # 유사도 계산
#         similarity = compute_similarity(doc['embedded'], question_embedding)
#         # similarity가 0.5 이상인 경우만 추가
#         if similarity >= 0.5:
#             retrieved_docs.append((similarity, doc['doc_no'], doc['category']))

#     # 유사도 기준으로 정렬하고 가장 유사한 상위 5개 문서 선택
#     retrieved_docs.sort(reverse=True, key=lambda x: x[0])
#     print(retrieved_docs)
#     doc_nos = [[int(doc[1]), doc[2]] for doc in retrieved_docs[:5]]

#     # 중복 값 제거
#     doc_nos = remove_duplicates_preserve_order(doc_nos)
#     return doc_nos

# # 코사인 유사도를 계산하는 함수
# def compute_similarity(vec1, vec2):
#     from sklearn.metrics.pairwise import cosine_similarity
#     import numpy as np
#     vec1 = np.array(vec1).reshape(1, -1)
#     vec2 = np.array(vec2).reshape(1, -1)
#     return cosine_similarity(vec1, vec2)[0][0]

def rag_chain(question):
    # retrieved_docs = retrieve_docs(question)
    model = SentenceTransformer("nlpai-lab/KURE-v1")
    query_vector = model.encode(question)

    faiss_ids = find_top_similar_vectors(query_vector)   # 벡터 ID 가 추출된다.
    
    if not faiss_ids:
        return "질문을 구체적으로 해주세요."
    
    embedded_doc = EmbeddedVector.get_documents_by_faiss_ids(faiss_ids)
    find_docs = [MongodbNotice.find_document_by_doc_and_category(doc) for doc in embedded_doc]
    # docs = remove_duplicates_preserve_order(find_docs)

    formatted_prompt = f"Question: {question}\n\nContext: {find_docs}"
    return find_docs
    # response = llama_kr_model(formatted_prompt)
    # if response is None:
    #     return "응답을 생성하는데 실패했습니다."
    # return response