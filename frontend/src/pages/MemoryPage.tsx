import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { memoryAPI, datasetAPI } from "@/services/api";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Label } from "@/components/ui/label";
import {
  AlertCircle,
  RefreshCw,
  Brain,
  Zap,
  Activity,
  Target,
  TrendingUp,
  CheckCircle,
  XCircle,
  Play,
} from "lucide-react";
import { useNavigate } from "react-router-dom";

function fmt(val: number | null | undefined, decimals = 3): string {
  if (val == null) return "—";
  return val.toFixed(decimals);
}

function fmtPct(val: number | null | undefined): string {
  if (val == null) return "—";
  return (val * 100).toFixed(1) + "%";
}

function LineChart({
  series,
  color,
  formatY = (v: number) => v.toFixed(3),
}: {
  series: (number | null)[];
  color: string;
  label: string;
  formatY?: (v: number) => string;
}) {
  const W = 400,
    H = 140;
  const PAD = { top: 16, right: 16, bottom: 32, left: 44 };
  const chartW = W - PAD.left - PAD.right;
  const chartH = H - PAD.top - PAD.bottom;
  const valid = series.filter((v): v is number => v != null);
  if (valid.length === 0) {
    return (
      <div className="flex items-center justify-center h-24 text-gray-400 text-xs">
        No data yet — run a learning cycle first
      </div>
    );
  }
  const minVal = Math.min(...valid);
  const maxVal = Math.max(...valid);
  const range = maxVal - minVal || 1;
  const xScale = (i: number) =>
    PAD.left + (i / Math.max(series.length - 1, 1)) * chartW;
  const yScale = (v: number) =>
    PAD.top + chartH - ((v - minVal) / range) * chartH;
  const points = series
    .map((v, i) => (v != null ? { x: xScale(i), y: yScale(v), v, i } : null))
    .filter(Boolean) as { x: number; y: number; v: number; i: number }[];
  const polyline = points.map((p) => `${p.x},${p.y}`).join(" ");
  const yTicks = [minVal, (minVal + maxVal) / 2, maxVal];
  return (
    <svg
      viewBox={`0 0 ${W} ${H}`}
      className="w-full"
      style={{ fontFamily: "monospace" }}
    >
      {yTicks.map((v, i) => {
        const y = yScale(v);
        return (
          <g key={i}>
            <line
              x1={PAD.left}
              y1={y}
              x2={PAD.left + chartW}
              y2={y}
              stroke="#e5e7eb"
              strokeWidth={1}
              strokeDasharray="4 3"
            />
            <text
              x={PAD.left - 5}
              y={y + 4}
              textAnchor="end"
              fontSize={8}
              fill="#9ca3af"
            >
              {formatY(v)}
            </text>
          </g>
        );
      })}
      {points.length > 1 && (
        <polygon
          points={`${PAD.left},${PAD.top + chartH} ${polyline} ${points[points.length - 1].x},${PAD.top + chartH}`}
          fill={color}
          opacity={0.08}
        />
      )}
      {points.length > 1 && (
        <polyline
          points={polyline}
          fill="none"
          stroke={color}
          strokeWidth={2}
          strokeLinejoin="round"
          strokeLinecap="round"
        />
      )}
      {points.map((p) => (
        <circle
          key={p.i}
          cx={p.x}
          cy={p.y}
          r={3.5}
          fill={color}
          stroke="white"
          strokeWidth={1.5}
        />
      ))}
      {points.map((p) => (
        <text
          key={p.i}
          x={p.x}
          y={H - PAD.bottom + 13}
          textAnchor="middle"
          fontSize={8}
          fill="#9ca3af"
        >
          {p.i + 1}
        </text>
      ))}
      <line
        x1={PAD.left}
        y1={PAD.top}
        x2={PAD.left}
        y2={PAD.top + chartH}
        stroke="#d1d5db"
        strokeWidth={1}
      />
      <line
        x1={PAD.left}
        y1={PAD.top + chartH}
        x2={PAD.left + chartW}
        y2={PAD.top + chartH}
        stroke="#d1d5db"
        strokeWidth={1}
      />
      <text
        x={PAD.left + chartW / 2}
        y={H - 2}
        textAnchor="middle"
        fontSize={8}
        fill="#9ca3af"
      >
        Cycle
      </text>
    </svg>
  );
}

