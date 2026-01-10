import { useQuery } from '@tanstack/react-query';
import { experimentAPI } from '@/services/api';
import type { Experiment, ExperimentSummary } from '@/types/experiment';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, BarChart, Bar } from 'recharts';
import { TrendingUp, Target, Clock, AlertCircle } from 'lucide-react';

interface ExperimentDetailsDialogProps {
  experiment: Experiment;
  summary?: ExperimentSummary;
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

export function ExperimentDetailsDialog({
  experiment,
  summary,
  open,
  onOpenChange,
}: ExperimentDetailsDialogProps) {
  // Fetch iterations
  const { data: iterations, isLoading } = useQuery({
    queryKey: ['experiment-iterations', experiment.id],
    queryFn: () => experimentAPI.getIterations(experiment.id),
    enabled: open,
  });

  // Prepare chart data
  const accuracyData = iterations?.map((iter) => ({
    iteration: iter.iteration_number,
    Accuracy: (iter.accuracy * 100).toFixed(2),
    Precision: iter.precision ? (iter.precision * 100).toFixed(2) : null,
    Recall: iter.recall ? (iter.recall * 100).toFixed(2) : null,
    'F1 Score': iter.f1_score ? (iter.f1_score * 100).toFixed(2) : null,
  }));

  const correctionsData = iterations?.map((iter) => ({
    iteration: iter.iteration_number,
    Flagged: iter.samples_flagged,
    Corrected: iter.samples_corrected,
    Reviewed: iter.samples_reviewed,
  }));

  const noiseData = iterations?.map((iter) => ({
    iteration: iter.iteration_number,
    'Noise %': iter.remaining_noise_percentage?.toFixed(2) || experiment.noise_percentage,
  }));

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-5xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>{experiment.name}</DialogTitle>
          <DialogDescription>
            Detailed experiment results and performance metrics
          </DialogDescription>
        </DialogHeader>

        {isLoading ? (
          <div className="flex items-center justify-center py-8">
            <div className="text-gray-500">Loading experiment data...</div>
          </div>
        ) : (
          <div className="space-y-6">
            {/* Summary Stats */}
            {summary && (
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <Card>
                  <CardHeader className="pb-2">
                    <CardTitle className="text-sm font-medium text-gray-600 flex items-center gap-2">
                      <TrendingUp className="h-4 w-4" />
                      Accuracy Gain
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="text-2xl font-bold text-green-600">
                      +{summary.accuracy_improvement.toFixed(1)}%
                    </div>
                  </CardContent>
                </Card>

                <Card>
                  <CardHeader className="pb-2">
                    <CardTitle className="text-sm font-medium text-gray-600 flex items-center gap-2">
                      <AlertCircle className="h-4 w-4" />
                      Noise Reduced
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="text-2xl font-bold text-orange-600">
                      -{summary.noise_reduction.toFixed(1)}%
                    </div>
                  </CardContent>
                </Card>

                <Card>
                  <CardHeader className="pb-2">
                    <CardTitle className="text-sm font-medium text-gray-600 flex items-center gap-2">
                      <Target className="h-4 w-4" />
                      Corrections
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="text-2xl font-bold text-blue-600">
                      {summary.total_corrections}
                    </div>
                  </CardContent>
                </Card>

                <Card>
                  <CardHeader className="pb-2">
                    <CardTitle className="text-sm font-medium text-gray-600 flex items-center gap-2">
                      <Clock className="h-4 w-4" />
                      Avg Time/Iter
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="text-2xl font-bold text-purple-600">
                      {summary.avg_time_per_iteration.toFixed(1)}s
                    </div>
                  </CardContent>
                </Card>
              </div>
            )}

            {/* Accuracy Over Time */}
            <Card>
              <CardHeader>
                <CardTitle className="text-base">Accuracy Progress</CardTitle>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={300}>
                  <LineChart data={accuracyData}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                    <XAxis
                      dataKey="iteration"
                      label={{ value: 'Iteration', position: 'insideBottom', offset: -5 }}
                    />
                    <YAxis
                      domain={[0, 100]}
                      label={{ value: 'Percentage (%)', angle: -90, position: 'insideLeft' }}
                    />
                    <Tooltip />
                    <Legend />
                    <Line
                      type="monotone"
                      dataKey="Accuracy"
                      stroke="#3b82f6"
                      strokeWidth={2}
                      dot={{ r: 4 }}
                    />
                    <Line
                      type="monotone"
                      dataKey="Precision"
                      stroke="#10b981"
                      strokeWidth={2}
                      dot={{ r: 4 }}
                    />
                    <Line
                      type="monotone"
                      dataKey="Recall"
                      stroke="#f59e0b"
                      strokeWidth={2}
                      dot={{ r: 4 }}
                    />
                  </LineChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>

            {/* Corrections Per Iteration */}
            <Card>
              <CardHeader>
                <CardTitle className="text-base">Corrections Per Iteration</CardTitle>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={250}>
                  <BarChart data={correctionsData}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                    <XAxis dataKey="iteration" />
                    <YAxis />
                    <Tooltip />
                    <Legend />
                    <Bar dataKey="Flagged" fill="#f59e0b" />
                    <Bar dataKey="Corrected" fill="#10b981" />
                    <Bar dataKey="Reviewed" fill="#3b82f6" />
                  </BarChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>

            {/* Noise Reduction */}
            <Card>
              <CardHeader>
                <CardTitle className="text-base">Noise Reduction Over Time</CardTitle>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={250}>
                  <LineChart data={noiseData}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                    <XAxis
                      dataKey="iteration"
                      label={{ value: 'Iteration', position: 'insideBottom', offset: -5 }}
                    />
                    <YAxis
                      domain={[0, experiment.noise_percentage + 5]}
                      label={{ value: 'Noise (%)', angle: -90, position: 'insideLeft' }}
                    />
                    <Tooltip />
                    <Legend />
                    <Line
                      type="monotone"
                      dataKey="Noise %"
                      stroke="#ef4444"
                      strokeWidth={2}
                      dot={{ r: 4 }}
                    />
                  </LineChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>
          </div>
        )}
      </DialogContent>
    </Dialog>
  );
}