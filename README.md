# VRISKO — The Deal Behind the Deal

> AI-powered electronics price intelligence platform.

Vrisko researches multiple retailers for an exact product model and compares
prices, delivery fees, discounts, warranties, return policies and customer
sentiment — surfacing the *real* deal behind the headline price.

---

## Project Structure

```
vrisko/
├── frontend/          React + Vite + TypeScript + Tailwind CSS
│   ├── src/
│   │   ├── components/
│   │   │   ├── Logo.tsx
│   │   │   ├── RetailerCard.tsx
│   │   │   ├── DealIntegrityScore.tsx
│   │   │   ├── CustomerSentiment.tsx
│   │   │   ├── ComparisonSummaryPanel.tsx
│   │   │   ├── EvidencePanel.tsx
│   │   │   ├── StarRating.tsx
│   │   │   └── LoadingSkeleton.tsx
│   │   ├── App.tsx
│   │   ├── api.ts
│   │   ├── types.ts
│   │   └── index.css
│   ├── index.html
│   └── vite.config.ts
│
└── backend/           Python + FastAPI + Pydantic
    ├── main.py        API routes + demo fixtures
    ├── models.py      Pydantic data models
    ├── comparison.py  Comparison engine (decoupled from data sources)
    ├── requirements.txt
    ├── .env.example
    └── .gitignore
```

---

## Setup & Running

### Backend

```bash
# 1. Create and activate a virtual environment
cd backend
python -m venv venv

# Windows
venv\Scripts\activate
# macOS / Linux
source venv/bin/activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Copy environment variables
copy .env.example .env      # Windows
# cp .env.example .env      # macOS / Linux

# 4. Start the development server
uvicorn main:app --reload --port 8000
```

The API will be available at: **http://localhost:8000**
Interactive docs: **http://localhost:8000/docs**

---

### Frontend

```bash
# In a new terminal
cd frontend

# 1. Install dependencies
npm install

# 2. Copy environment variables
copy .env.example .env.local      # Windows
# cp .env.example .env.local      # macOS / Linux

# 3. Start the dev server
npm run dev
```

The frontend will be available at: **http://localhost:5173**

---

## API Reference

| Method | Endpoint      | Description                              |
|--------|---------------|------------------------------------------|
| GET    | /api/health   | Liveness check                           |
| GET    | /api/demo     | Returns labelled DEMO DATA result        |
| POST   | /api/compare  | Compare prices for an exact product model|

### POST /api/compare — Request body

```json
{
  "query": "Sony WH-CH720N",
  "currency": "GBP",
  "include_used": false
}
```

---

## Architecture Notes

### Data Safety Rules
- **Unknown delivery fees are never treated as zero.** If a retailer's delivery cost cannot be confirmed, `delivery_fee_unknown = true` and `comparable_total = null`.
- **Conditional discounts are never automatically applied.** Bank card offers, voucher codes etc. are listed separately and excluded from the comparable total.
- **Different product variants are never silently compared.** If the listing model doesn't exactly match the query model, `exact_model_match = false` and a warning note is shown.
- **All unverified fields are explicitly flagged.** Every data field carries a verification status.

### TinyFish Integration (Pending)
The comparison engine (`comparison.py`) is fully decoupled from the data source.
When TinyFish instructions are provided:
1. Create `backend/research/tinyfish.py`
2. Implement `async def fetch_offers(request, api_key) -> tuple[list[RetailerOffer], CustomerReviews]`
3. Uncomment the integration block in `main.py → POST /api/compare`

No changes to `comparison.py` or the frontend are required.

### Demo Data
All demo fixtures are in `main.py → _build_demo_offers()` and `_build_demo_reviews()`.
Every demo result has `is_demo = True` and `data_source = "demo"`.
The frontend displays a prominent **DEMO DATA** banner for all demo results.

---

## Tech Stack

| Layer     | Technology                     |
|-----------|--------------------------------|
| Frontend  | React 19, Vite 6, TypeScript   |
| Styling   | Tailwind CSS v4                |
| Backend   | Python 3.11+, FastAPI 0.115    |
| Validation| Pydantic v2                    |
| Research  | TinyFish API *(pending)*       |
