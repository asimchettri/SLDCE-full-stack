import { useState, useMemo } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { benchmarkAPI, datasetAPI } from "@/services/api";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  AlertCircle,
  RefreshCw,
  Play,
  TrendingUp,
  BarChart3,
  Target,
  Users,
} from "lucide-react";
import type { BenchmarkResult } from "../services/api";
import { Download } from "lucide-react";

// ─── Constants ────────────────────────────────────────────────────────────────

const TOOL_LABELS: Record<string, string> = {
  no_correction: "No Correction",
  random: "Random",
  cleanlab: "Cleanlab",
  sldce: "SLDCE",
};

const TOOL_COLORS: Record<
  string,
  { bg: string; bar: string; text: string; badge: string }
> = {
  no_correction: {
    bg: "bg-red-50",
    bar: "#ef4444",
    text: "text-red-700",
    badge: "bg-red-100 text-red-700 border border-red-200",
  },
  random: {
    bg: "bg-amber-50",
    bar: "#f59e0b",
    text: "text-amber-700",
    badge: "bg-amber-100 text-amber-700 border border-amber-200",
  },
  cleanlab: {
    bg: "bg-blue-50",
    bar: "#3b82f6",
    text: "text-blue-700",
    badge: "bg-blue-100 text-blue-700 border border-blue-200",
  },
  sldce: {
    bg: "bg-emerald-50",
    bar: "#10b981",
    text: "text-emerald-700",
    badge: "bg-emerald-100 text-emerald-700 border border-emerald-200",
  },
};

const TOOL_ORDER = ["no_correction", "random", "cleanlab", "sldce"];

function fmt(val: number | null | undefined): string {
  if (val == null) return "—";
  return (val * 100).toFixed(2) + "%";
}

function fmtShort(val: number | null | undefined): string {
  if (val == null) return "—";
  return (val * 100).toFixed(1) + "%";
}

// ─── Subcomponents ────────────────────────────────────────────────────────────

function MetricBar({ value, color }: { value: number; color: string }) {
  const pct = Math.min(100, value * 100);
  return (
    <div className="w-full bg-gray-100 rounded-full h-2 overflow-hidden">
      <div
        className="h-2 rounded-full transition-all duration-700"
        style={{ width: `${pct}%`, backgroundColor: color }}
      />
    </div>
  );
}

function AccuracyBarChart({
  rows,
}: {
  rows: { tool: string; accuracy: number }[];
}) {
  const W = 480;
  const H = 200;
  const PAD = { top: 20, right: 20, bottom: 40, left: 50 };
  const chartW = W - PAD.left - PAD.right;
  const chartH = H - PAD.top - PAD.bottom;
  const barW = chartW / rows.length - 12;

  return (
    <svg
      viewBox={`0 0 ${W} ${H}`}
      className="w-full"
      style={{ fontFamily: "monospace" }}
    >
      {[0, 0.25, 0.5, 0.75, 1.0].map((v) => {
        const y = PAD.top + chartH - v * chartH;
        return (
          <g key={v}>
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
              x={PAD.left - 6}
              y={y + 4}
              textAnchor="end"
              fontSize={9}
              fill="#9ca3af"
            >
              {(v * 100).toFixed(0)}%
            </text>
          </g>
        );
      })}
      {rows.map((r, i) => {
        const barH = r.accuracy * chartH;
        const x = PAD.left + i * (chartW / rows.length) + 6;
        const y = PAD.top + chartH - barH;
        const color = TOOL_COLORS[r.tool]?.bar ?? "#6b7280";
        return (
          <g key={r.tool}>
            <rect
              x={x}
              y={y}
              width={barW}
              height={barH}
              fill={color}
              rx={4}
              opacity={0.9}
            />
            <text
              x={x + barW / 2}
              y={y - 5}
              textAnchor="middle"
              fontSize={9}
              fill={color}
              fontWeight="600"
            >
              {fmtShort(r.accuracy)}
            </text>
            <text
              x={x + barW / 2}
              y={H - PAD.bottom + 14}
              textAnchor="middle"
              fontSize={9}
              fill="#6b7280"
            >
              {TOOL_LABELS[r.tool] ?? r.tool}
            </text>
          </g>
        );
      })}
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
    </svg>
  );
}

