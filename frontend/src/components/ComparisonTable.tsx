import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { Badge } from '@/components/ui/badge';
import { TrendingUp, TrendingDown, GitCompare, BarChart } from 'lucide-react';

interface MetricRow {
  metric: string;
  baseline: number | string;
  current: number | string;
  change?: number;
  unit?: string;
}

interface IterationRow {
  iteration: number;
  accuracy: number;
  precision: number;
  recall: number;
  corrections: number;
}

interface ComparisonTableProps {
  data?: MetricRow[];
  iterationComparison?: IterationRow[];
}

// ─── Iteration Line Chart ─────────────────────────────────────────────────────

function IterationChart({ rows }: { rows: IterationRow[] }) {
  if (rows.length < 2) return null;

  const W = 560;
  const H = 200;
  const PAD = { top: 20, right: 24, bottom: 40, left: 50 };
  const chartW = W - PAD.left - PAD.right;
  const chartH = H - PAD.top - PAD.bottom;

  const allVals = rows.flatMap(r => [r.accuracy, r.precision, r.recall]);
  const minVal = Math.max(0, Math.min(...allVals) - 5);
  const maxVal = Math.min(100, Math.max(...allVals) + 5);
  const range = maxVal - minVal || 1;

  const xScale = (i: number) =>
    PAD.left + (i / Math.max(rows.length - 1, 1)) * chartW;
  const yScale = (v: number) =>
    PAD.top + chartH - ((v - minVal) / range) * chartH;

  const line = (key: keyof IterationRow) =>
    rows.map((r, i) => `${xScale(i)},${yScale(r[key] as number)}`).join(' ');

  const SERIES = [
    { key: 'accuracy' as const, color: '#10b981', label: 'Accuracy' },
    { key: 'precision' as const, color: '#3b82f6', label: 'Precision' },
    { key: 'recall' as const, color: '#8b5cf6', label: 'Recall' },
  ];

  const yTicks = [minVal, (minVal + maxVal) / 2, maxVal];

  return (
    <div className="mb-6">
      <p className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-2">
        Learning Curve — Accuracy / Precision / Recall per Iteration
      </p>
      <svg viewBox={`0 0 ${W} ${H}`} className="w-full" style={{ fontFamily: 'monospace' }}>
        {/* Gridlines */}
        {yTicks.map((v, i) => {
          const y = yScale(v);
          return (
            <g key={i}>
              <line x1={PAD.left} y1={y} x2={PAD.left + chartW} y2={y}
                stroke="#e5e7eb" strokeWidth={1} strokeDasharray="4 3" />
              <text x={PAD.left - 5} y={y + 4} textAnchor="end"
                fontSize={9} fill="#9ca3af">{v.toFixed(0)}%</text>
            </g>
          );
        })}

        {/* Accuracy area fill */}
        <polygon
          points={`${PAD.left},${PAD.top + chartH} ${rows.map((r, i) => `${xScale(i)},${yScale(r.accuracy)}`).join(' ')} ${xScale(rows.length - 1)},${PAD.top + chartH}`}
          fill="#10b981" opacity={0.06}
        />

        {/* Lines */}
        {SERIES.map(s => (
          <polyline key={s.key} points={line(s.key)} fill="none"
            stroke={s.color} strokeWidth={2}
            strokeLinejoin="round" strokeLinecap="round" />
        ))}

        {/* Accuracy dots + value labels */}
        {rows.map((r, i) => (
          <g key={i}>
            <circle cx={xScale(i)} cy={yScale(r.accuracy)} r={4}
              fill="#10b981" stroke="white" strokeWidth={2} />
            <text x={xScale(i)} y={yScale(r.accuracy) - 8}
              textAnchor="middle" fontSize={8.5} fill="#10b981" fontWeight="600">
              {r.accuracy.toFixed(1)}%
            </text>
            <text x={xScale(i)} y={H - PAD.bottom + 14}
              textAnchor="middle" fontSize={9} fill="#6b7280">
              {r.iteration === 0 ? 'Base' : `Iter ${r.iteration}`}
            </text>
          </g>
        ))}

        {/* Axes */}
        <line x1={PAD.left} y1={PAD.top} x2={PAD.left} y2={PAD.top + chartH}
          stroke="#d1d5db" strokeWidth={1} />
        <line x1={PAD.left} y1={PAD.top + chartH} x2={PAD.left + chartW} y2={PAD.top + chartH}
          stroke="#d1d5db" strokeWidth={1} />
      </svg>

      {/* Legend */}
      <div className="flex gap-4 mt-1">
        {SERIES.map(s => (
          <span key={s.key} className="flex items-center gap-1.5 text-xs text-gray-500">
            <span style={{ backgroundColor: s.color, width: 12, height: 2, display: 'inline-block', borderRadius: 1 }} />
            {s.label}
          </span>
        ))}
      </div>
    </div>
  );
}

