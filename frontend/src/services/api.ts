import axios from "axios";
import type { Dataset, DatasetStats } from "../types/dataset";
import type { MLModel, ModelIteration, ModelComparisonItem } from "../types/model";
import type {
  Experiment,
  ExperimentIteration,
  ExperimentSummary,
} from "../types/experiment";
import type {
  Detection,
  DetectionRunRequest,
  DetectionRunResponse,
  DetectionStats,
  SuggestionGenerateResponse,
  SignalStats,
} from "../types/detection";

import type {
  Suggestion,
  SuggestionWithDetection,
  SuggestionGenerateRequest,
  SuggestionListResponse,
  SuggestionUpdateRequest,
  SuggestionStats,
  SuggestionFilters,
} from "../types/suggestion";

import type {
  Feedback,
  FeedbackWithDetails,
  FeedbackStats,
  FeedbackPatterns,
  FeedbackListResponse,
  FeedbackFilters,
} from "../types/feedback";
const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

export const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    "Content-Type": "application/json",
  },
});

// Dataset API calls
export const datasetAPI = {
  // Get all datasets
  getAll: async (): Promise<Dataset[]> => {
    const response = await api.get("/api/v1/datasets");
    return response.data;
  },

  // Get single dataset
  getById: async (id: number): Promise<Dataset> => {
    const response = await api.get(`/api/v1/datasets/${id}`);
    return response.data;
  },

 

// Upload dataset
upload: async (
  file: File,
  name: string,
  description?: string,
  labelColumn?: string 
): Promise<Dataset> => {
  const formData = new FormData();
  formData.append("file", file);
  formData.append("name", name);
  if (description) {
    formData.append("description", description);
  }
  //  Append label column if provided
  if (labelColumn) {
    formData.append("label_column", labelColumn);
  }

  const response = await api.post("/api/v1/datasets/upload", formData, {
    headers: {
      "Content-Type": "multipart/form-data",
    },
  });
  return response.data;
},

  // Get dataset stats
  getStats: async (id: number): Promise<DatasetStats> => {
    const response = await api.get(`/api/v1/datasets/${id}/stats`);
    return response.data;
  },

  // Delete dataset
  delete: async (id: number): Promise<void> => {
    await api.delete(`/api/v1/datasets/${id}`);
  },
};

export const modelAPI = {
  // Get all models
  getAll: async (datasetId?: number): Promise<MLModel[]> => {
    const params = datasetId ? { dataset_id: datasetId } : {};
    const response = await api.get("/api/v1/models", { params });
    return response.data;
  },

  // Get single model
  getById: async (id: number): Promise<MLModel> => {
    const response = await api.get(`/api/v1/models/${id}`);
    return response.data;
  },

  // Create model
  create: async (data: {
    dataset_id: number;
    name: string;
    model_type: string;
    description?: string;
    hyperparameters?: Record<string, any>;
  }): Promise<MLModel> => {
    const response = await api.post("/api/v1/models", data);
    return response.data;
  },

  // Get model iterations
  getIterations: async (modelId: number): Promise<ModelIteration[]> => {
    const response = await api.get(`/api/v1/models/${modelId}/iterations`);
    return response.data;
  },

  // Compare models for a dataset
  compare: async (datasetId: number): Promise<ModelComparisonItem[]> => {
    const response = await api.get(
      `/api/v1/models/dataset/${datasetId}/compare`
    );
    return response.data;
  },

  // Delete model
  delete: async (id: number): Promise<void> => {
    await api.delete(`/api/v1/models/${id}`);
  },
};

