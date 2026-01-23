"""
Confidence and Anomaly detection extracted from Notebooks 03 & 04
FIXED: Handle both numpy arrays and pandas Series
"""
import pandas as pd
import numpy as np
from typing import Tuple, List, Dict, Any
from sklearn.ensemble import IsolationForest


def detect_confidence_issues(
    model: Any,
    X_test: np.ndarray,
    y_test: np.ndarray,
    confidence_threshold: float = 0.7
) -> pd.DataFrame:
    """
    Detect samples with confidence issues (from Notebook 03)
    
    Args:
        model: Trained model with predict_proba method
        X_test: Test features (numpy array)
        y_test: Test labels (numpy array or pandas Series)
        confidence_threshold: Threshold for flagging low confidence
        
    Returns:
        DataFrame with confidence analysis
    """
    # Convert y_test to numpy array if it's a Series
    if hasattr(y_test, 'values'):
        y_test = y_test.values
    
    # Get predictions and probabilities
    y_pred = model.predict(X_test)
    y_proba = model.predict_proba(X_test)
    
    # Get class labels from model
    class_labels = list(model.model.classes_)
    
    # Calculate confidences
    given_label_confidence = []
    predicted_label_confidence = []
    
    for i, true_label in enumerate(y_test):
        # Find index of true label in class_labels
        try:
            true_label_index = class_labels.index(true_label)
            # Confidence in given label
            given_label_confidence.append(y_proba[i][true_label_index])
        except ValueError:
            # If label not in training classes, use 0 confidence
            given_label_confidence.append(0.0)
        
        # Confidence in predicted label (max probability)
        predicted_label_confidence.append(y_proba[i].max())
    
    # Create results DataFrame
    results = pd.DataFrame({
        'predicted_label': y_pred,
        'given_label_confidence': given_label_confidence,
        'predicted_label_confidence': predicted_label_confidence,
    })
    
    # Flag suspicious samples
    # FIXED: Compare directly with y_test (already numpy array)
    results['confidence_flag'] = (
        (results['predicted_label'] != y_test) &
        (results['given_label_confidence'] < confidence_threshold)
    )
    
    return results


def detect_anomalies(
    X: np.ndarray,
    contamination: float = 0.1
) -> pd.DataFrame:
    """
    Detect anomalies using Isolation Forest (from Notebook 04)
    
    Args:
        X: Feature matrix (numpy array)
        contamination: Expected proportion of anomalies
        
    Returns:
        DataFrame with anomaly scores and flags
    """
    # Train Isolation Forest
    iso_forest = IsolationForest(
        n_estimators=200,
        contamination=contamination,
        random_state=42
    )
    
    iso_forest.fit(X)
    
    # Get anomaly scores
    # decision_function: higher = more normal
    raw_scores = iso_forest.decision_function(X)
    
    # Convert to anomaly score: higher = more anomalous
    anomaly_scores = -raw_scores
    
    # Normalize to [0, 1] range for consistency
    min_score = anomaly_scores.min()
    max_score = anomaly_scores.max()
    if max_score - min_score > 0:
        anomaly_scores = (anomaly_scores - min_score) / (max_score - min_score)
    
    # Predict outliers (-1 = anomaly, 1 = normal)
    anomaly_flags = iso_forest.predict(X) == -1
    
    # Create results
    results = pd.DataFrame({
        'anomaly_score': anomaly_scores,
        'anomaly_flag': anomaly_flags
    })
    
    return results


def combine_signals(
    confidence_df: pd.DataFrame,
    anomaly_df: pd.DataFrame,
    confidence_weight: float = 0.6,
    anomaly_weight: float = 0.4
) -> pd.DataFrame:
    """
    Combine confidence and anomaly signals (from Notebook 05)
    
    Args:
        confidence_df: Results from confidence detection
        anomaly_df: Results from anomaly detection
        confidence_weight: Weight for confidence signal
        anomaly_weight: Weight for anomaly signal
        
    Returns:
        DataFrame with combined risk scores
    """
    # Validate weights sum to 1
    assert abs((confidence_weight + anomaly_weight) - 1.0) < 0.001, \
        "Weights must sum to 1.0"
    
    # Create combined dataframe
    combined = confidence_df.copy()
    
    # Normalize confidence risk (use predicted_label_confidence as risk)
    # Higher confidence in wrong prediction = higher risk
    combined['confidence_risk'] = combined['confidence_flag'].astype(float)
    
    # For samples where confidence disagrees, use the confidence score as risk
    mask = combined['confidence_flag']
    combined.loc[mask, 'confidence_risk'] = combined.loc[mask, 'predicted_label_confidence']
    
    # Anomaly risk already normalized in detect_anomalies
    combined['anomaly_risk'] = anomaly_df['anomaly_score'].values
    
    # Weighted fusion
    combined['combined_risk_score'] = (
        confidence_weight * combined['confidence_risk'] +
        anomaly_weight * combined['anomaly_risk']
    )
    
    return combined


def generate_suggestions(
    combined_df: pd.DataFrame,
    reject_threshold: float = 0.8,
    review_threshold: float = 0.4
) -> pd.DataFrame:
    """
    Generate suggestions based on risk scores (from Notebook 06)
    
    Args:
        combined_df: DataFrame with combined risk scores
        reject_threshold: Threshold for REJECT decision
        review_threshold: Threshold for REVIEW decision
        
    Returns:
        DataFrame with suggestions and explanations
    """
    def make_suggestion(risk):
        if risk >= reject_threshold:
            return "REJECT"
        elif risk >= review_threshold:
            return "REVIEW"
        else:
            return "KEEP"
    
    def explain_decision(row):
        reasons = []
        
        if row.get('confidence_flag', False):
            conf_pct = row.get('predicted_label_confidence', 0) * 100
            reasons.append(f"Model confident ({conf_pct:.1f}%) in different label")
        
        if row.get('anomaly_risk', 0) >= 0.5:
            anom_pct = row.get('anomaly_risk', 0) * 100
            reasons.append(f"Anomalous features detected ({anom_pct:.1f}%)")
        
        if not reasons:
            reasons.append("Low risk signals")
        
        return "; ".join(reasons)
    
    # Add suggestions
    combined_df = combined_df.copy()
    combined_df['suggestion'] = combined_df['combined_risk_score'].apply(make_suggestion)
    combined_df['decision_reason'] = combined_df.apply(explain_decision, axis=1)
    
    return combined_df