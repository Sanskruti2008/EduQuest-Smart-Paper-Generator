export const REVIEW_STORAGE_KEY = 'extracted_for_review';

type ReviewPayload = Record<string, any> | null;

export const readReviewData = (): ReviewPayload => {
  if (typeof window === 'undefined') return null;

  const globalData = (window as any).__EDUQUEST_REVIEW_DATA__;
  if (globalData) return globalData;

  const storageSources = [
    sessionStorage.getItem(REVIEW_STORAGE_KEY),
    localStorage.getItem(REVIEW_STORAGE_KEY),
  ];

  for (const raw of storageSources) {
    if (!raw) continue;
    try {
      const parsed = JSON.parse(raw);
      if (parsed) return parsed;
    } catch {
      // ignore malformed storage data
    }
  }

  return null;
};

export const saveReviewData = (data: Record<string, any>) => {
  if (!data || typeof window === 'undefined') return;

  const payload = JSON.stringify(data);

  try {
    sessionStorage.setItem(REVIEW_STORAGE_KEY, payload);
    localStorage.setItem(REVIEW_STORAGE_KEY, payload);
    (window as any).__EDUQUEST_REVIEW_DATA__ = data;
  } catch {
    // ignore storage quota issues; route state still carries the payload
    (window as any).__EDUQUEST_REVIEW_DATA__ = data;
  }
};

export const clearReviewData = () => {
  if (typeof window === 'undefined') return;

  sessionStorage.removeItem(REVIEW_STORAGE_KEY);
  localStorage.removeItem(REVIEW_STORAGE_KEY);
  delete (window as any).__EDUQUEST_REVIEW_DATA__;
};
