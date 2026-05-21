from sqlalchemy import Column, Integer, String, BigInteger, Float, Boolean, ForeignKey, Table, Date, DateTime, Text, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .database import Base

# Association table for Post and Narrative mapping
post_narrative_mapping = Table(
    'post_narrative_mapping',
    Base.metadata,
    Column('post_id', Integer, ForeignKey('posts.id', ondelete='CASCADE'), primary_key=True),
    Column('narrative_id', Integer, ForeignKey('narratives.id', ondelete='CASCADE'), primary_key=True),
    Column('confidence_score', Float)
)

class Movement(Base):
    __tablename__ = 'movements'
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), unique=True, nullable=False)
    tagline = Column(String(255))
    slug = Column(String(100), unique=True, nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    metrics = relationship("MetricsTracker", back_populates="movement", cascade="all, delete-orphan")
    sources = relationship("Source", back_populates="movement", cascade="all, delete-orphan")
    posts = relationship("Post", back_populates="movement", cascade="all, delete-orphan")
    narratives = relationship("Narrative", back_populates="movement", cascade="all, delete-orphan")
    memes = relationship("Meme", back_populates="movement", cascade="all, delete-orphan")
    summaries = relationship("Summary", back_populates="movement", cascade="all, delete-orphan")
    timeline_events = relationship("TimelineEvent", back_populates="movement", cascade="all, delete-orphan")
    platform_events = relationship("PlatformEvent", back_populates="movement", cascade="all, delete-orphan")


class MetricsTracker(Base):
    __tablename__ = 'metrics_tracker'
    
    id = Column(Integer, primary_key=True, index=True)
    movement_id = Column(Integer, ForeignKey('movements.id', ondelete='CASCADE'))
    platform = Column(String(50), nullable=False)
    follower_count = Column(BigInteger)
    mentions_per_minute = Column(Integer)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())

    movement = relationship("Movement", back_populates="metrics")


class Source(Base):
    __tablename__ = 'sources'
    
    id = Column(Integer, primary_key=True, index=True)
    movement_id = Column(Integer, ForeignKey('movements.id', ondelete='CASCADE'))
    name = Column(String(255), nullable=False)
    platform = Column(String(50), nullable=False)
    url = Column(Text, unique=True)
    source_reputation_score = Column(Integer, default=50)
    verification_status = Column(String(50), default='unverified')
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    movement = relationship("Movement", back_populates="sources")
    posts = relationship("Post", back_populates="source")


