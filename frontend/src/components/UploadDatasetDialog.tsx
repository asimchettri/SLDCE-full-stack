import { useState } from 'react';
import { useMutation } from '@tanstack/react-query';
import { datasetAPI } from '@/services/api';
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
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'; // ADDED: Select component
import { Upload, CheckCircle, XCircle, Loader2, Info } from 'lucide-react'; // ADDED: Info icon

interface UploadDatasetDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onSuccess: () => void;
}

export function UploadDatasetDialog({
  open,
  onOpenChange,
  onSuccess,
}: UploadDatasetDialogProps) {
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [file, setFile] = useState<File | null>(null);
  const [labelColumn, setLabelColumn] = useState<string>('auto'); 

  const uploadMutation = useMutation({
    mutationFn: (data: { 
      file: File; 
      name: string; 
      description?: string;
      labelColumn?: string; // ADDED
    }) =>
      datasetAPI.upload(data.file, data.name, data.description, data.labelColumn), 
    onSuccess: () => {
      // Reset form
      setName('');
      setDescription('');
      setFile(null);
      setLabelColumn('auto');
      // Close dialog and refresh
      onSuccess();
    },
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!file || !name.trim()) return;

    uploadMutation.mutate({ 
      file, 
      name: name.trim(), 
      description: description.trim() || undefined,
      labelColumn: labelColumn === 'auto' ? undefined : labelColumn 
    });
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFile = e.target.files?.[0];
    if (selectedFile) {
      setFile(selectedFile);
      // Auto-fill name if empty
      if (!name) {
        const fileName = selectedFile.name.replace('.csv', '');
        setName(fileName);
      }
    }
  };

  const resetForm = () => {
    setName('');
    setDescription('');
    setFile(null);
    setLabelColumn('auto');
    uploadMutation.reset();
  };

  const handleClose = () => {
    if (!uploadMutation.isPending) {
      resetForm();
      onOpenChange(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={handleClose}>
      <DialogContent className="sm:max-w-[500px]">
        <DialogHeader>
          <DialogTitle>Upload Dataset</DialogTitle>
          <DialogDescription>
           
            Upload a CSV file with your dataset. The label column will be automatically detected.
          </DialogDescription>
        </DialogHeader>

        {uploadMutation.isSuccess ? (
          /* Success State */
          <div className="flex flex-col items-center justify-center py-8">
            <CheckCircle className="h-16 w-16 text-green-500 mb-4" />
            <h3 className="text-lg font-semibold mb-2">Upload Successful!</h3>
            <p className="text-sm text-gray-500 text-center mb-6">
              Your dataset has been uploaded and is ready to use.
            </p>
            <Button onClick={handleClose}>Done</Button>
          </div>
        ) : (
          /* Upload Form */
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="name">Dataset Name *</Label>
              <Input
                id="name"
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="e.g., Wine Dataset"
                required
                disabled={uploadMutation.isPending}
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="description">Description (Optional)</Label>
              <Input
                id="description"
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                placeholder="Brief description of your dataset"
                disabled={uploadMutation.isPending}
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="file">CSV File *</Label>
              <Input
                id="file"
                type="file"
                accept=".csv"
                onChange={handleFileChange}
                required
                disabled={uploadMutation.isPending}
              />
              {file && (
                <div className="flex items-center gap-2 mt-2 p-2 bg-blue-50 rounded text-sm text-blue-700">
                  <Upload className="h-4 w-4" />
                  <span className="flex-1">{file.name}</span>
                  <span className="text-xs text-blue-600">
                    {(file.size / 1024).toFixed(2)} KB
                  </span>
                </div>
              )}
            </div>

            {/* Label Column Selection */}
            <div className="space-y-2">
              <Label htmlFor="labelColumn">Label Column</Label>
              <Select
                value={labelColumn}
                onValueChange={setLabelColumn}
                disabled={uploadMutation.isPending}
              >
                <SelectTrigger id="labelColumn">
                  <SelectValue placeholder="Auto-detect label column" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="auto">
                    Auto-detect (Recommended)
                  </SelectItem>
                  <SelectItem value="class">
                    Column named "class"
                  </SelectItem>
                  <SelectItem value="label">
                    Column named "label"
                  </SelectItem>
                  <SelectItem value="target">
                    Column named "target"
                  </SelectItem>
                  <SelectItem value="first">
                    First column
                  </SelectItem>
                  <SelectItem value="last">
                    Last column
                  </SelectItem>
                </SelectContent>
              </Select>
              
              {/*  Help text */}
              <div className="flex items-start gap-2 mt-1 text-xs text-gray-500">
                <Info className="h-3 w-3 mt-0.5 shrink-0" />
                <p>
                  Auto-detect will look for columns named "class", "label", or "target", 
                  otherwise uses the last column.
                </p>
              </div>
            </div>

            {uploadMutation.isError && (
              <div className="flex items-start gap-2 p-3 bg-red-50 border border-red-200 rounded-lg">
                <XCircle className="h-5 w-5 text-red-600 shrink-0 mt-0.5" />
                <div className="text-sm">
                  <p className="font-medium text-red-900">Upload Failed</p>
                  <p className="text-red-700 mt-1">
                    {uploadMutation.error instanceof Error
                      ? uploadMutation.error.message
                      : 'An error occurred while uploading. Please try again.'}
                  </p>
                </div>
              </div>
            )}

            <div className="flex gap-3 pt-2">
              <Button
                type="button"
                variant="outline"
                onClick={handleClose}
                disabled={uploadMutation.isPending}
                className="flex-1"
              >
                Cancel
              </Button>
              <Button
                type="submit"
                disabled={!file || !name.trim() || uploadMutation.isPending}
                className="flex-1"
              >
                {uploadMutation.isPending ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    Uploading...
                  </>
                ) : (
                  <>
                    <Upload className="mr-2 h-4 w-4" />
                    Upload
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