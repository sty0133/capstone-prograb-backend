import os
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()

# 환경 변수에서 MongoDB 설정 읽기
MONGODB_URI = os.getenv('MONGODB_URI')
DATABASE_NAME = os.getenv('DATABASE_NAME')
NOTICE_DOCUMENT_COLLECTION = os.getenv('NOTICE_DOCUMENT_COLLECTION')
EMBEDDING_VECTOR_COLLECTION = os.getenv('EMBEDDING_VECTOR_COLLECTION')

# MongoDB 클라이언트 생성
client = MongoClient(MONGODB_URI)
db = client[DATABASE_NAME]

notice_document_collection = db[NOTICE_DOCUMENT_COLLECTION]
embedded_vector_collection = db[EMBEDDING_VECTOR_COLLECTION]

class MongodbNotice:
    def insert_document(document):
        try:
            notice = notice_document_collection.insert_one(document)

            # 임베딩 벡터는 별도의 컬렉션에 저장
            # for doc in document:
            #     embedded_vector_collection.insert_one(doc)

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
            documents = notice_document_collection.find()
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
            documents = notice_document_collection.find({"info.url": {"$regex": f"^{sub_notice_url}"}}, {"_id": 0, "info.url": 1})
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
            max_doc = notice_document_collection.find_one(sort=[("docNo", -1)])
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
            document = notice_document_collection.find_one({}, sort=[("docNo", -1)], projection={"_id": 0, "info.url": 1})
            if document and "info" in document and "url" in document["info"]:
                return document["info"]["url"]
            else:
                return None
        except Exception as e:
            print(f"An error occurred: {e}")
            return None
    
    def get_document_title_by_url(url):
        try:
            document = notice_document_collection.find_one({"info.url": url}, {"_id": 0, "rawTitle": 1})
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
        result = notice_document_collection.update_one(query, {'$set': update})
        return result.modified_count

    def delete_document(query):
        """
        MongoDB 컬렉션에서 문서를 삭제합니다.
        
        :param query: 삭제할 조건 (딕셔너리)
        :return: 삭제된 문서의 수
        """
        result = notice_document_collection.delete_one(query)
        return result.deleted_count

class EmbeddedVector:
    def get_all_embeddings():
            try:
                documents = embedded_vector_collection.find({}, {'_id': 0})
            except Exception as e:
                print(f"Failed to retrieve documents: {e}")
            return documents
    
    def insert_document(document):
        try:
            vector = embedded_vector_collection.insert_one(document)

            return vector.inserted_id
        except Exception as e:
            print(f"Failed to insert document: {e}")
            return None
    
    def get_documents_by_faiss_ids(faiss_ids):
        documents = []
        for faiss_id in faiss_ids:
            document = embedded_vector_collection.find_one({"faissID": faiss_id}, {"_id": 0, "faissID": 0})
            documents.append(document)
        return documents