"""
Vrisko — Backend automated tests (tests/test_comparison.py).

Run from the backend directory with the venv activated:
    pytest tests/ -v

All tests use pure Python — no live network calls, no TinyFish.
"""

from __future__ import annotations

import sys
import os
from datetime import datetime, timezone
from typing import Optional

# Make the backend package importable from the tests sub-directory
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest

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
    INDIAN_RETAILERS,
    RetailerConfig,
    build_unavailable_offer,
    get_market_retailers,
    reconcile_market_investigation,
    register_retailer,
)
from comparison import (
    build_comparison_result,
    calculate_comparable_total,
    calculate_deal_integrity_score,
    find_best_conditional_offer,
    find_best_verified_deal,
    find_cheapest_listed,
    find_highest_rated,
    normalise_model_string,
    normalise_price,
    rank_offers,
)


# ---------------------------------------------------------------------------
# Helpers / fixtures
# ---------------------------------------------------------------------------

NOW = datetime.now(timezone.utc)


def make_offer(
    retailer_name="TestShop",
    listed_price=100.0,
    delivery_fee=0.0,
    delivery_fee_unknown=False,
    is_verified=True,
    exact_model_match=True,
    condition=ProductCondition.NEW,
    rating=4.0,
    review_count=100,
    warranty_value="1-year",
    warranty_verified=True,
    return_value="30-day",
    return_verified=True,
    conditional_discounts=None,
    checked_at=NOW,
):
    """
    Construct a RetailerOffer and pre-compute its comparable_total so that
    tests calling engine functions directly get consistent results
    (build_comparison_result does the same computation internally).
    """
    offer = RetailerOffer(
        retailer_name=retailer_name,
        listed_price=listed_price,
        currency="GBP",
        delivery_fee=delivery_fee,
        delivery_fee_unknown=delivery_fee_unknown,
        condition=condition,
        is_verified=is_verified,
        exact_model_match=exact_model_match,
        rating=rating,
        review_count=review_count,
        warranty=VerifiedField(value=warranty_value, is_verified=warranty_verified),
        return_policy=VerifiedField(value=return_value, is_verified=return_verified),
        conditional_discounts=conditional_discounts or [],
        data_source=DataSource.DEMO,
        checked_at=checked_at,
    )
    # Pre-compute comparable_total so direct engine function calls are consistent
    offer.comparable_total = calculate_comparable_total(offer)
    return offer


def make_request(query="TestProduct X1", include_used=True):
    return CompareRequest(query=query, currency="GBP", include_used=include_used)


# ---------------------------------------------------------------------------
# 1. Normal price calculation
# ---------------------------------------------------------------------------

class TestNormalPriceCalculation:
    def test_comparable_total_with_known_delivery(self):
        """listed_price + delivery_fee = comparable_total when both are known."""
        offer = make_offer(listed_price=89.00, delivery_fee=4.99)
        total = calculate_comparable_total(offer)
        assert total == 93.99

    def test_comparable_total_with_free_delivery(self):
        """Confirmed free delivery (0.0) yields listed_price as the total."""
        offer = make_offer(listed_price=89.00, delivery_fee=0.0)
        total = calculate_comparable_total(offer)
        assert total == 89.00

    def test_normalise_price_strips_commas(self):
        assert normalise_price("1,299.99") == 1299.99

    def test_normalise_price_rounds_to_two_dp(self):
        assert normalise_price(99.999) == 100.0

    def test_normalise_price_none_returns_none(self):
        assert normalise_price(None) is None

    def test_normalise_price_garbage_returns_none(self):
        assert normalise_price("N/A") is None

    def test_build_result_populates_comparable_total(self):
        """build_comparison_result must compute comparable_total for each offer."""
        # Create offer WITHOUT pre-computed total to test the builder
        offer = RetailerOffer(
            retailer_name="Builder Test",
            listed_price=50.00,
            currency="GBP",
            delivery_fee=5.00,
            delivery_fee_unknown=False,
            is_verified=True,
            exact_model_match=True,
            warranty=VerifiedField(value="1yr", is_verified=True),
            return_policy=VerifiedField(value="30d", is_verified=True),
            data_source=DataSource.DEMO,
        )
        result = build_comparison_result(make_request(), [offer])
        assert result.offers[0].comparable_total == 55.00