// ─── Main Component ───────────────────────────────────────────────────────────

export function ComparisonTable({
  data = [
    { metric: 'Accuracy', baseline: 78, current: 90, change: 12, unit: '%' },
    { metric: 'Precision', baseline: 75, current: 88, change: 13, unit: '%' },
    { metric: 'Recall', baseline: 72, current: 86, change: 14, unit: '%' },
    { metric: 'F1 Score', baseline: 73.5, current: 87, change: 13.5, unit: '%' },
    { metric: 'Error Rate', baseline: 22, current: 10, change: -12, unit: '%' },
    { metric: 'Samples Corrected', baseline: 0, current: 32, change: 32, unit: '' },
  ],
  iterationComparison = [
    { iteration: 0, accuracy: 78, precision: 75, recall: 72, corrections: 0 },
    { iteration: 1, accuracy: 84, precision: 81, recall: 79, corrections: 15 },
    { iteration: 2, accuracy: 88, precision: 86, recall: 84, corrections: 28 },
    { iteration: 3, accuracy: 90, precision: 88, recall: 86, corrections: 32 },
  ]
}: ComparisonTableProps) {

  const getTrendBadge = (change?: number, isErrorRate = false) => {
    if (change === undefined || change === 0) {
      return <Badge variant="outline">No Change</Badge>;
    }
    const actuallyPositive = isErrorRate ? change < 0 : change > 0;
    return (
      <Badge className={actuallyPositive ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'}>
        {actuallyPositive
          ? <TrendingUp className="h-3 w-3 mr-1 inline" />
          : <TrendingDown className="h-3 w-3 mr-1 inline" />}
        {change > 0 ? '+' : ''}{Number(change).toFixed(1)}%
      </Badge>
    );
  };

  const totalImprovement =
    iterationComparison[iterationComparison.length - 1].accuracy -
    iterationComparison[0].accuracy;

  return (
    <div className="space-y-6">

      {/* Before/After Comparison Table */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <GitCompare className="h-5 w-5" />
            Before vs After Comparison
          </CardTitle>
          <CardDescription>
            Performance metrics before and after SLDCE corrections
          </CardDescription>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead className="w-[200px]">Metric</TableHead>
                <TableHead className="text-center">Baseline (Before)</TableHead>
                <TableHead className="text-center">Current (After)</TableHead>
                <TableHead className="text-center">Change</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {data.map((row, index) => (
                <TableRow key={index}>
                  <TableCell className="font-medium">{row.metric}</TableCell>
                  <TableCell className="text-center text-gray-600">
                    {row.baseline}{row.unit}
                  </TableCell>
                  <TableCell className="text-center font-semibold text-blue-600">
                    {row.current}{row.unit}
                  </TableCell>
                  <TableCell className="text-center">
                    {getTrendBadge(row.change, row.metric === 'Error Rate')}
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </CardContent>
      </Card>

      {/* Iteration Chart + Table */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <BarChart className="h-5 w-5" />
            Iteration-by-Iteration Progress
          </CardTitle>
          <CardDescription>
            Learning curve across each correction cycle
          </CardDescription>
        </CardHeader>
        <CardContent>

          {/* Line Chart */}
          <IterationChart rows={iterationComparison} />

          {/* Table */}
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Iteration</TableHead>
                <TableHead className="text-center">Accuracy</TableHead>
                <TableHead className="text-center">Precision</TableHead>
                <TableHead className="text-center">Recall</TableHead>
                <TableHead className="text-center">Corrections</TableHead>
                <TableHead className="text-center">Δ Accuracy</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {iterationComparison.map((row, index) => {
                const prev = index > 0 ? iterationComparison[index - 1].accuracy : row.accuracy;
                const delta = row.accuracy - prev;
                return (
                  <TableRow key={row.iteration}>
                    <TableCell className="font-medium">
                      {row.iteration === 0 ? 'Baseline' : `Iteration ${row.iteration}`}
                    </TableCell>
                    <TableCell className="text-center">
                      <span className={row.iteration === 0 ? 'text-gray-600' : 'font-semibold text-blue-600'}>
                        {row.accuracy}%
                      </span>
                    </TableCell>
                    <TableCell className="text-center">{row.precision}%</TableCell>
                    <TableCell className="text-center">{row.recall}%</TableCell>
                    <TableCell className="text-center">
                      {row.corrections > 0
                        ? <Badge variant="outline">{row.corrections}</Badge>
                        : <span className="text-gray-400">—</span>}
                    </TableCell>
                    <TableCell className="text-center">
                      {index === 0 ? (
                        <span className="text-gray-400">—</span>
                      ) : delta > 0 ? (
                        <Badge className="bg-green-100 text-green-800">
                          <TrendingUp className="h-3 w-3 mr-1 inline" />
                          +{delta.toFixed(1)}%
                        </Badge>
                      ) : (
                        <Badge variant="outline">{delta.toFixed(1)}%</Badge>
                      )}
                    </TableCell>
                  </TableRow>
                );
              })}
            </TableBody>
          </Table>

          {/* Summary bar */}
          <div className="mt-6 p-4 bg-blue-50 rounded-lg border border-blue-200 flex items-center justify-between">
            <div>
              <div className="text-sm font-semibold text-blue-900">Total Improvement</div>
              <div className="text-xs text-blue-700 mt-0.5">Baseline → Latest iteration</div>
            </div>
            <div className="text-3xl font-bold text-blue-600">
              +{totalImprovement.toFixed(1)}%
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Key Insights */}
      <Card className="bg-gradient-to-r from-purple-50 to-pink-50 border-purple-200">
        <CardHeader>
          <CardTitle className="text-base">Key Insights</CardTitle>
        </CardHeader>
        <CardContent>
          <ul className="space-y-2 text-sm text-gray-700">
            <li className="flex items-start gap-2">
              <TrendingUp className="h-4 w-4 text-green-600 mt-0.5 shrink-0" />
              <span>
                <strong>Accuracy improved by {data[0]?.change ?? '—'}%</strong> after {data[5]?.current ?? '—'} corrections
              </span>
            </li>
            <li className="flex items-start gap-2">
              <TrendingUp className="h-4 w-4 text-green-600 mt-0.5 shrink-0" />
              <span>
                <strong>Precision: {data[1]?.baseline}% → {data[1]?.current}%</strong>, indicating better detection quality
              </span>
            </li>
            <li className="flex items-start gap-2">
              <TrendingUp className="h-4 w-4 text-green-600 mt-0.5 shrink-0" />
              <span>
                <strong>Error rate reduced by {Math.abs(data[4]?.change as number ?? 0)}%</strong>,
                from {data[4]?.baseline}% to {data[4]?.current}%
              </span>
            </li>
            <li className="flex items-start gap-2">
              <BarChart className="h-4 w-4 text-blue-600 mt-0.5 shrink-0" />
              <span>
                System demonstrates <strong>consistent improvement</strong> across all {iterationComparison.length - 1} iterations
              </span>
            </li>
          </ul>
        </CardContent>
      </Card>
    </div>
  );
}