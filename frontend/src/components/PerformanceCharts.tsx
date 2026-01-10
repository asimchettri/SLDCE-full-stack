import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  CardDescription,
} from "@/components/ui/card";
import {
  LineChart,
  Line,
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  Radar,
} from "recharts";
import {
  TrendingUp,
  BarChart3,
  PieChart as PieChartIcon,
  Target,
} from "lucide-react";

interface PerformanceChartsProps {
  iterationData?: Array<{
    iteration: number;
    accuracy: number;
    precision: number;
    recall: number;
    f1_score: number;
  }>;
  feedbackDistribution?: {
    accepted: number;
    rejected: number;
    modified: number;
  };
  signalData?: Array<{
    subject: string;
    value: number;
  }>;
}

export function PerformanceCharts({
  iterationData = [
    { iteration: 0, accuracy: 78, precision: 75, recall: 72, f1_score: 73.5 },
    { iteration: 1, accuracy: 84, precision: 81, recall: 79, f1_score: 80 },
    { iteration: 2, accuracy: 88, precision: 86, recall: 84, f1_score: 85 },
    { iteration: 3, accuracy: 90, precision: 88, recall: 86, f1_score: 87 },
  ],
  feedbackDistribution = {
    accepted: 25,
    rejected: 12,
    modified: 8,
  },
  signalData = [
    { subject: "Confidence", value: 85 },
    { subject: "Anomaly", value: 78 },
    { subject: "Priority", value: 82 },
    { subject: "Acceptance", value: 85 },
    { subject: "Precision", value: 88 },
  ],
}: PerformanceChartsProps) {
  const COLORS = {
    accepted: "#10b981",
    rejected: "#ef4444",
    modified: "#3b82f6",
  };

  const pieData = [
    {
      name: "Accepted",
      value: feedbackDistribution.accepted,
      color: COLORS.accepted,
    },
    {
      name: "Rejected",
      value: feedbackDistribution.rejected,
      color: COLORS.rejected,
    },
    {
      name: "Modified",
      value: feedbackDistribution.modified,
      color: COLORS.modified,
    },
  ];

  return (
    <div className="space-y-6">
      {/* Line Chart - Performance Over Iterations */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <TrendingUp className="h-5 w-5" />
            Performance Over Iterations
          </CardTitle>
          <CardDescription>
            Track accuracy, precision, recall, and F1-score improvements
          </CardDescription>
        </CardHeader>
        <CardContent>
          <ResponsiveContainer width="100%" height={350}>
            <LineChart data={iterationData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
              <XAxis
                dataKey="iteration"
                label={{
                  value: "Iteration",
                  position: "insideBottom",
                  offset: -5,
                }}
              />
              <YAxis
                label={{
                  value: "Score (%)",
                  angle: -90,
                  position: "insideLeft",
                }}
                domain={[60, 100]}
              />
              <Tooltip
                contentStyle={{
                  backgroundColor: "white",
                  border: "1px solid #e5e7eb",
                  borderRadius: "8px",
                }}
              />
              <Legend />
              <Line
                type="monotone"
                dataKey="accuracy"
                stroke="#3b82f6"
                strokeWidth={2}
                dot={{ r: 4 }}
                name="Accuracy"
              />
              <Line
                type="monotone"
                dataKey="precision"
                stroke="#10b981"
                strokeWidth={2}
                dot={{ r: 4 }}
                name="Precision"
              />
              <Line
                type="monotone"
                dataKey="recall"
                stroke="#f59e0b"
                strokeWidth={2}
                dot={{ r: 4 }}
                name="Recall"
              />
              <Line
                type="monotone"
                dataKey="f1_score"
                stroke="#8b5cf6"
                strokeWidth={2}
                dot={{ r: 4 }}
                name="F1 Score"
              />
            </LineChart>
          </ResponsiveContainer>
        </CardContent>
      </Card>

      <div className="grid gap-6 md:grid-cols-2">
        {/* Bar Chart - Metrics Comparison */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <BarChart3 className="h-5 w-5" />
              Latest Iteration Metrics
            </CardTitle>
            <CardDescription>Current performance breakdown</CardDescription>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={[iterationData[iterationData.length - 1]]}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                <XAxis dataKey="iteration" />
                <YAxis domain={[0, 100]} />
                <Tooltip
                  contentStyle={{
                    backgroundColor: "white",
                    border: "1px solid #e5e7eb",
                    borderRadius: "8px",
                  }}
                />
                <Bar dataKey="accuracy" fill="#3b82f6" name="Accuracy" />
                <Bar dataKey="precision" fill="#10b981" name="Precision" />
                <Bar dataKey="recall" fill="#f59e0b" name="Recall" />
                <Bar dataKey="f1_score" fill="#8b5cf6" name="F1 Score" />
              </BarChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        {/* Pie Chart - Feedback Distribution */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <PieChartIcon className="h-5 w-5" />
              Feedback Distribution
            </CardTitle>
            <CardDescription>Human review decision breakdown</CardDescription>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie
                  data={pieData}
                  cx="50%"
                  cy="50%"
                  labelLine={false}
                  label={(entry) => {
                    const percent = entry.percent || 0;
                    return `${entry.name}: ${(percent * 100).toFixed(0)}%`;
                  }}
                  outerRadius={80}
                  fill="#8884d8"
                  dataKey="value"
                >
                  {pieData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
            <div className="mt-4 flex justify-center gap-4 text-sm">
              <div className="flex items-center gap-2">
                <div className="w-3 h-3 rounded-full bg-green-500" />
                <span>Accepted ({feedbackDistribution.accepted})</span>
              </div>
              <div className="flex items-center gap-2">
                <div className="w-3 h-3 rounded-full bg-red-500" />
                <span>Rejected ({feedbackDistribution.rejected})</span>
              </div>
              <div className="flex items-center gap-2">
                <div className="w-3 h-3 rounded-full bg-blue-500" />
                <span>Modified ({feedbackDistribution.modified})</span>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Radar Chart - Multi-Signal Analysis */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Target className="h-5 w-5" />
            Multi-Signal Performance Analysis
          </CardTitle>
          <CardDescription>
            Comprehensive view of all detection and feedback signals
          </CardDescription>
        </CardHeader>
        <CardContent>
          <ResponsiveContainer width="100%" height={400}>
            <RadarChart data={signalData}>
              <PolarGrid stroke="#e5e7eb" />
              <PolarAngleAxis dataKey="subject" />
              <PolarRadiusAxis angle={90} domain={[0, 100]} />
              <Radar
                name="Signal Strength"
                dataKey="value"
                stroke="#3b82f6"
                fill="#3b82f6"
                fillOpacity={0.6}
              />
              <Tooltip />
            </RadarChart>
          </ResponsiveContainer>
        </CardContent>
      </Card>
    </div>
  );
}
