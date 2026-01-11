from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.session import Base

class ChatSessions(Base):
    __tablename__ = "chat_sessions"

    id = Column(String(36), primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    title = Column(String(255), nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())
    deleted_at = Column(DateTime, nullable=True)

    # Relationships
    user = relationship("User", back_populates="chat_sessions")
    chat_messages = relationship("ChatMessages", back_populates="chat_session")

class ChatMessages(Base):
    __tablename__ = "chat_messages"

    id = Column(String(36), primary_key=True, index=True)
    session_id = Column(String(36), ForeignKey("chat_sessions.id"), nullable=False)
    role = Column(String(50), nullable=False)  # e.g., 'user' or 'assistant' or 'system'
    content = Column(Text, nullable=False)
    sources = Column(Text, nullable=True) # To store the list of products or pharmacies metadata (RAG sources)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())
    deleted_at = Column(DateTime, nullable=True)

    # Relationships
    chat_session = relationship("ChatSessions", back_populates="chat_messages")
