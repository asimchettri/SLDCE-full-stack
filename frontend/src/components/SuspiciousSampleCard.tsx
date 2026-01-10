import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { detectionAPI } from '@/services/api';
import type { Detection } from '@/types/detection';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { AlertTriangle, ChevronRight, TrendingUp } from 'lucide-react';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';

interface SuspiciousSampleCardProps {
  detection: Detection;
}

export function SuspiciousSampleCard({ detection }: SuspiciousSampleCardProps) {
  const [detailsOpen, setDetailsOpen] = useState(false);

  // Fetch full details when dialog opens
  const { data: details } = useQuery({
    queryKey: ['detection-details', detection.id],
    queryFn: () => detectionAPI.getById(detection.id),
    enabled: detailsOpen,
  });

  const getPriorityColor = (priority: number) => {
    if (priority >= 0.8) return 'bg-red-100 text-red-800 border-red-200';
    if (priority >= 0.6) return 'bg-orange-100 text-orange-800 border-orange-200';
    return 'bg-yellow-100 text-yellow-800 border-yellow-200';
  };

  const getPriorityLabel = (priority: number) => {
    if (priority >= 0.8) return 'High';
    if (priority >= 0.6) return 'Medium';
    return 'Low';
  };

  return (
    <>
      <Card className="hover:shadow-md transition-shadow cursor-pointer" onClick={() => setDetailsOpen(true)}>
        <CardHeader className="pb-3">
          <div className="flex items-start justify-between">
            <div className="flex items-center gap-2">
              <AlertTriangle className="h-5 w-5 text-orange-500" />
              <CardTitle className="text-base">Sample #{detection.sample_id}</CardTitle>
            </div>
            <Badge className={getPriorityColor(detection.priority_score)}>
              {getPriorityLabel(detection.priority_score)}
            </Badge>
          </div>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            {/* Priority Score */}
            <div className="flex items-center justify-between">
              <span className="text-sm text-gray-600">Priority Score</span>
              <span className="text-sm font-bold">
                {(detection.priority_score * 100).toFixed(1)}%
              </span>
            </div>

            {/* Metrics */}
            <div className="grid grid-cols-2 gap-2 text-xs">
              <div className="bg-blue-50 p-2 rounded">
                <div className="text-gray-600">Confidence</div>
                <div className="font-semibold text-blue-700">
                  {(detection.confidence_score * 100).toFixed(1)}%
                </div>
              </div>
              <div className="bg-purple-50 p-2 rounded">
                <div className="text-gray-600">Anomaly</div>
                <div className="font-semibold text-purple-700">
                  {(detection.anomaly_score * 100).toFixed(1)}%
                </div>
              </div>
            </div>

            {/* Predicted Label */}
            <div className="flex items-center justify-between pt-2 border-t">
              <span className="text-sm text-gray-600">Predicted Label</span>
              <span className="text-sm font-semibold text-green-600">
                Class {detection.predicted_label}
              </span>
            </div>

            {/* View Details Button */}
            <Button variant="outline" size="sm" className="w-full">
              View Details
              <ChevronRight className="ml-2 h-4 w-4" />
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Details Dialog */}
      {/* Details Dialog */}
<Dialog open={detailsOpen} onOpenChange={setDetailsOpen}>
  <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
    <DialogHeader>
      <DialogTitle>Sample #{detection.sample_id} - Detection Details</DialogTitle>
      <DialogDescription>
        Detailed information about this suspicious sample
      </DialogDescription>
    </DialogHeader>

    {details ? (
      <div className="space-y-4 pb-4">
        {/* Labels Comparison */}
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Label Analysis</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-sm text-gray-600">Current Label:</span>
                <Badge variant="outline">Class {details.current_label}</Badge>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm text-gray-600">Predicted Label:</span>
                <Badge className="bg-green-100 text-green-800">
                  Class {details.predicted_label}
                </Badge>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm text-gray-600">Original Label:</span>
                <Badge variant="secondary">Class {details.original_label}</Badge>
              </div>
            </div>

            {details.current_label !== details.original_label && (
              <div className="mt-3 p-2 bg-orange-50 border border-orange-200 rounded text-sm text-orange-800">
                <AlertTriangle className="inline h-4 w-4 mr-1" />
                This sample has a noisy label (current ≠ original)
              </div>
            )}
          </CardContent>
        </Card>

        {/* Detection Metrics */}
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Detection Metrics</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-sm text-gray-600">Confidence Score:</span>
                <div className="flex items-center gap-2">
                  <div className="w-32 bg-gray-200 rounded-full h-2">
                    <div
                      className="bg-blue-600 h-2 rounded-full transition-all"
                      style={{ width: `${details.confidence_score * 100}%` }}
                    />
                  </div>
                  <span className="text-sm font-semibold">
                    {(details.confidence_score * 100).toFixed(1)}%
                  </span>
                </div>
              </div>

              <div className="flex items-center justify-between">
                <span className="text-sm text-gray-600">Anomaly Score:</span>
                <div className="flex items-center gap-2">
                  <div className="w-32 bg-gray-200 rounded-full h-2">
                    <div
                      className="bg-purple-600 h-2 rounded-full transition-all"
                      style={{ width: `${details.anomaly_score * 100}%` }}
                    />
                  </div>
                  <span className="text-sm font-semibold">
                    {(details.anomaly_score * 100).toFixed(1)}%
                  </span>
                </div>
              </div>

              <div className="flex items-center justify-between">
                <span className="text-sm text-gray-600">Priority Score:</span>
                <div className="flex items-center gap-2">
                  <div className="w-32 bg-gray-200 rounded-full h-2">
                    <div
                      className="bg-orange-600 h-2 rounded-full transition-all"
                      style={{ width: `${details.priority_score * 100}%` }}
                    />
                  </div>
                  <span className="text-sm font-semibold">
                    {(details.priority_score * 100).toFixed(1)}%
                  </span>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Features */}
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Sample Features</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-4 gap-2">
              {details.features?.map((feature: number, idx: number) => (
                <div key={idx} className="bg-gray-50 p-2 rounded text-center">
                  <div className="text-xs text-gray-600">F{idx + 1}</div>
                  <div className="text-sm font-semibold">{feature.toFixed(2)}</div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        {/* Recommendation */}
        <Card className="bg-blue-50 border-blue-200">
          <CardContent className="pt-4">
            <div className="flex items-start gap-3">
              <TrendingUp className="h-5 w-5 text-blue-600 mt-0.5 shrink-0" />
              <div>
                <h4 className="font-semibold text-blue-900">Recommendation</h4>
                <p className="text-sm text-blue-800 mt-1">
                  Based on high confidence ({(details.confidence_score * 100).toFixed(1)}%) and
                  anomaly detection, this sample should be reviewed. The model predicts
                  Class {details.predicted_label} instead of the current Class {details.current_label}.
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    ) : (
      <div className="flex items-center justify-center py-8">
        <div className="text-gray-500">Loading details...</div>
      </div>
    )}
  </DialogContent>
</Dialog>
    </>
  );
}