"""
Complete Workflow Test - Tests entire detection → suggestion → feedback flow
Run this to verify the full SLDCE pipeline works end-to-end

Usage:
    python scripts/test_full_workflow.py --dataset-id 1
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy.orm import Session
from core.database import SessionLocal
from services.detection_service import DetectionService
from services.suggestion_service import SuggestionService
from services.feedback_service import FeedbackService
import argparse
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_full_workflow(dataset_id: int):
    """Test complete detection → suggestion → feedback workflow"""
    
    logger.info("=" * 60)
    logger.info("SLDCE FULL WORKFLOW TEST")
    logger.info("=" * 60)
    
    db: Session = SessionLocal()
    
    try:
        # STEP 1: Run Detection
        logger.info("\n[1/4] Running Detection...")
        detection_result = DetectionService.run_detection(
            db=db,
            dataset_id=dataset_id,
            confidence_threshold=0.7,
            max_samples=100,  # Test with 100 samples
            priority_weights={'confidence': 0.6, 'anomaly': 0.4},
            use_ml=True  # Use real ML pipeline
        )
        
        logger.info(f"✓ Detection complete")
        logger.info(f"  Total samples: {detection_result['total_samples_analyzed']}")
        logger.info(f"  Suspicious: {detection_result['suspicious_samples_found']}")
        logger.info(f"  Detection rate: {detection_result['detection_rate']}%")
        
        if detection_result['suspicious_samples_found'] == 0:
            logger.warning("⚠️  No suspicious samples found - try with more samples or different dataset")
            return True  # Not a failure, just means dataset is very clean
        
        # STEP 2: Generate Suggestions
        logger.info("\n[2/4] Generating Suggestions...")
        suggestion_result = SuggestionService.generate_suggestions(
            db=db,
            dataset_id=dataset_id,
            iteration=1,
            top_n=10  # Generate top 10 suggestions
        )
        
        logger.info(f"✓ Suggestions generated")
        logger.info(f"  Created: {suggestion_result['suggestions_created']}")
        
        # STEP 3: Get Suggestions
        logger.info("\n[3/4] Retrieving Suggestions...")
        suggestions = SuggestionService.get_suggestions(
            db=db,
            dataset_id=dataset_id,
            status='pending',
            limit=5
        )
        
        logger.info(f"✓ Retrieved {len(suggestions)} pending suggestions")
        
        if suggestions:
            logger.info("\n  Sample suggestion details:")
            first = suggestions[0]
            logger.info(f"    ID: {first.id}")
            logger.info(f"    Suggested Label: {first.suggested_label}")
            logger.info(f"    Confidence: {first.confidence:.3f}")
            logger.info(f"    Reason: {first.reason[:80]}...")
        
        # STEP 4: Simulate Human Feedback
        logger.info("\n[4/4] Simulating Human Feedback...")
        
        if suggestions:
            # Accept first suggestion
            feedback_count = 0
            for i, suggestion in enumerate(suggestions[:3]):
                action = ['accepted', 'rejected', 'modified'][i % 3]
                
                updated = SuggestionService.update_suggestion_status(
                    db=db,
                    suggestion_id=suggestion.id,
                    status=action,
                    reviewer_notes=f"Test feedback - {action}",
                    custom_label=suggestion.suggested_label + 1 if action == 'modified' else None
                )
                feedback_count += 1
            
            logger.info(f"✓ Created {feedback_count} feedback entries")
            
            # Get feedback stats
            feedback_stats = FeedbackService.get_stats(db, dataset_id)
            logger.info(f"\n  Feedback Statistics:")
            logger.info(f"    Total: {feedback_stats['total_feedback']}")
            logger.info(f"    Accepted: {feedback_stats['accepted']}")
            logger.info(f"    Rejected: {feedback_stats['rejected']}")
            logger.info(f"    Modified: {feedback_stats['modified']}")
        
        # STEP 5: Get Detection Stats
        logger.info("\n[5/5] Final Statistics...")
        det_stats = DetectionService.get_detection_stats(db, dataset_id)
        sug_stats = SuggestionService.get_suggestion_stats(db, dataset_id)
        
        logger.info(f"\n  Detection Stats:")
        logger.info(f"    Total samples: {det_stats['total_samples']}")
        logger.info(f"    Suspicious: {det_stats['suspicious_samples']}")
        logger.info(f"    High priority: {det_stats['high_priority_detections']}")
        
        logger.info(f"\n  Suggestion Stats:")
        logger.info(f"    Total: {sug_stats['total_suggestions']}")
        logger.info(f"    Pending: {sug_stats['pending']}")
        logger.info(f"    Acceptance rate: {sug_stats['acceptance_rate']:.1f}%")
        
        # SUCCESS
        logger.info("\n" + "=" * 60)
        logger.info("✅ FULL WORKFLOW TEST PASSED")
        logger.info("=" * 60)
        logger.info("\nAll components working together correctly!")
        logger.info("Ready for frontend integration!")
        
        return True
        
    except Exception as e:
        logger.error(f"\n❌ Workflow test failed: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False
        
    finally:
        db.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Test full SLDCE workflow")
    parser.add_argument(
        '--dataset-id',
        type=int,
        required=True,
        help='Dataset ID to test with'
    )
    
    args = parser.parse_args()
    
    success = test_full_workflow(args.dataset_id)
    sys.exit(0 if success else 1)