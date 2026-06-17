import logging
from typing import List
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_text_splitters import RecursiveCharacterTextSplitter
from src.core.config import settings

logger = logging.getLogger(__name__)

class VectorStoreService:
    """
    Service to handle splitting resume text, generating HuggingFace embeddings,
    and storing/retrieving documents from a local ChromaDB instance.
    """
    def __init__(self):
        logger.info("Initializing HuggingFaceEmbeddings (all-MiniLM-L6-v2)...")
        # Initialize standard local embeddings model
        self.embeddings = HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-MiniLM-L6-v2",
            encode_kwargs={"normalize_embeddings": True}
        )
        # Configure text splitter for resume content
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len
        )

    def index_resume(self, resume_id: str, text: str) -> None:
        """
        Splits and stores the text content of a resume into a dedicated ChromaDB collection.
        Scoping collections per-resume prevents data leakage.
        """
        collection_name = f"resume_{resume_id}"
        logger.info(f"Indexing resume {resume_id} into collection {collection_name}")
        
        chunks = self.text_splitter.split_text(text)
        logger.info(f"Generated {len(chunks)} chunks from resume raw text.")
        
        # Initialize collection and insert documents
        Chroma.from_texts(
            texts=chunks,
            embedding=self.embeddings,
            persist_directory=str(settings.chroma_path),
            collection_name=collection_name
        )
        logger.info(f"Successfully indexed and persisted collection: {collection_name}")

    def retrieve_relevant_chunks(self, resume_id: str, query: str, k: int = 5) -> List[str]:
        """
        Retrieves the top-k most relevant text chunks from the resume's collection.
        """
        collection_name = f"resume_{resume_id}"
        logger.info(f"Querying relevant chunks from collection '{collection_name}' with query: '{query}'")
        
        db = Chroma(
            persist_directory=str(settings.chroma_path),
            embedding_function=self.embeddings,
            collection_name=collection_name
        )
        
        results = db.similarity_search(query, k=k)
        chunks = [doc.page_content for doc in results]
        logger.info(f"Retrieved {len(chunks)} chunks from Chroma.")
        return chunks
