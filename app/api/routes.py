
from pathlib import Path

from fastapi import (
    APIRouter,
    UploadFile,
    File,
    HTTPException,
    Header
)
from pydantic import BaseModel, Field

from app.core.config import get_settings
from app.rag.workflow import ask
from app.rag.vectorstore import add_documents
from app.services.ingestion import load_file, chunk_documents, SUPPORTED
from app.services.audit import write_audit


router = APIRouter(prefix="/api")
settings = get_settings()


class ChatRequest(BaseModel):
    question: str = Field(min_length=2, max_length=3000)


# -----------------------------
# Health Check
# -----------------------------

@router.get("/health")
def health():
    return {
        "status": "ok",
        "service": settings.app_name
    }


# -----------------------------
# Chat Endpoint
# -----------------------------

@router.post("/chat")
def chat(payload: ChatRequest):

    try:
        result = ask(payload.question)

        write_audit(
            payload.question,
            result["source_used"],
            result.get("trace", [])
        )

        return {
            "answer": result["answer"],
            "source_used": result["source_used"],
            "trace": result.get("trace", []),
            "citations": result.get("citations", []),
            "rewritten_query": result.get(
                "current_query",
                payload.question
            )
        }

    except Exception:
        import logging
        logging.exception("Chat request failed")

        raise HTTPException(
            status_code=500,
            detail="Unable to process your request. Check application logs."
        )


# -----------------------------
# Document Ingestion Endpoint
# -----------------------------

@router.post("/ingest")
async def ingest(
    file: UploadFile = File(...),
    x_admin_key: str = Header(default="")
):

    if x_admin_key != settings.admin_api_key:
        raise HTTPException(
            status_code=401,
            detail="Invalid admin key"
        )

    if not file.filename:
        raise HTTPException(
            status_code=400,
            detail="Filename is required"
        )

    suffix = Path(file.filename).suffix.lower()

    if suffix not in SUPPORTED:
        raise HTTPException(
            status_code=400,
            detail=f"Supported: {', '.join(sorted(SUPPORTED))}"
        )

    try:
        upload_dir = Path(settings.upload_dir)
        upload_dir.mkdir(parents=True, exist_ok=True)

        dest = upload_dir / Path(file.filename).name

        content = await file.read()

        if not content:
            raise HTTPException(
                status_code=400,
                detail="Uploaded file is empty"
            )

        dest.write_bytes(content)

        docs = load_file(dest)
        chunks = chunk_documents(docs)

        if not chunks:
            raise HTTPException(
                status_code=400,
                detail="No text content found in the uploaded file"
            )

        ids = add_documents(chunks)

        return {
            "message": "Document indexed successfully",
            "file": dest.name,
            "chunks": len(chunks),
            "ids_created": len(ids)
        }

    except HTTPException:
        raise

    except Exception:
        import logging
        logging.exception("Document ingestion failed")

        raise HTTPException(
            status_code=500,
            detail="Document ingestion failed. Check application logs."
        )

    finally:
        await file.close()
