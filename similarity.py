print("[SIMILARITY] Initializing engine...")
from sentence_transformers import SentenceTransformer
model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')

def get_similarity(input1, input2):
    sentences = [input1, input2]
    embeddings = model.encode(sentences)
    return embeddings[0].dot(embeddings[1])