from models.mysql import get_cursor, get_db_connection
from models.mysql.my_pdf_model import MysqlPDF

class MysqlChat:    
    def create_new_chat(user_id, chat_id):
        cursor = get_cursor()
        
        # # chat_id 중복 확인
        # cursor.execute("SELECT chat_id FROM chat_info WHERE chat_id=%s", (chat_id,))
        # existing_chat = cursor.fetchone()
        # if existing_chat:
        #     return False, 'chat_id already exists'

        # 사용자 정보 조회
        cursor.execute("SELECT user_password FROM user_info WHERE user_id=%s", (user_id,))
        hashed_user_password = cursor.fetchone()
        if not hashed_user_password:
            return False, 'User not found'
        
        # 새로운 채팅 생성
        new_chat_sql = "INSERT INTO chat_info(user_id, chat_id) VALUES (%s, %s)"
        new_chat_data = (user_id, chat_id)

        try:
            cursor.execute(new_chat_sql, new_chat_data)
            get_db_connection().commit()

            return True, new_chat_data
        
        except Exception as e:
            get_db_connection().rollback()
            return False, str(e)
        
    def check_chat_id_exists(chat_id):

        cursor = get_cursor()
        
        # chat_id 존재 여부 확인
        try:
            cursor.execute("SELECT chat_id FROM chat_info WHERE chat_id=%s", (chat_id,))
            existing_chat = cursor.fetchone()
        except Exception as e:
            get_db_connection().rollback()
            return False, str(e)
        
        if existing_chat:
            return True
        else:
            return False
        
    def get_chat_list(user_id):
        cursor = get_cursor()
        
        # 사용자 정보 조회
        try:
            cursor.execute("SELECT user_password FROM user_info WHERE user_id=%s", (user_id,))
            hashed_user_password = cursor.fetchone()
        except Exception as e:
            get_db_connection().rollback()
            return False, str(e)
        if not hashed_user_password:
            return False, 'User not found'

        try:
            # 사용자의 채팅 목록 조회
            cursor.execute("SELECT chat_id FROM chat_info WHERE user_id=%s", (user_id,))
            chat_list = cursor.fetchall()
        except Exception as e:
            get_db_connection().rollback()
            return False, str(e)
        
        if chat_list:
            return True, chat_list
        else:
            return False, 'No chats found'
        
    def delete_chat(chat_id):
        cursor = get_cursor()
        
        if MysqlChat.check_chat_id_exists(chat_id) == False:
            return False, 'chat_id not found'

        try:
            # 채팅에 연관된 pdf_info 삭제가 선행되어야 함(JOIN)
            result, message = MysqlPDF.delete_pdf_by_chat_id(chat_id)
            if not result:
                return False, message

            cursor.execute("DELETE FROM chat_info WHERE chat_id=%s", (chat_id,))
            get_db_connection().commit()
            return True, 1
        except Exception as e:
            get_db_connection().rollback()
            return False, f"{__name__}: {str(e)}"