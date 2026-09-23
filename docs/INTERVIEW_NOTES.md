# Interview Notes — Day 2: RAG Concepts

Beginner-friendly explanations of the concepts behind Day 2, in the order they come up in the
pipeline. Written to prepare for the assessment interview, not as a general ML textbook.

---

### 1. What is RAG?

**WHAT:** Retrieval-Augmented Generation. Instead of asking an LLM a question and hoping it
"knows" the answer, you first *retrieve* relevant text from your own documents, then *generate* an
answer using that text as context.
**WHY:** an LLM's training data doesn't include your company's leave policy. RAG lets it answer
correctly about documents it has never seen, without retraining the model.
**HOW USED HERE:** `app/services/rag_service.py` — retrieve chunks, build context, ask Gemini to
answer using only that context.
**ALTERNATIVE:** fine-tuning the LLM on your documents — far more expensive, and the model would
still need retraining every time a policy changes. RAG just needs re-ingestion.

### 2. Why RAG instead of sending every document to an LLM?

**WHAT:** you could, in principle, paste all six documents into every prompt.
**WHY NOT:** it's slower and more expensive per request (more tokens), and irrelevant content
dilutes the model's attention — asking about sick leave while also showing it the travel policy
makes mistakes more likely, not less.
**HOW USED HERE:** retrieval picks only the `TOP_K` (default 4) most relevant chunks per question.
**ALTERNATIVE:** "long-context stuffing" is viable for genuinely tiny corpora, but doesn't scale —
this project's design scales to hundreds of documents without changing the architecture.

### 3. What is document chunking?

**WHAT:** splitting a document into smaller overlapping pieces before embedding them.
**WHY:** a whole document is often "about" several things; embedding it as one vector blurs those
topics together. A question about one section should retrieve just that section.
**HOW USED HERE:** `app/rag/chunker.py` — 700 characters per chunk, split on paragraph/sentence
boundaries where possible.
**ALTERNATIVE:** embedding whole documents (loses precision) or splitting by every single
sentence (loses surrounding context, and multiplies the number of vectors unnecessarily).

### 4. Why use chunk overlap?

**WHAT:** consecutive chunks share a small amount of text (120 characters here) at their boundary.
**WHY:** if a chunk boundary happens to fall in the middle of an important sentence, overlap means
the sentence's beginning still appears (at the end of the previous chunk, or the start of the
next), so no single fact gets fully "cut in half" and lost from both chunks.
**HOW USED HERE:** `chunker.py`'s sliding window: `start = end - chunk_overlap` for the next chunk.
**ALTERNATIVE:** no overlap — simpler, but risks losing information right at a chunk boundary.

### 5. What is an embedding?

**WHAT:** a list of numbers (a vector) that represents the *meaning* of a piece of text.
**WHY:** computers can't compare "meaning" directly, but they can compare numbers — embeddings
turn "how similar are these two ideas?" into "how close are these two points in space?"
**HOW USED HERE:** `app/rag/embedder.py`, using `sentence-transformers/all-MiniLM-L6-v2` — every
chunk and every user question gets turned into a 384-number vector.
**ALTERNATIVE:** keyword/TF-IDF search — fast and simple, but only matches literal words, not
meaning (won't connect "work remotely" to "work from home").

### 6. What is a vector?

**WHAT:** just a list of numbers, e.g. `[0.12, -0.03, 0.87, ...]` (384 of them here).
**WHY:** it's the mathematical form an embedding takes — you can do arithmetic on vectors (like
measuring the angle between two of them) in a way you can't do on raw text.
**HOW USED HERE:** every chunk's vector is stored in ChromaDB; every question's vector is computed
on the fly and compared against them.

### 7. What is semantic similarity?

**WHAT:** how close two pieces of text are in *meaning*, regardless of exact wording.
**WHY:** it's what makes RAG work despite users not phrasing questions exactly like the documents.
**HOW USED HERE:** measured as **cosine similarity** between two embedding vectors — the cosine of
the angle between them, from -1 (opposite meaning) to 1 (identical meaning).

### 8. What is a vector database?

**WHAT:** a database built to efficiently answer "which stored vectors are closest to this one?"
across potentially millions of vectors.
**WHY:** comparing a query against every single chunk one-by-one (a Python loop) doesn't scale;
vector databases use indexing structures (Chroma uses HNSW) to make this fast.
**HOW USED HERE:** ChromaDB, persisted locally under `vector_store/`.
**ALTERNATIVE:** FAISS (a library, not a full database — no built-in persistence/metadata storage),
Qdrant/Pinecone (full standalone servers — more setup than this assessment needs).

### 9. Why ChromaDB?

**WHAT/WHY:** runs embedded in-process (no server to deploy), persists to disk automatically, and
has a small, readable Python API — a good fit for "understand every line" plus a small project.
**HOW USED HERE:** `app/rag/vector_store.py`, `chromadb.PersistentClient(path=...)`.
**ALTERNATIVE:** Pinecone (managed, needs an account/network, overkill here); Qdrant (a real
server to run); FAISS (would require hand-rolling metadata storage and persistence ourselves).

