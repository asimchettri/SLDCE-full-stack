import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, Cell } from 'recharts';
import type { ModelComparison } from '@/types/model';

interface ModelComparisonChartProps {
  data: ModelComparison[];
}

export function ModelComparisonChart({ data }: ModelComparisonChartProps) {
  // Transform data for chart
  const chartData = data.map((model) => ({
    name: model.name.length > 15 ? model.name.substring(0, 15) + '...' : model.name,
    fullName: model.name,
    Accuracy: (model.accuracy * 100).toFixed(1),
    Precision: model.precision ? (model.precision * 100).toFixed(1) : null,
    Recall: model.recall ? (model.recall * 100).toFixed(1) : null,
    'F1 Score': model.f1_score ? (model.f1_score * 100).toFixed(1) : null,
    isBaseline: model.is_baseline,
  }));

  // Colors
  const colors = {
    Accuracy: '#3b82f6',    // blue
    Precision: '#10b981',   // green
    Recall: '#f59e0b',      // orange
    'F1 Score': '#8b5cf6',  // purple
  };

  // Custom tooltip
  const CustomTooltip = ({ active, payload }: any) => {
    if (active && payload && payload.length) {
      const data = payload[0].payload;
      return (
        <div className="bg-white p-3 border rounded-lg shadow-lg">
          <p className="font-semibold mb-2">{data.fullName}</p>
          {payload.map((entry: any) => (
            <p key={entry.name} className="text-sm" style={{ color: entry.color }}>
              {entry.name}: {entry.value}%
            </p>
          ))}
          {data.isBaseline && (
            <p className="text-xs text-gray-500 mt-1 italic">Baseline Model</p>
          )}
        </div>
      );
    }
    return null;
  };

  return (
    <div className="w-full h-[400px]">
      <ResponsiveContainer width="100%" height="100%">
        <BarChart
          data={chartData}
          margin={{ top: 20, right: 30, left: 20, bottom: 60 }}
        >
          <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
          <XAxis
            dataKey="name"
            angle={-45}
            textAnchor="end"
            height={80}
            tick={{ fontSize: 12 }}
          />
          <YAxis
            domain={[0, 100]}
            tick={{ fontSize: 12 }}
            label={{ value: 'Percentage (%)', angle: -90, position: 'insideLeft' }}
          />
          <Tooltip content={<CustomTooltip />} />
          <Legend
            wrapperStyle={{ paddingTop: '20px' }}
            iconType="circle"
          />
          <Bar dataKey="Accuracy" fill={colors.Accuracy} radius={[8, 8, 0, 0]}>
            {chartData.map((entry, index) => (
              <Cell
                key={`cell-${index}`}
                fill={entry.isBaseline ? '#94a3b8' : colors.Accuracy}
                opacity={entry.isBaseline ? 0.6 : 1}
              />
            ))}
          </Bar>
          <Bar dataKey="Precision" fill={colors.Precision} radius={[8, 8, 0, 0]} />
          <Bar dataKey="Recall" fill={colors.Recall} radius={[8, 8, 0, 0]} />
          <Bar dataKey="F1 Score" fill={colors['F1 Score']} radius={[8, 8, 0, 0]} />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}