"use client";

import React, { useState, useEffect, useMemo } from "react";
import Image from "next/image";
import {
  DEFAULT_LOCATIONS,
  DEFAULT_CUISINES,
  DEFAULT_TRENDING,
} from "@/constants/initialData";
import type { RestaurantItem, RecommendationCard, Metrics } from "@/types";

const INSPIRATION_DISHES = [
  { name: "Biryani", image: "https://images.unsplash.com/photo-1563379091339-03b21ab4a4f8?w=300&auto=format&fit=crop&q=80" },
  { name: "Pizza", image: "https://images.unsplash.com/photo-1513104890138-7c749659a591?w=300&auto=format&fit=crop&q=80" },
  { name: "North Indian", image: "https://images.unsplash.com/photo-1585937421612-70a008356fbe?w=300&auto=format&fit=crop&q=80" },
  { name: "Burger", image: "https://images.unsplash.com/photo-1568901346375-23c9450c58cd?w=300&auto=format&fit=crop&q=80" },
  { name: "South Indian", image: "https://images.unsplash.com/photo-1610057099443-fde8c4d50f91?w=300&auto=format&fit=crop&q=80" },
  { name: "Chinese", image: "https://images.unsplash.com/photo-1569718212165-3a8278d5f624?w=300&auto=format&fit=crop&q=80" },
  { name: "Rolls", image: "https://images.unsplash.com/photo-1626777552726-4a6b54c97e46?w=300&auto=format&fit=crop&q=80" },
  { name: "Cafe", image: "https://images.unsplash.com/photo-1554118811-1e0d58224f24?w=300&auto=format&fit=crop&q=80" },
  { name: "Desserts", image: "https://images.unsplash.com/photo-1551024709-8f23befc6f87?w=300&auto=format&fit=crop&q=80" },
];

const TOP_BRANDS = [
  { name: "Empire Restaurant", time: "30–35 min", icon: "🍗", color: "bg-red-50 text-red-600" },
  { name: "Nandhana Palace", time: "40–45 min", icon: "🌶️", color: "bg-orange-50 text-orange-600" },
  { name: "Meghana Foods", time: "35–40 min", icon: "🥘", color: "bg-amber-50 text-amber-600" },
  { name: "Beijing Bites", time: "30–35 min", icon: "🥢", color: "bg-rose-50 text-rose-600" },
  { name: "McDonald's", time: "40–45 min", icon: "🍔", color: "bg-yellow-50 text-yellow-600" },
];

const FEATURE_CARDS = [
  { title: "Healthy", icon: "🥗" },
  { title: "Veg Mode", icon: "🥦" },
  { title: "Gourmet", icon: "🍝" },
  { title: "Offers", icon: "🏷️" },
  { title: "Gift Cards", icon: "🎁" },
  { title: "Collections", icon: "🔖" },
];

