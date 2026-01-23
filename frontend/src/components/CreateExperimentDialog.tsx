import { useState } from 'react';
import { useMutation, useQuery } from '@tanstack/react-query';
import { experimentAPI, datasetAPI } from '@/services/api';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { FlaskConical, CheckCircle, XCircle, Loader2 } from 'lucide-react';

interface CreateExperimentDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onSuccess: () => void;
}

export function CreateExperimentDialog({
  open,
  onOpenChange,
  onSuccess,
}: CreateExperimentDialogProps) {
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [datasetId, setDatasetId] = useState<number | undefined>();
  const [noisePercentage, setNoisePercentage] = useState('15');
  const [detectionThreshold, setDetectionThreshold] = useState('0.7');
  const [maxIterations, setMaxIterations] = useState('5');

  //  Fetch datasets for selection
  const { data: datasets } = useQuery({
    queryKey: ['datasets'],
    queryFn: datasetAPI.getAll,
  });

  //  Create experiment mutation
  const createMutation = useMutation({
    mutationFn: (data: {
      dataset_id: number;
      name: string;
      description?: string;
      noise_percentage: number;
      detection_threshold?: number;
      max_iterations?: number;
    }) => experimentAPI.create(data),
    onSuccess: () => {
      // Reset form
      setName('');
      setDescription('');
      setDatasetId(undefined);
      setNoisePercentage('15');
      setDetectionThreshold('0.7');
      setMaxIterations('5');
      // Close dialog and refresh
      onSuccess();
    },
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!datasetId || !name.trim()) return;

    createMutation.mutate({
      dataset_id: datasetId,
      name: name.trim(),
      description: description.trim() || undefined,
      noise_percentage: parseFloat(noisePercentage),
      detection_threshold: parseFloat(detectionThreshold),
      max_iterations: parseInt(maxIterations),
    });
  };

  const resetForm = () => {
    setName('');
    setDescription('');
    setDatasetId(undefined);
    setNoisePercentage('15');
    setDetectionThreshold('0.7');
    setMaxIterations('5');
    createMutation.reset();
  };

  const handleClose = () => {
    if (!createMutation.isPending) {
      resetForm();
      onOpenChange(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={handleClose}>
      <DialogContent className="sm:max-w-[500px]">
        <DialogHeader>
          <DialogTitle>Create Experiment</DialogTitle>
          <DialogDescription>
            Set up a new experiment to track data correction progress
          </DialogDescription>
        </DialogHeader>

        {createMutation.isSuccess ? (
          /* Success State */
          <div className="flex flex-col items-center justify-center py-8">
            <CheckCircle className="h-16 w-16 text-green-500 mb-4" />
            <h3 className="text-lg font-semibold mb-2">Experiment Created!</h3>
            <p className="text-sm text-gray-500 text-center mb-6">
              Your experiment is ready. Start by running detection on your dataset.
            </p>
            <Button onClick={handleClose}>Done</Button>
          </div>
        ) : (
          /* Create Form */
          <form onSubmit={handleSubmit} className="space-y-4">
            {/* Dataset Selection */}
            <div className="space-y-2">
              <Label htmlFor="dataset">Dataset *</Label>
              <Select
                value={datasetId?.toString() || ''}
                onValueChange={(value) => setDatasetId(parseInt(value))}
                disabled={createMutation.isPending}
              >
                <SelectTrigger id="dataset">
                  <SelectValue placeholder="Select dataset" />
                </SelectTrigger>
                <SelectContent>
                  {datasets?.map((dataset) => (
                    <SelectItem key={dataset.id} value={dataset.id.toString()}>
                      {dataset.name} ({dataset.num_samples} samples)
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            {/* Experiment Name */}
            <div className="space-y-2">
              <Label htmlFor="name">Experiment Name *</Label>
              <Input
                id="name"
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="e.g., Wine Classification Correction"
                required
                disabled={createMutation.isPending}
              />
            </div>

            {/* Description */}
            <div className="space-y-2">
              <Label htmlFor="description">Description (Optional)</Label>
              <Input
                id="description"
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                placeholder="Brief description of experiment goals"
                disabled={createMutation.isPending}
              />
            </div>

            {/* Configuration Grid */}
            <div className="grid grid-cols-3 gap-4">
              {/* Noise Percentage */}
              <div className="space-y-2">
                <Label htmlFor="noise">
                  Noise %
                  <span className="text-xs text-gray-500 block">Expected error rate</span>
                </Label>
                <Input
                  id="noise"
                  type="number"
                  min="0"
                  max="100"
                  step="0.1"
                  value={noisePercentage}
                  onChange={(e) => setNoisePercentage(e.target.value)}
                  disabled={createMutation.isPending}
                />
              </div>

              {/* Detection Threshold */}
              <div className="space-y-2">
                <Label htmlFor="threshold">
                  Threshold
                  <span className="text-xs text-gray-500 block">Confidence cutoff</span>
                </Label>
                <Input
                  id="threshold"
                  type="number"
                  min="0"
                  max="1"
                  step="0.1"
                  value={detectionThreshold}
                  onChange={(e) => setDetectionThreshold(e.target.value)}
                  disabled={createMutation.isPending}
                />
              </div>

              {/* Max Iterations */}
              <div className="space-y-2">
                <Label htmlFor="iterations">
                  Max Iter.
                  <span className="text-xs text-gray-500 block">Correction loops</span>
                </Label>
                <Input
                  id="iterations"
                  type="number"
                  min="1"
                  max="50"
                  value={maxIterations}
                  onChange={(e) => setMaxIterations(e.target.value)}
                  disabled={createMutation.isPending}
                />
              </div>
            </div>

            {/* Error Display */}
            {createMutation.isError && (
              <div className="flex items-start gap-2 p-3 bg-red-50 border border-red-200 rounded-lg">
                <XCircle className="h-5 w-5 text-red-600 shrink-0 mt-0.5" />
                <div className="text-sm">
                  <p className="font-medium text-red-900">Creation Failed</p>
                  <p className="text-red-700 mt-1">
                    {createMutation.error instanceof Error
                      ? createMutation.error.message
                      : 'An error occurred. Please try again.'}
                  </p>
                </div>
              </div>
            )}

            {/* Action Buttons */}
            <div className="flex gap-3 pt-2">
              <Button
                type="button"
                variant="outline"
                onClick={handleClose}
                disabled={createMutation.isPending}
                className="flex-1"
              >
                Cancel
              </Button>
              <Button
                type="submit"
                disabled={!datasetId || !name.trim() || createMutation.isPending}
                className="flex-1"
              >
                {createMutation.isPending ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    Creating...
                  </>
                ) : (
                  <>
                    <FlaskConical className="mr-2 h-4 w-4" />
                    Create Experiment
                  </>
                )}
              </Button>
            </div>
          </form>
        )}
      </DialogContent>
    </Dialog>
  );
}