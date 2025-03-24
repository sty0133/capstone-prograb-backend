import faiss
import numpy as np
import os

# 전역 변수 선언
embedding_dim = 1024
index = None  # 초기 상태에서는 None

# FAISS 인덱스를 초기화하거나 로드
def initialize_faiss():
    global index  # 전역 변수 접근
    if index is None:  # 아직 초기화되지 않은 경우
        if os.path.exists("faiss.index"):
            index = faiss.read_index("faiss.index")
            print(f"Index loaded. Total vectors: {index.ntotal}")
        else:
            index = faiss.IndexFlatL2(embedding_dim)
            print("New FAISS index created.")
    return index

# FAISS 인덱스를 저장
def save_index():
    global index
    if index is not None:
        faiss.write_index(index, "faiss.index")
        print(f"Index saved. Total vectors: {index.ntotal}")

# 새 벡터 추가
def instert_vectors(vectors):
    global index
    if index is None:
        initialize_faiss()  # 필요 시 초기화
    index.add(vectors)
    faiss_ids = list(range(index.ntotal - len(vectors), index.ntotal))  # 새로 추가된 벡터들의 ID
    print(f"Added {len(vectors)} vectors. Total vectors: {index.ntotal}")
    return faiss_ids

# 유사도 검색
def find_top_similar_vectors(query_vector, top_k=3, threshold=1.5):
    global index
    if index is None:
        initialize_faiss()  # 필요 시 초기화
    query_vector = query_vector.reshape(1, -1).astype('float32')
    distances, indices = index.search(query_vector, index.ntotal)
    filtered_results = [
        (dist, idx) for dist, idx in zip(distances[0], indices[0]) 
        if dist <= threshold and idx != -1
    ]
    filtered_results.sort(key=lambda x: x[0])
    top_results = filtered_results[:top_k]
    top_indices = [int(idx) for _, idx in top_results]
    return top_indices
