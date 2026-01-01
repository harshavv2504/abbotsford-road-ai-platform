"""
Detection Module

Modularized detection with:
- Flow state detection (flow_detector.py)
- Customer type detection (type_detector.py)
"""

from app.services.outbound.detection.flow_detector import FlowDetector, flow_detector
from app.services.outbound.detection.type_detector import TypeDetector, type_detector

__all__ = [
    'FlowDetector',
    'TypeDetector',
    'flow_detector',
    'type_detector',
]
