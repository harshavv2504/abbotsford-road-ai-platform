"""
RAG Module

Modularized RAG handling with:
- Question detection (question_detector.py)
- Question rules (question_rules.py)
- Answer handling (answer_handler.py)
- Context building (context_builder.py)
"""

from app.services.outbound.rag.question_detector import QuestionDetector, question_detector
from app.services.outbound.rag.question_rules import QuestionRules, question_rules
from app.services.outbound.rag.answer_handler import AnswerHandler, answer_handler
from app.services.outbound.rag.context_builder import ContextBuilder, context_builder

__all__ = [
    'QuestionDetector',
    'QuestionRules',
    'AnswerHandler',
    'ContextBuilder',
    'question_detector',
    'question_rules',
    'answer_handler',
    'context_builder',
]
