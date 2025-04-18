from openai import OpenAI
import os

client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

def gpt_ping_test():
    # OpenAI API 키 설정

    # 테스트 메시지
    test_message = "안녕하세요! 이 메시지는 GPT와의 핑 테스트를 위한 메시지입니다."
    print("GPT 핑 테스트를 시작합니다...")

    # OpenAI API 호출
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "user", "content": test_message}
        ],
        temperature=0.1,
        max_tokens=50
    )

    # 응답 출력
    print("GPT 응답 성공!")
    print(f"응답 내용: {response}")

if __name__ == "__main__":
    gpt_ping_test()