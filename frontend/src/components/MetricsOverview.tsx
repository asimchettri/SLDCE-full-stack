import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { 
  TrendingUp, 
  TrendingDown,
  Target,
  CheckCircle,
  AlertTriangle,
  Award,
  BarChart3,
  Percent
} from 'lucide-react';

interface MetricCardProps {
  title: string;
  value: string | number;
  subtitle?: string;
  trend?: 'up' | 'down' | 'neutral';
  trendValue?: string;
  icon?: React.ReactNode;
  color?: string;
}

function MetricCard({ 
  title, 
  value, 
  subtitle, 
  trend, 
  trendValue,
  icon,
  color = 'text-blue-600'
}: MetricCardProps) {
  const getTrendIcon = () => {
    if (trend === 'up') return <TrendingUp className="h-4 w-4 text-green-600" />;
    if (trend === 'down') return <TrendingDown className="h-4 w-4 text-red-600" />;
    return null;
  };

  const getTrendColor = () => {
    if (trend === 'up') return 'text-green-600';
    if (trend === 'down') return 'text-red-600';
    return 'text-gray-600';
  };

  return (
    <Card>
      <CardHeader className="pb-2">
        <CardTitle className="text-sm font-medium text-gray-600 flex items-center gap-2">
          {icon}
          {title}
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className={`text-3xl font-bold ${color}`}>{value}</div>
        {subtitle && (
          <p className="text-xs text-gray-500 mt-1">{subtitle}</p>
        )}
        {trendValue && (
          <div className={`flex items-center gap-1 mt-2 text-sm ${getTrendColor()}`}>
            {getTrendIcon()}
            <span className="font-semibold">{trendValue}</span>
            <span className="text-xs text-gray-500">vs. baseline</span>
          </div>
        )}
      </CardContent>
    </Card>
  );
}

interface MetricsOverviewProps {
  totalSamples?: number;
  suspiciousSamples?: number;
  correctedSamples?: number;
  accuracyImprovement?: number;
  acceptanceRate?: number;
  detectionPrecision?: number;
  currentAccuracy?: number;
  baselineAccuracy?: number;
}

export function MetricsOverview({
  totalSamples = 150,
  suspiciousSamples = 45,
  correctedSamples = 32,
  accuracyImprovement = 12,
  acceptanceRate = 85,
  detectionPrecision = 78,
  currentAccuracy = 90,
  baselineAccuracy = 78
}: MetricsOverviewProps) {
  return (
    <div className="space-y-4">
      <div>
        <h3 className="text-lg font-semibold flex items-center gap-2">
          <BarChart3 className="h-5 w-5" />
          Executive Summary
        </h3>
        <p className="text-sm text-gray-500">Key performance metrics at a glance</p>
      </div>

      {/* Main Metrics Grid */}
      <div className="grid gap-4 md:grid-cols-4">
        <MetricCard
          title="Total Samples"
          value={totalSamples.toLocaleString()}
          subtitle="In dataset"
          icon={<Target className="h-4 w-4" />}
          color="text-gray-700"
        />
        
        <MetricCard
          title="Suspicious Detected"
          value={suspiciousSamples}
          subtitle={`${((suspiciousSamples / totalSamples) * 100).toFixed(1)}% of total`}
          icon={<AlertTriangle className="h-4 w-4 text-orange-600" />}
          color="text-orange-600"
        />
        
        <MetricCard
          title="Samples Corrected"
          value={correctedSamples}
          subtitle={`${((correctedSamples / suspiciousSamples) * 100).toFixed(1)}% of suspicious`}
          icon={<CheckCircle className="h-4 w-4 text-green-600" />}
          color="text-green-600"
        />
        
        <MetricCard
          title="Acceptance Rate"
          value={`${acceptanceRate}%`}
          subtitle="Suggestions accepted"
          icon={<Award className="h-4 w-4 text-purple-600" />}
          color="text-purple-600"
        />
      </div>

      {/* Performance Metrics */}
      <div className="grid gap-4 md:grid-cols-3">
        <MetricCard
          title="Current Accuracy"
          value={`${currentAccuracy}%`}
          subtitle="After corrections"
          trend="up"
          trendValue={`+${accuracyImprovement}%`}
          icon={<TrendingUp className="h-4 w-4 text-blue-600" />}
          color="text-blue-600"
        />
        
        <MetricCard
          title="Baseline Accuracy"
          value={`${baselineAccuracy}%`}
          subtitle="Before corrections"
          icon={<BarChart3 className="h-4 w-4 text-gray-600" />}
          color="text-gray-600"
        />
        
        <MetricCard
          title="Detection Precision"
          value={`${detectionPrecision}%`}
          subtitle="True positives / Total flagged"
          icon={<Percent className="h-4 w-4 text-blue-600" />}
          color="text-blue-600"
        />
      </div>

      {/* Improvement Highlight */}
      <Card className="bg-gradient-to-r from-green-50 to-blue-50 border-green-200">
        <CardContent className="pt-6">
          <div className="flex items-center justify-between">
            <div>
              <div className="text-sm font-semibold text-gray-700 flex items-center gap-2">
                <TrendingUp className="h-5 w-5 text-green-600" />
                Overall Improvement
              </div>
              <div className="text-xs text-gray-600 mt-1">
                Accuracy increased from {baselineAccuracy}% to {currentAccuracy}%
              </div>
            </div>
            <div className="text-5xl font-bold text-green-600">
              +{accuracyImprovement}%
            </div>
          </div>
          <div className="mt-4 w-full bg-gray-200 rounded-full h-3">
            <div
              className="bg-gradient-to-r from-green-500 to-blue-500 h-3 rounded-full transition-all"
              style={{ width: `${(currentAccuracy / 100) * 100}%` }}
            />
          </div>
        </CardContent>
      </Card>
    </div>
  );
}