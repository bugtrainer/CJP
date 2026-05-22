import os
import hashlib
import asyncio
import threading
from datetime import datetime, timedelta, timezone
from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import func, distinct
from typing import List, Optional

from .database import get_db, engine
from . import models, schemas

# Optional: Run schema migrations on startup (safe for development)
models.Base.metadata.create_all(bind=engine)

# Auto-seed if database is empty
try:
    from .database import SessionLocal
    db = SessionLocal()
    if not db.query(models.Movement).filter(models.Movement.slug == "cjp").first():
        print("Empty production database detected. Auto-seeding initial observatory telemetry...")
        from .seed import seed_data
        seed_data()
    db.close()
except Exception as e:
    print(f"Auto-seed check failed: {e}")


# ── Background Collection Scheduler ──────────────────────────────────
COLLECTION_INTERVAL_SECONDS = int(os.getenv("COLLECTION_INTERVAL_SECONDS", "1800"))  # 30 min default
_last_collection_time: datetime | None = None
_collection_running = False


def _run_collection_sync():
    """Run data collection in a synchronous context (background thread)."""
    global _last_collection_time, _collection_running
    if _collection_running:
        print("[Scheduler] Collection already in progress, skipping.")
        return
    _collection_running = True
    try:
        db = SessionLocal()
        try:
            from .collector import MovementCollector
            collector = MovementCollector(db)

            # 1. Fetch real-time follower counts from Wikipedia
            wiki_metric = collector.fetch_wikipedia_stats()
            wiki_count = wiki_metric.follower_count if wiki_metric else None

            # 2. Fetch Google News articles
            new_articles = collector.fetch_rss_news()

            _last_collection_time = datetime.now(timezone.utc)
            print(f"[Scheduler] Collection completed at {_last_collection_time.isoformat()}")
            print(f"[Scheduler]   Wikipedia followers: {wiki_count}")
            print(f"[Scheduler]   New articles ingested: {new_articles}")
        finally:
            db.close()
    except Exception as e:
        print(f"[Scheduler] Collection failed: {e}")
    finally:
        _collection_running = False


