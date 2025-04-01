import os
from langchain_community.document_loaders import TextLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS

# テキストファイルのパス
DATA_DIR = "chatbot/background"

# Embeddingモデル
embeddings = HuggingFaceEmbeddings(
    model_name="intfloat/multilingual-e5-large",
    model_kwargs={"device": "cpu"}
)

# 文書の読み込み
all_documents = []
for filename in os.listdir(DATA_DIR):
    if filename.endswith(".txt"):
        loader = TextLoader(os.path.join(DATA_DIR, filename), encoding="utf-8")
        documents = loader.load()
        print(f"[DEBUG] Loaded {len(documents)} documents from {filename}")
        all_documents.extend(documents)

# 分割
splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
docs = splitter.split_documents(all_documents)
print(f"[DEBUG] Total chunks: {len(docs)}")
if docs:
    print(f"[DEBUG] First chunk content: {docs[0].page_content[:200]}")

# ベクトル化 & DB化
db = FAISS.from_documents(docs, embeddings)

# 保存
db.save_local("himehime.db")
print("✅ himehime.db を作成しました！")
