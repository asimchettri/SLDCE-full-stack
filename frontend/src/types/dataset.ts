export interface Dataset {
  id: number;
  name: string;
  description: string | null;
  file_path: string;
  num_samples: number;
  num_features: number;
  num_classes: number;
  created_at: string;
  updated_at: string | null;
  is_active: boolean;
}

export interface DatasetStats {
  dataset_id: number;
  name: string;
  total_samples: number;
  num_features: number;
  num_classes: number;
  suspicious_samples: number;
  corrected_samples: number;
  mismatched_labels: number;
  noise_percentage: number;
}

export interface Sample {
  id: number;
  dataset_id: number;
  sample_index: number;
  features: string;
  original_label: number;
  current_label: number;
  is_suspicious: boolean;
  is_corrected: boolean;
  created_at: string;
  updated_at: string | null;
}