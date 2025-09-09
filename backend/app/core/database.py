"""
Database configuration and session management with enhanced query logging and monitoring
"""
import logging
import time
import json
import hashlib
from typing import AsyncGenerator, Optional, Dict, Any, List
from contextlib import asynccontextmanager
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker, AsyncEngine
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import text, event, func
from sqlalchemy.engine import Engine
from sqlalchemy.pool import StaticPool
from app.core.config import settings

logger = logging.getLogger(__name__)

# Custom formatter for SQL queries
class QueryLogger:
    """Enhanced query logger with detailed information"""
    
    @staticmethod
    def format_query(statement: Any, params: Any = None) -> str:
        """Format SQL query for logging"""
        try:
            if hasattr(statement, 'statement'):
                # SQLAlchemy query object
                sql = str(statement.statement.compile(compile_kwargs={"literal_binds": True}))
            elif hasattr(statement, 'compile'):
                # SQLAlchemy statement
                sql = str(statement.compile(compile_kwargs={"literal_binds": True}))
            else:
                # Raw SQL string
                sql = str(statement)
            
            # Include parameters if available
            if params:
                sql += f" -- Params: {params}"
            
            # Truncate very long queries
            if len(sql) > 500:
                sql = sql[:500] + "... (truncated)"
            
            return sql
        except Exception:
            # Fallback to basic string representation
            return str(statement)[:500]
    
    @staticmethod
    def get_query_hash(query: str) -> str:
        """Generate a hash for query identification"""
        # Remove parameters and whitespace for consistent hashing
        normalized_query = ' '.join(query.split())
        return hashlib.md5(normalized_query.encode()).hexdigest()[:8]
    
    @staticmethod
    def get_query_type(query: str) -> str:
        """Determine query type (SELECT, INSERT, UPDATE, DELETE)"""
        query_upper = query.upper().strip()
        if query_upper.startswith('SELECT'):
            return 'SELECT'
        elif query_upper.startswith('INSERT'):
            return 'INSERT'
        elif query_upper.startswith('UPDATE'):
            return 'UPDATE'
        elif query_upper.startswith('DELETE'):
            return 'DELETE'
        else:
            return 'OTHER'

query_logger = QueryLogger()

# Query Statistics Tracker
class QueryStats:
    """Track query statistics for monitoring"""
    
    def __init__(self):
        self.queries: Dict[str, Dict[str, Any]] = {}
        self.session_queries: List[Dict[str, Any]] = []
    
    def record_query(self, query_hash: str, query: str, execution_time: float, query_type: str):
        """Record query statistics"""
        if query_hash not in self.queries:
            self.queries[query_hash] = {
                "query": query[:200],  # Store truncated version
                "type": query_type,
                "count": 0,
                "total_time": 0,
                "min_time": float('inf'),
                "max_time": 0,
                "avg_time": 0,
                "last_execution": None,
                "slow_count": 0  # Count of slow executions
            }
        
        stats = self.queries[query_hash]
        stats["count"] += 1
        stats["total_time"] += execution_time
        stats["min_time"] = min(stats["min_time"], execution_time)
        stats["max_time"] = max(stats["max_time"], execution_time)
        stats["avg_time"] = stats["total_time"] / stats["count"]
        stats["last_execution"] = time.time()
        
        # Track slow queries
        if execution_time > 1.0:
            stats["slow_count"] += 1
        
        # Keep recent queries for session tracking
        self.session_queries.append({
            "hash": query_hash,
            "query": query[:100],
            "time": execution_time,
            "timestamp": time.time(),
            "type": query_type
        })
        
        # Keep only last 1000 queries to prevent memory issues
        if len(self.session_queries) > 1000:
            self.session_queries = self.session_queries[-1000:]
    
    def get_slow_queries(self, threshold: float = 1.0) -> List[Dict]:
        """Get queries with average time above threshold"""
        slow_queries = []
        for query_hash, stats in self.queries.items():
            if stats["avg_time"] > threshold or stats["slow_count"] > 0:
                slow_queries.append({
                    "hash": query_hash,
                    "query": stats["query"],
                    "type": stats["type"],
                    "avg_time": stats["avg_time"],
                    "count": stats["count"],
                    "max_time": stats["max_time"],
                    "slow_count": stats["slow_count"]
                })
        return sorted(slow_queries, key=lambda x: x["avg_time"], reverse=True)
    
    def get_most_frequent(self, limit: int = 10) -> List[Dict]:
        """Get most frequently executed queries"""
        sorted_queries = sorted(
            self.queries.items(), 
            key=lambda x: x[1]["count"], 
            reverse=True
        )
        return [
            {
                "hash": hash_key,
                "query": stats["query"],
                "type": stats["type"],
                "count": stats["count"],
                "avg_time": stats["avg_time"]
            }
            for hash_key, stats in sorted_queries[:limit]
        ]
    
    def get_recent_queries(self, limit: int = 50) -> List[Dict]:
        """Get most recent queries"""
        return self.session_queries[-limit:]

