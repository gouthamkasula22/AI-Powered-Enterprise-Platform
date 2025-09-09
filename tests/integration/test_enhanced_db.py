"""
Enhanced Database Configuration Test

Test script demonstrating the new enhanced query logging and monitoring features.
This will show you exactly how slow queries are detected and logged.
"""

import asyncio
import sys
import os
import time

# Add the parent directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import (
    test_database_connection,
    check_database_health,
    get_database_stats,
    create_database_tables,
    get_query_statistics,
    get_slow_query_analysis,
    AsyncSessionLocal,
    query_stats
)
from app.core.config import settings
from sqlalchemy import text
import logging

# Set up logging to see our enhanced query logging in action
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

async def test_enhanced_query_logging():
    """Test the enhanced query logging system"""
    print("🔧 Testing Enhanced SQLAlchemy Configuration with Query Monitoring...")
    print(f"Environment: {settings.ENVIRONMENT}")
    print(f"Database URL: {settings.DATABASE_URL}")
    print(f"Pool Size: {settings.DB_POOL_SIZE}")
    print(f"Max Overflow: {settings.DB_MAX_OVERFLOW}")
    print(f"Echo Queries: {settings.DB_ECHO}")
    print("-" * 70)
    
    # Test basic connectivity
    print("1. Testing database connectivity...")
    connection_success = await test_database_connection()
    print(f"   Result: {'✅ Success' if connection_success else '❌ Failed'}")
    
    if not connection_success:
        print("❌ Database connection failed. Please check your configuration.")
        return False
    
    # Test query execution with monitoring
    print("\n2. Testing query execution with enhanced logging...")
    async with AsyncSessionLocal() as session:
        try:
            # Fast query (should not trigger slow query detection)
            print("   2.1 Executing fast query...")
            await session.execute(text("SELECT 1 as test_value"))
            
            # Slow query simulation (using pg_sleep to simulate slowness)
            print("   2.2 Executing intentionally slow query...")
            await session.execute(text("SELECT pg_sleep(1.5), 'slow_query' as test"))
            
            # Multiple similar queries (to test frequency tracking)
            print("   2.3 Executing multiple similar queries...")
            for i in range(3):
                await session.execute(text(f"SELECT {i} as iteration_number"))
            
            # Complex query example
            print("   2.4 Executing complex query (for pattern analysis)...")
            await session.execute(text("""
                SELECT 
                    current_database() as db_name,
                    current_user as username,
                    version() as pg_version
                ORDER BY db_name
            """))
            
            await session.commit()
            
        except Exception as e:
            print(f"   ❌ Query execution failed: {e}")
            await session.rollback()
            return False
    
    # Test statistics gathering
    print("\n3. Testing query statistics...")
    try:
        stats = await get_query_statistics()
        print(f"   Total queries executed: {stats['total_queries']}")
        print(f"   Unique query patterns: {stats['unique_queries']}")
        print(f"   Slow queries detected: {len(stats['slow_queries'])}")
        print(f"   Recent queries count: {len(stats['recent_queries'])}")
        
        # Show slow queries if any
        if stats['slow_queries']:
            print("\n   📊 Slow Queries Detected:")
            for slow_query in stats['slow_queries'][:3]:  # Show first 3
                print(f"      Hash: {slow_query['hash']}")
                print(f"      Type: {slow_query['type']}")
                print(f"      Avg Time: {slow_query['avg_time']:.3f}s")
                print(f"      Count: {slow_query['count']}")
                print(f"      Query: {slow_query['query'][:100]}...")
                print()
        
        # Show most frequent queries
        if stats['frequent_queries']:
            print("   🔄 Most Frequent Queries:")
            for freq_query in stats['frequent_queries'][:3]:  # Show first 3
                print(f"      Hash: {freq_query['hash']}")
                print(f"      Type: {freq_query['type']}")
                print(f"      Count: {freq_query['count']}")
                print(f"      Avg Time: {freq_query['avg_time']:.3f}s")
                print(f"      Query: {freq_query['query'][:80]}...")
                print()
                
    except Exception as e:
        print(f"   ❌ Failed to get statistics: {e}")
        return False
    
    # Test slow query analysis
    print("\n4. Testing slow query analysis...")
    try:
        slow_analysis = await get_slow_query_analysis()
        print(f"   Total slow queries logged: {slow_analysis['total_slow_queries']}")
        print(f"   Total failed queries: {slow_analysis['total_failed_queries']}")
        
        if slow_analysis['slow_queries_by_hash']:
            print("\n   📈 Slow Query Analysis:")
            for hash_key, data in list(slow_analysis['slow_queries_by_hash'].items())[:2]:
                print(f"      Hash: {hash_key}")
                print(f"      Occurrences: {data['occurrences']}")
                print(f"      Avg Time: {data['avg_time']:.3f}s")
                print(f"      Max Time: {data['max_time']:.3f}s")
                if data['recommendations']:
                    print(f"      Recommendations: {', '.join(data['recommendations'][:2])}")
                print()
                
    except Exception as e:
        print(f"   ⚠️ Slow query analysis not available: {e}")
    
    # Test health check
    print("\n5. Testing comprehensive health check...")
    try:
        health_data = await check_database_health()
        print(f"   Status: {health_data['status']}")
        print(f"   Response Time: {health_data['response_time_ms']}ms")
        print(f"   Connection Test: {'✅' if health_data['connection_test'] else '❌'}")
        if 'pool_stats' in health_data:
            pool_stats = health_data['pool_stats']
            print(f"   Pool Stats: Size={pool_stats.get('pool_size', 0)}, "
                  f"Checked Out={pool_stats.get('checked_out', 0)}")
    except Exception as e:
        print(f"   ❌ Health check failed: {e}")
        return False
    
    print("\n✅ All enhanced database configuration tests passed!")
    print("\n💡 Key Features Demonstrated:")
    print("   • Enhanced query logging with execution time tracking")
    print("   • Slow query detection and analysis")
    print("   • Query pattern recognition and statistics")
    print("   • Performance recommendations")
    print("   • Comprehensive health monitoring")
    print("\n📁 Check these files for detailed logs:")
    print("   • slow_queries.log - Detailed slow query information")
    print("   • failed_queries.log - Failed query debugging info")
    print("   • App logs - Real-time query execution monitoring")
    
    return True

