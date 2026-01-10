import { useState } from 'react';
import type { Detection } from '@/types/detection';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Eye } from 'lucide-react';
import { ConfidenceVisualization } from './ConfidenceVisualization';
import { useQuery } from '@tanstack/react-query';
import { detectionAPI } from '@/services/api';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';

interface DetectionTableProps {
  detections: Detection[];
}

export function DetectionTable({ detections }: DetectionTableProps) {
  const [selectedDetection, setSelectedDetection] = useState<Detection | null>(null);

  const { data: details } = useQuery({
    queryKey: ['detection-details', selectedDetection?.id],
    queryFn: () => detectionAPI.getById(selectedDetection!.id),
    enabled: !!selectedDetection,
  });

  const getPriorityBadge = (priority: number) => {
    if (priority >= 0.8) {
      return <Badge className="bg-red-100 text-red-800">High</Badge>;
    }
    if (priority >= 0.6) {
      return <Badge className="bg-orange-100 text-orange-800">Medium</Badge>;
    }
    return <Badge className="bg-yellow-100 text-yellow-800">Low</Badge>;
  };

  return (
    <>
      <div className="rounded-md border">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead className="w-[100px]">Sample ID</TableHead>
              <TableHead>Priority</TableHead>
              <TableHead>Confidence</TableHead>
              <TableHead>Anomaly</TableHead>
              <TableHead>Priority Score</TableHead>
              <TableHead>Predicted Label</TableHead>
              <TableHead className="text-right">Actions</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {detections.map((detection) => (
              <TableRow key={detection.id} className="cursor-pointer hover:bg-gray-50">
                <TableCell className="font-medium">#{detection.sample_id}</TableCell>
                <TableCell>{getPriorityBadge(detection.priority_score)}</TableCell>
                <TableCell>
                  <ConfidenceVisualization
                    value={detection.confidence_score}
                    label="Confidence"
                    color="blue"
                    size="sm"
                  />
                </TableCell>
                <TableCell>
                  <ConfidenceVisualization
                    value={detection.anomaly_score}
                    label="Anomaly"
                    color="purple"
                    size="sm"
                  />
                </TableCell>
                <TableCell>
                  <span className="font-semibold">
                    {(detection.priority_score * 100).toFixed(1)}%
                  </span>
                </TableCell>
                <TableCell>
                  <Badge variant="outline">Class {detection.predicted_label}</Badge>
                </TableCell>
                <TableCell className="text-right">
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => setSelectedDetection(detection)}
                  >
                    <Eye className="h-4 w-4" />
                  </Button>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </div>

      {/* Details Dialog */}
     {/* Details Dialog */}
<Dialog
  open={!!selectedDetection}
  onOpenChange={(open) => !open && setSelectedDetection(null)}
>
  <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
    <DialogHeader>
      <DialogTitle>Sample #{selectedDetection?.sample_id} - Details</DialogTitle>
      <DialogDescription>
        Complete detection information
      </DialogDescription>
    </DialogHeader>

    {details && (
      <div className="space-y-4 pb-4">
        {/* Labels */}
        <div className="grid grid-cols-3 gap-4">
          <div className="space-y-1">
            <p className="text-sm text-gray-600">Current Label</p>
            <Badge variant="outline" className="text-base">
              Class {details.current_label}
            </Badge>
          </div>
          <div className="space-y-1">
            <p className="text-sm text-gray-600">Predicted Label</p>
            <Badge className="bg-green-100 text-green-800 text-base">
              Class {details.predicted_label}
            </Badge>
          </div>
          <div className="space-y-1">
            <p className="text-sm text-gray-600">Original Label</p>
            <Badge variant="secondary" className="text-base">
              Class {details.original_label}
            </Badge>
          </div>
        </div>

        {/* Metrics */}
        <div className="space-y-3">
          <ConfidenceVisualization
            value={details.confidence_score}
            label="Confidence Score"
            color="blue"
          />
          <ConfidenceVisualization
            value={details.anomaly_score}
            label="Anomaly Score"
            color="purple"
          />
          <ConfidenceVisualization
            value={details.priority_score}
            label="Priority Score"
            color="orange"
          />
        </div>

        {/* Features */}
        <div>
          <p className="text-sm font-semibold mb-2">Sample Features</p>
          <div className="grid grid-cols-4 gap-2">
            {details.features?.map((feature: number, idx: number) => (
              <div key={idx} className="bg-gray-50 p-2 rounded text-center">
                <div className="text-xs text-gray-600">F{idx + 1}</div>
                <div className="text-sm font-semibold">{feature.toFixed(2)}</div>
              </div>
            ))}
          </div>
        </div>
      </div>
    )}
  </DialogContent>
</Dialog>
    </>
  );
}