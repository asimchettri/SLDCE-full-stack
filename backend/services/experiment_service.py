"""
Experiment service - Business logic for experiment tracking
"""
from sqlalchemy.orm import Session
from models.experiment import Experiment, ExperimentIteration
from fastapi import HTTPException
from typing import List, Dict, Any
from datetime import datetime


class ExperimentService:
    """Service class for experiment operations"""
    
    @staticmethod
    def get_all_experiments(db: Session, dataset_id: int = None, skip: int = 0, limit: int = 100) -> List[Experiment]:
        """Get all experiments, optionally filtered by dataset"""
        query = db.query(Experiment)
        
        if dataset_id:
            query = query.filter(Experiment.dataset_id == dataset_id)
        
        return query.order_by(Experiment.created_at.desc()).offset(skip).limit(limit).all()
    
    @staticmethod
    def get_experiment_by_id(db: Session, experiment_id: int) -> Experiment:
        """Get experiment by ID"""
        experiment = db.query(Experiment).filter(Experiment.id == experiment_id).first()
        
        if not experiment:
            raise HTTPException(status_code=404, detail="Experiment not found")
        
        return experiment
    
    @staticmethod
    def create_experiment(
        db: Session,
        dataset_id: int,
        name: str,
        noise_percentage: float,
        description: str = None,
        detection_threshold: float = 0.7,
        max_iterations: int = 10
    ) -> Experiment:
        """Create a new experiment"""
        # Check if experiment with same name exists
        existing = db.query(Experiment).filter(
            Experiment.dataset_id == dataset_id,
            Experiment.name == name
        ).first()
        
        if existing:
            raise HTTPException(
                status_code=400,
                detail=f"Experiment with name '{name}' already exists for this dataset"
            )
        
        experiment = Experiment(
            dataset_id=dataset_id,
            name=name,
            description=description,
            noise_percentage=noise_percentage,
            detection_threshold=detection_threshold,
            max_iterations=max_iterations,
            status='running'
        )
        
        db.add(experiment)
        db.commit()
        db.refresh(experiment)
        
        return experiment
    
    @staticmethod
    def add_iteration(
        db: Session,
        experiment_id: int,
        iteration_number: int,
        accuracy: float,
        precision: float = None,
        recall: float = None,
        f1_score: float = None,
        samples_flagged: int = 0,
        samples_corrected: int = 0,
        correction_acceptance_rate: float = None,
        remaining_noise_percentage: float = None,
        samples_reviewed: int = 0,
        iteration_time_seconds: float = None
    ) -> ExperimentIteration:
        """Add a new iteration to an experiment"""
        experiment = ExperimentService.get_experiment_by_id(db, experiment_id)
        
        # Create iteration record
        iteration = ExperimentIteration(
            experiment_id=experiment_id,
            iteration_number=iteration_number,
            accuracy=accuracy,
            precision=precision,
            recall=recall,
            f1_score=f1_score,
            samples_flagged=samples_flagged,
            samples_corrected=samples_corrected,
            correction_acceptance_rate=correction_acceptance_rate,
            remaining_noise_percentage=remaining_noise_percentage,
            samples_reviewed=samples_reviewed,
            iteration_time_seconds=iteration_time_seconds
        )
        
        db.add(iteration)
        
        # Update experiment state
        experiment.current_iteration = iteration_number
        experiment.total_corrections += samples_corrected
        
        # Set baseline on first iteration
        if iteration_number == 1 and experiment.baseline_accuracy is None:
            experiment.baseline_accuracy = accuracy
        
        # Update final accuracy
        experiment.final_accuracy = accuracy
        
        db.commit()
        db.refresh(iteration)
        
        return iteration
    
    @staticmethod
    def get_experiment_iterations(db: Session, experiment_id: int) -> List[ExperimentIteration]:
        """Get all iterations for an experiment"""
        return db.query(ExperimentIteration).filter(
            ExperimentIteration.experiment_id == experiment_id
        ).order_by(ExperimentIteration.iteration_number).all()
    
    @staticmethod
    def complete_experiment(
        db: Session,
        experiment_id: int,
        total_time_seconds: float = None
    ) -> Experiment:
        """Mark an experiment as completed"""
        experiment = ExperimentService.get_experiment_by_id(db, experiment_id)
        
        experiment.status = 'completed'
        experiment.completed_at = datetime.utcnow()
        
        if total_time_seconds:
            experiment.total_time_seconds = total_time_seconds
        
        db.commit()
        db.refresh(experiment)
        
        return experiment
    
    @staticmethod
    def get_experiment_summary(db: Session, experiment_id: int) -> Dict[str, Any]:
        """Get comprehensive summary of an experiment"""
        experiment = ExperimentService.get_experiment_by_id(db, experiment_id)
        iterations = ExperimentService.get_experiment_iterations(db, experiment_id)
        
        if not iterations:
            return {
                "experiment_id": experiment_id,
                "name": experiment.name,
                "status": experiment.status,
                "total_iterations": 0,
                "accuracy_improvement": 0,
                "noise_reduction": 0,
                "total_corrections": 0,
                "avg_time_per_iteration": 0
            }
        
        # Calculate metrics
        baseline_accuracy = experiment.baseline_accuracy or iterations[0].accuracy
        final_accuracy = experiment.final_accuracy or iterations[-1].accuracy
        accuracy_improvement = final_accuracy - baseline_accuracy
        
        initial_noise = experiment.noise_percentage
        final_noise = iterations[-1].remaining_noise_percentage or 0
        noise_reduction = initial_noise - final_noise
        
        avg_time = sum(i.iteration_time_seconds or 0 for i in iterations) / len(iterations)
        
        return {
            "experiment_id": experiment_id,
            "name": experiment.name,
            "status": experiment.status,
            "total_iterations": len(iterations),
            "accuracy_improvement": round(accuracy_improvement * 100, 2),
            "noise_reduction": round(noise_reduction, 2),
            "total_corrections": experiment.total_corrections,
            "avg_time_per_iteration": round(avg_time, 2)
        }