"""
Detection service - Business logic for error detection
UPDATED: Auto-creates model entry in database when running detection
"""
from sqlalchemy.orm import Session
from models.dataset import Sample, Detection
from models.model import MLModel 
from fastapi import HTTPException
from typing import List, Dict, Any, Optional
import json
from datetime import datetime
import logging

from services.ml_integration import get_ml_integration

logger = logging.getLogger(__name__)


class DetectionService:
    """Service class for detection operations"""
    
    @staticmethod
    def _create_or_get_model(
        db: Session,
        dataset_id: int,
        model_name: str,
        model_params: Dict[str, Any],
        is_baseline: bool = True
    ) -> MLModel:
        """
        
        
        Args:
            db: Database session
            dataset_id: Dataset ID
            model_name: Model type (e.g., 'random_forest')
            model_params: Model hyperparameters
            is_baseline: Whether this is the baseline model (before corrections)
            
        Returns:
            MLModel instance
        """
        # Check if baseline model already exists for this dataset
        existing_model = db.query(MLModel).filter(
            MLModel.dataset_id == dataset_id,
            MLModel.model_type == model_name,
            MLModel.is_baseline == is_baseline,
            MLModel.is_active == True
        ).first()
        
        if existing_model:
            logger.info(f"Using existing model: {existing_model.name} (ID: {existing_model.id})")
            return existing_model
        
        # Create new model entry
        model_display_name = f"{model_name.replace('_', ' ').title()}"
        if is_baseline:
            model_display_name += " (Baseline)"
        
        model = MLModel(
            dataset_id=dataset_id,
            name=model_display_name,
            model_type=model_name,
            description=f"Model trained for detection on dataset {dataset_id}",
            hyperparameters=json.dumps(model_params),
            is_baseline=is_baseline,
            is_active=True
        )
        
        db.add(model)
        db.commit()
        db.refresh(model)
        
        logger.info(f"✅ Created new model: {model.name} (ID: {model.id})")
        return model
    
    @staticmethod
    def run_detection(
        db: Session,
        dataset_id: int,
        confidence_threshold: float = 0.7,
        max_samples: Optional[int] = None,
        priority_weights: Optional[Dict[str, float]] = None,
        use_ml: bool = True
    ) -> Dict[str, Any]:
        """
        Run detection on a dataset using Dev 1's ML pipeline
        UPDATED: Now creates/updates model in database
        
        Args:
            db: Database session
            dataset_id: ID of dataset to analyze
            confidence_threshold: Threshold for confidence detection
            max_samples: Optional limit on samples to analyze
            priority_weights: Custom weights for signal fusion
            use_ml: If True, use ML pipeline. If False, use simulation (for testing)
            
        Returns:
            Detection run summary with stats
        """
        # Get samples from database
        samples_query = db.query(Sample).filter(Sample.dataset_id == dataset_id)
        
        if max_samples:
            samples_query = samples_query.limit(max_samples)
        
        samples = samples_query.all()
        
        if not samples:
            raise HTTPException(
                status_code=404,
                detail=f"No samples found for dataset {dataset_id}"
            )
        
        logger.info(f"Running detection on {len(samples)} samples from dataset {dataset_id}")
        
        detections_created = 0
        iteration = 1  # Phase 1: Single iteration
        model_id = None  #  Track model ID
        
        if use_ml:
            # === USE DEV 1'S ML PIPELINE ===
            try:
                ml = get_ml_integration()
                
                #  Get model config from ML integration
                model_name = ml.config.get("model", {}).get("name", "random_forest")
                model_params = ml.config.get("model", {}).get("params", {
                    "n_estimators": 100,
                    "random_state": 42,
                    "n_jobs": -1
                })
                
                #  Create or get model in database
                db_model = DetectionService._create_or_get_model(
                    db,
                    dataset_id=dataset_id,
                    model_name=model_name,
                    model_params=model_params,
                    is_baseline=True
                )
                model_id = db_model.id
                
                # Run full detection pipeline
                ml_results = ml.run_full_detection(
                    samples=samples,
                    priority_weights=priority_weights,
                    confidence_threshold=confidence_threshold
                )
                
                #  Extract metrics from ML pipeline for model update
                if ml_results and len(ml_results) > 0:
                    # Calculate basic metrics from detection results
                    total_analyzed = len(ml_results)
                    flagged_count = sum(1 for r in ml_results if r['flagged_by'] != 'none')
                    
                    # Update model with training info
                    db_model.num_samples_trained = total_analyzed
                    # Note: Actual accuracy will be calculated after corrections in retrain phase
                    db.commit()
                
                # Create Detection records from ML results
                for result in ml_results:
                    # Skip samples that aren't flagged by either signal
                    if result['flagged_by'] == 'none':
                        continue  

                    # Find corresponding sample
                    sample = next(
                        (s for s in samples if s.id == result['sample_id']),
                        None
                    )
                    
                    if not sample:
                        logger.warning(f"Sample {result['sample_id']} not found")
                        continue
                    
                    # Create detection record
                    detection = Detection(
                        sample_id=sample.id,
                        iteration=iteration,
                        confidence_score=result['confidence_score'],
                        anomaly_score=result['anomaly_score'],
                        predicted_label=result['predicted_label'],
                        priority_score=result['priority_score'],
                        signal_breakdown=json.dumps(result['signal_breakdown']),
                        priority_weights=json.dumps(priority_weights) if priority_weights else None
                    )
                    
                    db.add(detection)
                    sample.is_suspicious = True
                    detections_created += 1
                
                logger.info(f"Created {detections_created} detection records")
                
            except Exception as e:
                logger.error(f"ML detection failed: {e}")
                raise HTTPException(
                    status_code=500,
                    detail=f"Detection failed: {str(e)}"
                )
        
        else:
            # === FALLBACK: SIMULATION (for testing without ML) ===
            logger.warning("Using simulation mode - not recommended for production")
            
            for sample in samples:
                # Simulate detection on actually mislabeled samples
                is_mislabeled = sample.original_label != sample.current_label
                
                if is_mislabeled:
                    import random
                    confidence_score = random.uniform(0.75, 0.95)
                    anomaly_score = random.uniform(0.65, 0.90)
                    
                    priority_score = DetectionService.calculate_priority_score(
                        confidence_score,
                        anomaly_score,
                        priority_weights
                    )
                    
                    detection = Detection(
                        sample_id=sample.id,
                        iteration=iteration,
                        confidence_score=confidence_score,
                        anomaly_score=anomaly_score,
                        predicted_label=sample.original_label,
                        priority_score=priority_score,
                        signal_breakdown=json.dumps({
                            "confidence": confidence_score,
                            "anomaly": anomaly_score,
                            "simulated": True
                        })
                    )
                    
                    db.add(detection)
                    sample.is_suspicious = True
                    detections_created += 1
        
        # Commit to database
        db.commit()
        
        # Calculate stats
        total_samples = len(samples)
        suspicious_count = detections_created
        detection_rate = (suspicious_count / total_samples * 100) if total_samples > 0 else 0
        
        return {
            "dataset_id": dataset_id,
            "model_id": model_id,  #  Return model ID
            "iteration": iteration,
            "total_samples_analyzed": total_samples,
            "suspicious_samples_found": suspicious_count,
            "detection_rate": round(detection_rate, 2),
            "confidence_threshold": confidence_threshold,
            "ml_pipeline_used": use_ml,
            "priority_weights": priority_weights,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    @staticmethod
    def calculate_priority_score(
        confidence: float,
        anomaly: float,
        weights: Optional[Dict[str, float]] = None
    ) -> float:
        """Calculate priority score with configurable weights"""
        if weights is None:
            weights = {"confidence": 0.6, "anomaly": 0.4}
        
        priority = (
            confidence * weights.get("confidence", 0.6) +
            anomaly * weights.get("anomaly", 0.4)
        )
        return min(max(priority, 0.0), 1.0)
    
    @staticmethod
    def get_detections(
        db: Session,
        dataset_id: Optional[int] = None,
        iteration: Optional[int] = None,
        min_priority: Optional[float] = None,
        min_confidence: Optional[float] = None,
        min_anomaly: Optional[float] = None,
        signal_type: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Detection]:
        """Get detections with comprehensive filters"""
        query = db.query(Detection)
        
        # Join with Sample if filtering by dataset
        if dataset_id:
            query = query.join(Sample, Detection.sample_id == Sample.id).filter(
                Sample.dataset_id == dataset_id
            )
        
        # Apply filters
        if iteration:
            query = query.filter(Detection.iteration == iteration)
        
        if min_priority:
            query = query.filter(Detection.priority_score >= min_priority)
        
        if min_confidence:
            query = query.filter(Detection.confidence_score >= min_confidence)
        
        if min_anomaly:
            query = query.filter(Detection.anomaly_score >= min_anomaly)
        
        # Filter by dominant signal
        if signal_type == "confidence":
            query = query.filter(Detection.confidence_score > Detection.anomaly_score)
        elif signal_type == "anomaly":
            query = query.filter(Detection.anomaly_score > Detection.confidence_score)
        elif signal_type == "both":
            query = query.filter(
                Detection.confidence_score >= 0.7,
                Detection.anomaly_score >= 0.7
            )
        
        # Order by priority (highest first)
        query = query.order_by(Detection.priority_score.desc())
        
        return query.offset(offset).limit(limit).all()
    
    @staticmethod
    def get_detection_stats(db: Session, dataset_id: int) -> Dict[str, Any]:
        """Get detection statistics for a dataset"""
        total_samples = db.query(Sample).filter(
            Sample.dataset_id == dataset_id
        ).count()
        
        suspicious_samples = db.query(Sample).filter(
            Sample.dataset_id == dataset_id,
            Sample.is_suspicious == True
        ).count()
        
        total_detections = db.query(Detection).join(
            Sample, Detection.sample_id == Sample.id
        ).filter(
            Sample.dataset_id == dataset_id
        ).count()
        
        high_priority = db.query(Detection).join(
            Sample, Detection.sample_id == Sample.id
        ).filter(
            Sample.dataset_id == dataset_id,
            Detection.priority_score >= 0.8
        ).count()
        
        from sqlalchemy import func
        
        avg_confidence = db.query(
            func.avg(Detection.confidence_score)
        ).join(
            Sample, Detection.sample_id == Sample.id
        ).filter(
            Sample.dataset_id == dataset_id
        ).scalar() or 0
        
        return {
            "dataset_id": dataset_id,
            "total_samples": total_samples,
            "suspicious_samples": suspicious_samples,
            "total_detections": total_detections,
            "high_priority_detections": high_priority,
            "average_confidence": round(float(avg_confidence), 4),
            "detection_rate": round(
                (suspicious_samples / total_samples * 100) if total_samples > 0 else 0,
                2
            )
        }
    
    @staticmethod
    def get_signal_stats(db: Session, dataset_id: int) -> Dict[str, Any]:
        """Get signal-specific statistics"""
        detections = db.query(Detection).join(
            Sample, Detection.sample_id == Sample.id
        ).filter(
            Sample.dataset_id == dataset_id
        ).all()
        
        if not detections:
            return {
                "dataset_id": dataset_id,
                "total_detections": 0,
                "confidence_dominant": 0,
                "anomaly_dominant": 0,
                "both_high": 0,
                "avg_confidence": 0,
                "avg_anomaly": 0
            }
        
        confidence_dominant = sum(
            1 for d in detections if d.confidence_score > d.anomaly_score
        )
        anomaly_dominant = sum(
            1 for d in detections if d.anomaly_score > d.confidence_score
        )
        both_high = sum(
            1 for d in detections 
            if d.confidence_score >= 0.7 and d.anomaly_score >= 0.7
        )
        
        avg_confidence = sum(d.confidence_score for d in detections) / len(detections)
        avg_anomaly = sum(d.anomaly_score for d in detections) / len(detections)
        
        return {
            "dataset_id": dataset_id,
            "total_detections": len(detections),
            "confidence_dominant": confidence_dominant,
            "anomaly_dominant": anomaly_dominant,
            "both_high": both_high,
            "avg_confidence": round(avg_confidence, 4),
            "avg_anomaly": round(avg_anomaly, 4)
        }
    
    @staticmethod
    def get_detection_with_sample(db: Session, detection_id: int) -> Dict[str, Any]:
        """Get detection with associated sample details"""
        detection = db.query(Detection).filter(Detection.id == detection_id).first()
        
        if not detection:
            raise HTTPException(status_code=404, detail="Detection not found")
        
        sample = db.query(Sample).filter(Sample.id == detection.sample_id).first()
        
        if not sample:
            raise HTTPException(status_code=404, detail="Sample not found")
        
        # Parse signal breakdown if available
        signal_breakdown = None
        if detection.signal_breakdown:
            try:
                signal_breakdown = json.loads(detection.signal_breakdown)
            except:
                signal_breakdown = None
        
        # Parse priority weights if available
        priority_weights = None
        if detection.priority_weights:
            try:
                priority_weights = json.loads(detection.priority_weights)
            except:
                priority_weights = None
        
        return {
            "detection_id": detection.id,
            "sample_id": sample.id,
            "features": json.loads(sample.features),
            "current_label": sample.current_label,
            "predicted_label": detection.predicted_label,
            "original_label": sample.original_label,
            "confidence_score": detection.confidence_score,
            "anomaly_score": detection.anomaly_score,
            "priority_score": detection.priority_score,
            "iteration": detection.iteration,
            "detected_at": detection.detected_at.isoformat() if detection.detected_at else None,
            "signal_breakdown": signal_breakdown,
            "priority_weights": priority_weights
        }