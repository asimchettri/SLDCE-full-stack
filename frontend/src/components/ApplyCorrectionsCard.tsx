import { useState } from 'react';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { correctionsAPI } from '@/services/api';
import { CheckCircle2, XCircle, AlertCircle, Loader2 } from 'lucide-react';

interface ApplyCorrectionsCardProps {
  datasetId: number;
  iteration?: number;
  onSuccess?: () => void;
}

export default function ApplyCorrectionsCard({
  datasetId,
  iteration = 1,
  onSuccess
}: ApplyCorrectionsCardProps) {
  const [isLoading, setIsLoading] = useState(false);
  const [preview, setPreview] = useState<any>(null);
  const [result, setResult] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);

  // Preview what will happen
  const handlePreview = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const data = await correctionsAPI.preview(datasetId, iteration);
      setPreview(data);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to preview corrections');
    } finally {
      setIsLoading(false);
    }
  };

  // Apply corrections
  const handleApply = async () => {
    if (!confirm('Are you sure you want to apply these corrections? This will update the dataset labels.')) {
      return;
    }

    setIsLoading(true);
    setError(null);
    try {
      const data = await correctionsAPI.apply(datasetId, iteration);
      setResult(data);
      setPreview(null);
      if (onSuccess) onSuccess();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to apply corrections');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <Card className="p-6 space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-lg font-semibold">Apply Corrections</h3>
          <p className="text-sm text-muted-foreground">
            Apply accepted feedback to update dataset labels
          </p>
        </div>
        {!result && (
          <div className="flex gap-2">
            <Button
              variant="outline"
              onClick={handlePreview}
              disabled={isLoading}
            >
              {isLoading ? <Loader2 className="w-4 h-4 animate-spin" /> : 'Preview'}
            </Button>
            <Button
              onClick={handleApply}
              disabled={isLoading || !preview}
            >
              {isLoading ? <Loader2 className="w-4 h-4 animate-spin" /> : 'Apply Corrections'}
            </Button>
          </div>
        )}
      </div>

      {/* Error Message */}
      {error && (
        <div className="flex items-center gap-2 p-4 bg-destructive/10 border border-destructive rounded-lg">
          <XCircle className="w-5 h-5 text-destructive flex-shrink-0" />
          <p className="text-sm text-destructive">{error}</p>
        </div>
      )}

      {/* Preview Results */}
      {preview && !result && (
        <div className="space-y-3 p-4 bg-blue-50 dark:bg-blue-950/20 border border-blue-200 dark:border-blue-800 rounded-lg">
          <div className="flex items-center gap-2 text-blue-700 dark:text-blue-400">
            <AlertCircle className="w-5 h-5" />
            <h4 className="font-semibold">Preview: Changes to be Applied</h4>
          </div>
          
          <div className="grid grid-cols-2 gap-4 text-sm">
            <div>
              <p className="text-muted-foreground">Total Feedback</p>
              <p className="text-lg font-semibold">{preview.total_feedback}</p>
            </div>
            <div>
              <p className="text-muted-foreground">Corrections to Apply</p>
              <p className="text-lg font-semibold text-green-600">
                {preview.corrections_to_apply}
              </p>
            </div>
            <div>
              <p className="text-muted-foreground">Labels to Change</p>
              <p className="text-lg font-semibold text-blue-600">
                {preview.labels_to_change}
              </p>
            </div>
            <div>
              <p className="text-muted-foreground">Samples Rejected</p>
              <p className="text-lg font-semibold text-red-600">
                {preview.samples_to_reject}
              </p>
            </div>
          </div>

          <div className="pt-2 border-t border-blue-200 dark:border-blue-800">
            <p className="text-sm text-muted-foreground">Estimated Noise Reduction</p>
            <p className="text-2xl font-bold text-blue-700 dark:text-blue-400">
              {preview.estimated_noise_reduction}%
            </p>
          </div>
        </div>
      )}

      {/* Success Results */}
      {result && (
        <div className="space-y-3 p-4 bg-green-50 dark:bg-green-950/20 border border-green-200 dark:border-green-800 rounded-lg">
          <div className="flex items-center gap-2 text-green-700 dark:text-green-400">
            <CheckCircle2 className="w-5 h-5" />
            <h4 className="font-semibold">Corrections Applied Successfully!</h4>
          </div>
          
          <div className="grid grid-cols-2 gap-4 text-sm">
            <div>
              <p className="text-muted-foreground">Feedback Processed</p>
              <p className="text-lg font-semibold">{result.total_feedback_processed}</p>
            </div>
            <div>
              <p className="text-muted-foreground">Corrections Applied</p>
              <p className="text-lg font-semibold text-green-600">
                {result.corrections_applied}
              </p>
            </div>
            <div>
              <p className="text-muted-foreground">Labels Changed</p>
              <p className="text-lg font-semibold text-blue-600">
                {result.labels_changed}
              </p>
            </div>
            <div>
              <p className="text-muted-foreground">Samples Rejected</p>
              <p className="text-lg font-semibold text-red-600">
                {result.samples_rejected}
              </p>
            </div>
          </div>

          <div className="pt-4">
            <Button
              variant="outline"
              onClick={() => {
                setResult(null);
                setPreview(null);
              }}
              className="w-full"
            >
              Close
            </Button>
          </div>
        </div>
      )}

      {/* Instructions */}
      {!preview && !result && (
        <div className="text-sm text-muted-foreground space-y-2 p-4 bg-muted/50 rounded-lg">
          <p className="font-medium">Workflow:</p>
          <ol className="list-decimal list-inside space-y-1 ml-2">
            <li>Click "Preview" to see what changes will be made</li>
            <li>Review the preview to ensure corrections are as expected</li>
            <li>Click "Apply Corrections" to update dataset labels</li>
            <li>Proceed to retrain the model on corrected data</li>
          </ol>
          <p className="text-xs italic mt-2">
            Note: Original labels are preserved for evaluation purposes
          </p>
        </div>
      )}
    </Card>
  );
}