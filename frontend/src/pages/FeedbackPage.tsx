import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { feedbackAPI, datasetAPI } from '@/services/api';
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
  RefreshCw,
  History,
  Filter,
  ChevronLeft,
  ChevronRight,
  FileText,
  Inbox
} from 'lucide-react';
import { FeedbackTimelineItem } from '@/components/FeedbackTimelineItem';
import { FeedbackStatsDashboard } from '@/components/FeedbackStatsDashboard';
import type { FeedbackAction } from '@/types/feedback';

export function FeedbackPage() {
  const [selectedDatasetId, setSelectedDatasetId] = useState<number | undefined>();
  const [actionFilter, setActionFilter] = useState<FeedbackAction | 'all'>('all');
  const [iterationFilter, setIterationFilter] = useState<number | undefined>();
  const [page, setPage] = useState(1);
  const pageSize = 10;

  // Fetch datasets
  const { data: datasets } = useQuery({
    queryKey: ['datasets'],
    queryFn: datasetAPI.getAll,
  });

  // Fetch feedback with filters
  const {
    data: feedbackResponse,
    isLoading: feedbackLoading,
    refetch: refetchFeedback,
  } = useQuery({
    queryKey: [
      'feedback',
      selectedDatasetId,
      actionFilter,
      iterationFilter,
      page,
      pageSize,
    ],
    queryFn: () =>
      feedbackAPI.getAll({
        dataset_id: selectedDatasetId,
        action: actionFilter === 'all' ? undefined : actionFilter,
        iteration: iterationFilter,
        page,
        page_size: pageSize,
      }),
    enabled: !!selectedDatasetId,
  });

  // Fetch feedback stats
  const { data: stats } = useQuery({
    queryKey: ['feedback-stats', selectedDatasetId],
    queryFn: () => feedbackAPI.getStats(selectedDatasetId!),
    enabled: !!selectedDatasetId,
  });

  const totalPages = feedbackResponse?.total_pages || 1;
  const feedback = feedbackResponse?.feedback || [];
  const hasData = feedback.length > 0;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <div className="flex items-center gap-3">
            <h2 className="text-3xl font-bold tracking-tight">Feedback History</h2>
          </div>
          <p className="text-gray-500 mt-1">
            Review past decisions and track learning progress
          </p>
        </div>
        <Button
          variant="outline"
          onClick={() => refetchFeedback()}
          disabled={!selectedDatasetId}
        >
          <RefreshCw className="mr-2 h-4 w-4" />
          Refresh
        </Button>
      </div>

      {/* Filters */}
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

            {/* Action Filter */}
            <div className="space-y-2">
              <Label>Action</Label>
              <Select
                value={actionFilter}
                onValueChange={(value: string) => {
                  setActionFilter(value as FeedbackAction | 'all');
                  setPage(1);
                }}
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Actions</SelectItem>
                  <SelectItem value="accept">Accepted</SelectItem>
                  <SelectItem value="reject">Rejected</SelectItem>
                  <SelectItem value="modify">Modified</SelectItem>
                </SelectContent>
              </Select>
            </div>

            {/* Iteration Filter */}
            <div className="space-y-2">
              <Label>Iteration</Label>
              <Select
                value={iterationFilter?.toString() || 'all'}
                onValueChange={(value: string) => {
                  setIterationFilter(value === 'all' ? undefined : parseInt(value));
                  setPage(1);
                }}
              >
                <SelectTrigger>
                  <SelectValue placeholder="All Iterations" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Iterations</SelectItem>
                  <SelectItem value="1">Iteration 1</SelectItem>
                  <SelectItem value="2">Iteration 2</SelectItem>
                  <SelectItem value="3">Iteration 3</SelectItem>
                </SelectContent>
              </Select>
            </div>

            {/* Quick Info */}
            <div className="space-y-2">
              <Label>Results</Label>
              <div className="flex items-center gap-2 h-10 px-3 rounded-md border bg-gray-50">
                <Filter className="h-4 w-4 text-gray-500" />
                <span className="text-sm text-gray-700">
                  {feedback.length} of {feedbackResponse?.total || 0}
                </span>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Statistics Dashboard */}
      {stats && selectedDatasetId && stats.total_feedback > 0 && (
        <FeedbackStatsDashboard stats={stats} />
      )}

      {/* Timeline */}
      {selectedDatasetId ? (
        <>
          {feedbackLoading ? (
            <div className="flex items-center justify-center py-12">
              <RefreshCw className="h-8 w-8 animate-spin text-gray-400" />
            </div>
          ) : hasData ? (
            <>
              {/* Timeline Header */}
              <div className="flex items-center justify-between">
                <h3 className="text-lg font-semibold flex items-center gap-2">
                  <History className="h-5 w-5" />
                  Timeline ({feedbackResponse?.total || 0} total)
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

              {/* Timeline Items */}
              <div className="relative">
                {feedback.map((item, index) => (
                  <FeedbackTimelineItem
                    key={item.id}
                    feedback={item}
                    showDetails={index === 0} // First item expanded by default
                  />
                ))}
              </div>

              {/* Bottom Pagination */}
              {totalPages > 1 && (
                <div className="flex justify-center pt-4">
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
              <CardContent className="flex flex-col items-center justify-center py-16">
                <Inbox className="h-16 w-16 text-gray-400 mb-4" />
                <h3 className="text-lg font-semibold mb-2">No Feedback Yet</h3>
                <p className="text-sm text-gray-500 text-center max-w-sm mb-4">
                  {actionFilter !== 'all'
                    ? `No ${actionFilter}ed suggestions found. Try changing the filter.`
                    : 'Start reviewing suggestions to see feedback history here.'}
                </p>
                <Button
                  variant="outline"
                  onClick={() => window.location.href = '/correction'}
                >
                  Go to Correction Page
                </Button>
              </CardContent>
            </Card>
          )}
        </>
      ) : (
        <Card>
          <CardContent className="flex flex-col items-center justify-center py-16">
            <FileText className="h-16 w-16 text-gray-400 mb-4" />
            <h3 className="text-lg font-semibold mb-2">Select a Dataset</h3>
            <p className="text-sm text-gray-500 text-center max-w-sm">
              Choose a dataset from the dropdown above to view feedback history and statistics
            </p>
          </CardContent>
        </Card>
      )}
    </div>
  );
}