"""
Re-export IntentClassifier under agents directory for seamless modular access.
"""

from ml_pipeline.classifier.intent_classifier import IntentClassifier
from ml_pipeline.schemas.intent_schema import Intent, Route, Entities, IntentResult

__all__ = ["IntentClassifier", "Intent", "Route", "Entities", "IntentResult"]
