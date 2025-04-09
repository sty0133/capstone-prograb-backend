# initialize.py에서 faiss_init import
from .initialize import faiss_init

# 앱 시작 시 DCU FAISS 인덱스 초기화 (싱글톤)
dcu_index = faiss_init.initialize()
dcu_faiss_path = faiss_init.get_index_path()
