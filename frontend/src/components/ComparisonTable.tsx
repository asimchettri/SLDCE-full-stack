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

interface ComparisonTableProps {
  data?: MetricRow[];
  iterationComparison?: Array<{
    iteration: number;
    accuracy: number;
    precision: number;
    recall: number;
    corrections: number;
  }>;
}

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
  
  const getTrendBadge = (change?: number) => {
    if (change === undefined || change === 0) {
      return <Badge variant="outline">No Change</Badge>;
    }
    
    const isPositive = change > 0;
    const isErrorRate = data.find(d => d.change === change)?.metric === 'Error Rate';
    const actuallyPositive = isErrorRate ? !isPositive : isPositive;
    
    return (
      <Badge className={actuallyPositive ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'}>
        {actuallyPositive ? (
          <TrendingUp className="h-3 w-3 mr-1" />
        ) : (
          <TrendingDown className="h-3 w-3 mr-1" />
        )}
        {Math.abs(change).toFixed(1)}%
      </Badge>
    );
  };

  return (
    <div className="space-y-6">
      {/* Before/After Comparison */}
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
                  <TableCell className="text-center">
                    <span className="text-gray-600">
                      {row.baseline}{row.unit}
                    </span>
                  </TableCell>
                  <TableCell className="text-center">
                    <span className="font-semibold text-blue-600">
                      {row.current}{row.unit}
                    </span>
                  </TableCell>
                  <TableCell className="text-center">
                    {getTrendBadge(row.change)}
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </CardContent>
      </Card>

      {/* Iteration-by-Iteration Comparison */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <BarChart className="h-5 w-5" />
            Iteration-by-Iteration Progress
          </CardTitle>
          <CardDescription>
            Track improvements across each correction cycle
          </CardDescription>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Iteration</TableHead>
                <TableHead className="text-center">Accuracy</TableHead>
                <TableHead className="text-center">Precision</TableHead>
                <TableHead className="text-center">Recall</TableHead>
                <TableHead className="text-center">Corrections Made</TableHead>
                <TableHead className="text-center">Improvement</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {iterationComparison.map((row, index) => {
                const prevAccuracy = index > 0 ? iterationComparison[index - 1].accuracy : row.accuracy;
                const improvement = row.accuracy - prevAccuracy;
                
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
                      {row.corrections > 0 ? (
                        <Badge variant="outline">{row.corrections}</Badge>
                      ) : (
                        <span className="text-gray-400">—</span>
                      )}
                    </TableCell>
                    <TableCell className="text-center">
                      {row.iteration === 0 ? (
                        <span className="text-gray-400">—</span>
                      ) : improvement > 0 ? (
                        <Badge className="bg-green-100 text-green-800">
                          <TrendingUp className="h-3 w-3 mr-1" />
                          +{improvement.toFixed(1)}%
                        </Badge>
                      ) : (
                        <Badge variant="outline">
                          {improvement.toFixed(1)}%
                        </Badge>
                      )}
                    </TableCell>
                  </TableRow>
                );
              })}
            </TableBody>
          </Table>

          {/* Summary */}
          <div className="mt-6 p-4 bg-blue-50 rounded-lg border border-blue-200">
            <div className="flex items-center justify-between">
              <div>
                <div className="text-sm font-semibold text-blue-900">Total Improvement</div>
                <div className="text-xs text-blue-700 mt-1">
                  From baseline to current iteration
                </div>
              </div>
              <div className="text-3xl font-bold text-blue-600">
                +{(iterationComparison[iterationComparison.length - 1].accuracy - iterationComparison[0].accuracy).toFixed(1)}%
              </div>
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
                <strong>Accuracy improved by {data[0].change}%</strong> after {data[5].current} corrections
              </span>
            </li>
            <li className="flex items-start gap-2">
              <TrendingUp className="h-4 w-4 text-green-600 mt-0.5 shrink-0" />
              <span>
                <strong>Precision increased from {data[1].baseline}% to {data[1].current}%</strong>, 
                indicating better detection quality
              </span>
            </li>
            <li className="flex items-start gap-2">
              <TrendingUp className="h-4 w-4 text-green-600 mt-0.5 shrink-0" />
              <span>
                <strong>Error rate reduced by {Math.abs(data[4].change as number)}%</strong>, 
                from {data[4].baseline}% to {data[4].current}%
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