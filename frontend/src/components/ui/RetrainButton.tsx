import { useState } from 'react';
import { useMutation } from '@tanstack/react-query';
import { retrainAPI } from '@/services/api';
import { Button } from '@/components/ui/button';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { 
  RefreshCw, 
  TrendingUp, 
  Loader2,
  CheckCircle,
  Target,
  Clock
} from 'lucide-react';
import { toast } from 'sonner';

interface RetrainButtonProps {
  datasetId: number;
  iteration?: number;
  onSuccess?: () => void;
  disabled?: boolean;
}

export function RetrainButton({
  datasetId,
  iteration = 1,
  onSuccess,
  disabled = false,
}: RetrainButtonProps) {
  const [resultsOpen, setResultsOpen] = useState(false);
  const [retrainResults, setRetrainResults] = useState<any>(null);

  //  Retrain mutation
  const retrainMutation = useMutation({
    mutationFn: () => retrainAPI.retrain(datasetId, iteration),
    onSuccess: (data) => {
      setRetrainResults(data);
      setResultsOpen(true);
      
      const improvement = data.improvement.percentage;
      const message = improvement > 0 
        ? `Model improved by ${improvement.toFixed(2)}%! 🎉`
        : improvement < 0
        ? `Performance decreased by ${Math.abs(improvement).toFixed(2)}%`
        : 'Performance unchanged';
      
      toast.success('Retraining Complete', {
        description: message,
      });
      
      onSuccess?.();
    },
    onError: (error: any) => {
      toast.error('Retraining Failed', {
        description: error.response?.data?.detail || 'An error occurred during retraining',
      });
    },
  });

  const handleRetrain = () => {
    retrainMutation.mutate();
  };

  return (
    <>
      {/* Main Button */}
      <Button
        onClick={handleRetrain}
        disabled={disabled || retrainMutation.isPending}
        size="lg"
        className="bg-blue-600 hover:bg-blue-700"
      >
        {retrainMutation.isPending ? (
          <>
            <Loader2 className="mr-2 h-5 w-5 animate-spin" />
            Retraining Model...
          </>
        ) : (
          <>
            <RefreshCw className="mr-2 h-5 w-5" />
            Retrain Model
          </>
        )}
      </Button>

      {/* Results Dialog */}
      <Dialog open={resultsOpen} onOpenChange={setResultsOpen}>
        <DialogContent className="sm:max-w-[700px]">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <CheckCircle className="h-5 w-5 text-green-600" />
              Retraining Results
            </DialogTitle>
            <DialogDescription>
              Model has been retrained on corrected data. Here's the comparison:
            </DialogDescription>
          </DialogHeader>

          {retrainResults && (
            <div className="space-y-4">
              {/* Improvement Highlight */}
              <Card className={
                retrainResults.improvement.percentage > 0 
                  ? 'bg-green-50 border-green-200'
                  : retrainResults.improvement.percentage < 0
                  ? 'bg-red-50 border-red-200'
                  : 'bg-gray-50 border-gray-200'
              }>
                <CardContent className="pt-6">
                  <div className="text-center">
                    <TrendingUp className={`h-12 w-12 mx-auto mb-2 ${
                      retrainResults.improvement.percentage > 0 
                        ? 'text-green-600'
                        : 'text-gray-600'
                    }`} />
                    <div className={`text-4xl font-bold mb-1 ${
                      retrainResults.improvement.percentage > 0 
                        ? 'text-green-700'
                        : retrainResults.improvement.percentage < 0
                        ? 'text-red-700'
                        : 'text-gray-700'
                    }`}>
                      {retrainResults.improvement.percentage > 0 ? '+' : ''}
                      {retrainResults.improvement.percentage.toFixed(2)}%
                    </div>
                    <div className="text-sm text-gray-600">
                      Accuracy Improvement
                    </div>
                  </div>
                </CardContent>
              </Card>

              {/* Metrics Comparison */}
              <div className="grid grid-cols-2 gap-4">
                {/* Baseline */}
                <Card>
                  <CardHeader className="pb-3">
                    <CardTitle className="text-sm">Baseline Model</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-2">
                      <div>
                        <div className="text-2xl font-bold text-gray-700">
                          {(retrainResults.baseline_metrics.accuracy * 100).toFixed(2)}%
                        </div>
                        <div className="text-xs text-gray-500">Accuracy</div>
                      </div>
                    </div>
                  </CardContent>
                </Card>

                {/* Retrained */}
                <Card className="border-blue-200">
                  <CardHeader className="pb-3">
                    <CardTitle className="text-sm text-blue-700">
                      Retrained Model
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-2">
                      <div>
                        <div className="text-2xl font-bold text-blue-700">
                          {(retrainResults.retrained_metrics.accuracy * 100).toFixed(2)}%
                        </div>
                        <div className="text-xs text-gray-500">Accuracy</div>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              </div>

              {/* Detailed Metrics */}
              <Card>
                <CardHeader className="pb-3">
                  <CardTitle className="text-sm">Detailed Metrics (Retrained)</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-3 gap-4 text-center">
                    <div>
                      <div className="text-lg font-bold text-gray-700">
                        {(retrainResults.retrained_metrics.precision * 100).toFixed(1)}%
                      </div>
                      <div className="text-xs text-gray-500">Precision</div>
                    </div>
                    <div>
                      <div className="text-lg font-bold text-gray-700">
                        {(retrainResults.retrained_metrics.recall * 100).toFixed(1)}%
                      </div>
                      <div className="text-xs text-gray-500">Recall</div>
                    </div>
                    <div>
                      <div className="text-lg font-bold text-gray-700">
                        {(retrainResults.retrained_metrics.f1_score * 100).toFixed(1)}%
                      </div>
                      <div className="text-xs text-gray-500">F1-Score</div>
                    </div>
                  </div>
                </CardContent>
              </Card>

              {/* Training Info */}
              <Card>
                <CardHeader className="pb-3">
                  <CardTitle className="text-sm">Training Information</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-2 gap-4 text-sm">
                    <div className="flex items-center gap-2">
                      <Target className="h-4 w-4 text-gray-500" />
                      <div>
                        <div className="font-semibold">
                          {retrainResults.training_info.samples_corrected}
                        </div>
                        <div className="text-xs text-gray-500">Samples Corrected</div>
                      </div>
                    </div>
                    <div className="flex items-center gap-2">
                      <Clock className="h-4 w-4 text-gray-500" />
                      <div>
                        <div className="font-semibold">
                          {retrainResults.training_info.training_time_seconds}s
                        </div>
                        <div className="text-xs text-gray-500">Training Time</div>
                      </div>
                    </div>
                    <div className="flex items-center gap-2">
                      <CheckCircle className="h-4 w-4 text-gray-500" />
                      <div>
                        <div className="font-semibold">
                          {retrainResults.training_info.labels_changed}
                        </div>
                        <div className="text-xs text-gray-500">Labels Changed</div>
                      </div>
                    </div>
                    <div className="flex items-center gap-2">
                      <TrendingUp className="h-4 w-4 text-gray-500" />
                      <div>
                        <div className="font-semibold">
                          {retrainResults.training_info.noise_reduced_pct.toFixed(1)}%
                        </div>
                        <div className="text-xs text-gray-500">Noise Reduced</div>
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>

              {/* Action Button */}
              <div className="flex justify-end">
                <Button onClick={() => setResultsOpen(false)}>
                  Close
                </Button>
              </div>
            </div>
          )}
        </DialogContent>
      </Dialog>
    </>
  );
}