import asyncio

from models.mongodb.mg_pdf_model import MongodbPDF
from models.faiss.process import FindTopSimilarVectors

from utils.embedding_utils import embedding_model
from utils.openai_gpt import ChatGPT

def pdf_rag_chain(question, chat_id):

    async def async_function():
        chat_gpt = ChatGPT()
        response = await chat_gpt.is_pdf_question(question)
        if response:
            query_vector = embedding_model([question])

            faiss_ids = FindTopSimilarVectors.pdf(query_vector, chat_id)   # 벡터 ID 가 추출된다.

            if not faiss_ids:
                return "질문을 구체적으로 해주세요."
            
            find_docs = MongodbPDF.find_documents_by_faiss_ids(faiss_ids)

            formatted_prompt = f"사용자 질문: {question}\n참고자료: {find_docs}"
            response = await chat_gpt.get_response(formatted_prompt, 'pdf')
        else:
            response = await chat_gpt.get_response(question, 'pdf_default')
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