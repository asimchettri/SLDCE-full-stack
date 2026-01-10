/**
 * Suggestion-related TypeScript types
 */

export interface Suggestion {
  id: number;
  detection_id: number;
  suggested_label: number;
  reason: string;
  confidence: number;
  status: SuggestionStatus;
  created_at: string;
  reviewed_at?: string;
  reviewer_notes?: string;
}

export interface SuggestionWithDetection extends Suggestion {
  detection_info?: {
    confidence_score: number;
    anomaly_score: number;
    priority_score: number;
    iteration: number;
  };
  sample_features?: number[];
  current_label?: number;
  predicted_label?: number;
  original_label?: number;
}

export interface SuggestionGenerateRequest {
  dataset_id: number;
  iteration?: number;
  top_n?: number;
}

export interface SuggestionGenerateResponse {
  dataset_id: number;
  iteration: number;
  suggestions_created: number;
  total_detections: number;
  message?: string;
}

export interface SuggestionListResponse {
  suggestions: Suggestion[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export interface SuggestionUpdateRequest {
  status: SuggestionReviewStatus; // Only reviewable statuses
  reviewer_notes?: string;
  custom_label?: number; // For 'modified' action
}

export interface SuggestionStats {
  dataset_id: number;
  total_suggestions: number;
  pending: number;
  accepted: number;
  rejected: number;
  modified: number;
  acceptance_rate: number;
}

export type SuggestionStatus = 'pending' | 'accepted' | 'rejected' | 'modified';

// Only statuses that can be set during review (excludes 'pending')
export type SuggestionReviewStatus = 'accepted' | 'rejected' | 'modified';

export interface SuggestionFilters {
  dataset_id?: number;
  iteration?: number;
  status?: SuggestionStatus;
  min_confidence?: number;
  page?: number;
  page_size?: number;
}