import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { experimentAPI, datasetAPI } from '@/services/api';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { RefreshCw, AlertCircle, FlaskConical } from 'lucide-react';
import { ExperimentCard } from '@/components/ExperimentCard';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';

export function ExperimentsPage() {
  const [selectedDatasetId, setSelectedDatasetId] = useState<number | undefined>();

  // Fetch datasets for filter
  const { data: datasets } = useQuery({
    queryKey: ['datasets'],
    queryFn: datasetAPI.getAll,
  });

  // Fetch experiments
  const {
    data: experiments,
    isLoading,
    error,
    refetch,
    isRefetching,
  } = useQuery({
    queryKey: ['experiments', selectedDatasetId],
    queryFn: () => experimentAPI.getAll(selectedDatasetId),
  });

  if (isLoading) {
    return (
      <div className="flex flex-col items-center justify-center h-full space-y-4">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-green-600"></div>
        <p className="text-gray-500">Loading experiments...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex flex-col items-center justify-center h-full space-y-4">
        <AlertCircle className="h-12 w-12 text-red-500" />
        <div className="text-center">
          <p className="text-lg font-semibold text-red-600">Error Loading Experiments</p>
          <Button onClick={() => refetch()} className="mt-4">
            <RefreshCw className="mr-2 h-4 w-4" />
            Try Again
          </Button>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-3xl font-bold tracking-tight">Experiments</h2>
          <p className="text-gray-500 mt-1">
            Track and compare correction experiments
          </p>
        </div>
        <Button variant="outline" onClick={() => refetch()} disabled={isRefetching}>
          <RefreshCw className={`mr-2 h-4 w-4 ${isRefetching ? 'animate-spin' : ''}`} />
          Refresh
        </Button>
      </div>

      {/* Dataset Filter */}
      <Card>
        <CardContent className="pt-6">
          <div className="flex items-center gap-4">
            <label className="text-sm font-medium">Filter by Dataset:</label>
            <Select
              value={selectedDatasetId?.toString() || 'all'}
              onValueChange={(value: string) =>
                setSelectedDatasetId(value === 'all' ? undefined : parseInt(value))
              }
            >
              <SelectTrigger className="w-[300px]">
                <SelectValue placeholder="All Datasets" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Datasets</SelectItem>
                {datasets?.map((dataset) => (
                  <SelectItem key={dataset.id} value={dataset.id.toString()}>
                    {dataset.name}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        </CardContent>
      </Card>

      {/* Summary Stats */}
      {experiments && experiments.length > 0 && (
        <div className="grid gap-4 md:grid-cols-4">
          <Card>
            <CardContent className="pt-6">
              <div className="text-2xl font-bold">{experiments.length}</div>
              <p className="text-xs text-gray-500">Total Experiments</p>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="pt-6">
              <div className="text-2xl font-bold text-green-600">
                {experiments.filter((e) => e.status === 'completed').length}
              </div>
              <p className="text-xs text-gray-500">Completed</p>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="pt-6">
              <div className="text-2xl font-bold text-blue-600">
                {experiments.filter((e) => e.status === 'running').length}
              </div>
              <p className="text-xs text-gray-500">Running</p>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="pt-6">
              <div className="text-2xl font-bold text-orange-600">
                {experiments.reduce((sum, e) => sum + e.total_corrections, 0)}
              </div>
              <p className="text-xs text-gray-500">Total Corrections</p>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Empty State */}
      {experiments && experiments.length === 0 ? (
        <Card>
          <CardContent className="flex flex-col items-center justify-center py-16">
            <FlaskConical className="h-16 w-16 text-gray-400 mb-4" />
            <h3 className="text-lg font-semibold mb-2">No experiments yet</h3>
            <p className="text-sm text-gray-500 mb-6 text-center max-w-sm">
              Experiments will track your data correction progress across multiple iterations.
            </p>
          </CardContent>
        </Card>
      ) : (
        /* Experiments Grid */
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {experiments?.map((experiment) => (
            <ExperimentCard key={experiment.id} experiment={experiment} />
          ))}
        </div>
      )}
    </div>
  );
}