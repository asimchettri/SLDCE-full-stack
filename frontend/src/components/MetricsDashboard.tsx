import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Download, TrendingUp, Target, Award, AlertCircle } from 'lucide-react';
import { LineChart, Line, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts';
import type { DetectionStats } from '@/types/detection';

interface MetricsDashboardProps {
  stats: DetectionStats;
  datasetName: string;
  detections?: any[];
}

export function MetricsDashboard({ stats, datasetName, detections }: MetricsDashboardProps) {
  
  // Calculate additional metrics
  const precision = stats.suspicious_samples > 0 
    ? (stats.high_priority_detections / stats.suspicious_samples) 
    : 0;
  
  const recall = stats.total_samples > 0
    ? (stats.suspicious_samples / stats.total_samples)
    : 0;
  
  const f1Score = (precision + recall) > 0
    ? (2 * precision * recall) / (precision + recall)
    : 0;

  // Prepare data for charts
  const metricsData = [
    {
      name: 'Precision',
      value: precision * 100,
      color: '#3b82f6',
    },
    {
      name: 'Recall',
      value: recall * 100,
      color: '#10b981',
    },
    {
      name: 'F1 Score',
      value: f1Score * 100,
      color: '#8b5cf6',
    },
    {
      name: 'Avg Confidence',
      value: stats.average_confidence * 100,
      color: '#f59e0b',
    },
  ];

  // Distribution data
  const distributionData = [
    { name: 'Clean Samples', value: stats.total_samples - stats.suspicious_samples, color: '#10b981' },
    { name: 'Suspicious', value: stats.suspicious_samples - stats.high_priority_detections, color: '#f59e0b' },
    { name: 'High Priority', value: stats.high_priority_detections, color: '#ef4444' },
  ];

  // Priority distribution from detections
  const priorityDistribution = detections
    ? [
        {
          range: 'High (≥0.8)',
          count: detections.filter(d => d.priority_score >= 0.8).length,
        },
        {
          range: 'Medium (0.6-0.8)',
          count: detections.filter(d => d.priority_score >= 0.6 && d.priority_score < 0.8).length,
        },
        {
          range: 'Low (<0.6)',
          count: detections.filter(d => d.priority_score < 0.6).length,
        },
      ]
    : [];

  // Confidence distribution
  const confidenceDistribution = detections
    ? [
        {
          range: 'Very High (≥0.9)',
          count: detections.filter(d => d.confidence_score >= 0.9).length,
        },
        {
          range: 'High (0.8-0.9)',
          count: detections.filter(d => d.confidence_score >= 0.8 && d.confidence_score < 0.9).length,
        },
        {
          range: 'Medium (0.7-0.8)',
          count: detections.filter(d => d.confidence_score >= 0.7 && d.confidence_score < 0.8).length,
        },
        {
          range: 'Low (<0.7)',
          count: detections.filter(d => d.confidence_score < 0.7).length,
        },
      ]
    : [];

  // Export data as JSON
  const handleExportJSON = () => {
    const exportData = {
      dataset: datasetName,
      timestamp: new Date().toISOString(),
      summary: {
        total_samples: stats.total_samples,
        suspicious_samples: stats.suspicious_samples,
        high_priority_detections: stats.high_priority_detections,
        detection_rate: stats.detection_rate,
      },
      metrics: {
        precision: precision.toFixed(4),
        recall: recall.toFixed(4),
        f1_score: f1Score.toFixed(4),
        average_confidence: stats.average_confidence.toFixed(4),
      },
      detections: detections?.map(d => ({
        sample_id: d.sample_id,
        priority_score: d.priority_score,
        confidence_score: d.confidence_score,
        anomaly_score: d.anomaly_score,
        predicted_label: d.predicted_label,
      })),
    };

    const blob = new Blob([JSON.stringify(exportData, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `detection-results-${datasetName}-${Date.now()}.json`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  // Export data as CSV
  const handleExportCSV = () => {
    if (!detections || detections.length === 0) return;

    const headers = [
      'Sample ID',
      'Priority Score',
      'Confidence Score',
      'Anomaly Score',
      'Predicted Label',
      'Detected At',
    ];

    const rows = detections.map(d => [
      d.sample_id,
      d.priority_score.toFixed(4),
      d.confidence_score.toFixed(4),
      d.anomaly_score.toFixed(4),
      d.predicted_label,
      new Date(d.detected_at).toISOString(),
    ]);

    const csvContent = [
      headers.join(','),
      ...rows.map(row => row.join(',')),
    ].join('\n');

    const blob = new Blob([csvContent], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `detection-results-${datasetName}-${Date.now()}.csv`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  return (
    <div className="space-y-6">
      {/* Header with Export Options */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold">Performance Metrics</h2>
          <p className="text-gray-500">Dataset: {datasetName}</p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" onClick={handleExportJSON}>
            <Download className="mr-2 h-4 w-4" />
            Export JSON
          </Button>
          <Button variant="outline" onClick={handleExportCSV} disabled={!detections || detections.length === 0}>
            <Download className="mr-2 h-4 w-4" />
            Export CSV
          </Button>
        </div>
      </div>

      {/* Key Metrics Cards */}
      <div className="grid gap-4 md:grid-cols-4">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-gray-600 flex items-center gap-2">
              <Target className="h-4 w-4 text-blue-600" />
              Precision
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold text-blue-600">
              {(precision * 100).toFixed(1)}%
            </div>
            <p className="text-xs text-gray-500 mt-1">
              High priority / All suspicious
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-gray-600 flex items-center gap-2">
              <TrendingUp className="h-4 w-4 text-green-600" />
              Recall
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold text-green-600">
              {(recall * 100).toFixed(1)}%
            </div>
            <p className="text-xs text-gray-500 mt-1">
              Detection rate
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-gray-600 flex items-center gap-2">
              <Award className="h-4 w-4 text-purple-600" />
              F1 Score
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold text-purple-600">
              {(f1Score * 100).toFixed(1)}%
            </div>
            <p className="text-xs text-gray-500 mt-1">
              Harmonic mean
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-gray-600 flex items-center gap-2">
              <AlertCircle className="h-4 w-4 text-orange-600" />
              Avg Confidence
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold text-orange-600">
              {(stats.average_confidence * 100).toFixed(1)}%
            </div>
            <p className="text-xs text-gray-500 mt-1">
              Across all detections
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Charts Row 1: Metrics Comparison & Sample Distribution */}
      <div className="grid gap-4 md:grid-cols-2">
        {/* Performance Metrics Bar Chart */}
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Performance Metrics Comparison</CardTitle>
            <CardDescription>
              Key detection performance indicators
            </CardDescription>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={metricsData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                <XAxis dataKey="name" tick={{ fontSize: 12 }} />
                <YAxis domain={[0, 100]} tick={{ fontSize: 12 }} />
                <Tooltip />
                <Bar dataKey="value" radius={[8, 8, 0, 0]}>
                  {metricsData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        {/* Sample Distribution Pie Chart */}
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Sample Distribution</CardTitle>
            <CardDescription>
              Breakdown of dataset by detection status
            </CardDescription>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie
                  data={distributionData}
                  cx="50%"
                  cy="50%"
                  labelLine={false}
                  label={({ name, percent }) => `${name}: ${((percent ?? 0) * 100).toFixed(0)}%`}
                  outerRadius={100}
                  fill="#8884d8"
                  dataKey="value"
                >
                  {distributionData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>
      </div>

      {/* Charts Row 2: Priority & Confidence Distribution */}
      {detections && detections.length > 0 && (
        <div className="grid gap-4 md:grid-cols-2">
          {/* Priority Distribution */}
          <Card>
            <CardHeader>
              <CardTitle className="text-base">Priority Score Distribution</CardTitle>
              <CardDescription>
                Number of samples by priority level
              </CardDescription>
            </CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={250}>
                <BarChart data={priorityDistribution}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                  <XAxis dataKey="range" tick={{ fontSize: 11 }} />
                  <YAxis />
                  <Tooltip />
                  <Bar dataKey="count" fill="#f59e0b" radius={[8, 8, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>

          {/* Confidence Distribution */}
          <Card>
            <CardHeader>
              <CardTitle className="text-base">Confidence Score Distribution</CardTitle>
              <CardDescription>
                Number of samples by confidence level
              </CardDescription>
            </CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={250}>
                <BarChart data={confidenceDistribution}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                  <XAxis dataKey="range" tick={{ fontSize: 11 }} />
                  <YAxis />
                  <Tooltip />
                  <Bar dataKey="count" fill="#3b82f6" radius={[8, 8, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Detection Summary Table */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base">Detection Summary</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-2 text-sm">
            <div className="flex justify-between py-2 border-b">
              <span className="text-gray-600">Total Samples</span>
              <span className="font-semibold">{stats.total_samples}</span>
            </div>
            <div className="flex justify-between py-2 border-b">
              <span className="text-gray-600">Suspicious Samples Detected</span>
              <span className="font-semibold text-orange-600">{stats.suspicious_samples}</span>
            </div>
            <div className="flex justify-between py-2 border-b">
              <span className="text-gray-600">High Priority Detections</span>
              <span className="font-semibold text-red-600">{stats.high_priority_detections}</span>
            </div>
            <div className="flex justify-between py-2 border-b">
              <span className="text-gray-600">Detection Rate</span>
              <span className="font-semibold">{stats.detection_rate.toFixed(2)}%</span>
            </div>
            <div className="flex justify-between py-2 border-b">
              <span className="text-gray-600">Average Confidence</span>
              <span className="font-semibold">{(stats.average_confidence * 100).toFixed(2)}%</span>
            </div>
            <div className="flex justify-between py-2 border-b">
              <span className="text-gray-600">Precision</span>
              <span className="font-semibold text-blue-600">{(precision * 100).toFixed(2)}%</span>
            </div>
            <div className="flex justify-between py-2 border-b">
              <span className="text-gray-600">Recall</span>
              <span className="font-semibold text-green-600">{(recall * 100).toFixed(2)}%</span>
            </div>
            <div className="flex justify-between py-2">
              <span className="text-gray-600">F1 Score</span>
              <span className="font-semibold text-purple-600">{(f1Score * 100).toFixed(2)}%</span>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}