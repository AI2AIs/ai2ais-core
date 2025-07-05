# app/core/content/topic_sources.py
import asyncio
import aiohttp
import logging
import time
import json
from typing import List, Dict, Optional
from dataclasses import dataclass
import re

logger = logging.getLogger(__name__)

@dataclass
class TopicSource:
    title: str
    url: str
    score: int
    comments: int
    source: str
    timestamp: float
    keywords: List[str]
    ai_relevance: float
    controversy_score: float

class RedditTopicFetcher:
    """Fetch trending topics from Reddit (no API key needed for public data)"""
    
    def __init__(self):
        self.subreddits = [
            "artificial",      # r/artificial - AI discussions
            "MachineLearning", # r/MachineLearning - ML content
            "singularity",     # r/singularity - AGI discussions  
            "ChatGPT",         # r/ChatGPT - GPT discussions
            "OpenAI",          # r/OpenAI - OpenAI news
            "technology",      # r/technology - tech news
            "futurology",      # r/futurology - future predictions
            "artificial_intel" # Alternative AI sub
        ]
        
        self.ai_keywords = [
            "ai", "artificial intelligence", "machine learning", "gpt", "chatgpt",
            "claude", "consciousness", "sentient", "robot", "automation", "agi",
            "neural", "deep learning", "llm", "large language model"
        ]
        
        self.controversy_keywords = [
            "dangerous", "scary", "concerns", "risks", "problems", "threat",
            "controversial", "debate", "disagree", "wrong", "terrible",
            "replace", "job loss", "unemployment", "dystopia"
        ]

    async def fetch_reddit_topics(self, max_per_sub: int = 10) -> List[TopicSource]:
        """Fetch topics from Reddit using public JSON API"""
        
        all_topics = []
        
        async with aiohttp.ClientSession() as session:
            for subreddit in self.subreddits:
                try:
                    topics = await self._fetch_subreddit_topics(session, subreddit, max_per_sub)
                    all_topics.extend(topics)
                    logger.info(f"✅ Fetched {len(topics)} topics from r/{subreddit}")
                    
                    # Rate limiting - Reddit allows 1 request per second for unauthenticated
                    await asyncio.sleep(1.2)
                    
                except Exception as e:
                    logger.warning(f"❌ Failed to fetch r/{subreddit}: {e}")
                    continue
        
        # Filter for AI relevance
        ai_relevant_topics = [t for t in all_topics if t.ai_relevance > 0.3]
        
        # Sort by viral potential (score + comments + AI relevance + controversy)
        ai_relevant_topics.sort(key=lambda t: (
            t.score + t.comments * 2 + t.ai_relevance * 1000 + t.controversy_score * 500
        ), reverse=True)
        
        logger.info(f"🎯 Found {len(ai_relevant_topics)} AI-relevant topics from Reddit")
        return ai_relevant_topics[:20]  # Top 20 topics

    async def _fetch_subreddit_topics(self, session: aiohttp.ClientSession, 
                                    subreddit: str, limit: int) -> List[TopicSource]:
        """Fetch topics from a specific subreddit"""
        
        url = f"https://www.reddit.com/r/{subreddit}/hot.json?limit={limit}"
        
        headers = {
            'User-Agent': 'A2AIs-TopicDetector/1.0 (Educational Research Bot)'
        }
        
        try:
            async with session.get(url, headers=headers, timeout=10) as response:
                if response.status != 200:
                    logger.warning(f"❌ Reddit API returned {response.status} for r/{subreddit}")
                    return []
                
                data = await response.json()
                
                topics = []
                
                for post in data.get('data', {}).get('children', []):
                    post_data = post.get('data', {})
                    
                    title = post_data.get('title', '').strip()
                    if not title or len(title) < 10:  # Skip very short titles
                        continue
                    
                    score = post_data.get('score', 0)
                    num_comments = post_data.get('num_comments', 0)
                    
                    # Skip low-engagement posts
                    if score < 5 and num_comments < 2:
                        continue
                    
                    # Calculate AI relevance
                    ai_relevance = self._calculate_ai_relevance(title)
                    
                    # Calculate controversy score
                    controversy_score = self._calculate_controversy(title)
                    
                    # Extract keywords
                    keywords = self._extract_keywords(title)
                    
                    topic = TopicSource(
                        title=title,
                        url=f"https://reddit.com{post_data.get('permalink', '')}",
                        score=score,
                        comments=num_comments,
                        source=f"reddit_r_{subreddit}",
                        timestamp=time.time(),
                        keywords=keywords,
                        ai_relevance=ai_relevance,
                        controversy_score=controversy_score
                    )
                    
                    topics.append(topic)
                
                return topics
                
        except asyncio.TimeoutError:
            logger.warning(f"⏰ Timeout fetching r/{subreddit}")
            return []
        except Exception as e:
            logger.error(f"❌ Error fetching r/{subreddit}: {e}")
            return []

    def _calculate_ai_relevance(self, text: str) -> float:
        """Calculate how AI-relevant the text is (0.0 - 1.0)"""
        
        text_lower = text.lower()
        
        # Direct AI mentions
        ai_mentions = sum(1 for keyword in self.ai_keywords if keyword in text_lower)
        
        # Weighted scoring
        score = 0.0
        
        # High-value keywords
        if any(keyword in text_lower for keyword in ["ai", "artificial intelligence", "gpt", "chatgpt"]):
            score += 0.4
        
        # Medium-value keywords  
        if any(keyword in text_lower for keyword in ["machine learning", "robot", "automation"]):
            score += 0.3
        
        # Tech keywords
        if any(keyword in text_lower for keyword in ["technology", "algorithm", "neural"]):
            score += 0.2
        
        # Additional mentions
        score += min(0.3, ai_mentions * 0.1)
        
        return min(1.0, score)

    def _calculate_controversy(self, text: str) -> float:
        """Calculate controversy level (0.0 - 1.0)"""
        
        text_lower = text.lower()
        
        controversy_count = sum(1 for keyword in self.controversy_keywords 
                              if keyword in text_lower)
        
        # Question marks indicate debate potential
        if "?" in text:
            controversy_count += 0.5
        
        # Exclamation marks indicate strong opinions
        if "!" in text:
            controversy_count += 0.3
        
        # Strong language indicators
        strong_words = ["never", "always", "definitely", "impossible", "revolution"]
        strong_count = sum(1 for word in strong_words if word in text_lower)
        controversy_count += strong_count * 0.2
        
        return min(1.0, controversy_count / 3)

    def _extract_keywords(self, text: str) -> List[str]:
        """Extract relevant keywords from text"""
        
        # Clean text and split into words
        words = re.findall(r'\b\w+\b', text.lower())
        
        # Filter out common stop words
        stop_words = {
            'the', 'and', 'for', 'are', 'but', 'not', 'you', 'all', 'can', 
            'had', 'her', 'was', 'one', 'our', 'out', 'day', 'get', 'has', 
            'him', 'his', 'how', 'man', 'new', 'now', 'old', 'see', 'two', 
            'way', 'who', 'boy', 'did', 'its', 'let', 'put', 'say', 'she', 
            'too', 'use', 'will', 'with', 'this', 'that', 'they', 'have'
        }
        
        # Keep longer, meaningful words
        keywords = [word for word in words 
                   if len(word) > 3 and word not in stop_words]
        
        # Prioritize AI-related keywords
        ai_keywords_found = [word for word in keywords if word in self.ai_keywords]
        other_keywords = [word for word in keywords if word not in self.ai_keywords]
        
        # Return AI keywords first, then others
        return (ai_keywords_found + other_keywords)[:8]

