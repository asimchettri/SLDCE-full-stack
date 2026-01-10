export interface MLModel {
  id: number;
  dataset_id: number;
  name: string;
  model_type: string;
  description: string | null;
  hyperparameters: Record<string, any> | null;
  train_accuracy: number | null;
  test_accuracy: number | null;
  precision: number | null;
  recall: number | null;
  f1_score: number | null;
  num_samples_trained: number | null;
  training_time_seconds: number | null;
  is_active: boolean;
  is_baseline: boolean;
  created_at: string;
}

export interface ModelIteration {
  id: number;
  model_id: number;
  dataset_id: number;
  iteration_number: number;
  accuracy: number;
  precision: number | null;
  recall: number | null;
  f1_score: number | null;
  samples_corrected: number;
  noise_reduced: number;
  created_at: string;
}

export interface ModelComparison {
  model_id: number;
  name: string;
  model_type: string;
  accuracy: number;
  precision: number | null;
  recall: number | null;
  f1_score: number | null;
  training_time: number | null;
  is_baseline: boolean;
}