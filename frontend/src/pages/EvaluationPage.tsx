import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { datasetAPI, retrainAPI, correctionsAPI } from '@/services/api';
import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Label } from '@/components/ui/label';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import {
  BarChart3,
  Download,
  RefreshCw,
  FileText,
  TrendingUp,
  TrendingDown,
  Minus,
  CheckCircle,
  AlertCircle
} from 'lucide-react';
import { ComparisonTable } from '@/components/ComparisonTable';

interface ModelComparisonItem {
  model_id: number;
  name: string;
  model_type: string;
  is_baseline: boolean;
  accuracy: number;
  precision: number | null;
  recall: number | null;
  f1_score: number | null;
  training_time: number | null;
  samples_trained: number | null;
  iteration_number: number | null;
  samples_corrected: number | null;
  noise_reduced: number | null;
  created_at: string | null;
}

interface ModelComparisonResponse {
  dataset_id: number;
  total_models: number;
  models: ModelComparisonItem[];
  overall_improvement: {
    absolute: number;
    percentage: number;
  } | null;
}

interface CorrectionSummary {
  dataset_id: number;
  total_samples: number;
  corrected_samples: number;
  labels_changed: number;
  suspicious_samples: number;
  correction_rate: number;
  noise_reduction: number;
  original_label_distribution: Record<string, number>;
  current_label_distribution: Record<string, number>;
}