function IterationLineChart({
  sldceRows,
  baselineAcc,
  cleanlabAcc,
}: {
  sldceRows: BenchmarkResult[];
  baselineAcc: number | null;
  cleanlabAcc: number | null;
}) {
  const W = 480;
  const H = 200;
  const PAD = { top: 20, right: 24, bottom: 40, left: 50 };
  const chartW = W - PAD.left - PAD.right;
  const chartH = H - PAD.top - PAD.bottom;

  if (sldceRows.length === 0)
    return (
      <div className="flex items-center justify-center h-32 text-gray-400 text-sm">
        No SLDCE iterations yet
      </div>
    );

  const maxIter = sldceRows[sldceRows.length - 1].iteration;
  const xScale = (iter: number) =>
    PAD.left + ((iter - 1) / Math.max(maxIter - 1, 1)) * chartW;
  const yScale = (acc: number) => PAD.top + chartH - acc * chartH;

  const points = sldceRows.map((r) => ({
    x: xScale(r.iteration),
    y: yScale(r.accuracy ?? 0),
    acc: r.accuracy ?? 0,
    iter: r.iteration,
  }));

  const polyline = points.map((p) => `${p.x},${p.y}`).join(" ");

  return (
    <svg
      viewBox={`0 0 ${W} ${H}`}
      className="w-full"
      style={{ fontFamily: "monospace" }}
    >
      {[0, 0.25, 0.5, 0.75, 1.0].map((v) => {
        const y = PAD.top + chartH - v * chartH;
        return (
          <g key={v}>
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
              x={PAD.left - 6}
              y={y + 4}
              textAnchor="end"
              fontSize={9}
              fill="#9ca3af"
            >
              {(v * 100).toFixed(0)}%
            </text>
          </g>
        );
      })}
      {baselineAcc != null && (
        <line
          x1={PAD.left}
          y1={yScale(baselineAcc)}
          x2={PAD.left + chartW}
          y2={yScale(baselineAcc)}
          stroke="#ef4444"
          strokeWidth={1.5}
          strokeDasharray="6 3"
          opacity={0.7}
        />
      )}
      {cleanlabAcc != null && (
        <line
          x1={PAD.left}
          y1={yScale(cleanlabAcc)}
          x2={PAD.left + chartW}
          y2={yScale(cleanlabAcc)}
          stroke="#3b82f6"
          strokeWidth={1.5}
          strokeDasharray="6 3"
          opacity={0.7}
        />
      )}
      {points.length > 1 && (
        <polygon
          points={`${PAD.left},${PAD.top + chartH} ${polyline} ${points[points.length - 1].x},${PAD.top + chartH}`}
          fill="#10b981"
          opacity={0.08}
        />
      )}
      <polyline
        points={polyline}
        fill="none"
        stroke="#10b981"
        strokeWidth={2.5}
        strokeLinejoin="round"
        strokeLinecap="round"
      />
      {points.map((p) => (
        <g key={p.iter}>
          <circle
            cx={p.x}
            cy={p.y}
            r={5}
            fill="#10b981"
            stroke="white"
            strokeWidth={2}
          />
          <text
            x={p.x}
            y={p.y - 10}
            textAnchor="middle"
            fontSize={8.5}
            fill="#10b981"
            fontWeight="600"
          >
            {fmtShort(p.acc)}
          </text>
          <text
            x={p.x}
            y={H - PAD.bottom + 14}
            textAnchor="middle"
            fontSize={9}
            fill="#6b7280"
          >
            {p.iter}
          </text>
        </g>
      ))}
      <g>
        <line
          x1={PAD.left + chartW - 120}
          y1={12}
          x2={PAD.left + chartW - 106}
          y2={12}
          stroke="#ef4444"
          strokeWidth={1.5}
          strokeDasharray="4 2"
        />
        <text x={PAD.left + chartW - 102} y={15} fontSize={8} fill="#ef4444">
          No Correction
        </text>
        <line
          x1={PAD.left + chartW - 120}
          y1={24}
          x2={PAD.left + chartW - 106}
          y2={24}
          stroke="#3b82f6"
          strokeWidth={1.5}
          strokeDasharray="4 2"
        />
        <text x={PAD.left + chartW - 102} y={27} fontSize={8} fill="#3b82f6">
          Cleanlab
        </text>
      </g>
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
        fontSize={9}
        fill="#9ca3af"
      >
        Iteration
      </text>
    </svg>
  );
}

