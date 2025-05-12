from models.mongodb import NOTICE_DOCUMENT_COLLECTION, EMBEDDING_VECTOR_COLLECTION, db

class MongodbDCU:
    def insert_document(document):
        try:
            notice = NOTICE_DOCUMENT_COLLECTION.insert_one(document)

            # 임베딩 벡터는 별도의 컬렉션에 저장
            # for doc in document:
            #     EMBEDDING_VECTOR_COLLECTION.insert_one(doc)

            return notice.inserted_id
        except Exception as e:
            print(f"Failed to insert document: {e}")
            return None
        
    def get_all_urls():
        """
        MongoDB 컬렉션에서 모든 문서의 info.url 값을 추출하여 리스트에 저장합니다.
        
        :return: 모든 url의 리스트
        """
        urls = []
        try:
            documents = NOTICE_DOCUMENT_COLLECTION.find()
            for document in documents:
                if 'info' in document and 'url' in document['info']:
                    urls.append(document['info']['url'])
            return urls
        except Exception as e:
            print(f"Failed to retrieve documents: {e}")
        return []
    
    def get_all_urls_by_category(sub_notice_url):
        urls = []
        try:
            documents = NOTICE_DOCUMENT_COLLECTION.find({"info.url": {"$regex": f"^{sub_notice_url}"}}, {"_id": 0, "info.url": 1})
            for document in documents:
                if 'info' in document and 'url' in document['info']:
                    urls.append(document['info']['url'])
            return urls
        except Exception as e:
            print(f"Failed to retrieve documents: {e}")
        return None

    # "doc_no" 필드에 대해서 임베딩 컬렉션에는 유니크 인덱스 생성 불필요
    def get_max_doc_no():
        try:
            # doc_no 필드를 기준으로 내림차순 정렬하여 첫 번째 문서를 가져옴
            max_doc = NOTICE_DOCUMENT_COLLECTION.find_one(sort=[("docNo", -1)])
            if max_doc and "docNo" in max_doc:
                return max_doc["docNo"]
            else:
                return 0
        except Exception as e:
            print(f"No searchable documents found: {e}")
            return 0

    def find_document_by_doc_and_category(doc):
        doc_no = doc['docNo']
        category = doc['category']

        document = db[category].find_one({"docNo": doc_no}, {"_id": 0}) 
        return document

    def get_latest_document_url():
        try:
            document = NOTICE_DOCUMENT_COLLECTION.find_one({}, sort=[("docNo", -1)], projection={"_id": 0, "info.url": 1})
            if document and "info" in document and "url" in document["info"]:
                return document["info"]["url"]
            else:
                return None
        except Exception as e:
            print(f"An error occurred: {e}")
            return None
    
    def get_document_title_by_url(url):
        try:
            document = NOTICE_DOCUMENT_COLLECTION.find_one({"info.url": url}, {"_id": 0, "rawTitle": 1})
            if document and "rawTitle" in document:
                return document["rawTitle"]
            else:
                return None
        except Exception as e:
            print(f"An error occurred: {e}")
            return None

    def update_document(query, update):
        """
        MongoDB 컬렉션에서 문서를 업데이트합니다.
        
        :param query: 업데이트할 조건 (딕셔너리)
        :param update: 업데이트할 내용 (딕셔너리)
        :return: 업데이트 결과
        """
        result = NOTICE_DOCUMENT_COLLECTION.update_one(query, {'$set': update})
        return result.modified_count

    def delete_document(query):
        """
        MongoDB 컬렉션에서 문서를 삭제합니다.
        
        :param query: 삭제할 조건 (딕셔너리)
        :return: 삭제된 문서의 수
        """
        result = NOTICE_DOCUMENT_COLLECTION.delete_one(query)
        return result.deleted_count

# 아래의 클래스는 PDF 문서 형식과 같이 저장한다면 구조 변경이 필요함 
class MongodbEmbeddedVector:
    def get_all_embeddings():
        try:
            documents = EMBEDDING_VECTOR_COLLECTION.find({}, {'_id': 0})
        except Exception as e:
            print(f"Failed to retrieve documents: {e}")
        return documents
    
    def insert_document(document):
        try:
            vector = EMBEDDING_VECTOR_COLLECTION.insert_one(document)

            return vector.inserted_id
        except Exception as e:
            print(f"Failed to insert document: {e}")
            return None
    
    def get_documents_by_faiss_ids(faiss_ids):
        documents = []
        for faiss_id in faiss_ids:
            document = EMBEDDING_VECTOR_COLLECTION.find_one({"faissID": faiss_id}, {"_id": 0, "faissID": 0})
            documents.append(document)
        return documents
    
