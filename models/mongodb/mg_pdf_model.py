from models.mongodb import PDF_DOCUMENT_COLLECTION
    
class MongodbPDF:
    def insert_document(document):
        try:
            pdf = PDF_DOCUMENT_COLLECTION.insert_one(document)
            return True, pdf.inserted_id
        except Exception as e:
            print(f"Failed to insert document: {e}")
            return False, f"{__name__}: {str(e)}"
    
    # def get_all_documents():
    #     try:
    #         documents = PDF_DOCUMENT_COLLECTION.find({}, {'_id': 0})
    #     except Exception as e:
    #         print(f"Failed to retrieve documents: {e}")
    #     return documents
    
    def find_documents_by_faiss_ids(faiss_ids):
        documents = []
        for faiss_id in faiss_ids:
            try:
                document = PDF_DOCUMENT_COLLECTION.find_one({"faissID": faiss_id}, {"_id": 0, "faissID": 0})
            except Exception as e:
                print(f"Failed to insert document: {e}")
                return False, f"{__name__}: {str(e)}"
            finally:
                documents.append(document['text'])
        return documents
    
    def delete_document_by_chat_id(chat_id):
        # chatID가 chat_id와 같은 모든 문서 삭제
        try:
            PDF_DOCUMENT_COLLECTION.delete_many({"chatID": chat_id})
        except Exception as e:
            print(f"Failed to insert document: {e}")
            return False, f"{__name__}: {str(e)}"
        return True, "success"
        
