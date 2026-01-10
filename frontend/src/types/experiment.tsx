export interface Experiment {
  id: number;
  dataset_id: number;
  name: string;
  description: string | null;
  status: 'running' | 'completed' | 'failed';
  noise_percentage: number;
  detection_threshold: number;
  max_iterations: number;
  current_iteration: number;
  baseline_accuracy: number | null;
  final_accuracy: number | null;
  total_corrections: number;
  total_time_seconds: number | null;
  iteration_results: Record<string, any> | null;
  created_at: string;
  updated_at: string | null;
  completed_at: string | null;
}

export interface ExperimentIteration {
  id: number;
  experiment_id: number;
  iteration_number: number;
  accuracy: number;
  precision: number | null;
  recall: number | null;
  f1_score: number | null;
  samples_flagged: number;
  samples_corrected: number;
  correction_acceptance_rate: number | null;
  remaining_noise_percentage: number | null;
  samples_reviewed: number;
  iteration_time_seconds: number | null;
  created_at: string;
}

export interface ExperimentSummary {
  experiment_id: number;
  name: string;
  status: string;
  total_iterations: number;
  accuracy_improvement: number;
  noise_reduction: number;
  total_corrections: number;
  avg_time_per_iteration: number;
}