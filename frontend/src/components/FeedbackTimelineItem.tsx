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
  HelpCircle,
} from 'lucide-react';
import type { Feedback } from '@/types/feedback';

interface FeedbackTimelineItemProps {
  feedback: Feedback;
  showDetails?: boolean;
}

export function FeedbackTimelineItem({
  feedback,
  showDetails = false,
}: FeedbackTimelineItemProps) {
  const [expanded, setExpanded] = useState(showDetails);

  const getActionConfig = (action: string) => {
    switch (action) {
      case 'approve':
        return {
          icon: CheckCircle,
          color: 'text-green-600',
          bgColor: 'bg-green-50',
          borderColor: 'border-green-200',
          label: 'Accepted',
          badgeClass: 'bg-green-100 text-green-800',
        };
      case 'reject':
        return {
          icon: XCircle,
          color: 'text-red-600',
          bgColor: 'bg-red-50',
          borderColor: 'border-red-200',
          label: 'Rejected',
          badgeClass: 'bg-red-100 text-red-800',
        };
      case 'modify':
        return {
          icon: Edit,
          color: 'text-blue-600',
          bgColor: 'bg-blue-50',
          borderColor: 'border-blue-200',
          label: 'Modified',
          badgeClass: 'bg-blue-100 text-blue-800',
        };
      case 'uncertain':
        return {
          icon: HelpCircle,
          color: 'text-amber-600',
          bgColor: 'bg-amber-50',
          borderColor: 'border-amber-200',
          label: 'Uncertain',
          badgeClass: 'bg-amber-100 text-amber-800',
        };
      default:
        return {
          icon: Clock,
          color: 'text-gray-600',
          bgColor: 'bg-gray-50',
          borderColor: 'border-gray-200',
          label: 'Unknown',
          badgeClass: 'bg-gray-100 text-gray-800',
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
      year: date.getFullYear() !== now.getFullYear() ? 'numeric' : undefined,
    });
  };

  const formatTime = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleTimeString('en-US', {
      hour: 'numeric',
      minute: '2-digit',
      hour12: true,
    });
  };

  return (
    <div className="relative">
      {/* Timeline Dot */}
      <div className="absolute left-0 top-0 w-8 flex justify-center">
        <div
          className={`w-3 h-3 rounded-full ${config.bgColor} border-2 ${config.borderColor} mt-6`}
        />
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

        <Card
          className={`${config.borderColor} border-l-4 hover:shadow-md transition-shadow`}
        >
          <CardContent className="pt-4">
            {/* Header */}
            <div className="flex items-start justify-between mb-3">
              <div className="flex items-center gap-3">
                <ActionIcon className={`h-5 w-5 ${config.color}`} />
                <div className="flex items-center gap-2">
                  <Badge className={config.badgeClass}>{config.label}</Badge>
                  <span className="text-sm text-gray-600">
                    Sample #{feedback.sample_id}
                  </span>
                </div>
              </div>

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

            {/* Final Label — always available on base Feedback */}
            <div className="flex items-center gap-2 mb-3 text-sm">
              <Tag className="h-4 w-4 text-gray-500" />
              <span className="text-gray-600">
                Final label:{' '}
                <span className={`font-semibold ${config.color}`}>
                  Class {feedback.final_label}
                </span>
              </span>
            </div>

            {/* Expanded Details — only fields that exist on base Feedback */}
            {expanded && (
              <div className="mt-4 pt-4 border-t space-y-3">
                <div className="flex items-center gap-2 text-sm text-gray-600">
                  <span className="font-semibold">Iteration:</span>
                  <Badge variant="outline">{feedback.iteration}</Badge>
                </div>

                {feedback.review_time_seconds != null && (
                  <div className="text-xs text-gray-500">
                    Review time: {feedback.review_time_seconds.toFixed(1)}s
                  </div>
                )}

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