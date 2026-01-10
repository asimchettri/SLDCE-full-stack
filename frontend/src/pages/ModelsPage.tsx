import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { modelAPI, datasetAPI } from '@/services/api';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { RefreshCw, AlertCircle, Award, BarChart3 } from 'lucide-react';
import { ModelCard } from '@/components/ModelCard';
import { ModelComparisonChart } from '../components/ModelComparisonChart';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';

export function ModelsPage() {
  const [selectedDatasetId, setSelectedDatasetId] = useState<number | undefined>();

  // Fetch datasets for filter
  const { data: datasets } = useQuery({
    queryKey: ['datasets'],
    queryFn: datasetAPI.getAll,
  });

  // Fetch models
  const {
    data: models,
    isLoading,
    error,
    refetch,
    isRefetching,
  } = useQuery({
    queryKey: ['models', selectedDatasetId],
    queryFn: () => modelAPI.getAll(selectedDatasetId),
  });

  // Fetch comparison data if dataset selected
  const { data: comparisonData } = useQuery({
    queryKey: ['model-comparison', selectedDatasetId],
    queryFn: () => modelAPI.compare(selectedDatasetId!),
    enabled: !!selectedDatasetId && !!models && models.length > 0,
  });

  if (isLoading) {
    return (
      <div className="flex flex-col items-center justify-center h-full space-y-4">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-purple-600"></div>
        <p className="text-gray-500">Loading models...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex flex-col items-center justify-center h-full space-y-4">
        <AlertCircle className="h-12 w-12 text-red-500" />
        <div className="text-center">
          <p className="text-lg font-semibold text-red-600">Error Loading Models</p>
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
          <h2 className="text-3xl font-bold tracking-tight">Models</h2>
          <p className="text-gray-500 mt-1">
            Manage trained models and compare performance
          </p>
        </div>
        <div className="flex gap-2">
          <Button
            variant="outline"
            onClick={() => refetch()}
            disabled={isRefetching}
          >
            <RefreshCw className={`mr-2 h-4 w-4 ${isRefetching ? 'animate-spin' : ''}`} />
            Refresh
          </Button>
        </div>
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
      {models && models.length > 0 && (
        <div className="grid gap-4 md:grid-cols-4">
          <Card>
            <CardContent className="pt-6">
              <div className="text-2xl font-bold">{models.length}</div>
              <p className="text-xs text-gray-500">Total Models</p>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="pt-6">
              <div className="text-2xl font-bold">
                {models.filter((m) => m.is_baseline).length}
              </div>
              <p className="text-xs text-gray-500">Baseline Models</p>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="pt-6">
              <div className="text-2xl font-bold text-green-600">
                {Math.max(
                  ...models.map((m) => (m.test_accuracy || m.train_accuracy || 0) * 100)
                ).toFixed(1)}
                %
              </div>
              <p className="text-xs text-gray-500">Best Accuracy</p>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="pt-6">
              <div className="text-2xl font-bold text-blue-600">
                {(
                  models.reduce(
                    (sum, m) => sum + (m.test_accuracy || m.train_accuracy || 0),
                    0
                  ) /
                  models.length *
                  100
                ).toFixed(1)}
                %
              </div>
              <p className="text-xs text-gray-500">Average Accuracy</p>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Model Comparison Chart */}
      {comparisonData && comparisonData.length > 0 && (
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center gap-2 mb-4">
              <BarChart3 className="h-5 w-5 text-purple-600" />
              <h3 className="text-lg font-semibold">Model Comparison</h3>
            </div>
            <ModelComparisonChart data={comparisonData} />
          </CardContent>
        </Card>
      )}

      {/* Empty State */}
      {models && models.length === 0 ? (
        <Card>
          <CardContent className="flex flex-col items-center justify-center py-16">
            <Award className="h-16 w-16 text-gray-400 mb-4" />
            <h3 className="text-lg font-semibold mb-2">No models yet</h3>
            <p className="text-sm text-gray-500 mb-6 text-center max-w-sm">
              Models will appear here after training. Start by training a model on your dataset.
            </p>
          </CardContent>
        </Card>
      ) : (
        /* Models Grid */
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {models?.map((model) => (
            <ModelCard key={model.id} model={model} />
          ))}
        </div>
      )}
    </div>
  );
}