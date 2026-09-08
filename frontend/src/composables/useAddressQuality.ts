import { computed } from "vue";
import type { ComputedRef } from "vue";

const BROAD_TERMS = new Set([
  "hong kong",
  "russia",
  "russian federation",
  "singapore",
  "china",
  "united states",
  "usa",
  "us",
  "united kingdom",
  "uk",
  "iran",
  "uae",
  "united arab emirates",
  "moscow",
  "beijing",
  "new york",
  "london",
  "philadelphia",
  "unknown",
  "n/a",
  "na",
]);

export interface AddressQualityResult {
  score: ComputedRef<number>;
  isBroad: ComputedRef<boolean>;
  warning: ComputedRef<string>;
}

function normalize(text: string): string {
  return text.trim().toLowerCase().replace(/\s+/g, " ");
}

function assessAddressQuality(fullText: string): {
  score: number;
  isBroad: boolean;
} {
  const normalized = normalize(fullText);

  if (!normalized) {
    return { score: 0, isBroad: false };
  }

  if (BROAD_TERMS.has(normalized)) {
    return { score: 0.1, isBroad: true };
  }

  if (/\d/.test(normalized)) {
    return { score: 1.0, isBroad: false };
  }

  const tokens = normalized.split(" ");
  if (tokens.length >= 3) {
    return { score: 0.7, isBroad: false };
  }

  return { score: 0.3, isBroad: true };
}

export function useAddressQuality(fullText: string): AddressQualityResult {
  const score = computed(() => assessAddressQuality(fullText).score);
  const isBroad = computed(() => assessAddressQuality(fullText).isBroad);

  const warning = computed(() => {
    if (!isBroad.value) return "";
    return "This address is very broad and may produce many false-positive matches. Consider entering a street address.";
  });

  return {
    score,
    isBroad,
    warning,
  };
}
