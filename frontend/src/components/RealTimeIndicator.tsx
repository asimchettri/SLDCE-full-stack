import { Activity } from 'lucide-react';
import { Badge } from '@/components/ui/badge';

export function RealTimeIndicator() {
  return (
    <Badge variant="outline" className="gap-1.5">
      <Activity className="h-3 w-3 animate-pulse text-green-600" />
      <span className="text-xs">Live Updates</span>
    </Badge>
  );
}