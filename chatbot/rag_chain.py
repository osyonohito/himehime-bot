from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain.chains import RetrievalQA
from langchain_openai import ChatOpenAI
import os

def load_rag_chain(openai_api_key: str):
    os.environ["OPENAI_API_KEY"] = openai_api_key

    embeddings = HuggingFaceEmbeddings(
        model_name="intfloat/multilingual-e5-large",
        model_kwargs={'device': 'cpu'}
    )
    db = FAISS.load_local('himehime.db', embeddings, allow_dangerous_deserialization=True)
    retriever = db.as_retriever()

    llm = ChatOpenAI(model_name="gpt-3.5-turbo")
    rag_chain = RetrievalQA.from_chain_type(
        llm=llm,
        retriever=retriever,
        return_source_documents=True,
    )
    return rag_chain
