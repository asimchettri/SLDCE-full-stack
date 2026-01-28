import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { 
  TrendingUp, 
  CheckCircle, 
  XCircle, 
  Edit, 
  BarChart3,
  Target,
  Brain
} from 'lucide-react';
import type { FeedbackStats } from '@/types/feedback';

interface FeedbackStatsDashboardProps {
  stats: FeedbackStats;
}

export function FeedbackStatsDashboard({ stats }: FeedbackStatsDashboardProps) {
  const getPercentage = (count: number) => {
    if (stats.total_feedback === 0) return 0;
    return ((count / stats.total_feedback) * 100).toFixed(1);
  };

  // Calculate positive rate (accept + modify)
  const positiveCount = stats.accepted + stats.modified;
  const positiveRate = stats.total_feedback > 0 
    ? ((positiveCount / stats.total_feedback) * 100).toFixed(1)
    : 0;

  return (
    <div className="space-y-4">
      {/* Title */}
      <div>
        <h3 className="text-lg font-semibold flex items-center gap-2">
          <BarChart3 className="h-5 w-5" />
          Feedback Statistics
        </h3>
        <p className="text-sm text-gray-500">Overall review decision patterns</p>
      </div>

      {/* Main Stats Grid */}
      <div className="grid gap-4 md:grid-cols-6">
        {/* Total Feedback */}
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-gray-600 flex items-center gap-2">
              <Target className="h-4 w-4" />
              Total
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold">{stats.total_feedback}</div>
            <p className="text-xs text-gray-500 mt-1">Reviews</p>
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
            <div className="text-3xl font-bold text-green-600">
              {stats.accepted}
            </div>
            <p className="text-xs text-gray-500 mt-1">
              {getPercentage(stats.accepted)}% of total
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
            <div className="text-3xl font-bold text-red-600">
              {stats. rejected}
            </div>
            <p className="text-xs text-gray-500 mt-1">
              {getPercentage(stats. rejected)}% of total
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
            <div className="text-3xl font-bold text-blue-600">
              {stats.modified}
            </div>
            <p className="text-xs text-gray-500 mt-1">
              {getPercentage(stats.modified)}% of total
            </p>
          </CardContent>
        </Card>

        {/* Positive Rate */}
        <Card className="bg-gradient-to-br from-green-50 to-blue-50 border-green-200">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-gray-700 flex items-center gap-2">
              <TrendingUp className="h-4 w-4 text-green-600" />
              Positive
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold text-green-600">
              {positiveRate}%
            </div>
            <p className="text-xs text-gray-600 mt-1">
              Accept + Modify
            </p>
          </CardContent>
        </Card>

        {/* Acceptance Rate */}
        <Card className="bg-gradient-to-br from-purple-50 to-pink-50 border-purple-200">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-gray-700 flex items-center gap-2">
              <Brain className="h-4 w-4 text-purple-600" />
              Learning
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold text-purple-600">
              {stats.acceptance_rate.toFixed(1)}%
            </div>
            <p className="text-xs text-gray-600 mt-1">
              Acceptance Rate
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Visual Breakdown */}
      <Card>
        <CardHeader>
          <CardTitle className="text-sm">Decision Distribution</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            {/* Accepted Bar */}
            <div>
              <div className="flex items-center justify-between text-sm mb-1">
                <span className="text-gray-600 flex items-center gap-2">
                  <CheckCircle className="h-3 w-3 text-green-600" />
                  Accepted
                </span>
                <span className="font-semibold text-green-600">
                  {stats.accepted} ({getPercentage(stats.accepted)}%)
                </span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-2">
                <div
                  className="bg-green-500 h-2 rounded-full transition-all"
                  style={{ width: `${getPercentage(stats.accepted)}%` }}
                />
              </div>
            </div>

            {/* Rejected Bar */}
            <div>
              <div className="flex items-center justify-between text-sm mb-1">
                <span className="text-gray-600 flex items-center gap-2">
                  <XCircle className="h-3 w-3 text-red-600" />
                  Rejected
                </span>
                <span className="font-semibold text-red-600">
                  {stats. rejected} ({getPercentage(stats. rejected)}%)
                </span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-2">
                <div
                  className="bg-red-500 h-2 rounded-full transition-all"
                  style={{ width: `${getPercentage(stats. rejected)}%` }}
                />
              </div>
            </div>

            {/* Modified Bar */}
            <div>
              <div className="flex items-center justify-between text-sm mb-1">
                <span className="text-gray-600 flex items-center gap-2">
                  <Edit className="h-3 w-3 text-blue-600" />
                  Modified
                </span>
                <span className="font-semibold text-blue-600">
                  {stats.modified} ({getPercentage(stats.modified)}%)
                </span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-2">
                <div
                  className="bg-blue-500 h-2 rounded-full transition-all"
                  style={{ width: `${getPercentage(stats.modified)}%` }}
                />
              </div>
            </div>
          </div>

          {/* Overall Acceptance Rate */}
          <div className="mt-6 pt-4 border-t">
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm font-semibold text-gray-700">
                Overall Acceptance Rate
              </span>
              <span className="text-2xl font-bold text-purple-600">
                {stats.acceptance_rate.toFixed(1)}%
              </span>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-3">
              <div
                className="bg-gradient-to-r from-green-500 via-blue-500 to-purple-500 h-3 rounded-full transition-all"
                style={{ width: `${stats.acceptance_rate}%` }}
              />
            </div>
            <p className="text-xs text-gray-500 mt-2">
              Measures how often suggestions are accepted or modified vs. rejected
            </p>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}