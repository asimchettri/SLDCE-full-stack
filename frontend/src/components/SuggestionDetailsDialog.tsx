import { useQuery } from '@tanstack/react-query';
import { suggestionAPI } from '@/services/api';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { 
  Lightbulb, 
  TrendingUp, 
  AlertTriangle,
  CheckCircle,
  XCircle,
  Edit,
  Clock
} from 'lucide-react';
import { SuggestionReviewActions } from './SuggestionReviewActions';

interface SuggestionDetailsDialogProps {
  suggestionId: number;
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onStatusUpdate?: () => void;
}

export function SuggestionDetailsDialog({
  suggestionId,
  open,
  onOpenChange,
  onStatusUpdate
}: SuggestionDetailsDialogProps) {
  const { data: details, isLoading } = useQuery({
    queryKey: ['suggestion-details', suggestionId],
    queryFn: () => suggestionAPI.getDetails(suggestionId),
    enabled: open,
  });

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'accepted': return CheckCircle;
      case 'rejected': return XCircle;
      case 'modified': return Edit;
      default: return Clock;
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'accepted': return 'text-green-600';
      case 'rejected': return 'text-red-600';
      case 'modified': return 'text-blue-600';
      default: return 'text-yellow-600';
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-3xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <div className="flex items-center gap-2">
            <Lightbulb className="h-5 w-5 text-yellow-500" />
            <DialogTitle>Suggestion #{suggestionId} - Full Details</DialogTitle>
          </div>
          <DialogDescription>
            Complete information about this correction suggestion
          </DialogDescription>
        </DialogHeader>

        {isLoading ? (
          <div className="flex items-center justify-center py-12">
            <div className="text-gray-500">Loading details...</div>
          </div>
        ) : details ? (
          <div className="space-y-4 pb-4">
            {/* Status Badge */}
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                {(() => {
                  const StatusIcon = getStatusIcon(details.status);
                  return <StatusIcon className={`h-5 w-5 ${getStatusColor(details.status)}`} />;
                })()}
                <span className="text-sm font-semibold capitalize">{details.status}</span>
              </div>
              {details.reviewed_at && (
                <span className="text-xs text-gray-500">
                  Reviewed: {new Date(details.reviewed_at).toLocaleString()}
                </span>
              )}
            </div>

            {/* Label Comparison */}
            <Card>
              <CardHeader>
                <CardTitle className="text-base">Label Analysis</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-gray-600">Current Label:</span>
                    <Badge variant="outline">Class {details.current_label}</Badge>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-gray-600">Suggested Label:</span>
                    <Badge className="bg-green-100 text-green-800">
                      Class {details.suggested_label}
                    </Badge>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-gray-600">Model Prediction:</span>
                    <Badge className="bg-blue-100 text-blue-800">
                      Class {details.predicted_label}
                    </Badge>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-gray-600">Original Label:</span>
                    <Badge variant="secondary">Class {details.original_label}</Badge>
                  </div>
                </div>

                {details.current_label !== details.original_label && (
                  <div className="mt-3 p-2 bg-orange-50 border border-orange-200 rounded text-sm text-orange-800">
                    <AlertTriangle className="inline h-4 w-4 mr-1" />
                    This sample has a noisy label (current ≠ original)
                  </div>
                )}
              </CardContent>
            </Card>

            {/* Detection Scores */}
            {details.detection_info && (
              <Card>
                <CardHeader>
                  <CardTitle className="text-base">Detection Signals</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-3">
                    <div>
                      <div className="flex items-center justify-between mb-1">
                        <span className="text-sm text-gray-600">Confidence Score</span>
                        <span className="text-sm font-semibold text-blue-600">
                          {(details.detection_info.confidence_score * 100).toFixed(1)}%
                        </span>
                      </div>
                      <div className="w-full bg-gray-200 rounded-full h-2">
                        <div
                          className="bg-blue-600 h-2 rounded-full transition-all"
                          style={{ width: `${details.detection_info.confidence_score * 100}%` }}
                        />
                      </div>
                    </div>

                    <div>
                      <div className="flex items-center justify-between mb-1">
                        <span className="text-sm text-gray-600">Anomaly Score</span>
                        <span className="text-sm font-semibold text-purple-600">
                          {(details.detection_info.anomaly_score * 100).toFixed(1)}%
                        </span>
                      </div>
                      <div className="w-full bg-gray-200 rounded-full h-2">
                        <div
                          className="bg-purple-600 h-2 rounded-full transition-all"
                          style={{ width: `${details.detection_info.anomaly_score * 100}%` }}
                        />
                      </div>
                    </div>

                    <div>
                      <div className="flex items-center justify-between mb-1">
                        <span className="text-sm text-gray-600">Priority Score</span>
                        <span className="text-sm font-semibold text-orange-600">
                          {(details.detection_info.priority_score * 100).toFixed(1)}%
                        </span>
                      </div>
                      <div className="w-full bg-gray-200 rounded-full h-2">
                        <div
                          className="bg-orange-600 h-2 rounded-full transition-all"
                          style={{ width: `${details.detection_info.priority_score * 100}%` }}
                        />
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>
            )}

            {/* Reasoning */}
            <Card className="bg-blue-50 border-blue-200">
              <CardHeader>
                <CardTitle className="text-base text-blue-900">
                  Why This Suggestion?
                </CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-sm text-blue-800">{details.reason}</p>
                
                <div className="mt-3 flex items-center gap-2">
                  <span className="text-xs font-semibold text-blue-900">Confidence:</span>
                  <Badge className="bg-blue-200 text-blue-900">
                    {(details.confidence * 100).toFixed(1)}%
                  </Badge>
                </div>
              </CardContent>
            </Card>

            {/* Sample Features */}
            {details.sample_features && details.sample_features.length > 0 && (
              <Card>
                <CardHeader>
                  <CardTitle className="text-base">Sample Features</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-4 gap-2">
                    {details.sample_features.map((feature: number, idx: number) => (
                      <div key={idx} className="bg-gray-50 p-2 rounded text-center">
                        <div className="text-xs text-gray-600">F{idx + 1}</div>
                        <div className="text-sm font-semibold">{feature.toFixed(2)}</div>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>
            )}

            {/* Review Notes */}
            {details.reviewer_notes && (
              <Card className="bg-gray-50">
                <CardHeader>
                  <CardTitle className="text-base">Review Notes</CardTitle>
                </CardHeader>
                <CardContent>
                  <p className="text-sm text-gray-700">{details.reviewer_notes}</p>
                </CardContent>
              </Card>
            )}

            {/* Review Actions (if pending) */}
            {details.status === 'pending' && (
              <Card>
                <CardHeader>
                  <CardTitle className="text-base">Review This Suggestion</CardTitle>
                </CardHeader>
                <CardContent>
                  <SuggestionReviewActions
                    suggestion={details}
                    onComplete={() => {
                      onStatusUpdate?.();
                      onOpenChange(false);
                    }}
                  />
                </CardContent>
              </Card>
            )}

            {/* Recommendation */}
            <Card className="bg-green-50 border-green-200">
              <CardContent className="pt-4">
                <div className="flex items-start gap-3">
                  <TrendingUp className="h-5 w-5 text-green-600 mt-0.5 shrink-0" />
                  <div>
                    <h4 className="font-semibold text-green-900">System Recommendation</h4>
                    <p className="text-sm text-green-800 mt-1">
                      Based on {details.detection_info ? 
                        `confidence (${(details.detection_info.confidence_score * 100).toFixed(1)}%) and anomaly detection (${(details.detection_info.anomaly_score * 100).toFixed(1)}%)` 
                        : 'multiple detection signals'
                      }, this suggestion has a high likelihood of being correct. 
                      Consider accepting or providing feedback.
                    </p>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        ) : (
          <div className="text-center py-8 text-gray-500">
            No details available
          </div>
        )}
      </DialogContent>
    </Dialog>
  );
}