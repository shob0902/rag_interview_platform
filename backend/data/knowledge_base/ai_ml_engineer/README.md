# AI / ML Engineer knowledge base

Place the role's source document(s) here, then run ingestion.

**Recommended (from the assignment):** *Machine Learning* — Tom Mitchell.

1. Download the PDF and save it in this folder, e.g.:

   ```
   data/knowledge_base/ai_ml_engineer/tom_mitchell_machine_learning.pdf
   ```

2. From the `backend/` directory, run:

   ```bash
   python -m scripts.ingest --role ai_ml_engineer
   ```

Supported file types: `.pdf`, `.txt`, `.md`. You can drop multiple files here;
all of them are chunked, embedded, and tagged with the `ai_ml_engineer` role.
