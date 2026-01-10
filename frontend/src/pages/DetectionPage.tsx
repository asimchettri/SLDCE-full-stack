import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { detectionAPI, datasetAPI } from "@/services/api";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import {
  Play,
  RefreshCw,
  AlertCircle,
  Target,
  TrendingUp,
  Sparkles,
  Filter,
  ArrowUpDown,
  Waves,
} from "lucide-react";
import { SuspiciousSampleCard } from "@/components/SuspiciousSampleCard";
import { DetectionTable } from "@/components/DetectionTable";
import { MetricsDashboard } from "@/components/MetricsDashboard";
import { PriorityWeightsControl } from "@/components/PriorityWeightsControl";
import { SignalFilters } from "@/components/SignalFilters";
import { SignalRadarChart } from "@/components/SignalRadarChart";
import { useRealTimeMetrics } from "@/hooks/useRealTimeMetrics";
import { RealTimeIndicator } from "@/components/RealTimeIndicator";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import type { PriorityWeights, SignalType } from "@/types/detection";
import { useNavigate } from 'react-router-dom';
import { CheckSquare } from 'lucide-react';


export function DetectionPage() {
  const [selectedDatasetId, setSelectedDatasetId] = useState<number | undefined>();
  const [confidenceThreshold, setConfidenceThreshold] = useState(0.7);
  const [viewMode, setViewMode] = useState<"cards" | "table">("cards");

  const navigate = useNavigate();

  // NEW: Priority weights state
  const [priorityWeights, setPriorityWeights] = useState<PriorityWeights>({
    confidence: 0.6,
    anomaly: 0.4,
  });

  // Filtering & Sorting
  const [minPriority, setMinPriority] = useState<number | undefined>();
  const [sortBy, setSortBy] = useState<"priority" | "confidence" | "anomaly">("priority");
  const [sortOrder, setSortOrder] = useState<"desc" | "asc">("desc");

  // NEW: Signal-specific filters
  const [minConfidence, setMinConfidence] = useState<number | undefined>();
  const [minAnomaly, setMinAnomaly] = useState<number | undefined>();
  const [signalType, setSignalType] = useState<SignalType>("all");

  // Pagination
  const [page, setPage] = useState(1);
  const [pageSize] = useState(12);

  const queryClient = useQueryClient();

  // Fetch datasets
  const { data: datasets } = useQuery({
    queryKey: ["datasets"],
    queryFn: datasetAPI.getAll,
  });

  // Fetch detections with signal filters
  const {
    data: detections,
    isLoading: detectionsLoading,
    refetch: refetchDetections,
  } = useQuery({
    queryKey: [
      "detections",
      selectedDatasetId,
      minPriority,
      minConfidence,
      minAnomaly,
      signalType,
      page,
      pageSize,
    ],
    queryFn: () =>
      detectionAPI.getAll({
        dataset_id: selectedDatasetId,
        min_priority: minPriority,
        min_confidence: minConfidence,
        min_anomaly: minAnomaly,
        signal_type: signalType === "all" ? undefined : signalType,
        limit: pageSize,
        offset: (page - 1) * pageSize,
      }),
    enabled: !!selectedDatasetId,
  });

  // Fetch stats
  const { data: stats } = useQuery({
    queryKey: ["detection-stats", selectedDatasetId],
    queryFn: () => detectionAPI.getStats(selectedDatasetId!),
    enabled: !!selectedDatasetId,
  });

  // NEW: Fetch signal stats
  const { data: signalStats } = useQuery({
    queryKey: ["signal-stats", selectedDatasetId],
    queryFn: () => detectionAPI.getSignalStats(selectedDatasetId!),
    enabled: !!selectedDatasetId,
  });

  // Run detection mutation with priority weights
  const runDetectionMutation = useMutation({
    mutationFn: (datasetId: number) =>
      detectionAPI.run({
        dataset_id: datasetId,
        confidence_threshold: confidenceThreshold,
        priority_weights: priorityWeights,
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["detections"] });
      queryClient.invalidateQueries({ queryKey: ["detection-stats"] });
      queryClient.invalidateQueries({ queryKey: ["signal-stats"] });
      setPage(1);
      refetchDetections();
    },
  });

  // Generate suggestions mutation
  const generateSuggestionsMutation = useMutation({
    mutationFn: (datasetId: number) =>
      detectionAPI.generateSuggestions(datasetId, 1),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["detections"] });
    },
  });

  const handleRunDetection = () => {
    if (selectedDatasetId) {
      runDetectionMutation.mutate(selectedDatasetId);
    }
  };

  const handleGenerateSuggestions = () => {
    if (selectedDatasetId) {
      generateSuggestionsMutation.mutate(selectedDatasetId);
    }
  };

  const handleResetWeights = () => {
    setPriorityWeights({ confidence: 0.6, anomaly: 0.4 });
  };

  // Enable real-time metrics updates
  useRealTimeMetrics(selectedDatasetId, true);

  // Sort detections client-side
  const sortedDetections = detections
    ? [...detections].sort((a, b) => {
        let compareValue = 0;
        switch (sortBy) {
          case "priority":
            compareValue = a.priority_score - b.priority_score;
            break;
          case "confidence":
            compareValue = a.confidence_score - b.confidence_score;
            break;
          case "anomaly":
            compareValue = a.anomaly_score - b.anomaly_score;
            break;
        }
        return sortOrder === "desc" ? -compareValue : compareValue;
      })
    : [];

  const totalPages = stats ? Math.ceil(stats.suspicious_samples / pageSize) : 1;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <div className="flex items-center gap-3">
            <h2 className="text-3xl font-bold tracking-tight">Detection</h2>
            {selectedDatasetId && <RealTimeIndicator />}
          </div>
          <p className="text-gray-500 mt-1">
            Identify potentially mislabeled samples using multi-signal analysis
          </p>
        </div>
        <Button
          variant="outline"
          onClick={() => refetchDetections()}
          disabled={!selectedDatasetId}
        >
          <RefreshCw className="mr-2 h-4 w-4" />
          Refresh
        </Button>
      </div>

      {/* Configuration Card */}
      <Card>
        <CardHeader>
          <CardTitle>Detection Configuration</CardTitle>
          <CardDescription>
            Select a dataset and configure detection parameters
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {/* Dataset Selection */}
            <div className="space-y-2">
              <Label>Dataset</Label>
              <Select
                value={selectedDatasetId?.toString() || ""}
                onValueChange={(value: string) => {
                  setSelectedDatasetId(parseInt(value));
                  setPage(1);
                }}
              >
                <SelectTrigger>
                  <SelectValue placeholder="Select dataset" />
                </SelectTrigger>
                <SelectContent>
                  {datasets?.map((dataset) => (
                    <SelectItem key={dataset.id} value={dataset.id.toString()}>
                      {dataset.name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            {/* Confidence Threshold */}
            <div className="space-y-2">
              <Label>
                Confidence Threshold: {confidenceThreshold.toFixed(2)}
              </Label>
              <Input
                type="range"
                min="0"
                max="1"
                step="0.05"
                value={confidenceThreshold}
                onChange={(e) =>
                  setConfidenceThreshold(parseFloat(e.target.value))
                }
              />
            </div>

            {/* Action Buttons */}
            <div className="space-y-2">
              <Label>Actions</Label>
              <div className="flex gap-2">
                <Button
                  onClick={handleRunDetection}
                  disabled={
                    !selectedDatasetId || runDetectionMutation.isPending
                  }
                  className="flex-1"
                >
                  {runDetectionMutation.isPending ? (
                    <>
                      <RefreshCw className="mr-2 h-4 w-4 animate-spin" />
                      Running...
                    </>
                  ) : (
                    <>
                      <Play className="mr-2 h-4 w-4" />
                      Run Detection
                    </>
                  )}
                </Button>
              </div>
            </div>
          </div>

          {/* Generate Suggestions & Review Button */}
{detections && detections.length > 0 && (
  <div className="pt-4 border-t">
    <div className="flex gap-3">
      <Button
        onClick={handleGenerateSuggestions}
        disabled={generateSuggestionsMutation.isPending}
        variant="secondary"
        className="flex-1"
      >
        {generateSuggestionsMutation.isPending ? (
          <>
            <RefreshCw className="mr-2 h-4 w-4 animate-spin" />
            Generating...
          </>
        ) : (
          <>
            <Sparkles className="mr-2 h-4 w-4" />
            Generate Suggestions
          </>
        )}
      </Button>
      
      <Button
        onClick={() => navigate('/correction')}
        variant="default"
        className="flex-1"
      >
        <CheckSquare className="mr-2 h-4 w-4" />
        Review Suggestions
      </Button>
    </div>
  </div>
)}

          {/* Success Messages */}
          {runDetectionMutation.isSuccess && runDetectionMutation.data && (
            <div className="p-3 bg-green-50 border border-green-200 rounded text-sm text-green-800">
              ✓ Detection complete! Found{" "}
              {runDetectionMutation.data.suspicious_samples_found} suspicious
              samples ({runDetectionMutation.data.detection_rate.toFixed(1)}%
              detection rate)
            </div>
          )}

          {generateSuggestionsMutation.isSuccess &&
            generateSuggestionsMutation.data && (
              <div className="p-3 bg-blue-50 border border-blue-200 rounded text-sm text-blue-800">
                ✓ Generated{" "}
                {generateSuggestionsMutation.data.suggestions_created}{" "}
                correction suggestions
              </div>
            )}
        </CardContent>
      </Card>

      {/* NEW: Priority Weights Control */}
      {selectedDatasetId && (
        <PriorityWeightsControl
          weights={priorityWeights}
          onChange={setPriorityWeights}
          onReset={handleResetWeights}
        />
      )}

      {/* Statistics Cards */}
      {stats && (
        <div className="grid gap-4 md:grid-cols-4">
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium text-gray-600 flex items-center gap-2">
                <Target className="h-4 w-4" />
                Total Samples
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{stats.total_samples}</div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium text-gray-600 flex items-center gap-2">
                <AlertCircle className="h-4 w-4" />
                Suspicious
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-orange-600">
                {stats.suspicious_samples}
              </div>
              <p className="text-xs text-gray-500">
                {stats.detection_rate.toFixed(1)}% of total
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium text-gray-600 flex items-center gap-2">
                <TrendingUp className="h-4 w-4" />
                High Priority
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-red-600">
                {stats.high_priority_detections}
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium text-gray-600">
                Avg Confidence
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-blue-600">
                {(stats.average_confidence * 100).toFixed(1)}%
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {/* NEW: Signal Stats Cards */}
      {signalStats && signalStats.total_detections > 0 && (
        <div className="grid gap-4 md:grid-cols-3">
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium text-gray-600 flex items-center gap-2">
                <Waves className="h-4 w-4 text-blue-600" />
                Confidence Dominant
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-blue-600">
                {signalStats.confidence_dominant}
              </div>
              <p className="text-xs text-gray-500">
                {((signalStats.confidence_dominant / signalStats.total_detections) * 100).toFixed(1)}% of detections
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium text-gray-600 flex items-center gap-2">
                <Waves className="h-4 w-4 text-purple-600" />
                Anomaly Dominant
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-purple-600">
                {signalStats.anomaly_dominant}
              </div>
              <p className="text-xs text-gray-500">
                {((signalStats.anomaly_dominant / signalStats.total_detections) * 100).toFixed(1)}% of detections
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium text-gray-600 flex items-center gap-2">
                <TrendingUp className="h-4 w-4 text-green-600" />
                Both High (≥0.7)
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-green-600">
                {signalStats.both_high}
              </div>
              <p className="text-xs text-gray-500">
                {((signalStats.both_high / signalStats.total_detections) * 100).toFixed(1)}% of detections
              </p>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Tabs: Detections, Metrics, & Signal Analysis */}
      {selectedDatasetId && stats && (
        <Tabs defaultValue="detections" className="space-y-4">
          <TabsList>
            <TabsTrigger value="detections">Detections</TabsTrigger>
            <TabsTrigger value="metrics">Metrics Dashboard</TabsTrigger>
            <TabsTrigger value="signals">Signal Analysis</TabsTrigger>
          </TabsList>

          {/* Detections Tab */}
          <TabsContent value="detections" className="space-y-4">
            {/* Filters & Sorting */}
            {detections && detections.length > 0 && (
              <>
                {/* Existing Filters Card */}
                <Card>
                  <CardHeader>
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <Filter className="h-5 w-5" />
                        <CardTitle>Filters & Display Options</CardTitle>
                      </div>
                      <Tabs
                        value={viewMode}
                        onValueChange={(v) => setViewMode(v as "cards" | "table")}
                      >
                        <TabsList>
                          <TabsTrigger value="cards">Cards</TabsTrigger>
                          <TabsTrigger value="table">Table</TabsTrigger>
                        </TabsList>
                      </Tabs>
                    </div>
                  </CardHeader>
                  <CardContent className="space-y-6">
                    {/* Priority and Sort Filters */}
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                      {/* Min Priority Filter */}
                      <div className="space-y-2">
                        <Label>Minimum Priority</Label>
                        <Select
                          value={minPriority?.toString() || "all"}
                          onValueChange={(value: string) => {
                            setMinPriority(
                              value === "all" ? undefined : parseFloat(value)
                            );
                            setPage(1);
                          }}
                        >
                          <SelectTrigger>
                            <SelectValue placeholder="All priorities" />
                          </SelectTrigger>
                          <SelectContent>
                            <SelectItem value="all">All Priorities</SelectItem>
                            <SelectItem value="0.8">High (≥ 0.8)</SelectItem>
                            <SelectItem value="0.6">Medium (≥ 0.6)</SelectItem>
                            <SelectItem value="0.4">Low (≥ 0.4)</SelectItem>
                          </SelectContent>
                        </Select>
                      </div>

                      {/* Sort By */}
                      <div className="space-y-2">
                        <Label>Sort By</Label>
                        <Select
                          value={sortBy}
                          onValueChange={(value: string) =>
                            setSortBy(value as any)
                          }
                        >
                          <SelectTrigger>
                            <SelectValue />
                          </SelectTrigger>
                          <SelectContent>
                            <SelectItem value="priority">
                              Priority Score
                            </SelectItem>
                            <SelectItem value="confidence">Confidence</SelectItem>
                            <SelectItem value="anomaly">Anomaly Score</SelectItem>
                          </SelectContent>
                        </Select>
                      </div>

                      {/* Sort Order */}
                      <div className="space-y-2">
                        <Label>Sort Order</Label>
                        <Button
                          variant="outline"
                          onClick={() =>
                            setSortOrder(sortOrder === "desc" ? "asc" : "desc")
                          }
                          className="w-full justify-start"
                        >
                          <ArrowUpDown className="mr-2 h-4 w-4" />
                          {sortOrder === "desc"
                            ? "Highest First"
                            : "Lowest First"}
                        </Button>
                      </div>
                    </div>

                    {/* NEW: Signal Filters */}
                    <div className="pt-4 border-t">
                      <h4 className="text-sm font-semibold mb-4 flex items-center gap-2">
                        <Waves className="h-4 w-4" />
                        Signal-Specific Filters
                      </h4>
                      <SignalFilters
                        minConfidence={minConfidence}
                        minAnomaly={minAnomaly}
                        signalType={signalType}
                        onMinConfidenceChange={(value) => {
                          setMinConfidence(value);
                          setPage(1);
                        }}
                        onMinAnomalyChange={(value) => {
                          setMinAnomaly(value);
                          setPage(1);
                        }}
                        onSignalTypeChange={(value) => {
                          setSignalType(value);
                          setPage(1);
                        }}
                      />
                    </div>
                  </CardContent>
                </Card>
              </>
            )}

            {/* Detections Display */}
            <div>
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-semibold">
                  Suspicious Samples{" "}
                  {sortedDetections && `(${sortedDetections.length})`}
                </h3>
                {totalPages > 1 && (
                  <div className="flex items-center gap-2">
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => setPage((p) => Math.max(1, p - 1))}
                      disabled={page === 1}
                    >
                      Previous
                    </Button>
                    <span className="text-sm text-gray-600">
                      Page {page} of {totalPages}
                    </span>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() =>
                        setPage((p) => Math.min(totalPages, p + 1))
                      }
                      disabled={page === totalPages}
                    >
                      Next
                    </Button>
                  </div>
                )}
              </div>

              {detectionsLoading ? (
                <div className="flex items-center justify-center py-12">
                  <RefreshCw className="h-8 w-8 animate-spin text-gray-400" />
                </div>
              ) : sortedDetections && sortedDetections.length > 0 ? (
                <>
                  {viewMode === "cards" ? (
                    <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
                      {sortedDetections.map((detection) => (
                        <SuspiciousSampleCard
                          key={detection.id}
                          detection={detection}
                        />
                      ))}
                    </div>
                  ) : (
                    <DetectionTable detections={sortedDetections} />
                  )}
                </>
              ) : (
                <Card>
                  <CardContent className="flex flex-col items-center justify-center py-12">
                    <Target className="h-12 w-12 text-gray-400 mb-4" />
                    <h3 className="text-lg font-semibold mb-2">
                      No detections yet
                    </h3>
                    <p className="text-sm text-gray-500 text-center max-w-sm mb-4">
                      Run detection on this dataset to identify potentially
                      mislabeled samples
                    </p>
                    <Button
                      onClick={handleRunDetection}
                      disabled={runDetectionMutation.isPending}
                    >
                      <Play className="mr-2 h-4 w-4" />
                      Run Detection Now
                    </Button>
                  </CardContent>
                </Card>
              )}
            </div>
          </TabsContent>

          {/* Metrics Dashboard Tab */}
          <TabsContent value="metrics">
            <MetricsDashboard
              stats={stats}
              datasetName={
                datasets?.find((d) => d.id === selectedDatasetId)?.name ||
                "Unknown Dataset"
              }
              detections={sortedDetections}
            />
          </TabsContent>

          {/* NEW: Signal Analysis Tab */}
          <TabsContent value="signals" className="space-y-4">
            <SignalRadarChart
              detections={sortedDetections}
              title="Multi-Signal Distribution Analysis"
            />

            {signalStats && (
              <Card>
                <CardHeader>
                  <CardTitle>Signal Statistics Summary</CardTitle>
                  <CardDescription>
                    Breakdown of signal dominance across {signalStats.total_detections} detections
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                    <div className="text-center p-4 bg-blue-50 rounded-lg">
                      <div className="text-xs text-gray-600 mb-1">Avg Confidence</div>
                      <div className="text-2xl font-bold text-blue-600">
                        {(signalStats.avg_confidence * 100).toFixed(1)}%
                      </div>
                    </div>
                    <div className="text-center p-4 bg-purple-50 rounded-lg">
                      <div className="text-xs text-gray-600 mb-1">Avg Anomaly</div>
                      <div className="text-2xl font-bold text-purple-600">
                        {(signalStats.avg_anomaly * 100).toFixed(1)}%
                      </div>
                    </div>
                    <div className="text-center p-4 bg-green-50 rounded-lg">
                      <div className="text-xs text-gray-600 mb-1">Confidence Dom.</div>
                      <div className="text-2xl font-bold text-green-600">
                        {((signalStats.confidence_dominant / signalStats.total_detections) * 100).toFixed(0)}%
                      </div>
                    </div>
                    <div className="text-center p-4 bg-orange-50 rounded-lg">
                      <div className="text-xs text-gray-600 mb-1">Anomaly Dom.</div>
                      <div className="text-2xl font-bold text-orange-600">
                        {((signalStats.anomaly_dominant / signalStats.total_detections) * 100).toFixed(0)}%
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>
            )}
          </TabsContent>
        </Tabs>
      )}

      {/* No Dataset Selected */}
      {!selectedDatasetId && (
        <Card>
          <CardContent className="flex flex-col items-center justify-center py-16">
            <AlertCircle className="h-16 w-16 text-gray-400 mb-4" />
            <h3 className="text-lg font-semibold mb-2">Select a Dataset</h3>
            <p className="text-sm text-gray-500 text-center max-w-sm">
              Choose a dataset from the dropdown above to start detecting
              mislabeled samples with multi-signal analysis
            </p>
          </CardContent>
        </Card>
      )}
    </div>
  );
}