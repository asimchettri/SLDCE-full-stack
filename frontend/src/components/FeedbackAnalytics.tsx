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
            <div className="text-2xl font-bold text-green-600">{stats.accepted}</div>
            <p className="text-xs text-gray-500">
              {stats.total_feedback > 0
                ? ((stats.accepted / stats.total_feedback) * 100).toFixed(1)
                : '0.0'}%
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
            <div className="text-2xl font-bold text-red-600">{stats.rejected}</div>
            <p className="text-xs text-gray-500">
              {stats.total_feedback > 0
                ? ((stats.rejected / stats.total_feedback) * 100).toFixed(1)
                : '0.0'}%
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
            <div className="text-2xl font-bold text-blue-600">{stats.modified}</div>
            <p className="text-xs text-gray-500">
              {stats.total_feedback > 0
                ? ((stats.modified / stats.total_feedback) * 100).toFixed(1)
                : '0.0'}%
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Patterns Analysis */}
      {patterns && patterns.patterns_found > 0 && (
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
          <CardContent className="space-y-4">
            {/* Confidence Patterns */}
            {patterns.acceptance_by_confidence &&
              Object.keys(patterns.acceptance_by_confidence).length > 0 && (
                <div>
                  <div className="text-xs font-semibold text-gray-700 mb-3">
                    Acceptance Rate by Confidence Level
                  </div>
                  <div className="grid grid-cols-3 gap-3">
                    {Object.entries(patterns.acceptance_by_confidence)
                      .sort(([a], [b]) => parseInt(b) - parseInt(a)) // Sort descending
                      .map(([range, data]) => (
                        <div key={range} className="bg-white p-3 rounded-lg border shadow-sm">
                          <div className="text-xs font-medium text-gray-600 mb-1">
                            Confidence {range}
                          </div>
                          <div className="text-2xl font-bold text-green-600">
                            {data.acceptance_rate.toFixed(1)}%
                          </div>
                          <p className="text-xs text-gray-500 mt-1">
                            {data.accepted}/{data.total} accepted
                          </p>
                        </div>
                      ))}
                  </div>
                </div>
              )}

            {/* Priority Patterns */}
            {patterns.acceptance_by_priority &&
              Object.keys(patterns.acceptance_by_priority).length > 0 && (
                <div className="pt-3 border-t">
                  <div className="text-xs font-semibold text-gray-700 mb-3">
                    Acceptance Rate by Priority Level
                  </div>
                  <div className="grid grid-cols-3 gap-3">
                    {['high', 'medium', 'low']
                      .filter((priority) => patterns.acceptance_by_priority![priority])
                      .map((priority) => {
                        const data = patterns.acceptance_by_priority![priority];
                        return (
                          <div
                            key={priority}
                            className="bg-white p-3 rounded-lg border shadow-sm"
                          >
                            <div className="text-xs font-medium text-gray-600 mb-1 capitalize">
                              {priority} Priority
                            </div>
                            <div
                              className={`text-2xl font-bold ${
                                priority === 'high'
                                  ? 'text-red-600'
                                  : priority === 'medium'
                                  ? 'text-orange-600'
                                  : 'text-yellow-600'
                              }`}
                            >
                              {data.acceptance_rate.toFixed(1)}%
                            </div>
                            <p className="text-xs text-gray-500 mt-1">
                              {data.accepted}/{data.total} accepted
                            </p>
                          </div>
                        );
                      })}
                  </div>
                </div>
              )}

            {/* Insights from Backend */}
            {patterns.insights && patterns.insights.length > 0 && (
              <div className="pt-3 border-t">
                <div className="text-xs font-semibold text-gray-700 mb-2">
                  Key Learning Insights
                </div>
                <ul className="space-y-2">
                  {patterns.insights.map((insight, idx) => (
                    <li
                      key={idx}
                      className="text-sm text-purple-700 flex items-start gap-2 bg-white p-2 rounded border border-purple-100"
                    >
                      <TrendingUp className="h-4 w-4 mt-0.5 flex-shrink-0 text-purple-600" />
                      <span>{insight}</span>
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {/* Learning Summary */}
            <div className="pt-3 border-t bg-white p-3 rounded-lg">
              <p className="text-xs text-purple-700">
                <Brain className="inline h-4 w-4 mr-1" />
                <strong>Phase 2 Memory:</strong> System has learned from{' '}
                <span className="font-semibold">{patterns.patterns_found}</span> feedback
                samples. These patterns will be used to improve detection accuracy in future
                iterations.
              </p>
            </div>
          </CardContent>
        </Card>
      )}

      {/* No Patterns Message */}
      {patterns && patterns.patterns_found === 0 && (
        <Card className="border-dashed border-2">
          <CardContent className="pt-6 pb-6">
            <div className="text-center">
              <Brain className="h-8 w-8 mx-auto text-gray-400 mb-2" />
              <p className="text-sm text-gray-600 font-medium">No Learning Patterns Yet</p>
              <p className="text-xs text-gray-500 mt-1">
                Review some suggestions to generate insights for the memory system
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
              <div className="text-sm font-semibold text-gray-700">
                Overall Acceptance Rate
              </div>
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
              style={{ width: `${Math.min(stats.acceptance_rate, 100)}%` }}
            />
          </div>
        </CardContent>
      </Card>
    </div>
  );
}