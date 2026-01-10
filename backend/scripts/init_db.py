"""
Database initialization script
Loads sample Iris dataset and prepares database
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from sqlalchemy.orm import Session
from core.database import engine, SessionLocal, Base
from models.dataset import Dataset, Sample
import json
from datetime import datetime


def load_iris_dataset():
    """Load Iris dataset from sklearn"""
    from sklearn.datasets import load_iris
    import numpy as np
    
    print("Loading Iris dataset...")
    iris = load_iris()
    
    return {
        'data': iris.data,
        'target': iris.target,
        'feature_names': iris.feature_names,
        'target_names': iris.target_names.tolist(),
        'num_samples': len(iris.data),
        'num_features': iris.data.shape[1],
        'num_classes': len(iris.target_names)
    }


def inject_label_noise(labels, noise_percentage=15):
    """
    Inject label noise into dataset
    
    Args:
        labels: Original labels
        noise_percentage: Percentage of labels to flip (default 15%)
    
    Returns:
        noisy_labels, noise_indices
    """
    import numpy as np
    
    print(f"Injecting {noise_percentage}% label noise...")
    
    noisy_labels = labels.copy()
    num_samples = len(labels)
    num_noisy = int(num_samples * noise_percentage / 100)
    
    # Randomly select samples to corrupt
    noise_indices = np.random.choice(num_samples, num_noisy, replace=False)
    
    # Flip labels to random wrong class
    for idx in noise_indices:
        original_label = labels[idx]
        # Get all other classes
        other_classes = [c for c in range(3) if c != original_label]
        # Randomly pick one
        noisy_labels[idx] = np.random.choice(other_classes)
    
    print(f"Corrupted {len(noise_indices)} samples")
    return noisy_labels, noise_indices


def init_database(noise_percentage=15):
    """
    Initialize database with Iris dataset
    
    Args:
        noise_percentage: Percentage of labels to corrupt (default 15%)
    """
    db = SessionLocal()
    
    try:
        print("=" * 50)
        print("SLDCE - Database Initialization")
        print("=" * 50)
        
        # Load Iris dataset
        iris_data = load_iris_dataset()
        
        # Inject label noise
        noisy_labels, noise_indices = inject_label_noise(
            iris_data['target'], 
            noise_percentage
        )
        
        # Create dataset entry
        print("\nCreating dataset entry...")
        dataset = Dataset(
            name="Iris Dataset (15% Noise)",
            description=f"Classic Iris dataset with {noise_percentage}% injected label noise for testing SLDCE",
            file_path="sklearn.datasets.load_iris",
            num_samples=iris_data['num_samples'],
            num_features=iris_data['num_features'],
            num_classes=iris_data['num_classes']
        )
        db.add(dataset)
        db.commit()
        db.refresh(dataset)
        print(f"✓ Dataset created (ID: {dataset.id})")
        
        # Create sample entries
        print(f"\nInserting {iris_data['num_samples']} samples...")
        samples_created = 0
        
        for idx, (features, original_label, noisy_label) in enumerate(
            zip(iris_data['data'], iris_data['target'], noisy_labels)
        ):
            sample = Sample(
                dataset_id=dataset.id,
                sample_index=idx,
                features=json.dumps(features.tolist()),  # Store as JSON
                original_label=int(original_label),
                current_label=int(noisy_label),
                is_suspicious=False,
                is_corrected=False
            )
            db.add(sample)
            samples_created += 1
            
            # Commit in batches for performance
            if samples_created % 50 == 0:
                db.commit()
                print(f"  Inserted {samples_created}/{iris_data['num_samples']} samples...")
        
        db.commit()
        print(f"✓ All {samples_created} samples inserted")
        
        # Statistics
        print("\n" + "=" * 50)
        print("Database Initialization Complete!")
        print("=" * 50)
        print(f"Dataset: {dataset.name}")
        print(f"Total Samples: {iris_data['num_samples']}")
        print(f"Features: {iris_data['num_features']}")
        print(f"Classes: {iris_data['num_classes']}")
        print(f"Noisy Labels: {len(noise_indices)} ({noise_percentage}%)")
        print(f"Clean Labels: {iris_data['num_samples'] - len(noise_indices)} ({100 - noise_percentage}%)")
        print("\nTarget Classes:")
        for i, name in enumerate(iris_data['target_names']):
            print(f"  {i}: {name}")
        print("=" * 50)
        
        return dataset.id
        
    except Exception as e:
        print(f"\n❌ Error initializing database: {e}")
        db.rollback()
        raise
    finally:
        db.close()


def reset_database():
    """Drop all tables and recreate them"""
    print("⚠️  Dropping all tables...")
    Base.metadata.drop_all(bind=engine)
    print("✓ Tables dropped")
    
    print("Creating fresh tables...")
    Base.metadata.create_all(bind=engine)
    print("✓ Tables created")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Initialize SLDCE database")
    parser.add_argument(
        '--reset',
        action='store_true',
        help='Reset database (drop and recreate all tables)'
    )
    parser.add_argument(
        '--noise',
        type=int,
        default=15,
        help='Percentage of label noise to inject (default: 15)'
    )
    
    args = parser.parse_args()
    
    if args.reset:
        confirm = input("⚠️  This will DELETE all data. Continue? (yes/no): ")
        if confirm.lower() == 'yes':
            reset_database()
        else:
            print("Aborted.")
            sys.exit(0)
    
    init_database(noise_percentage=args.noise)