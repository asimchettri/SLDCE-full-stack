import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { datasetAPI } from "@/services/api";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Plus, Upload, AlertCircle, RefreshCw } from "lucide-react";
import { UploadDatasetDialog } from "@/components/UploadDatasetDialog";
import { DatasetCard } from "@/components/DatasetCard";

export function DatasetsPage() {
  const [uploadDialogOpen, setUploadDialogOpen] = useState(false);

  const {
    data: datasets,
    isLoading,
    error,
    refetch,
    isRefetching,
  } = useQuery({
    queryKey: ["datasets"],
    queryFn: datasetAPI.getAll,
    refetchOnMount: true,
  });

  // Loading state
  if (isLoading) {
    return (
      <div className="flex flex-col items-center justify-center h-full space-y-4">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
        <p className="text-gray-500">Loading datasets...</p>
      </div>
    );
  }

  // Error state
  if (error) {
    return (
      <div className="flex flex-col items-center justify-center h-full space-y-4">
        <AlertCircle className="h-12 w-12 text-red-500" />
        <div className="text-center">
          <p className="text-lg font-semibold text-red-600">
            Error Loading Datasets
          </p>
          <p className="text-sm text-gray-500 mt-1">
            {error instanceof Error
              ? error.message
              : "Failed to fetch datasets"}
          </p>
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
          <h2 className="text-3xl font-bold tracking-tight">Datasets</h2>
          <p className="text-gray-500 mt-1">
            Manage your datasets and upload new data
          </p>
        </div>
        <div className="flex gap-2">
          <Button
            variant="outline"
            onClick={() => refetch()}
            disabled={isRefetching}
          >
            <RefreshCw
              className={`mr-2 h-4 w-4 ${isRefetching ? "animate-spin" : ""}`}
            />
            Refresh
          </Button>
          <Button onClick={() => setUploadDialogOpen(true)}>
            <Plus className="mr-2 h-4 w-4" />
            Upload Dataset
          </Button>
        </div>
      </div>

      {/* Summary Stats */}
      {datasets && datasets.length > 0 && (
        <div className="grid gap-4 md:grid-cols-3">
          <Card>
            <CardContent className="pt-6">
              <div className="text-2xl font-bold">{datasets.length}</div>
              <p className="text-xs text-gray-500">Total Datasets</p>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="pt-6">
              <div className="text-2xl font-bold">
                {datasets
                  .reduce((sum, d) => sum + d.num_samples, 0)
                  .toLocaleString()}
              </div>
              <p className="text-xs text-gray-500">Total Samples</p>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="pt-6">
              <div className="text-2xl font-bold">
                {Math.max(...datasets.map((d) => d.num_features))}
              </div>
              <p className="text-xs text-gray-500">Max Features</p>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Empty State */}
      {datasets && datasets.length === 0 ? (
        <Card>
          <CardContent className="flex flex-col items-center justify-center py-16">
            <Upload className="h-16 w-16 text-gray-400 mb-4" />
            <h3 className="text-lg font-semibold mb-2">No datasets yet</h3>
            <p className="text-sm text-gray-500 mb-6 text-center max-w-sm">
              Get started by uploading your first dataset. CSV files with
              labeled data are supported.
            </p>
            <Button onClick={() => setUploadDialogOpen(true)} size="lg">
              <Plus className="mr-2 h-5 w-5" />
              Upload Your First Dataset
            </Button>
          </CardContent>
        </Card>
      ) : (
        /* Dataset Grid */
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {datasets?.map((dataset) => (
            <DatasetCard key={dataset.id} dataset={dataset} />
          ))}
        </div>
      )}

      {/* Upload Dialog */}
      <UploadDatasetDialog
        open={uploadDialogOpen}
        onOpenChange={setUploadDialogOpen}
        onSuccess={() => {
          refetch();
          setUploadDialogOpen(false);
        }}
      />
    </div>
  );
}
