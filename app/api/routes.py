@router.post("/chat")
def chat(payload: ChatRequest):

    import logging

    try:
        result = ask(payload.question)

        if not result or not result.get("answer"):
            raise ValueError("RAG workflow returned an empty answer")

        try:
            write_audit(
                payload.question,
                result.get("source_used", "unknown"),
                result.get("trace", [])
            )
        except Exception:
            logging.exception("Audit logging failed")

        return {
            "answer": result["answer"],
            "source_used": result.get("source_used", "unknown"),
            "trace": result.get("trace", []),
            "citations": result.get("citations", []),
            "rewritten_query": result.get(
                "current_query",
                payload.question
            )
        }

    except Exception:
        logging.exception("Chat request failed")

        raise HTTPException(
            status_code=500,
            detail="Unable to process your request. Check application logs."
        )