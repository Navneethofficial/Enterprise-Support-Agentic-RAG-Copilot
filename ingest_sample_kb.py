
from pathlib import Path
import logging

from app.core.config import get_settings
from app.services.ingestion import load_file, chunk_documents
from app.rag.vectorstore import add_documents


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

settings = get_settings()


def ingest_sample_kb():

    folder = Path(settings.sample_kb_dir)

    if not folder.exists():
        raise FileNotFoundError(
            f"Sample knowledge base folder not found: {folder}"
        )

    if not folder.is_dir():
        raise NotADirectoryError(
            f"Expected a directory: {folder}"
        )

    files = sorted(
        p for p in folder.iterdir()
        if p.is_file()
    )

    if not files:
        logger.warning("No files found in %s", folder)
        return

    all_docs = []

    for path in files:
        logger.info("Loading: %s", path.name)
        all_docs.extend(load_file(path))

    if not all_docs:
        logger.warning("No readable documents found.")
        return

    chunks = chunk_documents(all_docs)

    if not chunks:
        logger.warning("No document chunks generated.")
        return

    ids = add_documents(chunks)

    print(
        f"Indexed {len(files)} files -> "
        f"{len(chunks)} chunks -> "
        f"{len(ids)} Pinecone vectors"
    )


if __name__ == "__main__":
    ingest_sample_kb()
