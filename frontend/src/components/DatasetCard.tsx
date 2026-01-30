import { useState } from 'react';
import { Brain } from 'lucide-react'; 
import { useMutation, useQueryClient, useQuery } from '@tanstack/react-query';
import { baselineAPI, datasetAPI } from '@/services/api';
import type { Dataset } from '@/types/dataset';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import {  Trash2, AlertCircle, TrendingUp, Database as DatabaseIcon } from 'lucide-react';
import { TrainBaselineDialog } from './TrainBaselineDialog'; 

import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';

interface DatasetCardProps {
  dataset: Dataset;
}

export function DatasetCard({ dataset }: DatasetCardProps) {
  const [trainBaselineOpen, setTrainBaselineOpen] = useState(false);
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [statsDialogOpen, setStatsDialogOpen] = useState(false);
  const queryClient = useQueryClient();

  // Fetch dataset statistics
  const { data: stats, isLoading: statsLoading } = useQuery({
    queryKey: ['dataset-stats', dataset.id],
    queryFn: () => datasetAPI.getStats(dataset.id),
    enabled: statsDialogOpen,
  });

  // Delete mutation
  const deleteMutation = useMutation({
    mutationFn: () => datasetAPI.delete(dataset.id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['datasets'] });
      setDeleteDialogOpen(false);
    },
  });

  // Check if baseline exists
  const { data: baselineCheck } = useQuery({
    queryKey: ['baseline-check', dataset.id],
    queryFn: () => baselineAPI.checkExists(dataset.id),
  });

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
    });
  };

  return (
    <>
      <Card className="hover:shadow-lg transition-shadow">
        <CardHeader>
          <div className="flex items-start justify-between">
            <div className="flex-1">
              <CardTitle className="text-lg">{dataset.name}</CardTitle>
              <CardDescription className="mt-1">
                {dataset.description || 'No description provided'}
              </CardDescription>
            </div>
            <DatabaseIcon className="h-5 w-5 text-blue-600 shrink-0 ml-2" />
          </div>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            {/* Statistics Grid */}
            <div className="grid grid-cols-3 gap-2 text-sm">
              <div className="flex flex-col items-center p-2 bg-blue-50 rounded-lg">
                <span className="text-xs text-gray-600">Samples</span>
                <span className="text-lg font-bold text-blue-700">
                  {dataset.num_samples}
                </span>
              </div>
              <div className="flex flex-col items-center p-2 bg-green-50 rounded-lg">
                <span className="text-xs text-gray-600">Features</span>
                <span className="text-lg font-bold text-green-700">
                  {dataset.num_features}
                </span>
              </div>
              <div className="flex flex-col items-center p-2 bg-purple-50 rounded-lg">
                <span className="text-xs text-gray-600">Classes</span>
                <span className="text-lg font-bold text-purple-700">
                  {dataset.num_classes}
                </span>
              </div>
            </div>

            {/* Upload Date */}
            <div className="text-xs text-gray-500 pt-2 border-t">
              Uploaded {formatDate(dataset.created_at)}
            </div>

            {/* ========== ADD THIS SECTION ========== */}
            {/* Baseline Training Status */}
            {!baselineCheck?.exists ? (
              <div className="pt-2 border-t">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setTrainBaselineOpen(true)}
                  className="w-full"
                >
                  <Brain className="mr-2 h-4 w-4" />
                  Train Baseline Model
                </Button>
                <p className="text-xs text-gray-500 text-center mt-1">
                  Train on clean data first
                </p>
              </div>
            ) : (
              <div className="pt-2 border-t">
                <div className="bg-green-50 border border-green-200 rounded-md p-3">
                  <div className="flex items-start gap-2">
                    <Brain className="h-4 w-4 text-green-600 mt-0.5 flex-shrink-0" />
                    <div className="flex-1 min-w-0">
                      <div className="text-xs font-medium text-green-800">
                        Baseline Trained
                      </div>
                      <div className="text-xs text-green-600 mt-0.5 truncate">
                        {baselineCheck.model_type.replace('_', ' ')} • 
                        {' '}{(baselineCheck.test_accuracy * 100).toFixed(1)}% accuracy
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            )}
            {/* ========== END NEW SECTION ========== */}

            {/* Action Buttons */}
            <div className="flex gap-2 pt-2">
              <Button
                variant="outline"
                size="sm"
                className="flex-1"
                onClick={() => setStatsDialogOpen(true)}
              >
                <TrendingUp className="mr-2 h-4 w-4" />
                View Stats
              </Button>
              <Button
                variant="outline"
                size="sm"
                onClick={() => setDeleteDialogOpen(true)}
                className="text-red-600 hover:text-red-700 hover:bg-red-50"
              >
                <Trash2 className="h-4 w-4" />
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* ========== ADD THIS DIALOG ========== */}
      {/* Train Baseline Dialog */}
      <TrainBaselineDialog
        open={trainBaselineOpen}
        onOpenChange={setTrainBaselineOpen}
        datasetId={dataset.id}
        datasetName={dataset.name}
        onSuccess={() => {
          // Refetch baseline check to update UI
          queryClient.invalidateQueries({ queryKey: ['baseline-check', dataset.id] });
          queryClient.invalidateQueries({ queryKey: ['models'] });
        }}
      />
      {/* ========== END NEW DIALOG ========== */}

      {/* Statistics Dialog */}
      <Dialog open={statsDialogOpen} onOpenChange={setStatsDialogOpen}>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle>{dataset.name} - Statistics</DialogTitle>
            <DialogDescription>
              Detailed statistics and information about this dataset
            </DialogDescription>
          </DialogHeader>

          {statsLoading ? (
            <div className="flex items-center justify-center py-8">
              <div className="text-gray-500">Loading statistics...</div>
            </div>
          ) : stats ? (
            <div className="space-y-4">
              {/* Overview Stats */}
              <div className="grid grid-cols-2 gap-4">
                <Card>
                  <CardHeader className="pb-2">
                    <CardTitle className="text-sm font-medium text-gray-600">
                      Total Samples
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="text-2xl font-bold">{stats.total_samples}</div>
                  </CardContent>
                </Card>

                <Card>
                  <CardHeader className="pb-2">
                    <CardTitle className="text-sm font-medium text-gray-600">
                      Features
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="text-2xl font-bold">{stats.num_features}</div>
                  </CardContent>
                </Card>

                <Card>
                  <CardHeader className="pb-2">
                    <CardTitle className="text-sm font-medium text-gray-600">
                      Classes
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="text-2xl font-bold">{stats.num_classes}</div>
                  </CardContent>
                </Card>

                <Card>
                  <CardHeader className="pb-2">
                    <CardTitle className="text-sm font-medium text-gray-600">
                      Noise Level
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="text-2xl font-bold text-orange-600">
                      {stats.noise_percentage}%
                    </div>
                  </CardContent>
                </Card>
              </div>

              {/* Quality Metrics */}
              <Card>
                <CardHeader>
                  <CardTitle className="text-sm">Data Quality</CardTitle>
                </CardHeader>
                <CardContent className="space-y-2">
                  <div className="flex justify-between text-sm">
                    <span className="text-gray-600">Suspicious Samples</span>
                    <span className="font-medium text-orange-600">
                      {stats.suspicious_samples}
                    </span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span className="text-gray-600">Corrected Samples</span>
                    <span className="font-medium text-green-600">
                      {stats.corrected_samples}
                    </span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span className="text-gray-600">Mismatched Labels</span>
                    <span className="font-medium text-red-600">
                      {stats.mismatched_labels}
                    </span>
                  </div>
                </CardContent>
              </Card>

              {/* Warning if high noise */}
              {stats.noise_percentage > 10 && (
                <div className="flex items-start gap-2 p-3 bg-orange-50 border border-orange-200 rounded-lg">
                  <AlertCircle className="h-5 w-5 text-orange-600 shrink-0 mt-0.5" />
                  <div className="text-sm">
                    <p className="font-medium text-orange-900">High Noise Level Detected</p>
                    <p className="text-orange-700 mt-1">
                      This dataset has {stats.noise_percentage}% noisy labels. 
                      Consider running detection to identify mislabeled samples.
                    </p>
                  </div>
                </div>
              )}
            </div>
          ) : (
            <div className="text-center py-8 text-gray-500">
              Failed to load statistics
            </div>
          )}

          <DialogFooter>
            <Button onClick={() => setStatsDialogOpen(false)}>Close</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Delete Confirmation Dialog */}
      <Dialog open={deleteDialogOpen} onOpenChange={setDeleteDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Delete Dataset</DialogTitle>
            <DialogDescription>
              Are you sure you want to delete "{dataset.name}"? This action cannot be undone.
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => setDeleteDialogOpen(false)}
              disabled={deleteMutation.isPending}
            >
              Cancel
            </Button>
            <Button
              variant="destructive"
              onClick={() => deleteMutation.mutate()}
              disabled={deleteMutation.isPending}
            >
              {deleteMutation.isPending ? 'Deleting...' : 'Delete'}
            </Button>
          </DialogFooter>
          {deleteMutation.isError && (
            <p className="text-sm text-red-500 mt-2">
              Failed to delete dataset. Please try again.
            </p>
          )}
        </DialogContent>
      </Dialog>
    </>
  );
}