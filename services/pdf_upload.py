import os
from werkzeug.utils import secure_filename
import unicodedata

# 사용자 정의 예외 클래스들
class PDFUploadError(Exception):
    """PDF 업로드 관련 기본 예외 클래스"""
    pass

class MaxFilesExceededError(PDFUploadError):
    """최대 파일 개수 초과 시 발생하는 예외"""
    def __init__(self):
        self.message = "최대 3개의 PDF 파일만 업로드할 수 있습니다."
        super().__init__(self.message)

class FileSizeExceededError(PDFUploadError):
    """파일 크기 초과 시 발생하는 예외"""
    def __init__(self, filename):
        self.message = f"파일 '{filename}'이(가) 5MB 크기 제한을 초과했습니다."
        super().__init__(self.message)

class InvalidFileTypeError(PDFUploadError):
    """PDF가 아닌 파일 업로드 시 발생하는 예외"""
    def __init__(self, filename):
        self.message = f"'{filename}' 파일은 PDF 형식이 아닙니다. PDF 파일만 업로드 가능합니다."
        super().__init__(self.message)

def sanitize_pdf_filename(filename):
    # 파일 확장자 분리
    name, ext = os.path.splitext(filename)

    # 확장자가 .pdf가 아닌 경우 예외 처리
    if ext.lower() != '.pdf':
        raise InvalidFileTypeError(filename)

    # 불필요한 확장자 제거 (.ppt, .hwp, .hwpx 등)
    invalid_extensions = [
        # 문서 및 오피스 파일
        '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx', '.hwp', '.hwpx', '.txt', '.rtf', '.odt',

        # 이미지
        '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.svg', '.tiff', '.webp', '.heic',

        # 오디오
        '.mp3', '.wav', '.flac', '.aac', '.ogg', '.m4a',

        # 비디오
        '.mp4', '.avi', '.mov', '.mkv', '.wmv', '.flv', '.webm',

        # 압축 파일
        '.zip', '.rar', '.7z', '.tar', '.gz', '.bz2',

        # 코드 및 실행파일
        '.exe', '.dll', '.msi', '.sh', '.bat', '.py', '.js', '.java', '.cpp', '.c', '.class',

        # 기타
        '.iso', '.bin', '.apk', '.dmg', '.csv', '.json', '.xml', '.yml'
    ]
    for invalid_ext in invalid_extensions:
        if invalid_ext in name.lower():
            name = name.lower().replace(invalid_ext, '')

    # 한글과 영숫자만 허용하고 나머지는 언더스코어로 변경
    name = unicodedata.normalize('NFKC', name)
    name = name.replace(' ', '_')  # 공백을 언더스코어로 변경
    name = ''.join(c for c in name if c.isalnum() or c in '-_')

    # 최종적으로 .pdf 확장자 추가
    return f"{name}.pdf"

def save_pdf_files(files):
    if len(files) > 3:
        raise MaxFilesExceededError()
    
    UPLOAD_FOLDER = './uploads/pdf'
    MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB in bytes
    
    # 업로드 디렉토리가 없으면 생성
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    
    file_names = []
    file_paths = []
    
    for file in files:
        # PDF 확장자 검사
        if not file.filename.lower().endswith('.pdf'):
            raise InvalidFileTypeError(file.filename)
            
        # 파일 크기 검사
        if len(file.read()) > MAX_FILE_SIZE:
            file.seek(0)
            raise FileSizeExceededError(file.filename)
        
        file.seek(0)
        
        try:
            file_name = sanitize_pdf_filename(file.filename)
        except InvalidFileTypeError as e:
            raise InvalidFileTypeError(f"Invalid file type for file: {file.filename}")
        
        file_names.append(file_name)

        file_path = os.path.join(UPLOAD_FOLDER, file_name)
        file_paths.append(file_path)
        file.save(file_path)
    
    return file_names, file_paths
