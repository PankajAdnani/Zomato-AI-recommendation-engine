export interface RestaurantItem {
  restaurant_id: string;
  name: string;
  location: string;
  cuisines: string;
  rating: number;
  votes_count: number;
  cost_for_two: number | null;
  dish_liked: string | null;
  url: string;
  image_url: string;
}

export interface RecommendationCard {
  restaurant_id: string;
  name: string;
  cuisines: string;
  location: string;
  rating: number;
  cost_for_two: number | null;
  why_recommended: string;
  highlights: string[];
  must_try_dishes: string[];
  url: string;
  image_url: string;
}

export interface Metrics {
  candidate_count: number;
  filter_ms: number;
  llm_ms: number;
  total_ms: number;
}