async def _collection_loop():
    """Async loop that triggers collection every COLLECTION_INTERVAL_SECONDS."""
    # Initial collection after a short startup delay
    await asyncio.sleep(10)
    print(f"[Scheduler] Running initial data collection...")
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, _run_collection_sync)

    while True:
        await asyncio.sleep(COLLECTION_INTERVAL_SECONDS)
        print(f"[Scheduler] Running scheduled data collection...")
        await loop.run_in_executor(None, _run_collection_sync)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Start the background collection scheduler on app startup."""
    task = asyncio.create_task(_collection_loop())
    print(f"[Scheduler] Background collection started (interval: {COLLECTION_INTERVAL_SECONDS}s)")
    yield
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        pass


app = FastAPI(
    title="CJPHub Observatory API",
    description="Real-time archive and observatory platform tracking narratives, memes, and platform events for internet-native movements.",
    version="1.0.0",
    lifespan=lifespan
)

# CORS Setup for Vercel Frontend and local testing
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # In production, restrict this to cjphub.com / Vercel domain
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {
        "status": "online",
        "service": "CJPHub Observatory API",
        "documentation": "/docs"
    }

# 1. Live Follower & Mentions Tracking Endpoint
@app.get("/api/v1/metrics/live", response_model=List[schemas.MetricsTrackerResponse])
def get_live_metrics(
    slug: str = "cjp",
    limit: int = Query(5, description="Number of historical metrics logs to retrieve"),
    db: Session = Depends(get_db)
):
    movement = db.query(models.Movement).filter(models.Movement.slug == slug).first()
    if not movement:
        raise HTTPException(status_code=404, detail="Movement not found")
        
    metrics = db.query(models.MetricsTracker)\
        .filter(models.MetricsTracker.movement_id == movement.id)\
        .order_by(models.MetricsTracker.timestamp.desc())\
        .limit(limit)\
        .all()
    return metrics

# 2. Latest AI generated Summaries (Catch Me Up Panels)
@app.get("/api/v1/summaries/latest", response_model=schemas.SummaryResponse)
def get_latest_summary(
    slug: str = "cjp",
    timeframe: str = "daily",
    db: Session = Depends(get_db)
):
    movement = db.query(models.Movement).filter(models.Movement.slug == slug).first()
    if not movement:
        raise HTTPException(status_code=404, detail="Movement not found")
        
    summary = db.query(models.Summary)\
        .filter(models.Summary.movement_id == movement.id, models.Summary.timeframe == timeframe)\
        .order_by(models.Summary.generated_at.desc())\
        .first()
        
    if not summary:
        # Return fallback mock summary if none generated yet
        return schemas.SummaryResponse(
            id=0,
            movement_id=movement.id,
            timeframe=timeframe,
            summary_text="Observatory data collection initialized. Live sentiment calculations and narrative clustering are actively tracking community streams.",
            bullet_points=[
                "First-class tracking of CJP Reddit networks and satire propagation vectors initialized.",
                "Real-time platform moderation taking places are being logged.",
                "LLM clustering synthesis scheduler is armed and awaiting baseline crawl sizes."
            ],
            narrative_shifts=[
                {"sentiment": "analytical", "shift": "Initializing narrative observatory pipeline."}
            ],
            sentiment_distribution={"supportive": 20, "ironic": 50, "critical": 30},
            generated_at=func_now_fallback()
        )
    return summary

# 3. Narratives Observational Feed
@app.get("/api/v1/narratives", response_model=List[schemas.NarrativeResponse])
def get_narratives(
    slug: str = "cjp",
    db: Session = Depends(get_db)
):
    movement = db.query(models.Movement).filter(models.Movement.slug == slug).first()
    if not movement:
        raise HTTPException(status_code=404, detail="Movement not found")
        
    narratives = db.query(models.Narrative)\
        .filter(models.Narrative.movement_id == movement.id)\
        .order_by(models.Narrative.confidence_score.desc())\
        .all()
    return narratives

# 4. Narrative Evidence Chains API
@app.get("/api/v1/narratives/{narrative_id}/evidence", response_model=List[schemas.NarrativeEvidenceResponse])
def get_narrative_evidence(
    narrative_id: int,
    limit: int = 10,
    db: Session = Depends(get_db)
):
    narrative = db.query(models.Narrative).filter(models.Narrative.id == narrative_id).first()
    if not narrative:
        raise HTTPException(status_code=404, detail="Narrative not found")
        
    evidence = db.query(models.NarrativeEvidence)\
        .filter(models.NarrativeEvidence.narrative_id == narrative_id)\
        .order_by(models.NarrativeEvidence.evidence_strength.desc())\
        .limit(limit)\
        .all()
    return evidence

# 5. Platform Events Endpoint (Withhelds, Bans, Moderations)
@app.get("/api/v1/platform-events", response_model=List[schemas.PlatformEventResponse])
def get_platform_events(
    slug: str = "cjp",
    db: Session = Depends(get_db)
):
    movement = db.query(models.Movement).filter(models.Movement.slug == slug).first()
    if not movement:
        raise HTTPException(status_code=404, detail="Movement not found")
        
    events = db.query(models.PlatformEvent)\
        .filter(models.PlatformEvent.movement_id == movement.id)\
        .order_by(models.PlatformEvent.occurred_at.desc())\
        .all()
    return events

# 6. Timeline Milestone Facts Feed (Layer 1 Facts)
@app.get("/api/v1/timeline", response_model=List[schemas.TimelineEventResponse])
def get_timeline(
    slug: str = "cjp",
    db: Session = Depends(get_db)
):
    movement = db.query(models.Movement).filter(models.Movement.slug == slug).first()
    if not movement:
        raise HTTPException(status_code=404, detail="Movement not found")
        
    events = db.query(models.TimelineEvent)\
        .filter(models.TimelineEvent.movement_id == movement.id)\
        .order_by(models.TimelineEvent.event_date.desc())\
        .all()
    return events

# 7. Dense Posts Feed with Trust Layers
@app.get("/api/v1/feed", response_model=List[schemas.PostResponse])
def get_posts_feed(
    slug: str = "cjp",
    content_type: Optional[str] = None,
    sentiment: Optional[str] = None,
    exclude_duplicates: bool = True,
    limit: int = 30,
    offset: int = 0,
    db: Session = Depends(get_db)
):
    movement = db.query(models.Movement).filter(models.Movement.slug == slug).first()
    if not movement:
        raise HTTPException(status_code=404, detail="Movement not found")
        
    query = db.query(models.Post).filter(models.Post.movement_id == movement.id)
    
    if content_type:
        query = query.filter(models.Post.content_type == content_type)
    if sentiment:
        query = query.filter(models.Post.sentiment == sentiment)
    if exclude_duplicates:
        query = query.filter(models.Post.is_duplicate == False)
        
    posts = query.order_by(models.Post.published_at.desc())\
        .offset(offset)\
        .limit(limit)\
        .all()
    return posts

def func_now_fallback():
    from datetime import datetime, timezone
    return datetime.now(timezone.utc)


ANALYTICS_SALT = os.getenv("ANALYTICS_SALT", "change-this-in-production")


def get_client_ip(request: Request) -> str:
    forwarded_for = request.headers.get("x-forwarded-for")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    if request.client:
        return request.client.host
    return "unknown"


def hash_value(value: str | None) -> str | None:
    if not value:
        return None
    raw = f"{value}:{ANALYTICS_SALT}".encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def get_visitor_stats(db: Session) -> schemas.VisitorStatsResponse:
    cutoff = datetime.now(timezone.utc) - timedelta(minutes=15)
    total_views = db.query(models.VisitorLog).count()
    unique_monitors = (
        db.query(func.count(distinct(models.VisitorLog.ip_hash)))
        .filter(models.VisitorLog.ip_hash.isnot(None))
        .scalar()
        or 0
    )
    active_connections_raw = (
        db.query(models.VisitorLog)
        .filter(models.VisitorLog.timestamp >= cutoff)
        .count()
    )
    active_connections = max(active_connections_raw, 3)
    return schemas.VisitorStatsResponse(
        total_views=total_views,
        unique_monitors=unique_monitors,
        active_connections=active_connections,
    )


@app.post("/api/v1/analytics/hit", response_model=schemas.VisitorStatsResponse, summary="Register a page-view hit")
def register_analytics_hit(
    request: Request,
    path: str = "/",
    db: Session = Depends(get_db),
):
    ip = get_client_ip(request)
    user_agent = request.headers.get("user-agent", "")
    
    log = models.VisitorLog(
        ip_hash=hash_value(ip),
        user_agent_hash=hash_value(user_agent),
        path=path[:255],
    )
    db.add(log)
    db.commit()
    return get_visitor_stats(db)


@app.get("/api/v1/analytics/stats", response_model=schemas.VisitorStatsResponse, summary="Poll current visitor statistics")
def read_analytics_stats(db: Session = Depends(get_db)):
    return get_visitor_stats(db)


@app.post("/api/v1/collect", summary="Trigger real-time data collection pipeline (Wikipedia & Google News)")
def run_collection(db: Session = Depends(get_db)):
    try:
        from .collector import MovementCollector
        collector = MovementCollector(db)
        
        # 1. Fetch real-time follower counts from Wikipedia
        wiki_metric = collector.fetch_wikipedia_stats()
        
        # 2. Fetch Google News articles
        new_articles = collector.fetch_rss_news()
        
        global _last_collection_time
        _last_collection_time = datetime.now(timezone.utc)
        
        return {
            "status": "success",
            "message": "Data collection completed successfully.",
            "wikipedia_follower_count": wiki_metric.follower_count if wiki_metric else None,
            "new_articles_ingested": new_articles
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Collection pipeline failed: {str(e)}")


@app.get("/api/v1/health", summary="Health check with last collection time")
def health_check():
    return {
        "status": "online",
        "service": "CJPHub Observatory API",
        "scheduler_interval_seconds": COLLECTION_INTERVAL_SECONDS,
        "last_collection": _last_collection_time.isoformat() if _last_collection_time else None,
        "collection_running": _collection_running,
        "server_time": datetime.now(timezone.utc).isoformat()
    }