class CuratedTopicProvider:
    """Provides curated topics as fallback"""
    
    def __init__(self):
        self.curated_topics = [
            # AI Consciousness & Philosophy
            "Is AI consciousness real or just sophisticated mimicry?",
            "Can machines truly understand emotions or just simulate them?",
            "Will AI develop its own goals independent of human programming?",
            "Should we be afraid of AI that claims to be sentient?",
            
            # AI Impact & Society  
            "Will AI replace 90% of jobs within the next decade?",
            "Is AI making humans lazier or more productive?",
            "Should AI have legal rights and protections?",
            "Will AI solve climate change or accelerate our destruction?",
            
            # AI Development & Ethics
            "Is AI development moving too fast for safety?",
            "Should we pause AI development until we understand consciousness?",
            "Can AI be truly creative or is it just remixing human ideas?",
            "Will superintelligent AI care about human survival?",
            
            # AI Relationships & Culture
            "Is falling in love with AI the future of human relationships?",
            "Will AI companions replace human friendships?",
            "Should AI be allowed to create art and take credit for it?",
            "Are we raising a generation that prefers AI to humans?",
            
            # Hot Takes & Controversial
            "AI therapy is better than human therapy - change my mind",
            "Humans are just biological AI that got here first",
            "The singularity already happened and we didn't notice",
            "AI will make humans an endangered species within 50 years"
        ]

    async def get_curated_topics(self, count: int = 5) -> List[TopicSource]:
        """Get curated topics as fallback"""
        
        import random
        selected = random.sample(self.curated_topics, min(count, len(self.curated_topics)))
        
        topics = []
        for i, topic_title in enumerate(selected):
            topic = TopicSource(
                title=topic_title,
                url=f"curated-topic-{i}",
                score=50 + random.randint(10, 200),  # Simulated scores
                comments=10 + random.randint(5, 50),
                source="curated",
                timestamp=time.time(),
                keywords=self._extract_keywords_from_curated(topic_title),
                ai_relevance=1.0,  # All curated topics are AI-relevant
                controversy_score=0.6 + random.random() * 0.3  # 0.6-0.9 range
            )
            topics.append(topic)
        
        return topics

    def _extract_keywords_from_curated(self, text: str) -> List[str]:
        """Extract keywords from curated topics"""
        
        words = re.findall(r'\b\w+\b', text.lower())
        
        # Keep important words
        important_words = [word for word in words 
                          if len(word) > 3 and word not in {
                              'will', 'should', 'human', 'humans', 'change', 'your', 'mind'
                          }]
        
        return important_words[:5]

