import { useQuery } from '@tanstack/react-query'; 
import { datasetAPI, detectionAPI, feedbackAPI } from '@/services/api'; 
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Database, FileCheck, TrendingUp, Settings, Loader2 } from 'lucide-react'; 

export function HomePage() {
  // Fetch all datasets
  const { data: datasets, isLoading: loadingDatasets } = useQuery({
    queryKey: ['datasets'],
    queryFn: datasetAPI.getAll,
    refetchInterval: 5000, // Auto-refresh every 5 seconds
  });

  // Fetch detection stats for all datasets
  const { data: allDetectionStats, isLoading: loadingDetections } = useQuery({
    queryKey: ['all-detections'],
    queryFn: async () => {
      if (!datasets || datasets.length === 0) return null;
      
      // Fetch stats for all datasets
      const statsPromises = datasets.map(dataset => 
        detectionAPI.getStats(dataset.id).catch(() => ({ suspicious_samples: 0 }))
      );
      
      const stats = await Promise.all(statsPromises);
      
      // Sum up all suspicious samples
      return {
        totalDetections: stats.reduce((sum, s) => sum + (s.suspicious_samples || 0), 0)
      };
    },
    enabled: !!datasets && datasets.length > 0,
    refetchInterval: 5000, // Auto-refresh every 5 seconds
  });

  // Fetch feedback stats for all datasets
  const { data: allFeedbackStats, isLoading: loadingFeedback } = useQuery({
    queryKey: ['all-feedback'],
    queryFn: async () => {
      if (!datasets || datasets.length === 0) return null;
      
      // Fetch feedback stats for all datasets
      const statsPromises = datasets.map(dataset => 
        //  Changed default fallback to match backend FeedbackStatsResponse
        feedbackAPI.getStats(dataset.id).catch(() => ({ 
          dataset_id: dataset.id,
          total_feedback: 0,
          accepted: 0,  
          rejected: 0,  
          modified: 0,  
          acceptance_rate: 0
        }))
      );
      
      const stats = await Promise.all(statsPromises);
      
      //  Now uses 'accepted' and 'modified' to match backend
      return {
        totalCorrections: stats.reduce((sum, s) => 
          sum + (s.accepted || 0) + (s.modified || 0), 0
        )
      };
    },
    enabled: !!datasets && datasets.length > 0,
    refetchInterval: 5000, // Auto-refresh every 5 seconds
  });

  // Calculate derived values
  const totalDatasets = datasets?.length || 0;
  const detectedErrors = allDetectionStats?.totalDetections || 0;
  const correctionsMade = allFeedbackStats?.totalCorrections || 0;
  const isLoading = loadingDatasets || loadingDetections || loadingFeedback;

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-3xl font-bold tracking-tight">Welcome to SLDCE</h2>
        <p className="text-gray-500">
          Self-Learning Data Correction Engine
        </p>
      </div>

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Datasets</CardTitle>
            <Database className="h-4 w-4 text-blue-600" />
          </CardHeader>
          <CardContent>
            {isLoading ? (
              <Loader2 className="h-8 w-8 animate-spin text-blue-600" />
            ) : (
              <>
                <div className="text-2xl font-bold">{totalDatasets}</div>
                <p className="text-xs text-gray-500">
                  {totalDatasets === 0 ? 'No datasets uploaded yet' : `${totalDatasets} active dataset${totalDatasets > 1 ? 's' : ''}`}
                </p>
              </>
            )}
          </CardContent>
        </Card>

        {/* Detected Errors - Now dynamic */}
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Detected Errors</CardTitle>
            <FileCheck className="h-4 w-4 text-orange-600" />
          </CardHeader>
          <CardContent>
            {isLoading ? (
              <Loader2 className="h-8 w-8 animate-spin text-orange-600" />
            ) : (
              <>
                <div className="text-2xl font-bold">{detectedErrors}</div>
                <p className="text-xs text-gray-500">
                  {detectedErrors === 0 ? 'Waiting for detection' : `Suspicious samples found`}
                </p>
              </>
            )}
          </CardContent>
        </Card>

        {/* Corrections Made - Now dynamic */}
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Corrections Made</CardTitle>
            <TrendingUp className="h-4 w-4 text-green-600" />
          </CardHeader>
          <CardContent>
            {isLoading ? (
              <Loader2 className="h-8 w-8 animate-spin text-green-600" />
            ) : (
              <>
                <div className="text-2xl font-bold">{correctionsMade}</div>
                <p className="text-xs text-gray-500">
                  {correctionsMade === 0 ? 'No corrections yet' : `Labels corrected via feedback`}
                </p>
              </>
            )}
          </CardContent>
        </Card>

        {/* System Status - Enhanced */}
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">System Status</CardTitle>
            <Settings className="h-4 w-4 text-gray-600" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-green-600">Ready</div>
            <p className="text-xs text-gray-500">
              {isLoading ? 'Loading stats...' : 'All systems operational'}
            </p>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Getting Started</CardTitle>
          <CardDescription>
            Follow these steps to start using SLDCE
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex items-start gap-4">
            <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-blue-100 text-blue-600 font-semibold">
              1
            </div>
            <div>
              <h4 className="font-semibold">Upload a Dataset</h4>
              <p className="text-sm text-gray-500">
                Start by uploading a CSV dataset with your data
              </p>
            </div>
          </div>

          <div className="flex items-start gap-4">
            <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-blue-100 text-blue-600 font-semibold">
              2
            </div>
            <div>
              <h4 className="font-semibold">Run Detection</h4>
              <p className="text-sm text-gray-500">
                Let the system detect potentially mislabeled samples
              </p>
            </div>
          </div>

          <div className="flex items-start gap-4">
            <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-blue-100 text-blue-600 font-semibold">
              3
            </div>
            <div>
              <h4 className="font-semibold">Review & Correct</h4>
              <p className="text-sm text-gray-500">
                Review suggestions and make corrections
              </p>
            </div>
          </div>

          <div className="flex items-start gap-4">
            <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-blue-100 text-blue-600 font-semibold">
              4
            </div>
            <div>
              <h4 className="font-semibold">Apply & Retrain</h4>
              <p className="text-sm text-gray-500">
                Apply corrections and retrain to measure improvement
              </p>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}