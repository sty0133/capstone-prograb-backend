import os

from flask import Flask, request
from flask_cors import CORS

def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')

    from views.chat_views import chat
    from views.pdf_views import pdf
    from views.user_views import user

    app.register_blueprint(chat, url_prefix='/chat')
    app.register_blueprint(pdf, url_prefix='/pdf')
    app.register_blueprint(user, url_prefix='/user')

    CORS(app)

    return app

if __name__ == "__main__":
    app = create_app()
    app.run(debug=True, port=8080, host='0.0.0.0')