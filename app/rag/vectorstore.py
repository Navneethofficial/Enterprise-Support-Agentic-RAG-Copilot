
import time

from pinecone import Pinecone, ServerlessSpec
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_pinecone import PineconeVectorStore

from app.core.config import get_settings


settings = get_settings()

_embeddings = None
_vectorstore = None


EMBEDDING_DIMENSIONS = {
    "sentence-transformers/all-minilm-l6-v2": 384,
    "all-minilm-l6-v2": 384,
}


def get_embedding_dimension(model_name: str | None = None) -> int:
    name = (model_name or settings.embedding_model or "").strip().lower()

    if not name:
        raise RuntimeError("Embedding model is not configured")

    if name in EMBEDDING_DIMENSIONS:
        return EMBEDDING_DIMENSIONS[name]

    if "all-minilm-l6-v2" in name:
        return 384

    raise ValueError(
        f"Unsupported Hugging Face embedding model: {name}"
    )


def get_embeddings():
    global _embeddings

    if _embeddings is None:
        model_name = settings.embedding_model.strip()

        if not model_name:
            raise RuntimeError("EMBEDDING_MODEL is missing")

        _embeddings = HuggingFaceEmbeddings(
            model_name=model_name,
            model_kwargs={"device": "cpu"},
            encode_kwargs={"normalize_embeddings": True},
        )

    return _embeddings


def ensure_index():

    if not settings.pinecone_api_key:
        raise RuntimeError("PINECONE_API_KEY is missing")

    desired_dimension = get_embedding_dimension()

    pc = Pinecone(api_key=settings.pinecone_api_key)

    existing_indexes = [
        index["name"] for index in pc.list_indexes()
    ]

    if settings.pinecone_index_name in existing_indexes:

        index_info = pc.describe_index(
            settings.pinecone_index_name
        )

        current_dimension = getattr(
            index_info, "dimension", None
        )

        if current_dimension != desired_dimension:
            raise ValueError(
                f"Pinecone index '{settings.pinecone_index_name}' "
                f"has dimension {current_dimension}, but the "
                f"embedding model requires {desired_dimension}. "
                "Create a new Pinecone index with the correct "
                "dimension. Existing index was not deleted."
            )

    else:

        pc.create_index(
            name=settings.pinecone_index_name,
            dimension=desired_dimension,
            metric="cosine",
            spec=ServerlessSpec(
                cloud="aws",
                region="us-east-1"
            ),
        )

        while True:
            index_info = pc.describe_index(
                settings.pinecone_index_name
            )

            status = getattr(index_info, "status", None)

            if status and status["ready"]:
                break

            time.sleep(1)

    return pc.Index(settings.pinecone_index_name)


def get_vectorstore():
    global _vectorstore

    if _vectorstore is None:

        index = ensure_index()

        _vectorstore = PineconeVectorStore(
            index=index,
            embedding=get_embeddings(),
            namespace=settings.pinecone_namespace,
        )

    return _vectorstore


def get_retriever():
    return get_vectorstore().as_retriever(
        search_kwargs={"k": settings.top_k}
    )


def add_documents(chunks):
    store = get_vectorstore()
    return store.add_documents(chunks)
