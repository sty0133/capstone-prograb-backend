import asyncio
from concurrent.futures import TimeoutError
from asyncio import TimeoutError as AsyncTimeoutError

from models.mongodb.mongodb import *
from models.faiss.process import FindTopSimilarVectors

from utils.embedding_utils import embedding_model
from utils.openai_gpt import ChatGPT

def rag_chain(question):

    def remove_duplicates_preserve_order(lst):
        seen = set()
        result = []
        
        for item in lst:
            if item['docNo'] not in seen:
                seen.add(item['docNo'])
                result.append(item)
        
        return result
    # retrieved_docs = retrieve_docs(question)

    query_vector = embedding_model(question)

    faiss_ids = FindTopSimilarVectors.dcu(query_vector)   # 벡터 ID 가 추출된다.

    if not faiss_ids:
        return "질문을 구체적으로 해주세요."
    
    embedded_doc = EmbeddedVector.get_documents_by_faiss_ids(faiss_ids)
    docs = remove_duplicates_preserve_order(embedded_doc)
    find_docs = [MongodbNotice.find_document_by_doc_and_category(doc) for doc in docs]

    formatted_prompt = f"사용자 질문: {question}\n\n참고 문서: {find_docs}"

    async def async_function():
        try:
            chat_gpt = ChatGPT()
            response = await chat_gpt.get_response(formatted_prompt)
            return response
        except Exception as e:
            return "챗봇 응답 생성 중 오류가 발생했습니다"

    try:
        # 타임아웃 30초 설정하여 비동기 함수 실행
        response = asyncio.run(
            asyncio.wait_for(async_function(), timeout=30.0)
        )
    except (TimeoutError, AsyncTimeoutError):
        response = "요청 시간이 초과되었습니다. 잠시 후 다시 시도해주세요."
    except RuntimeError as e:
        if "Event loop is closed" in str(e):
            # 이벤트 루프가 이미 실행 중인 경우 처리
            try:
                loop = asyncio.get_event_loop()
                response = loop.run_until_complete(async_function())
            except Exception as inner_e:
                response = f"이벤트 루프 실행 중 오류가 발생했습니다: {str(inner_e)}"
    except Exception as e:
        response = f"예상치 못한 오류가 발생했습니다: {str(e)}"

    return response