# Global query stats instance
query_stats = QueryStats()

# Enhanced database session with query tracking
class TrackedAsyncSession(AsyncSession):
    """Custom session that tracks query execution with detailed logging"""
    
    async def execute(self, statement, parameters=None, execution_options=None, bind_arguments=None, _parent_execute_state=None, _add_event=None):
        """Execute with comprehensive timing and logging"""
        # Format the query for logging
        query_str = query_logger.format_query(statement, parameters)
        query_hash = query_logger.get_query_hash(query_str)
        query_type = query_logger.get_query_type(query_str)
        
        # Start timing
        start_time = time.time()
        
        try:
            # Execute the query using parent's execute method
            result = await super().execute(
                statement, 
                parameters, 
                execution_options, 
                bind_arguments, 
                _parent_execute_state, 
                _add_event
            )
            
            # Calculate execution time
            execution_time = time.time() - start_time
            
            # Record statistics
            query_stats.record_query(query_hash, query_str, execution_time, query_type)
            
            # Log based on execution time and settings
            if execution_time > 2.0:  # Critical slow query
                logger.error(
                    f"🚨 CRITICAL SLOW QUERY [Hash: {query_hash}] [Type: {query_type}] "
                    f"[Time: {execution_time:.3f}s]\n"
                    f"Query: {query_str}\n"
                    f"🔧 IMMEDIATE OPTIMIZATION REQUIRED!"
                )
                await self._log_slow_query(query_hash, query_str, execution_time, "CRITICAL")
                
            elif execution_time > 1.0:  # Standard slow query
                logger.warning(
                    f"🐌 SLOW QUERY DETECTED [Hash: {query_hash}] [Type: {query_type}] "
                    f"[Time: {execution_time:.3f}s]\n"
                    f"Query: {query_str}\n"
                    f"💡 Consider optimizing this query!"
                )
                await self._log_slow_query(query_hash, query_str, execution_time, "SLOW")
                
            elif execution_time > 0.5:  # Warning threshold
                logger.info(
                    f"⚠️ Query approaching slow threshold [Hash: {query_hash}] [Type: {query_type}] "
                    f"[Time: {execution_time:.3f}s]: {query_str[:100]}..."
                )
            elif settings.DB_ECHO:  # Debug mode
                logger.debug(
                    f"✅ Query executed [Hash: {query_hash}] [Type: {query_type}] "
                    f"[Time: {execution_time:.3f}s]: {query_str[:100]}..."
                )
            
            return result
            
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(
                f"❌ Query failed [Hash: {query_hash}] [Type: {query_type}] "
                f"[Time: {execution_time:.3f}s]\n"
                f"Query: {query_str}\n"
                f"Error: {str(e)}"
            )
            
            # Log failed query for analysis
            await self._log_failed_query(query_hash, query_str, execution_time, str(e))
            raise
    
    async def _log_slow_query(self, query_hash: str, query: str, execution_time: float, severity: str):
        """Log slow query to file for analysis"""
        try:
            slow_query_data = {
                "timestamp": time.time(),
                "hash": query_hash,
                "severity": severity,
                "execution_time": execution_time,
                "query": query,
                "environment": settings.ENVIRONMENT,
                "recommendations": self._get_query_recommendations(query)
            }
            
            with open("slow_queries.log", "a", encoding="utf-8") as f:
                f.write(json.dumps(slow_query_data) + "\n")
        except Exception as e:
            logger.error(f"Failed to log slow query: {e}")
    
    async def _log_failed_query(self, query_hash: str, query: str, execution_time: float, error: str):
        """Log failed query for debugging"""
        try:
            failed_query_data = {
                "timestamp": time.time(),
                "hash": query_hash,
                "execution_time": execution_time,
                "query": query,
                "error": error,
                "environment": settings.ENVIRONMENT
            }
            
            with open("failed_queries.log", "a", encoding="utf-8") as f:
                f.write(json.dumps(failed_query_data) + "\n")
        except Exception as e:
            logger.error(f"Failed to log failed query: {e}")
    
    def _get_query_recommendations(self, query: str) -> List[str]:
        """Generate optimization recommendations based on query pattern"""
        recommendations = []
        query_upper = query.upper()
        
        if "SELECT *" in query_upper:
            recommendations.append("Avoid SELECT *, specify only needed columns")
        
        if "LEFT JOIN" in query_upper and "WHERE" not in query_upper:
            recommendations.append("Consider adding WHERE clause to filter JOIN results")
        
        if "ORDER BY" in query_upper and "LIMIT" not in query_upper:
            recommendations.append("Consider adding LIMIT when using ORDER BY")
        
        if "LIKE '%'" in query_upper:
            recommendations.append("Leading wildcard LIKE patterns can't use indexes")
        
        if query_upper.count("JOIN") > 3:
            recommendations.append("Complex joins detected, consider query restructuring")
        
        return recommendations

