-- Enable vector extension for pgvector similarity mapping
CREATE EXTENSION IF NOT EXISTS vector;

-- 1. Movements Table
CREATE TABLE IF NOT EXISTS movements (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL UNIQUE,       -- 'Cockroach Janta Party'
    tagline VARCHAR(255),
    slug VARCHAR(100) NOT NULL UNIQUE,       -- 'cjp'
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 2. Follower & Mentions Tracker
CREATE TABLE IF NOT EXISTS metrics_tracker (
    id SERIAL PRIMARY KEY,
    movement_id INTEGER REFERENCES movements(id) ON DELETE CASCADE,
    platform VARCHAR(50) NOT NULL,           -- 'instagram', 'twitter', 'reddit_mentions', 'youtube'
    follower_count BIGINT,
    mentions_per_minute INTEGER,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 3. Sources with Credibility Scoring
CREATE TABLE IF NOT EXISTS sources (
    id SERIAL PRIMARY KEY,
    movement_id INTEGER REFERENCES movements(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    platform VARCHAR(50) NOT NULL,           -- 'reddit', 'x', 'instagram', 'news_rss', 'youtube'
    url TEXT UNIQUE,
    source_reputation_score INT DEFAULT 50,  -- 0-100 score assessing reliability
    verification_status VARCHAR(50) DEFAULT 'unverified', -- 'verified', 'suspicious', 'unverified'
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 4. Posts Table with Ingestion, Trust, Multilingual, and Content Types
CREATE TABLE IF NOT EXISTS posts (
    id SERIAL PRIMARY KEY,
    movement_id INTEGER REFERENCES movements(id) ON DELETE CASCADE,
    source_id INTEGER REFERENCES sources(id) ON DELETE SET NULL,
    source_platform VARCHAR(50) NOT NULL,    -- 'reddit', 'instagram', 'twitter', 'news', 'youtube'
    external_id VARCHAR(255) NOT NULL,       -- Original post URL/ID
    title VARCHAR(500),
    content TEXT,
    author VARCHAR(255),
    post_url TEXT NOT NULL,
    published_at TIMESTAMP WITH TIME ZONE,
    
    -- Ingestion & Verification Metadata
    ingested_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    collector_version VARCHAR(20) DEFAULT '1.0.0',
    scrape_status VARCHAR(50) DEFAULT 'success',
    
    -- Multilingual Parameters
    language_code VARCHAR(10) DEFAULT 'en',
    translated_content TEXT,
    
    -- Content & Trust Layers
    content_type VARCHAR(50),                -- 'meme', 'opinion', 'news', 'screenshot', 'manifesto', 'livestream', 'reaction', 'rumor', 'timeline_event'
    credibility_score FLOAT DEFAULT 0.5,     -- 0.0 - 1.0 (reporting quality, bot levels)
    bot_probability FLOAT DEFAULT 0.0,       -- 0.0 - 1.0 probability score
    verification_status VARCHAR(50),         -- 'verified', 'disputed', 'unverified'
    
    -- AI Curation Labels
    sentiment VARCHAR(50),                   -- 'supportive', 'ironic', 'critical', 'psyop_accusation', 'frustration'
    primary_theme VARCHAR(100),              -- 'unemployment', 'affordability', 'exam_scandals', 'satire'
    
    -- Immutable raw payload
    raw_payload_json JSONB,                  -- Snapshot data for historical preservation
    
    is_duplicate BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 5. Post Embeddings Table
CREATE TABLE IF NOT EXISTS post_embeddings (
    post_id INTEGER PRIMARY KEY REFERENCES posts(id) ON DELETE CASCADE,
    embedding vector(1536) NOT NULL,          -- Standard 1536-dimensional OpenAI / Gemini text embeddings
    embedding_model_version VARCHAR(50) DEFAULT 'models/text-embedding-004'
);

-- 6. Entities (Entity Graph Moat)
CREATE TABLE IF NOT EXISTS entities (
    id SERIAL PRIMARY KEY,
    entity_type VARCHAR(50),                 -- 'person', 'slogan', 'hashtag', 'organization', 'creator', 'meme_template'
    name VARCHAR(255) UNIQUE,
    aliases JSONB DEFAULT '[]'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 7. Entity Mentions
CREATE TABLE IF NOT EXISTS entity_mentions (
    id SERIAL PRIMARY KEY,
    entity_id INTEGER REFERENCES entities(id) ON DELETE CASCADE,
    post_id INTEGER REFERENCES posts(id) ON DELETE CASCADE,
    mention_context TEXT,                    -- Excerpt containing the mention
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 8. Narratives Table (Narrative Observatory Layer)
CREATE TABLE IF NOT EXISTS narratives (
    id SERIAL PRIMARY KEY,
    movement_id INTEGER REFERENCES movements(id) ON DELETE CASCADE,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    confidence_score FLOAT DEFAULT 0.5,      -- Exposed in UI to build user trust
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 9. Narrative Evolution
CREATE TABLE IF NOT EXISTS narrative_evolution (
    id SERIAL PRIMARY KEY,
    narrative_id INTEGER REFERENCES narratives(id) ON DELETE CASCADE,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    volume_score FLOAT,                      -- Narrative popularity score
    sentiment_score FLOAT,                   -- Mapped sentiment score
    platform_distribution JSONB              -- E.g. {"reddit": 0.45, "instagram": 0.55}
);

-- 10. Post to Narrative Mapping
CREATE TABLE IF NOT EXISTS post_narrative_mapping (
    post_id INTEGER REFERENCES posts(id) ON DELETE CASCADE,
    narrative_id INTEGER REFERENCES narratives(id) ON DELETE CASCADE,
    confidence_score FLOAT,
    PRIMARY KEY (post_id, narrative_id)
);

-- 11. Narrative Evidence Chains
CREATE TABLE IF NOT EXISTS narrative_evidence (
    id SERIAL PRIMARY KEY,
    narrative_id INTEGER REFERENCES narratives(id) ON DELETE CASCADE,
    post_id INTEGER REFERENCES posts(id) ON DELETE CASCADE,
    evidence_strength FLOAT DEFAULT 0.5,     -- Cosine similarity or classification probability
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 12. Platform Events Table
CREATE TABLE IF NOT EXISTS platform_events (
    id SERIAL PRIMARY KEY,
    movement_id INTEGER REFERENCES movements(id) ON DELETE CASCADE,
    platform VARCHAR(50) NOT NULL,           -- 'x', 'instagram', 'reddit', 'youtube'
    event_type VARCHAR(100) NOT NULL,        -- 'account_withholding', 'post_takedown', 'hashtag_ban', 'shadowban_suspicion'
    description TEXT NOT NULL,
    external_url TEXT,                       -- Reference link or legal order notice
    occurred_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 13. Memes Radar
CREATE TABLE IF NOT EXISTS memes (
    id SERIAL PRIMARY KEY,
    movement_id INTEGER REFERENCES movements(id) ON DELETE CASCADE,
    image_url TEXT NOT NULL,
    caption TEXT,
    slogan VARCHAR(255),
    reposts_count INT DEFAULT 1,
    detected_theme VARCHAR(100),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 14. AI Generated Briefings (Catch Me Up Summaries)
CREATE TABLE IF NOT EXISTS summaries (
    id SERIAL PRIMARY KEY,
    movement_id INTEGER REFERENCES movements(id) ON DELETE CASCADE,
    timeframe VARCHAR(50) NOT NULL,          -- 'hourly', 'daily', 'weekly'
    summary_text TEXT NOT NULL,
    bullet_points JSONB,                     -- Key chronological facts
    narrative_shifts JSONB,                  -- Array of shifted perceptions detected
    sentiment_distribution JSONB,            -- {"frustrated": 40, "ironic": 40, "supportive": 20}
    generated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 15. Milestones Timeline
CREATE TABLE IF NOT EXISTS timeline_events (
    id SERIAL PRIMARY KEY,
    movement_id INTEGER REFERENCES movements(id) ON DELETE CASCADE,
    event_date DATE NOT NULL,
    title VARCHAR(255) NOT NULL,
    description TEXT NOT NULL,
    linked_posts JSONB,                      -- Associated proof links
    event_confidence VARCHAR(50) DEFAULT 'verified', -- 'verified', 'disputed', 'inferred'
    importance_score INT DEFAULT 5,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Indices for high-frequency search and vector lookups
CREATE INDEX IF NOT EXISTS idx_posts_movement ON posts(movement_id);
CREATE INDEX IF NOT EXISTS idx_posts_duplicate ON posts(is_duplicate);
CREATE INDEX IF NOT EXISTS idx_posts_content_type ON posts(content_type);
CREATE INDEX IF NOT EXISTS idx_posts_platform ON posts(source_platform);
CREATE INDEX IF NOT EXISTS idx_narrative_evolution_timestamp ON narrative_evolution(timestamp);
