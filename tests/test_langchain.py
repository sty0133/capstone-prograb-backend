from services.langchain import *

while True:
    q = input("질문을 입력하세요: ")
    a = rag_chain(q)
    print(a)
    print("-" * 50)