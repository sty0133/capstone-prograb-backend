import requests
import time
from bs4 import BeautifulSoup

from utils.google_cld_vision import *
from utils.date_utils import *
from utils.text_utils import *
from utils.embedding_utils import *

from models.mongodb.mg_dcu_model import *
from models.faiss.process import InsertVectors, SaveIndex

base_url = 'https://www.cu.ac.kr'

# FAISS_INDEX_DCU_PATH = os.getenv('FAISS_INDEX_DCU_PATH')

def make_full_url(url):
    valid_starts = ["https://www.cu.ac.kr", "http://www.cu.ac.kr", "https://cu.ac.kr", "http://cu.ac.kr"]
    if any(url.startswith(start) for start in valid_starts):
        return url
    else:
        return base_url + url
                    
class CrawlingNotice:
    # 공지 데이터 포멧
    @staticmethod
    def format_notice_data(doc_no, url, title, date, author, views, images, image_text_conv, attachments, content_text, category):
        formated_notice = {
                "docNo": doc_no,
                "rawTitle": title,
                "rawContent": content_text if content_text else "",
                "images": {
                    "rawText":image_text_conv if image_text_conv else "",
                    "urls": images
                },
                "attachments": attachments if attachments else [],
                "info": {
                    "author": author,
                    "date": date,
                    "views": views,
                    "url": url
                }
            }
        
        return formated_notice
    @staticmethod
    def format_embedded_data(doc_no, category, title, content_text, image_text_conv):
        all_contents = title + content_text + image_text_conv
        embedded_vector, _ = load_and_retrieve_docs_sliding_window(all_contents)
        faiss_ids = InsertVectors.dcu(embedded_vector)

        formated_embed = {
            "docNo": doc_no,
            "category": category,
            "faissID": faiss_ids,
        }
        
        return formated_embed

    # 공지안에 카테고리가 " 공지"인 경우 해당 공지 링크 추출
    def get_notice_links(self, url):
        try:
            # 페이지 요청
            response = requests.get(url)
            response.raise_for_status()
            
            # BeautifulSoup 객체 생성
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # 클래스가 'notice'인 모든 a 태그 찾기
            notice_links = []
            a_tags = soup.find_all('a', class_='notice')
            for a_tag in a_tags:
                if 'href' in a_tag.attrs:
                    notice_links.append(base_url + a_tag['href'])

            return notice_links
        except requests.RequestException as e:
            print(f"페이지를 요청하는데 실패했습니다: {e}")
            return []

    # 가장 첫 일반공지 링크 추출
    def get_first_normal_notice_link(self, url):
        try:
            # 페이지 요청
            response = requests.get(url)
            response.raise_for_status()
            
            # BeautifulSoup 객체 생성
            soup = BeautifulSoup(response.content, 'html.parser')

            board_list_div = soup.find('div', class_='board_list')
            if not board_list_div:
                print("클래스명이 'board_list'인 div를 찾을 수 없습니다.")
                return []

            table = board_list_div.find('table')
            if not table:
                print("table 요소를 찾을 수 없습니다.")
                return []

            tbody = table.find('tbody')
            if not tbody:
                print("tbody 요소를 찾을 수 없습니다.")
                return []
            
            rows = tbody.find_all('tr')
            for row in rows:
                first_td = row.find_all('td')[0]
                if first_td and first_td.text != " 공지":       # 공지가 아닌 일반공지만 추출
                    second_td = row.find_all('td')[1]
                    if second_td:
                        a_tag = second_td.find('a')
                        if a_tag and 'href' in a_tag.attrs:
                            first_notice_url = base_url + a_tag['href']
                            return first_notice_url
        
        except requests.RequestException as e:
            print(f"페이지를 요청하는데 실패했습니다: {e}")
            
    def crawl(self, url, category="notice", visited=[], is_notice=False):
        global doc_no, max_crawl_mount, count_crawl_mount, check_point
        try:
            response = requests.get(url)
            response.raise_for_status()
        except requests.RequestException as e:
            print(f"{url}을(를) 가져오는데 실패했습니다: {e}")
            return
        
        # BeautifulSoup 객체 생성
        soup = BeautifulSoup(response.text, 'html.parser')

        if not check_point:
            # 이미 방문한 URL인 경우 종료
            if url in visited:
                print('-' * 80,f"\n{category} 카테고리에서 방문한 URL 터치.\n터치한 URL : {url}\n", '-' * 80)
                return
            
            # 크롤링한 공지 개수가 설정한 개수를 넘으면 종료
            if count_crawl_mount >= max_crawl_mount:
                return

            # 클래스명이 'board'인 div 태그의 내용 추출
            board_divs = soup.find_all('div', class_='board')
            for board_div in board_divs:
                # 제목 추출
                title_tag = board_div.find('h6')  
                title = title_tag.text.strip() if title_tag else None

                # 작성일, 작성자, 조회수 추출
                info_div = board_div.find('div', class_='view_info')
                info_items = info_div.find_all('span') if info_div else []

                date = info_items[0].contents[-1].strip() if len(info_items) > 0 else None

                if date:
                    date = convert_to_iso(date)

                    # 2024년 1월 1일 이전의 데이터는 수집 안함
                    date_obj = datetime.fromisoformat(date)
                    if date_obj < datetime(2024, 1, 1):
                        print(f"{category} 카테고리에서 2024년 1월 1일 이전의 데이터 터치.")
                        return

                author = remove_whitespace_patterns(info_items[1].contents[-1].strip().replace(": ", "")) if len(info_items) > 1 else None  # ": 교육인사팀" 형식으로 나오는것을 수정
                views = info_items[2].contents[-1].strip().replace(": ", "") if len(info_items) > 2 else None  # ": 1506" 형식으로 나오는것을 수정

                # views가 숫자인지 확인하고 정수로 변환
                if views and views.isdigit():
                    views = int(views)
                else:
                    views = None

                # 이미지 URL 추출 (존재할 때만)
                global image_text_conv, images
                images = []
                image_text_conv = ''

                image_div_view_images = board_div.find('div', class_='view_images')
                image_div_se_contents = board_div.find('div', class_='se-contents')

                def process_images(image_div):
                    global image_text_conv, images, count_ocr_mount
                    if image_div:
                        image_tags = image_div.find_all('img')
                        for image_tag in image_tags:
                            if 'src' in image_tag.attrs:
                                image_url = image_tag['src']
                                image_url = make_full_url(image_url)
                                image_text = detect_text_image_url(image_url)
                                image_text_conv += image_text
                                images.append(image_url)

                                # Gcloud OCR 사용 횟수 카운트
                                count_ocr_mount += 1

                # 이미지 처리
                process_images(image_div_view_images)
                process_images(image_div_se_contents)

                # OCR 결과가 존재할시 텍스트 보완
                if len(image_text_conv) > 0:
                    image_text_conv = remove_whitespace_patterns(image_text_conv)

                # 첨부파일 링크 및 파일명 추출 (존재할 때만)
                attachments = []
                attach_div = board_div.find('ul', class_='attach')
                if attach_div:
                    attachment_items = attach_div.find_all('a')
                    for attachment in attachment_items:
                        attachment_url = attachment['href']
                        attachment_url = base_url + attachment_url
                        attachment_name = attachment.text.strip()
                        attachments.append({'name': attachment_name, 'url': attachment_url})

                # 내용 추출 (존재할 때만)
                content_text = None
                content_div = board_div.find('div', class_='view_content')
                if content_div:
                    count_crawl_mount += 1

                    print("-" * 80)
                    print(f"문서 번호: {doc_no}")
                    print(f"카테고리: {category}")
                    print(f"제목: {title}")
                    print(f"날짜: {date}")
                    print(f"공지: {is_notice}")
                    print(f"Gcloud Vision API 사용 횟수: {count_ocr_mount}")
                    print(f"진행된 크롤링 개수: {count_crawl_mount}")
                    print(f"목표까지 남은 크롤링 개수: {max_crawl_mount - count_crawl_mount}")
                    print("-" * 80)
                    
                    content_text = content_div.text.strip()
                    content_text = remove_whitespace_patterns(content_text)

                    document = self.format_notice_data(doc_no, url, title, date, author, views, images, image_text_conv, attachments, content_text, category)
                    embedded = self.format_embedded_data(doc_no, category, title, content_text, image_text_conv)

                    flag_doc = MongodbDCU.insert_document(document)
                    flag_emb = MongodbEmbeddedVector.insert_document(embedded)

                    if flag_doc and flag_emb:
                        doc_no += 1
                        visited.append(url)
                        SaveIndex.dcu()

                    else: return

        if is_notice: return

        # CSS 선택자를 사용하여 href 추출, 해당 선택자는 다음 페이지를 가르킨다
        element = soup.select_one('#main_contents > div.layout > div > div > div.board_list_nav > ul > li:nth-child(2) > a')

        if element:
            href_url = element.get('href')
            if href_url != '#':
                next_url = make_full_url(href_url)

                # 체크포인트 한번 쓰고 파기
                if check_point:
                    check_point = None
                else:
                    time.sleep(20)

                self.crawl(next_url, category, visited)
            elif href_url == '#':
                print("다음 페이지 선택자가 없습니다.")
                '''
                크롤링 도중 다음페이지가 존재하는데 없다고 뜰 때 크롬으로 접속하여 검색란에 제목 입력
                검색 결과에서 제목을 기반으로 href 추출하여 다음 페이지로 이동
                '''

                title = MongodbDCU.get_document_title_by_url(url)

                if not title:
                    check_point = None
                    print("URL 기반 제목 추출 실패.\n")
                    return
                    
                # search_order_sanitized = (
                #     title
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
                    "search_item": "subject",
                    "search_order": title
                }

                # POST 요청 보내기
                response = requests.post(sub_notice_url, data=data)

                # 응답 확인
                if response.status_code == 200:
                    soup = BeautifulSoup(response.text, 'html.parser')
                    cleaned_search_text = title.replace(" ", "")
                    a_tag = soup.find('a', string=lambda text: text and cleaned_search_text in text.replace(" ", ""))

                    if a_tag:
                        href_url = a_tag.get('href')
                        href_url = make_full_url(href_url)
                    else:
                        print("다음 페이지 선택자가 없고, 검색 결과도 없습니다.")
                        return

                else:
                    print(f"Error: {response.status_code}")
                    exit()

                if href_url:
                    check_point = 'True'
                    self.crawl(href_url, category, visited)
                return
        else:     
            print("잘못된 URL로 진입하였거나, 다음 페이지 선택자가 존재하지 않음.")
            print(f"URL: {url}")
            print(f"document number: {doc_no}")
            exit()

