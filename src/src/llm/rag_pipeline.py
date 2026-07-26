import os

from langchain.chains import RetrievalQA
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS

from src.llm.llama_client import get_llama


def _vectorstore(docs, embeddings):
    backend = os.getenv("VECTORSTORE_BACKEND", "faiss").strip().lower()

    if backend == "pinecone":
        index_name = os.getenv("PINECONE_INDEX_NAME", "").strip()
        namespace = os.getenv("PINECONE_NAMESPACE", "transformerforge").strip()
        if not os.getenv("PINECONE_API_KEY"):
            raise RuntimeError(
                "PINECONE_API_KEY is required when VECTORSTORE_BACKEND=pinecone."
            )
        if not index_name:
            raise RuntimeError(
                "PINECONE_INDEX_NAME is required when VECTORSTORE_BACKEND=pinecone."
            )

        from langchain_pinecone import PineconeVectorStore

        return PineconeVectorStore.from_documents(
            docs,
            embeddings,
            index_name=index_name,
            namespace=namespace,
        )

    if backend != "faiss":
        raise ValueError("VECTORSTORE_BACKEND must be 'faiss' or 'pinecone'.")

    return FAISS.from_documents(docs, embeddings)


def build_rag_pipeline(docs):
    embeddings = HuggingFaceEmbeddings(
        model_name=os.getenv(
            "EMBEDDING_MODEL",
            "sentence-transformers/all-MiniLM-L6-v2",
        )
    )

    vectorstore = _vectorstore(docs, embeddings)
    retriever = vectorstore.as_retriever()

    qa_chain = RetrievalQA.from_chain_type(
        llm=get_llama(),
        retriever=retriever,
        chain_type="stuff",
    )

    return qa_chain
