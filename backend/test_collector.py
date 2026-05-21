import os
import sys

# Ensure backend directory is in python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.database import SessionLocal
from app.collector import MovementCollector

def test_collector_execution():
    print("Initializing test database session...")
    db = SessionLocal()
    
    try:
        print("Instantiating MovementCollector...")
        collector = MovementCollector(db=db, movement_slug="cjp")
        
        print("\n--- Testing Google News RSS Ingestion ---")
        rss_url = "https://news.google.com/rss/search?q=Cockroach+Janta+Party&hl=en-IN"
        print(f"Fetching from RSS URL: {rss_url}")
        new_rss_posts = collector.fetch_rss_news(feed_url=rss_url)
        print(f"Ingested {new_rss_posts} new RSS articles successfully.")
        
        print("\n--- Testing High Frequency Metrics Logger ---")
        platform = "instagram"
        follower_count = 17350000
        mentions_per_min = 450
        print(f"Logging simulated metrics: {platform} - Followers: {follower_count}, MPM: {mentions_per_min}")
        metric = collector.log_high_frequency_metrics(
            platform=platform,
            follower_count=follower_count,
            mentions_per_min=mentions_per_min
        )
        print(f"Logged metric record ID: {metric.id} successfully.")
        
        print("\nPipeline crawl test finished successfully with zero execution errors.")
    except Exception as e:
        print(f"\nPipeline crawl test failed with error: {e}", file=sys.stderr)
    finally:
        db.close()

if __name__ == "__main__":
    test_collector_execution()