# Database connection parameters based on environment
def get_engine_params() -> dict:
    """Get database engine parameters based on environment"""
    base_params = {
        "echo": settings.DB_ECHO,
        "echo_pool": settings.DB_ECHO_POOL,
        "future": True,
        "pool_pre_ping": settings.DB_POOL_PRE_PING,
        "pool_recycle": settings.DB_POOL_RECYCLE,
        "pool_timeout": settings.DB_POOL_TIMEOUT,
        "connect_args": {
            "command_timeout": settings.DB_COMMAND_TIMEOUT,
            "server_settings": {
                "application_name": f"{settings.APP_NAME}_{settings.ENVIRONMENT}",
                "statement_timeout": str(settings.DB_STATEMENT_TIMEOUT),
            }
        }
    }
    
    # Production vs Development settings
    if settings.ENVIRONMENT == "production":
        base_params.update({
            "pool_size": settings.DB_POOL_SIZE,
            "max_overflow": settings.DB_MAX_OVERFLOW,
            # Remove poolclass for async engines
        })
    else:
        base_params.update({
            "pool_size": settings.DB_POOL_SIZE,
            "max_overflow": settings.DB_MAX_OVERFLOW,
            # Remove poolclass for async engines  
        })
    
    return base_params

# Create async engine with optimized configuration
engine = create_async_engine(
    settings.DATABASE_URL,
    **get_engine_params()
)

# Remove old event listeners and use our custom session tracking instead
# (The TrackedAsyncSession handles all query monitoring internally)

# Create optimized async session factory with our custom session class
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=TrackedAsyncSession,  # Use our enhanced session class
    expire_on_commit=False,
    autoflush=False,
    autocommit=False,
)

