
import json
import os
from typing import Any
from urllib.parse import quote_plus

import httpx


def get_tinyfish_config():
    """Load TinyFish configuration without exposing the API key."""
    api_key = os.getenv("TINYFISH_API_KEY")
    base_url = os.getenv(
        "TINYFISH_BASE_URL",
        "https://agent.tinyfish.ai"
    ).rstrip("/")

    if not api_key:
        raise RuntimeError("TINYFISH_API_KEY is not configured")

    return api_key, base_url


async def research_retailer(
    retailer,
    product_query: str
) -> dict[str, Any]:
    """
    Run one TinyFish investigation for one retailer.
    Returns the final COMPLETE event.
    """

    api_key, base_url = get_tinyfish_config()

    search_url = retailer.search_url_template.format(
        query=quote_plus(product_query)
    )

    
    goal = f"""
Investigate this exact product: {product_query}

Website: {retailer.domain}

MANDATORY RESEARCH PROCESS:

1. Open the retailer search page.
2. Examine the search results.
3. Identify the exact requested product and variant.
4. Do not select similar products or different storage capacities.
5. Click the matching product result.
6. Wait for the product detail page to load.
7. Extract information from the actual product detail page.

PRICE VERIFICATION:
- Extract the current selling price displayed on the product detail page.
- Do not use search-result snippets or advertisements.
- Do not use old, cached or unrelated prices.
- Do not calculate prices from discount percentages.
- Return null if the actual selling price cannot be verified.
- Record the original price separately.

PRODUCT URL:

- Return the actual product detail page URL.
- Never return the homepage or search results URL.
- Never invent or construct a product URL.
- The URL must belong to {retailer.domain}.


EXACT VARIANT:
- Verify product name, model number and variant.
- Reject different storage capacities and configurations.
- Reject refurbished, used and open-box products.
- If the exact variant cannot be confirmed, return null for its price.

OTHER INFORMATION:
- Delivery fee and stock status.
- Warranty and return policy.
- Customer rating and review count.
- Conditional bank offers, coupons and EMI discounts separately.

TRUTHFULNESS:
- Only report information visible on the retailer website.
- Never invent or estimate missing information.
- Return null for fields that cannot be verified.
- Distinguish inaccessible pages from confirmed unavailable listings.

Return structured information matching the requested schema.
"""


    output_schema = {
        "type": "object",
        "properties": {
            "product_name": {"type": "string", "nullable": True},
            "model_number": {"type": "string", "nullable": True},
            "product_url": {"type": "string", "nullable": True},
            "listed_price": {"type": "number", "nullable": True},
            "original_price": {"type": "number", "nullable": True},
            "delivery_fee": {"type": "number", "nullable": True},
            "availability": {
                "type": "string",
                "enum": ["AVAILABLE", "UNAVAILABLE", "UNKNOWN"]
            },
            "rating": {"type": "number", "nullable": True},
            "review_count": {"type": "integer", "nullable": True},
            "warranty": {"type": "string", "nullable": True},
            "return_policy": {"type": "string", "nullable": True},
            "discount_details": {
                "type": "array",
                "items": {"type": "string"}
            },
            "source_url": {"type": "string", "nullable": True}
        },
        "required": [
            "product_name",
            "model_number",
            "product_url",
            "listed_price",
            "original_price",
            "delivery_fee",
            "availability",
            "rating",
            "review_count",
            "warranty",
            "return_policy",
            "discount_details",
            "source_url"
        ]
    }

    payload = {
        "url": search_url,
        "goal": goal,
        "output_schema": output_schema,
        "browser_profile": "lite",
        "proxy_config": {
            "enabled": True,
            "type": "tinyfish",
            "country_code": "IN"
        },
        "agent_config": {
            "max_duration_seconds": 120
        }
    }

    headers = {
        "X-API-Key": api_key,
        "Content-Type": "application/json",
        "Accept": "text/event-stream"
    }

    endpoint = f"{base_url}/v1/automation/run-sse"

    final_event = None

    timeout = httpx.Timeout(
        connect=20,
        read=150,
        write=30,
        pool=20
    )

    async with httpx.AsyncClient(timeout=timeout) as client:
        async with client.stream(
            "POST",
            endpoint,
            headers=headers,
            json=payload
        ) as response:

            response.raise_for_status()

            async for line in response.aiter_lines():
                if not line.startswith("data:"):
                    continue

                raw_data = line[5:].strip()

                if not raw_data:
                    continue

                try:
                    event = json.loads(raw_data)
                except json.JSONDecodeError:
                    continue

                event_type = event.get("type")

                if event_type == "COMPLETE":
                    final_event = event
                    break

    if final_event is None:
        raise RuntimeError(
            f"TinyFish did not return a COMPLETE event for {retailer.name}"
        )

    if final_event.get("status") != "COMPLETED":
        raise RuntimeError(
            f"TinyFish investigation failed for {retailer.name}"
        )
    print("\n========== TINYFISH RAW RESULT ==========")
    print(json.dumps(final_event, indent=2)[:10000])
    print("=========================================\n")
     
    return final_event
