import { useState } from 'react';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Brain, Loader2, TrendingUp, AlertCircle } from 'lucide-react';
import { baselineAPI } from '@/services/api';

interface TrainBaselineDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  datasetId: number;
  datasetName: string;
  onSuccess: () => void;
}

export function TrainBaselineDialog({
  open,
  onOpenChange,
  datasetId,
  datasetName,
  onSuccess,
}: TrainBaselineDialogProps) {
  const [modelType, setModelType] = useState<'random_forest' | 'logistic' | 'svm'>('random_forest');
  const [isTraining, setIsTraining] = useState(false);
  const [result, setResult] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);

  const handleTrain = async () => {
    setIsTraining(true);
    setError(null);
    setResult(null);

    try {
      const trainResult = await baselineAPI.train(datasetId, modelType, 0.2);
      setResult(trainResult);
      
      // Auto-close after 3 seconds on success
      setTimeout(() => {
        onSuccess();
        onOpenChange(false);
      }, 3000);
    } catch (err: any) {
      const errorMsg = err.response?.data?.detail || err.message || 'Training failed';
      setError(errorMsg);
    } finally {
      setIsTraining(false);
    }
  };

  const handleClose = () => {
    if (!isTraining) {
      setResult(null);
      setError(null);
      onOpenChange(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={handleClose}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Brain className="h-5 w-5 text-blue-600" />
            Train Baseline Model
          </DialogTitle>
          <DialogDescription>
            Train a model on clean data to establish baseline performance
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4 pt-2">
          {/* Dataset Info */}
          <div className="bg-gray-50 p-3 rounded-lg border">
            <p className="text-sm font-medium text-gray-700">Dataset</p>
            <p className="text-xs text-gray-500 mt-1">{datasetName}</p>
          </div>

          {/* Model Selection */}
          {!result && (
            <div>
              <label className="text-sm font-medium mb-2 block">Select Model Type</label>
              <Select
                value={modelType}
                onValueChange={(value: any) => setModelType(value)}
                disabled={isTraining}
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="random_forest">
                    <div className="flex items-center gap-2">
                      <span>🌲</span>
                      <div>
                        <div className="font-medium">Random Forest</div>
                        <div className="text-xs text-gray-500">Ensemble learning (Recommended)</div>
                      </div>
                    </div>
                  </SelectItem>
                  <SelectItem value="logistic">
                    <div className="flex items-center gap-2">
                      <span>📊</span>
                      <div>
                        <div className="font-medium">Logistic Regression</div>
                        <div className="text-xs text-gray-500">Fast and interpretable</div>
                      </div>
                    </div>
                  </SelectItem>
                  <SelectItem value="svm">
                    <div className="flex items-center gap-2">
                      <span>🎯</span>
                      <div>
                        <div className="font-medium">Support Vector Machine</div>
                        <div className="text-xs text-gray-500">Good for complex boundaries</div>
                      </div>
                    </div>
                  </SelectItem>
                </SelectContent>
              </Select>
            </div>
          )}

          {/* Info Box */}
          {!result && !error && (
            <div className="bg-blue-50 p-3 rounded-lg border border-blue-200">
              <p className="text-xs text-blue-800">
                <strong>Important:</strong> Train baseline on clean data before injecting noise or running detection. This establishes ground truth performance.
              </p>
            </div>
          )}

          {/* Success Result */}
          {result && (
            <div className="bg-green-50 p-4 rounded-lg border border-green-200">
              <div className="flex items-start gap-2 mb-3">
                <TrendingUp className="h-5 w-5 text-green-600 mt-0.5" />
                <div className="flex-1">
                  <p className="font-semibold text-green-800">Baseline Trained Successfully!</p>
                  <p className="text-xs text-green-700 mt-1">Model: {result.model_name}</p>
                </div>
              </div>
              
              <div className="space-y-2">
                <div className="grid grid-cols-2 gap-2 text-sm">
                  <div className="bg-white p-2 rounded border">
                    <div className="text-xs text-gray-600">Test Accuracy</div>
                    <div className="font-bold text-green-600">
                      {(result.test_metrics.accuracy * 100).toFixed(2)}%
                    </div>
                  </div>
                  <div className="bg-white p-2 rounded border">
                    <div className="text-xs text-gray-600">Precision</div>
                    <div className="font-bold text-green-600">
                      {(result.test_metrics.precision * 100).toFixed(2)}%
                    </div>
                  </div>
                  <div className="bg-white p-2 rounded border">
                    <div className="text-xs text-gray-600">Recall</div>
                    <div className="font-bold text-green-600">
                      {(result.test_metrics.recall * 100).toFixed(2)}%
                    </div>
                  </div>
                  <div className="bg-white p-2 rounded border">
                    <div className="text-xs text-gray-600">F1-Score</div>
                    <div className="font-bold text-green-600">
                      {(result.test_metrics.f1_score * 100).toFixed(2)}%
                    </div>
                  </div>
                </div>
                <p className="text-xs text-gray-600 text-center mt-2">
                  Trained on {result.training_info.samples_trained} samples
                </p>
              </div>
            </div>
          )}

          {/* Error Display */}
          {error && (
            <div className="bg-red-50 p-3 rounded-lg border border-red-200">
              <div className="flex items-start gap-2">
                <AlertCircle className="h-5 w-5 text-red-600 mt-0.5 flex-shrink-0" />
                <div>
                  <p className="font-semibold text-red-800">Training Failed</p>
                  <p className="text-xs text-red-700 mt-1">{error}</p>
                </div>
              </div>
            </div>
          )}

          {/* Action Buttons */}
          <div className="flex gap-2 pt-2">
            {!result && (
              <Button
                onClick={handleTrain}
                disabled={isTraining}
                className="flex-1"
              >
                {isTraining ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    Training...
                  </>
                ) : (
                  <>
                    <Brain className="mr-2 h-4 w-4" />
                    Train Baseline
                  </>
                )}
              </Button>
            )}
            <Button
              variant="outline"
              onClick={handleClose}
              disabled={isTraining}
              className={result ? 'flex-1' : ''}
            >
              {result ? 'Close' : 'Cancel'}
            </Button>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
}