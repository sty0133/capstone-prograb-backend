from models.mongodb import USER_CHAT_DOCUMENT_COLLECTION, PDF_DOCUMENT_COLLECTION
from datetime import datetime

class MongodbUserChat:
    @staticmethod
    def initialize_chat(chat_id):
        try:
            chat_data = {
                "chat_id": chat_id,
                "messages": []  # 초기화 시 메시지는 비어 있음
            }
            result = USER_CHAT_DOCUMENT_COLLECTION.insert_one(chat_data)
            return True, result.inserted_id
        except Exception as e:
            print(f"Failed to initialize chat: {e}")
            return False, f"{__name__}: {str(e)}"

    @staticmethod
    def update_chat_by_id(chat_id, user_question, bot_response):
        try:
            new_message = [
                {
                    "role": "user",
                    "content": user_question,
                    "timestamp": datetime.now()
                },
                {
                    "role": "bot",
                    "content": bot_response,
                    "timestamp": datetime.now()
                }
            ]
            result = USER_CHAT_DOCUMENT_COLLECTION.update_one(
                {"chat_id": chat_id},
                {"$push": {"messages": {"$each": new_message}}}
            )
            if result.modified_count > 0:
                return True, "Chat updated successfully"
            else:
                return False, f"No chat found to update for chat_id: {chat_id}"
        except Exception as e:
            print(f"Failed to update chat: {e}")
            return False, f"{__name__}: {str(e)}"
        
    @staticmethod
    def get_messages_by_chat_id(chat_id):
        try:
            chat = USER_CHAT_DOCUMENT_COLLECTION.find_one({"chat_id": chat_id}, {"_id": 0, "messages": 1})
            if chat and "messages" in chat:
                return True, chat["messages"]
            else:
                return False, f"No messages found for chat_id"
        except Exception as e:
            print(f"Failed to retrieve messages: {e}")
            return False, f"{__name__}: {str(e)}"