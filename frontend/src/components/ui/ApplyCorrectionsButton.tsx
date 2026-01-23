import { useState } from 'react';
import { useMutation } from '@tanstack/react-query';
import { correctionsAPI } from '@/services/api';
import { Button } from '@/components/ui/button';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from '@/components/ui/dialog';
import { Card, CardContent } from '@/components/ui/card';
import { 
  Save, 
  CheckCircle, 
  AlertTriangle, 
  Loader2,
  ArrowRight,
  FileCheck
} from 'lucide-react';
import { toast } from 'sonner'; 

interface ApplyCorrectionsButtonProps {
  datasetId: number;
  iteration?: number;
  onSuccess?: () => void;
  disabled?: boolean;
}

export function ApplyCorrectionsButton({
  datasetId,
  iteration = 1,
  onSuccess,
  disabled = false,
}: ApplyCorrectionsButtonProps) {
  const [previewOpen, setPreviewOpen] = useState(false);
  const [previewData, setPreviewData] = useState<any>(null);

  //  Preview mutation
  const previewMutation = useMutation({
    mutationFn: () => correctionsAPI.preview(datasetId, iteration),
    onSuccess: (data) => {
      setPreviewData(data);
      if (data.total_changes === 0) {
        toast.info('No corrections to apply', {
          description: 'All accepted feedback has already been applied.',
        });
      } else {
        setPreviewOpen(true);
      }
    },
    onError: (error: any) => {
      toast.error('Failed to load preview', {
        description: error.response?.data?.detail || 'An error occurred',
      });
    },
  });

  //  Apply mutation
  const applyMutation = useMutation({
    mutationFn: () => correctionsAPI.apply(datasetId, iteration),
    onSuccess: (data) => {
      setPreviewOpen(false);
      toast.success('Corrections Applied Successfully! 🎉', {
        description: `${data.labels_changed} labels updated across ${data.corrections_applied} samples.`,
      });
      onSuccess?.();
    },
    onError: (error: any) => {
      toast.error('Failed to apply corrections', {
        description: error.response?.data?.detail || 'An error occurred',
      });
    },
  });

  const handlePreview = () => {
    previewMutation.mutate();
  };

  const handleApply = () => {
    applyMutation.mutate();
  };

  return (
    <>
      {/* Main Button */}
      <Button
        onClick={handlePreview}
        disabled={disabled || previewMutation.isPending}
        size="lg"
        className="bg-green-600 hover:bg-green-700"
      >
        {previewMutation.isPending ? (
          <>
            <Loader2 className="mr-2 h-5 w-5 animate-spin" />
            Loading Preview...
          </>
        ) : (
          <>
            <Save className="mr-2 h-5 w-5" />
            Apply Corrections
          </>
        )}
      </Button>

      {/* Preview & Confirm Dialog */}
      <Dialog open={previewOpen} onOpenChange={setPreviewOpen}>
        <DialogContent className="sm:max-w-[600px]">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <FileCheck className="h-5 w-5 text-green-600" />
              Confirm Corrections
            </DialogTitle>
            <DialogDescription>
              Review the changes that will be applied to your dataset
            </DialogDescription>
          </DialogHeader>

          {previewData && (
            <div className="space-y-4">
              {/* Summary Stats */}
              <Card className="bg-blue-50 border-blue-200">
                <CardContent className="pt-6">
                  <div className="grid grid-cols-2 gap-4 text-center">
                    <div>
                      <div className="text-3xl font-bold text-blue-700">
                        {previewData.total_changes}
                      </div>
                      <div className="text-sm text-blue-600">Labels to Update</div>
                    </div>
                    <div>
                      <div className="text-3xl font-bold text-blue-700">
                        {previewData.dataset_id}
                      </div>
                      <div className="text-sm text-blue-600">Dataset ID</div>
                    </div>
                  </div>
                </CardContent>
              </Card>

              {/* Warning if many changes */}
              {previewData.total_changes > 50 && (
                <Card className="bg-orange-50 border-orange-200">
                  <CardContent className="pt-6">
                    <div className="flex items-start gap-3">
                      <AlertTriangle className="h-5 w-5 text-orange-600 shrink-0 mt-0.5" />
                      <div className="text-sm text-orange-800">
                        <p className="font-semibold">Large Update</p>
                        <p className="mt-1">
                          You're about to update {previewData.total_changes} labels. 
                          This action cannot be undone easily.
                        </p>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              )}

              {/* Sample Preview (first 5 changes) */}
              {previewData.changes && previewData.changes.length > 0 && (
                <div>
                  <h4 className="text-sm font-semibold mb-2 text-gray-700">
                    Sample Changes (showing first 5):
                  </h4>
                  <div className="space-y-2 max-h-[200px] overflow-y-auto">
                    {previewData.changes.slice(0, 5).map((change: any, idx: number) => (
                      <Card key={idx} className="border-l-4 border-l-green-500">
                        <CardContent className="py-3">
                          <div className="flex items-center justify-between text-sm">
                            <span className="text-gray-600">
                              Sample #{change.sample_id}
                            </span>
                            <div className="flex items-center gap-3">
                              <span className="font-mono text-red-600">
                                {change.old_label}
                              </span>
                              <ArrowRight className="h-4 w-4 text-gray-400" />
                              <span className="font-mono text-green-600 font-semibold">
                                {change.new_label}
                              </span>
                              <span className="text-xs text-gray-500 capitalize">
                                ({change.action})
                              </span>
                            </div>
                          </div>
                        </CardContent>
                      </Card>
                    ))}
                    {previewData.changes.length > 5 && (
                      <p className="text-xs text-gray-500 text-center pt-2">
                        + {previewData.changes.length - 5} more changes...
                      </p>
                    )}
                  </div>
                </div>
              )}

              {/* No Changes Message */}
              {previewData.total_changes === 0 && (
                <Card className="bg-gray-50">
                  <CardContent className="py-6 text-center text-gray-600">
                    <CheckCircle className="h-12 w-12 text-gray-400 mx-auto mb-2" />
                    <p>No changes to apply. All corrections are already applied!</p>
                  </CardContent>
                </Card>
              )}
            </div>
          )}

          <DialogFooter className="gap-2">
            <Button
              variant="outline"
              onClick={() => setPreviewOpen(false)}
              disabled={applyMutation.isPending}
            >
              Cancel
            </Button>
            <Button
              onClick={handleApply}
              disabled={
                !previewData ||
                previewData.total_changes === 0 ||
                applyMutation.isPending
              }
              className="bg-green-600 hover:bg-green-700"
            >
              {applyMutation.isPending ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Applying...
                </>
              ) : (
                <>
                  <CheckCircle className="mr-2 h-4 w-4" />
                  Confirm & Apply
                </>
              )}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </>
  );
}