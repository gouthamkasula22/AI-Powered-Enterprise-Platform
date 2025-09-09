"""
Database Monitoring API Endpoints

Provides endpoints for monitoring database performance, query statistics,
and slow query analysis for the User Authentication System.
"""

from fastapi import APIRouter, Depends, Query, HTTPException, status
from typing import Dict, Any, List, Optional
import json
from datetime import datetime, timedelta

from app.core.database import (
    get_query_statistics,
    get_slow_query_analysis,
    clear_query_logs,
    query_stats
)

router = APIRouter(prefix="/api/monitoring", tags=["Database Monitoring"])

@router.get("/query-stats", response_model=Dict[str, Any])
async def get_query_statistics_endpoint():
    """
    Get comprehensive query execution statistics
    
    Returns detailed information about:
    - Slow queries (>1 second)
    - Most frequently executed queries
    - Recent query history
    - Overall query metrics
    """
    try:
        stats = await get_query_statistics()
        return {
            "status": "success",
            "data": stats,
            "summary": {
                "total_unique_queries": stats["unique_queries"],
                "slow_query_count": len([q for q in stats["slow_queries"] if q["slow_count"] > 0]),
                "most_frequent_query": stats["frequent_queries"][0] if stats["frequent_queries"] else None
            }
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get query statistics: {str(e)}"
        )

@router.get("/slow-queries", response_model=Dict[str, Any])
async def get_slow_queries_endpoint(
    threshold: float = Query(1.0, description="Slow query threshold in seconds", ge=0.1),
    limit: int = Query(50, description="Maximum number of results", le=1000)
):
    """
    Get detailed analysis of slow queries
    
    Args:
        threshold: Minimum execution time to consider a query slow (seconds)
        limit: Maximum number of slow queries to return
    
    Returns:
        Detailed slow query analysis with optimization recommendations
    """
    try:
        # Get current session slow queries
        slow_queries = query_stats.get_slow_queries(threshold)[:limit]
        
        # Get historical analysis from log files
        historical_analysis = await get_slow_query_analysis()
        
        return {
            "status": "success",
            "threshold_seconds": threshold,
            "data": {
                "current_session": slow_queries,
                "historical_analysis": historical_analysis,
                "recommendations": _generate_global_recommendations(slow_queries)
            }
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get slow queries: {str(e)}"
        )

@router.get("/frequent-queries", response_model=Dict[str, Any])
async def get_frequent_queries_endpoint(
    limit: int = Query(20, description="Number of queries to return", le=100)
):
    """
    Get most frequently executed queries
    
    Useful for identifying:
    - Queries that would benefit from caching
    - Common patterns that could be optimized
    - Potential candidates for database indexing
    """
    try:
        frequent_queries = query_stats.get_most_frequent(limit)
        
        return {
            "status": "success",
            "data": frequent_queries,
            "insights": {
                "top_query_count": frequent_queries[0]["count"] if frequent_queries else 0,
                "total_executions": sum(q["count"] for q in frequent_queries),
                "avg_frequency": sum(q["count"] for q in frequent_queries) / len(frequent_queries) if frequent_queries else 0
            }
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get frequent queries: {str(e)}"
        )

@router.get("/recent-queries", response_model=Dict[str, Any])
async def get_recent_queries_endpoint(
    limit: int = Query(50, description="Number of recent queries to return", le=200)
):
    """
    Get recently executed queries
    
    Useful for:
    - Real-time monitoring
    - Debugging current issues
    - Understanding application query patterns
    """
    try:
        recent_queries = query_stats.get_recent_queries(limit)
        
        # Calculate some basic statistics
        if recent_queries:
            times = [q["time"] for q in recent_queries]
            avg_time = sum(times) / len(times)
            max_time = max(times)
            slow_count = len([t for t in times if t > 1.0])
        else:
            avg_time = max_time = slow_count = 0
        
        return {
            "status": "success",
            "data": recent_queries,
            "statistics": {
                "total_queries": len(recent_queries),
                "average_time": round(avg_time, 3),
                "max_time": round(max_time, 3),
                "slow_queries": slow_count,
                "query_types": _count_query_types(recent_queries)
            }
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get recent queries: {str(e)}"
        )

@router.get("/performance-summary", response_model=Dict[str, Any])
async def get_performance_summary():
    """
    Get overall database performance summary
    
    Provides a high-level overview of database performance including:
    - Query execution statistics
    - Performance trends
    - Optimization recommendations
    """
    try:
        stats = await get_query_statistics()
        slow_analysis = await get_slow_query_analysis()
        
        # Calculate performance metrics
        total_queries = stats["total_queries"]
        slow_queries = len([q for q in stats["slow_queries"] if q["slow_count"] > 0])
        performance_score = max(0, 100 - (slow_queries / total_queries * 100 if total_queries > 0 else 0))
        
        return {
            "status": "success",
            "performance_score": round(performance_score, 1),
            "summary": {
                "total_queries_executed": total_queries,
                "unique_query_patterns": stats["unique_queries"],
                "slow_queries_detected": slow_queries,
                "failed_queries": slow_analysis["total_failed_queries"],
                "performance_grade": _get_performance_grade(performance_score)
            },
            "recommendations": _generate_performance_recommendations(stats, slow_analysis),
            "alerts": _generate_performance_alerts(stats, slow_analysis)
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get performance summary: {str(e)}"
        )

