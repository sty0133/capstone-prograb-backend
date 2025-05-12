import bcrypt
from models.mysql import get_cursor, get_db_connection

class MysqlUser:
    def register(user_id, user_password, user_name, user_school_uqid):
        cursor = get_cursor()

        # 중복 회원가입 방지
        try:
            cursor.execute(
                "SELECT user_id, user_school_uqid FROM user_info WHERE user_id=%s OR user_school_uqid=%s",
                (user_id, user_school_uqid)
            )
            duplicate_user = cursor.fetchone()
            print(duplicate_user, user_id, user_school_uqid)
            if duplicate_user:
                if duplicate_user[0] == user_id:
                    return False, 'Member already registered with user_id'
                elif duplicate_user[1] == user_school_uqid:
                    return False, 'Member already registered with user_school_uqid'
        except Exception as e:
            get_db_connection().rollback()
            return False, str(e)

        # 비밀번호 해싱
        hashed_password = bcrypt.hashpw(user_password.encode('utf-8'), bcrypt.gensalt())

        # 회원가입 정보
        register_sql = "INSERT INTO user_info(user_id, user_password, user_name, user_school_uqid) VALUES (%s, %s, %s, %s)"
        regist_user_data = (user_id, hashed_password, user_name, user_school_uqid)

        try:
            cursor.execute(register_sql, regist_user_data)
            get_db_connection().commit()

            # debugging
            print(f"{user_name}님 회원가입 하셨습니다.")
            return True, 1
        
        except Exception as e:
            get_db_connection().rollback()
            return False, str(e)
        
    def login(user_id, user_password):
        
        cursor = get_cursor()

        # 사용자 정보 조회
        cursor.execute("SELECT user_password FROM user_info WHERE user_id=%s", (user_id,))
        hashed_user_password = cursor.fetchone()

        if not hashed_user_password:
            return False, 'User not found'

        def check_password(input_password, hashed_password):
            # 입력받은 비밀번호를 해시와 비교 Bool 값 반환 T/F
            return bcrypt.checkpw(input_password.encode('utf-8'), hashed_password.encode('utf-8'))
        
        # 비밀번호 확인
        if not check_password(user_password, hashed_user_password[0]):
            return False, 'Incorrect password'

        # 로그인 성공
        return True, 1
    
    def check_chat_ownership(chat_id, user_id):
        cursor = get_cursor()

        try:
            # 채팅 ID와 사용자 ID로 소유 유무 확인

            cursor.execute("SELECT user_id FROM chat_info WHERE chat_id=%s", (chat_id,))
            owner = cursor.fetchone()
            if owner[0] == user_id:
                return True
            return False
        except Exception as e:
            return False