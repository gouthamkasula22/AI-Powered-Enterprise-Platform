"""
Unit tests for Query Optimizer
"""

import pytest
from datetime import datetime, timedelta
from src.application.use_cases.excel.query_optimizer import QueryOptimizer


class TestQueryOptimizer:
    """Tests for QueryOptimizer class."""
    
    def setup_method(self):
        """Setup test fixtures."""
        self.optimizer = QueryOptimizer(
            cache_ttl_minutes=60,
            max_cache_entries=10
        )
    
    def test_cache_key_generation(self):
        """Test that cache keys are generated consistently."""
        key1 = self.optimizer.get_cache_key(
            query_text="What is the average sales?",
            document_id=1,
            sheet_name="Sheet1"
        )
        
        key2 = self.optimizer.get_cache_key(
            query_text="what is the average sales?",  # Different case
            document_id=1,
            sheet_name="Sheet1"
        )
        
        # Should generate same key (case-insensitive)
        assert key1 == key2
        assert len(key1) == 64  # SHA256 hash length
    
    def test_cache_miss(self):
        """Test cache miss returns None."""
        cache_key = "nonexistent_key"
        result = self.optimizer.get_cached_result(cache_key)
        
        assert result is None
        assert self.optimizer._metrics["cache_misses"] == 1
    
    def test_cache_hit(self):
        """Test successful cache hit."""
        cache_key = self.optimizer.get_cache_key(
            query_text="test query",
            document_id=1,
            sheet_name="Sheet1"
        )
        
        # Cache a result
        test_result = {
            "code": "result = df['Sales'].mean()",
            "result": {"type": "scalar", "value": 100}
        }
        self.optimizer.cache_result(cache_key, test_result)
        
        # Retrieve cached result
        cached = self.optimizer.get_cached_result(cache_key)
        
        assert cached is not None
        assert cached["code"] == test_result["code"]
        assert self.optimizer._metrics["cache_hits"] == 1
    
    def test_cache_expiration(self):
        """Test that expired cache entries are not returned."""
        # Create optimizer with very short TTL
        optimizer = QueryOptimizer(cache_ttl_minutes=0)
        
        cache_key = optimizer.get_cache_key(
            query_text="test query",
            document_id=1,
            sheet_name="Sheet1"
        )
        
        # Cache a result
        test_result = {"code": "result = df['Sales'].mean()"}
        optimizer.cache_result(cache_key, test_result)
        
        # Manually set timestamp to past
        optimizer._cache[cache_key]["timestamp"] = datetime.now() - timedelta(minutes=5)
        
        # Should return None (expired)
        cached = optimizer.get_cached_result(cache_key)
        assert cached is None
    
    def test_cache_size_limit(self):
        """Test that cache respects max size limit."""
        optimizer = QueryOptimizer(max_cache_entries=3)
        
        # Add 5 entries (exceeds limit of 3)
        for i in range(5):
            cache_key = optimizer.get_cache_key(
                query_text=f"query {i}",
                document_id=1,
                sheet_name="Sheet1"
            )
            optimizer.cache_result(cache_key, {"code": f"code {i}"})
        
        # Should only have 3 entries (evicted oldest)
        assert len(optimizer._cache) == 3
    
    def test_query_execution_metrics(self):
        """Test that query execution is recorded in metrics."""
        self.optimizer.record_query_execution(
            query_text="What is the average sales?",
            execution_time_ms=150,
            success=True
        )
        
        self.optimizer.record_query_execution(
            query_text="Show top 10 products",
            execution_time_ms=200,
            success=True
        )
        
        metrics = self.optimizer.get_metrics()
        
        assert metrics["total_queries"] == 2
        assert metrics["avg_execution_time_ms"] == 175  # (150+200)/2
    
    def test_find_similar_queries(self):
        """Test similar query detection."""
        # Cache some queries
        queries = [
            "What is the average sales amount?",
            "Show me average sales",
            "Calculate total revenue"
        ]
        
        for i, query in enumerate(queries):
            cache_key = self.optimizer.get_cache_key(
                query_text=query,
                document_id=1,
                sheet_name="Sheet1"
            )
            self.optimizer.cache_result(cache_key, {
                "code": f"code {i}",
                "query_text": query
            })
        
        # Find similar to "average sales"
        similar = self.optimizer.find_similar_queries(
            query_text="average sales calculation",
            document_id=1,
            sheet_name="Sheet1",
            similarity_threshold=0.3
        )
        
        assert len(similar) > 0
        assert all("similarity" in s for s in similar)
    
    def test_clear_cache(self):
        """Test cache clearing."""
        # Add some entries
        for i in range(3):
            cache_key = self.optimizer.get_cache_key(
                query_text=f"query {i}",
                document_id=1,
                sheet_name="Sheet1"
            )
            self.optimizer.cache_result(cache_key, {"code": f"code {i}"})
        
        count = self.optimizer.clear_cache()
        
        assert count == 3
        assert len(self.optimizer._cache) == 0
    
    def test_cache_hit_rate_calculation(self):
        """Test cache hit rate is calculated correctly."""
        cache_key = self.optimizer.get_cache_key(
            query_text="test",
            document_id=1,
            sheet_name="Sheet1"
        )
        
        # Cache a result
        self.optimizer.cache_result(cache_key, {"code": "test"})
        
        # 2 hits
        result1 = self.optimizer.get_cached_result(cache_key)
        result2 = self.optimizer.get_cached_result(cache_key)
        
        # 1 miss
        result3 = self.optimizer.get_cached_result("nonexistent")
        
        assert result1 is not None
        assert result2 is not None
        assert result3 is None
        
        metrics = self.optimizer.get_metrics()
        
        # Hit rate = 2/(2+1) * 100 = 66.67%
        assert metrics["cache_hits"] == 2
        assert metrics["cache_misses"] == 1
        assert 66 <= metrics["cache_hit_rate"] <= 67
    
    def test_query_pattern_tracking(self):
        """Test that query patterns are tracked."""
        queries = [
            "What is the average sales?",
            "Calculate average revenue",
            "Show me the sum of profits",
            "Total sum of expenses"
        ]
        
        for query in queries:
            self.optimizer.record_query_execution(
                query_text=query,
                execution_time_ms=100,
                success=True
            )
        
        metrics = self.optimizer.get_metrics()
        patterns = metrics["top_query_patterns"]
        
        # Should detect "average" and "sum" patterns
        assert len(patterns) > 0