# ---------------------------------------------------------------------------
# 2. Unknown delivery fee — never treated as zero
# ---------------------------------------------------------------------------

class TestUnknownDeliveryFee:
    def test_unknown_fee_gives_none_total(self):
        """delivery_fee_unknown=True must yield comparable_total=None, not 0."""
        offer = make_offer(delivery_fee=None, delivery_fee_unknown=True)
        total = calculate_comparable_total(offer)
        assert total is None, "Unknown delivery fee must not be treated as zero"

    def test_unknown_fee_offer_not_selected_as_best_verified(self):
        """Offers with unknown delivery fees are excluded from best_verified_deal."""
        unknown = make_offer(retailer_name="Unknown Delivery", listed_price=50.0,
                             delivery_fee=None, delivery_fee_unknown=True)
        known = make_offer(retailer_name="Known Delivery", listed_price=55.0,
                           delivery_fee=0.0)
        result = build_comparison_result(make_request(), [unknown, known])
        assert result.summary.best_verified_deal is not None
        assert result.summary.best_verified_deal.retailer_name == "Known Delivery"

    def test_unknown_fee_preserved_in_result(self):
        """delivery_fee_unknown flag must survive build_comparison_result."""
        offer = make_offer(delivery_fee=None, delivery_fee_unknown=True)
        result = build_comparison_result(make_request(), [offer])
        assert result.offers[0].delivery_fee_unknown is True
        assert result.offers[0].comparable_total is None

    def test_unknown_fee_not_cheapest_when_known_exists(self):
        """
        rank_offers must put offers with a known comparable_total before
        offers with unknown totals, regardless of listed price.
        """
        unknown = make_offer(retailer_name="Cheap Listed",
                             listed_price=40.0,
                             delivery_fee=None, delivery_fee_unknown=True)
        known = make_offer(retailer_name="Full Total Known",
                           listed_price=45.0, delivery_fee=0.0)
        # Both offers already have comparable_total set by make_offer:
        # unknown.comparable_total = None, known.comparable_total = 45.0
        assert unknown.comparable_total is None
        assert known.comparable_total == 45.0
        ranked = rank_offers([unknown, known])
        assert ranked[0].retailer_name == "Full Total Known", (
            "Known-total offer must rank before unknown-total offer"
        )


# ---------------------------------------------------------------------------
# 3. Conditional bank discount
# ---------------------------------------------------------------------------

class TestConditionalBankDiscount:
    def test_conditional_discount_not_in_comparable_total(self):
        """
        A conditional discount (bank offer) must never reduce the comparable_total.
        The comparable_total = listed_price + delivery_fee only.
        """
        cd = ConditionalDiscount(
            label="HDFC Bank",
            amount=10.00,
            percentage=None,
            condition_description="Rs 1000 off on HDFC cards",
            is_verified=True,
        )
        offer = make_offer(listed_price=100.0, delivery_fee=0.0,
                           conditional_discounts=[cd])
        total = calculate_comparable_total(offer)
        assert total == 100.0, "Conditional discount must NOT reduce comparable_total"

    def test_best_conditional_offer_identified(self):
        """find_best_conditional_offer selects the offer with lowest potential total."""
        cd_small = ConditionalDiscount(
            label="Card offer", amount=5.0, percentage=None,
            condition_description="5 off", is_verified=True,
        )
        cd_large = ConditionalDiscount(
            label="Bank offer", amount=20.0, percentage=None,
            condition_description="20 off", is_verified=True,
        )
        offer_small = make_offer(retailer_name="ShopA", listed_price=100.0,
                                 delivery_fee=0.0, conditional_discounts=[cd_small])
        offer_large = make_offer(retailer_name="ShopB", listed_price=100.0,
                                 delivery_fee=0.0, conditional_discounts=[cd_large])
        best = find_best_conditional_offer([offer_small, offer_large])
        assert best is not None
        assert best.retailer_name == "ShopB"

    def test_unknown_amount_conditional_not_ranked(self):
        """
        If a conditional discount has amount=None (unknown),
        it must not contribute to the best_conditional_offer ranking.
        """
        cd_unknown = ConditionalDiscount(
            label="Mystery offer", amount=None, percentage=None,
            condition_description="Some discount", is_verified=False,
        )
        offer = make_offer(conditional_discounts=[cd_unknown])
        best = find_best_conditional_offer([offer])
        assert best is None, "Unknown discount amount must not influence conditional ranking"

    def test_conditional_discount_appears_in_evidence(self):
        """Conditional discounts must appear in the evidence list as 'conditional' category."""
        cd = ConditionalDiscount(
            label="Bank offer", amount=10.0, percentage=None,
            condition_description="10 off on bank card", is_verified=False,
        )
        offer = make_offer(conditional_discounts=[cd])
        result = build_comparison_result(make_request(), [offer])
        conditional_items = [e for e in result.evidence if e.category == "conditional"]
        assert len(conditional_items) >= 1

    def test_unverified_conditional_discount_is_flagged(self):
        """Unverified conditional discounts reduce the deal integrity score."""
        offer_with_unverified_cd = make_offer(
            conditional_discounts=[
                ConditionalDiscount(
                    label="Unverified offer", amount=5.0, percentage=None,
                    condition_description="Unverified", is_verified=False,
                )
            ]
        )
        offer_clean = make_offer(retailer_name="CleanShop")
        score_with, _ = calculate_deal_integrity_score([offer_with_unverified_cd])
        score_clean, _ = calculate_deal_integrity_score([offer_clean])
        assert score_with < score_clean, (
            "Unverified conditional discount must lower integrity score vs. no discount"
        )


