from functools import wraps
from flask import request, jsonify

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