### 10. What happens during ingestion?

**WHAT:** the one-time (or "whenever documents change") process: load documents → normalize →
chunk → embed every chunk → store (chunk text + vector + metadata) in ChromaDB.
**WHY SEPARATE FROM THE API:** it's comparatively slow (loading the embedding model, computing
many vectors) and doesn't need to happen on every server restart — only when the source documents
actually change.
**HOW USED HERE:** `python scripts/ingest_documents.py`.

### 11. What happens during retrieval?

**WHAT:** the per-question process: embed the user's question → ask ChromaDB for the closest
stored chunk vectors → get back their original text + metadata + distance.
**HOW USED HERE:** `app/rag/retriever.py:search_company_documents(query)`.

### 12. What is top-k?

**WHAT:** the number of chunks retrieved per question (`TOP_K`, default 4).
**WHY:** too few risks missing needed information; too many adds noise and cost. It's a tunable
trade-off, not a fixed law — hence it's a setting, not a hard-coded number.

### 13. What is retrieval distance/similarity?

**WHAT:** a number describing how close a stored chunk's vector is to the query's vector.
**WHY IT MATTERS HERE:** Chroma's collection is configured for **cosine distance**
(`1 - cosine_similarity`), so **smaller = more similar** (0 = identical, up to 2 = opposite) — the
opposite of a "higher score is better" metric. Getting this backwards would silently invert the
no-answer logic (see `app/rag/vector_store.py` docstring).

### 14. Why do we need a threshold?

**WHAT:** a cutoff distance beyond which retrieved chunks are considered "not actually relevant."
**WHY:** ChromaDB will always return *something* for `top_k` — even for a completely unrelated
question, it returns the "least bad" matches. Without a threshold, the LLM would be handed
irrelevant context and might still try to answer from it.
**HOW USED HERE:** `RETRIEVAL_SCORE_THRESHOLD` (default 0.8) — if the *best* retrieved distance
exceeds it, the app returns the no-answer response without even calling the LLM.

### 15. What is hallucination?

**WHAT:** an LLM confidently stating something false or unsupported, because it's generating
plausible-sounding text rather than looking anything up.
**WHY IT'S A RISK HERE:** asked "Does the company provide pet insurance?", an ungrounded LLM might
invent a plausible-sounding policy rather than admitting it doesn't know.

### 16. How does this application reduce hallucinations?

Three layers, all working together:
1. **Retrieval threshold** — if nothing relevant is found, the LLM is never even called; the
   no-answer response is returned directly.
2. **Strict system prompt** — explicitly tells the LLM to answer only from provided context, never
   from outside knowledge, and to use the exact no-answer sentence when context is insufficient.
3. **Sources from metadata, not the model** — filenames are attached by the application from
   retrieval results, never generated by the LLM, so it can't invent a plausible-sounding source.

### 17. Why must source names come from metadata?

**WHAT:** `sources` in the API response comes from `RetrievedChunk.source` (Chroma metadata),
never parsed from the LLM's text output.
**WHY:** an LLM asked to "cite your source" can invent a filename that sounds right but doesn't
exist, or cite the wrong one. The application already knows exactly which documents were
retrieved — there's no reason to trust the model to repeat that correctly.

### 18. Why use a local embedding model?

**WHAT:** `all-MiniLM-L6-v2` runs on the same machine as the app — no API call, no network
round-trip, no per-call cost.
**WHY:** embeddings are computed constantly (every chunk during ingestion, every question during
retrieval) — a local model is free, fast, and gives byte-identical results every time
(reproducible), unlike a hosted API that could change its model version underneath you.

### 19. Why separate embeddings from the LLM?

**WHAT:** the embedding model (MiniLM, local) and the answer-generation model (Gemini, hosted) are
two completely independent components.
**WHY:** they solve different problems (representing meaning vs. generating fluent text) and don't
need to be the same vendor or even the same *kind* of model. Keeping them separate means swapping
the LLM provider (e.g. Gemini → another vendor) never requires re-embedding the entire document
corpus, and vice versa.

### 20. What would change for a production-scale system?

- **Vector DB:** ChromaDB embedded-mode is fine for thousands of chunks; a production system with
  millions of documents would likely move to a managed/clustered vector database (Pinecone,
  Qdrant Cloud, or a managed Chroma deployment) for horizontal scaling and high availability.
- **Ingestion:** a one-off script would become a scheduled/event-driven pipeline (e.g. triggered
  when a document is added/updated in a document-management system), with incremental re-indexing.
- **Retrieval quality:** add reranking (a second, more expensive model that re-scores the top-N
  candidates from the fast vector search) and metadata filtering (e.g. restrict search to
  documents relevant to the employee's department/region).
- **Reliability:** retries/backoff for the LLM call, request-level timeouts, and observability
  (structured logs, latency/error metrics) beyond this project's basic exception logging.
- **Security:** authentication/authorization (this project's `employee_id` is currently unverified
  — see Known Limitations), rate limiting, and stricter prompt-injection defenses if documents can
  be uploaded by less-trusted sources.
