import { useQuery } from '@tanstack/react-query';
import { feedbackAPI } from '@/services/api';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { TrendingUp, Brain, CheckCircle, XCircle, Edit } from 'lucide-react';


interface FeedbackAnalyticsProps {
  datasetId: number;
  iteration?: number;
}

export function FeedbackAnalytics({ datasetId, iteration = 1 }: FeedbackAnalyticsProps) {
  const { data: stats } = useQuery({
    queryKey: ['feedback-stats', datasetId],
    queryFn: () => feedbackAPI.getStats(datasetId),
    enabled: !!datasetId,
  });

  const { data: patterns } = useQuery({
    queryKey: ['feedback-patterns', datasetId, iteration],
    queryFn: () => feedbackAPI.getPatterns(datasetId, iteration),
    enabled: !!datasetId,
  });

  if (!stats || stats.total_feedback === 0) {
    return null; // Don't show if no feedback yet
  }

  return (
    <div className="space-y-4">
      {/* Title */}
      <div className="flex items-center gap-2">
        <Brain className="h-5 w-5 text-purple-600" />
        <h3 className="text-lg font-semibold">Learning Analytics</h3>
        <span className="text-xs text-gray-500">(Phase 2 Memory Data)</span>
      </div>

      {/* Stats Grid */}
      <div className="grid gap-4 md:grid-cols-4">
        {/* Total Feedback */}
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-gray-600">
              Total Reviews
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats.total_feedback}</div>
            <p className="text-xs text-gray-500">Collected</p>
          </CardContent>
        </Card>

        {/* Accepted */}
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-gray-600 flex items-center gap-2">
              <CheckCircle className="h-4 w-4 text-green-600" />
              Accepted
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-green-600">{stats.accept_count}</div>
            <p className="text-xs text-gray-500">
              {((stats.accept_count / stats.total_feedback) * 100).toFixed(1)}%
            </p>
          </CardContent>
        </Card>

        {/* Rejected */}
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-gray-600 flex items-center gap-2">
              <XCircle className="h-4 w-4 text-red-600" />
              Rejected
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-red-600">{stats.reject_count}</div>
            <p className="text-xs text-gray-500">
              {((stats.reject_count / stats.total_feedback) * 100).toFixed(1)}%
            </p>
          </CardContent>
        </Card>

        {/* Modified */}
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-gray-600 flex items-center gap-2">
              <Edit className="h-4 w-4 text-blue-600" />
              Modified
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-blue-600">{stats.modify_count}</div>
            <p className="text-xs text-gray-500">
              {((stats.modify_count / stats.total_feedback) * 100).toFixed(1)}%
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Patterns Analysis */}
      {patterns && (
        <Card className="bg-gradient-to-r from-purple-50 to-pink-50 border-purple-200">
          <CardHeader>
            <CardTitle className="text-base flex items-center gap-2">
              <Brain className="h-5 w-5 text-purple-600" />
              Learning Insights (Iteration {iteration})
            </CardTitle>
            <CardDescription>
              Pattern analysis for Phase 2 memory system
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-3">
            <div className="grid grid-cols-2 gap-4">
              {/* Confidence Patterns */}
              <div className="bg-white p-3 rounded-lg border">
                <div className="text-xs font-semibold text-gray-600 mb-2">
                  High Confidence (≥80%)
                </div>
                <div className="text-2xl font-bold text-green-600">
                  {patterns.high_confidence_acceptance_rate.toFixed(1)}%
                </div>
                <p className="text-xs text-gray-500">Acceptance Rate</p>
              </div>

              <div className="bg-white p-3 rounded-lg border">
                <div className="text-xs font-semibold text-gray-600 mb-2">
                  Low Confidence (&lt;80%)
                </div>
                <div className="text-2xl font-bold text-orange-600">
                  {patterns.low_confidence_acceptance_rate.toFixed(1)}%
                </div>
                <p className="text-xs text-gray-500">Acceptance Rate</p>
              </div>
            </div>

            {/* Class Patterns */}
            {(patterns.most_accepted_class !== null || patterns.most_rejected_class !== null) && (
              <div className="grid grid-cols-2 gap-4 pt-3 border-t">
                {patterns.most_accepted_class !== null && (
                  <div className="text-center">
                    <div className="text-xs text-gray-600 mb-1">Most Accepted</div>
                    <div className="text-xl font-bold text-green-600">
                      Class {patterns.most_accepted_class}
                    </div>
                  </div>
                )}
                {patterns.most_rejected_class !== null && (
                  <div className="text-center">
                    <div className="text-xs text-gray-600 mb-1">Most Rejected</div>
                    <div className="text-xl font-bold text-red-600">
                      Class {patterns.most_rejected_class}
                    </div>
                  </div>
                )}
              </div>
            )}

            {/* Learning Note */}
            <div className="pt-3 border-t">
              <p className="text-xs text-purple-700">
                <TrendingUp className="inline h-3 w-3 mr-1" />
                <strong>Phase 2 Insight:</strong> System learns optimal thresholds from these patterns.
                {patterns.high_confidence_acceptance_rate > patterns.low_confidence_acceptance_rate + 20 && (
                  <span className="ml-1">
                    High confidence suggestions are significantly more reliable ({patterns.high_confidence_acceptance_rate.toFixed(0)}% vs {patterns.low_confidence_acceptance_rate.toFixed(0)}%).
                  </span>
                )}
              </p>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Overall Acceptance Rate */}
      <Card className="bg-gradient-to-r from-green-50 to-blue-50 border-green-200">
        <CardContent className="pt-6">
          <div className="flex items-center justify-between">
            <div>
              <div className="text-sm font-semibold text-gray-700">Overall Acceptance Rate</div>
              <div className="text-xs text-gray-600 mt-1">
                (Accepted + Modified) / Total Reviews
              </div>
            </div>
            <div className="text-4xl font-bold text-green-600">
              {stats.acceptance_rate.toFixed(1)}%
            </div>
          </div>
          <div className="mt-3 w-full bg-gray-200 rounded-full h-2">
            <div
              className="bg-gradient-to-r from-green-500 to-blue-500 h-2 rounded-full transition-all"
              style={{ width: `${stats.acceptance_rate}%` }}
            />
          </div>
        </CardContent>
      </Card>
    </div>
  );
}