class Post(Base):
    __tablename__ = 'posts'
    
    id = Column(Integer, primary_key=True, index=True)
    movement_id = Column(Integer, ForeignKey('movements.id', ondelete='CASCADE'), index=True)
    source_id = Column(Integer, ForeignKey('sources.id', ondelete='SET NULL'), nullable=True)
    source_platform = Column(String(50), nullable=False, index=True)
    external_id = Column(String(255), nullable=False)
    title = Column(String(500))
    content = Column(Text)
    author = Column(String(255))
    post_url = Column(Text, nullable=False)
    published_at = Column(DateTime(timezone=True))
    
    # Ingestion & Verification Metadata
    ingested_at = Column(DateTime(timezone=True), server_default=func.now())
    collector_version = Column(String(20), default='1.0.0')
    scrape_status = Column(String(50), default='success')
    
    # Multilingual Parameters
    language_code = Column(String(10), default='en')
    translated_content = Column(Text)
    
    # Content & Trust Layers
    content_type = Column(String(50), index=True)
    credibility_score = Column(Float, default=0.5)
    bot_probability = Column(Float, default=0.0)
    verification_status = Column(String(50))
    
    # AI Curation Labels
    sentiment = Column(String(50))
    primary_theme = Column(String(100))
    
    # Immutable raw snapshot payload
    raw_payload_json = Column(JSON)
    
    is_duplicate = Column(Boolean, default=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    movement = relationship("Movement", back_populates="posts")
    source = relationship("Source", back_populates="posts")
    
    # Relationships
    embedding_relation = relationship("PostEmbedding", back_populates="post", uselist=False, cascade="all, delete-orphan")
    entity_mentions = relationship("EntityMention", back_populates="post", cascade="all, delete-orphan")
    narratives = relationship("Narrative", secondary=post_narrative_mapping, back_populates="posts")
    evidence_links = relationship("NarrativeEvidence", back_populates="post", cascade="all, delete-orphan")


class PostEmbedding(Base):
    __tablename__ = 'post_embeddings'
    
    post_id = Column(Integer, ForeignKey('posts.id', ondelete='CASCADE'), primary_key=True)
    # The actual vector(1536) embedding column. Declarative SQLAlchemy type handles it as Text/custom.
    # We will declare it as standard type for model clarity.
    # Raw SQL handles pgvector inserts correctly.
    embedding = Column(Text, nullable=False)  # Stored as string format for ORM, converted via pgvector SQL functions
    embedding_model_version = Column(String(50), default='models/text-embedding-004')

    post = relationship("Post", back_populates="embedding_relation")


class Entity(Base):
    __tablename__ = 'entities'
    
    id = Column(Integer, primary_key=True, index=True)
    entity_type = Column(String(50))
    name = Column(String(255), unique=True, nullable=False)
    aliases = Column(JSON, default=list)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    mentions = relationship("EntityMention", back_populates="entity", cascade="all, delete-orphan")


class EntityMention(Base):
    __tablename__ = 'entity_mentions'
    
    id = Column(Integer, primary_key=True, index=True)
    entity_id = Column(Integer, ForeignKey('entities.id', ondelete='CASCADE'))
    post_id = Column(Integer, ForeignKey('posts.id', ondelete='CASCADE'))
    mention_context = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    entity = relationship("Entity", back_populates="mentions")
    post = relationship("Post", back_populates="entity_mentions")


class Narrative(Base):
    __tablename__ = 'narratives'
    
    id = Column(Integer, primary_key=True, index=True)
    movement_id = Column(Integer, ForeignKey('movements.id', ondelete='CASCADE'))
    title = Column(String(255), nullable=False)
    description = Column(Text)
    confidence_score = Column(Float, default=0.5)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    movement = relationship("Movement", back_populates="narratives")
    evolution = relationship("NarrativeEvolution", back_populates="narrative", cascade="all, delete-orphan")
    posts = relationship("Post", secondary=post_narrative_mapping, back_populates="narratives")
    evidence = relationship("NarrativeEvidence", back_populates="narrative", cascade="all, delete-orphan")


class NarrativeEvolution(Base):
    __tablename__ = 'narrative_evolution'
    
    id = Column(Integer, primary_key=True, index=True)
    narrative_id = Column(Integer, ForeignKey('narratives.id', ondelete='CASCADE'))
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    volume_score = Column(Float)
    sentiment_score = Column(Float)
    platform_distribution = Column(JSON)

    narrative = relationship("Narrative", back_populates="evolution")


class NarrativeEvidence(Base):
    __tablename__ = 'narrative_evidence'
    
    id = Column(Integer, primary_key=True, index=True)
    narrative_id = Column(Integer, ForeignKey('narratives.id', ondelete='CASCADE'))
    post_id = Column(Integer, ForeignKey('posts.id', ondelete='CASCADE'))
    evidence_strength = Column(Float, default=0.5)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    narrative = relationship("Narrative", back_populates="evidence")
    post = relationship("Post", back_populates="evidence_links")


class PlatformEvent(Base):
    __tablename__ = 'platform_events'
    
    id = Column(Integer, primary_key=True, index=True)
    movement_id = Column(Integer, ForeignKey('movements.id', ondelete='CASCADE'))
    platform = Column(String(50), nullable=False)
    event_type = Column(String(100), nullable=False)
    description = Column(Text, nullable=False)
    external_url = Column(Text)
    occurred_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    movement = relationship("Movement", back_populates="platform_events")


class Meme(Base):
    __tablename__ = 'memes'
    
    id = Column(Integer, primary_key=True, index=True)
    movement_id = Column(Integer, ForeignKey('movements.id', ondelete='CASCADE'))
    image_url = Column(Text, nullable=False)
    caption = Column(Text)
    slogan = Column(String(255))
    reposts_count = Column(Integer, default=1)
    detected_theme = Column(String(100))
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    movement = relationship("Movement", back_populates="memes")


class Summary(Base):
    __tablename__ = 'summaries'
    
    id = Column(Integer, primary_key=True, index=True)
    movement_id = Column(Integer, ForeignKey('movements.id', ondelete='CASCADE'))
    timeframe = Column(String(50), nullable=False)
    summary_text = Column(Text, nullable=False)
    bullet_points = Column(JSON)
    narrative_shifts = Column(JSON)
    sentiment_distribution = Column(JSON)
    generated_at = Column(DateTime(timezone=True), server_default=func.now())

    movement = relationship("Movement", back_populates="summaries")


class TimelineEvent(Base):
    __tablename__ = 'timeline_events'
    
    id = Column(Integer, primary_key=True, index=True)
    movement_id = Column(Integer, ForeignKey('movements.id', ondelete='CASCADE'))
    event_date = Column(Date, nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    linked_posts = Column(JSON)
    event_confidence = Column(String(50), default='verified')
    importance_score = Column(Integer, default=5)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    movement = relationship("Movement", back_populates="timeline_events")
