import asyncio

from models.mongodb.mg_dcu_model import MongodbEmbeddedVector, MongodbDCU
from models.faiss.process import FindTopSimilarVectors

from utils.embedding_utils import embedding_model
from utils.openai_gpt import ChatGPT

def dcu_rag_chain(question):

    def remove_duplicates_preserve_order(lst):
        seen = set()
        result = []
        
        for item in lst:
            if item['docNo'] not in seen:
                seen.add(item['docNo'])
                result.append(item)
        
        return result

    async def async_function():
        chat_gpt = ChatGPT()
        response = await chat_gpt.is_dcu_domain_question(question)
        if response:
            query_vector = embedding_model([question])

            faiss_ids = FindTopSimilarVectors.dcu(query_vector)   # 벡터 ID 가 추출된다.

            if not faiss_ids:
                return "질문을 구체적으로 해주세요."
            
            embedded_doc = MongodbEmbeddedVector.get_documents_by_faiss_ids(faiss_ids)
            docs = remove_duplicates_preserve_order(embedded_doc)
            find_docs = [MongodbDCU.find_document_by_doc_and_category(doc) for doc in docs]

            formatted_prompt = f"사용자 질문: {question}\n\참고자료: {find_docs}"
            response = await chat_gpt.get_response(formatted_prompt, 'dcu')
        else:
            response = await chat_gpt.get_response(question, 'dcu_default')
        return response

    try:
        response = asyncio.run(
            asyncio.wait_for(async_function(), timeout=30.0)
        )

    except asyncio.TimeoutError:
        response = "요청 시간이 초과되었습니다. 잠시 후 다시 시도해주세요."

    except RuntimeError as e:
        if "Event loop is closed" in str(e):
            try:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                response = loop.run_until_complete(async_function())
            except Exception as inner_e:
                response = f"이벤트 루프 실행 중 오류가 발생했습니다: {str(inner_e)}"
        else:
            response = f"실행 중 오류가 발생했습니다: {str(e)}"

    except Exception as e:
        response = f"예상치 못한 오류가 발생했습니다: {str(e)}"

    return response