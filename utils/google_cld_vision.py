# from PIL import Image
# from io import BytesIO

# import pytesseract
# OCR tesseract를 사용하여 이미지에서 텍스트 추출
# def ocr_image(image_url):
#     # 한국어 지원을 위해 https://github.com/tesseract-ocr/tessdata/blob/main/kor.traineddata 다운로드
#     # cp kor.traineddata /usr/share/tesseract-ocr/4.00/tessdata/

#     try:
#         # 이미지 다운로드
#         response = requests.get(image_url)
#         response.raise_for_status()
        
#         # 이미지 열기
#         image = Image.open(BytesIO(response.content))
        
#         # Tesseract를 사용하여 이미지에서 텍스트 추출
#         text = pytesseract.image_to_string(image, lang='kor')
        
#         return text
#     except requests.RequestException as e:
#         print(f"이미지를 다운로드하는데 실패했습니다: {e}")
#         return None

#Google Vision API를 사용하여 이미지에서 텍스트 추출
# https://cloud.google.com/vision/docs/ocr?hl=ko#vision_text_detection-python Vison API 사용법
# https://cloud.google.com/sdk/docs/install?hl=ko gcloud CLI 설치 --> --dearmor
# https://console.cloud.google.com/flows/enableapi?apiid=vision.googleapis.com&hl=ko Enable the Vision API.
# https://cloud.google.com/iam/docs/keys-upload?hl=ko&_gl=1*1595isi*_ga*MTIxOTg1NTMzNS4xNzM1NTIzNzIx*_ga_WH2QY8WWF5*MTczNTYwNjk3Mi4yLjEuMTczNTYwODY3MC4zNy4wLjA. Enable the IAM API
# https://console.developers.google.com/billing/enable? Billing Enable
# https://cloud.google.com/vision/pricing?_gl=1*amxc7o*_up*MQ..&gclid=Cj0KCQiA1p28BhCBARIsADP9HrPvUATVhUKsDzdB4X86lZnL1Lutfkp03LHYj7bXc1BG4BI0iM_kPR8aAlUJEALw_wcB&gclsrc=aw.ds&hl=ko#prices  Vision API 가격
from google.cloud import vision
import requests
import os
from google.cloud import storage
import json

os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')

def detect_text_image_url(url):
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
        
def detect_text_pdf_path(pdf_paths: list):
    """
    로컬 PDF 파일들을 OCR 처리하는 함수
    
    Args:
        pdf_paths: PDF 파일 경로들의 리스트 (예: ["/path/to/file1.pdf", "/path/to/file2.pdf"])
    
    Returns:
        모든 PDF에서 추출된 텍스트를 하나의 문자열로 반환
    """
    client = vision.ImageAnnotatorClient()
    bucket_name = "prograb-bucket"
    storage_client = storage.Client()
    
    try:
        bucket = storage_client.get_bucket(bucket_name)
    except Exception:
        bucket = storage_client.create_bucket(bucket_name)
    
    all_texts = []  # 모든 PDF의 텍스트를 저장할 리스트
    
    # 각 PDF 파일 처리
    for pdf_path in pdf_paths:
        if not isinstance(pdf_path, (str, bytes, os.PathLike)):
            print(f"잘못된 파일 경로 형식: {pdf_path}")
            continue
            
        file_name = os.path.basename(pdf_path)
        print(f"처리 중인 파일: {file_name}")
        
        source_blob_name = f"temp_pdf/{file_name}"
        output_prefix = f"temp_pdf/output_{file_name}"
        
        try:
            # 로컬 PDF를 GCS에 업로드
            blob = bucket.blob(source_blob_name)
            blob.upload_from_filename(pdf_path)
            
            # GCS URI 생성
            gcs_source_uri = f"gs://{bucket_name}/{source_blob_name}"
            gcs_destination_uri = f"gs://{bucket_name}/{output_prefix}/"
            
            # OCR 설정
            feature = vision.Feature(type_=vision.Feature.Type.DOCUMENT_TEXT_DETECTION)
            gcs_source = vision.GcsSource(uri=gcs_source_uri)
            input_config = vision.InputConfig(
                gcs_source=gcs_source, 
                mime_type="application/pdf"
            )
            gcs_destination = vision.GcsDestination(uri=gcs_destination_uri)
            output_config = vision.OutputConfig(
                gcs_destination=gcs_destination, 
                batch_size=2
            )
            
            # OCR 요청 실행
            async_request = vision.AsyncAnnotateFileRequest(
                features=[feature],
                input_config=input_config,
                output_config=output_config
            )
            
            operation = client.async_batch_annotate_files(requests=[async_request])
            print(f"OCR 처리 중: {file_name}")
            operation.result(timeout=420)
            
            # 결과 파일 가져오기
            blobs = list(bucket.list_blobs(prefix=output_prefix))
            
            for result_blob in blobs:
                if result_blob.name.endswith(".json"):
                    json_string = result_blob.download_as_bytes().decode("utf-8")
                    response = json.loads(json_string)
                    
                    for page_response in response.get("responses", []):
                        if "fullTextAnnotation" in page_response:
                            text = page_response["fullTextAnnotation"]["text"]
                            all_texts.append(text)
            
        except Exception as e:
            print(f"파일 처리 중 오류 발생 ({file_name}): {str(e)}")
        
        finally:
            # 임시 파일 정리
            try:
                bucket.blob(source_blob_name).delete()
                for blob in bucket.list_blobs(prefix=output_prefix):
                    blob.delete()
            except Exception as e:
                print(f"임시 파일 삭제 중 오류: {str(e)}")
    
    # 모든 텍스트를 하나의 문자열로 합쳐서 반환
    return "\n\n".join(all_texts)   # PDF 텍스트 OCR은 이미지 OCR과 달리 텍스트 좌표가 없음.