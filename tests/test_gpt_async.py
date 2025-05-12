import asyncio
from concurrent.futures import TimeoutError
from asyncio import TimeoutError as AsyncTimeoutError

from utils.openai_gpt import ChatGPT

formatted_prompt = """"""

async def async_function():
    chat_gpt = ChatGPT()
    return await chat_gpt.get_response(formatted_prompt)

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

print(response)