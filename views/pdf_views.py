import uuid

from flask import Blueprint, request, jsonify, g
from flask.views import MethodView

from services.pdf_upload import *
from services.pdf_process import pdf_process
from services.pdf_rag import pdf_rag_chain

from utils.decorators import validate_request, token_required

from models.mysql.my_pdf_model import MysqlPDF
from models.mysql.my_chat_model import MysqlChat
from models.mongodb.mg_user_model import MongodbUserChat

pdf = Blueprint('pdf', __name__)

class Upload(MethodView):
    @token_required
    def post(self):
        if 'files' not in request.files:
            return jsonify({"error": "PDF 파일이 요청에 포함되지 않았습니다."}), 400
        
        files = request.files.getlist('files')
        if not any(file.filename for file in files):
            return jsonify({"error": "선택된 파일이 없습니다."}), 400

        try:
            file_names, file_paths = save_pdf_files(files)

            if not file_names:
                return jsonify({
                    "status": "error",
                    "error": "invalid_file_type",
                    "message": "파일이 비어있습니다."
                }), 400

            # 중요한 로직은 try 블록 내에서 처리
            while True:
                new_chat_id = str(uuid.uuid4())
                if not MysqlChat.check_chat_id_exists(new_chat_id):
                    break

            user_id = g.user.get('user_id')
            result, message = MysqlChat.create_new_chat(user_id, new_chat_id)

            if result:
                result, message = MysqlPDF.insert_pdf_name(new_chat_id, file_names)
                if not result:
                    return jsonify({
                        "status": "error",
                        "error": "internal_server_error",
                        "message": message
                    }), 500

                result, message = MongodbUserChat.initialize_chat(new_chat_id)
                if not result:
                    return jsonify({
                        "status": "error",
                        "error": "internal_server_error",
                        "message": message
                    }), 500

            elif message == 'User not found':
                return jsonify({
                    "status": "error",
                    "error": "user_not_found",
                    "message": "사용자를 찾을 수 없습니다."
                }), 404

            # PDF 파일 처리
            result, message = pdf_process(file_paths, new_chat_id)
            if not result:
                return jsonify({
                    "status": "error",
                    "error": "internal_server_error",
                    "message": message
                }), 500

            return jsonify({
                "status": "success",
                "message": "파일 업로드 성공",
                "data": {
                    "file_names": file_names,
                    "file_count": len(file_names),
                    "chat_id": new_chat_id,
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

class RAG(MethodView):
    @token_required
    @validate_request(['chat_id', 'question'])
    def post(self):
        try:
            question = request.data['question']
            chat_id = request.data['chat_id']

            # RAG 체인 실행
            response = pdf_rag_chain(question, chat_id)

            # 에러 응답 처리
            if isinstance(response, str):
                if "요청 시간이 초과되었습니다" in response:
                    return jsonify({
                        "status": "error",
                        "message": response,
                        "error_code": "TIMEOUT_ERROR"
                    }), 504  # Gateway Timeout
                
                elif "이벤트 루프 실행 중 오류가 발생했습니다" in response:
                    return jsonify({
                        "status": "error",
                        "message": response,
                        "error_code": "EVENT_LOOP_ERROR"
                    }), 500
                
                elif "OpenAI API 오류가 발생했습니다" in response:
                    return jsonify({
                        "status": "error",
                        "message": response,
                        "error_code": "OPENAI_API_ERROR"
                    }), 503  # Service Unavailable
                
                elif "API 요청이 너무 많습니다" in response:
                    return jsonify({
                        "status": "error",
                        "message": response,
                        "error_code": "RATE_LIMIT_ERROR"
                    }), 429  # Too Many Requests
                
                elif "질문을 구체적으로 해주세요" in response:
                    return jsonify({
                        "status": "error",
                        "message": response,
                        "error_code": "INVALID_QUESTION"
                    }), 400
                elif "챗봇 응답 생성 중 오류가 발생했습니다" in response:
                    return jsonify({
                        "status": "error",
                        "message": response,
                        "error_code": "CHATBOT_RESPONSE_ERROR"
                    }), 400

            # 채팅 업데이트
            result, message = MongodbUserChat.update_chat_by_id(chat_id, question, response)
            if not result:
                return jsonify({
                    "status": "error",
                    "message": message,
                    "error_code": "CHAT_UPDATE_ERROR"
                }), 500
            
            # 정상 응답
            return jsonify({
                "status": "success",
                "message": "성공적으로 응답을 생성했습니다.",
                "data": {
                    "response": response
                }
            }), 200

        except Exception as e:
            # 예상치 못한 서버 에러
            return jsonify({
                "status": "error",
                "message": f"서버 내부 오류가 발생했습니다: {str(e)}",
                "error_code": "INTERNAL_SERVER_ERROR"
            }), 500
        
pdf.add_url_rule('/upload', view_func=Upload.as_view('pdf_upload'))
pdf.add_url_rule('/rag', view_func=RAG.as_view('pdf_rag'))