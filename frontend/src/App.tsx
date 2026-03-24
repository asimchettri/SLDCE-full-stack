import { lazy, Suspense } from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ReactQueryDevtools } from '@tanstack/react-query-devtools';
import { Toaster } from 'sonner';
import { Layout } from './components/layout/Layout';

// Eager — fast, lightweight pages
import { HomePage } from './pages/HomePage';
import { DatasetsPage } from './pages/DatasetsPage';
import { CorrectionPage } from './pages/CorrectionPage';
import { FeedbackPage } from './pages/FeedbackPage';

// Lazy — heavy pages with charts/ML data
const DetectionPage  = lazy(() => import('./pages/DetectionPage').then(m => ({ default: m.DetectionPage })));
const EvaluationPage = lazy(() => import('./pages/EvaluationPage').then(m => ({ default: m.EvaluationPage })));
const BenchmarkPage  = lazy(() => import('./pages/BenchmarkPage').then(m => ({ default: m.BenchmarkPage })));
const MemoryPage     = lazy(() => import('./pages/MemoryPage').then(m => ({ default: m.MemoryPage })));
const ModelsPage     = lazy(() => import('./pages/ModelsPage').then(m => ({ default: m.ModelsPage })));
const ExperimentsPage = lazy(() => import('./pages/ExperimentsPage').then(m => ({ default: m.ExperimentsPage })));

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      retry: 1,
      staleTime: 1000 * 60,        // 1 minute — don't re-fetch unless data is stale
      gcTime: 1000 * 60 * 5,       // 5 minutes — keep in cache after unmount
    },
  },
});

function PageLoader() {
  return (
    <div className="flex items-center justify-center py-24">
      <div className="animate-spin rounded-full h-8 w-8 border-2 border-blue-600 border-t-transparent" />
    </div>
  );
}

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <Layout>
          <Suspense fallback={<PageLoader />}>
            <Routes>
              <Route path="/"           element={<HomePage />} />
              <Route path="/datasets"   element={<DatasetsPage />} />
              <Route path="/detection"  element={<DetectionPage />} />
              <Route path="/correction" element={<CorrectionPage />} />
              <Route path="/feedback"   element={<FeedbackPage />} />
              <Route path="/evaluation" element={<EvaluationPage />} />
              <Route path="/memory"     element={<MemoryPage />} />
              <Route path="/benchmarks" element={<BenchmarkPage />} />
              <Route path="/models"     element={<ModelsPage />} />
              <Route path="/experiments" element={<ExperimentsPage />} />
              <Route path="/settings"   element={<div className="text-center text-gray-500 py-12">Settings Page (Coming Soon)</div>} />
            </Routes>
          </Suspense>
        </Layout>
      </BrowserRouter>
      <Toaster position="top-right" richColors />
      <ReactQueryDevtools initialIsOpen={false} />
    </QueryClientProvider>
  );
}

export default App;