import numpy as np
import faiss
import os

from .initialize import PDFFAISS
from . import dcu_index, dcu_faiss_path

class InsertVectors:
    def dcu(vectors):
        vectors = np.array(vectors).astype('float32')

        dcu_index.add(vectors)

        faiss_ids = list(range(dcu_index.ntotal - len(vectors), dcu_index.ntotal))
        print(f"Added {len(vectors)} vectors to dcu. Total vectors: {dcu_index.ntotal}")
        return faiss_ids
    
    def pdf(vectors, pdf_group_id):
        vectors = np.array(vectors).astype('float32')

        if pdf_group_id:
            pdf_faiss = PDFFAISS()
            index = pdf_faiss.initialize(pdf_group_id)
        else:
            raise ValueError("pdf_group_id is required for PDF service.")
        
        index.add(vectors)

        faiss_ids = list(range(index.ntotal - len(vectors), index.ntotal))
        print(f"Added {len(vectors)} vectors to pdf id {pdf_group_id}. Total vectors: {index.ntotal}")
        return faiss_ids

class FindTopSimilarVectors:
    def dcu(query_vector, top_k=3, threshold=1.5):
        # 인덱스가 비어있는지 확인
        if dcu_index.ntotal == 0:
            print("No vectors in the index.")
            return []
        
        if query_vector is None:
            return []
        
        query_vector = np.array(query_vector).reshape(1, -1).astype('float32')
        
        distances, indices = dcu_index.search(query_vector, min(top_k * 2, dcu_index.ntotal))
        
        filtered_results = [
            (dist, idx) for dist, idx in zip(distances[0], indices[0]) 
            if dist <= threshold and idx != -1
        ]
        filtered_results.sort(key=lambda x: x[0])
        top_results = filtered_results[:top_k]
        top_indices = [int(idx) for _, idx in top_results]
        return top_indices
    
    def pdf(query_vector, pdf_group_id, top_k=3, threshold=1.5):
        if not pdf_group_id or not query_vector:
            return []
        
        pdf_faiss = PDFFAISS()
        index = pdf_faiss.initialize(pdf_group_id)
            
        query_vector = np.array(query_vector).reshape(1, -1).astype('float32')
        
        distances, indices = index.search(query_vector, min(top_k * 2, index.ntotal))
        
        filtered_results = [
            (dist, idx) for dist, idx in zip(distances[0], indices[0]) 
            if dist <= threshold and idx != -1
        ]
        filtered_results.sort(key=lambda x: x[0])
        top_results = filtered_results[:top_k]
        top_indices = [int(idx) for _, idx in top_results]
        return top_indices
    
# 메모리에 인덱스 저장 방법
# chunk = faiss.serialize_index(index) 

class SaveIndex:
    def dcu():
        try:
            faiss.write_index(dcu_index, dcu_faiss_path)
            print(f"DCU FAISS saved. Total vectors: {dcu_index.ntotal}")
        except Exception as e:
            print(f"Error saving DCU FAISS: {e}")

    # def pdf(pdf_group_id):
    #     pdf_faiss = PDFFAISS()
    #     pdf_faiss.save(pdf_group_id, index)

def delete_pdf_faiss(pdf_group_id):
    index_path = PDFFAISS.get_index_path(pdf_group_id)
    if os.path.exists(index_path):
        os.remove(index_path)
    else:
        print(f"PDF FAISS index for group '{pdf_group_id}' does not exist.")