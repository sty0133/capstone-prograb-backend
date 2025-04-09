from flask import Blueprint, request, jsonify
from flask.views import MethodView
from services.pdf_upload import *
from models.faiss.initialize import PDFFAISS
from models.faiss.process import delete_pdf_faiss
import uuid

pdf = Blueprint('pdf', __name__, url_prefix='/pdf')

class Upload(MethodView):
    def post(self):
        if 'files' not in request.files:
            return jsonify({"error": "PDF 파일이 요청에 포함되지 않았습니다."}), 400
        
        files = request.files.getlist('files')
        
        # 파일이 선택되지 않은 경우 체크
        if not any(file.filename for file in files):
            return jsonify({"error": "선택된 파일이 없습니다."}), 400
        
        try:
            saved_paths = save_pdf_files(files)
            return jsonify({
                "status": "success",
                "message": "파일 업로드 성공",
                "data": {
                    "saved_paths": saved_paths,
                    "file_count": len(saved_paths)
                }
            }), 200
            
        except MaxFilesExceededError as e:
            return jsonify({
                "status": "error",
                "error": "max_files_exceeded",
                "message": str(e)
            }), 400
        except FileSizeExceededError as e:
            return jsonify({
                "status": "error",
                "error": "file_size_exceeded",
                "message": str(e)
            }), 400
        except InvalidFileTypeError as e:
            return jsonify({
                "status": "error",
                "error": "invalid_file_type",
                "message": str(e)
            }), 400
        except Exception as e:
            return jsonify({
                "status": "error",
                "error": "internal_server_error",
                "message": "파일 업로드 중 오류가 발생했습니다."
            }), 500

class List(MethodView):
    def get(self):
        # Mysql 에 자장된 유저 pdf uuid 조회
        return
    
    def post(self):
        # 새로운 pdf group id 생성
        pdf_group_id = str(uuid.uuid4())
        # Mysql에 pdf_group_id 저장
        
        pdf_faiss = PDFFAISS()
        pdf_faiss.initialize(pdf_group_id)
        
        return jsonify({
            "status": "success",
            "message": "PDF 그룹 ID 생성 성공",
            "data": {
                "pdf_group_id": pdf_group_id
            }
        }), 200
    
    def delete(self):
        # PDF 그룹 ID 검증 필요
        pdf_group_id = request.json.get('pdf_group_id')
        if not pdf_group_id:
            return jsonify({"error": "PDF 그룹 ID가 필요합니다"}), 400
        
        # Mysql에서 pdf_group_id 삭제
        try:
            delete_pdf_faiss(pdf_group_id)
            return jsonify({
                "status": "success",
                "message": "PDF 그룹 ID 삭제 성공"
            }), 200
        except Exception as e:
            return jsonify({"error": "PDF 그룹 ID 삭제 중 오류가 발생했습니다."}), 500
        
pdf.add_url_rule('/upload', view_func=Upload.as_view('pdf_upload'))
pdf.add_url_rule('/list', view_func=List.as_view('pdf_list'))