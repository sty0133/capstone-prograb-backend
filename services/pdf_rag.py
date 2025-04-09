from models.mongodb.mongodb import *
from models.faiss.process import FindTopSimilarVectors

from utils.list_utils import *
from utils.embedding_utils import embedding_model

def rag_chain(question, pdf_group_id):
    if not pdf_group_id:
        return "pdf_group_id가 필요합니다."
    
    # retrieved_docs = retrieve_docs(question)
    query_vector = embedding_model(question)

    faiss_ids = FindTopSimilarVectors.pdf(query_vector, pdf_group_id)
    
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