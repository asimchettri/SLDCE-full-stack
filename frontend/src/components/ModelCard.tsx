import { useState } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { modelAPI } from '@/services/api';
import type { MLModel } from '@/types/model';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { TrendingUp, Trash2, Clock, Target, Award } from 'lucide-react';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';

interface ModelCardProps {
  model: MLModel;
}

export function ModelCard({ model }: ModelCardProps) {
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const queryClient = useQueryClient();

  const deleteMutation = useMutation({
    mutationFn: () => modelAPI.delete(model.id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['models'] });
      setDeleteDialogOpen(false);
    },
  });

  const accuracy = model.test_accuracy || model.train_accuracy || 0;
  const accuracyColor = accuracy >= 90 ? 'text-green-600' : accuracy >= 70 ? 'text-blue-600' : 'text-orange-600';

  const formatTime = (seconds: number | null) => {
    if (!seconds) return 'N/A';
    if (seconds < 60) return `${seconds.toFixed(1)}s`;
    return `${(seconds / 60).toFixed(1)}m`;
  };

  return (
    <>
      <Card className="hover:shadow-lg transition-shadow">
        <CardHeader>
          <div className="flex items-start justify-between">
            <div className="flex-1">
              <div className="flex items-center gap-2">
                <CardTitle className="text-lg">{model.name}</CardTitle>
                {model.is_baseline && (
                  <Badge variant="secondary" className="text-xs">
                    Baseline
                  </Badge>
                )}
              </div>
              <CardDescription className="mt-1">
                {model.model_type}
              </CardDescription>
            </div>
            <Award className="h-5 w-5 text-purple-600 shrink-0 ml-2" />
          </div>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {/* Accuracy Display */}
            <div className="flex items-center justify-center py-4 bg-gray-50 rounded-lg">
              <div className="text-center">
                <div className={`text-3xl font-bold ${accuracyColor}`}>
                  {(accuracy * 100).toFixed(1)}%
                </div>
                <div className="text-xs text-gray-500 mt-1">Accuracy</div>
              </div>
            </div>

            {/* Metrics Grid */}
            <div className="grid grid-cols-2 gap-2 text-sm">
              {model.precision !== null && (
                <div className="flex items-center gap-1">
                  <Target className="h-3 w-3 text-gray-400" />
                  <span className="text-gray-600">Precision:</span>
                  <span className="font-medium">{(model.precision * 100).toFixed(1)}%</span>
                </div>
              )}
              {model.recall !== null && (
                <div className="flex items-center gap-1">
                  <TrendingUp className="h-3 w-3 text-gray-400" />
                  <span className="text-gray-600">Recall:</span>
                  <span className="font-medium">{(model.recall * 100).toFixed(1)}%</span>
                </div>
              )}
              {model.f1_score !== null && (
                <div className="flex items-center gap-1">
                  <Award className="h-3 w-3 text-gray-400" />
                  <span className="text-gray-600">F1:</span>
                  <span className="font-medium">{(model.f1_score * 100).toFixed(1)}%</span>
                </div>
              )}
              {model.training_time_seconds !== null && (
                <div className="flex items-center gap-1">
                  <Clock className="h-3 w-3 text-gray-400" />
                  <span className="text-gray-600">Time:</span>
                  <span className="font-medium">{formatTime(model.training_time_seconds)}</span>
                </div>
              )}
            </div>

            {/* Training Info */}
            {model.num_samples_trained && (
              <div className="text-xs text-gray-500 pt-2 border-t">
                Trained on {model.num_samples_trained.toLocaleString()} samples
              </div>
            )}

            {/* Actions */}
            <div className="flex gap-2 pt-2">
              <Button variant="outline" size="sm" className="flex-1">
                View Details
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

      {/* Delete Dialog */}
      <Dialog open={deleteDialogOpen} onOpenChange={setDeleteDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Delete Model</DialogTitle>
            <DialogDescription>
              Are you sure you want to delete "{model.name}"? This action cannot be undone.
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
        </DialogContent>
      </Dialog>
    </>
  );
}