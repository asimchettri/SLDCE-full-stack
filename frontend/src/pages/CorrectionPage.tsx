import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { suggestionAPI, datasetAPI, correctionsAPI } from '@/services/api';
import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Label } from '@/components/ui/label';
import {
  Select, SelectContent, SelectItem, SelectTrigger, SelectValue,
} from '@/components/ui/select';
import {
  CheckCircle, RefreshCw, Lightbulb, Filter,
  ChevronLeft, ChevronRight, Download, CheckSquare, XSquare, Square,
} from 'lucide-react';
import { SuggestionCard } from '@/components/SuggestionCard';
import { SuggestionStats } from '@/components/SuggestionStats';
import { FeedbackAnalytics } from '@/components/FeedbackAnalytics';
import { ApplyCorrectionsButton } from '@/components/ui/ApplyCorrectionsButton';
import { RetrainButton } from '@/components/ui/RetrainButton';
import type { SuggestionStatus } from '@/types/suggestion';
import { toast } from 'sonner';

export function CorrectionPage() {
  const [selectedDatasetId, setSelectedDatasetId] = useState<number | undefined>();
  const [statusFilter, setStatusFilter] = useState<SuggestionStatus | 'all'>('pending');
  const [minConfidence, setMinConfidence] = useState<number | undefined>();
  const [page, setPage] = useState(1);
  const [selectedIds, setSelectedIds] = useState<Set<number>>(new Set());
  const pageSize = 12;
  const queryClient = useQueryClient();

  const { data: datasets } = useQuery({
    queryKey: ['datasets'],
    queryFn: datasetAPI.getAll,
  });

 const {
    data: suggestionsResponse,
    isLoading: suggestionsLoading,
    refetch: refetchSuggestions,
  } = useQuery({
    queryKey: ['suggestions', selectedDatasetId, statusFilter, minConfidence, page, pageSize],
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

  const { data: stats, refetch: refetchStats } = useQuery({
    queryKey: ['suggestion-stats', selectedDatasetId],
    queryFn: () => suggestionAPI.getStats(selectedDatasetId!),
    enabled: !!selectedDatasetId,
  });

  // current_iteration comes from backend via suggestion stats
  const currentIteration: number = (stats as any)?.current_iteration ?? 1;

  const batchMutation = useMutation({
    mutationFn: ({ ids, action }: { ids: number[]; action: 'accepted' | 'rejected' }) =>
      suggestionAPI.batchUpdate(ids, action),
    onSuccess: (data, variables) => {
      toast.success(`Batch ${variables.action}: ${data.updated} suggestions updated`);
      setSelectedIds(new Set());
      refetchSuggestions();
      refetchStats();
      queryClient.invalidateQueries({ queryKey: ['suggestions'] });
      queryClient.invalidateQueries({ queryKey: ['suggestion-stats'] });
    },
    onError: () => toast.error('Batch update failed'),
  });

  const handleStatusUpdate = () => {
    refetchSuggestions();
    refetchStats();
  };

  const totalPages = suggestionsResponse?.total_pages || 1;
  const suggestions = suggestionsResponse?.suggestions || [];
  const hasAcceptedSuggestions = stats && (stats.accepted + stats.modified) > 0;

  const pendingSuggestions = suggestions.filter(s => s.status === 'pending');
  const allPendingSelected =
    pendingSuggestions.length > 0 && pendingSuggestions.every(s => selectedIds.has(s.id));
  const someSelected = selectedIds.size > 0;

  const toggleSelect = (id: number) => {
    setSelectedIds(prev => {
      const next = new Set(prev);
      next.has(id) ? next.delete(id) : next.add(id);
      return next;
    });
  };

  const toggleSelectAll = () => {
    if (allPendingSelected) {
      setSelectedIds(new Set());
    } else {
      setSelectedIds(new Set(pendingSuggestions.map(s => s.id)));
    }
  };

  return (
    <div className="space-y-6">

      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-3xl font-bold tracking-tight">Correction & Review</h2>
          <p className="text-gray-500 mt-1">
            Review and approve correction suggestions from the detection system
          </p>
        </div>
        <div className="flex gap-2">
          {selectedDatasetId && (
            <Button variant="outline"
              onClick={() => correctionsAPI.downloadCorrected(selectedDatasetId)}>
              <Download className="mr-2 h-4 w-4" />Export CSV
            </Button>
          )}
          <Button variant="outline" onClick={() => refetchSuggestions()}
            disabled={!selectedDatasetId}>
            <RefreshCw className="mr-2 h-4 w-4" />Refresh
          </Button>
        </div>
      </div>

      {/* Apply Corrections Banner */}
      {selectedDatasetId && hasAcceptedSuggestions && (
        <Card className="border-blue-200 bg-blue-50">
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="font-semibold text-blue-900 mb-1">Ready to Apply Corrections</h3>
                <p className="text-sm text-blue-700">
                  You have {stats.accepted + stats.modified} accepted/modified suggestions ready to apply
                </p>
              </div>
              <div className="flex gap-2">
               <ApplyCorrectionsButton
                  datasetId={selectedDatasetId}
                  iteration={currentIteration}
                  onSuccess={() => { refetchSuggestions(); refetchStats(); }}
                />
                <RetrainButton
                  datasetId={selectedDatasetId}
                  iteration={currentIteration}
                  onSuccess={() => {}}
                  disabled={!stats}
                />
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Filters */}
      <Card>
        <CardContent className="pt-6">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div className="space-y-2">
              <Label>Dataset</Label>
              <Select
                value={selectedDatasetId?.toString() || ''}
                onValueChange={(value) => {
                  setSelectedDatasetId(parseInt(value));
                  setPage(1);
                  setSelectedIds(new Set());
                }}
              >
                <SelectTrigger><SelectValue placeholder="Select dataset" /></SelectTrigger>
                <SelectContent>
                  {datasets?.map((d) => (
                    <SelectItem key={d.id} value={d.id.toString()}>{d.name}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-2">
              <Label>Status</Label>
              <Select
                value={statusFilter}
                onValueChange={(value) => {
                  setStatusFilter(value as SuggestionStatus | 'all');
                  setPage(1);
                  setSelectedIds(new Set());
                }}
              >
                <SelectTrigger><SelectValue /></SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Statuses</SelectItem>
                  <SelectItem value="pending">Pending</SelectItem>
                  <SelectItem value="accepted">Accepted</SelectItem>
                  <SelectItem value="rejected">Rejected</SelectItem>
                  <SelectItem value="modified">Modified</SelectItem>
                  <SelectItem value="uncertain">Uncertain</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-2">
              <Label>Min Confidence</Label>
              <Select
                value={minConfidence?.toString() || 'all'}
                onValueChange={(value) => {
                  setMinConfidence(value === 'all' ? undefined : parseFloat(value));
                  setPage(1);
                }}
              >
                <SelectTrigger><SelectValue placeholder="All" /></SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Confidence</SelectItem>
                  <SelectItem value="0.9">Very High (≥90%)</SelectItem>
                  <SelectItem value="0.8">High (≥80%)</SelectItem>
                  <SelectItem value="0.7">Medium (≥70%)</SelectItem>
                  <SelectItem value="0.6">Low (≥60%)</SelectItem>
                </SelectContent>
              </Select>
            </div>

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

      {/* Stats */}
      {stats && selectedDatasetId && <SuggestionStats stats={stats} />}

      {/* Feedback Analytics */}
{selectedDatasetId && <FeedbackAnalytics datasetId={selectedDatasetId} iteration={currentIteration} />}

      {/* Suggestions Grid */}
      {selectedDatasetId ? (
        <>
          {suggestionsLoading ? (
            <div className="flex items-center justify-center py-12">
              <RefreshCw className="h-8 w-8 animate-spin text-gray-400" />
            </div>
          ) : suggestions.length > 0 ? (
            <>
              {/* Batch toolbar */}
              {statusFilter === 'pending' && pendingSuggestions.length > 0 && (
                <div className="flex items-center gap-3 p-3 bg-gray-50 rounded-lg border">
                  <button
                    onClick={toggleSelectAll}
                    className="flex items-center gap-2 text-sm text-gray-600 hover:text-gray-900"
                  >
                    {allPendingSelected
                      ? <CheckSquare className="h-4 w-4 text-blue-600" />
                      : <Square className="h-4 w-4" />
                    }
                    {allPendingSelected ? 'Deselect All' : 'Select All'}
                  </button>

                  {someSelected && (
                    <>
                      <span className="text-sm text-gray-500">{selectedIds.size} selected</span>
                      <div className="flex gap-2 ml-auto">
                        <Button size="sm"
                          className="bg-green-600 hover:bg-green-700"
                          disabled={batchMutation.isPending}
                          onClick={() => batchMutation.mutate({
                            ids: Array.from(selectedIds), action: 'accepted',
                          })}>
                          <CheckSquare className="h-3.5 w-3.5 mr-1.5" />
                          Approve Selected ({selectedIds.size})
                        </Button>
                        <Button size="sm" variant="destructive"
                          disabled={batchMutation.isPending}
                          onClick={() => batchMutation.mutate({
                            ids: Array.from(selectedIds), action: 'rejected',
                          })}>
                          <XSquare className="h-3.5 w-3.5 mr-1.5" />
                          Reject Selected ({selectedIds.size})
                        </Button>
                      </div>
                    </>
                  )}
                </div>
              )}

              {/* Top pagination + count */}
              <div className="flex items-center justify-between">
                <h3 className="text-lg font-semibold">
                  Suggestions ({suggestionsResponse?.total || 0})
                </h3>
                {totalPages > 1 && (
                  <div className="flex items-center gap-2">
                    <Button variant="outline" size="sm"
                      onClick={() => setPage(p => Math.max(1, p - 1))} disabled={page === 1}>
                      <ChevronLeft className="h-4 w-4" />Previous
                    </Button>
                    <span className="text-sm text-gray-600 px-2">
                      Page {page} of {totalPages}
                    </span>
                    <Button variant="outline" size="sm"
                      onClick={() => setPage(p => Math.min(totalPages, p + 1))}
                      disabled={page === totalPages}>
                      Next<ChevronRight className="h-4 w-4 ml-1" />
                    </Button>
                  </div>
                )}
              </div>

              {/* Cards grid */}
              <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
                {suggestions.map((suggestion) => (
                  <div key={suggestion.id} className="relative">
                    {suggestion.status === 'pending' && statusFilter === 'pending' && (
                      <div className="absolute top-3 left-3 z-10">
                        <button
                          onClick={() => toggleSelect(suggestion.id)}
                          className="rounded bg-white shadow-sm border p-0.5 hover:bg-gray-50"
                        >
                          {selectedIds.has(suggestion.id)
                            ? <CheckSquare className="h-4 w-4 text-blue-600" />
                            : <Square className="h-4 w-4 text-gray-400" />
                          }
                        </button>
                      </div>
                    )}
                    <SuggestionCard
                      suggestion={suggestion}
                      onStatusUpdate={handleStatusUpdate}
                    />
                  </div>
                ))}
              </div>

              {/* Bottom pagination */}
              {totalPages > 1 && (
                <div className="flex justify-center">
                  <div className="flex items-center gap-2">
                    <Button variant="outline"
                      onClick={() => setPage(p => Math.max(1, p - 1))} disabled={page === 1}>
                      <ChevronLeft className="h-4 w-4 mr-1" />Previous
                    </Button>
                    <span className="text-sm text-gray-600 px-4">
                      Page {page} of {totalPages}
                    </span>
                    <Button variant="outline"
                      onClick={() => setPage(p => Math.min(totalPages, p + 1))}
                      disabled={page === totalPages}>
                      Next<ChevronRight className="h-4 w-4 ml-1" />
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
                  {statusFilter === 'pending' ? 'All caught up!' : 'No suggestions found'}
                </h3>
                <p className="text-sm text-gray-500 text-center max-w-sm">
                  {statusFilter === 'pending'
                    ? 'No pending suggestions. Run detection to generate new ones.'
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
              Choose a dataset from the dropdown above to view and review correction suggestions
            </p>
          </CardContent>
        </Card>
      )}
    </div>
  );
}