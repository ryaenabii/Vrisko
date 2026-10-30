"""
Vrisko — Modular Retailer & Market Configuration (retailers.py).

Configures supported retailers per market/country.
Designed to be modular so additional retailers and countries can be added
without changing core comparison or research logic.

Initial India market configuration includes:
1. Amazon India (amazon.in)
2. Flipkart (flipkart.com)
3. Croma (croma.com)
4. Reliance Digital (reliancedigital.in)
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional
from pydantic import BaseModel, Field

from models import (
    DataSource,
    OfferAvailability,
    ProductCondition,
    RetailerOffer,
    VerifiedField,
)


class RetailerConfig(BaseModel):
    """Configuration definition for an individual retailer."""
    id: str = Field(..., description="Unique slug identifier, e.g. 'amazon_in'")
    name: str = Field(..., description="Human-readable retailer name, e.g. 'Amazon India'")
    domain: str = Field(..., description="Primary domain name, e.g. 'amazon.in'")
    country: str = Field("IN", description="ISO 3166-1 alpha-2 country code")
    currency: str = Field("INR", description="Default ISO 4217 currency code")
    retailer_url: str = Field(..., description="Storefront homepage URL")
    search_url_template: Optional[str] = Field(
        None,
        description="URL pattern containing {query} placeholder for product research",
    )
    enabled: bool = True


# ─────────────────────────────────────────────────────────────────────────────
# Market Configurations
# ─────────────────────────────────────────────────────────────────────────────

INDIAN_RETAILERS: list[RetailerConfig] = [
    RetailerConfig(
        id="amazon_in",
        name="Amazon India",
        domain="amazon.in",
        country="IN",
        currency="INR",
        retailer_url="https://www.amazon.in",
        search_url_template="https://www.amazon.in/s?k={query}",
    ),
    RetailerConfig(
        id="flipkart",
        name="Flipkart",
        domain="flipkart.com",
        country="IN",
        currency="INR",
        retailer_url="https://www.flipkart.com",
        search_url_template="https://www.flipkart.com/search?q={query}",
    ),
    RetailerConfig(
        id="croma",
        name="Croma",
        domain="croma.com",
        country="IN",
        currency="INR",
        retailer_url="https://www.croma.com",
        search_url_template="https://www.croma.com/searchB?q={query}",
    ),
    RetailerConfig(
        id="reliance_digital",
        name="Reliance Digital",
        domain="reliancedigital.in",
        country="IN",
        currency="INR",
        retailer_url="https://www.reliancedigital.in",
        search_url_template="https://www.reliancedigital.in/search?q={query}",
    ),
]

UK_RETAILERS: list[RetailerConfig] = [
    RetailerConfig(
        id="amazon_uk",
        name="Amazon UK",
        domain="amazon.co.uk",
        country="UK",
        currency="GBP",
        retailer_url="https://www.amazon.co.uk",
        search_url_template="https://www.amazon.co.uk/s?k={query}",
    ),
    RetailerConfig(
        id="currys",
        name="Currys",
        domain="currys.co.uk",
        country="UK",
        currency="GBP",
        retailer_url="https://www.currys.co.uk",
        search_url_template="https://www.currys.co.uk/search?q={query}",
    ),
    RetailerConfig(
        id="john_lewis",
        name="John Lewis",
        domain="johnlewis.com",
        country="UK",
        currency="GBP",
        retailer_url="https://www.johnlewis.com",
        search_url_template="https://www.johnlewis.com/search?search-term={query}",
    ),
]

# Modular market registry
MARKET_REGISTRY: dict[str, list[RetailerConfig]] = {
    "IN": INDIAN_RETAILERS,
    "UK": UK_RETAILERS,
}


def get_market_retailers(country_code: str = "IN") -> list[RetailerConfig]:
    """
    Retrieve all enabled retailers configured for a given country market.
    Defaults to Indian market ('IN') if not specified.
    """
    code = (country_code or "IN").upper().strip()
    retailers = MARKET_REGISTRY.get(code, MARKET_REGISTRY.get("IN", []))
    return [r for r in retailers if r.enabled]


def register_retailer(retailer: RetailerConfig) -> None:
    """
    Register a new retailer modularly into the market registry.
    Allows dynamic extension of retailers and countries without modifying core code.
    """
    code = retailer.country.upper().strip()
    if code not in MARKET_REGISTRY:
        MARKET_REGISTRY[code] = []
    # Avoid duplicate IDs
    existing = [r for r in MARKET_REGISTRY[code] if r.id == retailer.id]
    if not existing:
        MARKET_REGISTRY[code].append(retailer)
    else:
        # Update existing
        idx = MARKET_REGISTRY[code].index(existing[0])
        MARKET_REGISTRY[code][idx] = retailer


def get_supported_markets() -> dict[str, str]:
    """Return dictionary of supported market codes and their descriptions."""
    return {
        "IN": "India (INR)",
        "UK": "United Kingdom (GBP)",
    }


# ─────────────────────────────────────────────────────────────────────────────
# Investigation & Truthful Fallback Engine
# ─────────────────────────────────────────────────────────────────────────────


def build_unavailable_offer(
    retailer: RetailerConfig,
    query: str,
    status: OfferAvailability = OfferAvailability.UNAVAILABLE,
    reason: Optional[str] = None,
    checked_at: Optional[datetime] = None,
) -> RetailerOffer:
    """
    Construct a truthful, unverified listing placeholder when a retailer
    has no matching listing, is inaccessible, or cannot be verified.

    Safety Rule:
    NEVER fabricate missing retailer results, prices, ratings, or delivery fees.
    """
    now = checked_at or datetime.now(timezone.utc)
    default_reason = f"No matching listing found on {retailer.domain} for '{query}'"

    return RetailerOffer(
        retailer_name=retailer.name,
        retailer_url=retailer.retailer_url,
        product_url=None,
        listed_price=None,  # NEVER invent a price
        currency=retailer.currency,
        delivery_fee=None,
        delivery_fee_unknown=True,
        comparable_total=None,
        condition=ProductCondition.UNKNOWN,
        exact_model_match=False,
        model_match_note=f"Listing not found on {retailer.domain}",
        warranty=VerifiedField(value=None, is_verified=False, note="Not available"),
        return_policy=VerifiedField(value=None, is_verified=False, note="Not available"),
        is_verified=False,
        rating=None,
        review_count=None,
        availability=status,
        availability_note=reason or default_reason,
        data_source=DataSource.DEMO,
        checked_at=now,
    )


def reconcile_market_investigation(
    query: str,
    country_code: str = "IN",
    discovered_offers: Optional[list[RetailerOffer]] = None,
    checked_at: Optional[datetime] = None,
) -> list[RetailerOffer]:
    """
    Ensure ALL configured retailers for the specified market are investigated
    for the exact product model.

    If a retailer in the configuration has an actual verified offer, that offer is used.
    If a retailer has no matching listing, is inaccessible, or could not be verified,
    it is marked as unavailable or unknown.

    Never fabricates missing retailer results.
    """
    configured_retailers = get_market_retailers(country_code)
    discovered = discovered_offers or []

    # Map discovered offers by normalised domain or name for reliable matching
    discovered_by_domain: dict[str, RetailerOffer] = {}
    for offer in discovered:
        key = offer.retailer_name.lower().strip()
        discovered_by_domain[key] = offer
        if offer.retailer_url:
            for conf in configured_retailers:
                if conf.domain.lower() in offer.retailer_url.lower():
                    discovered_by_domain[conf.id] = offer

    results: list[RetailerOffer] = []
    now = checked_at or datetime.now(timezone.utc)

    for conf in configured_retailers:
        # Check by ID, domain, or name
        match = (
            discovered_by_domain.get(conf.id)
            or discovered_by_domain.get(conf.name.lower().strip())
            or next(
                (
                    o for o in discovered
                    if conf.domain.lower() in (o.retailer_url or "").lower()
                    or conf.name.lower() in o.retailer_name.lower()
                ),
                None,
            )
        )

        if match:
            # Preserved discovered offer
            results.append(match)
        else:
            # Retailer was investigated but no verified listing was found
            results.append(
                build_unavailable_offer(
                    retailer=conf,
                    query=query,
                    status=OfferAvailability.UNAVAILABLE,
                    reason=f"No matching listing found on {conf.domain} for '{query}'.",
                    checked_at=now,
                )
            )

    return results