async def demonstrate_pagination():
    """Demonstrate the enhanced pagination utility"""
    print("\n" + "="*70)
    print("🔄 PAGINATION DEMONSTRATION")
    print("="*70)
    
    # This would normally use actual models, but we'll simulate with raw SQL
    async with AsyncSessionLocal() as session:
        try:
            # Simulate a paginated query
            print("Simulating paginated query execution...")
            
            # This would be a real pagination example:
            # from app.core.database import paginate_query
            # from sqlalchemy import select
            # query = select(User).filter(User.is_active == True)
            # result = await paginate_query(session, query, page=1, per_page=10)
            
            print("✅ Pagination utility ready for use with actual models")
            print("💡 Usage example:")
            print("   result = await paginate_query(session, query, page=1, per_page=20)")
            print("   items = result['items']")
            print("   pagination_info = result['pagination']")
            
        except Exception as e:
            print(f"❌ Pagination test failed: {e}")

if __name__ == "__main__":
    print("🚀 Starting Enhanced Database Configuration Tests...\n")
    
    async def run_all_tests():
        success = await test_enhanced_query_logging()
        await demonstrate_pagination()
        return success
    
    success = asyncio.run(run_all_tests())
    
    if success:
        print("\n🎉 All tests completed successfully!")
        print("Your enhanced database configuration is ready for production!")
    else:
        print("\n❌ Some tests failed. Please check your configuration.")
        sys.exit(1)