@router.delete("/clear-logs")
async def clear_query_logs_endpoint():
    """
    Clear query log files
    
    ⚠️ WARNING: This will permanently delete all slow query and failed query logs.
    Use with caution, preferably only in development environments.
    """
    try:
        clear_query_logs()
        
        # Also clear in-memory stats
        query_stats.queries.clear()
        query_stats.session_queries.clear()
        
        return {
            "status": "success",
            "message": "Query logs and statistics cleared successfully"
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to clear query logs: {str(e)}"
        )

# Helper functions
def _generate_global_recommendations(slow_queries: List[Dict]) -> List[str]:
    """Generate optimization recommendations based on slow query patterns"""
    recommendations = []
    
    if not slow_queries:
        return ["No slow queries detected. Database performance looks good!"]
    
    # Analyze common patterns
    select_count = sum(1 for q in slow_queries if q["type"] == "SELECT")
    join_count = sum(1 for q in slow_queries if "JOIN" in q["query"].upper())
    
    if select_count > len(slow_queries) * 0.8:
        recommendations.append("Most slow queries are SELECT statements - consider adding database indexes")
    
    if join_count > len(slow_queries) * 0.5:
        recommendations.append("Many slow queries involve JOINs - review join conditions and consider denormalization")
    
    recommendations.extend([
        "Consider implementing query result caching for frequently accessed data",
        "Review database indexes for slow query patterns",
        "Consider using database query optimization tools",
        "Monitor query execution plans for complex queries"
    ])
    
    return recommendations

def _count_query_types(queries: List[Dict]) -> Dict[str, int]:
    """Count queries by type"""
    types = {}
    for query in queries:
        query_type = query.get("type", "UNKNOWN")
        types[query_type] = types.get(query_type, 0) + 1
    return types

def _get_performance_grade(score: float) -> str:
    """Convert performance score to letter grade"""
    if score >= 95:
        return "A+ (Excellent)"
    elif score >= 90:
        return "A (Very Good)"
    elif score >= 80:
        return "B (Good)"
    elif score >= 70:
        return "C (Fair)"
    elif score >= 60:
        return "D (Poor)"
    else:
        return "F (Critical)"

def _generate_performance_recommendations(stats: Dict, slow_analysis: Dict) -> List[str]:
    """Generate performance recommendations based on overall statistics"""
    recommendations = []
    
    total_queries = stats["total_queries"]
    slow_queries = len([q for q in stats["slow_queries"] if q["slow_count"] > 0])
    
    if total_queries == 0:
        return ["No queries executed yet"]
    
    slow_percentage = (slow_queries / total_queries) * 100
    
    if slow_percentage > 10:
        recommendations.append("⚠️ High percentage of slow queries - immediate optimization needed")
    elif slow_percentage > 5:
        recommendations.append("Moderate number of slow queries - consider optimization")
    
    if slow_analysis["total_failed_queries"] > 0:
        recommendations.append("Failed queries detected - review error logs for issues")
    
    # Add general recommendations
    recommendations.extend([
        "Implement query result caching for read-heavy operations",
        "Regular database maintenance and index optimization",
        "Monitor query patterns and optimize frequent operations",
        "Consider connection pooling optimization"
    ])
    
    return recommendations

def _generate_performance_alerts(stats: Dict, slow_analysis: Dict) -> List[Dict]:
    """Generate performance alerts based on thresholds"""
    alerts = []
    
    total_queries = stats["total_queries"]
    slow_queries = len([q for q in stats["slow_queries"] if q["slow_count"] > 0])
    
    if total_queries > 0:
        slow_percentage = (slow_queries / total_queries) * 100
        
        if slow_percentage > 15:
            alerts.append({
                "level": "critical",
                "message": f"Critical: {slow_percentage:.1f}% of queries are slow",
                "action": "Immediate optimization required"
            })
        elif slow_percentage > 10:
            alerts.append({
                "level": "warning",
                "message": f"Warning: {slow_percentage:.1f}% of queries are slow",
                "action": "Consider query optimization"
            })
    
    if slow_analysis["total_failed_queries"] > 10:
        alerts.append({
            "level": "warning",
            "message": f"{slow_analysis['total_failed_queries']} failed queries detected",
            "action": "Review error logs and fix query issues"
        })
    
    return alerts