function EffortBarChart({ sldceRows }: { sldceRows: BenchmarkResult[] }) {
  const W = 480;
  const H = 160;
  const PAD = { top: 20, right: 20, bottom: 36, left: 44 };
  const chartW = W - PAD.left - PAD.right;
  const chartH = H - PAD.top - PAD.bottom;

  if (sldceRows.length === 0) return null;

  const maxEffort = Math.max(...sldceRows.map((r) => r.human_effort ?? 0), 1);
  const barW = chartW / sldceRows.length - 10;

  return (
    <svg
      viewBox={`0 0 ${W} ${H}`}
      className="w-full"
      style={{ fontFamily: "monospace" }}
    >
      {[0, 0.5, 1].map((v) => {
        const y = PAD.top + chartH - v * chartH;
        return (
          <g key={v}>
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
              fontSize={9}
              fill="#9ca3af"
            >
              {Math.round(v * maxEffort)}
            </text>
          </g>
        );
      })}
      {sldceRows.map((r, i) => {
        const effort = r.human_effort ?? 0;
        const barH = maxEffort > 0 ? (effort / maxEffort) * chartH : 0;
        const x = PAD.left + i * (chartW / sldceRows.length) + 5;
        const y = PAD.top + chartH - barH;
        return (
          <g key={r.iteration}>
            <rect
              x={x}
              y={y}
              width={barW}
              height={barH}
              fill="#10b981"
              rx={3}
              opacity={effort > 0 ? 0.85 : 0.2}
            />
            <text
              x={x + barW / 2}
              y={y - 4}
              textAnchor="middle"
              fontSize={9}
              fill="#059669"
              fontWeight="600"
            >
              {effort}
            </text>
            <text
              x={x + barW / 2}
              y={H - PAD.bottom + 13}
              textAnchor="middle"
              fontSize={9}
              fill="#6b7280"
            >
              {r.iteration}
            </text>
          </g>
        );
      })}
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
        fontSize={9}
        fill="#9ca3af"
      >
        Iteration
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
      <div>
        <p className="text-xs text-gray-500 font-medium">{label}</p>
        <p className="text-xl font-bold text-gray-900 tracking-tight">
          {value}
        </p>
        {sub && <p className="text-xs text-gray-400 mt-0.5">{sub}</p>}
      </div>
    </div>
  );
}

// ─── Main Page ────────────────────────────────────────────────────────────────

