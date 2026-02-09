import json
from pathlib import Path

from langchain_community.vectorstores import FAISS
from langchain_openai import AzureOpenAIEmbeddings
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_core.documents import Document



from .config import Settings


def load_knowledge_base(data_dir: Path) -> list[Document]:
    kb_path = data_dir / "knowledge_base.json"
    raw = json.loads(kb_path.read_text(encoding="utf-8"))
    docs: list[Document] = []
    for item in raw:
        docs.append(
            Document(
                page_content=item["content"],
                metadata={
                    "title": item.get("title", "policy"),
                    "policy_id": item.get("policy_id", "unknown"),
                },
            )
        )
    return docs


def build_vector_store(settings: Settings) -> FAISS:
    if settings.hf_embeddings_model:
        embeddings = HuggingFaceEmbeddings(model_name=settings.hf_embeddings_model)
    else:
        embeddings = AzureOpenAIEmbeddings(
            azure_endpoint=settings.azure_endpoint,
            api_key=settings.azure_api_key,
            api_version=settings.azure_api_version,
            azure_deployment=settings.azure_embeddings_deployment,
        )
    docs = load_knowledge_base(settings.data_dir)
    return FAISS.from_documents(docs, embeddings)