export const experimentAPI = {
  // Get all experiments
  getAll: async (datasetId?: number): Promise<Experiment[]> => {
    const params = datasetId ? { dataset_id: datasetId } : {};
    const response = await api.get("/api/v1/experiments", { params });
    return response.data;
  },

  // Get single experiment
  getById: async (id: number): Promise<Experiment> => {
    const response = await api.get(`/api/v1/experiments/${id}`);
    return response.data;
  },

  // Create experiment
  create: async (data: {
    dataset_id: number;
    name: string;
    description?: string;
    noise_percentage: number;
    detection_threshold?: number;
    max_iterations?: number;
  }): Promise<Experiment> => {
    const response = await api.post("/api/v1/experiments", data);
    return response.data;
  },

  // Get experiment iterations
  getIterations: async (
    experimentId: number
  ): Promise<ExperimentIteration[]> => {
    const response = await api.get(
      `/api/v1/experiments/${experimentId}/iterations`
    );
    return response.data;
  },

  // Get experiment summary
  getSummary: async (experimentId: number): Promise<ExperimentSummary> => {
    const response = await api.get(
      `/api/v1/experiments/${experimentId}/summary`
    );
    return response.data;
  },

  // Complete experiment
  complete: async (
    experimentId: number,
    totalTimeSeconds?: number
  ): Promise<Experiment> => {
    const response = await api.post(
      `/api/v1/experiments/${experimentId}/complete`,
      null,
      {
        params: { total_time_seconds: totalTimeSeconds },
      }
    );
    return response.data;
  },
};

export const detectionAPI = {
  run: async (request: DetectionRunRequest): Promise<DetectionRunResponse> => {
    const response = await api.post("/api/v1/detection/run", request);
    return response.data;
  },

  getAll: async (params?: {
    dataset_id?: number;
    iteration?: number;
    min_priority?: number;
    min_confidence?: number;
    min_anomaly?: number;
    signal_type?: string;
    limit?: number;
    offset?: number;
  }): Promise<Detection[]> => {
    const response = await api.get("/api/v1/detection/list", { params });
    return response.data;
  },

  // Get detection details
  getById: async (detectionId: number): Promise<any> => {
    const response = await api.get(`/api/v1/detection/${detectionId}`);
    return response.data;
  },

  // Generate suggestions
  generateSuggestions: async (
    datasetId: number,
    iteration: number = 1
  ): Promise<SuggestionGenerateResponse> => {
    const response = await api.post("/api/v1/detection/suggestions", null, {
      params: { dataset_id: datasetId, iteration },
    });
    return response.data;
  },

  // Get detection stats
  getStats: async (datasetId: number): Promise<DetectionStats> => {
    const response = await api.get(`/api/v1/detection/stats/${datasetId}`);
    return response.data;
  },

  // NEW: Get signal-specific stats
  getSignalStats: async (datasetId: number): Promise<SignalStats> => {
    const response = await api.get(
      `/api/v1/detection/signal-stats/${datasetId}`
    );
    return response.data;
  },
};

export const suggestionAPI = {
  // Generate suggestions
  generate: async (
    request: SuggestionGenerateRequest
  ): Promise<SuggestionGenerateResponse> => {
    const response = await api.post("/api/v1/suggestions/generate", request);
    return response.data;
  },

  // Get suggestions with filters and pagination
  getAll: async (
    filters?: SuggestionFilters
  ): Promise<SuggestionListResponse> => {
    const response = await api.get("/api/v1/suggestions/list", {
      params: filters,
    });
    return response.data;
  },

  // Get single suggestion
  getById: async (suggestionId: number): Promise<Suggestion> => {
    const response = await api.get(`/api/v1/suggestions/${suggestionId}`);
    return response.data;
  },

  // Get suggestion with full details
  getDetails: async (
    suggestionId: number
  ): Promise<SuggestionWithDetection> => {
    const response = await api.get(
      `/api/v1/suggestions/${suggestionId}/details`
    );
    return response.data;
  },

  // Update suggestion status (for human feedback)
  updateStatus: async (
    suggestionId: number,
    request: SuggestionUpdateRequest
  ): Promise<Suggestion> => {
    const response = await api.patch(
      `/api/v1/suggestions/${suggestionId}/status`,
      {
        status: request.status,
        reviewer_notes: request.reviewer_notes,
        custom_label: request.custom_label, 
      }
    );
    return response.data;
  },

  // Get suggestion statistics
  getStats: async (datasetId: number): Promise<SuggestionStats> => {
    const response = await api.get(`/api/v1/suggestions/stats/${datasetId}`);
    return response.data;
  },

  // Delete suggestion
  delete: async (suggestionId: number): Promise<void> => {
    await api.delete(`/api/v1/suggestions/${suggestionId}`);
  },
};




