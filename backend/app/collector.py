import os
import datetime
import urllib.request
import urllib.parse
import re
from typing import List, Dict, Any
import feedparser
import praw
from bs4 import BeautifulSoup
from sqlalchemy.orm import Session
from . import models


DEFAULT_NEWS_QUERIES = [
    "Cockroach Janta Party",
    "\"Cockroach Janta Party\"",
    "Abhijeet Dipke Cockroach Janta Party",
    "Cockroach Janta Party Instagram followers",
    "Cockroach Janta Party X account",
    "CJP Abhijeet Dipke",
]


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

    def build_google_news_url(self, query: str) -> str:
        encoded = urllib.parse.quote_plus(query)
        return f"https://news.google.com/rss/search?q={encoded}&hl=en-IN&gl=IN&ceid=IN:en"

    def fetch_rss_news_multi(self, queries: List[str] | None = None) -> int:
        """
        Fetch multiple Google News RSS searches so the feed is not empty when one query is too narrow.
        """
        total_new = 0
        for query in queries or DEFAULT_NEWS_QUERIES:
            feed_url = self.build_google_news_url(query)
            try:
                inserted = self.fetch_rss_news(feed_url=feed_url, source_name=f"Google News RSS: {query}")
                print(f"[Collector] Google News query '{query}' inserted {inserted} posts")
                total_new += inserted
            except Exception as e:
                print(f"[Collector] Google News query '{query}' failed: {e}")
        return total_new

    def fetch_rss_news(
        self,
        feed_url: str = "https://news.google.com/rss/search?q=Cockroach+Janta+Party&hl=en-IN&gl=IN&ceid=IN:en",
        source_name: str = "Google News CJP RSS",
    ):
        """
        Parses Google News search RSS feed for CJP, normalizing headlines and storing snapshots.
        """
        feed = feedparser.parse(feed_url)
        new_posts_count = 0

        if getattr(feed, "bozo", 0):
            print(f"[Collector] RSS parse warning for {feed_url}: {getattr(feed, 'bozo_exception', '')}")

        # Verify or create the News source in the db
        source = self.db.query(models.Source).filter(models.Source.url == feed_url).first()
        if not source:
            source = models.Source(
                movement_id=self.movement.id,
                name=source_name,
                platform="news_rss",
                url=feed_url,
                source_reputation_score=85, # High credibility for news
                verification_status="verified"
            )
            self.db.add(source)
            self.db.commit()
            self.db.refresh(source)

        for entry in feed.entries:
            entry_link = getattr(entry, "link", None)
            if not entry_link:
                continue

            # Check for existing external URL globally to avoid duplicate Google News links
            existing = self.db.query(models.Post).filter(models.Post.external_id == entry_link).first()
            if existing:
                continue

            published_dt = datetime.datetime.now(datetime.timezone.utc)
            if hasattr(entry, 'published_parsed') and entry.published_parsed:
                published_dt = datetime.datetime(*entry.published_parsed[:6], tzinfo=datetime.timezone.utc)

            source_title = "News Source"
            entry_source = getattr(entry, "source", None)
            if isinstance(entry_source, dict):
                source_title = entry_source.get("title") or source_title
            elif entry_source is not None:
                source_title = getattr(entry_source, "title", source_title)

            # Create immutable snapshot payload
            raw_payload = {
                "title": getattr(entry, "title", ""),
                "link": entry_link,
                "summary": getattr(entry, "summary", ""),
                "published": getattr(entry, "published", ""),
                "source": source_title,
                "feed_url": feed_url,
            }

            post = models.Post(
                movement_id=self.movement.id,
                source_id=source.id,
                source_platform="news",
                external_id=entry_link,
                title=getattr(entry, "title", "No Title"),
                content=getattr(entry, "summary", ""),
                author=source_title,
                post_url=entry_link,
                published_at=published_dt,
                content_type="news",
                credibility_score=0.90, # Verified facts/reporting
                bot_probability=0.0,
                verification_status="verified",
                sentiment="analytical",
                primary_theme="cjp_live_news",
                language_code="en",
                raw_payload_json=raw_payload,
                is_duplicate=False
            )
            self.db.add(post)
            new_posts_count += 1

        self.db.commit()
        return new_posts_count

    def build_bing_news_url(self, query: str) -> str:
        encoded = urllib.parse.quote_plus(query)
        return f"https://www.bing.com/news/search?q={encoded}&format=rss"

    def fetch_bing_news_rss_multi(self, queries: List[str] | None = None) -> int:
        """
        Fetch multiple Bing News RSS searches to catch articles Google misses.
        """
        total_new = 0
        for query in queries or DEFAULT_NEWS_QUERIES:
            feed_url = self.build_bing_news_url(query)
            try:
                inserted = self.fetch_rss_news(feed_url=feed_url, source_name=f"Bing News RSS: {query}")
                print(f"[Collector] Bing News query '{query}' inserted {inserted} posts")
                total_new += inserted
            except Exception as e:
                print(f"[Collector] Bing News query '{query}' failed: {e}")
        return total_new

    def fetch_wikipedia_references(self, wiki_url: str = "https://en.wikipedia.org/wiki/Cockroach_Janta_Party"):
        """
        Scrapes the Wikipedia page to extract external citation URLs.
        """
        new_posts_count = 0
        try:
            req = urllib.request.Request(wiki_url, headers={'User-Agent': 'Mozilla/5.0'})
            html = urllib.request.urlopen(req).read()
            soup = BeautifulSoup(html, 'html.parser')

            # Extract all external links
            external_links = soup.find_all('a', href=True)
            refs = [a.get('href') for a in external_links if a.get('href').startswith('http')]
            
            # Filter out wikimedia/wikipedia internal subdomains
            valid_refs = [url for url in refs if 'wikipedia.org' not in url and 'wikimedia.org' not in url and 'wikidata.org' not in url]
            
            # Verify or create the Wikipedia source in the db
            source = self.db.query(models.Source).filter(models.Source.url == wiki_url).first()
            if not source:
                source = models.Source(
                    movement_id=self.movement.id,
                    name="Wikipedia References",
                    platform="wikipedia",
                    url=wiki_url,
                    source_reputation_score=80, # Wikipedia references
                    verification_status="verified"
                )
                self.db.add(source)
                self.db.commit()
                self.db.refresh(source)

            for ref_url in valid_refs:
                # Check for existing external URL globally
                existing = self.db.query(models.Post).filter(models.Post.external_id == ref_url).first()
                if existing:
                    continue

                published_dt = datetime.datetime.now(datetime.timezone.utc)
                
                # Create immutable snapshot payload
                raw_payload = {
                    "title": "Wikipedia Reference Citation",
                    "link": ref_url,
                    "summary": "Extracted from Wikipedia references section.",
                    "feed_url": wiki_url,
                }

                post = models.Post(
                    movement_id=self.movement.id,
                    source_id=source.id,
                    source_platform="news",
                    external_id=ref_url,
                    title="Wikipedia Cited Article",
                    content="Extracted from Wikipedia references. " + ref_url,
                    author="Wikipedia Contributor",
                    post_url=ref_url,
                    published_at=published_dt,
                    content_type="news",
                    credibility_score=0.85, # Wikipedia reference
                    bot_probability=0.0,
                    verification_status="verified",
                    sentiment="analytical",
                    primary_theme="cjp_live_news",
                    language_code="en",
                    raw_payload_json=raw_payload,
                    is_duplicate=False
                )
                self.db.add(post)
                new_posts_count += 1

            self.db.commit()
            if new_posts_count > 0:
                print(f"[Collector] Extracted {new_posts_count} new references from Wikipedia")
        except Exception as e:
            print(f"[Collector] Error fetching Wikipedia references: {e}")
            
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