export default function HomePage() {
  // Metadata state with instant fallbacks so dropdowns are never blank
  const [locations, setLocations] = useState<string[]>(DEFAULT_LOCATIONS);
  const [cuisines, setCuisines] = useState<string[]>(DEFAULT_CUISINES);
  const [totalRestaurants, setTotalRestaurants] = useState<number>(9249);
  const [totalLocalities, setTotalLocalities] = useState<number>(92);

  // Search state
  const [searchQuery, setSearchQuery] = useState<string>("");
  const [searchResults, setSearchResults] = useState<RestaurantItem[]>([]);
  const [totalFound, setTotalFound] = useState<number>(0);
  const [isSearching, setIsSearching] = useState<boolean>(false);

  // Trending state with verified top restaurants so the section is never blank
  const [trending, setTrending] = useState<RestaurantItem[]>(DEFAULT_TRENDING);

  // Form input state
  const [selectedLocation, setSelectedLocation] = useState<string>("Koramangala 5th Block");
  const [budgetBand, setBudgetBand] = useState<string>("medium");
  const [selectedCuisine, setSelectedCuisine] = useState<string>("North Indian");
  const [minRating, setMinRating] = useState<number>(3.8);
  const [specialPreferences, setSpecialPreferences] = useState<string>("");
  const [topN, setTopN] = useState<number>(4);

  // Recommendation execution state
  const [isLoadingRecs, setIsLoadingRecs] = useState<boolean>(false);
  const [recommendations, setRecommendations] = useState<RecommendationCard[]>([]);
  const [metrics, setMetrics] = useState<Metrics | null>(null);
  const [submitted, setSubmitted] = useState<boolean>(false);
  const [recError, setRecError] = useState<string | null>(null);

  // Active Category tab
  const [activeTab, setActiveTab] = useState<string>("dining");

  // Fetch live metadata & trending restaurants from backend with automatic retry
  useEffect(() => {
    let isMounted = true;

    async function loadInitialData(retryCount = 0) {
      try {
        const metaRes = await fetch("/api/metadata");
        if (metaRes.ok) {
          const metaData = await metaRes.json();
          if (isMounted) {
            if (metaData.locations?.length) setLocations(metaData.locations);
            if (metaData.cuisines?.length) setCuisines(metaData.cuisines);
            if (metaData.total_restaurants) setTotalRestaurants(metaData.total_restaurants);
            if (metaData.total_localities) setTotalLocalities(metaData.total_localities);
          }
        }

        const trendRes = await fetch("/api/trending");
        if (trendRes.ok) {
          const trendData = await trendRes.json();
          if (isMounted && trendData.trending?.length) {
            setTrending(trendData.trending);
          }
        }
      } catch (err) {
        console.warn("Initial data load attempt failed (backend may be spinning up):", err);
        // Retry once after 3.5s in case Render backend was waking up from sleep
        if (retryCount < 2 && isMounted) {
          setTimeout(() => loadInitialData(retryCount + 1), 3500);
        }
      }
    }

    loadInitialData();
    return () => {
      isMounted = false;
    };
  }, []);

  // Handle Search Input with debounce
  useEffect(() => {
    const q = searchQuery.trim();
    if (!q) {
      setSearchResults([]);
      setTotalFound(0);
      setIsSearching(false);
      return;
    }

    setIsSearching(true);
    const timer = setTimeout(async () => {
      try {
        const res = await fetch(`/api/search?q=${encodeURIComponent(q)}&limit=15`);
        if (res.ok) {
          const data = await res.json();
          setSearchResults(data.results || []);
          setTotalFound(data.total_found || 0);
        }
      } catch (err) {
        console.error("Search failed:", err);
      } finally {
        setIsSearching(false);
      }
    }, 250);

    return () => clearTimeout(timer);
  }, [searchQuery]);

  // Handle Recommendation Form Submission
  async function handleDiscoverRecommendations(e: React.FormEvent) {
    e.preventDefault();
    setIsLoadingRecs(true);
    setRecError(null);
    setSearchQuery(""); // Clear search when user explicitly submits recommendation form

    try {
      const res = await fetch("/api/recommend", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          location: selectedLocation,
          budget: budgetBand,
          cuisine: selectedCuisine,
          min_rating: minRating,
          additional: specialPreferences.trim() || null,
          top_n: topN,
        }),
      });

      if (!res.ok) {
        const errData = await res.json();
        throw new Error(errData.detail || "Failed to generate recommendations");
      }

      const data = await res.json();
      setRecommendations(data.recommendations || []);
      setMetrics(data.metrics || null);
      setSubmitted(true);
    } catch (err: any) {
      setRecError(err.message || "An unexpected error occurred.");
    } finally {
      setIsLoadingRecs(false);
    }
  }

  function handleResetView() {
    setSubmitted(false);
    setRecommendations([]);
    setMetrics(null);
    setSearchQuery("");
  }

  return (
    <div className="min-h-screen bg-[#FDFDFD] text-[#1C1C1C]">
      {/* Top Navbar */}
      <header className="sticky top-0 z-50 bg-white/95 backdrop-blur-md border-b border-[#ECECEC] shadow-[0_2px_12px_rgba(0,0,0,0.03)] px-4 sm:px-8 py-3">
        <div className="max-w-[1400px] mx-auto flex items-center justify-between gap-6">
          {/* Left: Brand Logo & Badge */}
          <div className="flex items-center gap-2.5 shrink-0">
            <span className="text-[2.2rem] font-[900] italic text-[#E23744] tracking-[-1.5px] leading-none select-none">
              zomato
            </span>
            <span className="bg-[#FFF0F1] text-[#E23744] text-[0.68rem] font-[700] px-2 py-0.5 rounded-md border border-[rgba(226,55,68,0.2)] tracking-[0.5px] uppercase">
              AI GUIDE
            </span>
          </div>

          {/* Center: Active Search Bar with 35px+ clearance */}
          <div className="flex-1 max-w-[620px] mx-4 relative">
            <div className="flex items-center bg-white border border-[#E2E2E2] focus-within:border-[#E23744] focus-within:shadow-[0_3px_12px_rgba(226,55,68,0.16)] rounded-full px-4 py-2 transition-all shadow-[0_2px_8px_rgba(0,0,0,0.04)] h-[44px]">
              <span className="text-gray-400 text-sm shrink-0 mr-2.5">
                📍 Bengaluru <span className="text-[0.65rem] text-gray-400 ml-0.5">▼</span>
              </span>
              <span className="w-[1px] h-4 bg-gray-200 shrink-0 mr-2.5" />
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Search for restaurant, cuisine or dish across 9,249+ spots..."
                className="w-full bg-transparent text-[0.92rem] text-[#1C1C1C] placeholder:text-gray-400 focus:outline-none"
              />
              {searchQuery && (
                <button
                  type="button"
                  onClick={() => setSearchQuery("")}
                  className="text-gray-400 hover:text-gray-600 text-sm px-1.5 shrink-0"
                >
                  ✕
                </button>
              )}
            </div>
          </div>

          {/* Right: Actions */}
          <div className="flex items-center gap-6 shrink-0 text-[0.92rem] font-[500] text-[#363636]">
            <button
              onClick={() => setActiveTab("dining")}
              className={`hover:text-[#E23744] transition-colors ${activeTab === "dining" ? "text-[#E23744] font-[600]" : ""}`}
            >
              Dining Out
            </button>
            <button
              onClick={() => setActiveTab("delivery")}
              className={`hover:text-[#E23744] transition-colors ${activeTab === "delivery" ? "text-[#E23744] font-[600]" : ""}`}
            >
              Delivery
            </button>
            <span className="text-[#E23744] font-[700] flex items-center gap-1">
              ✨ Gemini AI
            </span>
          </div>
        </div>
      </header>

      {/* Main Container */}
      <main className="max-w-[1400px] mx-auto px-4 sm:px-8 py-6">
        {/* Category Switcher Tabs */}
        <div className="flex items-center gap-8 border-b border-[#E8E8E8] pb-3 mb-6">
          <button
            onClick={() => setActiveTab("dining")}
            className={`flex items-center gap-2.5 text-[1.1rem] pb-2 font-[500] transition-all relative ${
              activeTab === "dining"
                ? "text-[#E23744] font-[600] after:absolute after:bottom-[-13px] after:left-0 after:right-0 after:h-[2.5px] after:bg-[#E23744]"
                : "text-gray-500 hover:text-gray-800"
            }`}
          >
            <span className="text-xl">🍽️</span>
            <span>Dining Out</span>
          </button>
          <button
            onClick={() => setActiveTab("delivery")}
            className={`flex items-center gap-2.5 text-[1.1rem] pb-2 font-[500] transition-all relative ${
              activeTab === "delivery"
                ? "text-[#E23744] font-[600] after:absolute after:bottom-[-13px] after:left-0 after:right-0 after:h-[2.5px] after:bg-[#E23744]"
                : "text-gray-500 hover:text-gray-800"
            }`}
          >
            <span className="text-xl">🛵</span>
            <span>Delivery</span>
          </button>
          <button
            onClick={() => setActiveTab("nightlife")}
            className={`flex items-center gap-2.5 text-[1.1rem] pb-2 font-[500] transition-all relative ${
              activeTab === "nightlife"
                ? "text-[#E23744] font-[600] after:absolute after:bottom-[-13px] after:left-0 after:right-0 after:h-[2.5px] after:bg-[#E23744]"
                : "text-gray-500 hover:text-gray-800"
            }`}
          >
            <span className="text-xl">🍸</span>
            <span>Nightlife</span>
          </button>
        </div>

        {/* 2-Column Responsive Grid Layout (Form on Left ~42%, Content on Right ~58%) */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
          {/* Left Column: Recommendation Engine Form (lg:col-span-5) */}
          <div className="lg:col-span-5 space-y-4">
            {/* Header Card */}
            <div className="bg-white border border-[#EAEAEA] rounded-[18px] p-6 shadow-[0_4px_18px_rgba(0,0,0,0.04)]">
              <h2 className="text-[1.35rem] font-[800] text-[#1C1C1C] leading-snug mb-1.5 flex items-center gap-2">
                🎯 Find Your Perfect Spot
              </h2>
              <p className="text-[0.92rem] text-[#696969] leading-relaxed">
                Select your location, budget, and cuisine preferences and let Gemini AI curate the best restaurants for you.
              </p>
            </div>

            {/* Main Preferences Form */}
            <form
              onSubmit={handleDiscoverRecommendations}
              className="bg-white border border-[#EAEAEA] rounded-[18px] p-6 shadow-[0_4px_18px_rgba(0,0,0,0.04)] space-y-5"
            >
              {/* Select Location / Locality */}
              <div>
                <label className="block text-[0.95rem] font-[600] text-[#1C1C1C] mb-1.5">
                  📍 Select Location / Locality
                </label>
                <select
                  value={selectedLocation}
                  onChange={(e) => setSelectedLocation(e.target.value)}
                  className="w-full h-[48px] px-3.5 bg-white border border-[#D1D5DB] rounded-xl text-[0.94rem] font-[500] text-[#1C1C1C] focus:border-[#E23744] focus:ring-1 focus:ring-[#E23744] outline-none transition-all shadow-sm"
                >
                  {locations.map((loc) => (
                    <option key={loc} value={loc}>
                      {loc}
                    </option>
                  ))}
                </select>
              </div>

              {/* Budget Band */}
              <div>
                <label className="block text-[0.95rem] font-[600] text-[#1C1C1C] mb-1.5">
                  💰 Budget Band
                </label>
                <select
                  value={budgetBand}
                  onChange={(e) => setBudgetBand(e.target.value)}
                  className="w-full h-[48px] px-3.5 bg-white border border-[#D1D5DB] rounded-xl text-[0.94rem] font-[500] text-[#1C1C1C] focus:border-[#E23744] focus:ring-1 focus:ring-[#E23744] outline-none transition-all shadow-sm"
                >
                  <option value="low">Low (&lt; ₹500 for two)</option>
                  <option value="medium">Medium (₹500–1500 for two)</option>
                  <option value="high">High (&gt; ₹1500 for two)</option>
                </select>
              </div>

              {/* Preferred Cuisine */}
              <div>
                <label className="block text-[0.95rem] font-[600] text-[#1C1C1C] mb-1.5">
                  🍕 Preferred Cuisine
                </label>
                <select
                  value={selectedCuisine}
                  onChange={(e) => setSelectedCuisine(e.target.value)}
                  className="w-full h-[48px] px-3.5 bg-white border border-[#D1D5DB] rounded-xl text-[0.94rem] font-[500] text-[#1C1C1C] focus:border-[#E23744] focus:ring-1 focus:ring-[#E23744] outline-none transition-all shadow-sm"
                >
                  {cuisines.map((c) => (
                    <option key={c} value={c}>
                      {c}
                    </option>
                  ))}
                </select>
              </div>

              {/* Minimum Rating Threshold */}
              <div>
                <div className="flex justify-between items-center mb-1.5">
                  <label className="text-[0.95rem] font-[600] text-[#1C1C1C]">
                    ⭐ Minimum Rating Threshold
                  </label>
                  <span className="text-[0.88rem] font-[700] text-[#E23744] bg-[#FFF0F1] px-2.5 py-0.5 rounded-md border border-[rgba(226,55,68,0.2)]">
                    ★ {minRating.toFixed(1)}
                  </span>
                </div>
                <input
                  type="range"
                  min="0"
                  max="5"
                  step="0.1"
                  value={minRating}
                  onChange={(e) => setMinRating(parseFloat(e.target.value))}
                  className="w-full accent-[#E23744] cursor-pointer"
                />
                <div className="flex justify-between text-[0.75rem] text-gray-400 mt-1">
                  <span>0.0</span>
                  <span>2.5</span>
                  <span>5.0</span>
                </div>
              </div>

              {/* Special Preferences / Mood (Optional) */}
              <div>
                <label className="block text-[0.95rem] font-[600] text-[#1C1C1C] mb-1.5">
                  📝 Special Preferences / Mood (Optional)
                </label>
                <textarea
                  value={specialPreferences}
                  onChange={(e) => setSpecialPreferences(e.target.value)}
                  placeholder="e.g. romantic candle light dinner, rooftop view, family-friendly with kids"
                  rows={4}
                  maxLength={500}
                  className="w-full px-3.5 py-3 bg-white border border-[#D1D5DB] rounded-xl text-[0.94rem] text-[#1C1C1C] placeholder:text-gray-400 focus:border-[#E23744] focus:ring-1 focus:ring-[#E23744] outline-none transition-all shadow-sm resize-none"
                />
              </div>

              {/* Number of Recommendations */}
              <div>
                <div className="flex justify-between items-center mb-1.5">
                  <label className="text-[0.95rem] font-[600] text-[#1C1C1C]">
                    🔢 Number of Recommendations
                  </label>
                  <span className="text-[0.88rem] font-[700] text-[#363636]">
                    {topN} spots
                  </span>
                </div>
                <input
                  type="range"
                  min="1"
                  max="10"
                  step="1"
                  value={topN}
                  onChange={(e) => setTopN(parseInt(e.target.value))}
                  className="w-full accent-[#E23744] cursor-pointer"
                />
              </div>

              {/* Error Message */}
              {recError && (
                <div className="bg-red-50 border border-red-200 text-red-600 text-sm p-3 rounded-xl">
                  {recError}
                </div>
              )}

              {/* Discover Recommendations Button: Strictly single-line! */}
              <button
                type="submit"
                disabled={isLoadingRecs}
                className="w-full h-[48px] bg-gradient-to-r from-[#EF4F5F] to-[#E23744] hover:from-[#E23744] hover:to-[#C92A36] text-white font-[700] text-[0.98rem] rounded-xl shadow-[0_4px_14px_rgba(226,55,68,0.35)] transition-all flex items-center justify-center whitespace-nowrap overflow-visible active:scale-[0.98] disabled:opacity-70 disabled:cursor-not-allowed"
              >
                {isLoadingRecs ? (
                  <span className="flex items-center gap-2">
                    <svg className="animate-spin h-5 w-5 text-white" viewBox="0 0 24 24" fill="none">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z" />
                    </svg>
                    Curating with Gemini AI...
                  </span>
                ) : (
                  <span>✨ Discover Recommendations</span>
                )}
              </button>
            </form>

            {/* Dataset Info Box */}
            <div className="bg-white border border-[#EAEAEA] rounded-[18px] p-5 shadow-[0_2px_10px_rgba(0,0,0,0.03)] text-sm space-y-1.5">
              <div className="font-[700] text-[1.02rem] text-[#1C1C1C] mb-2 flex items-center gap-2">
                📊 Zomato Dataset & Engine
              </div>
              <div className="text-gray-600 flex justify-between">
                <span>Verified Restaurants:</span>
                <b className="text-gray-900">{totalRestaurants.toLocaleString()}+</b>
              </div>
              <div className="text-gray-600 flex justify-between">
                <span>Bengaluru Localities:</span>
                <b className="text-gray-900">{totalLocalities}+</b>
              </div>
              <div className="text-gray-600 flex justify-between">
                <span>AI Recommendation Model:</span>
                <b className="text-[#E23744]">gemini-3.5-flash-lite</b>
              </div>
            </div>
          </div>

          {/* Right Column: Dynamic Content Area (lg:col-span-7) */}
          <div className="lg:col-span-7 space-y-6">
            {/* View 1: Active Search Mode */}
            {searchQuery.trim() ? (
              <div className="space-y-4">
                <div className="flex items-center justify-between pb-3 border-b border-[#ECECEC]">
                  <div>
                    <h2 className="text-[1.35rem] font-[700] text-[#1C1C1C]">
                      🔍 Search Results for &ldquo;<span className="text-[#E23744]">{searchQuery}</span>&rdquo;
                    </h2>
                    <p className="text-[0.92rem] text-gray-500">
                      Found <b>{totalFound.toLocaleString()}</b> matching restaurants across Bengaluru dataset
                    </p>
                  </div>
                  <button
                    onClick={() => setSearchQuery("")}
                    className="text-sm font-[600] text-[#E23744] hover:underline"
                  >
                    Clear Search
                  </button>
                </div>

                {isSearching ? (
                  <div className="text-center py-16 text-gray-400">
                    <div className="animate-spin inline-block w-8 h-8 border-4 border-[#E23744] border-t-transparent rounded-full mb-3" />
                    <div>Searching 9,249+ restaurants...</div>
                  </div>
                ) : searchResults.length === 0 ? (
                  <div className="bg-white border border-[#ECECEC] rounded-2xl p-12 text-center shadow-sm">
                    <div className="text-4xl mb-3">🍽️</div>
                    <div className="text-lg font-[700] text-[#1C1C1C] mb-2">
                      No restaurants found for &ldquo;{searchQuery}&rdquo;
                    </div>
                    <p className="text-sm text-gray-500 max-w-md mx-auto">
                      Try searching for a cuisine like <b>Biryani</b>, <b>Pizza</b>, or <b>Chinese</b>, a locality like <b>Indiranagar</b> or <b>Koramangala</b>, or a restaurant like <b>Truffles</b>.
                    </p>
                  </div>
                ) : (
                  <div className="space-y-4">
                    {searchResults.map((rest) => (
                      <div
                        key={rest.restaurant_id}
                        className="bg-white border border-[#EAEAEA] rounded-2xl overflow-hidden shadow-sm hover:shadow-md transition-all flex flex-col md:flex-row"
                      >
                        <div className="md:w-[220px] h-[160px] md:h-auto relative shrink-0">
                          <img
                            src={rest.image_url}
                            alt={rest.name}
                            className="w-full h-full object-cover"
                          />
                          <span className="absolute top-2.5 left-2.5 bg-[#1C1C1C]/80 text-white text-[0.72rem] font-[700] px-2.5 py-1 rounded-md backdrop-blur-sm">
                            📍 {rest.location}
                          </span>
                        </div>
                        <div className="p-4 sm:p-5 flex-1 flex flex-col justify-between">
                          <div>
                            <div className="flex justify-between items-start gap-4">
                              <div>
                                <h3 className="text-[1.15rem] font-[800] text-[#1C1C1C]">
                                  {rest.name}
                                </h3>
                                <p className="text-[0.88rem] text-gray-600 mt-0.5">{rest.cuisines}</p>
                                <p className="text-[0.82rem] text-gray-400 mt-1">
                                  {rest.votes_count.toLocaleString()} customer reviews on Zomato
                                </p>
                              </div>
                              <div className="flex flex-col items-end gap-1 shrink-0">
                                <span className="bg-[#24963F] text-white text-[0.88rem] font-[700] px-2.5 py-1 rounded-lg">
                                  ★ {rest.rating.toFixed(1)}
                                </span>
                                <span className="text-[0.85rem] font-[700] text-gray-800">
                                  {rest.cost_for_two ? `₹${Math.round(rest.cost_for_two)} for two` : "Price on request"}
                                </span>
                              </div>
                            </div>
                            {rest.dish_liked && (
                              <div className="mt-2.5 text-[0.8rem] bg-gray-50 border border-gray-100 rounded-md px-2.5 py-1 text-gray-700">
                                🍽️ <b>Popular Dishes:</b> {rest.dish_liked}
                              </div>
                            )}
                          </div>
                          <div className="mt-3 pt-3 border-t border-gray-100 flex justify-between items-center text-xs text-gray-500">
                            <div className="flex gap-2">
                              <span className="bg-gray-100 px-2 py-0.5 rounded">🛵 Online Order</span>
                              <span className="bg-gray-100 px-2 py-0.5 rounded">🪑 Dine-in</span>
                            </div>
                            <a
                              href={rest.url || "#"}
                              target="_blank"
                              rel="noreferrer"
                              className="bg-[#E23744] hover:bg-[#D32332] text-white text-[0.82rem] font-[600] px-4 py-1.5 rounded-lg transition-colors"
                            >
                              View on Zomato ↗
                            </a>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            ) : submitted && recommendations.length > 0 ? (
              /* View 2: Recommendation Mode (Form Submitted) */
              <div className="space-y-6">
                {/* Active Filter Chips Row */}
                <div className="flex flex-wrap items-center justify-between gap-3 bg-white border border-[#EAEAEA] rounded-xl p-3 shadow-sm">
                  <div className="flex flex-wrap items-center gap-2 text-xs">
                    <span className="bg-red-50 text-[#E23744] border border-red-100 font-[600] px-2.5 py-1 rounded-md">
                      📍 {selectedLocation}
                    </span>
                    <span className="bg-gray-100 text-gray-700 font-[600] px-2.5 py-1 rounded-md capitalize">
                      💰 {budgetBand} Band
                    </span>
                    <span className="bg-gray-100 text-gray-700 font-[600] px-2.5 py-1 rounded-md">
                      🍕 {selectedCuisine}
                    </span>
                    <span className="bg-gray-100 text-gray-700 font-[600] px-2.5 py-1 rounded-md">
                      ⭐ &gt;= {minRating.toFixed(1)}
                    </span>
                  </div>
                  <button
                    onClick={handleResetView}
                    className="text-xs font-[700] text-[#E23744] hover:underline"
                  >
                    Reset View ✕
                  </button>
                </div>

                {/* Performance Metrics Dashboard Grid */}
                {metrics && (
                  <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 bg-white border border-[#EAEAEA] rounded-[16px] p-4 shadow-[0_2px_10px_rgba(0,0,0,0.03)] text-center">
                    <div className="p-2 border-r border-gray-100 last:border-0">
                      <div className="text-[1.1rem] font-[800] text-[#1C1C1C]">
                        {metrics.candidate_count} <span className="text-[0.75rem] font-[600] text-gray-500">Spots</span>
                      </div>
                      <div className="text-[0.72rem] font-[600] text-gray-500 mt-0.5">Candidate Pool</div>
                    </div>
                    <div className="p-2 border-r border-gray-100 last:border-0">
                      <div className="text-[1.1rem] font-[800] text-[#1C1C1C]">
                        {metrics.filter_ms.toFixed(1)} <span className="text-[0.75rem] font-[600] text-gray-500">ms</span>
                      </div>
                      <div className="text-[0.72rem] font-[600] text-gray-500 mt-0.5">Filter Engine</div>
                    </div>
                    <div className="p-2 border-r border-gray-100 last:border-0">
                      <div className="text-[1.1rem] font-[800] text-[#E23744]">
                        {(metrics.llm_ms / 1000).toFixed(2)} <span className="text-[0.75rem] font-[600] text-gray-500">s</span>
                      </div>
                      <div className="text-[0.72rem] font-[600] text-gray-500 mt-0.5">Gemini 3.5 LLM</div>
                    </div>
                    <div className="p-2">
                      <div className="text-[1.1rem] font-[800] text-[#1C1C1C]">
                        {(metrics.total_ms / 1000).toFixed(2)} <span className="text-[0.75rem] font-[600] text-gray-500">s</span>
                      </div>
                      <div className="text-[0.72rem] font-[600] text-gray-500 mt-0.5">Total Latency</div>
                    </div>
                  </div>
                )}

                {/* AI Recommendation Cards (Balanced 2-Column Square Cards) */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
                  {recommendations.map((rec) => (
                    <div
                      key={rec.restaurant_id}
                      className="bg-white border border-[#EAEAEA] rounded-[18px] overflow-hidden shadow-sm hover:shadow-md transition-all flex flex-col justify-between"
                    >
                      <div>
                        {/* Hero Image */}
                        <div className="h-[180px] w-full relative">
                          <img
                            src={rec.image_url}
                            alt={rec.name}
                            className="w-full h-full object-cover"
                          />
                          <div className="absolute top-2.5 left-2.5 flex gap-2">
                            <span className="bg-[#E23744] text-white text-[0.72rem] font-[700] px-2.5 py-1 rounded-md shadow-sm">
                              AI CURATED
                            </span>
                            <span className="bg-black/75 backdrop-blur-sm text-white text-[0.72rem] font-[600] px-2 py-1 rounded-md">
                              📍 {rec.location}
                            </span>
                          </div>
                        </div>

                        {/* Card Body */}
                        <div className="p-5 space-y-3">
                          <div className="flex justify-between items-start gap-3">
                            <div>
                              <h3 className="text-[1.15rem] font-[800] text-[#1C1C1C] leading-snug">
                                {rec.name}
                              </h3>
                              <p className="text-[0.88rem] text-gray-500 mt-0.5">{rec.cuisines}</p>
                            </div>
                            <div className="text-right shrink-0">
                              <span className="bg-[#24963F] text-white text-[0.88rem] font-[700] px-2.5 py-0.5 rounded-md inline-block">
                                ★ {rec.rating.toFixed(1)}
                              </span>
                              <div className="text-[0.82rem] font-[700] text-gray-700 mt-1">
                                {rec.cost_for_two ? `₹${Math.round(rec.cost_for_two)} for two` : "Price on request"}
                              </div>
                            </div>
                          </div>

                          {/* Why Recommended */}
                          <div className="bg-[#FFF9F9] border border-[#FFE8E8] rounded-xl p-3 text-[0.86rem] text-[#363636] leading-relaxed">
                            <span className="font-[700] text-[#E23744] block mb-1">
                              💡 Why Gemini Recommends:
                            </span>
                            {rec.why_recommended}
                          </div>

                          {/* Highlights */}
                          {rec.highlights && rec.highlights.length > 0 && (
                            <div>
                              <span className="text-[0.75rem] font-[700] text-gray-500 uppercase tracking-wide block mb-1.5">
                                Highlights
                              </span>
                              <div className="flex flex-wrap gap-1.5">
                                {rec.highlights.map((h, idx) => (
                                  <span
                                    key={idx}
                                    className="bg-gray-100 text-gray-700 text-[0.76rem] font-[600] px-2 py-0.5 rounded-md"
                                  >
                                    ✓ {h}
                                  </span>
                                ))}
                              </div>
                            </div>
                          )}

                          {/* Must Try Dishes */}
                          {rec.must_try_dishes && rec.must_try_dishes.length > 0 && (
                            <div>
                              <span className="text-[0.75rem] font-[700] text-gray-500 uppercase tracking-wide block mb-1.5">
                                Must-Try Dishes
                              </span>
                              <div className="flex flex-wrap gap-1.5">
                                {rec.must_try_dishes.map((dish, idx) => (
                                  <span
                                    key={idx}
                                    className="bg-red-50 text-[#E23744] border border-red-100 text-[0.76rem] font-[600] px-2 py-0.5 rounded-md"
                                  >
                                    🍽️ {dish}
                                  </span>
                                ))}
                              </div>
                            </div>
                          )}
                        </div>
                      </div>

                      {/* Card Footer */}
                      <div className="p-5 pt-0">
                        <a
                          href={rec.url || "#"}
                          target="_blank"
                          rel="noreferrer"
                          className="w-full h-[40px] bg-[#E23744] hover:bg-[#D32332] text-white text-[0.88rem] font-[700] rounded-xl transition-colors flex items-center justify-center gap-1.5 shadow-sm"
                        >
                          View on Zomato ↗
                        </a>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            ) : (
              /* View 3: Default Landing Showcase */
              <div className="space-y-8">
                {/* Hero Banner ("Better food for more people") */}
                <div className="bg-white border border-[#EAEAEA] rounded-[22px] p-7 text-center shadow-[0_4px_20px_rgba(0,0,0,0.03)] relative overflow-hidden">
                  <h1 className="text-[2.1rem] font-[800] text-[#E23744] leading-tight mb-2 tracking-[-0.5px]">
                    Better food for more people
                  </h1>
                  <p className="text-[0.95rem] text-[#4F4F4F] leading-relaxed max-w-[620px] mx-auto mb-6">
                    For over a decade, we&apos;ve enabled our customers to discover new tastes, delivered right to their doorstep across Bengaluru.
                  </p>

                  {/* Floating Stats Box: Exactly equal sizes (0.98rem), centered in equal 1/3 partitions */}
                  <div className="grid grid-cols-3 bg-white border border-[#ECECEC] rounded-[14px] p-3 shadow-[0_4px_16px_rgba(0,0,0,0.05)] max-w-full mx-auto">
                    {/* Stat 1 */}
                    <div className="flex flex-col items-center justify-center p-1 border-r border-[#ECECEC] overflow-hidden min-w-0">
                      <div className="text-[0.98rem] font-[700] text-[#1C1C1C] flex items-center gap-1.5 whitespace-nowrap leading-tight">
                        <span>{totalRestaurants.toLocaleString()}+</span>
                        <span className="text-[0.92rem]">🏬</span>
                      </div>
                      <div className="text-[0.72rem] font-[600] text-[#696969] mt-1 text-center leading-tight">
                        Restaurants in Bengaluru
                      </div>
                    </div>

                    {/* Stat 2 */}
                    <div className="flex flex-col items-center justify-center p-1 border-r border-[#ECECEC] overflow-hidden min-w-0">
                      <div className="text-[0.98rem] font-[700] text-[#1C1C1C] flex items-center gap-1.5 whitespace-nowrap leading-tight">
                        <span>{totalLocalities}+</span>
                        <span className="text-[0.92rem]">📍</span>
                      </div>
                      <div className="text-[0.72rem] font-[600] text-[#696969] mt-1 text-center leading-tight">
                        Localities Covered
                      </div>
                    </div>

                    {/* Stat 3 */}
                    <div className="flex flex-col items-center justify-center p-1 overflow-hidden min-w-0">
                      <div className="text-[0.98rem] font-[700] text-[#1C1C1C] flex items-center gap-1.5 whitespace-nowrap leading-tight">
                        <span>Gemini 3.5</span>
                        <span className="text-[0.92rem]">✨</span>
                      </div>
                      <div className="text-[0.72rem] font-[600] text-[#696969] mt-1 text-center leading-tight">
                        AI Recommendation Engine
                      </div>
                    </div>
                  </div>
                </div>

                {/* Inspiration for your first order (Large, clear, equal circles) */}
                <div>
                  <h2 className="text-[1.35rem] font-[700] text-[#1C1C1C] mb-4">
                    Inspiration for your first order
                  </h2>
                  <div className="grid grid-cols-3 sm:grid-cols-6 lg:grid-cols-9 gap-3">
                    {INSPIRATION_DISHES.map((d) => (
                      <button
                        key={d.name}
                        onClick={() => setSelectedCuisine(d.name)}
                        className="flex flex-col items-center group text-center"
                      >
                        <div className="w-[68px] h-[68px] sm:w-[74px] sm:h-[74px] rounded-full overflow-hidden border-2 border-transparent group-hover:border-[#E23744] group-hover:scale-105 transition-all shadow-sm">
                          <img
                            src={d.image}
                            alt={d.name}
                            className="w-full h-full object-cover"
                          />
                        </div>
                        <span className="text-[0.82rem] font-[600] text-[#363636] mt-2 group-hover:text-[#E23744] transition-colors leading-tight">
                          {d.name}
                        </span>
                      </button>
                    ))}
                  </div>
                </div>

                {/* Top brands for you in Bengaluru */}
                <div>
                  <h2 className="text-[1.35rem] font-[700] text-[#1C1C1C] mb-4">
                    Top brands for you in Bengaluru
                  </h2>
                  <div className="grid grid-cols-2 sm:grid-cols-5 gap-3">
                    {TOP_BRANDS.map((b) => (
                      <div
                        key={b.name}
                        className="bg-white border border-[#EAEAEA] rounded-xl p-3.5 text-center shadow-sm hover:shadow-md transition-all hover:-translate-y-1"
                      >
                        <div className={`w-12 h-12 mx-auto rounded-full ${b.color} flex items-center justify-center text-xl mb-2 shadow-inner`}>
                          {b.icon}
                        </div>
                        <div className="text-[0.84rem] font-[700] text-[#1C1C1C] truncate">{b.name}</div>
                        <div className="text-[0.72rem] text-gray-500 mt-0.5">{b.time}</div>
                      </div>
                    ))}
                  </div>
                </div>

                {/* What's waiting for you on the app */}
                <div>
                  <h2 className="text-[1.35rem] font-[700] text-[#1C1C1C] mb-4">
                    What&apos;s waiting for you on the app?
                  </h2>
                  <div className="grid grid-cols-3 sm:grid-cols-6 gap-3">
                    {FEATURE_CARDS.map((f) => (
                      <div
                        key={f.title}
                        className="bg-white border border-[#EAEAEA] rounded-xl p-3 text-center shadow-sm hover:shadow-md transition-all hover:-translate-y-1"
                      >
                        <span className="text-2xl block mb-1.5">{f.icon}</span>
                        <span className="text-[0.78rem] font-[600] text-[#363636]">{f.title}</span>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Trending & Top-Rated in Bengaluru */}
                <div>
                  <h2 className="text-[1.35rem] font-[700] text-[#1C1C1C] mb-4 flex items-center gap-2">
                    🔥 Trending &amp; Top-Rated in Bengaluru
                  </h2>
                  <div className="space-y-4">
                    {trending.map((r) => (
                      <div
                        key={r.restaurant_id}
                        className="bg-white border border-[#EAEAEA] rounded-[18px] overflow-hidden shadow-sm hover:shadow-md transition-all flex flex-col md:flex-row"
                      >
                        <div className="md:w-[240px] h-[170px] md:h-auto relative shrink-0">
                          <img
                            src={r.image_url}
                            alt={r.name}
                            className="w-full h-full object-cover"
                          />
                          <div className="absolute top-2.5 left-2.5 flex flex-col gap-1.5">
                            <span className="bg-[#E23744] text-white text-[0.72rem] font-[700] px-2 py-0.5 rounded shadow">
                              POPULAR SPOT
                            </span>
                            <span className="bg-black/75 backdrop-blur-sm text-white text-[0.7rem] font-[600] px-2 py-0.5 rounded">
                              ⭐ BENGALURU LEGEND
                            </span>
                          </div>
                        </div>
                        <div className="p-5 flex-1 flex flex-col justify-between">
                          <div>
                            <div className="flex justify-between items-start gap-4">
                              <div>
                                <h3 className="text-[1.2rem] font-[800] text-[#1C1C1C]">
                                  {r.name}
                                </h3>
                                <p className="text-[0.9rem] text-gray-600 mt-0.5">{r.cuisines}</p>
                                <p className="text-[0.82rem] text-gray-400 mt-1">
                                  📍 {r.location} • {r.votes_count.toLocaleString()} customer reviews
                                </p>
                              </div>
                              <div className="flex flex-col items-end gap-1 shrink-0">
                                <span className="bg-[#24963F] text-white text-[0.92rem] font-[700] px-2.5 py-0.5 rounded-lg">
                                  ★ {r.rating.toFixed(1)}
                                </span>
                                <span className="text-[0.88rem] font-[700] text-gray-800">
                                  {r.cost_for_two ? `₹${Math.round(r.cost_for_two)} for two` : "Price on request"}
                                </span>
                                <span className="text-[0.72rem] font-[700] text-[#E23744] bg-[#FFF0F1] px-2 py-0.5 rounded border border-[rgba(226,55,68,0.2)]">
                                  🏆 Top 1% in Bengaluru
                                </span>
                              </div>
                            </div>
                          </div>
                          <div className="mt-4 pt-3 border-t border-gray-100 flex justify-between items-center text-xs text-gray-500">
                            <div className="flex gap-2">
                              <span className="bg-gray-100 px-2 py-0.5 rounded">🛵 Online Order</span>
                              <span className="bg-gray-100 px-2 py-0.5 rounded">🪑 Table Booking</span>
                              <span className="bg-gray-100 px-2 py-0.5 rounded">🥘 Dine-in</span>
                            </div>
                            <a
                              href={r.url || "#"}
                              target="_blank"
                              rel="noreferrer"
                              className="bg-[#E23744] hover:bg-[#D32332] text-white text-[0.85rem] font-[600] px-4 py-1.5 rounded-lg transition-colors"
                            >
                              View on Zomato ↗
                            </a>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      </main>

      {/* Footer */}
      <footer className="mt-16 border-t border-[#ECECEC] bg-white py-8 text-center text-xs text-gray-400">
        <div className="max-w-[1400px] mx-auto px-4 flex flex-col sm:flex-row justify-between items-center gap-4">
          <div className="flex items-center gap-2">
            <span className="text-xl font-[900] italic text-[#E23744]">zomato</span>
            <span>AI Restaurant Recommendation Engine</span>
          </div>
          <div>
            Powered by Next.js, Google Gemini AI (gemini-3.5-flash-lite) &amp; 9,249+ Bengaluru Restaurants
          </div>
        </div>
      </footer>
    </div>
  );
}
