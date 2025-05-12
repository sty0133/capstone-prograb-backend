from flask import Flask, request, jsonify
from sentence_transformers import SentenceTransformer
import torch

app = Flask(__name__)

# GPU 상태 확인
def check_gpu():
    if torch.cuda.is_available():
        gpu_count = torch.cuda.device_count()
        gpu_names = [torch.cuda.get_device_name(i) for i in range(gpu_count)]
        print(f"사용 가능한 GPU: {gpu_names}")
    else:
        print("GPU를 사용할 수 없습니다. CPU를 사용합니다.")

@app.route('/embed', methods=['POST'])
def embed():
    try:
        # 요청 데이터에서 문서 리스트 가져오기
        data = request.get_json()
        if not data or 'docs' not in data:
            return jsonify({
                "status": "error",
                "error": "invalid_request",
                "message": "docs 필드가 필요합니다."
            }), 400

        docs = data['docs']
        if not isinstance(docs, list):
            return jsonify({
                "status": "error",
                "error": "invalid_request",
                "message": "docs는 리스트 형식이어야 합니다."
            }), 400

        # 임베딩 생성
        device = 'cuda' if torch.cuda.is_available() else 'cpu'
        model = SentenceTransformer("nlpai-lab/KURE-v1", device=device)
        embeddings = model.encode(docs)

        # numpy.ndarray를 Python 리스트로 변환
        embeddings_list = embeddings.tolist()

        return jsonify({
            "status": "success",
            "message": "임베딩 생성 성공",
            "data": embeddings_list
        }), 200

    except Exception as e:
        return jsonify({
            "status": "error",
            "error": "internal_server_error",
            "message": str(e)
        }), 500

if __name__ == '__main__':
    check_gpu()  # 앱 시작 시 GPU 상태 확인
    app.run(host='0.0.0.0', port=5001)  # 포트 5001에서 실행