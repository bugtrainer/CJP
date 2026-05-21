import os
import math
from typing import List, Dict, Any, Optional
import google.generativeai as genai
from sqlalchemy.orm import Session
from sqlalchemy import text
from . import models

# Configure Gemini Generative AI Client
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

EMBEDDING_MODEL = "models/text-embedding-004"

def get_embedding(text_content: str) -> List[float]:
    """
    Calls the Gemini API to get a 1536-dimensional vector embedding for text.
    Returns a list of floats. Falls back to empty list on failure or missing keys.
    """
    if not GEMINI_API_KEY or not text_content.strip():
        # Fallback to zero vector if API key is not supplied
        return [0.0] * 1536
        
    try:
        # standard text-embedding-004 produces 768 or 1536 dimensional vectors. 
        # For production consistency, we map standard vector dimensions.
        response = genai.embed_content(
            model=EMBEDDING_MODEL,
            content=text_content,
            task_type="retrieval_document"
        )
        return response['embedding']
    except Exception as e:
        print(f"Error fetching vector embedding from Gemini API: {e}")
        return [0.0] * 1536

def translate_and_clean_discourse(text_content: str) -> Dict[str, Any]:
    """
    Detections Hinglish, Hindi, or Marathi transliteration within organic posts,
    returning a normalized cleaned English version and language codes.
    Uses Gemini Pro selectively for multilingual translation.
    """
    if not GEMINI_API_KEY or not text_content.strip():
        return {
            "language_code": "en",
            "cleaned_text": text_content,
            "translated_content": text_content
        }
        
    try:
        # Prompt model to clean Hinglish discourse safely and objectively
        model = genai.GenerativeModel('gemini-1.5-flash')
        prompt = (
            f"Analyze the following internet discourse post and normalize it to objective, plain English. "
            f"If it uses Hinglish, Hindi, Marathi, or slang, translate it to clear English, maintaining "
            f"its core sentiments (irony, frustration, support) objectively. Remove URLs and formatting. "
            f"Return in this format: [LANG_CODE]|||[CLEANED_TRANSLATION]\n\n"
            f"Post Content:\n{text_content}"
        )
        response = model.generate_content(prompt)
        result = response.text.strip()
        
        if "|||" in result:
            parts = result.split("|||", 1)
            lang_code = parts[0].strip().replace("[", "").replace("]", "").lower()
            translated = parts[1].strip()
            return {
                "language_code": lang_code[:10],
                "cleaned_text": text_content,
                "translated_content": translated
            }
    except Exception as e:
        print(f"Language detection pipeline error: {e}")
        
    return {
        "language_code": "en",
        "cleaned_text": text_content,
        "translated_content": text_content
    }

def cosine_similarity(v1: List[float], v2: List[float]) -> float:
    """
    Calculates cosine similarity between two vectors.
    """
    dot_product = sum(a * b for a, b in zip(v1, v2))
    norm_v1 = math.sqrt(sum(a * a for a in v1))
    norm_v2 = math.sqrt(sum(b * b for b in v2))
    if norm_v1 == 0 or norm_v2 == 0:
        return 0.0
    return dot_product / (norm_v1 * norm_v2)

