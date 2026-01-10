import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ReactQueryDevtools } from '@tanstack/react-query-devtools';
import { Toaster } from 'sonner';
import { Layout } from './components/layout/Layout';
import { HomePage } from './pages/HomePage';
import { DatasetsPage } from './pages/DatasetsPage';
import { ModelsPage } from './pages/ModelsPage';
import { ExperimentsPage } from './pages/ExperimentsPage';
import { DetectionPage } from './pages/DetectionPage';
import { CorrectionPage } from './pages/CorrectionPage';
import { FeedbackPage } from './pages/FeedbackPage';
import { EvaluationPage } from './pages/EvaluationPage';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      retry: 1,
    },
  },
});

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <Layout>
          <Routes>
            <Route path="/" element={<HomePage />} />
            <Route path="/datasets" element={<DatasetsPage />} />
            <Route path="/models" element={<ModelsPage />} />
            <Route path="/detection" element={<DetectionPage />} />
            <Route path="/correction" element={<CorrectionPage />} />
            <Route path="/feedback" element={<FeedbackPage />} />
            <Route path="/evaluation" element={<EvaluationPage />} />
            <Route path="/settings" element={<div className="text-center text-gray-500 py-12">Settings Page (Coming Soon)</div>} />
            <Route path="/experiments" element={<ExperimentsPage />} />
          </Routes>
        </Layout>
      </BrowserRouter>
      <Toaster position="top-right" richColors />
      <ReactQueryDevtools initialIsOpen={false} />
    </QueryClientProvider>
  );
}

export default App;