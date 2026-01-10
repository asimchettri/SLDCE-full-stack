import { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { 
  Lightbulb, 
  ChevronRight, 
  Clock,
  CheckCircle,
  XCircle,
  Edit
} from 'lucide-react';
import type { Suggestion } from '@/types/suggestion';
import { SuggestionDetailsDialog } from './SuggestionDetailsDialog';
import { SuggestionReviewActions } from './SuggestionReviewActions'

interface SuggestionCardProps {
  suggestion: Suggestion;
  onStatusUpdate?: () => void;
}

export function SuggestionCard({ suggestion, onStatusUpdate }: SuggestionCardProps) {
  const [detailsOpen, setDetailsOpen] = useState(false);
  const [showActions, setShowActions] = useState(false);

  const getStatusConfig = (status: string) => {
    switch (status) {
      case 'accepted':
        return {
          icon: CheckCircle,
          color: 'bg-green-100 text-green-800 border-green-200',
          label: 'Accepted'
        };
      case 'rejected':
        return {
          icon: XCircle,
          color: 'bg-red-100 text-red-800 border-red-200',
          label: 'Rejected'
        };
      case 'modified':
        return {
          icon: Edit,
          color: 'bg-blue-100 text-blue-800 border-blue-200',
          label: 'Modified'
        };
      default:
        return {
          icon: Clock,
          color: 'bg-yellow-100 text-yellow-800 border-yellow-200',
          label: 'Pending'
        };
    }
  };

  const getConfidenceColor = (confidence: number) => {
    if (confidence >= 0.9) return 'text-green-600';
    if (confidence >= 0.7) return 'text-blue-600';
    return 'text-orange-600';
  };

  const statusConfig = getStatusConfig(suggestion.status);
  const StatusIcon = statusConfig.icon;

  return (
    <>
      <Card className={`hover:shadow-md transition-all ${
        suggestion.status === 'pending' ? 'border-l-4 border-l-orange-400' : ''
      }`}>
        <CardHeader className="pb-3">
          <div className="flex items-start justify-between">
            <div className="flex items-center gap-2">
              <Lightbulb className="h-5 w-5 text-yellow-500" />
              <CardTitle className="text-base">
                Suggestion #{suggestion.id}
              </CardTitle>
            </div>
            <Badge className={statusConfig.color}>
              <StatusIcon className="h-3 w-3 mr-1" />
              {statusConfig.label}
            </Badge>
          </div>
        </CardHeader>

        <CardContent>
          <div className="space-y-3">
            {/* Label Change */}
            <div className="bg-gray-50 p-3 rounded-lg">
              <div className="text-xs text-gray-600 mb-2">Suggested Change</div>
              <div className="flex items-center justify-between">
                <div className="text-center">
                  <div className="text-xs text-gray-500">Current</div>
                  <Badge variant="outline" className="mt-1">
                    Class {suggestion.detection_id}
                  </Badge>
                </div>
                <div className="text-gray-400">→</div>
                <div className="text-center">
                  <div className="text-xs text-gray-500">Suggested</div>
                  <Badge className="mt-1 bg-green-100 text-green-800">
                    Class {suggestion.suggested_label}
                  </Badge>
                </div>
              </div>
            </div>

            {/* Confidence */}
            <div className="flex items-center justify-between">
              <span className="text-sm text-gray-600">Confidence</span>
              <span className={`text-sm font-bold ${getConfidenceColor(suggestion.confidence)}`}>
                {(suggestion.confidence * 100).toFixed(1)}%
              </span>
            </div>

            {/* Reason Preview */}
            <div className="text-xs text-gray-600 bg-blue-50 p-2 rounded border border-blue-100">
              <span className="font-semibold">Reason: </span>
              {suggestion.reason.length > 80 
                ? `${suggestion.reason.substring(0, 80)}...` 
                : suggestion.reason
              }
            </div>

            {/* Review Notes (if reviewed) */}
            {suggestion.reviewed_at && suggestion.reviewer_notes && (
              <div className="text-xs text-gray-600 bg-gray-50 p-2 rounded border">
                <span className="font-semibold">Review Notes: </span>
                {suggestion.reviewer_notes}
              </div>
            )}

            {/* Action Buttons */}
            <div className="pt-2 border-t space-y-2">
              {suggestion.status === 'pending' ? (
                <>
                  <Button
                    variant="outline"
                    size="sm"
                    className="w-full"
                    onClick={() => setShowActions(!showActions)}
                  >
                    {showActions ? 'Hide Actions' : 'Review Suggestion'}
                  </Button>
                  
                  {showActions && (
                    <SuggestionReviewActions
                      suggestion={suggestion}
                      onComplete={() => {
                        setShowActions(false);
                        onStatusUpdate?.();
                      }}
                    />
                  )}
                </>
              ) : (
                <div className="text-xs text-gray-500 text-center">
                  Reviewed on {new Date(suggestion.reviewed_at!).toLocaleDateString()}
                </div>
              )}

              <Button
                variant="ghost"
                size="sm"
                className="w-full"
                onClick={() => setDetailsOpen(true)}
              >
                View Full Details
                <ChevronRight className="ml-2 h-4 w-4" />
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Details Dialog */}
      <SuggestionDetailsDialog
        suggestionId={suggestion.id}
        open={detailsOpen}
        onOpenChange={setDetailsOpen}
        onStatusUpdate={onStatusUpdate}
      />
    </>
  );
}