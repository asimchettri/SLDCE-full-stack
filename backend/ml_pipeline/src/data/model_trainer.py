"""
Model training utilities extracted from Notebook 02
"""
from abc import ABC, abstractmethod
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.svm import SVC
import numpy as np


class BaseModel(ABC):
    """Base class for all models - ensures consistent interface"""
    
    def __init__(self, **params):
        self.params = params
        self.model = None

    @abstractmethod
    def train(self, X, y):
        """Train the model"""
        pass

    @abstractmethod
    def predict(self, X):
        """Make predictions"""
        pass

    @abstractmethod
    def predict_proba(self, X):
        """Get prediction probabilities"""
        pass


class RandomForestModel(BaseModel):
    """Random Forest classifier wrapper"""
    
    def __init__(self, **params):
        super().__init__(**params)
        self.model = RandomForestClassifier(**params)

    def train(self, X, y):
        self.model.fit(X, y)

    def predict(self, X):
        return self.model.predict(X)

    def predict_proba(self, X):
        return self.model.predict_proba(X)


class LogisticModel(BaseModel):
    """Logistic Regression wrapper"""
    
    def __init__(self, **params):
        super().__init__(**params)
        self.model = LogisticRegression(max_iter=1000, **params)

    def train(self, X, y):
        self.model.fit(X, y)

    def predict(self, X):
        return self.model.predict(X)

    def predict_proba(self, X):
        return self.model.predict_proba(X)


class SVMModel(BaseModel):
    """SVM classifier wrapper"""
    
    def __init__(self, **params):
        super().__init__(**params)
        self.model = SVC(probability=True, **params)

    def train(self, X, y):
        self.model.fit(X, y)

    def predict(self, X):
        return self.model.predict(X)

    def predict_proba(self, X):
        return self.model.predict_proba(X)


def get_model(model_name: str, params: dict) -> BaseModel:
    """
    Factory function to create models
    
    Args:
        model_name: Name of model ("random_forest", "logistic", "svm")
        params: Model parameters
        
    Returns:
        Initialized model instance
    """
    if model_name == "random_forest":
        return RandomForestModel(**params)
    elif model_name == "logistic":
        return LogisticModel(**params)
    elif model_name == "svm":
        return SVMModel(**params)
    else:
        raise ValueError(f"Unsupported model: {model_name}")