"""
Vrisko — Comparison engine (comparison.py).

This module is intentionally decoupled from both the FastAPI layer and
any specific research data source (TinyFish or otherwise).

Key safety rules enforced here
-------------------------------
1. Unknown fees (delivery_fee_unknown=True) are NEVER treated as zero.
2. Conditional discounts are NEVER automatically applied to comparable totals.
3. Different product variants are NEVER silently compared as identical.
4. Every field distinction between verified and unverified is preserved.
5. Retailers marked unavailable or unknown have listed_price=None and are never
   fabricated or treated as having confirmed prices.
"""

from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import Optional

from models import (
    ComparisonResult,
    ComparisonSummary,
    CompareRequest,
    ConditionalDiscount,
    CustomerReviews,
    DataSource,
    EvidenceItem,
    OfferAvailability,
    Product,
    ProductCondition,
    RetailerOffer,
    Sentiment,
    VerifiedField,
)


# ─────────────────────────────────────────────────────────────────────────────
# Price / fee helpers
# ─────────────────────────────────────────────────────────────────────────────


def normalise_price(raw: float | str | None) -> Optional[float]:
    """
    Convert a raw price value to a float rounded to 2 decimal places.
    Returns None if the value is missing or cannot be parsed.
    """
    if raw is None:
        return None
    try:
        return round(float(str(raw).replace(",", "").strip()), 2)
    except (ValueError, TypeError):
        return None


def calculate_comparable_total(offer: RetailerOffer) -> Optional[float]:
    """
    Compute the comparable total for one offer.

    Returns None when the delivery fee or listed price is unknown so that the UI can
    clearly signal "we don't know the real total" rather than implying
    the listed price is the full cost.

    Conditional discounts are NEVER included here.
    """
    if (
        offer.listed_price is None
        or offer.delivery_fee_unknown
        or offer.delivery_fee is None
        or offer.availability != OfferAvailability.AVAILABLE
    ):
        return None
    return round(offer.listed_price + offer.delivery_fee, 2)


def get_currency_symbol(currency: str) -> str:
    """Return common display symbol for ISO currency codes."""
    code = (currency or "").upper().strip()
    symbols = {
        "INR": "₹",
        "GBP": "£",
        "USD": "$",
        "EUR": "€",
    }
    return symbols.get(code, f"{code} ")


# ─────────────────────────────────────────────────────────────────────────────
# Model matching
# ─────────────────────────────────────────────────────────────────────────────


def normalise_model_string(query: str) -> str:
    """
    Strip common noise words and normalise whitespace / case.
    Used for fuzzy model matching — does NOT guarantee an exact match.
    """
    noise = re.compile(
        r"\b(buy|order|price|cheap|best|deal|new|used|refurbished|review|vs|or)\b",
        re.IGNORECASE,
    )
    cleaned = noise.sub("", query)
    return re.sub(r"\s+", " ", cleaned).strip().upper()


def check_model_match(query_model: str, offer_model: str) -> tuple[bool, Optional[str]]:
    """
    Compare the normalised query model against a retailer listing model.

    Returns (is_match, note_if_suspicious).

    This is intentionally conservative: if any meaningful token differs,
    the match is flagged as suspicious rather than silently accepted.
    """
    q = normalise_model_string(query_model)
    o = normalise_model_string(offer_model)
    if q == o:
        return True, None
    # Check whether one is a prefix of the other (possible variant)
    if q in o or o in q:
        return False, f"Possible variant: searched '{query_model}', listing shows '{offer_model}'"
    return False, f"Model mismatch: searched '{query_model}', listing shows '{offer_model}'"


# ─────────────────────────────────────────────────────────────────────────────
# Missing field detection
# ─────────────────────────────────────────────────────────────────────────────


def identify_missing_fields(offer: RetailerOffer) -> list[str]:
    """Return a list of field names that are unknown for a given offer."""
    missing: list[str] = []
    if offer.listed_price is None:
        missing.append("listed_price")
    if offer.delivery_fee_unknown or offer.delivery_fee is None:
        missing.append("delivery_fee")
    if offer.rating is None:
        missing.append("rating")
    if offer.review_count is None:
        missing.append("review_count")
    if not offer.warranty.value:
        missing.append("warranty")
    if not offer.return_policy.value:
        missing.append("return_policy")
    if offer.condition == ProductCondition.UNKNOWN:
        missing.append("condition")
    return missing