export const feedbackAPI = {
  // Get feedback with filters and pagination
  getAll: async (filters?: FeedbackFilters): Promise<FeedbackListResponse> => {
    const response = await api.get("/api/v1/feedback/list", {
      params: filters,
    });
    return response.data;
  },

  // Get single feedback
  getById: async (feedbackId: number): Promise<Feedback> => {
    const response = await api.get(`/api/v1/feedback/${feedbackId}`);
    return response.data;
  },

  // Get feedback with full details
  getDetails: async (feedbackId: number): Promise<FeedbackWithDetails> => {
    const response = await api.get(`/api/v1/feedback/${feedbackId}/details`);
    return response.data;
  },

  // Get feedback statistics
  getStats: async (datasetId: number): Promise<FeedbackStats> => {
    const response = await api.get(`/api/v1/feedback/stats/${datasetId}`);
    return response.data;
  },

  // Analyze feedback patterns (Phase 2 learning data)
  getPatterns: async (
    datasetId: number,
    iteration: number = 1
  ): Promise<FeedbackPatterns> => {
    const response = await api.get(`/api/v1/feedback/patterns/${datasetId}`, {
      params: { iteration },
    });
    return response.data;
  },

  // Delete feedback
  delete: async (feedbackId: number): Promise<void> => {
    await api.delete(`/api/v1/feedback/${feedbackId}`);
  },
};

//  Corrections API
export const correctionsAPI = {
  // Apply corrections
  apply: async (datasetId: number, iteration: number = 1): Promise<any> => {
    const response = await api.post(`/api/v1/corrections/apply/${datasetId}`, null, {
      params: { iteration },
    });
    return response.data;
  },

  // Preview corrections
  preview: async (datasetId: number, iteration: number = 1): Promise<any> => {
    const response = await api.get(`/api/v1/corrections/preview/${datasetId}`, {
      params: { iteration },
    });
    return response.data;
  },

  // Get correction summary
  getSummary: async (datasetId: number): Promise<any> => {
    const response = await api.get(`/api/v1/corrections/summary/${datasetId}`);
    return response.data;
  },
};

//  Retrain API
export const retrainAPI = {
  // Retrain model
  retrain: async (datasetId: number, iteration: number = 1, testSize: number = 0.2): Promise<any> => {
    const response = await api.post(`/api/v1/retrain/retrain/${datasetId}`, null, {
      params: { iteration, test_size: testSize },
    });
    return response.data;
  },

  // Compare models
  compare: async (datasetId: number): Promise<any> => {
    const response = await api.get(`/api/v1/retrain/compare/${datasetId}`);
    return response.data;
  },

  download: async (datasetId: number): Promise<Blob> => {
    const response = await api.get(`/api/v1/corrections/download/${datasetId}`, {
      responseType: 'blob'
    });
    return response.data;
  },
};



export const baselineAPI = {
  // Train baseline model
  train: async (
    datasetId: number,
    modelType: 'random_forest' | 'logistic' | 'svm' = 'random_forest',
    testSize: number = 0.2,
    hyperparameters?: Record<string, any>
  ): Promise<any> => {
    const response = await api.post('/api/v1/baseline/train', {
      dataset_id: datasetId,
      model_type: modelType,
      test_size: testSize,
      hyperparameters,
    });
    return response.data;
  },

  // Check if baseline exists
  checkExists: async (datasetId: number): Promise<any> => {
    const response = await api.get(`/api/v1/baseline/check/${datasetId}`);
    return response.data;
  },
};