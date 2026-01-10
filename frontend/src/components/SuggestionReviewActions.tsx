import { useState } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { suggestionAPI } from '@/services/api';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Check, X, Edit3, SkipForward } from 'lucide-react';
import type { Suggestion, SuggestionReviewStatus } from '@/types/suggestion';
import { toast } from 'sonner';

interface SuggestionReviewActionsProps {
  suggestion: Suggestion;
  onComplete?: () => void;
}

export function SuggestionReviewActions({ 
  suggestion, 
  onComplete 
}: SuggestionReviewActionsProps) {
  const [showModify, setShowModify] = useState(false);
  const [customLabel, setCustomLabel] = useState<string>('');
  const [notes, setNotes] = useState<string>('');
  
  const queryClient = useQueryClient();

  const updateStatusMutation = useMutation({
    mutationFn: ({ status, reviewerNotes, customLabel }: { 
      status: SuggestionReviewStatus; 
      reviewerNotes?: string;
      customLabel?: number;  //Add custom label to mutation type
    }) =>
      suggestionAPI.updateStatus(suggestion.id, { 
        status, 
        reviewer_notes: reviewerNotes,
        custom_label: customLabel  
      }),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ['suggestions'] });
      queryClient.invalidateQueries({ queryKey: ['suggestion-stats'] });
      
      const statusMessages: Record<SuggestionReviewStatus, string> = {
        accepted: '✅ Suggestion accepted!',
        rejected: '❌ Suggestion rejected',
        modified: '✏️ Custom correction applied',
      };
      
      toast.success(statusMessages[variables.status] || 'Updated');
      onComplete?.();
    },
    onError: (error) => {
      toast.error('Failed to update suggestion');
      console.error(error);
    }
  });

  const handleAccept = () => {
    updateStatusMutation.mutate({ 
      status: 'accepted' as const,
      reviewerNotes: notes || 'Accepted suggested label'
    });
  };

  const handleReject = () => {
    updateStatusMutation.mutate({ 
      status: 'rejected' as const,
      reviewerNotes: notes || 'Rejected - current label is correct'
    });
  };

  const handleModify = () => {
    if (!customLabel || customLabel.trim() === '') {
      toast.error('Please enter a custom label');
      return;
    }
    
    const labelNumber = parseInt(customLabel);
    if (isNaN(labelNumber)) {
      toast.error('Label must be a valid number');
      return;
    }
    
    updateStatusMutation.mutate({ 
      status: 'modified' as const,
      reviewerNotes: notes || `Modified to custom label: ${labelNumber}`,
      customLabel: labelNumber  //  Send as camelCase to match mutation type
    });
  };

  const handleSkip = () => {
    // Simply close without making any update
    toast.info('⏭️ Skipped for later review');
    onComplete?.();
  };

  if (showModify) {
    return (
      <div className="space-y-3 bg-blue-50 p-3 rounded-lg border border-blue-200">
        <div className="text-sm font-semibold text-blue-900">Enter Custom Label</div>
        
        <div className="space-y-2">
          <Label htmlFor="customLabel" className="text-xs">Custom Label</Label>
          <Input
            id="customLabel"
            type="number"
            placeholder="Enter class number"
            value={customLabel}
            onChange={(e) => setCustomLabel(e.target.value)}
            className="h-8"
          />
        </div>

        <div className="space-y-2">
          <Label htmlFor="modifyNotes" className="text-xs">Notes (Optional)</Label>
          <Input
            id="modifyNotes"
            placeholder="Why this custom label?"
            value={notes}
            onChange={(e) => setNotes(e.target.value)}
            className="h-8"
          />
        </div>

        <div className="flex gap-2">
          <Button
            size="sm"
            onClick={handleModify}
            disabled={updateStatusMutation.isPending}
            className="flex-1"
          >
            <Check className="h-3 w-3 mr-1" />
            Apply
          </Button>
          <Button
            size="sm"
            variant="outline"
            onClick={() => setShowModify(false)}
            className="flex-1"
          >
            Cancel
          </Button>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-3 bg-gray-50 p-3 rounded-lg">
      {/* Optional Notes */}
      <div className="space-y-2">
        <Label htmlFor="reviewNotes" className="text-xs">
          Review Notes (Optional)
        </Label>
        <Input
          id="reviewNotes"
          placeholder="Add your notes..."
          value={notes}
          onChange={(e) => setNotes(e.target.value)}
          className="h-8 text-sm"
        />
      </div>

      {/* Action Buttons */}
      <div className="grid grid-cols-2 gap-2">
        <Button
          size="sm"
          onClick={handleAccept}
          disabled={updateStatusMutation.isPending}
          className="bg-green-600 hover:bg-green-700"
        >
          <Check className="h-3 w-3 mr-1" />
          Accept
        </Button>
        <Button
          size="sm"
          variant="destructive"
          onClick={handleReject}
          disabled={updateStatusMutation.isPending}
        >
          <X className="h-3 w-3 mr-1" />
          Reject
        </Button>
        <Button
          size="sm"
          variant="outline"
          onClick={() => setShowModify(true)}
          disabled={updateStatusMutation.isPending}
        >
          <Edit3 className="h-3 w-3 mr-1" />
          Modify
        </Button>
        <Button
          size="sm"
          variant="ghost"
          onClick={handleSkip}
          disabled={updateStatusMutation.isPending}
        >
          <SkipForward className="h-3 w-3 mr-1" />
          Skip
        </Button>
      </div>
    </div>
  );
}