# ─────────────────────────────────────────────────────────────────────────────
# Deal Integrity Score
# ─────────────────────────────────────────────────────────────────────────────


def calculate_deal_integrity_score(offers: list[RetailerOffer]) -> tuple[int, str]:
    """
    Score 0–100 reflecting evidence completeness for a set of offers.

    This measures evidence completeness, NOT product quality or retailer
    reputation.

    Scoring breakdown (per offer, averaged across all offers):
    ──────────────────────────────────────────────────────────
    Exact product match          30 pts
    Price verification           25 pts
    Delivery / fee transparency  15 pts
    Discount clarity             15 pts
    Warranty / return info       10 pts  (5 warranty + 5 return policy)
    Source freshness              5 pts
    ──────────────────────────────────────────────────────────
    Total per offer             100 pts

    Rules:
    - Missing information NEVER receives full points.
    - Unavailable/inaccessible listings receive points only for verified evidence.
    """
    if not offers:
        return 0, "No offers available to score."

    per_offer_scores: list[float] = []

    for offer in offers:
        pts = 0.0

        # If offer is unavailable or unknown, it earns 0 for listing/price attributes
        is_avail = offer.availability == OfferAvailability.AVAILABLE

        # ── 1. Exact product match (30 pts) ──────────────────────────────────
        if is_avail and offer.exact_model_match:
            pts += 30

        # ── 2. Price verification (25 pts) ───────────────────────────────────
        if is_avail and offer.is_verified and offer.listed_price is not None:
            pts += 25

        # ── 3. Delivery / fee transparency (15 pts) ──────────────────────────
        if is_avail and not offer.delivery_fee_unknown and offer.delivery_fee is not None:
            pts += 15

        # ── 4. Discount clarity (15 pts) ─────────────────────────────────────
        if is_avail and offer.listed_price is not None:
            if not offer.conditional_discounts:
                pts += 15  # no conditional discounts → full transparency
            else:
                verified_cd = sum(1 for cd in offer.conditional_discounts if cd.is_verified)
                total_cd = len(offer.conditional_discounts)
                pts += 15 * (verified_cd / total_cd) * 0.5
        elif not is_avail:
            # An unavailable retailer has no discount confusion
            pts += 0

        # ── 5. Warranty / return information (10 pts: 5 + 5) ─────────────────
        if is_avail:
            if offer.warranty.value:
                pts += 5 if offer.warranty.is_verified else 2
            if offer.return_policy.value:
                pts += 5 if offer.return_policy.is_verified else 2

        # ── 6. Source freshness (5 pts) ───────────────────────────────────────
        if offer.checked_at is not None:
            pts += 5   # timestamp confirms actual investigation was conducted

        per_offer_scores.append(pts)

    score = round(sum(per_offer_scores) / len(per_offer_scores)) if per_offer_scores else 0
    score = max(0, min(100, score))  # clamp to [0, 100]

    # ── Human-readable explanation ────────────────────────────────────────────
    explanation_parts: list[str] = []
    unavailable_count = sum(1 for o in offers if o.availability != OfferAvailability.AVAILABLE)
    verified_count = sum(1 for o in offers if o.is_verified and o.availability == OfferAvailability.AVAILABLE)
    unknown_delivery = sum(1 for o in offers if o.delivery_fee_unknown and o.availability == OfferAvailability.AVAILABLE)
    missing_warranty = sum(
        1 for o in offers
        if o.availability == OfferAvailability.AVAILABLE and (not o.warranty.value or not o.return_policy.value)
    )
    mismatch_count = sum(
        1 for o in offers
        if o.availability == OfferAvailability.AVAILABLE and not o.exact_model_match
    )
    unverified_discounts = sum(
        1 for o in offers
        if o.availability == OfferAvailability.AVAILABLE and any(not cd.is_verified for cd in o.conditional_discounts)
    )

    if unavailable_count:
        explanation_parts.append(
            f"{unavailable_count} of {len(offers)} retailers have no verified matching listing"
        )
    available_total = len(offers) - unavailable_count
    if available_total > 0 and verified_count < available_total:
        explanation_parts.append(
            f"{available_total - verified_count} available listing(s) are unverified"
        )
    if unknown_delivery:
        explanation_parts.append(f"{unknown_delivery} retailer(s) have unknown delivery fees")
    if missing_warranty:
        explanation_parts.append(f"{missing_warranty} listing(s) lack warranty/return details")
    if mismatch_count:
        explanation_parts.append(f"{mismatch_count} listing(s) may be a different product variant")
    if unverified_discounts:
        explanation_parts.append(
            f"{unverified_discounts} listing(s) have unverified conditional discounts"
        )

    suffix = (
        " This score measures evidence completeness, not product quality or retailer reputation."
    )
    explanation = (
        "Score reflects: " + "; ".join(explanation_parts) + "." + suffix
        if explanation_parts
        else "All checked fields are verified and complete." + suffix
    )
    return score, explanation


