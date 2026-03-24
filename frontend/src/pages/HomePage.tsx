import { useState } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { useNavigate } from "react-router-dom";
import {
  datasetAPI,
  detectionAPI,
  feedbackAPI,
  memoryAPI,
} from "@/services/api";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import {
  Database,
  FileCheck,
  TrendingUp,
  Settings,
  Loader2,
  Upload,
  CheckCircle2,
  XCircle,
  AlertCircle,
  Activity,
} from "lucide-react";
import { UploadDatasetDialog } from "@/components/UploadDatasetDialog";

export function HomePage() {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [uploadOpen, setUploadOpen] = useState(false);
  const [selectedDatasetId, setSelectedDatasetId] = useState<number | null>(
    null,
  );

  // ── Datasets ──────────────────────────────────────────────────────────────
  const { data: datasets, isLoading: loadingDatasets } = useQuery({
    queryKey: ["datasets"],
    queryFn: datasetAPI.getAll,
    refetchInterval: 10000,
  });

  const totalDatasets = datasets?.length ?? 0;
  const activeDatasetId = selectedDatasetId ?? datasets?.[0]?.id ?? null;

  // ── Detection stats across all datasets ──────────────────────────────────
  const { data: detectionStats, isLoading: loadingDetections } = useQuery({
    queryKey: ["home-detection-stats", datasets?.map((d) => d.id).join(",")],
    queryFn: async () => {
      if (!datasets || datasets.length === 0)
        return { totalDetections: 0, totalSamples: 0 };
      const results = await Promise.all(
        datasets.map((d) =>
          detectionAPI.getStats(d.id).catch(() => ({
            suspicious_samples: 0,
            total_samples: 0,
          })),
        ),
      );
      return {
        totalDetections: results.reduce(
          (s, r) => s + (r.suspicious_samples ?? 0),
          0,
        ),
        totalSamples: results.reduce((s, r) => s + (r.total_samples ?? 0), 0),
      };
    },
    enabled: totalDatasets > 0,
    refetchInterval: 10000,
  });

  // ── Feedback stats across all datasets ───────────────────────────────────
  const { data: feedbackStats, isLoading: loadingFeedback } = useQuery({
    queryKey: ["home-feedback-stats", datasets?.map((d) => d.id).join(",")],
    queryFn: async () => {
      if (!datasets || datasets.length === 0)
        return { totalFeedback: 0, totalCorrections: 0 };
      const results = await Promise.all(
        datasets.map((d) =>
          feedbackAPI.getStats(d.id).catch(() => ({
            total_feedback: 0,
            accepted: 0,
            modified: 0,
          })),
        ),
      );
      return {
        totalFeedback: results.reduce((s, r) => s + (r.total_feedback ?? 0), 0),
        totalCorrections: results.reduce(
          (s, r) => s + (r.accepted ?? 0) + (r.modified ?? 0),
          0,
        ),
      };
    },
    enabled: totalDatasets > 0,
    refetchInterval: 10000,
  });

  // ── Engine status for selected dataset ───────────────────────────────────
  const { data: engineStatus, isLoading: loadingEngine } = useQuery({
    queryKey: ["home-engine-status", activeDatasetId],
    queryFn: () => memoryAPI.getStatus(activeDatasetId!),
    enabled: activeDatasetId !== null,
    refetchInterval: 10000,
  });

  const { data: engineThreshold } = useQuery({
    queryKey: ["home-engine-threshold", activeDatasetId],
    queryFn: () => memoryAPI.getThreshold(activeDatasetId!),
    enabled: activeDatasetId !== null,
    refetchInterval: 10000,
  });

  // ── Derived ───────────────────────────────────────────────────────────────
  const totalDetections = detectionStats?.totalDetections ?? 0;
  const totalFeedback = feedbackStats?.totalFeedback ?? 0;
  const totalCorrections = feedbackStats?.totalCorrections ?? 0;
  const _isLoading = loadingDatasets || loadingDetections || loadingFeedback;
  const noDatasets = !loadingDatasets && totalDatasets === 0;

  return (
    <div className="space-y-6">
      {/* ── Page Header ── */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-3xl font-bold tracking-tight">
            Welcome to SLDCE
          </h2>
          <p className="text-gray-500">Self-Learning Data Correction Engine</p>
        </div>
        {totalDatasets > 0 && (
          <Button onClick={() => setUploadOpen(true)} className="gap-2">
            <Upload className="h-4 w-4" />
            Upload Dataset
          </Button>
        )}
      </div>

      {/* ── Quick Start Banner — only when no datasets ── */}
      {noDatasets && (
        <Card className="border-2 border-dashed border-blue-300 bg-blue-50">
          <CardContent className="flex flex-col items-center justify-center py-12 gap-4">
            <div className="rounded-full bg-blue-100 p-4">
              <Upload className="h-10 w-10 text-blue-600" />
            </div>
            <div className="text-center">
              <h3 className="text-xl font-semibold text-blue-900">
                Get Started
              </h3>
              <p className="text-blue-700 mt-1 max-w-md">
                Upload your first dataset to begin detecting and correcting
                label noise.
              </p>
            </div>
            <Button
              size="lg"
              onClick={() => setUploadOpen(true)}
              className="gap-2"
            >
              <Upload className="h-4 w-4" />
              Upload Your First Dataset
            </Button>
            <div className="flex gap-8 mt-2 text-sm text-blue-600">
              <span>✓ CSV format</span>
              <span>✓ Auto label detection</span>
              <span>✓ Any classification dataset</span>
            </div>
          </CardContent>
        </Card>
      )}

      {/* ── KPI Cards ── */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <Card
          className="cursor-pointer hover:shadow-md transition-shadow"
          onClick={() => navigate("/datasets")}
        >
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">
              Total Datasets
            </CardTitle>
            <Database className="h-4 w-4 text-blue-600" />
          </CardHeader>
          <CardContent>
            {loadingDatasets ? (
              <Loader2 className="h-8 w-8 animate-spin text-blue-600" />
            ) : (
              <>
                <div className="text-2xl font-bold">{totalDatasets}</div>
                <p className="text-xs text-gray-500">
                  {totalDatasets === 0
                    ? "No datasets uploaded yet"
                    : `${detectionStats?.totalSamples ?? 0} total samples`}
                </p>
              </>
            )}
          </CardContent>
        </Card>

        <Card
          className="cursor-pointer hover:shadow-md transition-shadow"
          onClick={() => navigate("/detection")}
        >
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">
              Detected Errors
            </CardTitle>
            <FileCheck className="h-4 w-4 text-orange-600" />
          </CardHeader>
          <CardContent>
            {loadingDetections ? (
              <Loader2 className="h-8 w-8 animate-spin text-orange-600" />
            ) : (
              <>
                <div className="text-2xl font-bold">{totalDetections}</div>
                <p className="text-xs text-gray-500">
                  {totalDetections === 0
                    ? "Run detection to find errors"
                    : "Suspicious samples found"}
                </p>
              </>
            )}
          </CardContent>
        </Card>

        <Card
          className="cursor-pointer hover:shadow-md transition-shadow"
          onClick={() => navigate("/feedback")}
        >
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">
              Feedback Given
            </CardTitle>
            <TrendingUp className="h-4 w-4 text-purple-600" />
          </CardHeader>
          <CardContent>
            {loadingFeedback ? (
              <Loader2 className="h-8 w-8 animate-spin text-purple-600" />
            ) : (
              <>
                <div className="text-2xl font-bold">{totalFeedback}</div>
                <p className="text-xs text-gray-500">
                  {totalFeedback === 0
                    ? "No feedback submitted yet"
                    : `${totalCorrections} corrections applied`}
                </p>
              </>
            )}
          </CardContent>
        </Card>

        <Card
          className="cursor-pointer hover:shadow-md transition-shadow"
          onClick={() => navigate("/correction")}
        >
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">
              Corrections Applied
            </CardTitle>
            <Settings className="h-4 w-4 text-green-600" />
          </CardHeader>
          <CardContent>
            {loadingFeedback ? (
              <Loader2 className="h-8 w-8 animate-spin text-green-600" />
            ) : (
              <>
                <div className="text-2xl font-bold">{totalCorrections}</div>
                <p className="text-xs text-gray-500">
                  {totalCorrections === 0
                    ? "No corrections yet"
                    : "Labels corrected via feedback"}
                </p>
              </>
            )}
          </CardContent>
        </Card>
      </div>

      {/* ── Engine Status Card — only when datasets exist ── */}
      {totalDatasets > 0 && (
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <div>
                <CardTitle className="flex items-center gap-2">
                  <Activity className="h-5 w-5 text-blue-600" />
                  Engine Status
                </CardTitle>
                <CardDescription>
                  Self-learning engine status for the active dataset
                </CardDescription>
              </div>
              {datasets && datasets.length > 1 && (
                <select
                  className="text-sm border rounded px-2 py-1 bg-white"
                  value={activeDatasetId ?? ""}
                  onChange={(e) => setSelectedDatasetId(Number(e.target.value))}
                >
                  {datasets.map((d) => (
                    <option key={d.id} value={d.id}>
                      {d.name}
                    </option>
                  ))}
                </select>
              )}
            </div>
          </CardHeader>
          <CardContent>
            {loadingEngine ? (
              <div className="flex items-center gap-2 text-gray-500">
                <Loader2 className="h-4 w-4 animate-spin" />
                Loading engine status...
              </div>
            ) : engineStatus ? (
              <>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  <div className="flex flex-col gap-1">
                    <span className="text-xs text-gray-500 uppercase tracking-wide">
                      Engine
                    </span>
                    <div className="flex items-center gap-1.5">
                      {engineStatus.exists ? (
                        <CheckCircle2 className="h-4 w-4 text-green-500" />
                      ) : (
                        <XCircle className="h-4 w-4 text-gray-400" />
                      )}
                      <span className="text-sm font-medium">
                        {engineStatus.exists ? "Created" : "Not created"}
                      </span>
                    </div>
                  </div>

                  <div className="flex flex-col gap-1">
                    <span className="text-xs text-gray-500 uppercase tracking-wide">
                      Fitted
                    </span>
                    <div className="flex items-center gap-1.5">
                      {engineStatus.fitted ? (
                        <CheckCircle2 className="h-4 w-4 text-green-500" />
                      ) : (
                        <AlertCircle className="h-4 w-4 text-yellow-500" />
                      )}
                      <span className="text-sm font-medium">
                        {engineStatus.fitted ? "Ready" : "Run detection first"}
                      </span>
                    </div>
                  </div>

                  <div className="flex flex-col gap-1">
                    <span className="text-xs text-gray-500 uppercase tracking-wide">
                      Persisted
                    </span>
                    <div className="flex items-center gap-1.5">
                      {engineStatus.on_disk ? (
                        <CheckCircle2 className="h-4 w-4 text-green-500" />
                      ) : (
                        <XCircle className="h-4 w-4 text-gray-400" />
                      )}
                      <span className="text-sm font-medium">
                        {engineStatus.on_disk ? "Saved to disk" : "Not saved"}
                      </span>
                    </div>
                  </div>

                  <div className="flex flex-col gap-1">
                    <span className="text-xs text-gray-500 uppercase tracking-wide">
                      Threshold
                    </span>
                    <div className="flex items-center gap-1.5">
                      <Activity className="h-4 w-4 text-blue-500" />
                      <span className="text-sm font-medium">
                        {engineThreshold?.threshold != null
                          ? `${(engineThreshold.threshold * 100).toFixed(0)}%`
                          : "—"}
                      </span>
                    </div>
                  </div>
                </div>

                {!engineStatus.fitted && (
                  <div className="mt-4 p-3 bg-yellow-50 border border-yellow-200 rounded-lg flex items-center justify-between">
                    <div className="flex items-center gap-2 text-yellow-800 text-sm">
                      <AlertCircle className="h-4 w-4" />
                      Engine not fitted — run detection to initialize it.
                    </div>
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() => navigate("/detection")}
                      className="border-yellow-400 text-yellow-800 hover:bg-yellow-100"
                    >
                      Go to Detection
                    </Button>
                  </div>
                )}
              </>
            ) : (
              <p className="text-sm text-gray-500">
                No engine data — run detection on a dataset first.
              </p>
            )}
          </CardContent>
        </Card>
      )}

      {/* ── Getting Started Steps ── */}
      <Card>
        <CardHeader>
          <CardTitle>Getting Started</CardTitle>
          <CardDescription>Follow these steps to use SLDCE</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          {[
            {
              step: 1,
              title: "Upload a Dataset",
              desc: "Upload a CSV file with features and a label column",
              done: totalDatasets > 0,
              action: () => setUploadOpen(true),
              actionLabel: "Upload",
            },
            {
              step: 2,
              title: "Run Detection",
              desc: "The engine flags potentially mislabeled samples",
              done: totalDetections > 0,
              action: () => navigate("/detection"),
              actionLabel: "Detect",
            },
            {
              step: 3,
              title: "Review Suggestions & Give Feedback",
              desc: "Approve, reject or modify each correction suggestion",
              done: totalFeedback > 0,
              action: () => navigate("/correction"),
              actionLabel: "Review",
            },
            {
              step: 4,
              title: "Evaluate Improvement",
              desc: "Apply corrections, retrain and measure accuracy gain",
              done: totalCorrections > 0,
              action: () => navigate("/evaluation"),
              actionLabel: "Evaluate",
            },
            {
              step: 5,
              title: "Trigger Learning Cycle",
              desc: "Let the engine adapt its threshold based on your feedback",
              done: false,
              action: () => navigate("/memory"),
              actionLabel: "Memory",
            },
          ].map(({ step, title, desc, done, action, actionLabel }) => (
            <div key={step} className="flex items-center gap-4">
              <div
                className={`flex h-8 w-8 shrink-0 items-center justify-center rounded-full font-semibold text-sm
      ${done ? "bg-green-100 text-green-600" : "bg-blue-100 text-blue-600"}`}
              >
                {done ? <CheckCircle2 className="h-5 w-5" /> : step}
              </div>
              <div className="flex-1">
                <h4
                  className={`font-semibold ${done ? "text-gray-400 line-through" : ""}`}
                >
                  {title}
                </h4>
                <p className="text-sm text-gray-500">{desc}</p>
              </div>
              {!done && (
                <Button size="sm" variant="outline" onClick={action}>
                  {actionLabel}
                </Button>
              )}
              {done && (
                <CheckCircle2 className="h-5 w-5 text-green-500 shrink-0" />
              )}
            </div>
          ))}
        </CardContent>
      </Card>

      {/* ── Upload Dialog ── */}
      <UploadDatasetDialog
        open={uploadOpen}
        onOpenChange={setUploadOpen}
        onSuccess={() => {
          queryClient.invalidateQueries({ queryKey: ["datasets"] });
          setUploadOpen(false);
        }}
      />
    </div>
  );
}
