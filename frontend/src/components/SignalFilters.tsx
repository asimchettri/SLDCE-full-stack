import { Label } from '@/components/ui/label';
import { Input } from '@/components/ui/input';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import type { SignalType } from '@/types/detection';

interface SignalFiltersProps {
  minConfidence: number | undefined;
  minAnomaly: number | undefined;
  signalType: SignalType;
  onMinConfidenceChange: (value: number | undefined) => void;
  onMinAnomalyChange: (value: number | undefined) => void;
  onSignalTypeChange: (value: SignalType) => void;
}

export function SignalFilters({
  minConfidence,
  minAnomaly,
  signalType,
  onMinConfidenceChange,
  onMinAnomalyChange,
  onSignalTypeChange,
}: SignalFiltersProps) {
  return (
    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
      {/* Min Confidence Filter */}
      <div className="space-y-2">
        <Label>Min Confidence Score</Label>
        <Input
          type="number"
          min="0"
          max="1"
          step="0.1"
          placeholder="No minimum"
          value={minConfidence ?? ''}
          onChange={(e) => {
            const value = e.target.value;
            onMinConfidenceChange(value ? parseFloat(value) : undefined);
          }}
        />
        <p className="text-xs text-gray-500">
          Filter samples with confidence ≥ this value
        </p>
      </div>

      {/* Min Anomaly Filter */}
      <div className="space-y-2">
        <Label>Min Anomaly Score</Label>
        <Input
          type="number"
          min="0"
          max="1"
          step="0.1"
          placeholder="No minimum"
          value={minAnomaly ?? ''}
          onChange={(e) => {
            const value = e.target.value;
            onMinAnomalyChange(value ? parseFloat(value) : undefined);
          }}
        />
        <p className="text-xs text-gray-500">
          Filter samples with anomaly ≥ this value
        </p>
      </div>

      {/* Signal Type Filter */}
      <div className="space-y-2">
        <Label>Dominant Signal</Label>
        <Select value={signalType} onValueChange={(value) => onSignalTypeChange(value as SignalType)}>
          <SelectTrigger>
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All Signals</SelectItem>
            <SelectItem value="confidence">Confidence Dominant</SelectItem>
            <SelectItem value="anomaly">Anomaly Dominant</SelectItem>
            <SelectItem value="both">Both High (≥0.7)</SelectItem>
          </SelectContent>
        </Select>
        <p className="text-xs text-gray-500">
          Filter by which signal is stronger
        </p>
      </div>
    </div>
  );
}