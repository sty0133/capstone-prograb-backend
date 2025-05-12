from flask import Blueprint, request, jsonify, g
from flask.views import MethodView

from models.mysql.my_user_model import MysqlUser
from models.mysql.my_chat_model import MysqlChat

from models.mongodb.mg_pdf_model import MongodbPDF
from models.mongodb.mg_user_model import MongodbUserChat

from utils.decorators import validate_request, token_required
from utils.token_utils import create_access_token

user = Blueprint('user', __name__)

class Login(MethodView):
    @validate_request(['user_id', 'user_password'])
    def post(self):
        user_id = request.data['user_id']
        user_password = request.data['user_password']

        # 로그인 모델 호출
        result, data = MysqlUser.login(user_id, user_password)

        if result:
            access_token = create_access_token({'user_id': user_id})
            return jsonify({"status": "success",
                            "message": "로그인 성공",
                            "token": access_token}), 200
        else:
            if data == 'User not found':
                return jsonify({"status": "error", 
                                "error": "user_not_found", 
                                "message": data}), 404
            elif data == 'Incorrect password':
                return jsonify({"status": "error", 
                                "error": "incorrect_password", 
                                "message": data}), 401
            else:
                return jsonify({"status": "error", 
                                "error": "internal_server_error", 
                                "message": data}), 500

class Register(MethodView):
    @validate_request(['user_id', 'user_password', 'user_name', 'user_school_uqid'])
    def post(self):
        user_id = request.data['user_id']
        user_password = request.data['user_password']
        user_name = request.data['user_name']
        user_school_uqid = int(request.data['user_school_uqid'])

        # 회원가입 모델 호출
        result, data = MysqlUser.register(user_id, user_password, user_name, user_school_uqid)

        if result:
            return jsonify({"status": "success", 
                            "message": "회원가입 성공", 
                            "data": user_name}), 200
        else:
            if data == 'Member already registered with user_id':
                return jsonify({"status": "error", 
                                "error": "member_already_registered_id"}), 409
            elif data == 'Member already registered with user_school_uqid':
                return jsonify({"status": "error", 
                                "error": "member_already_registered_school_uqid"}), 409
            else:
                return jsonify({"status": "error", 
                                "error": "internal_server_error",
                                "message": data}), 500
    
class Logout(MethodView):
    def post(self):
        # 로그아웃 처리
        pass

class List(MethodView):
    @token_required
    def get(self):
        # JWT에서 user_id 추출
        user_id = g.user.get('user_id')
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

    @token_required    
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

class ChatHistory(MethodView):
    @token_required
    def get(self):

        user_id = g.user.get('user_id')
        chat_id = request.args.get('chat_id')

        result = MysqlUser.check_chat_ownership(chat_id, user_id)

        if not result:
            return jsonify({
                "status": "error",
                "error": "not_own_chat",
                "message": "해당 채팅에 대한 권한이 없습니다."
            }), 403
        
        result, data = MongodbUserChat.get_messages_by_chat_id(chat_id)
        if not result:
            if data == 'No messages found for chat_id':
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
        return jsonify({
            "status": "success",
            "message": "채팅 기록 조회 성공",
            "data": data,
        }), 200

user.add_url_rule('/history', view_func=ChatHistory.as_view('user_chat_history'))
user.add_url_rule('/list', view_func=List.as_view('user_chat_list'))
user.add_url_rule('/login', view_func=Login.as_view('user_login'))
user.add_url_rule('/register', view_func=Register.as_view('user_register'))
user.add_url_rule('/logout', view_func=Logout.as_view('user_logout'))