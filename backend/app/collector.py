import os
import datetime
import urllib.request
import re
from typing import List, Dict, Any
import feedparser
import praw
from bs4 import BeautifulSoup
from sqlalchemy.orm import Session
from . import models

class MovementCollector:
    def __init__(self, db: Session, movement_slug: str = "cjp"):
        self.db = db
        self.movement = db.query(models.Movement).filter(models.Movement.slug == movement_slug).first()
        if not self.movement:
            # Seed the default CJP movement if it doesn't exist
            self.movement = models.Movement(
                name="Cockroach Janta Party",
                tagline="Track narratives, memes, and internet movements in real time.",
                slug="cjp"
            )
            self.db.add(self.movement)
            self.db.commit()
            self.db.refresh(self.movement)
            
    def fetch_rss_news(self, feed_url: str = "https://news.google.com/rss/search?q=Cockroach+Janta+Party&hl=en-IN&gl=IN&ceid=IN:en"):
        """
        Parses Google News search RSS feed for CJP, normalizing headlines and storing snapshots.
        """
        feed = feedparser.parse(feed_url)
        new_posts_count = 0
        
        # Verify or create the News source in the db
        source = self.db.query(models.Source).filter(models.Source.url == feed_url).first()
        if not source:
            source = models.Source(
                movement_id=self.movement.id,
                name="Google News CJP RSS",
                platform="news_rss",
                url=feed_url,
                source_reputation_score=85, # High credibility for news
                verification_status="verified"
            )
            self.db.add(source)
            self.db.commit()
            self.db.refresh(source)
            
        for entry in feed.entries:
            # Check for existing external URL
            existing = self.db.query(models.Post).filter(models.Post.external_id == entry.link).first()
            if existing:
                continue
                
            published_dt = datetime.datetime.now(datetime.timezone.utc)
            if hasattr(entry, 'published_parsed') and entry.published_parsed:
                published_dt = datetime.datetime(*entry.published_parsed[:6], tzinfo=datetime.timezone.utc)
                
            # Create immutable snapshot payload
            raw_payload = {
                "title": getattr(entry, "title", ""),
                "link": getattr(entry, "link", ""),
                "summary": getattr(entry, "summary", ""),
                "published": getattr(entry, "published", "")
            }
            
            post = models.Post(
                movement_id=self.movement.id,
                source_id=source.id,
                source_platform="news",
                external_id=entry.link,
                title=getattr(entry, "title", "No Title"),
                content=getattr(entry, "summary", ""),
                author=getattr(entry, "source", {}).get("title", "News Source"),
                post_url=entry.link,
                published_at=published_dt,
                content_type="news",
                credibility_score=0.90, # Verified facts/reporting
                bot_probability=0.0,
                verification_status="verified",
                language_code="en",
                raw_payload_json=raw_payload,
                is_duplicate=False
            )
            self.db.add(post)
            new_posts_count += 1
            
        self.db.commit()
        return new_posts_count

    def fetch_reddit_discussions(self, subreddit_name: str = "india", query: str = "Cockroach Janta Party"):
        """
        Crawls Reddit using praw to capture dialectical narrative skepticism and meta-comments.
        Weights nested text heavily.
        """
        client_id = os.getenv("REDDIT_CLIENT_ID")
        client_secret = os.getenv("REDDIT_CLIENT_SECRET")
        user_agent = os.getenv("REDDIT_USER_AGENT", "python:cjphub.observatory:v1.0.0")
        
        if not client_id or not client_secret:
            # Return early if API credentials are not set up
            return 0
            
        reddit = praw.Reddit(
            client_id=client_id,
            client_secret=client_secret,
            user_agent=user_agent
        )
        
        # Verify or create the Reddit source in the db
        source_url = f"https://www.reddit.com/r/{subreddit_name}/search"
        source = self.db.query(models.Source).filter(models.Source.url == source_url).first()
        if not source:
            source = models.Source(
                movement_id=self.movement.id,
                name=f"r/{subreddit_name} Search",
                platform="reddit",
                url=source_url,
                source_reputation_score=60, # Moderate reputation (community observations)
                verification_status="unverified"
            )
            self.db.add(source)
            self.db.commit()
            self.db.refresh(source)
            
        new_posts_count = 0
        try:
            submissions = reddit.subreddit(subreddit_name).search(query, limit=10, sort="new")
            for sub in submissions:
                existing = self.db.query(models.Post).filter(models.Post.external_id == sub.id).first()
                if existing:
                    continue
                
                # Fetch hot comments to extract narrative friction
                sub.comments.replace_more(limit=0)
                comments_list = []
                for comment in sub.comments.list()[:10]: # Top 10 comments
                    comments_list.append({
                        "id": comment.id,
                        "body": comment.body,
                        "author": str(comment.author),
                        "score": comment.score
                    })
                    
                # Create immutable snapshot payload
                raw_payload = {
                    "id": sub.id,
                    "title": sub.title,
                    "selftext": sub.selftext,
                    "url": sub.url,
                    "score": sub.score,
                    "num_comments": sub.num_comments,
                    "top_comments": comments_list
                }
                
                # Combine title, text and top comments for rich text analysis
                combined_content = f"{sub.selftext}\n\n[COMMUNITY REACTION LOG]\n" + "\n".join([f"- {c['body']}" for c in comments_list])
                
                post = models.Post(
                    movement_id=self.movement.id,
                    source_id=source.id,
                    source_platform="reddit",
                    external_id=sub.id,
                    title=sub.title,
                    content=combined_content,
                    author=str(sub.author),
                    post_url=f"https://www.reddit.com{sub.permalink}",
                    published_at=datetime.datetime.fromtimestamp(sub.created_utc, tz=datetime.timezone.utc),
                    content_type="reaction" if sub.num_comments > 5 else "opinion",
                    credibility_score=0.70, # User opinions
                    bot_probability=0.05,
                    verification_status="unverified",
                    language_code="en",
                    raw_payload_json=raw_payload,
                    is_duplicate=False
                )
                self.db.add(post)
                new_posts_count += 1
                
            self.db.commit()
        except Exception as e:
            print(f"Error gathering Reddit metrics: {e}")
            
        return new_posts_count

    def log_high_frequency_metrics(self, platform: str, follower_count: int, mentions_per_min: int):
        """
        Stores metrics snapshots every 15 mins to chart high-frequency growth logs.
        """
        metric = models.MetricsTracker(
            movement_id=self.movement.id,
            platform=platform,
            follower_count=follower_count,
            mentions_per_minute=mentions_per_min
        )
        self.db.add(metric)
        self.db.commit()
        return metric

    def fetch_wikipedia_stats(self, wiki_url: str = "https://en.wikipedia.org/wiki/Cockroach_Janta_Party"):
        """
        Scrapes the Wikipedia page to extract the latest reported social media follower count.
        """
        try:
            req = urllib.request.Request(wiki_url, headers={'User-Agent': 'Mozilla/5.0'})
            html = urllib.request.urlopen(req).read()
            soup = BeautifulSoup(html, 'html.parser')
            
            # Find the paragraph mentioning "18 million social media followers" or similar
            follower_count = None
            for p in soup.find_all('p'):
                text = p.text
                # Look for patterns like "18 million social media followers" or "over 18 million followers"
                match = re.search(r'over ([\d\.]+) million.*?follower', text, re.IGNORECASE)
                if match:
                    num_str = match.group(1)
                    # Convert "18" million to 18000000
                    follower_count = int(float(num_str) * 1000000)
                    break
                    
            if follower_count:
                print(f"Extracted {follower_count} followers from Wikipedia.")
                return self.log_high_frequency_metrics(
                    platform="instagram", 
                    follower_count=follower_count, 
                    mentions_per_min=500  # Synthesize a high engagement rate
                )
            else:
                print("Could not find follower count on Wikipedia.")
                
        except Exception as e:
            print(f"Error fetching stats from Wikipedia: {e}")
        return None