# ---------------------------------------------------------------------------
# 4. Different variants rejected / flagged
# ---------------------------------------------------------------------------

class TestDifferentVariants:
    def test_variant_mismatch_excluded_from_best_verified(self):
        """An offer with exact_model_match=False must not appear as best_verified_deal."""
        mismatch = make_offer(retailer_name="WrongVariant", listed_price=50.0,
                              delivery_fee=0.0, exact_model_match=False)
        exact = make_offer(retailer_name="ExactMatch", listed_price=80.0,
                           delivery_fee=0.0, exact_model_match=True)
        best = find_best_verified_deal([mismatch, exact])
        assert best is not None
        assert best.retailer_name == "ExactMatch"

    def test_variant_mismatch_excluded_from_highest_rated(self):
        """exact_model_match=False offers are excluded from the highest-rated slot."""
        mismatch = make_offer(retailer_name="WrongVariant", rating=5.0,
                              exact_model_match=False)
        exact = make_offer(retailer_name="ExactMatch", rating=4.0,
                           exact_model_match=True)
        best = find_highest_rated([mismatch, exact])
        assert best is not None
        assert best.retailer_name == "ExactMatch"

    def test_variant_mismatch_excluded_from_conditional_ranking(self):
        """exact_model_match=False offers are excluded from best_conditional_offer."""
        cd = ConditionalDiscount(label="Offer", amount=30.0, percentage=None,
                                 condition_description="Big discount", is_verified=True)
        mismatch = make_offer(retailer_name="WrongVariant", listed_price=50.0,
                              delivery_fee=0.0, exact_model_match=False,
                              conditional_discounts=[cd])
        best = find_best_conditional_offer([mismatch])
        assert best is None, "Variant mismatch must not appear as best conditional offer"

    def test_variant_mismatch_note_preserved(self):
        """model_match_note must be preserved through build_comparison_result."""
        offer = make_offer(
            retailer_name="VariantShop",
            exact_model_match=False,
        )
        offer.model_match_note = "Blue variant listed, Black searched"
        result = build_comparison_result(make_request(), [offer])
        matched = next(o for o in result.offers if o.retailer_name == "VariantShop")
        assert matched.model_match_note == "Blue variant listed, Black searched"

    def test_incompatible_variants_not_ranked_together(self):
        """
        The recommendation rationale must explicitly mention variant-mismatch
        exclusions so the user is never misled.
        """
        mismatch = make_offer(retailer_name="VariantShop", listed_price=60.0,
                              delivery_fee=0.0, exact_model_match=False)
        exact = make_offer(retailer_name="ExactShop", listed_price=80.0,
                           delivery_fee=0.0, exact_model_match=True)
        result = build_comparison_result(make_request(), [mismatch, exact])
        rationale_text = " ".join(result.summary.recommendation_rationale)
        assert "variant" in rationale_text.lower() or "mismatch" in rationale_text.lower(), (
            "Recommendation rationale must mention variant mismatch"
        )


