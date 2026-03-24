

export interface EngineThreshold {
  dataset_id: number;
  threshold: number | null;
  fitted: boolean;
  feedback_count?: number;
  message?: string;
}

export interface EngineStatus {
  dataset_id: number;
  exists: boolean;
  fitted: boolean;
  on_disk: boolean;
  file_path: string;
}

export interface LearningCycleResult {
  dataset_id: number;
  meta_model: {
    trained: boolean;
    feedback_count: number;
  };
  threshold: {
    previous_threshold: number;
    new_threshold: number;
    correction_precision: number;
  };
  retrain: {
    retrained: boolean;
    cycle_number: number;
    corrections_applied: number;
  };
}

export interface EngineAnalytics {
  dataset_id?: number;
  message?: string;
  history?: any[];
  [key: string]: any;
}