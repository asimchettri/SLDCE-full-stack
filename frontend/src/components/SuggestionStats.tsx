import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Clock, CheckCircle, XCircle, Edit, TrendingUp } from 'lucide-react';
import type { SuggestionStats as SuggestionStatsType } from '@/types/suggestion';

interface SuggestionStatsProps {
  stats: SuggestionStatsType;
}

export function SuggestionStats({ stats }: SuggestionStatsProps) {
  const getPercentage = (count: number) => {
    if (stats.total_suggestions === 0) return 0;
    return ((count / stats.total_suggestions) * 100).toFixed(1);
  };

  return (
    <div className="grid gap-4 md:grid-cols-5">
      {/* Total Suggestions */}
      <Card>
        <CardHeader className="pb-2">
          <CardTitle className="text-sm font-medium text-gray-600 flex items-center gap-2">
            <TrendingUp className="h-4 w-4" />
            Total
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold">{stats.total_suggestions}</div>
          <p className="text-xs text-gray-500">All suggestions</p>
        </CardContent>
      </Card>

      {/* Pending */}
      <Card>
        <CardHeader className="pb-2">
          <CardTitle className="text-sm font-medium text-gray-600 flex items-center gap-2">
            <Clock className="h-4 w-4 text-yellow-600" />
            Pending
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-2xl font-bold text-yellow-600">{stats.pending}</div>
          <p className="text-xs text-gray-500">
            {getPercentage(stats.pending)}% of total
          </p>
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
          <div className="text-2xl font-bold text-red-600">{stats.rejected}</div>
          <p className="text-xs text-gray-500">
            {getPercentage(stats.rejected)}% of total
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
            {getPercentage(stats.modified)}% of total
          </p>
        </CardContent>
      </Card>

      {/* Acceptance Rate Banner */}
      {stats.total_suggestions > stats.pending && (
        <Card className="md:col-span-5 bg-gradient-to-r from-green-50 to-blue-50 border-green-200">
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <div className="text-sm font-semibold text-gray-700">Acceptance Rate</div>
                <div className="text-xs text-gray-600 mt-1">
                  Accepted + Modified suggestions out of reviewed
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
      )}
    </div>
  );
}