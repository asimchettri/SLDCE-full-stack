import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { experimentAPI } from '@/services/api';
import type { Experiment } from '@/types/experiment';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { TrendingUp, Clock, Target, AlertCircle, PlayCircle, CheckCircle, XCircle } from 'lucide-react';

import { ExperimentDetailsDialog } from './ExperimentDetailsDialog';

interface ExperimentCardProps {
  experiment: Experiment;
}

export function ExperimentCard({ experiment }: ExperimentCardProps) {
  const [detailsOpen, setDetailsOpen] = useState(false);

  // Fetch summary
  const { data: summary } = useQuery({
    queryKey: ['experiment-summary', experiment.id],
    queryFn: () => experimentAPI.getSummary(experiment.id),
    enabled: detailsOpen,
  });

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed':
        return 'bg-green-100 text-green-800';
      case 'running':
        return 'bg-blue-100 text-blue-800';
      case 'failed':
        return 'bg-red-100 text-red-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed':
        return <CheckCircle className="h-4 w-4" />;
      case 'running':
        return <PlayCircle className="h-4 w-4" />;
      case 'failed':
        return <XCircle className="h-4 w-4" />;
      default:
        return <AlertCircle className="h-4 w-4" />;
    }
  };

  const accuracyImprovement = experiment.final_accuracy && experiment.baseline_accuracy
    ? ((experiment.final_accuracy - experiment.baseline_accuracy) * 100)
    : 0;

  return (
    <>
      <Card className="hover:shadow-lg transition-shadow">
        <CardHeader>
          <div className="flex items-start justify-between">
            <div className="flex-1">
              <div className="flex items-center gap-2 mb-1">
                <CardTitle className="text-lg">{experiment.name}</CardTitle>
                <Badge className={getStatusColor(experiment.status)}>
                  <span className="flex items-center gap-1">
                    {getStatusIcon(experiment.status)}
                    {experiment.status}
                  </span>
                </Badge>
              </div>
              <CardDescription>
                {experiment.description || 'No description'}
              </CardDescription>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {/* Progress */}
            <div>
              <div className="flex justify-between text-sm mb-1">
                <span className="text-gray-600">Progress</span>
                <span className="font-medium">
                  {experiment.current_iteration} / {experiment.max_iterations} iterations
                </span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-2">
                <div
                  className="bg-blue-600 h-2 rounded-full transition-all"
                  style={{
                    width: `${(experiment.current_iteration / experiment.max_iterations) * 100}%`,
                  }}
                />
              </div>
            </div>

            {/* Metrics Grid */}
            <div className="grid grid-cols-2 gap-3">
              {/* Noise Level */}
              <div className="bg-orange-50 p-3 rounded-lg">
                <div className="flex items-center gap-2 mb-1">
                  <AlertCircle className="h-4 w-4 text-orange-600" />
                  <span className="text-xs text-gray-600">Noise</span>
                </div>
                <div className="text-lg font-bold text-orange-700">
                  {experiment.noise_percentage}%
                </div>
              </div>

              {/* Accuracy Improvement */}
              {experiment.baseline_accuracy !== null && (
                <div className="bg-green-50 p-3 rounded-lg">
                  <div className="flex items-center gap-2 mb-1">
                    <TrendingUp className="h-4 w-4 text-green-600" />
                    <span className="text-xs text-gray-600">Improved</span>
                  </div>
                  <div className="text-lg font-bold text-green-700">
                    {accuracyImprovement > 0 ? '+' : ''}{accuracyImprovement.toFixed(1)}%
                  </div>
                </div>
              )}

              {/* Corrections */}
              <div className="bg-blue-50 p-3 rounded-lg">
                <div className="flex items-center gap-2 mb-1">
                  <Target className="h-4 w-4 text-blue-600" />
                  <span className="text-xs text-gray-600">Corrections</span>
                </div>
                <div className="text-lg font-bold text-blue-700">
                  {experiment.total_corrections}
                </div>
              </div>

              {/* Time */}
              {experiment.total_time_seconds !== null && (
                <div className="bg-purple-50 p-3 rounded-lg">
                  <div className="flex items-center gap-2 mb-1">
                    <Clock className="h-4 w-4 text-purple-600" />
                    <span className="text-xs text-gray-600">Time</span>
                  </div>
                  <div className="text-lg font-bold text-purple-700">
                    {(experiment.total_time_seconds / 60).toFixed(1)}m
                  </div>
                </div>
              )}
            </div>

            {/* Action Button */}
            <Button
              variant="outline"
              className="w-full"
              onClick={() => setDetailsOpen(true)}
            >
              View Details
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Details Dialog */}
      <ExperimentDetailsDialog
        experiment={experiment}
        summary={summary}
        open={detailsOpen}
        onOpenChange={setDetailsOpen}
      />
    </>
  );
}