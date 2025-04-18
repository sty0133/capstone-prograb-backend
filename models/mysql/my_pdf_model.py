from models.mysql import get_cursor, get_db_connection
from models.faiss.process import delete_pdf_faiss

class MysqlPDF:
    def insert_pdf_name(chat_id, pdf_names):
        cursor = get_cursor()

        # pdf_names가 리스트인지 확인
        if not isinstance(pdf_names, list):
            return False, "pdf_names must be a list"

        try:
            # 리스트 안의 각 pdf_name을 chat_id와 함께 삽입
            for pdf_name in pdf_names:
                insert_sql = "INSERT INTO pdf_info(chat_id, pdf_name) VALUES (%s, %s)"
                insert_data = (chat_id, pdf_name)  # pdf_path는 None으로 설정
                cursor.execute(insert_sql, insert_data)

            get_db_connection().commit()
            return True, len(pdf_names)
        except Exception as e:
            get_db_connection().rollback()
            return False, f"{__name__}: {str(e)}"

    def delete_pdf_by_chat_id(chat_id):
        cursor = get_cursor()

        try:
            # chat_id에 해당하는 모든 pdf_name 삭제
            cursor.execute("DELETE FROM pdf_info WHERE chat_id=%s", (chat_id,))
            get_db_connection().commit()

            # FAISS 인덱스 삭제
            delete_pdf_faiss(chat_id)
            return True, 1
        except Exception as e:
            get_db_connection().rollback()
            return False, f"{__name__}: {str(e)}"