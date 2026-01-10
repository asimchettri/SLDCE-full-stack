import { useEffect } from 'react';
import { useQueryClient } from '@tanstack/react-query';

export function useRealTimeMetrics(datasetId: number | undefined, enabled: boolean = true) {
  const queryClient = useQueryClient();

  useEffect(() => {
    if (!datasetId || !enabled) return;

    // Refresh metrics every 10 seconds
    const interval = setInterval(() => {
      queryClient.invalidateQueries({ queryKey: ['detection-stats', datasetId] });
      queryClient.invalidateQueries({ queryKey: ['detections', datasetId] });
    }, 10000);

    return () => clearInterval(interval);
  }, [datasetId, enabled, queryClient]);
}