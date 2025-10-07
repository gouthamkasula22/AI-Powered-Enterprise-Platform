"""
Query Optimizer for caching and performance monitoring.
"""

import hashlib
import json
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from collections import defaultdict

logger = logging.getLogger(__name__)


class QueryOptimizer:
    """
    Optimizes query execution through caching and pattern recognition.
    """
    
    def __init__(
        self,
        cache_ttl_minutes: int = 60,
        max_cache_entries: int = 1000,
        enable_similar_query_detection: bool = True
    ):
        """
        Initialize query optimizer.
        
        Args:
            cache_ttl_minutes: Cache time-to-live in minutes
            max_cache_entries: Maximum number of cached results
            enable_similar_query_detection: Enable similar query detection
        """
        self.cache_ttl_minutes = cache_ttl_minutes
        self.max_cache_entries = max_cache_entries
        self.enable_similar_query_detection = enable_similar_query_detection
        
        # Cache storage: {cache_key: {result, timestamp, hits}}
        self._cache: Dict[str, Dict[str, Any]] = {}
        
        # Performance metrics
        self._metrics = {
            "total_queries": 0,
            "cache_hits": 0,
            "cache_misses": 0,
            "avg_execution_time_ms": 0,
            "query_patterns": defaultdict(int)
        }
    
    def get_cache_key(
        self,
        query_text: str,
        document_id: int,
        sheet_name: str
    ) -> str:
        """
        Generate cache key for a query.
        
        Args:
            query_text: Natural language query
            document_id: Document ID
            sheet_name: Sheet name
        
        Returns:
            Cache key hash
        """
        # Normalize query text
        normalized_query = query_text.lower().strip()
        
        # Create composite key
        key_data = {
            "query": normalized_query,
            "document_id": document_id,
            "sheet_name": sheet_name
        }
        
        # Generate hash
        key_string = json.dumps(key_data, sort_keys=True)
        cache_key = hashlib.sha256(key_string.encode()).hexdigest()
        
        return cache_key
    
    def get_cached_result(
        self,
        cache_key: str
    ) -> Optional[Dict[str, Any]]:
        """
        Retrieve cached query result if available and not expired.
        
        Args:
            cache_key: Cache key
        
        Returns:
            Cached result or None
        """
        if cache_key not in self._cache:
            self._metrics["cache_misses"] += 1
            return None
        
        cached_entry = self._cache[cache_key]
        cache_time = cached_entry["timestamp"]
        expiry_time = cache_time + timedelta(minutes=self.cache_ttl_minutes)
        
        # Check if expired
        if datetime.now() > expiry_time:
            logger.debug(f"Cache entry expired: {cache_key[:8]}...")
            del self._cache[cache_key]
            self._metrics["cache_misses"] += 1
            return None
        
        # Update hit count
        cached_entry["hits"] += 1
        self._metrics["cache_hits"] += 1
        
        logger.info(f"Cache hit for key: {cache_key[:8]}... (hits: {cached_entry['hits']})")
        return cached_entry["result"]
    
    def cache_result(
        self,
        cache_key: str,
        result: Dict[str, Any]
    ) -> None:
        """
        Cache query result.
        
        Args:
            cache_key: Cache key
            result: Result to cache
        """
        # Check cache size limit
        if len(self._cache) >= self.max_cache_entries:
            self._evict_oldest_entry()
        
        self._cache[cache_key] = {
            "result": result,
            "timestamp": datetime.now(),
            "hits": 0
        }
        
        logger.debug(f"Cached result for key: {cache_key[:8]}...")
    
    def _evict_oldest_entry(self) -> None:
        """Evict oldest cache entry based on LRU."""
        if not self._cache:
            return
        
        # Find entry with oldest timestamp and lowest hits
        oldest_key = min(
            self._cache.keys(),
            key=lambda k: (self._cache[k]["hits"], self._cache[k]["timestamp"])
        )
        
        del self._cache[oldest_key]
        logger.debug(f"Evicted cache entry: {oldest_key[:8]}...")
    
    def find_similar_queries(
        self,
        query_text: str,
        document_id: int,
        sheet_name: str,
        similarity_threshold: float = 0.8
    ) -> List[Dict[str, Any]]:
        """
        Find similar cached queries using text similarity.
        
        Args:
            query_text: Query text to match
            document_id: Document ID
            sheet_name: Sheet name
            similarity_threshold: Minimum similarity score (0-1)
        
        Returns:
            List of similar cached queries
        """
        if not self.enable_similar_query_detection:
            return []
        
        similar_queries = []
        normalized_query = query_text.lower().strip()
        query_words = set(normalized_query.split())
        
        for cache_key, cached_entry in self._cache.items():
            # Skip expired entries
            cache_time = cached_entry["timestamp"]
            expiry_time = cache_time + timedelta(minutes=self.cache_ttl_minutes)
            if datetime.now() > expiry_time:
                continue
            
            # Simple word-based similarity
            cached_result = cached_entry["result"]
            if "query_text" in cached_result:
                cached_query = cached_result["query_text"].lower().strip()
                cached_words = set(cached_query.split())
                
                # Calculate Jaccard similarity
                intersection = query_words & cached_words
                union = query_words | cached_words
                
                if union:
                    similarity = len(intersection) / len(union)
                    
                    if similarity >= similarity_threshold:
                        similar_queries.append({
                            "query_text": cached_result.get("query_text"),
                            "similarity": similarity,
                            "cache_key": cache_key,
                            "hits": cached_entry["hits"]
                        })
        
        # Sort by similarity and hits
        similar_queries.sort(key=lambda x: (x["similarity"], x["hits"]), reverse=True)
        
        return similar_queries[:5]  # Return top 5
    
    def record_query_execution(
        self,
        query_text: str,
        execution_time_ms: int,
        success: bool
    ) -> None:
        """
        Record query execution metrics.
        
        Args:
            query_text: Query text
            execution_time_ms: Execution time in milliseconds
            success: Whether execution succeeded
        """
        self._metrics["total_queries"] += 1
        
        # Update average execution time
        current_avg = self._metrics["avg_execution_time_ms"]
        total_queries = self._metrics["total_queries"]
        
        new_avg = ((current_avg * (total_queries - 1)) + execution_time_ms) / total_queries
        self._metrics["avg_execution_time_ms"] = int(new_avg)
        
        # Track query patterns
        if success:
            # Extract pattern from query (simple keyword extraction)
            keywords = self._extract_keywords(query_text)
            pattern = " ".join(sorted(keywords))
            self._metrics["query_patterns"][pattern] += 1
    
    def _extract_keywords(self, query_text: str) -> List[str]:
        """Extract keywords from query text."""
        # Common analysis keywords
        keywords = [
            "average", "mean", "sum", "total", "count", "max", "min",
            "group", "filter", "sort", "top", "bottom", "unique",
            "percentage", "ratio", "trend", "correlation"
        ]
        
        query_lower = query_text.lower()
        found_keywords = [kw for kw in keywords if kw in query_lower]
        
        return found_keywords
    
    def get_metrics(self) -> Dict[str, Any]:
        """
        Get optimizer performance metrics.
        
        Returns:
            Metrics dictionary
        """
        cache_hit_rate = 0.0
        total_cached_queries = self._metrics["cache_hits"] + self._metrics["cache_misses"]
        if total_cached_queries > 0:
            cache_hit_rate = (self._metrics["cache_hits"] / total_cached_queries) * 100
        
        return {
            "total_queries": self._metrics["total_queries"],
            "cache_hits": self._metrics["cache_hits"],
            "cache_misses": self._metrics["cache_misses"],
            "cache_hit_rate": round(cache_hit_rate, 2),
            "cache_size": len(self._cache),
            "cache_capacity": self.max_cache_entries,
            "avg_execution_time_ms": self._metrics["avg_execution_time_ms"],
            "top_query_patterns": dict(
                sorted(
                    self._metrics["query_patterns"].items(),
                    key=lambda x: x[1],
                    reverse=True
                )[:10]
            )
        }
    
    def clear_cache(self) -> int:
        """
        Clear all cached results.
        
        Returns:
            Number of entries cleared
        """
        count = len(self._cache)
        self._cache.clear()
        logger.info(f"Cleared {count} cache entries")
        return count
    
    def invalidate_document_cache(
        self,
        document_id: int
    ) -> int:
        """
        Invalidate all cache entries for a document.
        
        Args:
            document_id: Document ID
        
        Returns:
            Number of entries invalidated
        """
        # Note: This is a simple implementation
        # In production, you'd want to store document_id with cache entries
        count = 0
        keys_to_delete = []
        
        for cache_key, cached_entry in self._cache.items():
            # Check if result contains document_id
            result = cached_entry.get("result", {})
            if result.get("document_id") == document_id:
                keys_to_delete.append(cache_key)
        
        for key in keys_to_delete:
            del self._cache[key]
            count += 1
        
        logger.info(f"Invalidated {count} cache entries for document {document_id}")
        return count
    
    def get_cache_statistics(self) -> Dict[str, Any]:
        """Get detailed cache statistics."""
        if not self._cache:
            return {
                "total_entries": 0,
                "avg_hits_per_entry": 0,
                "most_hit_entries": []
            }
        
        total_hits = sum(entry["hits"] for entry in self._cache.values())
        avg_hits = total_hits / len(self._cache) if self._cache else 0
        
        # Find most hit entries
        sorted_entries = sorted(
            self._cache.items(),
            key=lambda x: x[1]["hits"],
            reverse=True
        )[:10]
        
        most_hit = [
            {
                "cache_key": key[:8] + "...",
                "hits": entry["hits"],
                "age_minutes": int((datetime.now() - entry["timestamp"]).total_seconds() / 60)
            }
            for key, entry in sorted_entries
        ]
        
        return {
            "total_entries": len(self._cache),
            "avg_hits_per_entry": round(avg_hits, 2),
            "most_hit_entries": most_hit
        }
