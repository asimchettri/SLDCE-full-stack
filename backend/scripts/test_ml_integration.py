"""
ML Integration Testing Script
Run this to verify Dev 1's ML pipeline integrates correctly with your backend

Usage:
    python scripts/test_ml_integration.py --dataset-id 1
"""
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy.orm import Session
from core.database import SessionLocal
from services.ml_integration import get_ml_integration
from services.data_preprocessor import DataPreprocessor
from models.dataset import Sample
import argparse
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_ml_integration(dataset_id: int, max_samples: int = 100):
    """
    Test ML integration end-to-end
    
    Args:
        dataset_id: Dataset to test with
        max_samples: Max samples to use for testing
    """
    logger.info("=" * 60)
    logger.info("SLDCE ML Integration Test")
    logger.info("=" * 60)
    
    db: Session = SessionLocal()
    
    try:
        # Step 1: Validate dataset
        logger.info(f"\n[1/5] Validating dataset {dataset_id}...")
        validation = DataPreprocessor.validate_dataset_format(dataset_id, db)
        
        if not validation['valid']:
            logger.error(f"❌ Dataset validation failed: {validation.get('error', 'Unknown error')}")
            if 'issues' in validation:
                for issue in validation['issues']:
                    logger.error(f"  - {issue}")
            return False
        
        logger.info(f"✓ Dataset valid ({validation['num_samples_checked']} samples checked)")
        logger.info(f"  Feature dimensions: {validation['feature_dimensions']}")
        
        # Step 2: Get dataset info
        logger.info(f"\n[2/5] Getting dataset information...")
        info = DataPreprocessor.get_dataset_info(dataset_id, db)
        logger.info(f"✓ Dataset: {info['name']}")
        logger.info(f"  Samples: {info['num_samples']}")
        logger.info(f"  Features: {info['num_features']}")
        logger.info(f"  Classes: {info['num_classes']}")
        
        # Step 3: Get samples
        logger.info(f"\n[3/5] Loading samples from database...")
        samples = db.query(Sample).filter(
            Sample.dataset_id == dataset_id
        ).limit(max_samples).all()
        
        if not samples:
            logger.error(f"❌ No samples found for dataset {dataset_id}")
            return False
        
        logger.info(f"✓ Loaded {len(samples)} samples")
        
        # Step 4: Initialize ML integration
        logger.info(f"\n[4/5] Initializing ML integration...")
        ml = get_ml_integration()
        logger.info(f"✓ ML integration ready")
        logger.info(f"  Config loaded: {bool(ml.config)}")
        logger.info(f"  Model type: {ml.config.get('model', {}).get('name', 'Unknown')}")
        
        # Step 5: Run detection
        logger.info(f"\n[5/5] Running detection pipeline...")
        logger.info("  This may take a minute...")
        
        try:
            results = ml.run_full_detection(
                samples=samples,
                priority_weights={'confidence': 0.6, 'anomaly': 0.4}
            )
            
            logger.info(f"✓ Detection complete!")
            logger.info(f"  Results generated: {len(results)}")
            
            # Analyze results
            if results:
                flagged = sum(1 for r in results if r['flagged_by'] != 'none')
                confidence_flags = sum(1 for r in results if 'confidence' in r['flagged_by'])
                anomaly_flags = sum(1 for r in results if 'anomaly' in r['flagged_by'])
                both_flags = sum(1 for r in results if r['flagged_by'] == 'both')
                
                avg_priority = sum(r['priority_score'] for r in results) / len(results)
                avg_confidence = sum(r['confidence_score'] for r in results) / len(results)
                avg_anomaly = sum(r['anomaly_score'] for r in results) / len(results)
                
                logger.info(f"\n  📊 Detection Statistics:")
                logger.info(f"     Flagged samples: {flagged}/{len(results)} ({flagged/len(results)*100:.1f}%)")
                logger.info(f"     Confidence flags: {confidence_flags}")
                logger.info(f"     Anomaly flags: {anomaly_flags}")
                logger.info(f"     Both signals: {both_flags}")
                logger.info(f"     Avg priority score: {avg_priority:.3f}")
                logger.info(f"     Avg confidence: {avg_confidence:.3f}")
                logger.info(f"     Avg anomaly: {avg_anomaly:.3f}")
                
                # Show top 3 suspicious samples
                sorted_results = sorted(results, key=lambda x: x['priority_score'], reverse=True)
                logger.info(f"\n  🔍 Top 3 Suspicious Samples:")
                for i, r in enumerate(sorted_results[:3], 1):
                    logger.info(f"     {i}. Sample {r['sample_id']}")
                    logger.info(f"        Priority: {r['priority_score']:.3f}")
                    logger.info(f"        Flagged by: {r['flagged_by']}")
                    logger.info(f"        Reason: {r['reason'][:80]}...")
            
        except Exception as e:
            logger.error(f"❌ Detection failed: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return False
        
        # Success!
        logger.info("\n" + "=" * 60)
        logger.info("✅ ML INTEGRATION TEST PASSED")
        logger.info("=" * 60)
        logger.info("\nYour ML pipeline is correctly integrated!")
        logger.info("You can now use the detection API endpoints.")
        
        return True
        
    except Exception as e:
        logger.error(f"\n❌ Test failed with error: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False
        
    finally:
        db.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Test ML integration")
    parser.add_argument(
        '--dataset-id',
        type=int,
        required=True,
        help='Dataset ID to test with'
    )
    parser.add_argument(
        '--max-samples',
        type=int,
        default=100,
        help='Maximum samples to use for testing'
    )
    
    args = parser.parse_args()
    
    success = test_ml_integration(args.dataset_id, args.max_samples)
    sys.exit(0 if success else 1)