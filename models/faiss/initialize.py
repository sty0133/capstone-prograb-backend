import faiss
import os

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
    def __init__(self):
        self.base_path = os.getenv('FAISS_INDEX_PDF_PATH')

    def get_index_path(self, pdf_group_id):
        pdf_group_id = str(pdf_group_id)
        return f"{self.base_path}/{pdf_group_id}.index"

    def initialize(self, pdf_group_id):
        index_path = self.get_index_path(pdf_group_id)

        if os.path.exists(index_path):
            index = faiss.read_index(index_path)
            print(f"FAISS index for group '{pdf_group_id}' loaded. Total vectors: {index.ntotal}")
        else:
            index = faiss.IndexFlatL2(1024)
            print(f"New FAISS index created for group '{pdf_group_id}'.")
        return index