# ---------------------------------------------------------------------------
# 5. Missing reviews
# ---------------------------------------------------------------------------

class TestMissingReviews:
    def test_no_rating_not_invented(self):
        """rating=None must remain None — never replaced with a made-up value."""
        offer = make_offer(rating=None, review_count=None)
        result = build_comparison_result(make_request(), [offer])
        assert result.offers[0].rating is None

    def test_no_review_count_not_invented(self):
        offer = make_offer(rating=None, review_count=None)
        result = build_comparison_result(make_request(), [offer])
        assert result.offers[0].review_count is None

    def test_review_section_none_when_not_provided(self):
        """If no CustomerReviews object is provided, result.reviews must be None."""
        result = build_comparison_result(make_request(), [make_offer()], reviews=None)
        assert result.reviews is None

    def test_reviews_not_invented_for_insufficient_data(self):
        """CustomerReviews with sentiment=INSUFFICIENT_DATA must not be replaced."""
        reviews = CustomerReviews(
            average_rating=None,
            total_review_count=0,
            sentiment=Sentiment.INSUFFICIENT_DATA,
            data_source=DataSource.DEMO,
        )
        result = build_comparison_result(make_request(), [make_offer()], reviews=reviews)
        assert result.reviews is not None
        assert result.reviews.average_rating is None
        assert result.reviews.sentiment == Sentiment.INSUFFICIENT_DATA

    def test_offers_with_no_rating_excluded_from_highest_rated(self):
        """Offers missing ratings must not appear as highest_rated."""
        no_rating = make_offer(retailer_name="NoRatingShop", rating=None)
        with_rating = make_offer(retailer_name="RatedShop", rating=3.5)
        best = find_highest_rated([no_rating, with_rating])
        assert best is not None
        assert best.retailer_name == "RatedShop"


# ---------------------------------------------------------------------------
# 6. Deal Integrity Score
# ---------------------------------------------------------------------------