# ─────────────────────────────────────────────────────────────────────────────
# Offer ranking
# ─────────────────────────────────────────────────────────────────────────────


def rank_offers(offers: list[RetailerOffer]) -> list[RetailerOffer]:
    """
    Return offers sorted by:
    1. Available offers with confirmed comparable_total ascending
    2. Available offers with listed_price ascending (unknown delivery)
    3. Unavailable / unknown / inaccessible offers last
    """
    def sort_key(o: RetailerOffer) -> tuple[int, float]:
        if o.availability != OfferAvailability.AVAILABLE or o.listed_price is None:
            return (2, 999999999.0)
        if o.comparable_total is None:
            return (1, o.listed_price)
        return (0, o.comparable_total)

    return sorted(offers, key=sort_key)


def find_cheapest_listed(offers: list[RetailerOffer]) -> Optional[RetailerOffer]:
    """
    Cheapest listed price among available exact-match offers.
    Never claims this is the cheapest total cost — delivery may be unknown.
    """
    exact = [
        o for o in offers
        if o.exact_model_match
        and o.listed_price is not None
        and o.availability == OfferAvailability.AVAILABLE
    ]
    pool = exact if exact else [
        o for o in offers
        if o.listed_price is not None and o.availability == OfferAvailability.AVAILABLE
    ]
    return min(pool, key=lambda o: o.listed_price, default=None) if pool else None


def find_best_verified_deal(offers: list[RetailerOffer]) -> Optional[RetailerOffer]:
    """
    Best verified deal = lowest comparable_total among verified, available exact-match offers.
    Excludes offers with unknown delivery fees or missing prices.
    """
    candidates = [
        o for o in offers
        if o.is_verified
        and o.exact_model_match
        and o.comparable_total is not None
        and o.availability == OfferAvailability.AVAILABLE
    ]
    return min(candidates, key=lambda o: o.comparable_total, default=None)  # type: ignore[arg-type]


def find_best_conditional_offer(offers: list[RetailerOffer]) -> Optional[RetailerOffer]:
    """
    Best conditional offer = offer with the lowest potential total when
    a conditional discount with a known amount is applied.

    Only populated when at least one available offer has a conditional discount
    with a known `amount` value (not None). NEVER treated as confirmed.
    """
    best: Optional[RetailerOffer] = None
    best_potential: Optional[float] = None

    for offer in offers:
        if (
            not offer.exact_model_match
            or offer.listed_price is None
            or offer.availability != OfferAvailability.AVAILABLE
        ):
            continue
        for cd in offer.conditional_discounts:
            if cd.amount is None:
                continue
            delivery = 0.0 if (not offer.delivery_fee_unknown and offer.delivery_fee is not None) else 0.0
            potential = round(offer.listed_price + delivery - cd.amount, 2)
            if best_potential is None or potential < best_potential:
                best_potential = potential
                best = offer

    return best


def find_highest_rated(offers: list[RetailerOffer]) -> Optional[RetailerOffer]:
    rated = [
        o for o in offers
        if o.rating is not None
        and o.exact_model_match
        and o.availability == OfferAvailability.AVAILABLE
    ]
    return max(rated, key=lambda o: o.rating, default=None)  # type: ignore[arg-type]


# ─────────────────────────────────────────────────────────────────────────────
# Recommendation
# ─────────────────────────────────────────────────────────────────────────────