export function EvaluationPage() {
  const [selectedDatasetId, setSelectedDatasetId] = useState<number | undefined>();

  // Fetch datasets
  const { data: datasets } = useQuery({
    queryKey: ['datasets'],
    queryFn: datasetAPI.getAll,
  });

  // Fetch model comparison (REAL DATA!)
  const { data: modelComparison, refetch: refetchComparison, isLoading: comparisonLoading } = useQuery<ModelComparisonResponse>({
    queryKey: ['model-comparison', selectedDatasetId],
    queryFn: () => retrainAPI.compare(selectedDatasetId!),
    enabled: !!selectedDatasetId,
  });

  // Fetch correction summary
  const { data: correctionSummary } = useQuery<CorrectionSummary>({
    queryKey: ['correction-summary', selectedDatasetId],
    queryFn: () => correctionsAPI.getSummary(selectedDatasetId!),
    enabled: !!selectedDatasetId,
  });

  const handleRefresh = () => {
    refetchComparison();
  };

  const handleDownloadDataset = async () => {
    if (!selectedDatasetId) return;
    
    try {
      // Download CSV
      window.open(
        `${import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'}/api/v1/corrections/download/${selectedDatasetId}`,
        '_blank'
      );
    } catch (error) {
      console.error('Download failed:', error);
    }
  };

  const handleExportReport = () => {
    window.print();
  };

  // Extract baseline and latest model
  const baselineModel = modelComparison?.models?.find((m: ModelComparisonItem) => m.is_baseline);
  const latestModel = modelComparison?.models?.[modelComparison.models.length - 1];
  
  // Calculate metrics
  const baselineAccuracy = baselineModel?.accuracy || 0;
  const currentAccuracy = latestModel?.accuracy || 0;
  const improvement = modelComparison?.overall_improvement;

  const hasData = !!selectedDatasetId && !!modelComparison && modelComparison.models.length > 0;
  const hasImprovement = improvement && improvement.absolute !== 0;

  // Determine improvement icon
  const getImprovementIcon = () => {
    if (!improvement) return <Minus className="h-5 w-5 text-gray-400" />;
    if (improvement.absolute > 0) return <TrendingUp className="h-5 w-5 text-green-600" />;
    if (improvement.absolute < 0) return <TrendingDown className="h-5 w-5 text-red-600" />;
    return <Minus className="h-5 w-5 text-gray-400" />;
  };

  // Prepare data for ComparisonTable
  const prepareComparisonData = () => {
    if (!baselineModel || !latestModel) return undefined;

    return [
      {
        metric: 'Accuracy',
        baseline: (baselineAccuracy * 100).toFixed(1),
        current: (currentAccuracy * 100).toFixed(1),
        change: improvement?.percentage || 0,
        unit: '%'
      },
      {
        metric: 'Precision',
        baseline: baselineModel.precision ? (baselineModel.precision * 100).toFixed(1) : 'N/A',
        current: latestModel.precision ? (latestModel.precision * 100).toFixed(1) : 'N/A',
        change: baselineModel.precision && latestModel.precision 
          ? ((latestModel.precision - baselineModel.precision) / baselineModel.precision * 100)
          : undefined,
        unit: baselineModel.precision && latestModel.precision ? '%' : ''
      },
      {
        metric: 'Recall',
        baseline: baselineModel.recall ? (baselineModel.recall * 100).toFixed(1) : 'N/A',
        current: latestModel.recall ? (latestModel.recall * 100).toFixed(1) : 'N/A',
        change: baselineModel.recall && latestModel.recall
          ? ((latestModel.recall - baselineModel.recall) / baselineModel.recall * 100)
          : undefined,
        unit: baselineModel.recall && latestModel.recall ? '%' : ''
      },
      {
        metric: 'F1 Score',
        baseline: baselineModel.f1_score ? (baselineModel.f1_score * 100).toFixed(1) : 'N/A',
        current: latestModel.f1_score ? (latestModel.f1_score * 100).toFixed(1) : 'N/A',
        change: baselineModel.f1_score && latestModel.f1_score
          ? ((latestModel.f1_score - baselineModel.f1_score) / baselineModel.f1_score * 100)
          : undefined,
        unit: baselineModel.f1_score && latestModel.f1_score ? '%' : ''
      },
      {
        metric: 'Error Rate',
        baseline: ((1 - baselineAccuracy) * 100).toFixed(1),
        current: ((1 - currentAccuracy) * 100).toFixed(1),
        change: improvement ? -improvement.percentage : 0,
        unit: '%'
      },
      {
        metric: 'Samples Corrected',
        baseline: '0',
        current: latestModel.samples_corrected?.toString() || '0',
        change: latestModel.samples_corrected || 0,
        unit: ''
      },
    ];
  };

  // Prepare iteration comparison data
  const prepareIterationData = () => {
    if (!modelComparison?.models) return undefined;

    return modelComparison.models.map((model: ModelComparisonItem) => ({
      iteration: model.is_baseline ? 0 : (model.iteration_number || 1),
      accuracy: Number(((model.accuracy || 0) * 100).toFixed(1)),
      precision: Number(((model.precision || 0) * 100).toFixed(1)),
      recall: Number(((model.recall || 0) * 100).toFixed(1)),
      corrections: model.samples_corrected || 0,
    }));
  };

  const selectedDataset = datasets?.find(d => d.id === selectedDatasetId);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-3xl font-bold tracking-tight flex items-center gap-3">
            <BarChart3 className="h-8 w-8" />
            Evaluation & Analytics
          </h2>
          <p className="text-gray-500 mt-1">
            Before/after comparison with real ML metrics
          </p>
        </div>
        <div className="flex gap-2">
          <Button
            variant="outline"
            onClick={handleRefresh}
            disabled={!selectedDatasetId || comparisonLoading}
          >
            <RefreshCw className={`mr-2 h-4 w-4 ${comparisonLoading ? 'animate-spin' : ''}`} />
            Refresh
          </Button>
          <Button
            variant="outline"
            onClick={handleDownloadDataset}
            disabled={!selectedDatasetId}
          >
            <Download className="mr-2 h-4 w-4" />
            Download Dataset
          </Button>
          <Button
            onClick={handleExportReport}
            disabled={!hasData}
          >
            <Download className="mr-2 h-4 w-4" />
            Export Report
          </Button>
        </div>
      </div>

      {/* Dataset Selection */}
      <Card>
        <CardContent className="pt-6">
          <div className="flex items-center gap-4">
            <Label className="w-32">Select Dataset</Label>
            <Select
              value={selectedDatasetId?.toString() || ''}
              onValueChange={(value: string) => setSelectedDatasetId(parseInt(value))}
            >
              <SelectTrigger className="w-64">
                <SelectValue placeholder="Choose a dataset" />
              </SelectTrigger>
              <SelectContent>
                {datasets?.map((dataset) => (
                  <SelectItem key={dataset.id} value={dataset.id.toString()}>
                    {dataset.name}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            {hasImprovement && (
              <div className="flex items-center gap-2 text-sm">
                {getImprovementIcon()}
                <span className={
                  improvement!.absolute > 0 ? 'text-green-600 font-semibold' :
                  improvement!.absolute < 0 ? 'text-red-600 font-semibold' :
                  'text-gray-600'
                }>
                  {improvement!.absolute > 0 ? '+' : ''}{improvement!.percentage.toFixed(2)}% accuracy change
                </span>
              </div>
            )}
          </div>
        </CardContent>
      </Card>

      {/* Main Content */}
      {hasData ? (
        <Tabs defaultValue="overview" className="space-y-6">
          <TabsList>
            <TabsTrigger value="overview">Overview</TabsTrigger>
            <TabsTrigger value="comparison">Detailed Comparison</TabsTrigger>
            <TabsTrigger value="corrections">Corrections Applied</TabsTrigger>
          </TabsList>

          {/* Overview Tab */}
          <TabsContent value="overview" className="space-y-6">
            {/* Before/After Cards */}
            <div className="grid gap-4 md:grid-cols-2">
              {/* Baseline Model */}
              <Card className="border-2 border-gray-200">
                <CardContent className="pt-6">
                  <div className="text-center space-y-3">
                    <div className="flex items-center justify-center gap-2">
                      <AlertCircle className="h-5 w-5 text-gray-500" />
                      <div className="text-sm font-medium text-gray-600">
                        BASELINE MODEL (Before Corrections)
                      </div>
                    </div>
                    <div className="text-5xl font-bold text-gray-700">
                      {(baselineAccuracy * 100).toFixed(2)}%
                    </div>
                    <div className="text-xs text-gray-500">Test Accuracy</div>
                    
                    {baselineModel && (
                      <div className="grid grid-cols-3 gap-2 pt-4 text-sm border-t">
                        <div>
                          <div className="font-semibold text-blue-600">
                            {baselineModel.precision ? `${(baselineModel.precision * 100).toFixed(1)}%` : 'N/A'}
                          </div>
                          <div className="text-xs text-gray-500">Precision</div>
                        </div>
                        <div>
                          <div className="font-semibold text-green-600">
                            {baselineModel.recall ? `${(baselineModel.recall * 100).toFixed(1)}%` : 'N/A'}
                          </div>
                          <div className="text-xs text-gray-500">Recall</div>
                        </div>
                        <div>
                          <div className="font-semibold text-purple-600">
                            {baselineModel.f1_score ? `${(baselineModel.f1_score * 100).toFixed(1)}%` : 'N/A'}
                          </div>
                          <div className="text-xs text-gray-500">F1-Score</div>
                        </div>
                      </div>
                    )}
                  </div>
                </CardContent>
              </Card>

              {/* Latest Model */}
              <Card className="border-2 border-green-200 bg-green-50">
                <CardContent className="pt-6">
                  <div className="text-center space-y-3">
                    <div className="flex items-center justify-center gap-2">
                      <CheckCircle className="h-5 w-5 text-green-600" />
                      <div className="text-sm font-medium text-green-700">
                        CURRENT MODEL (After Corrections)
                      </div>
                    </div>
                    <div className="text-5xl font-bold text-green-700">
                      {(currentAccuracy * 100).toFixed(2)}%
                    </div>
                    <div className="text-xs text-green-600">Test Accuracy</div>
                    
                    {latestModel && (
                      <div className="grid grid-cols-3 gap-2 pt-4 text-sm border-t border-green-200">
                        <div>
                          <div className="font-semibold text-blue-600">
                            {latestModel.precision ? `${(latestModel.precision * 100).toFixed(1)}%` : 'N/A'}
                          </div>
                          <div className="text-xs text-gray-600">Precision</div>
                        </div>
                        <div>
                          <div className="font-semibold text-green-700">
                            {latestModel.recall ? `${(latestModel.recall * 100).toFixed(1)}%` : 'N/A'}
                          </div>
                          <div className="text-xs text-gray-600">Recall</div>
                        </div>
                        <div>
                          <div className="font-semibold text-purple-600">
                            {latestModel.f1_score ? `${(latestModel.f1_score * 100).toFixed(1)}%` : 'N/A'}
                          </div>
                          <div className="text-xs text-gray-600">F1-Score</div>
                        </div>
                      </div>
                    )}
                  </div>
                </CardContent>
              </Card>
            </div>

            {/* Improvement Summary */}
            {hasImprovement && (
              <Card className={
                improvement!.absolute > 0 ? 'bg-green-50 border-green-200' :
                improvement!.absolute < 0 ? 'bg-red-50 border-red-200' :
                'bg-gray-50 border-gray-200'
              }>
                <CardContent className="pt-6">
                  <div className="text-center space-y-2">
                    <div className="flex items-center justify-center gap-2">
                      {getImprovementIcon()}
                      <span className="text-2xl font-bold">
                        {improvement!.absolute > 0 ? '+' : ''}{improvement!.absolute.toFixed(4)}
                      </span>
                      <span className="text-gray-600">
                        ({improvement!.percentage > 0 ? '+' : ''}{improvement!.percentage.toFixed(2)}%)
                      </span>
                    </div>
                    <div className="text-sm text-gray-600">
                      Accuracy {improvement!.absolute >= 0 ? 'Improvement' : 'Change'}
                    </div>
                  </div>
                </CardContent>
              </Card>
            )}

            {/* Model Progress */}
            <Card>
              <CardContent className="pt-6">
                <h3 className="font-semibold mb-4">Model Evolution</h3>
                <div className="space-y-2">
                  {modelComparison.models.map((model: ModelComparisonItem, index: number) => (
                    <div
                      key={model.model_id}
                      className={`p-3 rounded-lg border ${
                        model.is_baseline ? 'bg-gray-50' : 'bg-blue-50 border-blue-200'
                      }`}
                    >
                      <div className="flex items-center justify-between">
                        <div>
                          <div className="font-medium">{model.name}</div>
                          <div className="text-xs text-gray-500">
                            {model.iteration_number && `Iteration ${model.iteration_number} • `}
                            {model.samples_corrected && `${model.samples_corrected} samples corrected`}
                          </div>
                        </div>
                        <div className="text-right">
                          <div className="text-lg font-bold">
                            {((model.accuracy || 0) * 100).toFixed(2)}%
                          </div>
                          {index > 0 && modelComparison.models[index - 1] && (
                            <div className={`text-xs ${
                              (model.accuracy || 0) > (modelComparison.models[index - 1].accuracy || 0)
                                ? 'text-green-600'
                                : (model.accuracy || 0) < (modelComparison.models[index - 1].accuracy || 0)
                                ? 'text-red-600'
                                : 'text-gray-500'
                            }`}>
                              {(model.accuracy || 0) > (modelComparison.models[index - 1].accuracy || 0) ? '+' : ''}
                              {(((model.accuracy || 0) - (modelComparison.models[index - 1].accuracy || 0)) * 100).toFixed(2)}%
                            </div>
                          )}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          {/* Detailed Comparison Tab */}
          <TabsContent value="comparison" className="space-y-4">
            <ComparisonTable 
              data={prepareComparisonData()}
              iterationComparison={prepareIterationData()}
            />
          </TabsContent>

          {/* Corrections Tab */}
          <TabsContent value="corrections">
            {correctionSummary ? (
              <div className="grid gap-4 md:grid-cols-2">
                <Card>
                  <CardContent className="pt-6">
                    <h3 className="font-semibold mb-4">Correction Statistics</h3>
                    <div className="space-y-3">
                      <div className="flex justify-between">
                        <span className="text-gray-600">Total Samples</span>
                        <span className="font-semibold">{correctionSummary.total_samples}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-gray-600">Corrected Samples</span>
                        <span className="font-semibold text-green-600">
                          {correctionSummary.corrected_samples}
                        </span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-gray-600">Labels Changed</span>
                        <span className="font-semibold text-orange-600">
                          {correctionSummary.labels_changed}
                        </span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-gray-600">Noise Reduction</span>
                        <span className="font-semibold text-blue-600">
                          {correctionSummary.noise_reduction.toFixed(2)}%
                        </span>
                      </div>
                    </div>
                  </CardContent>
                </Card>

                <Card>
                  <CardContent className="pt-6">
                    <h3 className="font-semibold mb-4">Label Distribution Changes</h3>
                    <div className="space-y-2 text-sm">
                      <div className="font-medium text-gray-600">Before:</div>
                      <div className="pl-4 space-y-1">
                        {Object.entries(correctionSummary.original_label_distribution).map(([label, count]) => (
                          <div key={`orig-${label}`} className="flex justify-between">
                            <span>Label {label}</span>
                            <span className="font-mono">{count as number}</span>
                          </div>
                        ))}
                      </div>
                      <div className="font-medium text-gray-600 pt-2">After:</div>
                      <div className="pl-4 space-y-1">
                        {Object.entries(correctionSummary.current_label_distribution).map(([label, count]) => (
                          <div key={`curr-${label}`} className="flex justify-between">
                            <span>Label {label}</span>
                            <span className="font-mono font-semibold">{count as number}</span>
                          </div>
                        ))}
                      </div>
                    </div>
                  </CardContent>
                </Card>
              </div>
            ) : (
              <Card>
                <CardContent className="py-12 text-center text-gray-500">
                  No correction data available
                </CardContent>
              </Card>
            )}
          </TabsContent>
        </Tabs>
      ) : (
        <Card>
          <CardContent className="flex flex-col items-center justify-center py-16">
            <FileText className="h-16 w-16 text-gray-400 mb-4" />
            <h3 className="text-lg font-semibold mb-2">
              {selectedDatasetId ? (comparisonLoading ? 'Loading...' : 'No Models Found') : 'Select a Dataset'}
            </h3>
            <p className="text-sm text-gray-500 text-center max-w-sm">
              {selectedDatasetId 
                ? 'Run detection and retrain the model to see evaluation metrics.'
                : 'Choose a dataset from the dropdown above to view performance analytics.'
              }
            </p>
          </CardContent>
        </Card>
      )}

      {/* Info Card */}
      {selectedDataset && (
        <Card className="bg-gradient-to-r from-blue-50 to-purple-50 border-blue-200">
          <CardContent className="pt-6">
            <div className="flex items-start gap-3">
              <div className="bg-blue-100 p-2 rounded-lg">
                <BarChart3 className="h-5 w-5 text-blue-600" />
              </div>
              <div className="flex-1">
                <h4 className="font-semibold text-blue-900 mb-1">
                  Dataset: {selectedDataset.name}
                </h4>
                <p className="text-sm text-blue-800">
                  All metrics shown are calculated from real ML model evaluations. 
                  The baseline model is trained on the noisy dataset, and retrained models 
                  are trained on corrected data. Improvements reflect actual label corrections.
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}