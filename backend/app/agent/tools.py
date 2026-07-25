"""
@spec AGT-TOOL-001
"""

SEARCH_DOCUMENTS_TOOL = {
    "name": "search_documents",
    "description": (
        "Semantic search over the ingested document corpus. Returns the most "
        "relevant chunks with their source document, page number, and a "
        "chunk_id to cite. Call this whenever answering the question requires "
        "information from the documents; call it again with a refined query "
        "if the first results don't fully answer the question."
    ),
    "inputSchema": {
        "json": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Natural-language search query"},
                "top_k": {
                    "type": "integer",
                    "description": "Number of chunks to retrieve, default 5",
                },
                "document_id": {
                    "type": "string",
                    "description": "Optional: restrict search to a single document ID from list_documents",
                },
            },
            "required": ["query"],
        }
    },
}

LIST_DOCUMENTS_TOOL = {
    "name": "list_documents",
    "description": (
        "List all documents currently available to search, with filename and "
        "page count. Call this when the question is about the corpus itself "
        "(e.g. 'what documents do you have?') or when you need a document_id "
        "to scope a search_documents call."
    ),
    "inputSchema": {"json": {"type": "object", "properties": {}}},
}

TOOL_SPECS = [SEARCH_DOCUMENTS_TOOL, LIST_DOCUMENTS_TOOL]
