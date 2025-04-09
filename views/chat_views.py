from flask import Blueprint, request, jsonify
from flask.views import MethodView

from services.chat_rag import *

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
            response = rag_chain(question)

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

# 클래스 기반 뷰를 블루프린트에 등록
chat.add_url_rule('/rag', view_func=RAG.as_view('dcu_rag'))