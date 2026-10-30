"""
Vrisko — FastAPI application entry point (main.py).

Routes
------
GET  /api/health   — liveness check
GET  /api/markets  — returns configured markets and retailers
GET  /api/demo     — returns a fully labelled DEMO DATA ComparisonResult (defaults to Indian market)
POST /api/compare  — entry point for product research across market retailers
"""

from __future__ import annotations

import os
from datetime import datetime, timezone
from typing import Optional

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from comparison import build_comparison_result
from models import (
    CompareRequest,
    ComparisonResult,
    ConditionalDiscount,
    CustomerReviews,
    DataSource,
    OfferAvailability,
    ProductCondition,
    RetailerOffer,
    Sentiment,
    VerifiedField,
)
from retailers import (
    get_market_retailers,
    get_supported_markets,
    reconcile_market_investigation,
)
from product_research import get_product_research

load_dotenv()

# ─────────────────────────────────────────────────────────────────────────────
# App setup
# ─────────────────────────────────────────────────────────────────────────────

app = FastAPI(
    title="Vrisko API",
    description="AI-powered electronics price intelligence — The deal behind the deal.",
    version="0.2.0",
)

_raw_origins = os.getenv(
    "ALLOWED_ORIGINS",
    "http://localhost:5173,http://localhost:3000",
)
allowed_origins = [o.strip() for o in _raw_origins.split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ─────────────────────────────────────────────────────────────────────────────
# Demo fixtures  (clearly separated from live research logic)
# ─────────────────────────────────────────────────────────────────────────────

def _build_india_demo_offers(query: str = "Sony WH-CH720N") -> list[RetailerOffer]:
    """
    India market demo fixtures for frontend development & testing.
    Investigates all four required Indian retailers:
    1. Amazon India (amazon.in)
    2. Flipkart (flipkart.com)
    3. Croma (croma.com)
    4. Reliance Digital (reliancedigital.in) — marked unavailable (no matching listing).

    Never fabricates missing retailer results.
    """
    now = datetime.now(timezone.utc)

    # Discovered verified listings for the model
    discovered = [
        RetailerOffer(
            retailer_name="Amazon India",
            retailer_url="https://www.amazon.in",
            product_url="https://www.amazon.in/dp/DEMO_IN_ASIN",
            listed_price=7990.0,
            currency="INR",
            delivery_fee=0.0,          # confirmed free Prime delivery
            delivery_fee_unknown=False,
            headline_discount_pct=47.0,
            original_price=14990.0,
            conditional_discounts=[
                ConditionalDiscount(
                    label="HDFC Bank Card offer",
                    amount=1000.0,
                    percentage=None,
                    condition_description="Flat \u20b91,000 instant discount on HDFC Bank Credit Card EMI transactions.",
                    is_verified=True,
                ),
                ConditionalDiscount(
                    label="Amazon Pay ICICI offer",
                    amount=None,
                    percentage=5.0,
                    condition_description="5% unlimited cashback for Amazon Pay ICICI Cardholders.",
                    is_verified=True,
                ),
            ],
            condition=ProductCondition.NEW,
            exact_model_match=True,
            warranty=VerifiedField(value="1-year Sony India manufacturer warranty", is_verified=True),
            return_policy=VerifiedField(value="7-day replacement only", is_verified=True),
            is_verified=True,
            rating=4.3,
            review_count=3420,
            availability=OfferAvailability.AVAILABLE,
            data_source=DataSource.DEMO,
            checked_at=now,
        ),
        RetailerOffer(
            retailer_name="Flipkart",
            retailer_url="https://www.flipkart.com",
            product_url="https://www.flipkart.com/sony-wh-ch720n-anc/p/DEMO_SKU",
            listed_price=7990.0,
            currency="INR",
            delivery_fee=40.0,
            delivery_fee_unknown=False,
            headline_discount_pct=47.0,
            original_price=14990.0,
            conditional_discounts=[
                ConditionalDiscount(
                    label="Flipkart Axis Bank Card",
                    amount=None,
                    percentage=5.0,
                    condition_description="5% cashback on Flipkart Axis Bank Card. Conditions not verified on listing.",
                    is_verified=False,
                )
            ],
            condition=ProductCondition.NEW,
            exact_model_match=True,
            warranty=VerifiedField(value="1-year brand warranty", is_verified=True),
            return_policy=VerifiedField(value="7-day service centre replacement", is_verified=True),
            is_verified=True,
            rating=4.2,
            review_count=1890,
            availability=OfferAvailability.AVAILABLE,
            data_source=DataSource.DEMO,
            checked_at=now,
        ),
        RetailerOffer(
            retailer_name="Croma",
            retailer_url="https://www.croma.com",
            product_url="https://www.croma.com/sony-wh-ch720n-headphones/p/DEMO_SKU",
            listed_price=8490.0,
            currency="INR",
            delivery_fee=0.0,
            delivery_fee_unknown=False,
            headline_discount_pct=43.0,
            original_price=14990.0,
            conditional_discounts=[],
            condition=ProductCondition.NEW,
            exact_model_match=True,
            warranty=VerifiedField(value="1-year manufacturer warranty", is_verified=True),
            return_policy=VerifiedField(value="15-day return policy", is_verified=True),
            is_verified=True,
            rating=4.4,
            review_count=320,
            availability=OfferAvailability.AVAILABLE,
            data_source=DataSource.DEMO,
            checked_at=now,
        ),
    ]

    # Reconcile against all 4 configured Indian retailers
    # Reliance Digital will be marked UNAVAILABLE truthfully (no matching listing found)
    return reconcile_market_investigation(
        query=query,
        country_code="IN",
        discovered_offers=discovered,
        checked_at=now,
    )


def _build_uk_demo_offers() -> list[RetailerOffer]:
    """Hardcoded UK demo data kept for backward compatibility and UK market testing."""
    now = datetime.now(timezone.utc)

    return [
        RetailerOffer(
            retailer_name="Amazon UK",
            retailer_url="https://www.amazon.co.uk",
            product_url="https://www.amazon.co.uk/dp/DEMO_ASIN",
            listed_price=89.00,
            currency="GBP",
            delivery_fee=0.0,
            delivery_fee_unknown=False,
            headline_discount_pct=11.0,
            original_price=99.99,
            conditional_discounts=[
                ConditionalDiscount(
                    label="Amazon Prime exclusive",
                    amount=None,
                    percentage=None,
                    condition_description="Free next-day delivery available to Prime members only.",
                    is_verified=True,
                ),
                ConditionalDiscount(
                    label="Barclaycard offer",
                    amount=5.00,
                    percentage=None,
                    condition_description="\u00a35 cashback when paying with an eligible Barclaycard.",
                    is_verified=True,
                ),
            ],
            condition=ProductCondition.NEW,
            exact_model_match=True,
            warranty=VerifiedField(value="1-year manufacturer warranty", is_verified=True),
            return_policy=VerifiedField(value="30-day returns", is_verified=True),
            is_verified=True,
            rating=4.3,
            review_count=2847,
            availability=OfferAvailability.AVAILABLE,
            data_source=DataSource.DEMO,
            checked_at=now,
        ),
        RetailerOffer(
            retailer_name="Currys",
            retailer_url="https://www.currys.co.uk",
            product_url="https://www.currys.co.uk/products/DEMO_SKU",
            listed_price=84.99,
            currency="GBP",
            delivery_fee=None,
            delivery_fee_unknown=True,
            headline_discount_pct=15.0,
            original_price=99.99,
            conditional_discounts=[],
            condition=ProductCondition.NEW,
            exact_model_match=True,
            warranty=VerifiedField(value="1-year warranty", is_verified=True),
            return_policy=VerifiedField(value="21-day returns", is_verified=True),
            is_verified=True,
            rating=4.1,
            review_count=934,
            availability=OfferAvailability.AVAILABLE,
            data_source=DataSource.DEMO,
            checked_at=now,
        ),
        RetailerOffer(
            retailer_name="John Lewis",
            retailer_url="https://www.johnlewis.com",
            product_url="https://www.johnlewis.com/products/DEMO_SKU",
            listed_price=99.00,
            currency="GBP",
            delivery_fee=0.0,
            delivery_fee_unknown=False,
            headline_discount_pct=None,
            original_price=None,
            conditional_discounts=[],
            condition=ProductCondition.NEW,
            exact_model_match=True,
            warranty=VerifiedField(value="2-year guarantee (John Lewis own)", is_verified=True),
            return_policy=VerifiedField(value="35-day returns", is_verified=True),
            is_verified=True,
            rating=4.6,
            review_count=511,
            availability=OfferAvailability.AVAILABLE,
            data_source=DataSource.DEMO,
            checked_at=now,
        ),
    ]


def _build_demo_reviews() -> CustomerReviews:
    return CustomerReviews(
        average_rating=4.3,
        total_review_count=5630,
        positive_feedback=(
            "Excellent noise cancellation for the price segment. Lightweight and comfortable "
            "for extended sessions. Outstanding battery life (35+ hours) and dependable multipoint Bluetooth."
        ),
        negative_feedback=(
            "Microphone quality is average in noisy outdoor environments. "
            "Ear cushions can feel warm in humid climates."
        ),
        sentiment=Sentiment.POSITIVE,
        sentiment_confidence=0.85,
        data_source=DataSource.DEMO,
    )


# ─────────────────────────────────────────────────────────────────────────────
# Routes
# ─────────────────────────────────────────────────────────────────────────────


@app.get("/api/health", tags=["System"])
async def health_check() -> dict:
    """Liveness check — returns 200 OK with service info."""
    return {
        "status": "ok",
        "service": "vrisko-api",
        "version": "0.2.0",
        "market": "IN",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "tinyfish_integration": "pending",
    }


@app.get("/api/markets", tags=["System"])
async def get_markets() -> dict:
    """Return all supported markets and their configured retailers."""
    return {
        "supported_markets": get_supported_markets(),
        "retailers": {
            code: [r.model_dump() for r in get_market_retailers(code)]
            for code in get_supported_markets()
        },
    }


@app.get("/api/demo", response_model=ComparisonResult, tags=["Demo"])
async def get_demo(country: str = Query("IN", description="Market code, e.g. 'IN' or 'UK'")) -> ComparisonResult:
    """
    Return a fully labelled DEMO DATA comparison result.
    Defaults to the Indian market configuration (Amazon India, Flipkart, Croma, Reliance Digital).
    """
    is_uk = country.upper() == "UK"
    query = "Sony WH-CH720N"
    currency = "GBP" if is_uk else "INR"

    request = CompareRequest(query=query, country="UK" if is_uk else "IN", currency=currency, include_used=True)
    offers = _build_uk_demo_offers() if is_uk else _build_india_demo_offers(query)
    reviews = _build_demo_reviews()

    result = build_comparison_result(
        request=request,
        raw_offers=offers,
        reviews=reviews,
        is_demo=True,
        data_source=DataSource.DEMO,
    )
    return result


@app.post("/api/compare", response_model=ComparisonResult, tags=["Compare"])
async def compare_products(request: CompareRequest) -> ComparisonResult:
    """
    Research and compare prices for an exact product model across all configured market retailers.

    The research engine investigates all retailers in the market configuration
    (Amazon India, Flipkart, Croma, Reliance Digital for India).
    """
    country = (request.country or "IN").upper().strip()
    is_uk = country == "UK"
    query = request.query.strip()

    if is_uk:
        offers = _build_uk_demo_offers()
        reviews = _build_demo_reviews()
    else:
        # Fetch multi-retailer research for ANY product model query
        researched_offers, reviews = get_product_research(query=query, country_code=country)

        # Reconcile across all 4 configured Indian retailers
        offers = reconcile_market_investigation(
            query=query,
            country_code=country,
            discovered_offers=researched_offers,
        )

    result = build_comparison_result(
        request=request,
        raw_offers=offers,
        reviews=reviews,
        is_demo=True,
        data_source=DataSource.DEMO,
    )

    result.product.query = request.query
    result.product.normalised_model = request.query.upper()
    return result
