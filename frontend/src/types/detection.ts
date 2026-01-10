export interface Detection {
  id: number;
  sample_id: number;
  iteration: number;
  confidence_score: number;
  anomaly_score: number;
  predicted_label: number;
  priority_score: number;
  rank: number | null;
  detected_at: string;
  
  entropy_score?: number;
  distance_score?: number;
  signal_breakdown?: string; 
  priority_weights?: string; 
}

export interface DetectionWithSample {
  detection_id: number;
  sample_id: number;
  features: number[];
  current_label: number;
  predicted_label: number;
  original_label: number;
  confidence_score: number;
  anomaly_score: number;
  priority_score: number;
  iteration?: number;
  detected_at?: string;
  signal_breakdown?: SignalBreakdown;
  priority_weights?: PriorityWeights;
}

export interface DetectionRunRequest {
  dataset_id: number;
  confidence_threshold?: number;
  max_samples?: number;
  priority_weights?: PriorityWeights; // NEW
}

export interface DetectionRunResponse {
  dataset_id: number;
  iteration: number;
  total_samples_analyzed: number;
  suspicious_samples_found: number;
  detection_rate: number;
  confidence_threshold: number;
  timestamp: string;
}

export interface DetectionStats {
  dataset_id: number;
  total_samples: number;
  suspicious_samples: number;
  total_detections: number;
  high_priority_detections: number;
  average_confidence: number;
  detection_rate: number;
}


export interface SignalStats {
  dataset_id: number;
  total_detections: number;
  confidence_dominant: number;
  anomaly_dominant: number;
  both_high: number;
  avg_confidence: number;
  avg_anomaly: number;
}

export interface SuggestionGenerateResponse {
  dataset_id: number;
  iteration: number;
  suggestions_created: number;
  total_detections: number;
  message?: string;
}

export interface MetricsSummary {
  dataset_id: number;
  dataset_name: string;
  total_samples: number;
  suspicious_samples: number;
  high_priority_samples: number;
  detection_rate: number;
  average_confidence: number;
  average_anomaly: number;
  average_priority: number;
  precision?: number;
  recall?: number;
  f1_score?: number;
}

export interface PerformanceMetrics {
  iteration: number;
  accuracy: number;
  precision: number;
  recall: number;
  f1_score: number;
  samples_corrected: number;
  timestamp: string;
}


export interface PriorityWeights {
  confidence: number;
  anomaly: number;
}


export interface SignalBreakdown {
  confidence: number;
  anomaly: number;
  entropy?: number;
  distance?: number;
  timestamp?: string;
}

export type SignalType = 'all' | 'confidence' | 'anomaly' | 'both';