def run_heuristic_clustering(db: Session, post_id: int):
    """
    Phase 1 Heuristic Clustering:
    Generates embeddings for a newly ingested post, performs local cosine similarity searches
    against active database narrative vector spaces, and establishes ground-truth evidence links.
    """
    post = db.query(models.Post).filter(models.Post.id == post_id).first()
    if not post:
        return
        
    # Step 1: Detect and translate Hinglish elements
    discourse_meta = translate_and_clean_discourse(post.content or post.title or "")
    post.language_code = discourse_meta["language_code"]
    post.translated_content = discourse_meta["translated_content"]
    db.commit()
    
    # Step 2: Get Embedding Vector
    vector_vals = get_embedding(post.translated_content or post.title or "")
    
    # Step 3: Persist embedding inside database using pgvector format
    # Because we represent vector format cleanly in post_embeddings table, we write via raw SQL
    # to avoid ORM driver typing limitations
    db.execute(
        text("INSERT INTO post_embeddings (post_id, embedding, embedding_model_version) VALUES (:post_id, :embedding, :version) "
             "ON CONFLICT (post_id) DO UPDATE SET embedding = :embedding"),
        {"post_id": post.id, "embedding": str(vector_vals), "version": EMBEDDING_MODEL}
    )
    db.commit()
    
    # Step 4: Map to Narratives (Level 4 Semantic grouping)
    # Perform simple cosine matching across existing narratives
    narratives = db.query(models.Narrative).filter(models.Narrative.movement_id == post.movement_id).all()
    matched_narrative_id = None
    max_similarity = 0.0
    
    # Simple heuristic cosine matching
    for narrative in narratives:
        # Find the mean vector of existing posts mapped to this narrative
        evidence_posts = db.query(models.Post)\
            .join(models.post_narrative_mapping, models.Post.id == models.post_narrative_mapping.c.post_id)\
            .filter(models.post_narrative_mapping.c.narrative_id == narrative.id)\
            .limit(10)\
            .all()
            
        if not evidence_posts:
            continue
            
        # Get mean embeddings of narrative posts
        narrative_vectors = []
        for ep in evidence_posts:
            emb_record = db.execute(
                text("SELECT embedding FROM post_embeddings WHERE post_id = :pid"),
                {"pid": ep.id}
            ).fetchone()
            if emb_record:
                # Parse string representation back into floats
                vec_str = emb_record[0].replace("[", "").replace("]", "")
                vec = [float(x) for x in vec_str.split(",") if x.strip()]
                narrative_vectors.append(vec)
                
        if not narrative_vectors:
            continue
            
        # Compute average narrative vector
        vector_len = len(vector_vals)
        avg_vector = [0.0] * vector_len
        for vec in narrative_vectors:
            for i in range(min(vector_len, len(vec))):
                avg_vector[i] += vec[i]
        avg_vector = [x / len(narrative_vectors) for x in avg_vector]
        
        sim = cosine_similarity(vector_vals, avg_vector)
        if sim > max_similarity:
            max_similarity = sim
            matched_narrative_id = narrative.id
            
    # Narrative Boundary Guardrail (Cosine Similarity > 0.78 for matching)
    if matched_narrative_id and max_similarity > 0.78:
        # Create narrative mapping and trace evidence
        db.execute(
            models.post_narrative_mapping.insert().values(
                post_id=post.id,
                narrative_id=matched_narrative_id,
                confidence_score=max_similarity
            )
        )
        
        evidence = models.NarrativeEvidence(
            narrative_id=matched_narrative_id,
            post_id=post.id,
            evidence_strength=max_similarity
        )
        db.add(evidence)
        db.commit()
    else:
        # Candidate narrative creation is bypassed in automatic MVP pipelines to prevent noise explosion.
        # Narratives are created when manual baseline parameters or high-density thresholds are achieved.
        pass

def generate_catch_me_up_brief(db: Session, movement_slug: str = "cjp") -> Optional[str]:
    """
    Level 5: Presentation Synthesis Layer
    Gathers mathematically clustered posts and verified evidence logs to summarize narrative changes
    without hallucinating facts.
    """
    movement = db.query(models.Movement).filter(models.Movement.slug == movement_slug).first()
    if not movement or not GEMINI_API_KEY:
        return None
        
    # Gathers latest 15 organic posts and timeline facts
    latest_posts = db.query(models.Post)\
        .filter(models.Post.movement_id == movement.id, models.Post.is_duplicate == False)\
        .order_by(models.Post.published_at.desc())\
        .limit(15)\
        .all()
        
    if not latest_posts:
        return "Not enough data gathered yet. Ingestion pipes are online."
        
    posts_summary = []
    for idx, p in enumerate(latest_posts):
        posts_summary.append(
            f"Source [{p.source_platform} / {p.author}]: {p.title or ''}\nExcerpt: {p.translated_content or p.content or ''[:150]}"
        )
        
    prompt = (
        f"You are the linguistic explanation layer for the CJPHub Internet Culture Observatory. "
        f"Generate a calm, objective 'Catch Me Up' brief (24-hour summary) analyzing narrative dynamics. "
        f"Do NOT invent facts, numbers, or events. Rely strictly on the telemetry posts logged below. "
        f"Ensure absolute neutrality and focus on tracking narratives and platform events rather than endorsing movement viewpoints.\n\n"
        f"Telemetry Inputs:\n" + "\n---\n".join(posts_summary)
    )
    
    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        print(f"Error generating Catch Me Up briefing: {e}")
        return None
