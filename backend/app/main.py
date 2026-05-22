import os
import hashlib
import asyncio
from datetime import datetime, timedelta, timezone
from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import func, distinct
from typing import List, Optional

from .database import get_db, engine
from . import models, schemas

models.Base.metadata.create_all(bind=engine)

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

COLLECTION_INTERVAL_SECONDS = int(os.getenv("COLLECTION_INTERVAL_SECONDS", "1800"))
_last_collection_time: datetime | None = None
_collection_running = False


def _collect_and_summarize(db: Session):
    from .collector import MovementCollector
    collector = MovementCollector(db)

    wiki_metric = collector.fetch_wikipedia_stats()
    wiki_count = wiki_metric.follower_count if wiki_metric else None

    # Multi-query RSS avoids empty feed when the exact phrase query has no active results.
    if hasattr(collector, "fetch_rss_news_multi"):
        new_articles = collector.fetch_rss_news_multi()
    else:
        new_articles = collector.fetch_rss_news()

    summary_id = None
    summary_error = None
    if os.getenv("GEMINI_API_KEY"):
        try:
            from .ai_synthesizer import generate_summary_from_recent_posts
            summary = generate_summary_from_recent_posts(db)
            summary_id = summary.id
        except Exception as e:
            summary_error = str(e)
    else:
        summary_error = "GEMINI_API_KEY is not set"

    return {
        "wikipedia_follower_count": wiki_count,
        "new_articles_ingested": new_articles,
        "gemini_summary_generated": summary_id is not None,
        "gemini_summary_id": summary_id,
        "gemini_summary_error": summary_error,
    }


def _run_collection_sync():
    global _last_collection_time, _collection_running
    if _collection_running:
        print("[Scheduler] Collection already in progress, skipping.")
        return
    _collection_running = True
    try:
        db = SessionLocal()
        try:
            result = _collect_and_summarize(db)
            _last_collection_time = datetime.now(timezone.utc)
            print(f"[Scheduler] Collection completed at {_last_collection_time.isoformat()}")
            print(f"[Scheduler]   Wikipedia followers: {result['wikipedia_follower_count']}")
            print(f"[Scheduler]   New articles ingested: {result['new_articles_ingested']}")
            if result["gemini_summary_generated"]:
                print(f"[Scheduler]   Gemini summary generated: {result['gemini_summary_id']}")
            else:
                print(f"[Scheduler]   Gemini synthesis skipped/failed: {result['gemini_summary_error']}")
        finally:
            db.close()
    except Exception as e:
        print(f"[Scheduler] Collection failed: {e}")
    finally:
        _collection_running = False


async def _collection_loop():
    await asyncio.sleep(10)
    print("[Scheduler] Running initial data collection...")
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, _run_collection_sync)

    while True:
        await asyncio.sleep(COLLECTION_INTERVAL_SECONDS)
        print("[Scheduler] Running scheduled data collection...")
        await loop.run_in_executor(None, _run_collection_sync)


@asynccontextmanager
async def lifespan(app: FastAPI):
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
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def read_root():
    return {"status": "online", "service": "CJPHub Observatory API", "documentation": "/docs"}


@app.get("/api/v1/metrics/live", response_model=List[schemas.MetricsTrackerResponse])
def get_live_metrics(slug: str = "cjp", limit: int = Query(5), db: Session = Depends(get_db)):
    movement = db.query(models.Movement).filter(models.Movement.slug == slug).first()
    if not movement:
        raise HTTPException(status_code=404, detail="Movement not found")
    return (
        db.query(models.MetricsTracker)
        .filter(models.MetricsTracker.movement_id == movement.id)
        .order_by(models.MetricsTracker.timestamp.desc())
        .limit(limit)
        .all()
    )


@app.get("/api/v1/summaries/latest", response_model=schemas.SummaryResponse)
def get_latest_summary(slug: str = "cjp", timeframe: str = "daily", db: Session = Depends(get_db)):
    movement = db.query(models.Movement).filter(models.Movement.slug == slug).first()
    if not movement:
        raise HTTPException(status_code=404, detail="Movement not found")
    summary = (
        db.query(models.Summary)
        .filter(models.Summary.movement_id == movement.id, models.Summary.timeframe == timeframe)
        .order_by(models.Summary.generated_at.desc())
        .first()
    )
    if not summary:
        return schemas.SummaryResponse(
            id=0,
            movement_id=movement.id,
            timeframe=timeframe,
            summary_text="Observatory data collection initialized. Live sentiment calculations and narrative clustering are actively tracking community streams.",
            bullet_points=[
                "First-class tracking of CJP RSS/news streams initialized.",
                "Real-time platform moderation tracking is being logged.",
                "LLM synthesis is armed and awaiting fresh collected posts.",
            ],
            narrative_shifts=[{"sentiment": "analytical", "shift": "Initializing narrative observatory pipeline."}],
            sentiment_distribution={"supportive": 20, "ironic": 50, "critical": 30},
            generated_at=func_now_fallback(),
        )
    return summary


@app.get("/api/v1/narratives", response_model=List[schemas.NarrativeResponse])
def get_narratives(slug: str = "cjp", db: Session = Depends(get_db)):
    movement = db.query(models.Movement).filter(models.Movement.slug == slug).first()
    if not movement:
        raise HTTPException(status_code=404, detail="Movement not found")
    return (
        db.query(models.Narrative)
        .filter(models.Narrative.movement_id == movement.id)
        .order_by(models.Narrative.confidence_score.desc())
        .all()
    )


