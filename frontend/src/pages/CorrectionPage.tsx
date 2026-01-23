import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { suggestionAPI, datasetAPI } from '@/services/api';
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
import {
  CheckCircle,
  RefreshCw,
  Lightbulb,
  Filter,
  ChevronLeft,
  ChevronRight,
} from 'lucide-react';
import { SuggestionCard } from '@/components/SuggestionCard';
import { SuggestionStats } from '@/components/SuggestionStats';
import { FeedbackAnalytics } from '@/components/FeedbackAnalytics';
import { ApplyCorrectionsButton } from '@/components/ui/ApplyCorrectionsButton'; 
import { RetrainButton } from '@/components/ui/RetrainButton'; 
import type { SuggestionStatus } from '@/types/suggestion';

export function CorrectionPage() {
  const [selectedDatasetId, setSelectedDatasetId] = useState<number | undefined>();
  const [statusFilter, setStatusFilter] = useState<SuggestionStatus | 'all'>('pending');
  const [minConfidence, setMinConfidence] = useState<number | undefined>();
  const [page, setPage] = useState(1);
  const pageSize = 12;

  // Fetch datasets
  const { data: datasets } = useQuery({
    queryKey: ['datasets'],
    queryFn: datasetAPI.getAll,
  });

  // Fetch suggestions
  const {
    data: suggestionsResponse,
    isLoading: suggestionsLoading,
    refetch: refetchSuggestions,
  } = useQuery({
    queryKey: [
      'suggestions',
      selectedDatasetId,
      statusFilter,
      minConfidence,
      page,
      pageSize,
    ],
    queryFn: () =>
      suggestionAPI.getAll({
        dataset_id: selectedDatasetId,
        status: statusFilter === 'all' ? undefined : statusFilter,
        min_confidence: minConfidence,
        page,
        page_size: pageSize,
      }),
    enabled: !!selectedDatasetId,
  });

  // Fetch stats 
  const { data: stats, refetch: refetchStats } = useQuery({
    queryKey: ['suggestion-stats', selectedDatasetId],
    queryFn: () => suggestionAPI.getStats(selectedDatasetId!),
    enabled: !!selectedDatasetId,
  });

  // Also refresh stats when status updates
  const handleStatusUpdate = () => {
    refetchSuggestions();
    refetchStats();
  };

  const totalPages = suggestionsResponse?.total_pages || 1;
  const suggestions = suggestionsResponse?.suggestions || [];

  //  Check if there are accepted/modified suggestions
  const hasAcceptedSuggestions = stats && (stats.accepted + stats.modified) > 0;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <div className="flex items-center gap-3">
            <h2 className="text-3xl font-bold tracking-tight">Correction & Review</h2>
          </div>
          <p className="text-gray-500 mt-1">
            Review and approve correction suggestions from the detection system
          </p>
        </div>
        <div className="flex gap-2">
          <Button
            variant="outline"
            onClick={() => refetchSuggestions()}
            disabled={!selectedDatasetId}
          >
            <RefreshCw className="mr-2 h-4 w-4" />
            Refresh
          </Button>
        </div>
      </div>

      {/*  Action Buttons Section */}
      {selectedDatasetId && hasAcceptedSuggestions && (
        <Card className="border-blue-200 bg-blue-50">
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="font-semibold text-blue-900 mb-1">
                  Ready to Apply Corrections
                </h3>
                <p className="text-sm text-blue-700">
                  You have {stats.accepted + stats.modified} accepted/modified suggestions ready to apply
                </p>
              </div>
              <div className="flex gap-2">
                <ApplyCorrectionsButton
                  datasetId={selectedDatasetId}
                  iteration={1}
                  onSuccess={() => {
                    refetchSuggestions();
                    refetchStats();
                  }}
                />
                <RetrainButton
                  datasetId={selectedDatasetId}
                  iteration={1}
                  onSuccess={() => {
                    // Optionally refresh data
                  }}
                />
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Configuration */}
      <Card>
        <CardContent className="pt-6">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            {/* Dataset Selection */}
            <div className="space-y-2">
              <Label>Dataset</Label>
              <Select
                value={selectedDatasetId?.toString() || ''}
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

            {/* Status Filter */}
            <div className="space-y-2">
              <Label>Status</Label>
              <Select
                value={statusFilter}
                onValueChange={(value: string) => {
                  setStatusFilter(value as SuggestionStatus | 'all');
                  setPage(1);
                }}
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Statuses</SelectItem>
                  <SelectItem value="pending">Pending</SelectItem>
                  <SelectItem value="accepted">Accepted</SelectItem>
                  <SelectItem value="rejected">Rejected</SelectItem>
                  <SelectItem value="modified">Modified</SelectItem>
                </SelectContent>
              </Select>
            </div>

            {/* Confidence Filter */}
            <div className="space-y-2">
              <Label>Min Confidence</Label>
              <Select
                value={minConfidence?.toString() || 'all'}
                onValueChange={(value: string) => {
                  setMinConfidence(value === 'all' ? undefined : parseFloat(value));
                  setPage(1);
                }}
              >
                <SelectTrigger>
                  <SelectValue placeholder="All" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Confidence</SelectItem>
                  <SelectItem value="0.9">Very High (≥90%)</SelectItem>
                  <SelectItem value="0.8">High (≥80%)</SelectItem>
                  <SelectItem value="0.7">Medium (≥70%)</SelectItem>
                  <SelectItem value="0.6">Low (≥60%)</SelectItem>
                </SelectContent>
              </Select>
            </div>

            {/* Quick Stats */}
            <div className="space-y-2">
              <Label>Quick Info</Label>
              <div className="flex items-center gap-2 h-10 px-3 rounded-md border bg-gray-50">
                <Filter className="h-4 w-4 text-gray-500" />
                <span className="text-sm text-gray-700">
                  {suggestions.length} of {suggestionsResponse?.total || 0}
                </span>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Statistics */}
      {stats && selectedDatasetId && (
        <SuggestionStats stats={stats} />
      )}

      {/* Feedback Analytics - Learning Data for Phase 2 */}
      {selectedDatasetId && (
        <FeedbackAnalytics datasetId={selectedDatasetId} iteration={1} />
      )}

      {/* Suggestions Grid */}
      {selectedDatasetId ? (
        <>
          {suggestionsLoading ? (
            <div className="flex items-center justify-center py-12">
              <RefreshCw className="h-8 w-8 animate-spin text-gray-400" />
            </div>
          ) : suggestions.length > 0 ? (
            <>
              <div className="flex items-center justify-between">
                <h3 className="text-lg font-semibold">
                  Suggestions ({suggestionsResponse?.total || 0})
                </h3>
                {totalPages > 1 && (
                  <div className="flex items-center gap-2">
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => setPage((p) => Math.max(1, p - 1))}
                      disabled={page === 1}
                    >
                      <ChevronLeft className="h-4 w-4" />
                      Previous
                    </Button>
                    <span className="text-sm text-gray-600 px-2">
                      Page {page} of {totalPages}
                    </span>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                      disabled={page === totalPages}
                    >
                      Next
                      <ChevronRight className="h-4 w-4 ml-1" />
                    </Button>
                  </div>
                )}
              </div>

              <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
                {suggestions.map((suggestion) => (
                  <SuggestionCard
                    key={suggestion.id}
                    suggestion={suggestion}
                    onStatusUpdate={handleStatusUpdate}
                  />
                ))}
              </div>

              {/* Bottom Pagination */}
              {totalPages > 1 && (
                <div className="flex justify-center">
                  <div className="flex items-center gap-2">
                    <Button
                      variant="outline"
                      onClick={() => setPage((p) => Math.max(1, p - 1))}
                      disabled={page === 1}
                    >
                      <ChevronLeft className="h-4 w-4 mr-1" />
                      Previous
                    </Button>
                    <span className="text-sm text-gray-600 px-4">
                      Page {page} of {totalPages}
                    </span>
                    <Button
                      variant="outline"
                      onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                      disabled={page === totalPages}
                    >
                      Next
                      <ChevronRight className="h-4 w-4 ml-1" />
                    </Button>
                  </div>
                </div>
              )}
            </>
          ) : (
            <Card>
              <CardContent className="flex flex-col items-center justify-center py-12">
                <CheckCircle className="h-12 w-12 text-green-400 mb-4" />
                <h3 className="text-lg font-semibold mb-2">
                  {statusFilter === 'pending'
                    ? 'All caught up!'
                    : 'No suggestions found'}
                </h3>
                <p className="text-sm text-gray-500 text-center max-w-sm">
                  {statusFilter === 'pending'
                    ? 'There are no pending suggestions to review. Run detection to generate new suggestions.'
                    : 'Try adjusting your filters to see more suggestions.'}
                </p>
              </CardContent>
            </Card>
          )}
        </>
      ) : (
        <Card>
          <CardContent className="flex flex-col items-center justify-center py-16">
            <Lightbulb className="h-16 w-16 text-gray-400 mb-4" />
            <h3 className="text-lg font-semibold mb-2">Select a Dataset</h3>
            <p className="text-sm text-gray-500 text-center max-w-sm">
              Choose a dataset from the dropdown above to view and review correction
              suggestions
            </p>
          </CardContent>
        </Card>
      )}
    </div>
  );
}