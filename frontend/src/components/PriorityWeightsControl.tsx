import { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Label } from '@/components/ui/label';
import { Slider } from '@/components/ui/slider';
import { Button } from '@/components/ui/button';
import { RotateCcw, Settings } from 'lucide-react';
import type { PriorityWeights } from '@/types/detection';

interface PriorityWeightsControlProps {
  weights: PriorityWeights;
  onChange: (weights: PriorityWeights) => void;
  onReset: () => void;
}

export function PriorityWeightsControl({ weights, onChange, onReset }: PriorityWeightsControlProps) {
  const [localConfidence, setLocalConfidence] = useState(weights.confidence * 100);

  // Auto-calculate anomaly weight to ensure they sum to 100%
  useEffect(() => {
    const anomaly = 100 - localConfidence;
    onChange({
      confidence: localConfidence / 100,
      anomaly: anomaly / 100,
    });
  }, [localConfidence, onChange]);

  // Update local state when external weights change
  useEffect(() => {
    setLocalConfidence(weights.confidence * 100);
  }, [weights.confidence]);

  const isDefault = weights.confidence === 0.6 && weights.anomaly === 0.4;

  const handleSliderChange = (value: number[]) => {
    setLocalConfidence(value[0]);
  };

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Settings className="h-5 w-5" />
            <CardTitle>Priority Weights</CardTitle>
          </div>
          <Button
            variant="ghost"
            size="sm"
            onClick={onReset}
            disabled={isDefault}
          >
            <RotateCcw className="h-4 w-4 mr-2" />
            Reset
          </Button>
        </div>
        <CardDescription>
          Adjust how signals contribute to priority scoring
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Confidence Weight Slider */}
        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <Label>Confidence Weight</Label>
            <span className="text-sm font-semibold text-blue-600">
              {localConfidence.toFixed(0)}%
            </span>
          </div>
          <Slider
            value={[localConfidence]}
            onValueChange={handleSliderChange}
            min={0}
            max={100}
            step={5}
            className="w-full"
          />
        </div>

        {/* Anomaly Weight (Auto-calculated) */}
        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <Label>Anomaly Weight</Label>
            <span className="text-sm font-semibold text-purple-600">
              {(100 - localConfidence).toFixed(0)}%
            </span>
          </div>
          <div className="h-2 w-full bg-gray-200 rounded-full overflow-hidden">
            <div
              className="h-full bg-purple-600 transition-all"
              style={{ width: `${100 - localConfidence}%` }}
            />
          </div>
        </div>

        {/* Visual Representation */}
        <div className="pt-2 border-t">
          <div className="text-xs text-gray-600 mb-2">Priority Formula:</div>
          <div className="p-3 bg-gray-50 rounded text-sm font-mono">
            Priority = (Confidence × {(weights.confidence).toFixed(2)}) + (Anomaly × {(weights.anomaly).toFixed(2)})
          </div>
        </div>

        {/* Preset Buttons */}
        <div className="pt-2 border-t">
          <Label className="text-xs text-gray-600 mb-2 block">Quick Presets:</Label>
          <div className="grid grid-cols-3 gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={() => setLocalConfidence(60)}
              className={localConfidence === 60 ? 'bg-blue-50 border-blue-300' : ''}
            >
              Balanced
              <span className="text-xs ml-1">(60/40)</span>
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={() => setLocalConfidence(70)}
              className={localConfidence === 70 ? 'bg-blue-50 border-blue-300' : ''}
            >
              Confidence
              <span className="text-xs ml-1">(70/30)</span>
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={() => setLocalConfidence(30)}
              className={localConfidence === 30 ? 'bg-blue-50 border-blue-300' : ''}
            >
              Anomaly
              <span className="text-xs ml-1">(30/70)</span>
            </Button>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}