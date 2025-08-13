"""Agent interaction models with rolling partitions."""

from datetime import datetime
from sqlalchemy import Column, String, Text, DateTime, JSON, Integer, Boolean, Index
from sqlalchemy.sql import func
from database import Base
import ulid


class AgentInteraction(Base):
    """Agent interaction logs with rolling partitions."""
    __tablename__ = "agent_interactions"
    
    id = Column(String(26), primary_key=True, default=lambda: ulid.new().str)
    org_id = Column(String(26), nullable=False, index=True)
    session_id = Column(String(64), nullable=False, index=True)
    user_message = Column(Text, nullable=False)
    agent_response = Column(Text, nullable=True)
    query_type = Column(String(50), nullable=True)
    metadata = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Indexes for performance
    __table_args__ = (
        Index('ix_agent_interactions_org_created', 'org_id', 'created_at'),
        Index('ix_agent_interactions_session_created', 'session_id', 'created_at'),
        Index('ix_agent_interactions_query_type', 'query_type'),
    )


class VectorEmbedding(Base):
    """Vector embeddings for semantic search with rolling partitions."""
    __tablename__ = "vector_embeddings"
    
    id = Column(String(26), primary_key=True, default=lambda: ulid.new().str)
    org_id = Column(String(26), nullable=False, index=True)
    content_id = Column(String(26), nullable=False, index=True)
    content_text = Column(Text, nullable=False)
    # Note: pgvector extension will be added via migration
    # embedding = Column(Vector(1536), nullable=False)  # text-embedding-3-small
    embedding_model = Column(String(100), default="text-embedding-3-small", nullable=False)
    metadata = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    __table_args__ = (
        Index('ix_vector_embeddings_org_content', 'org_id', 'content_id'),
        Index('ix_vector_embeddings_model', 'embedding_model'),
    )


class PropertyListing(Base):
    """Property listings with rolling partitions."""
    __tablename__ = "property_listings"
    
    id = Column(String(26), primary_key=True, default=lambda: ulid.new().str)
    org_id = Column(String(26), nullable=False, index=True)
    external_id = Column(String(100), nullable=True, index=True)  # Domain/REA ID
    address = Column(Text, nullable=False)
    suburb = Column(String(100), nullable=False, index=True)
    state = Column(String(10), nullable=False)
    postcode = Column(String(10), nullable=False, index=True)
    property_type = Column(String(50), nullable=True)
    bedrooms = Column(Integer, nullable=True)
    bathrooms = Column(Integer, nullable=True)
    car_spaces = Column(Integer, nullable=True)
    price = Column(String(100), nullable=True)
    description = Column(Text, nullable=True)
    features = Column(JSON, nullable=True)
    source_url = Column(Text, nullable=True)
    scraped_at = Column(DateTime(timezone=True), server_default=func.now())
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    __table_args__ = (
        Index('ix_property_listings_org_suburb', 'org_id', 'suburb'),
        Index('ix_property_listings_postcode', 'postcode'),
        Index('ix_property_listings_active', 'is_active'),
        Index('ix_property_listings_external', 'external_id'),
    )


class ApiUsage(Base):
    """API usage tracking with rolling partitions."""
    __tablename__ = "api_usage"
    
    id = Column(String(26), primary_key=True, default=lambda: ulid.new().str)
    org_id = Column(String(26), nullable=False, index=True)
    endpoint = Column(String(200), nullable=False)
    method = Column(String(10), nullable=False)
    status_code = Column(Integer, nullable=False)
    response_time_ms = Column(Integer, nullable=True)
    tokens_used = Column(Integer, nullable=True)
    model_used = Column(String(100), nullable=True)
    user_agent = Column(Text, nullable=True)
    ip_address = Column(String(45), nullable=True)  # IPv6 support
    metadata = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    __table_args__ = (
        Index('ix_api_usage_org_endpoint', 'org_id', 'endpoint'),
        Index('ix_api_usage_status', 'status_code'),
        Index('ix_api_usage_created', 'created_at'),
    )