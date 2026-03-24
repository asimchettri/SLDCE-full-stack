"""
Detection service - Business logic for error detection
UPDATED: Auto-creates model entry in database when running detection
"""
from sqlalchemy.orm import Session
from models.dataset import Sample, Detection
from models.model import MLModel 
from fastapi import HTTPException
from typing import List, Dict, Any, Optional, Tuple
import json
from datetime import datetime,timezone
import logging
import numpy as np  
from services.engine_registry import get_engine_registry
from sqlalchemy import func as sa_func

# ml_integration imported inside run_detection to avoid circular imports

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

        # Step 1: Get samples
        samples_query = db.query(Sample).filter(Sample.dataset_id == dataset_id)

        if max_samples:
            samples_query = samples_query.limit(max_samples)

        samples = samples_query.all()

        if not samples:
            raise HTTPException(
                status_code=400,
                detail=f"Dataset {dataset_id} has no samples. Upload data before running detection."
            )

     
            # Step 2: Determine next iteration number dynamically
       
        latest_iteration = db.query(sa_func.max(Detection.iteration)).join(
            Sample, Detection.sample_id == Sample.id
        ).filter(
            Sample.dataset_id == dataset_id
        ).scalar()
        iteration = (latest_iteration or 0) + 1
        model_id = None                                 

        # Step 3: NOW safe to use iteration in the duplicate check
        existing_detections = db.query(Detection).join(
            Sample, Detection.sample_id == Sample.id
        ).filter(
            Sample.dataset_id == dataset_id,
            Detection.iteration == iteration
        ).count()

        if existing_detections > 0:
            raise HTTPException(
                status_code=400,
                detail=(
                    f"Detection already run for dataset {dataset_id}, iteration {iteration}. "
                    f"Found {existing_detections} existing detections. "
                    f"To re-run, delete existing detections first."
                )
            )

        logger.info(f"Running detection on {len(samples)} samples from dataset {dataset_id}")

        detections_created = 0

        if use_ml:
            try:
                from services.ml_integration import fit_dataset, detect_noise

                fit_result = fit_dataset(db, dataset_id)
                logger.info(
                    f"Engine fitted: {fit_result['samples_fitted']} samples, "
                    f"classes={fit_result['classes']}"
                )

                db_model = DetectionService._create_or_get_model(
                    db,
                    dataset_id=dataset_id,
                    model_name="self_learning_engine",
                    model_params={
                        "contamination": 0.1,
                        "initial_threshold": 0.5,
                        "n_estimators": 100,
                    },
                    is_baseline=True
                )
                model_id = db_model.id

                detection_result = detect_noise(db, dataset_id)
                flagged_samples = detection_result["flagged_samples"]

                logger.info(
                    f"Detection complete: {len(flagged_samples)} flagged, "
                    f"threshold={detection_result['current_threshold']:.3f}"
                )

                for flagged in flagged_samples:
                    sample = next(
                        (s for s in samples if s.id == flagged["sample_id"]),
                        None
                    )

                    if not sample:
                        logger.warning(f"Sample {flagged['sample_id']} not found")
                        continue

                    noise_prob = flagged["noise_probability"]

                    registry = get_engine_registry()  # add this import at top of file
                    engine_instance = registry.get(dataset_id)
           
                    # Get position of this sample in the engine's original index
                    sample_pos = None
                    if engine_instance and engine_instance._last_signals:
                        try:
                            sample_pos = list(engine_instance._X_original.index).index(flagged["sample_id"])
                        except ValueError:
                            sample_pos = None

                    if sample_pos is not None and engine_instance._last_signals:
                        sig = engine_instance._last_signals[sample_pos]
                        # confidence signal: how much the model disagrees (1 - margin)
                        confidence_score = float(np.clip(1.0 - sig.get("margin", 0.5), 0.0, 1.0))
                        # anomaly signal: average of isolation + lof scores, normalized
                        raw_anomaly = (sig.get("isolation_score", 0.0) + sig.get("lof_score", 0.0)) / 2.0
                        anomaly_score = float(np.clip(raw_anomaly, 0.0, 1.0))
                    else:
                        # Fallback if signals not available
                        confidence_score = float(np.clip(noise_prob, 0.0, 1.0))
                        anomaly_score = float(np.clip(noise_prob, 0.0, 1.0))

                    conf_w = (priority_weights or {}).get("confidence", 0.6)
                    anom_w = (priority_weights or {}).get("anomaly", 0.4)
                    weighted = confidence_score * conf_w + anomaly_score * anom_w
                    agreement_bonus = confidence_score * anomaly_score * 0.2
                    priority_score = float(np.clip(weighted + agreement_bonus, 0.0, 1.0))

                    dominant = "confidence" if confidence_score >= anomaly_score else "anomaly"
                    if confidence_score >= 0.7 and anomaly_score >= 0.7:
                        dominant = "both"

                    signal_breakdown = {
                        "noise_probability": round(noise_prob, 4),
                        "confidence_score": round(confidence_score, 4),
                        "anomaly_score": round(anomaly_score, 4),
                        "predicted_label": flagged["predicted_label"],
                        "threshold": round(detection_result["current_threshold"], 4),
                        "dominant_signal": dominant,
                        "label_mismatch": (
                            int(flagged["predicted_label"]) != int(sample.current_label)
                        ),
                        "agreement_bonus": round(agreement_bonus, 4),
                        "priority_breakdown": {
                            "weighted": round(weighted, 4),
                            "bonus": round(agreement_bonus, 4),
                            "final": round(priority_score, 4),
                        }
                    }

                    detection = Detection(
                        sample_id=sample.id,
                        iteration=iteration,
                        confidence_score=confidence_score,
                        anomaly_score=anomaly_score,
                        predicted_label=int(flagged["predicted_label"]),
                        priority_score=priority_score,
                        signal_breakdown=json.dumps(signal_breakdown),
                        priority_weights=json.dumps(priority_weights) if priority_weights else None
                    )

                    db.add(detection)
                    sample.is_suspicious = True
                    detections_created += 1

                db_model.num_samples_trained = len(samples)
                db.commit()

                logger.info(f"Created {detections_created} detection records")

            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"Engine detection failed: {e}", exc_info=True)
                raise HTTPException(
                    status_code=500,
                    detail=f"Detection failed: {str(e)}"
                )

        else:
            logger.warning("Using simulation mode - not recommended for production")

            for sample in samples:
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

        db.commit()

        total_samples = len(samples)
        detection_rate = (detections_created / total_samples * 100) if total_samples > 0 else 0

        return {
            "dataset_id": dataset_id,
            "model_id": model_id,
            "iteration": iteration,
            "total_samples_analyzed": total_samples,
            "suspicious_samples_found": detections_created,
            "detection_rate": round(detection_rate, 2),
            "confidence_threshold": confidence_threshold,
            "ml_pipeline_used": use_ml,
            "priority_weights": priority_weights,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    
    @staticmethod
    def calculate_priority_score(
        confidence: float,
        anomaly: float,
        weights: Optional[Dict[str, float]] = None
    ) -> float:
        """
        Meaningful priority: weighted sum + agreement bonus.
        High confidence + high anomaly → higher than either alone.
        """
        if weights is None:
            weights = {"confidence": 0.6, "anomaly": 0.4}

        weighted = (
            confidence * weights.get("confidence", 0.6) +
            anomaly * weights.get("anomaly", 0.4)
        )
        # Agreement bonus: both signals high = more certain it's mislabeled
        agreement_bonus = confidence * anomaly * 0.2
        return float(min(max(weighted + agreement_bonus, 0.0), 1.0))
    
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
    
