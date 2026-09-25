# Official Assessment Acceptance Tests
Reset EMP001 Rahul to 12, EMP002 Priya to 8, clear leave records/conversations, then run through real `POST /api/chat`.

1. **A1 WFH** — `What is the work from home policy?` -> `search_company_documents`, `work_from_home_policy.txt`.
2. **A2 Annual leave** — `How many annual leaves are allowed?` -> RAG, `leave_policy.txt`.
3. **A3 Unsupported** — `Does the company provide pet insurance?` -> `I couldn't find this information in the provided documents.` and `sources=[]`.
4. **A4 Balance** — `How many leaves does EMP001 have?` -> `get_employee_info`, balance 12, no sources.
5. **A5 Multi-tool** — `What is the leave policy and how many leaves does EMP001 have?` -> RAG + employee tool, balance 12, leave-policy source.
6. **A6 Action** — `Apply leave for EMP001 from 2026-10-20 to 2026-10-22 for personal reasons.` -> `apply_leave`, 3 inclusive days, 12 -> 9, exactly one record. Save returned `conversation_id`.
7. **A7 Follow-up** — reuse A6 `conversation_id`: `How many leaves will I have after applying?` -> `get_employee_info`, balance remains 9, leave record count remains one, no `apply_leave` replay.
