from flask import Flask, request
# from flask_socketio import SocketIO, emit
from flask_cors import CORS

# import ollama
import os

def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')

    from views import bot_views
    app.register_blueprint(bot_views.pdf, url_prefix='/pdf')
    app.register_blueprint(bot_views.chat, url_prefix='/chat')

    return app

if __name__ == "__main__":
    app = create_app()
    CORS(app)

    app.run(debug = True, port = 8080, host = '0.0.0.0')

# socketio = SocketIO(app, cors_allowed_origins="*")
# # 모델 초기화 함수
# def initialize_model():
#     model = 'Llama3.2_kr'  # 사용할 모델 이름
#     try:
#         # 모델을 초기화하여 로드
#         ollama.chat(model=model, messages=[{'role': 'user', 'content': 'Initializing...'}])
#         return "LLM Model Ready"
#     except Exception as e:
#         print(f"Model initialization failed: {e}")
#         return "Model Initialization Failed"

# # 모델 초기화 호출
# model_status = initialize_model()
# print(model_status)  # 모델 초기화 상태 출력

# def interact_with_model(prompt):
#     stream = ollama.chat(
#         model='Llama3.2_kr',
#         messages=[{'role': 'user', 'content': prompt}],
#         stream=True,
#     )

#     # 스트림 응답을 실시간으로 출력
#     for response in stream:
#         print(response['message']['content'], end='', flush=True)
#         emit('output_text', {'output': response['message']['content']})

#     emit('sentence_finish', {}) # 모델의 출력이 끝났음을 전달
#     print()

# @socketio.on('input_text')
# def handle_input_text(data):
#     input_text = data['input']

#     print(f"User Input : {input_text}")
#     interact_with_model(input_text)

# if __name__ == '__main__':
#     socketio.run(app, debug=True, host='0.0.0.0', port=5000)