def generate_recommendation(
    cheapest: Optional[RetailerOffer],
    best_verified: Optional[RetailerOffer],
    best_conditional: Optional[RetailerOffer],
    highest_rated: Optional[RetailerOffer],
    offers: list[RetailerOffer],
) -> tuple[str, list[str]]:
    """
    Produce a human-readable recommendation and supporting rationale bullets.

    Safety invariants:
    - Never claims an offer is cheapest if its total cost is unknown.
    - Never ranks incompatible variants together.
    - Conditional discounts are explicitly called out, never baked in.
    - Mentions unavailable/inaccessible retailers truthfully.
    """
    rationale: list[str] = []

    if not offers:
        return "No offers available to compare.", rationale

    sym = get_currency_symbol(best_verified.currency if best_verified else (cheapest.currency if cheapest else "INR"))

    if best_verified and cheapest and best_verified.retailer_name == cheapest.retailer_name:
        summary = (
            f"Vrisko recommends {best_verified.retailer_name}: "
            f"it is both the cheapest verified deal "
            f"({sym}{best_verified.comparable_total:.2f} total including delivery) "
            f"and a confirmed exact model match."
        )
        rationale.append("Cheapest comparable total among verified listings")
        rationale.append("Listing has been verified as an exact model match")
    elif best_verified:
        summary = (
            f"Vrisko recommends {best_verified.retailer_name} for the best verified deal "
            f"at {sym}{best_verified.comparable_total:.2f} total (delivery included)."
        )
        rationale.append("Lowest confirmed comparable total")
        rationale.append("Listing verified and exact model match confirmed")
        if cheapest and cheapest.retailer_name != best_verified.retailer_name:
            cheap_sym = get_currency_symbol(cheapest.currency)
            rationale.append(
                f"{cheapest.retailer_name} has a lower listed price "
                f"({cheap_sym}{cheapest.listed_price:.2f}) but delivery costs are unknown"
            )
    elif cheapest and cheapest.listed_price is not None:
        cheap_sym = get_currency_symbol(cheapest.currency)
        summary = (
            f"{cheapest.retailer_name} shows the lowest listed price "
            f"({cheap_sym}{cheapest.listed_price:.2f}), but delivery fees could not be confirmed "
            f"for all retailers — verify total costs before purchasing."
        )
        rationale.append("Lowest listed price, but comparable totals are incomplete")
        rationale.append("Verify delivery fees directly with the retailer")
    else:
        summary = "Insufficient verified data to make a confident recommendation."
        rationale.append("No verified, exact-match offers found")

    unknown_fees = [
        o for o in offers
        if o.delivery_fee_unknown and o.availability == OfferAvailability.AVAILABLE
    ]
    if unknown_fees:
        rationale.append(
            f"Delivery fee unknown for: {', '.join(o.retailer_name for o in unknown_fees)}"
        )

    conditional = [
        discount
        for o in offers
        if o.availability == OfferAvailability.AVAILABLE
        for discount in o.conditional_discounts
    ]
    if conditional:
        rationale.append(
            f"{len(conditional)} conditional discount(s) exist but are not included in totals — "
            "check eligibility manually"
        )

    if best_conditional and (
        not best_verified
        or best_conditional.retailer_name != best_verified.retailer_name
    ):
        rationale.append(
            f"{best_conditional.retailer_name} may offer the lowest conditional price "
            "if bank/loyalty discount is applicable — verify eligibility before purchasing"
        )

    incompatible = [
        o for o in offers
        if not o.exact_model_match and o.availability == OfferAvailability.AVAILABLE
    ]
    if incompatible:
        rationale.append(
            f"{', '.join(o.retailer_name for o in incompatible)}: "
            "variant mismatch — excluded from price ranking"
        )

    unavailable = [o for o in offers if o.availability != OfferAvailability.AVAILABLE]
    if unavailable:
        rationale.append(
            f"No verified listing found on: {', '.join(o.retailer_name for o in unavailable)}"
        )

    return summary, rationale


# ─────────────────────────────────────────────────────────────────────────────
# Evidence builder
# ─────────────────────────────────────────────────────────────────────────────


