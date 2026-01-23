"""
Quick Integration Test Script
Tests the full pipeline: DB → ML → Detection → Response
"""
import sys
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent.parent
sys.path.insert(0, str(backend_path))

from core.database import SessionLocal
from models.dataset import Sample
from services.ml_integration import get_ml_integration
import json
import numpy as np

def create_test_samples():
    """Create dummy samples for testing"""
    db = SessionLocal()
    
    # Check if samples exist
    existing = db.query(Sample).first