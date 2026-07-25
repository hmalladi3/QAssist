# EARS: Generation Agent

Segment owner: [../llds/generation-agent.md](../llds/generation-agent.md)

## Tool Use Loop

- [x] **AGT-TOOL-001**: The system shall expose `search_documents` and `list_documents` (per [retrieval](retrieval.md)) as Bedrock Converse API tools available to Claude when answering a question.
- [x] **AGT-LOOP-001**: While Claude's response `stop_reason` is `tool_use`, the system shall execute the requested tool(s) and return each result to Claude as a `tool_result` message.
- [x] **AGT-LOOP-002**: The system shall bound the tool-use loop to a maximum of 4 round trips per question.
- [x] **AGT-LOOP-003**: If the tool-use loop (bounded per AGT-LOOP-002) reaches its round-trip limit without a `stop_reason` of `end_turn`, then the system shall force a final answer using only the context already gathered, rather than failing the request.

## Citations

- [x] **AGT-CITE-001**: The system shall resolve every `[chunk:<chunk_id>]` marker in Claude's answer text to a `Citation` containing filename, page number, and excerpt.
- [x] **AGT-CITE-002**: If an answer contains a `[chunk:<chunk_id>]` marker referencing a chunk_id never returned by a tool call within that question's conversation, then the system shall drop that citation and log a citation integrity violation, and shall never render it as a valid citation.

## Grounding & Trace

- [x] **AGT-PROMPT-001**: The system shall instruct Claude, via the system prompt, to answer only from `search_documents`/`list_documents` tool results and to state explicitly when the documents don't contain enough information to answer.
- [x] **AGT-TRACE-001**: The system shall record every tool call made during a question's agent loop — tool name, input, and a result summary — in the order they occurred, for inclusion in the API response's trace field.
