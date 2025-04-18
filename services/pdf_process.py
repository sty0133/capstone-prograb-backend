import os

from utils.google_cld_vision import detect_text_pdf_path
from utils.embedding_utils import load_and_retrieve_docs_sliding_window

from models.faiss.process import InsertVectors, SaveIndex
from models.faiss.process import PDFFAISS

from models.mongodb.mg_pdf_model import MongodbPDF

from models.mysql.my_pdf_model import MysqlPDF
from models.mysql.my_chat_model import MysqlChat

def pdf_process(file_paths, new_chat_id):
    pdf_faiss = PDFFAISS()

    # PDF 파일 OCR 처리 -> 리스트 반환
    texts = detect_text_pdf_path(file_paths)
    
    # OCR 처리된 텍스트 임베딩 -> 리스트 반환
    embedded_vectors, sentences = load_and_retrieve_docs_sliding_window(texts)

    # FAISS 인덱스 초기화 및 벡터 저장 -> 리스트 반환
    faiss_ids = InsertVectors.pdf(embedded_vectors, new_chat_id)

    # MongoDB에 PDF 정보 저장
    if len(sentences) != len(faiss_ids) or len(embedded_vectors) != len(faiss_ids):
        MysqlPDF.delete_pdf_by_chat_id(new_chat_id)
        MysqlChat.delete_chat(new_chat_id)
        return False, f"PDF 처리 중 오류 발생 chat_id: {new_chat_id}"
    

    for i in range(len(sentences)):

        pdf_data = {
            "chatID": new_chat_id,
            "faissID": faiss_ids[i],
            "text": sentences[i],
        }

        result, message = MongodbPDF.insert_document(pdf_data)
        if not result:
            return False, message
    
    # FAISS 인덱스 저장
    SaveIndex.pdf(new_chat_id)

    # 캐싱 데이터 삭제
    pdf_faiss.clear_cache(new_chat_id)

    # 사용된 PDF 파일 로컬에서 삭제
    for file_path in file_paths:
        try:
            os.remove(file_path)
        except Exception as e:
            print(f"Error deleting file {file_path}: {e}")
            
    return True, 1