class Base(DeclarativeBase):
    """Base class for all database models with enhanced metadata"""
    pass

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Enhanced database session dependency with comprehensive error handling
    
    Provides:
    - Automatic transaction management
    - Connection pool monitoring
    - Session lifecycle management
    - Error handling and rollback
    """
    session_start_time = time.time()
    session = None
    
    try:
        session = AsyncSessionLocal()
        logger.debug(f"Database session created in {time.time() - session_start_time:.3f}s")
        
        yield session
        
        # Commit transaction if no exceptions occurred
        await session.commit()
        logger.debug("Database transaction committed successfully")
        
    except Exception as e:
        if session:
            await session.rollback()
            logger.error(f"Database transaction rolled back due to error: {e}")
        raise
        
    finally:
        if session:
            await session.close()
            session_duration = time.time() - session_start_time
            logger.debug(f"Database session closed after {session_duration:.3f}s")

async def get_db_session() -> AsyncSession:
    """
    Get a database session for manual transaction management
    
    Note: Caller is responsible for closing the session and handling transactions
    """
    return AsyncSessionLocal()

async def test_database_connection() -> bool:
    """
    Enhanced database connectivity test with detailed diagnostics
    """
    start_time = time.time()
    try:
        async with engine.begin() as conn:
            # Test basic connectivity
            result = await conn.execute(text("SELECT 1 as test"))
            test_value = result.scalar()
            
            # Test database version and settings
            version_result = await conn.execute(text("SELECT version()"))
            db_version = version_result.scalar()
            
            connection_time = time.time() - start_time
            
            logger.info(f"✅ Database connection successful in {connection_time:.3f}s")
            logger.info(f"Database version: {db_version}")
            logger.debug(f"Test query result: {test_value}")
            
            return True
            
    except Exception as e:
        connection_time = time.time() - start_time
        logger.error(f"❌ Database connection failed after {connection_time:.3f}s: {e}")
        return False

async def get_database_stats() -> dict:
    """Get database connection pool statistics"""
    try:
        pool = engine.pool
        return {
            "pool_size": pool.size(),
            "checked_in": pool.checkedin(),
            "checked_out": pool.checkedout(),
            "overflow": pool.overflow(),
            "invalid": pool.invalid(),
        }
    except Exception as e:
        logger.error(f"Failed to get database stats: {e}")
        return {}

async def check_database_health() -> dict:
    """
    Comprehensive database health check
    """
    health_data = {
        "status": "unknown",
        "connection_test": False,
        "response_time_ms": 0,
        "pool_stats": {},
        "timestamp": time.time()
    }
    
    start_time = time.time()
    
    try:
        # Test connection
        health_data["connection_test"] = await test_database_connection()
        health_data["response_time_ms"] = round((time.time() - start_time) * 1000, 2)
        
        # Get pool statistics
        health_data["pool_stats"] = await get_database_stats()
        
        # Determine overall status
        if health_data["connection_test"] and health_data["response_time_ms"] < 1000:
            health_data["status"] = "healthy"
        elif health_data["connection_test"]:
            health_data["status"] = "degraded"
        else:
            health_data["status"] = "unhealthy"
            
    except Exception as e:
        health_data["status"] = "error"
        health_data["error"] = str(e)
        logger.error(f"Database health check failed: {e}")
    
    return health_data

async def create_database_tables():
    """
    Create all database tables with enhanced logging
    """
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("✅ Database tables created/verified successfully")
    except Exception as e:
        logger.error(f"❌ Failed to create database tables: {e}")
        raise

async def close_database_connections():
    """
    Gracefully close all database connections with cleanup
    """
    try:
        # Get final stats before closing
        final_stats = await get_database_stats()
        logger.info(f"Closing database connections. Final pool stats: {final_stats}")
        
        await engine.dispose()
        logger.info("✅ Database connections closed successfully")
        
    except Exception as e:
        logger.error(f"Error closing database connections: {e}")
        raise

# Query Monitoring Functions
async def get_query_statistics() -> Dict[str, Any]:
    """Get comprehensive query statistics"""
    return {
        "slow_queries": query_stats.get_slow_queries(),
        "frequent_queries": query_stats.get_most_frequent(),
        "recent_queries": query_stats.get_recent_queries(),
        "total_queries": len(query_stats.queries),
        "unique_queries": len(query_stats.queries),
        "session_queries": len(query_stats.session_queries)
    }

async def get_slow_query_analysis() -> Dict[str, Any]:
    """Analyze slow queries from log files"""
    slow_queries = []
    failed_queries = []
    
    try:
        # Read slow queries log
        try:
            with open("slow_queries.log", "r", encoding="utf-8") as f:
                for line in f.readlines()[-100:]:  # Last 100 entries
                    try:
                        slow_queries.append(json.loads(line))
                    except json.JSONDecodeError:
                        continue
        except FileNotFoundError:
            pass
        
        # Read failed queries log
        try:
            with open("failed_queries.log", "r", encoding="utf-8") as f:
                for line in f.readlines()[-50:]:  # Last 50 entries
                    try:
                        failed_queries.append(json.loads(line))
                    except json.JSONDecodeError:
                        continue
        except FileNotFoundError:
            pass
        
        # Group slow queries by hash
        slow_by_hash = {}
        for query in slow_queries:
            hash_key = query["hash"]
            if hash_key not in slow_by_hash:
                slow_by_hash[hash_key] = {
                    "query": query["query"],
                    "occurrences": 0,
                    "total_time": 0,
                    "max_time": 0,
                    "recommendations": query.get("recommendations", [])
                }
            slow_by_hash[hash_key]["occurrences"] += 1
            slow_by_hash[hash_key]["total_time"] += query["execution_time"]
            slow_by_hash[hash_key]["max_time"] = max(
                slow_by_hash[hash_key]["max_time"], 
                query["execution_time"]
            )
        
        # Calculate averages
        for data in slow_by_hash.values():
            data["avg_time"] = data["total_time"] / data["occurrences"]
        
        return {
            "slow_queries_by_hash": slow_by_hash,
            "recent_slow_queries": slow_queries[-20:],  # Last 20
            "recent_failed_queries": failed_queries[-10:],  # Last 10
            "total_slow_queries": len(slow_queries),
            "total_failed_queries": len(failed_queries)
        }
    
    except Exception as e:
        logger.error(f"Error analyzing slow queries: {e}")
        return {
            "error": str(e),
            "slow_queries_by_hash": {},
            "recent_slow_queries": [],
            "recent_failed_queries": [],
            "total_slow_queries": 0,
            "total_failed_queries": 0
        }

def clear_query_logs():
    """Clear query log files (use with caution)"""
    try:
        with open("slow_queries.log", "w") as f:
            f.write("")
        with open("failed_queries.log", "w") as f:
            f.write("")
        logger.info("Query log files cleared")
    except Exception as e:
        logger.error(f"Error clearing query logs: {e}")

# Pagination utility functions
async def paginate_query(
    session: AsyncSession,
    query,
    page: int = 1,
    per_page: int = 20,
    max_per_page: int = 100
) -> Dict[str, Any]:
    """
    Enhanced pagination utility with query optimization
    
    Args:
        session: Database session
        query: SQLAlchemy query object
        page: Page number (1-based)
        per_page: Items per page
        max_per_page: Maximum allowed items per page
    
    Returns:
        Dictionary with paginated results and metadata
    """
    # Validate and limit per_page
    per_page = min(per_page, max_per_page)
    page = max(page, 1)
    
    # Calculate offset
    offset = (page - 1) * per_page
    
    # Get total count (more efficient count query)
    count_query = query.statement.with_only_columns(func.count()).order_by(None)
    total = await session.scalar(count_query)
    
    # Calculate pagination metadata
    pages = (total + per_page - 1) // per_page if total > 0 else 0
    
    # Get paginated results
    paginated_query = query.limit(per_page).offset(offset)
    result = await session.execute(paginated_query)
    items = result.scalars().all()
    
    return {
        "items": items,
        "pagination": {
            "page": page,
            "per_page": per_page,
            "total": total,
            "pages": pages,
            "has_next": page < pages,
            "has_prev": page > 1,
            "next_page": page + 1 if page < pages else None,
            "prev_page": page - 1 if page > 1 else None
        }
    }