function StatCard({
  label,
  value,
  sub,
  icon: Icon,
  color,
}: {
  label: string;
  value: string;
  sub?: string;
  icon: React.ElementType;
  color: string;
}) {
  return (
    <div className="bg-white rounded-xl border border-gray-100 p-4 flex items-start gap-3 shadow-sm">
      <div className={`rounded-lg p-2 ${color}`}>
        <Icon className="h-4 w-4" />
      </div>
      <div className="min-w-0">
        <p className="text-xs text-gray-500 font-medium truncate">{label}</p>
        <p className="text-xl font-bold text-gray-900 tracking-tight">
          {value}
        </p>
        {sub && <p className="text-xs text-gray-400 mt-0.5">{sub}</p>}
      </div>
    </div>
  );
}

function CycleTable({ history }: { history: Record<string, any>[] }) {
  if (history.length === 0) {
    return (
      <div className="text-center py-10 text-gray-400 text-sm">
        No cycles recorded yet. Trigger a learning cycle to see history.
      </div>
    );
  }
  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b bg-gray-50">
            {[
              "Cycle",
              "Threshold",
              "Accuracy",
              "F1 Macro",
              "Correction Precision",
              "Flagged",
            ].map((h) => (
              <th
                key={h}
                className={`px-4 py-2.5 font-semibold text-gray-600 text-xs uppercase tracking-wide ${h === "Cycle" ? "text-left" : "text-right"}`}
              >
                {h}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {history.map((row, i) => (
            <tr key={i} className="border-b hover:bg-gray-50 transition-colors">
              <td className="px-4 py-2.5 font-medium text-gray-700">
                #{row.cycle ?? i + 1}
              </td>
              <td className="text-right px-4 py-2.5 font-mono text-gray-700">
                {fmt(row.threshold)}
              </td>
              <td className="text-right px-4 py-2.5 font-mono text-gray-700">
                {fmtPct(row.accuracy)}
              </td>
              <td className="text-right px-4 py-2.5 font-mono text-gray-600">
                {fmt(row.f1_macro)}
              </td>
              <td className="text-right px-4 py-2.5 font-mono text-gray-600">
                {fmtPct(row.correction_precision)}
              </td>
              <td className="text-right px-4 py-2.5 font-mono text-gray-500">
                {row.n_flagged ?? "—"}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export function MemoryPage() {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [selectedDatasetId, setSelectedDatasetId] = useState<number | null>(
    null,
  );

  // Fetch real datasets from DB
  const { data: datasets, isLoading: loadingDatasets } = useQuery({
    queryKey: ["datasets"],
    queryFn: datasetAPI.getAll,
  });

  const datasetId = selectedDatasetId ?? null;

  const {
    data: thresholdData,
    isLoading: thresholdLoading,
    refetch: refetchThreshold,
  } = useQuery({
    queryKey: ["memory-threshold", datasetId],
    queryFn: () => memoryAPI.getThreshold(datasetId!),
    enabled: datasetId !== null,
  });

  const {
    data: analyticsData,
    isLoading: analyticsLoading,
    refetch: refetchAnalytics,
  } = useQuery({
    queryKey: ["memory-analytics", datasetId],
    queryFn: () => memoryAPI.getAnalytics(datasetId!),
    enabled: datasetId !== null,
  });

  const { data: statusData } = useQuery({
    queryKey: ["memory-status", datasetId],
    queryFn: () => memoryAPI.getStatus(datasetId!),
    enabled: datasetId !== null,
  });

  const cycleMutation = useMutation({
    mutationFn: () => memoryAPI.updateThreshold(datasetId!),
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: ["memory-threshold", datasetId],
      });
      queryClient.invalidateQueries({
        queryKey: ["memory-analytics", datasetId],
      });
      queryClient.invalidateQueries({ queryKey: ["memory-status", datasetId] });
    },
  });

  const isLoading = thresholdLoading || analyticsLoading;

  const history: Record<string, any>[] = analyticsData?.full_history ?? [];
  const thresholdHistory: (number | null)[] =
    analyticsData?.threshold_history ?? [];
  const accuracyHistory: (number | null)[] =
    analyticsData?.accuracy_history ?? [];
  const f1History: (number | null)[] = analyticsData?.f1_macro_history ?? [];
  const corrPrecHistory: (number | null)[] =
    analyticsData?.correction_precision_history ?? [];
  const totalCycles: number = analyticsData?.total_cycles ?? 0;

  const isFitted = thresholdData?.fitted ?? false;
  const currentThreshold = thresholdData?.threshold;
  const feedbackCount = thresholdData?.feedback_count ?? 0;
  const latestCycle = history[history.length - 1] ?? null;

  function refetchAll() {
    refetchThreshold();
    refetchAnalytics();
  }

  // ── Empty state: no datasets at all ──────────────────────────────────────
  if (!loadingDatasets && (!datasets || datasets.length === 0)) {
    return (
      <div className="space-y-6">
        <div>
          <h2 className="text-2xl font-bold tracking-tight text-gray-900">
            Memory & Learning
          </h2>
          <p className="text-gray-500 text-sm mt-1">
            Engine state, adaptive threshold, and learning history
          </p>
        </div>
        <Card>
          <CardContent className="flex flex-col items-center justify-center py-20 gap-4">
            <Brain className="h-14 w-14 text-gray-300" />
            <div className="text-center">
              <h3 className="text-lg font-semibold text-gray-700">
                No Datasets Yet
              </h3>
              <p className="text-sm text-gray-500 mt-1 max-w-sm">
                Upload a dataset and run detection before using the Memory page.
              </p>
            </div>
            <Button onClick={() => navigate("/datasets")} className="gap-2">
              Go to Datasets
            </Button>
          </CardContent>
        </Card>
      </div>
    );
  }

  // ── Empty state: dataset selected but engine not fitted ───────────────────
  const showNotFittedBanner = datasetId !== null && !isLoading && !isFitted;

  return (
    <div className="space-y-6 pb-8">
      {/* Header */}
      <div className="flex items-start justify-between">
        <div>
          <h2 className="text-2xl font-bold tracking-tight text-gray-900">
            Memory & Learning
          </h2>
          <p className="text-gray-500 text-sm mt-1">
            Engine state, adaptive threshold, and longitudinal learning history
          </p>
        </div>
        <div className="flex gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={refetchAll}
            disabled={isLoading || datasetId === null}
          >
            <RefreshCw
              className={`mr-1.5 h-3.5 w-3.5 ${isLoading ? "animate-spin" : ""}`}
            />
            Refresh
          </Button>
          <Button
            size="sm"
            onClick={() => cycleMutation.mutate()}
            disabled={
              cycleMutation.isPending || !isFitted || datasetId === null
            }
            title={
              !isFitted
                ? "Run detection first to fit the engine"
                : feedbackCount === 0
                  ? "Submit feedback on suggestions before running a learning cycle"
                  : ""
            }
          >
            <Zap className="mr-1.5 h-3.5 w-3.5" />
            {cycleMutation.isPending ? "Running..." : "Trigger Learning Cycle"}
          </Button>
        </div>
      </div>

      {/* Dataset selector — from real DB */}
      <div className="flex items-center gap-3">
        <Label className="text-sm font-medium text-gray-600 shrink-0">
          Dataset
        </Label>
        <Select
          value={selectedDatasetId?.toString() ?? ""}
          onValueChange={(v) => setSelectedDatasetId(Number(v))}
        >
          <SelectTrigger className="w-64">
            <SelectValue placeholder="Select a dataset" />
          </SelectTrigger>
          <SelectContent>
            {datasets?.map((d) => (
              <SelectItem key={d.id} value={d.id.toString()}>
                {d.name}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      {/* No dataset selected */}
      {datasetId === null && (
        <Card>
          <CardContent className="flex flex-col items-center justify-center py-16 gap-3">
            <Activity className="h-12 w-12 text-gray-300" />
            <div className="text-center">
              <h3 className="text-lg font-semibold text-gray-600">
                Select a Dataset
              </h3>
              <p className="text-sm text-gray-500 mt-1">
                Choose a dataset above to view its engine status and learning
                history.
              </p>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Engine not fitted — prompt to run detection */}
      {showNotFittedBanner && (
        <Card className="border-amber-200 bg-amber-50">
          <CardContent className="flex items-center justify-between py-5 px-6">
            <div className="flex items-center gap-3">
              <AlertCircle className="h-5 w-5 text-amber-500 shrink-0" />
              <div>
                <p className="text-sm font-medium text-amber-800">
                  Engine not fitted for this dataset
                </p>
                <p className="text-xs text-amber-600 mt-0.5">
                  Run detection first to initialize the self-learning engine.
                </p>
              </div>
            </div>
            <Button
              size="sm"
              onClick={() => navigate("/detection")}
              className="shrink-0 bg-amber-600 hover:bg-amber-700 text-white"
            >
              <Play className="mr-1.5 h-3.5 w-3.5" />
              Go to Detection
            </Button>
          </CardContent>
        </Card>
      )}

      {isFitted && feedbackCount === 0 && !isLoading && datasetId !== null && (
        <div className="flex items-center gap-3 rounded-xl bg-blue-50 border border-blue-100 px-4 py-3">
          <AlertCircle className="h-4 w-4 text-blue-500 shrink-0" />
          <div className="text-sm text-blue-700">
            <span className="font-medium">No feedback yet.</span> Review
            correction suggestions and approve/reject them before triggering a
            learning cycle.
          </div>
          <Button
            size="sm"
            variant="outline"
            onClick={() => navigate("/correction")}
            className="shrink-0 border-blue-300 text-blue-700 hover:bg-blue-100 ml-auto"
          >
            Go to Corrections
          </Button>
        </div>
      )}

      {/* Banners */}
      {cycleMutation.isSuccess && (
        <div className="flex items-center gap-3 rounded-xl bg-emerald-50 border border-emerald-100 px-4 py-3">
          <CheckCircle className="h-4 w-4 text-emerald-500 shrink-0" />
          <div className="text-sm text-emerald-700">
            <span className="font-medium">Learning cycle complete.</span>{" "}
            Meta-model retrained, threshold updated
            {cycleMutation.data?.retrain?.retrained && ", ensemble retrained"}.
          </div>
        </div>
      )}

      {cycleMutation.isError && (
        <div className="flex items-center gap-3 rounded-xl bg-red-50 border border-red-100 px-4 py-3">
          <XCircle className="h-4 w-4 text-red-500 shrink-0" />
          <p className="text-sm text-red-700">
            {cycleMutation.error instanceof Error
              ? cycleMutation.error.message
              : "Learning cycle failed — check that the engine is fitted and feedback exists."}
          </p>
        </div>
      )}

      {/* Main content — only show when dataset selected */}
      {datasetId !== null && (
        <>
          {isLoading ? (
            <div className="flex items-center justify-center py-24">
              <div className="animate-spin rounded-full h-8 w-8 border-2 border-blue-600 border-t-transparent" />
            </div>
          ) : (
            <>
              {/* KPI Cards */}
              <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
                <StatCard
                  label="Engine Status"
                  value={isFitted ? "Fitted" : "Not Fitted"}
                  sub={isFitted ? "Ready for detection" : "Run detection first"}
                  icon={Brain}
                  color={
                    isFitted
                      ? "bg-emerald-100 text-emerald-700"
                      : "bg-gray-100 text-gray-500"
                  }
                />
                <StatCard
                  label="Current Threshold"
                  value={currentThreshold != null ? fmt(currentThreshold) : "—"}
                  sub="Decision boundary"
                  icon={Target}
                  color="bg-blue-100 text-blue-700"
                />
                <StatCard
                  label="Feedback Count"
                  value={`${feedbackCount}`}
                  sub="Human decisions recorded"
                  icon={Activity}
                  color="bg-violet-100 text-violet-700"
                />
                <StatCard
                  label="Cycles Completed"
                  value={`${totalCycles}`}
                  sub={
                    latestCycle
                      ? `Last accuracy: ${fmtPct(latestCycle.accuracy)}`
                      : "No cycles yet"
                  }
                  icon={TrendingUp}
                  color="bg-amber-100 text-amber-700"
                />
              </div>

              {/* Last cycle result */}
              {cycleMutation.isSuccess && cycleMutation.data && (
                <Card className="border-gray-100 shadow-sm">
                  <CardHeader className="pb-2">
                    <CardTitle className="text-sm font-semibold text-gray-700">
                      Last Learning Cycle Result
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 text-sm">
                      <div className="bg-gray-50 rounded-lg p-3">
                        <p className="text-xs text-gray-500 mb-1">Meta Model</p>
                        <p className="font-semibold text-gray-800">
                          {cycleMutation.data.meta_model?.trained
                            ? "Retrained"
                            : "Skipped"}
                        </p>
                        <p className="text-xs text-gray-400 mt-0.5">
                          {cycleMutation.data.meta_model?.feedback_count ?? 0}{" "}
                          feedback records
                        </p>
                      </div>
                      <div className="bg-gray-50 rounded-lg p-3">
                        <p className="text-xs text-gray-500 mb-1">Threshold</p>
                        <p className="font-semibold text-gray-800">
                          {fmt(
                            cycleMutation.data.threshold?.previous_threshold,
                          )}
                          {" → "}
                          {fmt(cycleMutation.data.threshold?.new_threshold)}
                        </p>
                        <p className="text-xs text-gray-400 mt-0.5">
                          Correction precision:{" "}
                          {fmtPct(
                            cycleMutation.data.threshold?.correction_precision,
                          )}
                        </p>
                      </div>
                      <div className="bg-gray-50 rounded-lg p-3">
                        <p className="text-xs text-gray-500 mb-1">
                          Ensemble Retrain
                        </p>
                        <p className="font-semibold text-gray-800">
                          {cycleMutation.data.retrain?.retrained
                            ? "Yes"
                            : "Not yet"}
                        </p>
                        <p className="text-xs text-gray-400 mt-0.5">
                          {cycleMutation.data.retrain?.corrections_applied ?? 0}{" "}
                          corrections applied
                          {" · "}cycle #
                          {cycleMutation.data.retrain?.cycle_number ?? 0}
                        </p>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              )}

              {/* Charts or empty state */}
              {totalCycles > 0 ? (
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
                  <Card className="border-gray-100 shadow-sm">
                    <CardHeader className="pb-1">
                      <CardTitle className="text-sm font-semibold text-gray-700 flex items-center gap-2">
                        <Target className="h-4 w-4 text-gray-400" />
                        Threshold Over Time
                      </CardTitle>
                    </CardHeader>
                    <CardContent>
                      <LineChart
                        series={thresholdHistory}
                        color="#3b82f6"
                        label="Threshold"
                        formatY={(v) => v.toFixed(2)}
                      />
                      <p className="text-xs text-gray-400 mt-1">
                        Higher = more conservative flagging.
                      </p>
                    </CardContent>
                  </Card>

                  <Card className="border-gray-100 shadow-sm">
                    <CardHeader className="pb-1">
                      <CardTitle className="text-sm font-semibold text-gray-700 flex items-center gap-2">
                        <TrendingUp className="h-4 w-4 text-gray-400" />
                        Accuracy Over Time
                      </CardTitle>
                    </CardHeader>
                    <CardContent>
                      <LineChart
                        series={accuracyHistory}
                        color="#10b981"
                        label="Accuracy"
                        formatY={(v) => (v * 100).toFixed(1) + "%"}
                      />
                    </CardContent>
                  </Card>

                  <Card className="border-gray-100 shadow-sm">
                    <CardHeader className="pb-1">
                      <CardTitle className="text-sm font-semibold text-gray-700 flex items-center gap-2">
                        <Activity className="h-4 w-4 text-gray-400" />
                        F1 Macro Over Time
                      </CardTitle>
                    </CardHeader>
                    <CardContent>
                      <LineChart
                        series={f1History}
                        color="#8b5cf6"
                        label="F1 Macro"
                      />
                    </CardContent>
                  </Card>

                  <Card className="border-gray-100 shadow-sm">
                    <CardHeader className="pb-1">
                      <CardTitle className="text-sm font-semibold text-gray-700 flex items-center gap-2">
                        <Brain className="h-4 w-4 text-gray-400" />
                        Correction Precision Over Time
                      </CardTitle>
                    </CardHeader>
                    <CardContent>
                      <LineChart
                        series={corrPrecHistory}
                        color="#f59e0b"
                        label="Correction Precision"
                        formatY={(v) => (v * 100).toFixed(1) + "%"}
                      />
                    </CardContent>
                  </Card>
                </div>
              ) : (
                <Card className="border-gray-100 shadow-sm">
                  <CardContent className="text-center py-12">
                    <Brain className="h-10 w-10 mx-auto mb-3 text-gray-300" />
                    <p className="text-sm font-medium text-gray-600">
                      No learning cycles yet
                    </p>
                    <p className="text-xs text-gray-400 mt-1 mb-4">
                      Submit feedback on corrections, then click "Trigger
                      Learning Cycle".
                    </p>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => navigate("/feedback")}
                    >
                      Go to Feedback
                    </Button>
                  </CardContent>
                </Card>
              )}

              {/* Cycle history table */}
              <Card className="border-gray-100 shadow-sm">
                <CardHeader className="pb-2">
                  <CardTitle className="text-sm font-semibold text-gray-700">
                    Cycle History
                  </CardTitle>
                </CardHeader>
                <CardContent className="p-0">
                  <CycleTable history={history} />
                </CardContent>
              </Card>

              {/* Engine status debug */}
              {statusData && (
                <Card className="border-gray-100 shadow-sm">
                  <CardHeader className="pb-2">
                    <CardTitle className="text-sm font-semibold text-gray-700">
                      Engine Registry Status
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <pre className="text-xs text-gray-500 bg-gray-50 rounded-lg p-3 overflow-x-auto">
                      {JSON.stringify(statusData, null, 2)}
                    </pre>
                  </CardContent>
                </Card>
              )}
            </>
          )}
        </>
      )}
    </div>
  );
}
