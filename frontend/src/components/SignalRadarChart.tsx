import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, Radar, ResponsiveContainer, Tooltip, Legend } from 'recharts';
import type { Detection } from '@/types/detection';

interface SignalRadarChartProps {
  detections: Detection[];
  title?: string;
}

export function SignalRadarChart({ detections, title = "Signal Distribution Analysis" }: SignalRadarChartProps) {
  if (!detections || detections.length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>{title}</CardTitle>
          <CardDescription>No detection data available</CardDescription>
        </CardHeader>
        <CardContent className="flex items-center justify-center h-[300px] text-gray-500">
          Run detection to see signal analysis
        </CardContent>
      </Card>
    );
  }

  // Calculate average scores
  const avgConfidence = detections.reduce((sum, d) => sum + d.confidence_score, 0) / detections.length;
  const avgAnomaly = detections.reduce((sum, d) => sum + d.anomaly_score, 0) / detections.length;
  const avgPriority = detections.reduce((sum, d) => sum + d.priority_score, 0) / detections.length;

  // Calculate max scores
  const maxConfidence = Math.max(...detections.map(d => d.confidence_score));
  const maxAnomaly = Math.max(...detections.map(d => d.anomaly_score));
  const maxPriority = Math.max(...detections.map(d => d.priority_score));

  // Calculate min scores
  const minConfidence = Math.min(...detections.map(d => d.confidence_score));
  const minAnomaly = Math.min(...detections.map(d => d.anomaly_score));
  const minPriority = Math.min(...detections.map(d => d.priority_score));

  const data = [
    {
      metric: 'Confidence',
      average: avgConfidence * 100,
      max: maxConfidence * 100,
      min: minConfidence * 100,
    },
    {
      metric: 'Anomaly',
      average: avgAnomaly * 100,
      max: maxAnomaly * 100,
      min: minAnomaly * 100,
    },
    {
      metric: 'Priority',
      average: avgPriority * 100,
      max: maxPriority * 100,
      min: minPriority * 100,
    },
  ];

  return (
    <Card>
      <CardHeader>
        <CardTitle>{title}</CardTitle>
        <CardDescription>
          Average, minimum, and maximum signal scores across {detections.length} detections
        </CardDescription>
      </CardHeader>
      <CardContent>
        <ResponsiveContainer width="100%" height={350}>
          <RadarChart data={data}>
            <PolarGrid stroke="#e5e7eb" />
            <PolarAngleAxis dataKey="metric" tick={{ fontSize: 12, fill: '#6b7280' }} />
            <PolarRadiusAxis angle={90} domain={[0, 100]} tick={{ fontSize: 10 }} />
            <Radar
              name="Average"
              dataKey="average"
              stroke="#3b82f6"
              fill="#3b82f6"
              fillOpacity={0.3}
            />
            <Radar
              name="Maximum"
              dataKey="max"
              stroke="#10b981"
              fill="#10b981"
              fillOpacity={0.2}
            />
            <Radar
              name="Minimum"
              dataKey="min"
              stroke="#f59e0b"
              fill="#f59e0b"
              fillOpacity={0.2}
            />
            <Tooltip />
            <Legend />
          </RadarChart>
        </ResponsiveContainer>

        {/* Stats Summary */}
        <div className="grid grid-cols-3 gap-4 mt-4 pt-4 border-t">
          <div className="text-center">
            <div className="text-xs text-gray-600">Confidence</div>
            <div className="text-lg font-bold text-blue-600">{(avgConfidence * 100).toFixed(1)}%</div>
            <div className="text-xs text-gray-500">avg</div>
          </div>
          <div className="text-center">
            <div className="text-xs text-gray-600">Anomaly</div>
            <div className="text-lg font-bold text-purple-600">{(avgAnomaly * 100).toFixed(1)}%</div>
            <div className="text-xs text-gray-500">avg</div>
          </div>
          <div className="text-center">
            <div className="text-xs text-gray-600">Priority</div>
            <div className="text-lg font-bold text-orange-600">{(avgPriority * 100).toFixed(1)}%</div>
            <div className="text-xs text-gray-500">avg</div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}