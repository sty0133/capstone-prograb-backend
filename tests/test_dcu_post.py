import requests
from bs4 import BeautifulSoup

# 검색어를 Python 변수로 설정
search_order = "대구가톨릭대학교 임시직 직원 채용 공고(9월 1일부, 추가)"
# search_order_sanitized = (
#     search_order
#     .replace("<", "&lt;")
#     .replace(">", "&gt;")
#     .replace("#", "&#35;")
#     .replace("&", "&#38;")
#     .replace("(", "&#40;")
#     .replace(")", "&#41;")
# )

# POST 요청에 필요한 데이터 구성
data = {
    "mv_data": "",
    "search_item": "subject",  # 'subject' 또는 'content'로 변경 가능
    "search_order": search_order
}

# URL 설정
url = "https://www.cu.ac.kr/plaza/notice/notice"  # 실제 URL로 변경 필요

# POST 요청 보내기
response = requests.post(url, data=data)

# 응답 확인
if response.status_code == 200:
    soup = BeautifulSoup(response.text, 'html.parser')
    print(soup.prettify())  # HTML 응답 내용 출력
else:
    print(f"Error: {response.status_code}")