@app.get("/api/v1/narratives/{narrative_id}/evidence", response_model=List[schemas.NarrativeEvidenceResponse])
def get_narrative_evidence(narrative_id: int, limit: int = 10, db: Session = Depends(get_db)):
    narrative = db.query(models.Narrative).filter(models.Narrative.id == narrative_id).first()
    if not narrative:
        raise HTTPException(status_code=404, detail="Narrative not found")
    return (
        db.query(models.NarrativeEvidence)
        .filter(models.NarrativeEvidence.narrative_id == narrative_id)
        .order_by(models.NarrativeEvidence.evidence_strength.desc())
        .limit(limit)
        .all()
    )


@app.get("/api/v1/platform-events", response_model=List[schemas.PlatformEventResponse])
def get_platform_events(slug: str = "cjp", db: Session = Depends(get_db)):
    movement = db.query(models.Movement).filter(models.Movement.slug == slug).first()
    if not movement:
        raise HTTPException(status_code=404, detail="Movement not found")
    return (
        db.query(models.PlatformEvent)
        .filter(models.PlatformEvent.movement_id == movement.id)
        .order_by(models.PlatformEvent.occurred_at.desc())
        .all()
    )


@app.get("/api/v1/timeline", response_model=List[schemas.TimelineEventResponse])
def get_timeline(slug: str = "cjp", db: Session = Depends(get_db)):
    movement = db.query(models.Movement).filter(models.Movement.slug == slug).first()
    if not movement:
        raise HTTPException(status_code=404, detail="Movement not found")
    return (
        db.query(models.TimelineEvent)
        .filter(models.TimelineEvent.movement_id == movement.id)
        .order_by(models.TimelineEvent.event_date.desc())
        .all()
    )


@app.get("/api/v1/feed", response_model=List[schemas.PostResponse])
def get_posts_feed(
    slug: str = "cjp",
    content_type: Optional[str] = None,
    sentiment: Optional[str] = None,
    exclude_duplicates: bool = True,
    fresh_only: bool = Query(True, description="Exclude seed/demo records and return collected posts first"),
    limit: int = 30,
    offset: int = 0,
    db: Session = Depends(get_db),
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
    if fresh_only:
        from .ai_synthesizer import DEMO_EXTERNAL_IDS
        query = query.filter(~models.Post.external_id.in_(DEMO_EXTERNAL_IDS))
    return (
        query.order_by(models.Post.published_at.desc(), models.Post.ingested_at.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )


def func_now_fallback():
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
    return hashlib.sha256(f"{value}:{ANALYTICS_SALT}".encode("utf-8")).hexdigest()


def get_visitor_stats(db: Session) -> schemas.VisitorStatsResponse:
    cutoff = datetime.now(timezone.utc) - timedelta(minutes=15)
    total_views = db.query(models.VisitorLog).count()
    unique_monitors = (
        db.query(func.count(distinct(models.VisitorLog.ip_hash)))
        .filter(models.VisitorLog.ip_hash.isnot(None))
        .scalar()
        or 0
    )
    active_connections = max(db.query(models.VisitorLog).filter(models.VisitorLog.timestamp >= cutoff).count(), 3)
    return schemas.VisitorStatsResponse(total_views=total_views, unique_monitors=unique_monitors, active_connections=active_connections)


@app.post("/api/v1/analytics/hit", response_model=schemas.VisitorStatsResponse)
def register_analytics_hit(request: Request, path: str = "/", db: Session = Depends(get_db)):
    log = models.VisitorLog(
        ip_hash=hash_value(get_client_ip(request)),
        user_agent_hash=hash_value(request.headers.get("user-agent", "")),
        path=path[:255],
    )
    db.add(log)
    db.commit()
    return get_visitor_stats(db)


@app.get("/api/v1/analytics/stats", response_model=schemas.VisitorStatsResponse)
def read_analytics_stats(db: Session = Depends(get_db)):
    return get_visitor_stats(db)


@app.get("/api/v1/collect")
@app.post("/api/v1/collect")
def run_collection(db: Session = Depends(get_db)):
    try:
        result = _collect_and_summarize(db)
        global _last_collection_time
        _last_collection_time = datetime.now(timezone.utc)
        return {"status": "success", "message": "Data collection completed.", **result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Collection pipeline failed: {str(e)}")


@app.get("/api/v1/summaries/generate", response_model=schemas.SummaryResponse)
@app.post("/api/v1/summaries/generate", response_model=schemas.SummaryResponse)
def generate_summary_endpoint(slug: str = "cjp", timeframe: str = "daily", limit: int = 30, db: Session = Depends(get_db)):
    try:
        from .ai_synthesizer import generate_summary_from_recent_posts
        return generate_summary_from_recent_posts(db, movement_slug=slug, timeframe=timeframe, limit=limit)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Gemini summary generation failed: {str(e)}")


@app.get("/api/v1/health")
def health_check():
    return {
        "status": "online",
        "service": "CJPHub Observatory API",
        "scheduler_interval_seconds": COLLECTION_INTERVAL_SECONDS,
        "last_collection": _last_collection_time.isoformat() if _last_collection_time else None,
        "collection_running": _collection_running,
        "server_time": datetime.now(timezone.utc).isoformat(),
    }
