
"""
Vrisko — Pydantic models.

These data models define the contract between the comparison engine,
the API layer, and the TinyFish research module.

Design rules:
- Unknown values are None, never zero.
- Retailer data must distinguish verified from unverified information.
- Conditional discounts are never automatically included in comparable totals.
- Live research, demo data and manual data are clearly distinguished.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


# ─────────────────────────────────────────────────────────────────────────────
# Enums
# ─────────────────────────────────────────────────────────────────────────────

class ProductCondition(str, Enum):
    NEW = "new"
    REFURBISHED = "refurbished"
    USED = "used"
    OPEN_BOX = "open_box"
    UNKNOWN = "unknown"


class Sentiment(str, Enum):
    POSITIVE = "positive"
    MIXED = "mixed"
    NEGATIVE = "negative"
    INSUFFICIENT_DATA = "insufficient_data"


class DataSource(str, Enum):
    """How a piece of data was obtained."""
    LIVE_RESEARCH = "live_research"
    DEMO = "demo"
    MANUAL = "manual"


class OfferAvailability(str, Enum):
    """Availability status of a retailer listing."""
    AVAILABLE = "available"
    UNAVAILABLE = "unavailable"
    UNKNOWN = "unknown"


# ─────────────────────────────────────────────────────────────────────────────
# Sub-models
# ─────────────────────────────────────────────────────────────────────────────

class ConditionalDiscount(BaseModel):
    """
    A discount that applies only when specific conditions are met.
    Never included in the comparable total automatically.
    """
    label: str = Field(
        ...,
        description="Human-readable condition, e.g. HDFC Bank card offer"
    )
    amount: Optional[float] = Field(
        None,
        description="Discount amount in listing currency, if known"
    )
    percentage: Optional[float] = Field(
        None,
        description="Discount percentage, if known"
    )
    condition_description: str = Field(
        ...,
        description="Full description of the qualifying condition"
    )
    is_verified: bool = Field(
        False,
        description="True if the condition was confirmed on the retailer page"
    )


class VerifiedField(BaseModel):
    """A value accompanied by its verification status."""
    value: Optional[str] = None
    is_verified: bool = False
    note: Optional[str] = None


# ─────────────────────────────────────────────────────────────────────────────
# Retailer Offer
# ─────────────────────────────────────────────────────────────────────────────

class RetailerOffer(BaseModel):
    """
    A single product listing from one retailer.

    Pricing rules:
    - listed_price: headline price shown on retailer page.
    - delivery_fee: None means unknown, not free.
    - comparable_total: listed_price + delivery_fee, only when both are known.
    """

    retailer_name: str
    retailer_url: Optional[str] = None
    product_url: Optional[str] = None

    # Pricing
    listed_price: Optional[float] = Field(None, ge=0)
    currency: str = Field("INR", description="ISO 4217 currency code")

    delivery_fee: Optional[float] = Field(
        None,
        description="None means unknown; zero means confirmed free delivery"
    )

    delivery_fee_unknown: bool = Field(
        False,
        description="True when delivery fee could not be determined"
    )

    comparable_total: Optional[float] = Field(
        None,
        description="Listed price plus delivery fee when both are known"
    )

    # Availability
    availability: OfferAvailability = Field(
        default=OfferAvailability.AVAILABLE
    )

    availability_note: Optional[str] = None

    # Discounts
    headline_discount_pct: Optional[float] = Field(
        None,
        ge=0,
        le=100
    )

    original_price: Optional[float] = Field(None, ge=0)

    conditional_discounts: list[ConditionalDiscount] = Field(
        default_factory=list
    )

    # Product details
    condition: ProductCondition = ProductCondition.UNKNOWN

    exact_model_match: bool = Field(
        True,
        description="False when listing may represent a different variant"
    )

    model_match_note: Optional[str] = None

    # Trust signals
    warranty: VerifiedField = Field(default_factory=VerifiedField)

    return_policy: VerifiedField = Field(default_factory=VerifiedField)

    is_verified: bool = Field(
        False,
        description="True when core listing details have been confirmed"
    )

    # Ratings
    rating: Optional[float] = Field(
        None,
        ge=0,
        le=5
    )

    review_count: Optional[int] = Field(None, ge=0)

    # Metadata
    data_source: DataSource = DataSource.LIVE_RESEARCH

    checked_at: Optional[datetime] = None


# ─────────────────────────────────────────────────────────────────────────────
# Customer Reviews
# ─────────────────────────────────────────────────────────────────────────────

class CustomerReviews(BaseModel):
    """Aggregated customer sentiment for a product model."""

    average_rating: Optional[float] = Field(
        None,
        ge=0,
        le=5
    )

    total_review_count: int = Field(0, ge=0)

    positive_feedback: Optional[str] = None

    negative_feedback: Optional[str] = None

    sentiment: Sentiment = Sentiment.INSUFFICIENT_DATA

    sentiment_confidence: Optional[float] = Field(
        None,
        ge=0,
        le=1
    )

    data_source: DataSource = DataSource.LIVE_RESEARCH


# ─────────────────────────────────────────────────────────────────────────────
# Evidence
# ─────────────────────────────────────────────────────────────────────────────

class EvidenceItem(BaseModel):
    """Evidence supporting a comparison result."""

    category: str
    label: str
    detail: Optional[str] = None
    source_url: Optional[str] = None


# ─────────────────────────────────────────────────────────────────────────────
# Comparison Summary
# ─────────────────────────────────────────────────────────────────────────────

class ComparisonSummary(BaseModel):

    cheapest_listed_price: Optional[RetailerOffer] = None

    best_verified_deal: Optional[RetailerOffer] = None

    best_conditional_offer: Optional[RetailerOffer] = Field(
        None,
        description=(
            "Offer with the lowest potential total after conditional discounts. "
            "Never treated as a confirmed price."
        )
    )

    highest_rated: Optional[RetailerOffer] = None

    recommendation: str = Field(
        "",
        description="Vrisko's overall recommendation"
    )

    recommendation_rationale: list[str] = Field(
        default_factory=list
    )


# ─────────────────────────────────────────────────────────────────────────────
# Product
# ─────────────────────────────────────────────────────────────────────────────

class Product(BaseModel):
    """The product being researched."""

    query: str = Field(
        ...,
        description="Raw product search query"
    )

    normalised_model: Optional[str] = None

    brand: Optional[str] = None

    category: Optional[str] = None


# ─────────────────────────────────────────────────────────────────────────────
# Comparison Result
# ─────────────────────────────────────────────────────────────────────────────

class ComparisonResult(BaseModel):
    """
    Top-level response returned by POST /api/compare.
    """

    product: Product

    offers: list[RetailerOffer] = Field(
        default_factory=list
    )

    reviews: Optional[CustomerReviews] = None

    summary: ComparisonSummary = Field(
        default_factory=ComparisonSummary
    )

    deal_integrity_score: Optional[int] = Field(
        None,
        ge=0,
        le=100
    )

    deal_integrity_explanation: Optional[str] = None

    evidence: list[EvidenceItem] = Field(
        default_factory=list
    )

    is_demo: bool = Field(
        False,
        description="True when result uses demo fixtures"
    )

    data_source: DataSource = DataSource.LIVE_RESEARCH

    generated_at: datetime = Field(
        default_factory=datetime.utcnow
    )

    error: Optional[str] = None


# ─────────────────────────────────────────────────────────────────────────────
# API Request
# ─────────────────────────────────────────────────────────────────────────────

class CompareRequest(BaseModel):

    query: str = Field(
        ...,
        min_length=2,
        max_length=200,
        description="Exact product model, e.g. Sony WH-CH720N"
    )

    country: str = Field(
        "IN",
        description="Market country code, e.g. IN or UK"
    )

    currency: str = Field(
        "INR",
        description="Preferred display currency"
    )

    include_used: bool = Field(
        False,
        description="Include refurbished or used listings"
    )
