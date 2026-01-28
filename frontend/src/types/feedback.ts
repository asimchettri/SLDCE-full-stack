/**
 * Feedback-related TypeScript types
 * CRITICAL: Feedback data feeds Phase 2 memory/learning system
 * FIXED: Aligned with backend FeedbackStatsResponse schema
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
  accepted: number;     
  rejected: number;     
  modified: number;     
  acceptance_rate: number;
  avg_review_time?: number;
}

export interface PatternRangeData {
  total: number;
  accepted:number;
  acceptance_rate: number;
}
export interface FeedbackPatterns {
  dataset_id: number;
  iteration?: number;
  patterns_found: number;
  acceptance_by_confidence?: {
    [range: string]: PatternRangeData; 
  };
  acceptance_by_priority?: {
    [priority: string]: PatternRangeData; 
  };
  insights?: string[];
  message?: string; 
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