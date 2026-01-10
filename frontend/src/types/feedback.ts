/**
 * Feedback-related TypeScript types
 * CRITICAL: Feedback data feeds Phase 2 memory/learning system
 */

export interface Feedback {
  id: number;
  suggestion_id: number;
  sample_id: number;
  action: FeedbackAction;
  final_label: number;
  iteration: number;
  review_time_seconds?: number;
  created_at: string;
}

export interface FeedbackWithDetails extends Feedback {
  current_label?: number;
  suggested_label?: number;
  original_label?: number;
  confidence_score?: number;
  detection_info?: {
    confidence_score: number;
    anomaly_score: number;
    priority_score: number;
  };
}

export interface FeedbackStats {
  dataset_id: number;
  total_feedback: number;
  accept_count: number;
  reject_count: number;
  modify_count: number;
  acceptance_rate: number;
  avg_review_time?: number;
}

export interface FeedbackPatterns {
  dataset_id: number;
  iteration: number;
  most_accepted_class?: number;
  most_rejected_class?: number;
  high_confidence_acceptance_rate: number;
  low_confidence_acceptance_rate: number;
}

export interface FeedbackListResponse {
  feedback: Feedback[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export type FeedbackAction = 'accept' | 'reject' | 'modify';

export interface FeedbackFilters {
  dataset_id?: number;
  iteration?: number;
  action?: FeedbackAction;
  page?: number;
  page_size?: number;
}