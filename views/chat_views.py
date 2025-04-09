from flask import Blueprint, request, jsonify
from flask.views import MethodView

from services.chat_rag import *

chat = Blueprint('chat', __name__)

class RAG(MethodView):
    def post(self):
        data = request.get_json()
        if data is None:
            return 500
        
        question = data.get('question')
        if not question:
            return "Key question is required", 400

        response = rag_chain(question)
        return jsonify({"response": response}), 200

# 클래스 기반 뷰를 블루프린트에 등록
chat.add_url_rule('/rag', view_func=RAG.as_view('dcu_rag'))