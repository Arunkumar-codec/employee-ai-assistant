# Interview Guide

## 60-second explanation
This project is an employee assistant that combines RAG with deterministic business tools. Policy questions are embedded with MiniLM and searched in ChromaDB; retrieved company text is sent to Gemini under a grounding prompt and sources come from retrieval metadata. Employee-specific questions use mock database tools instead of asking the LLM to invent state. The orchestrator can combine RAG and employee lookup, apply leave with validation and atomic state mutation, and continue conversations using an employee-bound `conversation_id` without replaying actions.

## Key concepts
- **RAG:** retrieve relevant private/reference text before generation so answers are grounded in supplied documents.
- **Embedding:** numeric semantic representation. MiniLM produces 384-dimensional vectors here.
- **Vector DB:** stores embeddings and retrieves semantically close chunks; Chroma is embedded/local and simple for this assessment.
- **Chunking/overlap:** documents are split into 500-character chunks with 50-character overlap so relevant passages fit retrieval while preserving boundary context.
- **Top-k:** retrieve the best 3 candidates, then use a distance threshold to reject weak evidence.
- **Why similarity is not enough:** an unsupported question can still be semantically close to a benefits document; the grounding prompt must still refuse when the retrieved context lacks the answer.
- **Source attribution:** filenames come from retrieval metadata, never from model-generated filenames.
- **Hallucination:** unsupported generated content. Grounding, no-answer behavior, and deterministic tools reduce it.
- **Agent/tool calling:** the orchestrator selects RAG, employee lookup, both, or the leave action based on intent and extracted parameters.
- **RAG vs tools:** RAG reads unstructured policy text; tools read/mutate structured application state.
- **Leave action:** validates employee/dates/reason, calculates inclusive days, checks balance, then commits balance and leave record.
- **Conversation context:** bounded in-memory history is keyed by `conversation_id` and bound to an employee.
- **Replay protection:** a follow-up asking for balance is reclassified as an info read and does not re-execute `apply_leave`.
- **Isolation:** reusing a conversation with a different employee is rejected.
- **Retry/backoff:** transient Gemini 429/5xx failures retry up to three attempts with bounded exponential delays.
- **CORS/errors/DOM:** explicit origins, sanitized unexpected errors, and `textContent`/DOM creation reduce common web risks.

## Complete request flow
Frontend sends employee ID, message, and optional conversation ID -> FastAPI validates -> session manager checks employee ownership -> classifier extracts intent/parameters -> orchestrator executes RAG/tool(s) -> mutable state is read from tools -> session records user/assistant messages -> API returns answer, sources, tools used, and conversation ID -> frontend safely renders text.
