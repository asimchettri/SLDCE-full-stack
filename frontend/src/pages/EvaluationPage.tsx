import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { datasetAPI, feedbackAPI, suggestionAPI, detectionAPI } from '@/services/api';
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
  TrendingUp
} from 'lucide-react';
import { MetricsOverview } from '@/components/MetricsOverview';
import { PerformanceCharts } from '@/components/PerformanceCharts';
import { ComparisonTable } from '@/components/ComparisonTable';

export function EvaluationPage() {
  const [selectedDatasetId, setSelectedDatasetId] = useState<number | undefined>();

  // Fetch datasets
  const { data: datasets } = useQuery({
    queryKey: ['datasets'],
    queryFn: datasetAPI.getAll,
  });

  // Fetch detection stats
  const { data: detectionStats, refetch: refetchDetection } = useQuery({
    queryKey: ['detection-stats', selectedDatasetId],
    queryFn: () => detectionAPI.getStats(selectedDatasetId!),
    enabled: !!selectedDatasetId,
  });

  // Fetch suggestion stats
  const { data: suggestionStats, refetch: refetchSuggestions } = useQuery({
    queryKey: ['suggestion-stats', selectedDatasetId],
    queryFn: () => suggestionAPI.getStats(selectedDatasetId!),
    enabled: !!selectedDatasetId,
  });

  // Fetch feedback stats
  const { data: feedbackStats, refetch: refetchFeedback } = useQuery({
    queryKey: ['feedback-stats', selectedDatasetId],
    queryFn: () => feedbackAPI.getStats(selectedDatasetId!),
    enabled: !!selectedDatasetId,
  });

  // Fetch feedback patterns
  const { data: feedbackPatterns } = useQuery({
    queryKey: ['feedback-patterns', selectedDatasetId],
    queryFn: () => feedbackAPI.getPatterns(selectedDatasetId!, 1),
    enabled: !!selectedDatasetId,
  });

  const handleRefresh = () => {
    refetchDetection();
    refetchSuggestions();
    refetchFeedback();
  };

  const handleExportReport = () => {
    window.print();
  };

  // Calculate metrics from real data
  const totalSamples = detectionStats?.total_samples || 150;
  const suspiciousSamples = detectionStats?.suspicious_samples || 0;
  const correctedSamples = (suggestionStats?.accepted || 0) + (suggestionStats?.modified || 0);
  const acceptanceRate = suggestionStats?.acceptance_rate || 0;
  const detectionPrecision = detectionStats?.average_confidence 
    ? detectionStats.average_confidence * 100 
    : 0;

  // Simulated improvement (Phase 2 will have real ML metrics)
  const baselineAccuracy = 78;
  const accuracyImprovement = correctedSamples > 0 
    ? Math.min(15, Math.round((correctedSamples / suspiciousSamples) * 15))
    : 0;
  const currentAccuracy = baselineAccuracy + accuracyImprovement;

  // Prepare feedback distribution for pie chart
  const feedbackDistribution = feedbackStats ? {
    accepted: feedbackStats.accept_count,
    rejected: feedbackStats.reject_count,
    modified: feedbackStats.modify_count,
  } : undefined;

  // Prepare signal data for radar chart
  const signalData = feedbackPatterns ? [
    { subject: 'High Confidence', value: feedbackPatterns.high_confidence_acceptance_rate },
    { subject: 'Low Confidence', value: feedbackPatterns.low_confidence_acceptance_rate },
    { subject: 'Acceptance Rate', value: acceptanceRate },
    { subject: 'Detection Rate', value: detectionStats?.detection_rate || 0 },
    { subject: 'Avg Confidence', value: detectionPrecision },
  ] : undefined;

  const hasData = !!selectedDatasetId && !!detectionStats;

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
            Comprehensive performance analysis and metrics dashboard
          </p>
        </div>
        <div className="flex gap-2">
          <Button
            variant="outline"
            onClick={handleRefresh}
            disabled={!selectedDatasetId}
          >
            <RefreshCw className="mr-2 h-4 w-4" />
            Refresh
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
            {hasData && (
              <div className="flex items-center gap-2 text-sm text-gray-600">
                <TrendingUp className="h-4 w-4 text-green-600" />
                <span>
                  {correctedSamples} samples corrected, 
                  +{accuracyImprovement}% improvement
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
            <TabsTrigger value="charts">Performance Charts</TabsTrigger>
            <TabsTrigger value="comparison">Detailed Comparison</TabsTrigger>
          </TabsList>

          {/* Overview Tab */}
          <TabsContent value="overview" className="space-y-6">
            <MetricsOverview
              totalSamples={totalSamples}
              suspiciousSamples={suspiciousSamples}
              correctedSamples={correctedSamples}
              accuracyImprovement={accuracyImprovement}
              acceptanceRate={acceptanceRate}
              detectionPrecision={detectionPrecision}
              currentAccuracy={currentAccuracy}
              baselineAccuracy={baselineAccuracy}
            />

            {/* Quick Stats */}
            <Card>
              <CardContent className="pt-6">
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-center">
                  <div>
                    <div className="text-2xl font-bold text-blue-600">
                      {detectionStats.detection_rate.toFixed(1)}%
                    </div>
                    <div className="text-xs text-gray-600">Detection Rate</div>
                  </div>
                  <div>
                    <div className="text-2xl font-bold text-green-600">
                      {suggestionStats?.pending || 0}
                    </div>
                    <div className="text-xs text-gray-600">Pending Reviews</div>
                  </div>
                  <div>
                    <div className="text-2xl font-bold text-purple-600">
                      {feedbackStats?.total_feedback || 0}
                    </div>
                    <div className="text-xs text-gray-600">Total Feedback</div>
                  </div>
                  <div>
                    <div className="text-2xl font-bold text-orange-600">
                      {detectionStats.high_priority_detections}
                    </div>
                    <div className="text-xs text-gray-600">High Priority</div>
                  </div>
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          {/* Charts Tab */}
          <TabsContent value="charts">
            <PerformanceCharts
              feedbackDistribution={feedbackDistribution}
              signalData={signalData}
            />
          </TabsContent>

          {/* Comparison Tab */}
          <TabsContent value="comparison">
            <ComparisonTable />
          </TabsContent>
        </Tabs>
      ) : (
        <Card>
          <CardContent className="flex flex-col items-center justify-center py-16">
            <FileText className="h-16 w-16 text-gray-400 mb-4" />
            <h3 className="text-lg font-semibold mb-2">
              {selectedDatasetId ? 'No Data Available' : 'Select a Dataset'}
            </h3>
            <p className="text-sm text-gray-500 text-center max-w-sm">
              {selectedDatasetId 
                ? 'Run detection and review suggestions to generate evaluation metrics.'
                : 'Choose a dataset from the dropdown above to view performance analytics and evaluation metrics.'
              }
            </p>
          </CardContent>
        </Card>
      )}

      {/* Phase 2 Notice */}
      <Card className="bg-gradient-to-r from-blue-50 to-purple-50 border-blue-200">
        <CardContent className="pt-6">
          <div className="flex items-start gap-3">
            <div className="bg-blue-100 p-2 rounded-lg">
              <BarChart3 className="h-5 w-5 text-blue-600" />
            </div>
            <div className="flex-1">
              <h4 className="font-semibold text-blue-900 mb-1">
                Phase 1: Simulated Metrics
              </h4>
              <p className="text-sm text-blue-800">
                Current accuracy improvements are simulated based on correction count. 
                <strong> Phase 2</strong> will integrate actual ML model training and evaluation 
                to provide real accuracy, precision, recall, and F1-score metrics across iterations.
              </p>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}