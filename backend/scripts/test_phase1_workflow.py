"""
Phase 1 Complete Workflow Test
🔧 NEW FILE: End-to-end integration test

Tests the complete manual workflow:
1. Upload dataset
2. Run detection
3. Generate suggestions
4. Simulate human review
5. Apply corrections
6. Retrain model
7. Compare results
"""
import requests
import time
from pathlib import Path

# Configuration
API_BASE = "http://localhost:8000/api/v1"
DATASET_FILE = Path("../ml_pipeline/data/raw/adult.csv")  # Adjust path
DATASET_NAME = "Test Adult Dataset"

def print_step(step_num, description):
    print(f"\n{'='*60}")
    print(f"STEP {step_num}: {description}")
    print('='*60)

def print_result(data):
    import json
    print(json.dumps(data, indent=2))

def main():
    print("\n🚀 SLDCE PHASE 1 - COMPLETE WORKFLOW TEST")
    print("Testing manual workflow with all integration points")
    
    # ==================== STEP 1: Upload Dataset ====================
    print_step(1, "Upload Dataset")
    
    if not DATASET_FILE.exists():
        print(f"❌ Dataset file not found: {DATASET_FILE}")
        print("Please update DATASET_FILE path in the script")
        return
    
    with open(DATASET_FILE, 'rb') as f:
        files = {'file': f}
        data = {
            'name': DATASET_NAME,
            'description': 'Test dataset for Phase 1 workflow',
            'label_column': 'auto'  # Auto-detect label column
        }
        
        response = requests.post(
            f"{API_BASE}/datasets/upload",
            files=files,
            data=data
        )
    
    if response.status_code == 201:
        dataset = response.json()
        dataset_id = dataset['id']
        print(f"✅ Dataset uploaded: ID={dataset_id}")
        print(f"   Samples: {dataset['num_samples']}")
        print(f"   Features: {dataset['num_features']}")
        print(f"   Classes: {dataset['num_classes']}")
    else:
        print(f"❌ Upload failed: {response.status_code}")
        print_result(response.json())
        return
    
    # ==================== STEP 2: Run Detection ====================
    print_step(2, "Run Detection")
    
    response = requests.post(
        f"{API_BASE}/detection/run",
        json={
            "dataset_id": dataset_id,
            "confidence_threshold": 0.7,
            "priority_weights": {
                "confidence": 0.6,
                "anomaly": 0.4
            }
        }
    )
    
    if response.status_code == 200:
        detection_result = response.json()
        print("✅ Detection complete:")
        print(f"   Total analyzed: {detection_result['total_samples_analyzed']}")
        print(f"   Suspicious found: {detection_result['suspicious_samples_found']}")
        print(f"   Detection rate: {detection_result['detection_rate']}%")
    else:
        print(f"❌ Detection failed: {response.status_code}")
        print_result(response.json())
        return
    
    # ==================== STEP 3: Generate Suggestions ====================
    print_step(3, "Generate Suggestions")
    
    response = requests.post(
        f"{API_BASE}/suggestions/generate",
        json={
            "dataset_id": dataset_id,
            "iteration": 1,
            "top_n": 50  # Limit to top 50 for testing
        }
    )
    
    if response.status_code == 200:
        suggestion_result = response.json()
        print("✅ Suggestions generated:")
        print(f"   Total created: {suggestion_result['suggestions_created']}")
    else:
        print(f"❌ Suggestion generation failed: {response.status_code}")
        print_result(response.json())
        return
    
    # ==================== STEP 4: Get Suggestions for Review ====================
    print_step(4, "Get Suggestions for Review")
    
    response = requests.get(
        f"{API_BASE}/suggestions/list",
        params={
            "dataset_id": dataset_id,
            "status": "pending",
            "page": 1,
            "page_size": 20
        }
    )
    
    if response.status_code == 200:
        suggestions_data = response.json()
        suggestions = suggestions_data['suggestions']
        print(f"✅ Retrieved {len(suggestions)} pending suggestions")
        
        if len(suggestions) == 0:
            print("⚠️  No suggestions to review. Workflow complete but no corrections needed.")
            return
    else:
        print(f"❌ Failed to get suggestions: {response.status_code}")
        return
    
    # ==================== STEP 5: Simulate Human Review ====================
    print_step(5, "Simulate Human Review (Auto-accept high confidence)")
    
    accepted_count = 0
    rejected_count = 0
    
    for suggestion in suggestions[:10]:  # Review first 10
        # Accept suggestions with confidence > 0.85
        if suggestion['confidence'] > 0.85:
            status = 'accepted'
            accepted_count += 1
        else:
            status = 'rejected'
            rejected_count += 1
        
        response = requests.patch(
            f"{API_BASE}/suggestions/{suggestion['id']}/status",
            json={
                "status": status,
                "reviewer_notes": f"Auto-review: {status}"
            }
        )
        
        if response.status_code != 200:
            print(f"⚠️  Failed to update suggestion {suggestion['id']}")
    
    print(f"✅ Review complete:")
    print(f"   Accepted: {accepted_count}")
    print(f"   Rejected: {rejected_count}")
    
    # ==================== STEP 6: Preview Corrections ====================
    print_step(6, "Preview Corrections")
    
    response = requests.get(
        f"{API_BASE}/corrections/preview/{dataset_id}",
        params={"iteration": 1}
    )
    
    if response.status_code == 200:
        preview = response.json()
        print("✅ Preview:")
        print(f"   Total feedback: {preview['total_feedback']}")
        print(f"   Corrections to apply: {preview['corrections_to_apply']}")
        print(f"   Labels to change: {preview['labels_to_change']}")
        print(f"   Estimated noise reduction: {preview['estimated_noise_reduction']}%")
    else:
        print(f"❌ Preview failed: {response.status_code}")
        print_result(response.json())
        return
    
    # ==================== STEP 7: Apply Corrections ====================
    print_step(7, "Apply Corrections to Dataset")
    
    response = requests.post(
        f"{API_BASE}/corrections/apply/{dataset_id}",
        params={"iteration": 1}
    )
    
    if response.status_code == 200:
        correction_result = response.json()
        print("✅ Corrections applied:")
        print(f"   Feedback processed: {correction_result['total_feedback_processed']}")
        print(f"   Corrections applied: {correction_result['corrections_applied']}")
        print(f"   Labels changed: {correction_result['labels_changed']}")
    else:
        print(f"❌ Apply corrections failed: {response.status_code}")
        print_result(response.json())
        return
    
    # ==================== STEP 8: Retrain Model ====================
    print_step(8, "Retrain Model on Corrected Data")
    
    print("Training model... (this may take a few seconds)")
    response = requests.post(
        f"{API_BASE}/retrain/retrain/{dataset_id}",
        params={
            "iteration": 1,
            "test_size": 0.2
        }
    )
    
    if response.status_code == 200:
        retrain_result = response.json()
        print("✅ Model retrained successfully!")
        print("\n📊 RESULTS:")
        print(f"   Baseline accuracy: {retrain_result['baseline_metrics']['accuracy']:.4f}")
        print(f"   After corrections: {retrain_result['retrained_metrics']['accuracy']:.4f}")
        print(f"   Improvement: {retrain_result['improvement']['absolute']:+.4f} ({retrain_result['improvement']['percentage']:+.2f}%)")
        print(f"\n   Training info:")
        print(f"   - Samples corrected: {retrain_result['training_info']['samples_corrected']}")
        print(f"   - Labels changed: {retrain_result['training_info']['labels_changed']}")
        print(f"   - Noise reduced: {retrain_result['training_info']['noise_reduced_pct']:.2f}%")
        print(f"   - Training time: {retrain_result['training_info']['training_time_seconds']:.2f}s")
    else:
        print(f"❌ Retraining failed: {response.status_code}")
        print_result(response.json())
        return
    
    # ==================== STEP 9: Get Final Summary ====================
    print_step(9, "Get Correction Summary")
    
    response = requests.get(
        f"{API_BASE}/corrections/summary/{dataset_id}"
    )
    
    if response.status_code == 200:
        summary = response.json()
        print("✅ Final Summary:")
        print(f"   Total samples: {summary['total_samples']}")
        print(f"   Corrected samples: {summary['corrected_samples']}")
        print(f"   Labels changed: {summary['labels_changed']}")
        print(f"   Correction rate: {summary['correction_rate']}%")
        print(f"   Noise reduction: {summary['noise_reduction']}%")
    else:
        print(f"⚠️  Could not get summary: {response.status_code}")
    
    # ==================== SUCCESS ====================
    print("\n" + "="*60)
    print("✅ PHASE 1 WORKFLOW TEST COMPLETE!")
    print("="*60)
    print("\n📊 Summary:")
    print(f"   Dataset ID: {dataset_id}")
    print(f"   Detection: {detection_result['suspicious_samples_found']} suspicious samples")
    print(f"   Review: {accepted_count} accepted, {rejected_count} rejected")
    print(f"   Corrections: {correction_result['labels_changed']} labels changed")
    print(f"   Improvement: {retrain_result['improvement']['percentage']:+.2f}%")
    print("\n✨ All integration points working correctly!")

if __name__ == "__main__":
    main()