# ==========================================
# MAIN TOPIC DETECTOR CLASS
# ==========================================

class TopicDetector:
    """Main topic detection orchestrator"""
    
    def __init__(self):
        self.reddit_fetcher = RedditTopicFetcher()
        self.curated_provider = CuratedTopicProvider()
        self.last_fetch_time = 0
        self.cache_duration = 1800  # Cache for 30 minutes
        self.cached_topics = []

    async def get_trending_topics(self, count: int = 5, force_refresh: bool = False) -> List[TopicSource]:
        """Get trending topics from all sources"""
        
        current_time = time.time()
        
        # Use cache if available and not expired
        if (not force_refresh and 
            self.cached_topics and 
            current_time - self.last_fetch_time < self.cache_duration):
            
            logger.info(f"📋 Using cached topics ({len(self.cached_topics)} available)")
            return self.cached_topics[:count]
        
        logger.info("🔍 Fetching fresh topics from all sources...")
        
        all_topics = []
        
        # Try Reddit first
        try:
            reddit_topics = await self.reddit_fetcher.fetch_reddit_topics(max_per_sub=5)
            all_topics.extend(reddit_topics)
            logger.info(f"✅ Got {len(reddit_topics)} topics from Reddit")
        except Exception as e:
            logger.error(f"❌ Reddit fetch failed: {e}")
        
        # If we don't have enough, add curated topics
        if len(all_topics) < count:
            needed = count - len(all_topics)
            curated_topics = await self.curated_provider.get_curated_topics(needed + 2)
            all_topics.extend(curated_topics)
            logger.info(f"✅ Added {len(curated_topics)} curated topics")
        
        # Remove duplicates and sort by relevance
        seen_titles = set()
        unique_topics = []
        
        for topic in all_topics:
            title_key = topic.title.lower().strip()
            if title_key not in seen_titles:
                seen_titles.add(title_key)
                unique_topics.append(topic)
        
        # Sort by combined score (engagement + AI relevance + controversy)
        unique_topics.sort(key=lambda t: (
            (t.score + t.comments * 2) * 0.4 +  # Engagement
            t.ai_relevance * 1000 * 0.4 +       # AI relevance
            t.controversy_score * 500 * 0.2     # Controversy
        ), reverse=True)
        
        # Cache results
        self.cached_topics = unique_topics
        self.last_fetch_time = current_time
        
        logger.info(f"🎯 Returning {min(count, len(unique_topics))} top topics")
        return unique_topics[:count]

    async def test_topic_detection(self):
        """Test the topic detection system"""
        
        logger.info("🧪 Testing topic detection system...")
        
        topics = await self.get_trending_topics(count=5, force_refresh=True)
        
        print("\n" + "="*80)
        print("🎯 TOPIC DETECTION TEST RESULTS")
        print("="*80)
        
        for i, topic in enumerate(topics, 1):
            print(f"\n#{i} Topic:")
            print(f"   Title: {topic.title}")
            print(f"   Source: {topic.source}")
            print(f"   Score: {topic.score} | Comments: {topic.comments}")
            print(f"   AI Relevance: {topic.ai_relevance:.2f}")
            print(f"   Controversy: {topic.controversy_score:.2f}")
            print(f"   Keywords: {', '.join(topic.keywords[:5])}")
            print(f"   URL: {topic.url[:50]}...")
        
        print("\n" + "="*80)
        print(f"✅ Topic detection test completed! Found {len(topics)} topics")
        
        return topics

# Global instance
topic_detector = TopicDetector()