# class CrawlingElse:
#     @staticmethod
#     def format_embedded_data(doc_no, category, title, content_text, image_text_conv):
#         all_contents = title + content_text + image_text_conv
#         embedded_vector = load_and_retrieve_docs_sliding_window(all_contents)
#         faiss_ids = instert_vectors(embedded_vector)

#         formated_embed = {
#             "docNo": doc_no,
#             "category": category,
#             "faissID": faiss_ids,
#         }
        
#         return formated_embed

class StartCrawling:
    def notice():
        global max_crawl_mount, count_crawl_mount, count_ocr_mount
        count_ocr_mount = 0

        while True:
            start_time = time.time()

            while True:
                user_input = input("크롤링할 공지 개수를 입력하세요(0 입력시 종료): ")
                try:
                    max_crawl_mount = int(user_input)
                    if max_crawl_mount > 0:
                        break
                    elif max_crawl_mount == 0:
                        print("Good Bye!")
                        exit()
                    else:
                        print("0보다 큰 수를 입력하세요.")
                except ValueError:
                    print("숫자로 입력해 주세요.")

            count_crawl_mount = 0

            # 공지 종류
            notice_list = [
                ["notice","https://www.cu.ac.kr/plaza/notice/notice"],  # 공지사항 - 공지사항
                ["lesson","https://www.cu.ac.kr/plaza/notice/lesson"],  # 공지사항 - 학사공지(수업/학적)
                ["scholarship","https://www.cu.ac.kr/plaza/notice/scholarship"],  # 공지사항 - 장학공지
                ["program","https://www.cu.ac.kr/plaza/notice/program"],  # 공지사항 - 진로·취업공지
                ["service","https://www.cu.ac.kr/plaza/notice/service"],  # 공지사항 - 봉사공지
                ["recruit","https://www.cu.ac.kr/plaza/notice/recruit"],  # 공지사항 - 채용정보
                ["iu_research","https://www.cu.ac.kr/plaza/notice/iu_research"],  # 공지사항 - 산학연구공지
                ["recruitment","https://www.cu.ac.kr/plaza/notice/recruitment"],  # 공지사항 - 교내모집공지
                ["event","https://www.cu.ac.kr/plaza/notice/event"],  # 공지사항 - 교외소식
            ]

            # MongoDB에 저장된 모든 URL 가져오기
            visited = MongodbDCU.get_all_urls()

            # 각 notice_list의 URL로 시작하는 visited URL을 추가
            for notice in notice_list:
                url_prefix = notice[1]
                matching_urls = [url for url in visited if url.startswith(url_prefix)]
                notice.append(matching_urls)

            # 문서 번호 조회
            global doc_no
            doc_no = int(MongodbDCU.get_max_doc_no()) + 1

            global check_point
            check_point = MongodbDCU.get_latest_document_url()
            start_index = 0

            if check_point:
                # check_point가 리스트 안에 공지 종류 중 어떤 URL로 시작하는지 파악
                for i, notice in enumerate(notice_list):
                    if check_point.startswith(notice[1]):
                        start_index = i
                        break                    

            # 크롤링 시작
            crawling_notice_instance = CrawlingNotice()
            for info in notice_list[start_index:]:
                
                # 크롤링한 공지 개수가 설정한 개수를 넘으면 종료
                if count_crawl_mount >= max_crawl_mount:
                    break
                
                global sub_notice_url
                category = info[0]
                sub_notice_url = info[1]
                visited = info[2]

                start_index = 0

                # 페이지에 " 공지"가 있는지 확인하고, 크롤링
                notice_notice = crawling_notice_instance.get_notice_links(sub_notice_url)

                # 체크포인트가 있을 시 " 공지" 에 체크포인트가 존재하는건지 파악
                if notice_notice and check_point:
                    for i, notice in enumerate(notice_notice):
                        if check_point == notice:
                            start_index = i

                            if start_index < len(notice_notice):
                                print(f"체크포인트가 {category} 카테고리의 공지 안에 존재함.\n{len(notice_notice) - start_index}개의 공지 크롤링 시작")
                                for notice_link in notice_notice[start_index:]:
                                    crawling_notice_instance.crawl(notice_link, category, visited, True)
                            else: break # 체크포인트가 마지막 공지일 경우 종료

                    print(f"체크포인트부터 {category} 카테고리의 일반공지 크롤링 시작")
                    crawling_notice_instance.crawl(check_point, category, visited)
                    continue

                # 체크포인트가 없을 시
                elif notice_notice and not check_point:
                    print(f"{category} 카테고리의 공지 크롤링 시작")
                    for notice_link in notice_notice:
                        crawling_notice_instance.crawl(notice_link, category, visited, True)

                    # 일반공지 크롤링
                    print(f"{category} 카테고리의 일반공지 크롤링 시작")
                    start_url = crawling_notice_instance.get_first_normal_notice_link(sub_notice_url)
                    crawling_notice_instance.crawl(start_url, category, visited)

                else: 
                    print(f"{category} 카테고리의 공지 및 체크포인트가 존재하지 않습니다.\n {category} 카테고리의 일반공지 크롤링 시작")
                    start_url = crawling_notice_instance.get_first_normal_notice_link(sub_notice_url)
                    crawling_notice_instance.crawl(start_url, category, visited)

            print(f"{max_crawl_mount}개 크롤링 완료")

            end_time = time.time()
            elapsed_time = end_time - start_time

            hours, remainder = divmod(elapsed_time, 3600)
            minutes, seconds = divmod(remainder, 60)
            print(f"{int(hours)}시간 {int(minutes)}분 {int(seconds)}초 소요")

if __name__ == "__main__":

    # 공지 크롤링 시작
    StartCrawling.notice()