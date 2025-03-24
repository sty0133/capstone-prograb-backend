import ollama
import os

from dotenv import load_dotenv
load_dotenv()

# 환경 변수에서 MongoDB 설정 읽기
oep = os.getenv('OllamaEndPoint')
# ocr 후처리 모델 초기화 함수
# https://github.com/ollama/ollama/issues/703 Ollama 0.0.0.0 Host
# https://huggingface.co/teddylee777/Llama-3-Open-Ko-8B-gguf/tree/main
def initialize_cor_processing_model():
    try:
        # 모델을 초기화하여 로드
        ollama.chat(
            model='Llama3.2_kr_ocr', 
            messages=[{
                        "role": "user",
                        "content": "모델 초기화"
                    }])

        print("LLM Model Ready")
        return
    except Exception as e:
        print(f"Model initialization failed: {e}")
        return "Model Initialization Failed"
    
# 사용자 질문 응답 모델
def llama_kr_model(text):
    # response = ollama.chat(
    #     model='Llama3.2_kr_ocr',
    #     messages=[{
    #                 "role": "user",
    #                 "content": text
    #             }])
    
    import requests
    data = {
        "model": "kr3b",
        "prompt": text
    }

    headers = {'Content-Type': 'application/json'}

    response = requests.post(oep, json=data, headers=headers)

    if response.status_code != 200:
        print("Error:", response.status_code, response.text)
        return None

    # 응답을 정제하여 하나의 문자열로 결합
    response_lines = response.text.split('\n')
    cleaned_response = ''.join([line.split('"response":"')[1].split('"')[0] for line in response_lines if '"response":"' in line])
    
    return cleaned_response

# OCR tesseract를 사용하여 이미지에서 텍스트 추출
import pytesseract
from PIL import Image
from io import BytesIO
import requests

def ocr_image(image_url):
    # 한국어 지원을 위해 https://github.com/tesseract-ocr/tessdata/blob/main/kor.traineddata 다운로드
    # cp kor.traineddata /usr/share/tesseract-ocr/4.00/tessdata/

    try:
        # 이미지 다운로드
        response = requests.get(image_url)
        response.raise_for_status()
        
        # 이미지 열기
        image = Image.open(BytesIO(response.content))
        
        # Tesseract를 사용하여 이미지에서 텍스트 추출
        text = pytesseract.image_to_string(image, lang='kor')
        
        return text
    except requests.RequestException as e:
        print(f"이미지를 다운로드하는데 실패했습니다: {e}")
        return None

#Google Vision API를 사용하여 이미지에서 텍스트 추출
# https://cloud.google.com/vision/docs/ocr?hl=ko#vision_text_detection-python Vison API 사용법
# https://cloud.google.com/sdk/docs/install?hl=ko gcloud CLI 설치 --> --dearmor
# https://console.cloud.google.com/flows/enableapi?apiid=vision.googleapis.com&hl=ko Enable the Vision API.
# https://cloud.google.com/iam/docs/keys-upload?hl=ko&_gl=1*1595isi*_ga*MTIxOTg1NTMzNS4xNzM1NTIzNzIx*_ga_WH2QY8WWF5*MTczNTYwNjk3Mi4yLjEuMTczNTYwODY3MC4zNy4wLjA. Enable the IAM API
# https://console.developers.google.com/billing/enable? Billing Enable
# https://cloud.google.com/vision/pricing?_gl=1*amxc7o*_up*MQ..&gclid=Cj0KCQiA1p28BhCBARIsADP9HrPvUATVhUKsDzdB4X86lZnL1Lutfkp03LHYj7bXc1BG4BI0iM_kPR8aAlUJEALw_wcB&gclsrc=aw.ds&hl=ko#prices  Vision API 가격
from google.cloud import vision
import layoutparser as lp
import os
from dotenv import load_dotenv

load_dotenv()

os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')

def detect_text_uri(url):
    image_path = "temp_image.jpg"
    # 이미지 다운로드 및 저장
    def download_image(url):
        response = requests.get(url)
        response.raise_for_status()  # URL 접근 실패 시 예외 발생
        with open(image_path, 'wb') as file:
            file.write(response.content)
    
    def process_ocr_text(texts):
        lines = []  # 각 줄을 저장할 리스트

        # 텍스트를 각 줄로 묶기
        current_line = []  # 현재 줄에 포함된 텍스트들을 저장할 리스트
        current_y = None  # 현재 줄의 y값

        for text in texts:
            # 텍스트의 y 좌표 추출
            vertices = text.bounding_poly.vertices
            y_coords = [vertex.y for vertex in vertices]
            average_y = sum(y_coords) / len(y_coords)  # y 좌표의 평균을 구하여 현재 줄을 결정

            # 같은 y값 범위 내에 있는 텍스트는 같은 줄로 묶음
            if current_y is None:
                current_y = average_y

            # y값이 비슷하면 같은 줄로 처리, 그렇지 않으면 새로운 줄 시작
            if abs(current_y - average_y) < 30:  # y좌표 차이가 12 이내일 때는 같은 줄로 취급
                current_line.append(text.description)
            else:
                # 이전 줄을 완료하고 새로운 줄로 시작
                lines.append(" ".join(current_line))
                current_line = [text.description]
                current_y = average_y

        # 마지막 줄 추가
        if current_line:
            lines.append(" ".join(current_line))

        return lines


    client = vision.ImageAnnotatorClient()

    # 이미지 다운로드
    download_image(url)

    try:
        # 다운로드한 이미지 파일 열기
        with open(image_path, "rb") as image_file:
            content = image_file.read()

        image = vision.Image(content=content)
        response = client.text_detection(image=image)

        texts = response.text_annotations

        if response.error.message:
            raise Exception(
                "{}\nFor more info on error messages, check: "
                "https://cloud.google.com/apis/design/errors".format(response.error.message)
            )
        
    finally:
        # 이미지 파일 삭제
        if os.path.exists(image_path):
            os.remove(image_path)
            
            lines = process_ocr_text(texts[1::])
            image_texts = ", ".join(lines)
            return image_texts