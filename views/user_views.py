from flask import Blueprint, request, jsonify
from flask.views import MethodView

from models.mysql.my_user_model import MysqlUser
from utils.decorators import validate_request

user = Blueprint('user', __name__, url_prefix='/user')

class Login(MethodView):
    @validate_request(['user_id', 'user_password'])
    def post(self):
        user_id = request.data['user_id']
        user_password = request.data['user_password']

        # 로그인 모델 호출
        result, data = MysqlUser.login(user_id, user_password)

        if result:
            return jsonify({"status": "success",
                            "message": "로그인 성공"}), 200
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

user.add_url_rule('/login', view_func=Login.as_view('user_login'))
user.add_url_rule('/register', view_func=Register.as_view('user_register'))
user.add_url_rule('/logout', view_func=Logout.as_view('user_logout'))