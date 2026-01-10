import { useState } from 'react';
import { Card, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { 
  CheckCircle, 
  XCircle, 
  Edit, 
  ChevronDown, 
  ChevronUp,
  Clock,
  Tag,
  
} from 'lucide-react';
import type { FeedbackWithDetails } from '@/types/feedback';

interface FeedbackTimelineItemProps {
  feedback: FeedbackWithDetails;
  showDetails?: boolean;
}

export function FeedbackTimelineItem({ 
  feedback, 
  showDetails = false 
}: FeedbackTimelineItemProps) {
  const [expanded, setExpanded] = useState(showDetails);

  const getActionConfig = (action: string) => {
    switch (action) {
      case 'accept':
        return {
          icon: CheckCircle,
          color: 'text-green-600',
          bgColor: 'bg-green-50',
          borderColor: 'border-green-200',
          label: 'Accepted',
          badgeClass: 'bg-green-100 text-green-800'
        };
      case 'reject':
        return {
          icon: XCircle,
          color: 'text-red-600',
          bgColor: 'bg-red-50',
          borderColor: 'border-red-200',
          label: 'Rejected',
          badgeClass: 'bg-red-100 text-red-800'
        };
      case 'modify':
        return {
          icon: Edit,
          color: 'text-blue-600',
          bgColor: 'bg-blue-50',
          borderColor: 'border-blue-200',
          label: 'Modified',
          badgeClass: 'bg-blue-100 text-blue-800'
        };
      default:
        return {
          icon: Clock,
          color: 'text-gray-600',
          bgColor: 'bg-gray-50',
          borderColor: 'border-gray-200',
          label: 'Unknown',
          badgeClass: 'bg-gray-100 text-gray-800'
        };
    }
  };

  const config = getActionConfig(feedback.action);
  const ActionIcon = config.icon;
  
  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMs / 3600000);
    const diffDays = Math.floor(diffMs / 86400000);

    if (diffMins < 1) return 'Just now';
    if (diffMins < 60) return `${diffMins} minute${diffMins > 1 ? 's' : ''} ago`;
    if (diffHours < 24) return `${diffHours} hour${diffHours > 1 ? 's' : ''} ago`;
    if (diffDays < 7) return `${diffDays} day${diffDays > 1 ? 's' : ''} ago`;
    
    return date.toLocaleDateString('en-US', { 
      month: 'short', 
      day: 'numeric', 
      year: date.getFullYear() !== now.getFullYear() ? 'numeric' : undefined 
    });
  };

  const formatTime = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleTimeString('en-US', { 
      hour: 'numeric', 
      minute: '2-digit',
      hour12: true 
    });
  };

  return (
    <div className="relative">
      {/* Timeline Dot */}
      <div className="absolute left-0 top-0 w-8 flex justify-center">
        <div className={`w-3 h-3 rounded-full ${config.bgColor} border-2 ${config.borderColor} mt-6`} />
      </div>

      {/* Timeline Line */}
      <div className="absolute left-0 top-0 w-8 flex justify-center">
        <div className="w-0.5 h-full bg-gray-200 -z-10" />
      </div>

      {/* Content Card */}
      <div className="ml-12 mb-6">
        {/* Timestamp */}
        <div className="flex items-center gap-2 mb-2 text-sm text-gray-500">
          <Clock className="h-3 w-3" />
          <span>{formatDate(feedback.created_at)}</span>
          <span className="text-gray-400">•</span>
          <span>{formatTime(feedback.created_at)}</span>
        </div>

        <Card className={`${config.borderColor} border-l-4 hover:shadow-md transition-shadow`}>
          <CardContent className="pt-4">
            {/* Header */}
            <div className="flex items-start justify-between mb-3">
              <div className="flex items-center gap-3">
                <ActionIcon className={`h-5 w-5 ${config.color}`} />
                <div>
                  <div className="flex items-center gap-2">
                    <Badge className={config.badgeClass}>
                      {config.label}
                    </Badge>
                    <span className="text-sm text-gray-600">
                      Sample #{feedback.sample_id}
                    </span>
                  </div>
                </div>
              </div>
              
              {/* Expand/Collapse Button */}
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setExpanded(!expanded)}
              >
                {expanded ? (
                  <ChevronUp className="h-4 w-4" />
                ) : (
                  <ChevronDown className="h-4 w-4" />
                )}
              </Button>
            </div>

            {/* Label Change Summary */}
            <div className="flex items-center gap-2 mb-3 text-sm">
              <Tag className="h-4 w-4 text-gray-500" />
              <span className="text-gray-600">
                {feedback.current_label !== undefined && (
                  <>
                    Current: <span className="font-semibold">Class {feedback.current_label}</span>
                  </>
                )}
                {feedback.suggested_label !== undefined && (
                  <>
                    {' → '}Suggested: <span className="font-semibold">Class {feedback.suggested_label}</span>
                  </>
                )}
                {' → '}Final: <span className={`font-semibold ${config.color}`}>
                  Class {feedback.final_label}
                </span>
              </span>
            </div>

            {/* Confidence Score (if available) */}
            {feedback.confidence_score !== undefined && (
              <div className="mb-3">
                <div className="flex items-center justify-between text-xs text-gray-600 mb-1">
                  <span>Confidence</span>
                  <span className="font-semibold">
                    {(feedback.confidence_score * 100).toFixed(1)}%
                  </span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-1.5">
                  <div
                    className={`h-1.5 rounded-full transition-all ${
                      feedback.confidence_score >= 0.8 ? 'bg-green-500' :
                      feedback.confidence_score >= 0.6 ? 'bg-blue-500' :
                      'bg-orange-500'
                    }`}
                    style={{ width: `${feedback.confidence_score * 100}%` }}
                  />
                </div>
              </div>
            )}

            {/* Expanded Details */}
            {expanded && (
              <div className="mt-4 pt-4 border-t space-y-3">
                {/* Detection Scores */}
                {feedback.detection_info && (
                  <div className="grid grid-cols-3 gap-2 text-xs">
                    <div className="bg-blue-50 p-2 rounded text-center">
                      <div className="text-gray-600">Confidence</div>
                      <div className="font-semibold text-blue-700">
                        {(feedback.detection_info.confidence_score * 100).toFixed(1)}%
                      </div>
                    </div>
                    <div className="bg-purple-50 p-2 rounded text-center">
                      <div className="text-gray-600">Anomaly</div>
                      <div className="font-semibold text-purple-700">
                        {(feedback.detection_info.anomaly_score * 100).toFixed(1)}%
                      </div>
                    </div>
                    <div className="bg-orange-50 p-2 rounded text-center">
                      <div className="text-gray-600">Priority</div>
                      <div className="font-semibold text-orange-700">
                        {(feedback.detection_info.priority_score * 100).toFixed(1)}%
                      </div>
                    </div>
                  </div>
                )}

                {/* Iteration Info */}
                <div className="flex items-center gap-2 text-sm text-gray-600">
                  <span className="font-semibold">Iteration:</span>
                  <Badge variant="outline">{feedback.iteration}</Badge>
                </div>

                {/* IDs for Reference */}
                <div className="text-xs text-gray-500 space-y-1">
                  <div>Feedback ID: {feedback.id}</div>
                  <div>Suggestion ID: {feedback.suggestion_id}</div>
                  <div>Sample ID: {feedback.sample_id}</div>
                </div>
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}