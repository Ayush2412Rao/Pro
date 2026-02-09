# Zomato RAG Complaint Agent (Azure OpenAI + LangChain)

This project provides a simple RAG-based complaint assistant for food delivery issues (missing item, wrong food, bad smell, broken seal, etc.) with a fallback to customer care. It uses:

- Azure OpenAI + LangChain for reasoning
- RAG over policy knowledge base
- Text-to-SQL over a small SQLite database
- FastAPI backend
- Streamlit UI

## Folder structure

```
backend/
  app/                # FastAPI app + agent logic
  data/               # JSON data + SQLite db + init script
  requirements.txt
ui/
  app.py              # Streamlit UI
  requirements.txt
.env.sample
README.md
```

## Setup

1. Create a virtual environment and install backend deps:
   - `python -m venv .venv`
   - `.venv\Scripts\activate`
   - `pip install -r backend\requirements.txt`

2. Copy `.env.sample` to `.env` and fill your Azure OpenAI values.
   - `AZURE_OPENAI_DEPLOYMENT` should be a chat model (e.g., `gpt-4o-gs`).
   - For embeddings, choose one:
     - Azure: set `AZURE_OPENAI_EMBEDDINGS_DEPLOYMENT` (e.g., `text-embedding-3-small`)
     - Hugging Face (free): set `HF_EMBEDDINGS_MODEL` (e.g., `sentence-transformers/all-MiniLM-L6-v2`)

3. Initialize the SQLite database:
   - `python backend\data\init_db.py`

4. Run the backend:
   - `uvicorn backend.app.main:app --reload`

5. Run the UI:
   - `pip install -r ui\requirements.txt`
   - `streamlit run ui\app.py`

## API

- `POST /chat`  
  Request body:
  ```
  {
    "message": "My fries were missing",
    "order_id": "ZOM123"
  }
  ```

## Notes

- JSON files under `backend/data` are static and can be edited to add new policies and scenarios.
- If the agent can't map a scenario to policy or confidence is low, it escalates to customer care.
