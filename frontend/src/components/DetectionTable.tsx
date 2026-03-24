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

function SignalBadges({ signalBreakdown }: { signalBreakdown: string | null | undefined }) {
  if (!signalBreakdown) return <span className="text-xs text-gray-400">—</span>;

  let parsed: Record<string, any> = {};
  try {
    parsed = JSON.parse(signalBreakdown);
  } catch {
    return <span className="text-xs text-gray-400">—</span>;
  }

  const dominant = parsed.dominant_signal;
  const labelMismatch = parsed.label_mismatch;
  const noisePct = parsed.noise_probability != null
    ? (parsed.noise_probability * 100).toFixed(0) + "%"
    : null;

  return (
    <div className="flex flex-wrap gap-1">
      {/* Dominant signal badge */}
      {dominant === "both" && (
        <span className="inline-flex items-center px-1.5 py-0.5 rounded text-xs font-medium bg-red-100 text-red-700 border border-red-200">
          ⚡ Both High
        </span>
      )}
      {dominant === "confidence" && (
        <span className="inline-flex items-center px-1.5 py-0.5 rounded text-xs font-medium bg-blue-100 text-blue-700 border border-blue-200">
          🎯 Confidence
        </span>
      )}
      {dominant === "anomaly" && (
        <span className="inline-flex items-center px-1.5 py-0.5 rounded text-xs font-medium bg-purple-100 text-purple-700 border border-purple-200">
          👾 Anomaly
        </span>
      )}

      {/* Label mismatch badge */}
      {labelMismatch && (
        <span className="inline-flex items-center px-1.5 py-0.5 rounded text-xs font-medium bg-orange-100 text-orange-700 border border-orange-200">
          ⚠ Mismatch
        </span>
      )}

      {/* Noise probability */}
      {noisePct && (
        <span className="inline-flex items-center px-1.5 py-0.5 rounded text-xs font-medium bg-gray-100 text-gray-600 border border-gray-200">
          ~{noisePct} noise
        </span>
      )}
    </div>
  );
}

// ─── Confidence Histogram ─────────────────────────────────────────────────────

function ConfidenceHistogram({ detections }: { detections: Detection[] }) {
  if (detections.length === 0) return null;

  const BINS = 10;
  const counts = new Array(BINS).fill(0);
  for (const d of detections) {
    const bin = Math.min(Math.floor(d.confidence_score * BINS), BINS - 1);
    counts[bin]++;
  }
  const maxCount = Math.max(...counts, 1);

  const W = 400;
  const H = 100;
  const PAD = { top: 8, right: 8, bottom: 28, left: 30 };
  const chartW = W - PAD.left - PAD.right;
  const chartH = H - PAD.top - PAD.bottom;
  const barW = chartW / BINS - 2;

  return (
    <div className="mb-4">
      <p className="text-xs font-semibold text-gray-600 mb-1 uppercase tracking-wide">
        Confidence Score Distribution
      </p>
      <svg viewBox={`0 0 ${W} ${H}`} className="w-full max-w-lg" style={{ fontFamily: "monospace" }}>
        {/* Y gridlines */}
        {[0, 0.5, 1].map((v) => {
          const y = PAD.top + chartH - v * chartH;
          return (
            <g key={v}>
              <line x1={PAD.left} y1={y} x2={PAD.left + chartW} y2={y}
                stroke="#e5e7eb" strokeWidth={1} strokeDasharray="3 2" />
              <text x={PAD.left - 4} y={y + 3} textAnchor="end"
                fontSize={8} fill="#9ca3af">{Math.round(v * maxCount)}</text>
            </g>
          );
        })}

        {/* Bars */}
        {counts.map((count, i) => {
          const barH = (count / maxCount) * chartH;
          const x = PAD.left + i * (chartW / BINS) + 1;
          const y = PAD.top + chartH - barH;
          // Color: red for high confidence (suspicious), blue for low
          const pct = i / BINS;
          const color = pct >= 0.8 ? "#ef4444" : pct >= 0.6 ? "#f59e0b" : "#3b82f6";
          return (
            <g key={i}>
              <rect x={x} y={y} width={barW} height={barH}
                fill={color} rx={2} opacity={0.8} />
              {count > 0 && (
                <text x={x + barW / 2} y={y - 2} textAnchor="middle"
                  fontSize={7} fill={color}>{count}</text>
              )}
              <text x={x + barW / 2} y={H - PAD.bottom + 10} textAnchor="middle"
                fontSize={7} fill="#9ca3af">
                {(i / BINS * 100).toFixed(0)}
              </text>
            </g>
          );
        })}

        {/* Axes */}
        <line x1={PAD.left} y1={PAD.top} x2={PAD.left} y2={PAD.top + chartH}
          stroke="#d1d5db" strokeWidth={1} />
        <line x1={PAD.left} y1={PAD.top + chartH} x2={PAD.left + chartW} y2={PAD.top + chartH}
          stroke="#d1d5db" strokeWidth={1} />
        <text x={PAD.left + chartW / 2} y={H - 2} textAnchor="middle"
          fontSize={8} fill="#9ca3af">Confidence Score (%)</text>
      </svg>
      <div className="flex gap-3 mt-1">
        <span className="flex items-center gap-1 text-xs text-gray-500">
          <span className="w-2 h-2 rounded-sm bg-blue-500 inline-block" /> Low (&lt;60%)
        </span>
        <span className="flex items-center gap-1 text-xs text-gray-500">
          <span className="w-2 h-2 rounded-sm bg-amber-500 inline-block" /> Medium (60–80%)
        </span>
        <span className="flex items-center gap-1 text-xs text-gray-500">
          <span className="w-2 h-2 rounded-sm bg-red-500 inline-block" /> High (&gt;80%)
        </span>
      </div>
    </div>
  );
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


  const sorted = [...detections].sort((a, b) => b.priority_score - a.priority_score);

  return (
    <>

    <ConfidenceHistogram detections={detections} />


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


        {details.signal_breakdown && (
                <div>
                  <p className="text-sm font-semibold mb-2">Signal Breakdown</p>
                  <div className="bg-gray-50 rounded-lg p-3 space-y-2">
                    <div className="flex flex-wrap gap-1.5 mb-2">
                      <SignalBadges signalBreakdown={JSON.stringify(details.signal_breakdown)} />
                    </div>
                    {details.signal_breakdown.priority_breakdown && (
                      <div className="grid grid-cols-3 gap-2 text-xs">
                        <div className="bg-white rounded p-2 border">
                          <div className="text-gray-500">Weighted</div>
                          <div className="font-semibold">{(details.signal_breakdown.priority_breakdown.weighted * 100).toFixed(1)}%</div>
                        </div>
                        <div className="bg-white rounded p-2 border">
                          <div className="text-gray-500">Agreement Bonus</div>
                          <div className="font-semibold text-emerald-600">+{(details.signal_breakdown.priority_breakdown.bonus * 100).toFixed(1)}%</div>
                        </div>
                        <div className="bg-white rounded p-2 border">
                          <div className="text-gray-500">Final</div>
                          <div className="font-semibold text-orange-600">{(details.signal_breakdown.priority_breakdown.final * 100).toFixed(1)}%</div>
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              )}

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