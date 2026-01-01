"""
Conversation State Management for Inbound Bot

Provides structured state management for customer support conversations.
"""

from dataclasses import dataclass, field
from typing import Optional, List, Dict
from datetime import datetime


@dataclass
class InboundConversationState:
    """
    Structured conversation state for inbound chatbot (customer support)
    
    Manages support conversation data with type safety and helper methods
    for tracking issues, ticket creation, and conversation flow.
    """
    
    # Issue tracking
    issue_summary: Optional[str] = None  # Brief summary of the issue
    issue_details: Optional[str] = None  # Detailed description
    issue_category: Optional[str] = None  # "equipment", "order", "billing", "quality", "general"
    
    # Ticket management
    create_ticket: bool = False  # Whether to create a ticket
    ticket_confirmation_pending: bool = False  # Waiting for user confirmation
    ticket_declined: bool = False  # User declined ticket creation
    ticket_mentioned: bool = False  # Already told customer about ticket creation
    conversation_closed: bool = False  # Conversation was closed (customer acknowledged)
    
    # Conversation flow
    conversation_type: Optional[str] = None  # "issue", "question", "general"
    questions_asked: int = 0  # Number of clarifying questions asked
    
    # Previous tickets (for context)
    has_previous_tickets: bool = False
    last_ticket_status: Optional[str] = None  # "open", "resolved", "in_progress"
    last_ticket_summary: Optional[str] = None
    
    # Metadata
    created_at: datetime = field(default_factory=datetime.now)
    
    def set_issue(self, summary: str, details: str) -> None:
        """Set or append issue information"""
        if self.issue_summary and self.issue_details:
            # Already have an issue - append the new one
            self.issue_summary = f"{self.issue_summary}; {summary}"
            self.issue_details = f"{self.issue_details}\n\nAdditional issue: {details}"
        else:
            # First issue
            self.issue_summary = summary
            self.issue_details = details
        self.conversation_type = "issue"
    
    def mark_ticket_pending(self) -> None:
        """Mark that we're waiting for ticket confirmation"""
        self.ticket_confirmation_pending = True
    
    def confirm_ticket(self) -> None:
        """User confirmed they want a ticket"""
        self.create_ticket = True
        self.ticket_confirmation_pending = False
        self.ticket_declined = False
    
    def add_additional_issue(self, summary: str, details: str) -> None:
        """Add another issue even after ticket is confirmed"""
        if self.issue_summary and self.issue_details:
            self.issue_summary = f"{self.issue_summary}; {summary}"
            self.issue_details = f"{self.issue_details}\n\nAdditional issue (mentioned later): {details}"
        else:
            self.set_issue(summary, details)
    
    def decline_ticket(self) -> None:
        """User declined ticket creation"""
        self.create_ticket = False
        self.ticket_confirmation_pending = False
        self.ticket_declined = True
    
    def increment_questions(self) -> int:
        """Increment question count and return new count"""
        self.questions_asked += 1
        return self.questions_asked
    
    def has_issue_details(self) -> bool:
        """Check if we have enough issue information"""
        return bool(self.issue_summary and self.issue_details)
    
    def is_ready_for_ticket(self) -> bool:
        """Check if ready to ask about ticket creation"""
        return self.has_issue_details() and not self.ticket_confirmation_pending and not self.create_ticket and not self.ticket_declined
    
    def set_previous_ticket(self, status: str, summary: str) -> None:
        """Set information about user's previous ticket"""
        self.has_previous_tickets = True
        self.last_ticket_status = status
        self.last_ticket_summary = summary
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for storage/API responses"""
        return {
            # Issue tracking
            "issue_summary": self.issue_summary,
            "issue_details": self.issue_details,
            "issue_category": self.issue_category,
            # Ticket management
            "create_ticket": self.create_ticket,
            "ticket_confirmation_pending": self.ticket_confirmation_pending,
            "ticket_declined": self.ticket_declined,
            "ticket_mentioned": self.ticket_mentioned,
            "conversation_closed": self.conversation_closed,
            # Conversation flow
            "conversation_type": self.conversation_type,
            "questions_asked": self.questions_asked,
            # Previous tickets
            "has_previous_tickets": self.has_previous_tickets,
            "last_ticket_status": self.last_ticket_status,
            "last_ticket_summary": self.last_ticket_summary,
            # Metadata
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'InboundConversationState':
        """Create InboundConversationState from dictionary"""
        # Extract datetime if present
        created_at = data.get("created_at")
        if created_at and isinstance(created_at, str):
            created_at = datetime.fromisoformat(created_at)
        
        return cls(
            # Issue tracking
            issue_summary=data.get("issue_summary"),
            issue_details=data.get("issue_details"),
            issue_category=data.get("issue_category"),
            # Ticket management
            create_ticket=data.get("create_ticket", False),
            ticket_confirmation_pending=data.get("ticket_confirmation_pending", False),
            ticket_declined=data.get("ticket_declined", False),
            ticket_mentioned=data.get("ticket_mentioned", False),
            conversation_closed=data.get("conversation_closed", False),
            # Conversation flow
            conversation_type=data.get("conversation_type"),
            questions_asked=data.get("questions_asked", 0),
            # Previous tickets
            has_previous_tickets=data.get("has_previous_tickets", False),
            last_ticket_status=data.get("last_ticket_status"),
            last_ticket_summary=data.get("last_ticket_summary"),
            # Metadata
            created_at=created_at or datetime.now(),
        )
    
    def __repr__(self) -> str:
        """String representation for debugging"""
        if self.issue_summary:
            ticket_status = "✓ ticket" if self.create_ticket else "⏳ pending" if self.ticket_confirmation_pending else "✗ no ticket"
            return f"<InboundState: {self.issue_summary[:30]}... ({ticket_status})>"
        return f"<InboundState: {self.conversation_type or 'new'}>"
