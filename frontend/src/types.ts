// Vrisko — shared TypeScript types (mirrors backend Pydantic models)

export type ProductCondition = 'new' | 'refurbished' | 'used' | 'open_box' | 'unknown';
export type Sentiment = 'positive' | 'mixed' | 'negative' | 'insufficient_data';
export type DataSource = 'live_research' | 'demo' | 'manual';
export type OfferAvailability = 'available' | 'unavailable' | 'unknown';

export interface ConditionalDiscount {
  label: string;
  amount: number | null;
  percentage: number | null;
  condition_description: string;
  is_verified: boolean;
}

export interface VerifiedField {
  value: string | null;
  is_verified: boolean;
  note: string | null;
}

export interface RetailerOffer {
  retailer_name: string;
  retailer_url: string | null;
  product_url: string | null;
  listed_price: number | null;
  currency: string;
  delivery_fee: number | null;
  delivery_fee_unknown: boolean;
  comparable_total: number | null;
  headline_discount_pct: number | null;
  original_price: number | null;
  conditional_discounts: ConditionalDiscount[];
  condition: ProductCondition;
  exact_model_match: boolean;
  model_match_note: string | null;
  warranty: VerifiedField;
  return_policy: VerifiedField;
  is_verified: boolean;
  rating: number | null;
  review_count: number | null;
  availability?: OfferAvailability;
  availability_note?: string | null;
  data_source: DataSource;
  checked_at: string | null;
}

export interface CustomerReviews {
  average_rating: number | null;
  total_review_count: number;
  positive_feedback: string | null;
  negative_feedback: string | null;
  sentiment: Sentiment;
  sentiment_confidence: number | null;
  data_source: DataSource;
}

export interface EvidenceItem {
  category: 'verified' | 'conditional' | 'unknown' | 'source';
  label: string;
  detail: string | null;
  source_url: string | null;
}

export interface ComparisonSummary {
  cheapest_listed_price: RetailerOffer | null;
  best_verified_deal: RetailerOffer | null;
  /** Lowest potential total when a conditional discount with a known amount applies.
   *  NEVER a confirmed price — always labelled as conditional. */
  best_conditional_offer: RetailerOffer | null;
  highest_rated: RetailerOffer | null;
  recommendation: string;
  recommendation_rationale: string[];
}

export interface Product {
  query: string;
  normalised_model: string | null;
  brand: string | null;
  category: string | null;
}

export interface ComparisonResult {
  product: Product;
  offers: RetailerOffer[];
  reviews: CustomerReviews | null;
  summary: ComparisonSummary;
  deal_integrity_score: number | null;
  deal_integrity_explanation: string | null;
  evidence: EvidenceItem[];
  is_demo: boolean;
  data_source: DataSource;
  generated_at: string;
  error: string | null;
}
