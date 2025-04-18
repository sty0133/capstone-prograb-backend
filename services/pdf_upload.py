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

def secure_filename_with_hangul(filename):
    """한글 파일명을 안전하게 처리하는 함수"""
    # 파일 확장자 분리
    name, ext = os.path.splitext(filename)
    
    # 한글과 영숫자만 허용하고 나머지는 언더스코어로 변경
    name = unicodedata.normalize('NFKC', name)
    
    # 공백을 언더스코어로 변경
    name = name.replace(' ', '_')
    
    # 허용된 문자만 포함
    name = ''.join(c for c in name if c.isalnum() or c in '-_.')
    
    return name + ext

def save_pdf_files(files):
    """
    PDF 파일들을 저장하는 함수
    
    Args:
        files: 업로드된 파일 객체들의 리스트
    
    Returns:
        저장된 파일 경로들의 리스트
    
    Raises:
        MaxFilesExceededError: 파일 개수가 3개를 초과할 때
        FileSizeExceededError: 파일 크기가 5MB를 초과할 때
        InvalidFileTypeError: PDF 파일이 아닐 때
    """
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
        
        file_name = secure_filename_with_hangul(file.filename)
        file_names.append(file_name)

        file_path = os.path.join(UPLOAD_FOLDER, file_name)
        file_paths.append(file_path)
        file.save(file_path)
    
    return file_names, file_paths