export function BenchmarkPage() {
  const [datasetId, setDatasetId] = useState<number | null>(null);
  const queryClient = useQueryClient();

  // Fetch all datasets for the dropdown
  const { data: datasets = [] } = useQuery({
    queryKey: ["datasets"],
    queryFn: () => datasetAPI.getAll(),
    staleTime: 1000 * 60 * 5,
  });

  // Auto-select first dataset when loaded
  const effectiveDatasetId = datasetId ?? datasets[0]?.id ?? null;

  const {
    data: results = [],
    isLoading,
    error,
    refetch,
  } = useQuery({
    queryKey: ["benchmarks", effectiveDatasetId],
    queryFn: () => benchmarkAPI.getResults(effectiveDatasetId!),
    enabled: !!effectiveDatasetId,
  });

  const runMutation = useMutation({
    mutationFn: () => benchmarkAPI.runFull(effectiveDatasetId!, 5),
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: ["benchmarks", effectiveDatasetId],
      });
    },
  });

  const hasResults = results.length > 0;

  const { summaryRows, sldceRows, baselineAcc, cleanlabAcc, sldceBest } =
    useMemo(() => {
      const toolMap: Record<string, BenchmarkResult[]> = {};
      for (const r of results) {
        if (!toolMap[r.tool]) toolMap[r.tool] = [];
        toolMap[r.tool].push(r);
      }

      const summaryRows: {
        tool: string;
        accuracy: number;
        precision: number;
        recall: number;
        f1: number;
        human_effort: number | null;
      }[] = [];
      for (const tool of ["no_correction", "random", "cleanlab"]) {
        const rows = toolMap[tool];
        if (!rows?.length) continue;
        const latest = rows[rows.length - 1];
        summaryRows.push({
          tool,
          accuracy: latest.accuracy ?? 0,
          precision: latest.precision ?? 0,
          recall: latest.recall ?? 0,
          f1: latest.f1 ?? 0,
          human_effort: latest.human_effort,
        });
      }

      const sldceMap: Record<number, BenchmarkResult> = {};
      for (const r of toolMap["sldce"] ?? []) {
        sldceMap[r.iteration] = r;
      }
      const sldceRows = Object.values(sldceMap).sort(
        (a, b) => a.iteration - b.iteration,
      );

      const sldceBest = sldceRows.reduce<BenchmarkResult | null>(
        (best, r) =>
          !best || (r.accuracy ?? 0) > (best.accuracy ?? 0) ? r : best,
        null,
      );

      if (sldceBest) {
        summaryRows.push({
          tool: "sldce",
          accuracy: sldceBest.accuracy ?? 0,
          precision: sldceBest.precision ?? 0,
          recall: sldceBest.recall ?? 0,
          f1: sldceBest.f1 ?? 0,
          human_effort: sldceBest.human_effort,
        });
      }

      summaryRows.sort(
        (a, b) => TOOL_ORDER.indexOf(a.tool) - TOOL_ORDER.indexOf(b.tool),
      );

      const baselineAcc =
        toolMap["no_correction"]?.[toolMap["no_correction"].length - 1]
          ?.accuracy ?? null;
      const cleanlabAcc =
        toolMap["cleanlab"]?.[toolMap["cleanlab"].length - 1]?.accuracy ?? null;

      return { summaryRows, sldceRows, baselineAcc, cleanlabAcc, sldceBest };
    }, [results]);

  const totalEffort = sldceRows.reduce((s, r) => s + (r.human_effort ?? 0), 0);
  const improvement =
    sldceBest && baselineAcc != null
      ? ((sldceBest.accuracy ?? 0) - baselineAcc) * 100
      : null;

  return (
    <div className="space-y-6 pb-8">
      {/* Header */}
      <div className="flex items-start justify-between">
        <div>
          <h2 className="text-2xl font-bold tracking-tight text-gray-900">
            Benchmark Comparison
          </h2>
          <p className="text-gray-500 text-sm mt-1">
            SLDCE vs Cleanlab, Random Correction, and No-Correction baselines
          </p>
        </div>
        <div className="flex gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={() => refetch()}
            disabled={isLoading}
          >
            <RefreshCw
              className={`mr-1.5 h-3.5 w-3.5 ${isLoading ? "animate-spin" : ""}`}
            />
            Refresh
          </Button>
          <Button
            variant="outline"
            size="sm"
            onClick={() => benchmarkAPI.exportCSV(effectiveDatasetId!)}
            disabled={!hasResults}
          >
            <Download className="mr-1.5 h-3.5 w-3.5" />
            Export CSV
          </Button>
          <div className="relative group">
            <Button
              size="sm"
              onClick={() => runMutation.mutate()}
              disabled={runMutation.isPending || hasResults}
              className={hasResults ? "opacity-50 cursor-not-allowed" : ""}
            >
              <Play className="mr-1.5 h-3.5 w-3.5" />
              {runMutation.isPending ? "Running..." : "Run Benchmark"}
            </Button>
            {hasResults && !runMutation.isPending && (
              <div className="absolute right-0 top-full mt-2 w-64 z-10 hidden group-hover:block">
                <div className="bg-gray-900 text-white text-xs rounded-lg px-3 py-2 shadow-lg">
                  Benchmarks already run. Re-upload a fresh noisy dataset to run
                  again.
                  <div className="absolute -top-1.5 right-4 w-3 h-3 bg-gray-900 rotate-45" />
                </div>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Dataset selector */}
      <div className="flex items-center gap-3">
        <label className="text-sm font-medium text-gray-600">Dataset</label>
        <select
          value={effectiveDatasetId ?? ""}
          onChange={(e) => setDatasetId(Number(e.target.value))}
          className="rounded-lg border border-gray-200 px-3 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-transparent bg-white min-w-[200px]"
        >
          {datasets.length === 0 && (
            <option value="" disabled>
              No datasets available
            </option>
          )}
          {datasets.map((d) => (
            <option key={d.id} value={d.id}>
              {d.name} (ID: {d.id})
            </option>
          ))}
        </select>
      </div>

      {/* Banners */}
      {runMutation.isPending && (
        <div className="flex items-center gap-3 rounded-xl bg-blue-50 border border-blue-100 px-4 py-3">
          <div className="animate-spin rounded-full h-4 w-4 border-2 border-blue-600 border-t-transparent" />
          <p className="text-sm text-blue-700 font-medium">
            Running full benchmark — this takes ~2 minutes...
          </p>
        </div>
      )}

      {hasResults && !runMutation.isPending && (
        <div className="flex items-center gap-3 rounded-xl bg-amber-50 border border-amber-100 px-4 py-3">
          <AlertCircle className="h-4 w-4 text-amber-500 shrink-0" />
          <p className="text-sm text-amber-700">
            Benchmarks have already been run on this dataset. SLDCE has
            corrected the labels — re-running would produce invalid baseline
            comparisons.{" "}
            <span className="font-medium">
              Upload a fresh noisy dataset to benchmark again.
            </span>
          </p>
        </div>
      )}

      {runMutation.isError && (
        <div className="flex items-center gap-3 rounded-xl bg-red-50 border border-red-100 px-4 py-3">
          <AlertCircle className="h-4 w-4 text-red-500 shrink-0" />
          <p className="text-sm text-red-700">
            {runMutation.error instanceof Error
              ? runMutation.error.message
              : "Benchmark failed"}
          </p>
        </div>
      )}

      {/* Body */}
      {isLoading ? (
        <div className="flex items-center justify-center py-24">
          <div className="animate-spin rounded-full h-8 w-8 border-2 border-emerald-600 border-t-transparent" />
        </div>
      ) : error ? (
        <div className="flex items-center gap-3 py-12 text-red-500">
          <AlertCircle className="h-5 w-5" />
          <span className="text-sm">Failed to load results</span>
        </div>
      ) : !hasResults ? (
        <div className="text-center py-24 text-gray-400">
          <BarChart3 className="h-10 w-10 mx-auto mb-3 opacity-30" />
          <p className="text-sm">No benchmark results yet.</p>
          <p className="text-xs mt-1">Click "Run Benchmark" to start.</p>
        </div>
      ) : (
        <>
          {/* KPI Cards */}
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
            <StatCard
              label="SLDCE Best Accuracy"
              value={fmt(sldceBest?.accuracy)}
              sub={`Iteration ${sldceBest?.iteration ?? "—"}`}
              icon={Target}
              color="bg-emerald-100 text-emerald-700"
            />
            <StatCard
              label="Improvement vs Baseline"
              value={improvement != null ? `+${improvement.toFixed(1)}%` : "—"}
              sub="over no-correction"
              icon={TrendingUp}
              color="bg-blue-100 text-blue-700"
            />
            <StatCard
              label="vs Cleanlab"
              value={
                sldceBest && cleanlabAcc != null
                  ? `+${(((sldceBest.accuracy ?? 0) - cleanlabAcc) * 100).toFixed(1)}%`
                  : "—"
              }
              sub="SLDCE advantage"
              icon={BarChart3}
              color="bg-violet-100 text-violet-700"
            />
            <StatCard
              label="Total Human Effort"
              value={`${totalEffort}`}
              sub="samples reviewed (SLDCE)"
              icon={Users}
              color="bg-amber-100 text-amber-700"
            />
          </div>

          {/* Charts */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            <Card className="border-gray-100 shadow-sm">
              <CardHeader className="pb-2">
                <CardTitle className="text-sm font-semibold text-gray-700 flex items-center gap-2">
                  <BarChart3 className="h-4 w-4 text-gray-400" />
                  Accuracy Comparison
                </CardTitle>
              </CardHeader>
              <CardContent>
                <AccuracyBarChart rows={summaryRows} />
                <div className="flex flex-wrap gap-2 mt-3">
                  {summaryRows.map((r) => (
                    <span
                      key={r.tool}
                      className={`text-xs px-2 py-0.5 rounded-full font-medium ${TOOL_COLORS[r.tool]?.badge}`}
                    >
                      {TOOL_LABELS[r.tool]}: {fmtShort(r.accuracy)}
                    </span>
                  ))}
                </div>
              </CardContent>
            </Card>

            <Card className="border-gray-100 shadow-sm">
              <CardHeader className="pb-2">
                <CardTitle className="text-sm font-semibold text-gray-700 flex items-center gap-2">
                  <TrendingUp className="h-4 w-4 text-gray-400" />
                  SLDCE Accuracy Over Iterations
                </CardTitle>
              </CardHeader>
              <CardContent>
                <IterationLineChart
                  sldceRows={sldceRows}
                  baselineAcc={baselineAcc}
                  cleanlabAcc={cleanlabAcc}
                />
              </CardContent>
            </Card>
          </div>

          {/* Effort chart */}
          {sldceRows.length > 0 && (
            <Card className="border-gray-100 shadow-sm">
              <CardHeader className="pb-2">
                <CardTitle className="text-sm font-semibold text-gray-700 flex items-center gap-2">
                  <Users className="h-4 w-4 text-gray-400" />
                  Human Effort per Iteration (Samples Reviewed)
                </CardTitle>
              </CardHeader>
              <CardContent>
                <EffortBarChart sldceRows={sldceRows} />
                <p className="text-xs text-gray-400 mt-2">
                  SLDCE reduces human review load with each iteration as the
                  model learns.
                </p>
              </CardContent>
            </Card>
          )}

          {/* Full metrics table */}
          <Card className="border-gray-100 shadow-sm">
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-semibold text-gray-700">
                Full Metrics Table
              </CardTitle>
            </CardHeader>
            <CardContent className="p-0">
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b bg-gray-50">
                      {[
                        "Tool",
                        "Accuracy",
                        "Precision",
                        "Recall",
                        "F1",
                        "Effort",
                        "",
                      ].map((h) => (
                        <th
                          key={h}
                          className={`px-4 py-3 font-semibold text-gray-600 text-xs uppercase tracking-wide ${h === "Tool" || h === "" ? "text-left" : "text-right"}`}
                        >
                          {h}
                        </th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {summaryRows
                      .filter((r) => r.tool !== "sldce")
                      .map((r) => (
                        <tr
                          key={r.tool}
                          className="border-b hover:bg-gray-50 transition-colors"
                        >
                          <td className="px-4 py-3">
                            <span
                              className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium ${TOOL_COLORS[r.tool]?.badge}`}
                            >
                              {TOOL_LABELS[r.tool] ?? r.tool}
                            </span>
                          </td>
                          <td className="text-right px-4 py-3 font-mono text-sm font-semibold text-gray-800">
                            {fmt(r.accuracy)}
                          </td>
                          <td className="text-right px-4 py-3 font-mono text-sm text-gray-600">
                            {fmt(r.precision)}
                          </td>
                          <td className="text-right px-4 py-3 font-mono text-sm text-gray-600">
                            {fmt(r.recall)}
                          </td>
                          <td className="text-right px-4 py-3 font-mono text-sm text-gray-600">
                            {fmt(r.f1)}
                          </td>
                          <td className="text-right px-4 py-3 font-mono text-sm text-gray-500">
                            {r.human_effort ?? "—"}
                          </td>
                          <td className="px-4 py-3 w-32">
                            <MetricBar
                              value={r.accuracy}
                              color={TOOL_COLORS[r.tool]?.bar ?? "#6b7280"}
                            />
                          </td>
                        </tr>
                      ))}
                  </tbody>
                </table>
              </div>

              {/* SLDCE iterations */}
              {sldceRows.length > 0 && (
                <div className="border-t">
                  <div className="px-4 py-2 bg-emerald-50 border-b">
                    <span className="text-xs font-semibold text-emerald-700 uppercase tracking-wide">
                      SLDCE — Iteration Breakdown
                    </span>
                  </div>
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="border-b bg-gray-50">
                        {[
                          "Iteration",
                          "Accuracy",
                          "Precision",
                          "Recall",
                          "F1",
                          "Flagged",
                          "Accepted",
                          "",
                        ].map((h) => (
                          <th
                            key={h}
                            className={`px-4 py-2 font-semibold text-gray-600 text-xs ${h === "Iteration" || h === "" ? "text-left" : "text-right"}`}
                          >
                            {h}
                          </th>
                        ))}
                      </tr>
                    </thead>
                    <tbody>
                      {sldceRows.map((r) => (
                        <tr
                          key={r.iteration}
                          className="border-b hover:bg-emerald-50/50 transition-colors"
                        >
                          <td className="px-4 py-2.5 font-medium text-gray-700">
                            Iter {r.iteration}
                            {r.iteration === sldceBest?.iteration && (
                              <span className="ml-2 text-xs bg-emerald-100 text-emerald-700 px-1.5 py-0.5 rounded-full">
                                best
                              </span>
                            )}
                          </td>
                          <td className="text-right px-4 py-2.5 font-mono font-semibold text-gray-800">
                            {fmt(r.accuracy)}
                          </td>
                          <td className="text-right px-4 py-2.5 font-mono text-gray-600">
                            {fmt(r.precision)}
                          </td>
                          <td className="text-right px-4 py-2.5 font-mono text-gray-600">
                            {fmt(r.recall)}
                          </td>
                          <td className="text-right px-4 py-2.5 font-mono text-gray-600">
                            {fmt(r.f1)}
                          </td>
                          <td className="text-right px-4 py-2.5 font-mono text-gray-500">
                            {r.meta?.flagged ?? "—"}
                          </td>
                          <td className="text-right px-4 py-2.5 font-mono text-gray-500">
                            {r.meta?.accepted ?? "—"}
                          </td>
                          <td className="px-4 py-2.5 w-32">
                            <MetricBar
                              value={r.accuracy ?? 0}
                              color="#10b981"
                            />
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </CardContent>
          </Card>
        </>
      )}
    </div>
  );
}