class TestDealIntegrityScore:
    def test_empty_offers_scores_zero(self):
        score, _ = calculate_deal_integrity_score([])
        assert score == 0

    def test_perfect_offer_scores_100(self):
        """
        A fully verified, exact-match offer with known delivery, no conditional
        discounts, verified warranty/return, and a timestamp should score 100.
        """
        offer = make_offer(
            is_verified=True,
            exact_model_match=True,
            delivery_fee=0.0,
            delivery_fee_unknown=False,
            conditional_discounts=[],
            warranty_value="2-year",
            warranty_verified=True,
            return_value="30-day",
            return_verified=True,
            checked_at=NOW,
        )
        score, explanation = calculate_deal_integrity_score([offer])
        assert score == 100, f"Expected 100, got {score}. Explanation: {explanation}"

    def test_unknown_delivery_reduces_score(self):
        """Unknown delivery fee must reduce the score vs. known delivery."""
        perfect = make_offer(delivery_fee=0.0, delivery_fee_unknown=False)
        unknown = make_offer(delivery_fee=None, delivery_fee_unknown=True)
        score_perfect, _ = calculate_deal_integrity_score([perfect])
        score_unknown, _ = calculate_deal_integrity_score([unknown])
        assert score_unknown < score_perfect

    def test_unverified_listing_reduces_score(self):
        verified = make_offer(is_verified=True)
        unverified = make_offer(is_verified=False)
        score_v, _ = calculate_deal_integrity_score([verified])
        score_uv, _ = calculate_deal_integrity_score([unverified])
        assert score_uv < score_v

    def test_model_mismatch_reduces_score(self):
        exact = make_offer(exact_model_match=True)
        mismatch = make_offer(exact_model_match=False)
        score_e, _ = calculate_deal_integrity_score([exact])
        score_m, _ = calculate_deal_integrity_score([mismatch])
        assert score_m < score_e

    def test_missing_warranty_reduces_score(self):
        with_warranty = make_offer(warranty_value="1-year", warranty_verified=True)
        no_warranty = make_offer(warranty_value=None, warranty_verified=False)
        score_w, _ = calculate_deal_integrity_score([with_warranty])
        score_nw, _ = calculate_deal_integrity_score([no_warranty])
        assert score_nw < score_w

    def test_score_out_of_100(self):
        """Score must always be in [0, 100]."""
        offers = [
            make_offer(is_verified=False, exact_model_match=False,
                       delivery_fee=None, delivery_fee_unknown=True,
                       warranty_value=None, return_value=None,
                       checked_at=None),
        ]
        score, _ = calculate_deal_integrity_score(offers)
        assert 0 <= score <= 100

    def test_score_explains_problems(self):
        """Explanation text must mention the specific issues found."""
        offer = make_offer(
            is_verified=False,
            delivery_fee=None,
            delivery_fee_unknown=True,
            exact_model_match=False,
        )
        _, explanation = calculate_deal_integrity_score([offer])
        # at least one specific problem should be mentioned
        assert any(keyword in explanation.lower() for keyword in
                   ("unverified", "delivery", "variant", "mismatch"))

    def test_score_is_not_product_quality(self):
        """
        The explanation must clarify that the score measures evidence completeness,
        not product quality or retailer reputation.
        """
        _, explanation = calculate_deal_integrity_score([make_offer()])
        assert "evidence" in explanation.lower() or "completeness" in explanation.lower() or \
               "quality" in explanation.lower()

    def test_no_missing_info_gets_full_points(self):
        """A single offer with no gaps should score 100."""
        offer = make_offer()
        score, _ = calculate_deal_integrity_score([offer])
        assert score == 100

    def test_multiple_offers_averaged(self):
        """Score for mixed offers must be between the individual best and worst."""
        perfect = make_offer(retailer_name="Perfect")
        terrible = make_offer(
            retailer_name="Terrible",
            is_verified=False,
            exact_model_match=False,
            delivery_fee=None,
            delivery_fee_unknown=True,
            warranty_value=None,
            return_value=None,
            checked_at=None,
        )
        score_perfect, _ = calculate_deal_integrity_score([perfect])
        score_terrible, _ = calculate_deal_integrity_score([terrible])
        score_mixed, _ = calculate_deal_integrity_score([perfect, terrible])
        assert score_terrible <= score_mixed <= score_perfect


# ---------------------------------------------------------------------------
# 7. Retailer ranking
# ---------------------------------------------------------------------------

class TestRetailerRanking:
    def test_cheapest_confirmed_comparable_offer(self):
        """
        Cheapest confirmed comparable offer = lowest comparable_total
        (listed_price + confirmed delivery_fee).
        """
        a = make_offer(retailer_name="A", listed_price=100.0, delivery_fee=0.0)
        b = make_offer(retailer_name="B", listed_price=90.0, delivery_fee=10.0)
        c = make_offer(retailer_name="C", listed_price=80.0, delivery_fee=25.0)
        # totals: A=100, B=100, C=105
        best = find_best_verified_deal([a, b, c])
        assert best is not None
        # A and B are tied at 100; either is acceptable
        assert best.retailer_name in ("A", "B")

    def test_offers_with_unknown_total_ranked_last(self):
        """rank_offers must place offers with known totals before unknown ones."""
        known = make_offer(retailer_name="Known", listed_price=80.0, delivery_fee=5.0)
        unknown = make_offer(retailer_name="Unknown", listed_price=70.0,
                             delivery_fee=None, delivery_fee_unknown=True)
        # verify make_offer set comparable_total correctly
        assert known.comparable_total == 85.0
        assert unknown.comparable_total is None
        ranked = rank_offers([unknown, known])
        assert ranked[0].retailer_name == "Known"
        assert ranked[1].retailer_name == "Unknown"

    def test_no_cheapest_claim_when_total_unknown(self):
        """
        When all offers have unknown delivery fees, best_verified_deal must be None.
        The engine must not claim any offer is cheapest.
        """
        a = make_offer(retailer_name="A", listed_price=70.0,
                       delivery_fee=None, delivery_fee_unknown=True)
        b = make_offer(retailer_name="B", listed_price=80.0,
                       delivery_fee=None, delivery_fee_unknown=True)
        result = build_comparison_result(make_request(), [a, b])
        assert result.summary.best_verified_deal is None, (
            "Must not claim an offer is cheapest when delivery fee is unknown"
        )

    def test_highest_rated_is_highest_rating(self):
        low = make_offer(retailer_name="Low", rating=3.0)
        high = make_offer(retailer_name="High", rating=4.8)
        mid = make_offer(retailer_name="Mid", rating=4.2)
        best = find_highest_rated([low, high, mid])
        assert best is not None
        assert best.retailer_name == "High"

    def test_recommendation_explains_reasoning(self):
        """Recommendation prose must be non-empty and the rationale list populated."""
        offers = [
            make_offer(retailer_name="A", listed_price=89.0, delivery_fee=0.0),
            make_offer(retailer_name="B", listed_price=79.0,
                       delivery_fee=None, delivery_fee_unknown=True),
        ]
        result = build_comparison_result(make_request(), offers)
        assert result.summary.recommendation  # non-empty
        assert result.summary.recommendation_rationale  # at least one bullet

    def test_is_demo_flag_preserved(self):
        """is_demo=True must be visible in the result."""
        result = build_comparison_result(make_request(), [make_offer()], is_demo=True)
        assert result.is_demo is True

    def test_result_generated_at_is_set(self):
        result = build_comparison_result(make_request(), [make_offer()])
        assert result.generated_at is not None


