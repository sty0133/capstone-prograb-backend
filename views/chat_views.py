# import uuid

from flask import Blueprint, request, jsonify
from flask.views import MethodView

from services.chat_rag import *

from models.faiss.process import delete_pdf_faiss

from models.mysql.my_chat_model import MysqlChat
from models.mongodb.mg_pdf_model import MongodbPDF

from utils.decorators import validate_request

chat = Blueprint('chat', __name__)

class RAG(MethodView):
    def post(self):
        try:
            # 요청 데이터 검증
            data = request.get_json()
            if data is None:
                return jsonify({
                    "status": "error",
                    "message": "올바른 JSON 형식이 아닙니다.",
                    "error_code": "INVALID_JSON"
                }), 400
            
            question = data.get('question')
            if not question:
                return jsonify({
                    "status": "error",
                    "message": "질문이 입력되지 않았습니다.",
                    "error_code": "QUESTION_REQUIRED"
                }), 400

            # RAG 체인 실행
            response = dcu_rag_chain(question)

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
        
class List(MethodView):
    @validate_request(['user_id'])
    def get(self):
        # chat 조회
        user_id = request.data['user_id']
        result, data = MysqlChat.get_chat_list(user_id)

        if result:
            chat_list = [chat[0] for chat in data]
            return jsonify({
                "status": "success",
                "message": "채팅 목록 조회 성공",
                "data": {
                    "chat_list": chat_list
                }
            }), 200
        # 조회에 성공하였지만, 생성한 채팅이 없을 때
        elif data == 'No chats found':
            return jsonify({
                "status": "success",
                "message": "채팅 목록이 비어 있습니다.",
                "data": {
                    "chat_list": []
                }
            }), 200
        elif data == 'User not found':
            return jsonify({
                "status": "error",
                "error": "user_not_found",
                "message": data
            }), 404
        else:
            return jsonify({
                "status": "error",
                "error": "internal_server_error",
                "message": data
            }), 500
        return
    
    # @validate_request(['user_id'])
    # def post(self):
    #     # chat_id 생성
    #     while True:
    #         new_chat_id = str(uuid.uuid4())
    #         if not MysqlChat.check_chat_id_exists(new_chat_id):
    #             break

    #     user_id = request.data['user_id']
    #     result, data = MysqlChat.create_new_chat(user_id, new_chat_id)
        
    #     if result:
    #         return jsonify({
    #             "status": "success",
    #             "message": "채팅 ID 생성 성공",
    #             "data": {
    #                 "chat_id": new_chat_id
    #             }
    #         }), 200
    #     elif data == 'chat_id already exists':
    #         return jsonify({
    #             "status": "error",
    #             "error": "chat_id_already_exists",
    #             "message": "이미 존재하는 chat_id 입니다."
    #         }), 409
    #     elif data == 'User not found':
    #         return jsonify({
    #             "status": "error",
    #             "error": "user_not_found",
    #             "message": "사용자를 찾을 수 없습니다."
    #         }), 404
    #     else:
    #         return jsonify({
    #             "status": "error",
    #             "error": "chat_id_creation_failed",
    #             "message": "채팅 ID 생성 실패"
    #         }), 500
        
    @validate_request(['chat_id'])
    def delete(self):
        chat_id = request.data['chat_id']
        
        result_mysql, message_mysql = MysqlChat.delete_chat(chat_id)
        result_mongodb, message_mongodb = MongodbPDF.delete_document_by_chat_id(chat_id)

        if result_mysql and result_mongodb:
            return jsonify({
                "status": "success",
                "message": "채팅 삭제 성공"
            }), 200
        elif not result_mysql:
            return jsonify({
                "status": "error",
                "error": "mysql_error",
                "message": message_mysql
            }), 500
        elif not result_mongodb:
            return jsonify({
                "status": "error",
                "error": "mongodb_error",
                "message": message_mongodb
            }), 500
        else:
            return jsonify({
                "status": "error",
                "error": "unknown_error",
                "message": "알 수 없는 오류가 발생했습니다."
            }), 500

chat.add_url_rule('/rag', view_func=RAG.as_view('dcu_rag'))
chat.add_url_rule('/list', view_func=List.as_view('chat_list'))