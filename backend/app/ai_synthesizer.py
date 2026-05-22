import json
import os
import re
from datetime import datetime, timezone
from typing import Any, Dict, List

from sqlalchemy.orm import Session

from . import models

DEMO_EXTERNAL_IDS = ["r1", "n1", "i1", "r2", "r3", "n2"]


def _extract_json_object(text: str) -> Dict[str, Any]:
    """Extract a JSON object from Gemini output, even if wrapped in markdown fences."""
    if not text:
        raise ValueError("Empty Gemini response")

    cleaned = text.strip()
    cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"\s*```$", "", cleaned)

    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", cleaned, flags=re.DOTALL)
        if not match:
            raise
        return json.loads(match.group(0))


def _normalize_summary_payload(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Keep the shape stable for the frontend and avoid missing/null fields."""
    summary_text = str(
        payload.get("summary_text")
        or "Live observatory synthesis generated from the latest collected posts."
    ).strip()

    bullet_points = payload.get("bullet_points") or []
    if not isinstance(bullet_points, list):
        bullet_points = [str(bullet_points)]
    bullet_points = [str(item).strip() for item in bullet_points if str(item).strip()][:5]

    narrative_shifts = payload.get("narrative_shifts") or []
    if not isinstance(narrative_shifts, list):
        narrative_shifts = []
    safe_shifts = []
    for item in narrative_shifts[:5]:
        if isinstance(item, dict):
            safe_shifts.append({
                "sentiment": str(item.get("sentiment") or "analytical"),
                "shift": str(item.get("shift") or "New narrative movement detected."),
            })
        else:
            safe_shifts.append({"sentiment": "analytical", "shift": str(item)})

    distribution = payload.get("sentiment_distribution") or {}
    if not isinstance(distribution, dict):
        distribution = {}
    supportive = int(distribution.get("supportive", 20) or 20)
    ironic = int(distribution.get("ironic", 50) or 50)
    critical = int(distribution.get("critical", 30) or 30)
    total = max(supportive + ironic + critical, 1)

    return {
        "summary_text": summary_text,
        "bullet_points": bullet_points,
        "narrative_shifts": safe_shifts,
        "sentiment_distribution": {
            "supportive": round(supportive * 100 / total),
            "ironic": round(ironic * 100 / total),
            "critical": round(critical * 100 / total),
        },
    }


def recent_fresh_posts(db: Session, movement_id: int, limit: int = 30) -> List[models.Post]:
    """Return fresh collected posts before seed/demo posts."""
    return (
        db.query(models.Post)
        .filter(models.Post.movement_id == movement_id)
        .filter(~models.Post.external_id.in_(DEMO_EXTERNAL_IDS))
        .filter(models.Post.is_duplicate == False)
        .order_by(models.Post.published_at.desc(), models.Post.ingested_at.desc())
        .limit(limit)
        .all()
    )


def generate_summary_from_recent_posts(
    db: Session,
    movement_slug: str = "cjp",
    timeframe: str = "daily",
    limit: int = 30,
) -> models.Summary:
    """
    Generate and persist a Gemini summary from fresh collected posts.

    Requires GEMINI_API_KEY in Railway. Optional GEMINI_MODEL can override the model.
    """
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY is not set")

    movement = db.query(models.Movement).filter(models.Movement.slug == movement_slug).first()
    if not movement:
        raise RuntimeError(f"Movement not found: {movement_slug}")

    posts = recent_fresh_posts(db, movement.id, limit=limit)
    if not posts:
        raise RuntimeError("No fresh non-demo posts available for Gemini synthesis")

    compact_posts = []
    for p in posts:
        compact_posts.append({
            "title": p.title or "",
            "content": (p.content or "")[:900],
            "source_platform": p.source_platform,
            "author": p.author or "",
            "published_at": p.published_at.isoformat() if p.published_at else "",
            "url": p.post_url,
            "credibility_score": p.credibility_score,
            "verification_status": p.verification_status,
        })

    prompt = f"""
You are CJPHub's neutral internet culture observatory analyst.
Use ONLY the collected posts below. Do not invent politicians, events, account bans, follower changes, or claims not present in these posts.
Return ONLY valid JSON with exactly these keys:
- summary_text: string, 2-4 sentences
- bullet_points: array of 3 concise strings
- narrative_shifts: array of objects with keys sentiment and shift
- sentiment_distribution: object with integer keys supportive, ironic, critical that sum to 100

Collected posts JSON:
{json.dumps(compact_posts, ensure_ascii=False)}
""".strip()

    import google.generativeai as genai

    genai.configure(api_key=api_key)
    model_name = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")
    model = genai.GenerativeModel(model_name)
    response = model.generate_content(prompt)
    payload = _extract_json_object(getattr(response, "text", ""))
    normalized = _normalize_summary_payload(payload)

    summary = models.Summary(
        movement_id=movement.id,
        timeframe=timeframe,
        summary_text=normalized["summary_text"],
        bullet_points=normalized["bullet_points"],
        narrative_shifts=normalized["narrative_shifts"],
        sentiment_distribution=normalized["sentiment_distribution"],
        generated_at=datetime.now(timezone.utc),
    )
    db.add(summary)
    db.commit()
    db.refresh(summary)
    return summary