# ---------------------------------------------------------------------------
# 8. Initial Indian retailer configuration & investigation
# ---------------------------------------------------------------------------

class TestIndianRetailerConfiguration:
    def test_all_four_indian_retailers_configured(self):
        """
        All four required retailers must be present in the initial India market:
        1. Amazon India (amazon.in)
        2. Flipkart (flipkart.com)
        3. Croma (croma.com)
        4. Reliance Digital (reliancedigital.in)
        """
        indian_retailers = get_market_retailers("IN")
        retailer_map = {r.domain.lower(): r.name for r in indian_retailers}

        assert "amazon.in" in retailer_map, "Amazon India must be in Indian retailer config"
        assert "flipkart.com" in retailer_map, "Flipkart must be in Indian retailer config"
        assert "croma.com" in retailer_map, "Croma must be in Indian retailer config"
        assert "reliancedigital.in" in retailer_map, "Reliance Digital must be in Indian retailer config"

        # Verify correct human-readable names
        assert retailer_map["amazon.in"] == "Amazon India"
        assert retailer_map["flipkart.com"] == "Flipkart"
        assert retailer_map["croma.com"] == "Croma"
        assert retailer_map["reliancedigital.in"] == "Reliance Digital"

    def test_investigate_all_four_retailers_same_product(self):
        """
        The research engine must attempt to investigate all four retailers
        for the same exact product model.
        """
        query = "Sony WH-CH720N"
        investigated = reconcile_market_investigation(query=query, country_code="IN")
        domains = [r.retailer_url for r in investigated]

        assert len(investigated) == 4, f"Expected 4 retailers investigated, got {len(investigated)}"
        retailer_names = {r.retailer_name for r in investigated}
        expected = {"Amazon India", "Flipkart", "Croma", "Reliance Digital"}
        assert retailer_names == expected, f"Missing retailers in investigation: {expected - retailer_names}"

    def test_missing_listing_marked_unavailable_without_fabrication(self):
        """
        If a retailer has no matching listing, it must be marked as unavailable
        and its listed_price must be None (never fabricated).
        """
        query = "Rare Obsolete Model XYZ"
        investigated = reconcile_market_investigation(query=query, country_code="IN")

        for offer in investigated:
            assert offer.availability == OfferAvailability.UNAVAILABLE
            assert offer.listed_price is None, "Price must NEVER be fabricated for missing listing"
            assert offer.comparable_total is None
            assert offer.is_verified is False
            assert "No matching listing" in (offer.availability_note or "")

    def test_partial_listings_preserves_verified_and_marks_missing(self):
        """
        When some retailers have listings and others do not, verified listings
        are retained while missing retailers are marked unavailable truthfully.
        """
        amazon_offer = make_offer(
            retailer_name="Amazon India",
            listed_price=7990.0,
            delivery_fee=0.0,
        )
        amazon_offer.retailer_url = "https://www.amazon.in"

        croma_offer = make_offer(
            retailer_name="Croma",
            listed_price=8490.0,
            delivery_fee=0.0,
        )
        croma_offer.retailer_url = "https://www.croma.com"

        investigated = reconcile_market_investigation(
            query="Sony WH-CH720N",
            country_code="IN",
            discovered_offers=[amazon_offer, croma_offer],
        )

        assert len(investigated) == 4
        by_name = {o.retailer_name: o for o in investigated}

        # Discovered ones remain available
        assert by_name["Amazon India"].availability == OfferAvailability.AVAILABLE
        assert by_name["Amazon India"].listed_price == 7990.0
        assert by_name["Croma"].availability == OfferAvailability.AVAILABLE
        assert by_name["Croma"].listed_price == 8490.0

        # Undiscovered ones are marked unavailable without price fabrication
        assert by_name["Flipkart"].availability == OfferAvailability.UNAVAILABLE
        assert by_name["Flipkart"].listed_price is None
        assert by_name["Reliance Digital"].availability == OfferAvailability.UNAVAILABLE
        assert by_name["Reliance Digital"].listed_price is None

    def test_inaccessible_retailer_marked_truthfully(self):
        """Inaccessible retailer can be marked with custom status and note."""
        rel_conf = next(r for r in INDIAN_RETAILERS if r.id == "reliance_digital")
        offer = build_unavailable_offer(
            retailer=rel_conf,
            query="Sony WH-CH720N",
            status=OfferAvailability.UNAVAILABLE,
            reason="Retailer endpoint timed out / inaccessible during research",
        )
        assert offer.availability == OfferAvailability.UNAVAILABLE
        assert "timed out" in (offer.availability_note or "")
        assert offer.listed_price is None

    def test_modular_retailer_addition(self):
        """
        Verify that new retailers can be added modularly to a market
        without changing the core engine code.
        """
        new_retailer = RetailerConfig(
            id="vijay_sales",
            name="Vijay Sales",
            domain="vijaysales.com",
            country="IN",
            currency="INR",
            retailer_url="https://www.vijaysales.com",
        )
        register_retailer(new_retailer)

        indian_retailers = get_market_retailers("IN")
        names = [r.name for r in indian_retailers]
        assert "Vijay Sales" in names

    def test_modular_country_addition(self):
        """
        Verify that an entirely new country/market can be added modularly.
        """
        germany_retailer = RetailerConfig(
            id="mediamarkt_de",
            name="MediaMarkt Germany",
            domain="mediamarkt.de",
            country="DE",
            currency="EUR",
            retailer_url="https://www.mediamarkt.de",
        )
        register_retailer(germany_retailer)

        de_retailers = get_market_retailers("DE")
        assert len(de_retailers) == 1
        assert de_retailers[0].name == "MediaMarkt Germany"
        assert de_retailers[0].currency == "EUR"

    def test_unavailable_retailer_ranked_last(self):
        """Unavailable retailers must be ranked after available offers."""
        available = make_offer(retailer_name="Amazon India", listed_price=7990.0, delivery_fee=0.0)
        unavailable = build_unavailable_offer(
            retailer=INDIAN_RETAILERS[3],  # Reliance Digital
            query="Sony WH-CH720N",
            status=OfferAvailability.UNAVAILABLE,
        )
        ranked = rank_offers([unavailable, available])
        assert ranked[0].retailer_name == "Amazon India"
        assert ranked[1].retailer_name == "Reliance Digital"

    def test_unavailable_retailer_penalised_in_integrity_score(self):
        """
        Missing listing information must not receive full points in Deal Integrity Score.
        """
        available = make_offer(retailer_name="Amazon India", is_verified=True, exact_model_match=True)
        unavailable = build_unavailable_offer(
            retailer=INDIAN_RETAILERS[3],
            query="Sony WH-CH720N",
        )
        score_both, explanation = calculate_deal_integrity_score([available, unavailable])
        score_only_available, _ = calculate_deal_integrity_score([available])

        assert score_both < score_only_available, "Missing retailer listings must reduce integrity score"
        assert "no verified" in explanation.lower() or "unverified" in explanation.lower()
