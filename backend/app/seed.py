import datetime
from sqlalchemy.orm import Session
from app.database import SessionLocal, engine, Base
from app import models

def seed_data():
    db = SessionLocal()
    
    # 1. Initialize tables (Base.metadata.create_all is already run, but let's be safe)
    Base.metadata.create_all(bind=engine)
    
    # Check if movement already seeded
    existing_movement = db.query(models.Movement).filter(models.Movement.slug == "cjp").first()
    if existing_movement:
        print("CJP movement already exists. Clearing existing data for a fresh seed...")
        # Clear existing tables to ensure a clean slate
        db.query(models.Meme).delete()
        db.query(models.Summary).delete()
        db.query(models.TimelineEvent).delete()
        db.query(models.PlatformEvent).delete()
        db.query(models.NarrativeEvidence).delete()
        db.query(models.post_narrative_mapping).delete()
        db.query(models.NarrativeEvolution).delete()
        db.query(models.Narrative).delete()
        db.query(models.EntityMention).delete()
        db.query(models.Entity).delete()
        db.query(models.PostEmbedding).delete()
        db.query(models.Post).delete()
        db.query(models.Source).delete()
        db.query(models.MetricsTracker).delete()
        db.query(models.Movement).delete()
        db.commit()

    print("Seeding CJP Movement...")
    movement = models.Movement(
        name="Cockroach Janta Party",
        tagline="Track narratives, memes, and internet movements in real time.",
        slug="cjp"
    )
    db.add(movement)
    db.commit()
    db.refresh(movement)
    
    # 2. Seed Sources
    print("Seeding Sources...")
    sources = [
        models.Source(
            movement_id=movement.id,
            name="Google News CJP RSS",
            platform="news_rss",
            url="https://news.google.com/rss/search?q=Cockroach+Janta+Party&hl=en-IN",
            source_reputation_score=85,
            verification_status="verified"
        ),
        models.Source(
            movement_id=movement.id,
            name="r/india Search",
            platform="reddit",
            url="https://www.reddit.com/r/india/search",
            source_reputation_score=60,
            verification_status="unverified"
        ),
        models.Source(
            movement_id=movement.id,
            name="r/IndianTeenagers Search",
            platform="reddit",
            url="https://www.reddit.com/r/IndianTeenagers/search",
            source_reputation_score=55,
            verification_status="unverified"
        ),
        models.Source(
            movement_id=movement.id,
            name="Instagram CJP Tracker",
            platform="instagram",
            url="https://www.instagram.com/explore/tags/cockroachjantaparty",
            source_reputation_score=40,
            verification_status="unverified"
        ),
        models.Source(
            movement_id=movement.id,
            name="X CJP Tracker",
            platform="x",
            url="https://twitter.com/search?q=CockroachJantaParty",
            source_reputation_score=45,
            verification_status="unverified"
        )
    ]
    for s in sources:
        db.add(s)
    db.commit()
    
    # Map sources by platform name for quick post binding
    source_map = {s.platform: s for s in db.query(models.Source).filter(models.Source.movement_id == movement.id).all()}
    
    # 3. Seed Posts
    print("Seeding Posts...")
    posts_data = [
        {
            "source_platform": "reddit",
            "source_id": source_map["reddit"].id,
            "external_id": "r1",
            "title": "CJP Twitter account withheld in India now. What are your thoughts?",
            "content": "Wait, the CJP X account is actually banned in India now. This isn't just about a parody name anymore, it highlights the exact institutional distress we are talking about. Students are organizing offline now.",
            "author": "u/aspirant_india98",
            "post_url": "https://www.reddit.com/r/india/comments/r1",
            "published_at": datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(minutes=24),
            "content_type": "reaction",
            "credibility_score": 0.85,
            "bot_probability": 0.02,
            "verification_status": "unverified",
            "sentiment": "critical",
            "primary_theme": "censorship",
            "language_code": "en",
            "translated_content": "Wait, the CJP X account is actually banned in India now. This isn't just about a parody name anymore, it highlights the exact institutional distress we are talking about. Students are organizing offline now."
        },
        {
            "source_platform": "news",
            "source_id": source_map["news_rss"].id,
            "external_id": "n1",
            "title": "Cockroach Janta Party: Satirical protest debuts convention, claims support from major opposition parliamentarians",
            "content": "A satirical protest group named Cockroach Janta Party held a student convention in New Delhi today. The organizers claim that multiple opposition parliamentarians have registered support for their campaign addressing the youth unemployment crisis.",
            "author": "India Today",
            "post_url": "https://www.indiatoday.in/india/story/n1",
            "published_at": datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(hours=1),
            "content_type": "news",
            "credibility_score": 0.95,
            "bot_probability": 0.0,
            "verification_status": "verified",
            "sentiment": "analytical",
            "primary_theme": "unemployment",
            "language_code": "en",
            "translated_content": "A satirical protest group named Cockroach Janta Party held a student convention in New Delhi today. The organizers claim that multiple opposition parliamentarians have registered support for their campaign addressing the youth unemployment crisis."
        },
        {
            "source_platform": "instagram",
            "source_id": source_map["instagram"].id,
            "external_id": "i1",
            "title": "INC-Parody Manifesto drop",
            "content": "Rival party 'Indian National Cockroaches' just dropped their manifesto! The satire is collapsing into a multi-party system lmao. They are promising 100% reservation in kitchens.",
            "author": "cjp_memes_hq",
            "post_url": "https://www.instagram.com/p/i1",
            "published_at": datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(hours=3),
            "content_type": "meme",
            "credibility_score": 0.60,
            "bot_probability": 0.12,
            "verification_status": "unverified",
            "sentiment": "ironic",
            "primary_theme": "satire",
            "language_code": "en",
            "translated_content": "Rival party 'Indian National Cockroaches' just dropped their manifesto! The satire is collapsing into a multi-party system lmao. They are promising 100% reservation in kitchens."
        },
        {
            "source_platform": "reddit",
            "source_id": source_map["reddit"].id,
            "external_id": "r2",
            "title": "Analyzing the sudden shift in narrative framing on CJP",
            "content": "Observe how fast the political framing changed on X today. The organic coordination timing shows highly correlated bursts right before the ban occurred. Possible psyop tracking. Some accounts are spamming hashtags.",
            "author": "u/meta_analyst",
            "post_url": "https://www.reddit.com/r/india/comments/r2",
            "published_at": datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(hours=5),
            "content_type": "opinion",
            "credibility_score": 0.72,
            "bot_probability": 0.08,
            "verification_status": "unverified",
            "sentiment": "critical",
            "primary_theme": "satire",
            "language_code": "en",
            "translated_content": "Observe how fast the political framing changed on X today. The organic coordination timing shows highly correlated bursts right before the ban occurred. Possible psyop tracking. Some accounts are spamming hashtags."
        },
        {
            "source_platform": "reddit",
            "source_id": source_map["reddit"].id,
            "external_id": "r3",
            "title": "Why the Cockroach analogy hit a nerve with Gen Z in India",
            "content": "The CJI comparing unemployed graduates to cockroaches trying to survive was supposed to be a metaphor for resilience, but it completely backfired. It shows how out of touch the institutions are. That's why CJP is expanding so fast.",
            "author": "u/student_union_sec",
            "post_url": "https://www.reddit.com/r/india/comments/r3",
            "published_at": datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(hours=8),
            "content_type": "opinion",
            "credibility_score": 0.78,
            "bot_probability": 0.01,
            "verification_status": "verified",
            "sentiment": "frustration",
            "primary_theme": "unemployment",
            "language_code": "en",
            "translated_content": "The CJI comparing unemployed graduates to cockroaches trying to survive was supposed to be a metaphor for resilience, but it completely backfired. It shows how out of touch the institutions are. That's why CJP is expanding so fast."
        },
        {
            "source_platform": "news",
            "source_id": source_map["news_rss"].id,
            "external_id": "n2",
            "title": "Unemployment debate enters Lok Sabha as parody party goes viral",
            "content": "Several Members of Parliament raised the issues of paper leaks and job deficits in Parliament today, directly referencing the 'Cockroach Janta Party' satirists who have amassed millions of young followers on social media.",
            "author": "Hindustan Times",
            "post_url": "https://www.hindustantimes.com/india-news/n2",
            "published_at": datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(hours=12),
            "content_type": "news",
            "credibility_score": 0.92,
            "bot_probability": 0.0,
            "verification_status": "verified",
            "sentiment": "analytical",
            "primary_theme": "unemployment",
            "language_code": "en",
            "translated_content": "Several Members of Parliament raised the issues of paper leaks and job deficits in Parliament today, directly referencing the 'Cockroach Janta Party' satirists who have amassed millions of young followers on social media."
        }
    ]
    
    seeded_posts = []
    for pd in posts_data:
        p = models.Post(
            movement_id=movement.id,
            source_id=pd["source_id"],
            source_platform=pd["source_platform"],
            external_id=pd["external_id"],
            title=pd["title"],
            content=pd["content"],
            author=pd["author"],
            post_url=pd["post_url"],
            published_at=pd["published_at"],
            content_type=pd["content_type"],
            credibility_score=pd["credibility_score"],
            bot_probability=pd["bot_probability"],
            verification_status=pd["verification_status"],
            sentiment=pd["sentiment"],
            primary_theme=pd["primary_theme"],
            language_code=pd["language_code"],
            translated_content=pd["translated_content"],
            is_duplicate=False
        )
        db.add(p)
        seeded_posts.append(p)
        
    db.commit()
    
    # 4. Seed Narratives
    print("Seeding Narratives...")
    narratives = [
        models.Narrative(
            movement_id=movement.id,
            title="Satirical Protest Against Unemployment and CJI Remarks",
            description="Satirical backlash targeting Chief Justice Kant's remarks comparing unemployed youth to cockroaches. Driven heavily by students and exam aspirants.",
            confidence_score=0.91
        ),
        models.Narrative(
            movement_id=movement.id,
            title="Rival Influencer Parody Group (Indian National Cockroaches)",
            description="Emergence of rival satirical factions ('INC-parody') mimicking established major party divisions. Driven by creators expanding meme outreach.",
            confidence_score=0.78
        ),
        models.Narrative(
            movement_id=movement.id,
            title="Astroturfing & Bot Accusations",
            description="Accusations of coordinate amplification and astroturfing by main political organizations seeking to exploit student sentiment.",
            confidence_score=0.64
        )
    ]
    for n in narratives:
        db.add(n)
    db.commit()
    
    # Refresh to fetch IDs
    seeded_narratives = db.query(models.Narrative).filter(models.Narrative.movement_id == movement.id).all()
    seeded_posts = db.query(models.Post).filter(models.Post.movement_id == movement.id).all()
    
    # 5. Seed Post-Narrative Mapping & Evidence Chains
    print("Seeding Evidence Chains & Maps...")
    # Link posts to narratives with confidence scores
    # post 0, 1, 4, 5 belong to Narrative 0 (CJI Remarks & Unemployment Satire)
    # post 2 belongs to Narrative 1 (Rival Parody Factions)
    # post 3 belongs to Narrative 2 (Astroturfing & bot accusations)
    mappings = [
        (seeded_posts[0], seeded_narratives[0], 0.88),
        (seeded_posts[1], seeded_narratives[0], 0.94),
        (seeded_posts[4], seeded_narratives[0], 0.95),
        (seeded_posts[5], seeded_narratives[0], 0.90),
        (seeded_posts[2], seeded_narratives[1], 0.85),
        (seeded_posts[3], seeded_narratives[2], 0.82)
    ]
    
    for post, narrative, score in mappings:
        db.execute(
            models.post_narrative_mapping.insert().values(
                post_id=post.id,
                narrative_id=narrative.id,
                confidence_score=score
            )
        )
        
        evidence = models.NarrativeEvidence(
            narrative_id=narrative.id,
            post_id=post.id,
            evidence_strength=score
        )
        db.add(evidence)
        
    db.commit()
    
    # 6. Seed Platform Events
    print("Seeding Platform Events...")
    platform_events = [
        models.PlatformEvent(
            movement_id=movement.id,
            platform="X / Twitter",
            event_type="Account Withholding",
            description="Official @CockroachJanta account withheld in India based on legal demands following IG expansion.",
            external_url="https://twitter.com/CockroachJanta",
            occurred_at=datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(hours=2)
        ),
        models.PlatformEvent(
            movement_id=movement.id,
            platform="Instagram",
            event_type="Visibility Throttling",
            description="Algorithm suppresses search indexing for CJP hashtags under community moderation guidelines.",
            external_url="https://instagram.com/explore/tags/cockroachjantaparty",
            occurred_at=datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=1)
        )
    ]
    for pe in platform_events:
        db.add(pe)
    db.commit()
    
    # 7. Seed Timeline Events
    print("Seeding Timeline Events...")
    timeline_events = [
        models.TimelineEvent(
            movement_id=movement.id,
            event_date=datetime.date(2026, 5, 21),
            title="Platform Censorship Escalation",
            description="Official CJP X account withheld in India. Instagram follower count surpasses ruling BJP handles within days.",
            linked_posts=["https://www.reddit.com/r/india/comments/r1"],
            event_confidence="verified",
            importance_score=8
        ),
        models.TimelineEvent(
            movement_id=movement.id,
            event_date=datetime.date(2026, 5, 18),
            title="TMC MPs Public Engagement",
            description="TMC MPs Mahua Moitra and Kirti Azad publicly reference and 'join' the satirical Gen Z CJP movement convention.",
            linked_posts=["https://www.indiatoday.in/india/story/n1"],
            event_confidence="verified",
            importance_score=6
        ),
        models.TimelineEvent(
            movement_id=movement.id,
            event_date=datetime.date(2026, 5, 16),
            title="Movement Founding",
            description="Founded by student strategist Abhijeet Dipke in response to open court comparison remarks by CJI Surya Kant.",
            linked_posts=["https://www.reddit.com/r/india/comments/r3"],
            event_confidence="verified",
            importance_score=9
        )
    ]
    for te in timeline_events:
        db.add(te)
    db.commit()
    
    # 8. Seed Summaries
    print("Seeding Summaries...")
    summary = models.Summary(
        movement_id=movement.id,
        timeframe="daily",
        summary_text="The satirical Cockroach Janta Party (CJP) movement reached an operational inflection point today as its official X handle was withheld in India. Driven by student strategies response to court comparisons on youth unemployment, the movement has shifted rapidly from baseline memetic satire to structured public organization.",
        bullet_points=[
            "Censorship Amplification: The withholding of the X account has triggered massive community backlash, driving an estimated 1.2M new followers to CJP Instagram networks.",
            "Rival Satire Factions: Creators launched the 'Indian National Cockroaches' as a parody alternative, signaling that the protest identity is evolving into structured multi-party satire.",
            "Parliamentary Traction: Direct public engagement by TMC MPs Mahua Moitra and Kirti Azad has elevated the meme into national political debates regarding youth job deficits."
        ],
        narrative_shifts=[
            {"sentiment": "ironic_protest", "shift": "Satirical identity transitioning to direct offline student organization."},
            {"sentiment": "frustration", "shift": "Backlash against judicial cockroach metaphors gaining major political consensus."}
        ],
        sentiment_distribution={"supportive": 20, "ironic": 50, "critical": 30}
    )
    db.add(summary)
    db.commit()
    
    # 9. Seed High-frequency metrics
    print("Seeding High-frequency Metrics...")
    base_time = datetime.datetime.now(datetime.timezone.utc)
    for i in range(24):
        time_offset = base_time - datetime.timedelta(hours=i)
        db.add(models.MetricsTracker(
            movement_id=movement.id,
            platform="instagram",
            follower_count=18000000 - i * 50000,
            mentions_per_minute=350 + i * 5,
            timestamp=time_offset
        ))
        db.add(models.MetricsTracker(
            movement_id=movement.id,
            platform="x",
            follower_count=802000 - i * 2000,
            mentions_per_minute=220 + i * 3,
            timestamp=time_offset
        ))
    db.commit()
    
    print("Database seeding completed successfully!")
    db.close()

if __name__ == "__main__":
    seed_data()
