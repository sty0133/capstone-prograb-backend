from functools import wraps
from flask import request, jsonify, g

import jwt
from utils.token_utils import get_token_from_header, SECRET_KEY, ALGORITHM
from jwt.exceptions import ExpiredSignatureError, InvalidTokenError

def validate_request(required_keys):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # JSON 요청인지 확인
            if request.is_json:
                data = request.json
            # multipart/form-data 요청인지 확인
            elif request.content_type.startswith('multipart/form-data'):
                data = request.form
            else:
                return jsonify({
                    "status": "error",
                    "error": "invalid_request",
                    "message": "요청 본문에 JSON 또는 Form 데이터가 필요합니다."
                }), 400

            # 필수 키 확인
            missing_keys = [key for key in required_keys if key not in data]
            if missing_keys:
                return jsonify({
                    "status": "error",
                    "error": "missing_keys",
                    "message": f"다음 키가 요청 본문에 필요합니다: {', '.join(missing_keys)}"
                }), 400

            # 요청 데이터를 저장
            request.data = {key: data.get(key) for key in required_keys}
            return func(*args, **kwargs)
        return wrapper
    return decorator

def token_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        token = get_token_from_header()
        if not token:
            return jsonify({"status": "error", "error": "token_missing", "message": "토큰이 필요합니다."}), 401
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            g.user = payload  # 전역 g 객체에 user 정보 저장 (Flask에서 공용 context용)
        except ExpiredSignatureError:
            return jsonify({"status": "error", "error": "token_expired", "message": "토큰이 만료되었습니다."}), 401
        except InvalidTokenError:
            return jsonify({"status": "error", "error": "invalid_token", "message": "유효하지 않은 토큰입니다."}), 401

        return f(*args, **kwargs)

    return decorated_function