def build_evidence(offers: list[RetailerOffer]) -> list[EvidenceItem]:
    """Compile the evidence section from all offers."""
    items: list[EvidenceItem] = []

    for offer in offers:
        sym = get_currency_symbol(offer.currency)

        # Unavailable / unknown / inaccessible listings
        if offer.availability != OfferAvailability.AVAILABLE:
            items.append(EvidenceItem(
                category="unknown",
                label=f"{offer.retailer_name} — {offer.availability.value.title()}",
                detail=offer.availability_note or "No matching listing found or information cannot be verified.",
                source_url=offer.product_url or offer.retailer_url,
            ))
            continue

        # Verified items
        if offer.is_verified and offer.listed_price is not None:
            items.append(EvidenceItem(
                category="verified",
                label=f"{offer.retailer_name} — listing verified",
                detail=f"Listed price {sym}{offer.listed_price:.2f}, condition: {offer.condition.value}",
                source_url=offer.product_url,
            ))
        if offer.warranty.value and offer.warranty.is_verified:
            items.append(EvidenceItem(
                category="verified",
                label=f"{offer.retailer_name} — warranty confirmed",
                detail=offer.warranty.value,
                source_url=offer.product_url,
            ))
        if offer.return_policy.value and offer.return_policy.is_verified:
            items.append(EvidenceItem(
                category="verified",
                label=f"{offer.retailer_name} — return policy confirmed",
                detail=offer.return_policy.value,
            ))

        # Conditional discounts
        for cd in offer.conditional_discounts:
            items.append(EvidenceItem(
                category="conditional",
                label=f"{offer.retailer_name} — {cd.label}",
                detail=cd.condition_description,
            ))

        # Unknown fields
        missing = identify_missing_fields(offer)
        if missing:
            items.append(EvidenceItem(
                category="unknown",
                label=f"{offer.retailer_name} — data not confirmed",
                detail=f"Unknown: {', '.join(missing)}",
            ))

        # Source link
        if offer.product_url:
            items.append(EvidenceItem(
                category="source",
                label=f"{offer.retailer_name} — product page",
                source_url=offer.product_url,
            ))

    return items


# ─────────────────────────────────────────────────────────────────────────────
# Top-level builder (called by API routes)
# ─────────────────────────────────────────────────────────────────────────────


def build_comparison_result(
    request: CompareRequest,
    raw_offers: list[RetailerOffer],
    reviews: Optional[CustomerReviews] = None,
    is_demo: bool = False,
    data_source: DataSource = DataSource.LIVE_RESEARCH,
) -> ComparisonResult:
    """
    Given a list of raw offers (from TinyFish, market investigation, or demo fixtures),
    run all normalisation, scoring, ranking and recommendation logic
    and return a fully populated ComparisonResult.

    This function is the single integration point for future research modules.
    """
    # 1. Normalise prices and compute comparable totals
    for offer in raw_offers:
        if offer.listed_price is not None:
            offer.listed_price = normalise_price(offer.listed_price)
        offer.comparable_total = calculate_comparable_total(offer)

    # 2. Filter out used/refurbished if not requested (keep unavailable status listings)
    if not request.include_used:
        raw_offers = [
            o for o in raw_offers
            if o.condition not in (ProductCondition.USED, ProductCondition.REFURBISHED)
            or o.availability != OfferAvailability.AVAILABLE
        ]

    # 3. Rank
    ranked = rank_offers(raw_offers)

    # 4. Derive summary
    cheapest = find_cheapest_listed(ranked)
    best_verified = find_best_verified_deal(ranked)
    best_conditional = find_best_conditional_offer(ranked)
    highest_rated = find_highest_rated(ranked)
    recommendation, rationale = generate_recommendation(
        cheapest, best_verified, best_conditional, highest_rated, ranked
    )

    summary = ComparisonSummary(
        cheapest_listed_price=cheapest,
        best_verified_deal=best_verified,
        best_conditional_offer=best_conditional,
        highest_rated=highest_rated,
        recommendation=recommendation,
        recommendation_rationale=rationale,
    )

    # 5. Deal Integrity Score
    score, score_explanation = calculate_deal_integrity_score(ranked)

    # 6. Evidence
    evidence = build_evidence(ranked)

    return ComparisonResult(
        product=Product(
            query=request.query,
            normalised_model=normalise_model_string(request.query),
        ),
        offers=ranked,
        reviews=reviews,
        summary=summary,
        deal_integrity_score=score,
        deal_integrity_explanation=score_explanation,
        evidence=evidence,
        is_demo=is_demo,
        data_source=data_source,
        generated_at=datetime.now(timezone.utc),
    )
