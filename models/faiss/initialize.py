import faiss
import os
import threading

class DCUFAISS:
    def __init__(self):
        self.index = None
        self.base_path = os.getenv('FAISS_INDEX_DCU_PATH')

    def get_index_path(self):
        return f"{self.base_path}/dcu.index"
    
    def initialize(self):
        index_path = self.get_index_path()

        if self.index is None:
            if os.path.exists(index_path):
                self.index = faiss.read_index(index_path)
                print(f"DCU FAISS loaded. Total vectors: {self.index.ntotal}")
            else:
                self.index = faiss.IndexFlatL2(1024)
                print("New DCU FAISS index created.")
        return self.index

faiss_init = DCUFAISS()

class PDFFAISS:
    _index_cache = {}  # chat_id별로 인덱스를 캐싱
    _lock = threading.Lock()  # 파일 접근 동기화를 위한 Lock

    def __init__(self):
        self.base_path = os.getenv('FAISS_INDEX_PDF_PATH')  # 기본 경로 설정

    def get_index_path(self, chat_id):
        return f"{self.base_path}/{chat_id}.index"

    def initialize(self, chat_id):
        chat_id = str(chat_id)

        # 캐싱된 인덱스가 있으면 반환
        if chat_id in self._index_cache:
            return self._index_cache[chat_id]

        index_path = self.get_index_path(chat_id)

        # 파일 접근 동기화
        with self._lock:
            if os.path.exists(index_path):
                # 파일이 존재하면 로드
                index = faiss.read_index(index_path)
                print(f"FAISS index for chat_id '{chat_id}' loaded. Total vectors: {index.ntotal}")
            else:
                # 파일이 없으면 새로운 인덱스 생성
                index = faiss.IndexFlatL2(1024)  # 벡터 차원에 맞게 수정
                print(f"New FAISS index created for chat_id '{chat_id}'.")

            # 캐싱에 저장
            self._index_cache[chat_id] = index
            return index

    def save_index(self, chat_id):
        """chat_id에 해당하는 인덱스를 저장"""
        chat_id = str(chat_id)
        index_path = self.get_index_path(chat_id)

        # 파일 접근 동기화
        with self._lock:
            if chat_id in self._index_cache:
                index = self._index_cache[chat_id]
                faiss.write_index(index, index_path)
                print(f"FAISS index for chat_id '{chat_id}' saved at {index_path}. Total vectors: {index.ntotal}")
            else:
                print(f"No index found for chat_id '{chat_id}' to save.")

    def clear_cache(self, chat_id):
        """chat_id에 해당하는 캐싱 데이터를 삭제"""
        chat_id = str(chat_id)
        with self._lock:
            if chat_id in self._index_cache:
                del self._index_cache[chat_id]
                print(f"Cache cleared for chat_id '{chat_id}'.")