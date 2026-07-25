/** Mirrors app.models.schemas.AuditReport on the backend. */
export interface AuditReport {
  url: string;
  status: number;
  response_time_ms: number;
  title: string | null;
  meta_description: string | null;
  h1_count: number;
  images_without_alt: number;
  word_count: number;

  // Bonus / extended fields - optional so the UI degrades gracefully
  // if the backend contract is ever trimmed down.
  total_images?: number | null;
  canonical_url?: string | null;
  og_title?: string | null;
  favicon_present?: boolean | null;
  language?: string | null;
  content_size_bytes?: number | null;
  seo_score?: number | null;
}

/** Mirrors app.models.schemas.ErrorResponse on the backend. */
export interface ApiError {
  error_code: string;
  message: string;
}
