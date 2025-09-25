#!/usr/bin/env python3
"""
Milestone 1.1 Review Gate Execution Script

This script executes all review gates for Milestone 1.1 completion:
- Architecture Review (target: 8.5+/10)
- Security Review (target: 8.5+/10) 
- Performance Benchmark (target: 8.0+/10)

Usage:
    python run_milestone_review.py
"""

import asyncio
import sys
import os
import json
from datetime import datetime

# Add the backend directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.shared.reviews import run_milestone_review
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


async def main():
    """Execute Milestone 1.1 review gates"""
    
    print("🚀 Starting Milestone 1.1 Review Gate Execution")
    print(f"📅 Timestamp: {datetime.utcnow().isoformat()}")
    print(f"🎯 Target Scores: Architecture 8.5+, Security 8.5+, Performance 8.0+")
    print("=" * 80)
    
    try:
        # Execute comprehensive review
        review_results = await run_milestone_review()
        
        # Save results to file
        results_file = f"milestone_1_1_review_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json"
        with open(results_file, 'w') as f:
            json.dump(review_results, f, indent=2, default=str)
        
        print(f"\n📄 Review results saved to: {results_file}")
        
        # Exit with appropriate code
        if review_results["milestone_status"] == "COMPLETED":
            print(f"\n🎉 SUCCESS: Milestone 1.1 completed successfully!")
            sys.exit(0)
        elif review_results["milestone_status"] == "CONDITIONAL_PASS":
            print(f"\n⚠️  CONDITIONAL: Minor issues to address")
            sys.exit(1)
        else:
            print(f"\n❌ FAILED: Critical issues must be resolved")
            sys.exit(2)
            
    except Exception as e:
        logger.error(f"Review execution failed: {str(e)}")
        print(f"\n💥 ERROR: Review execution failed - {str(e)}")
        sys.exit(3)


if __name__ == "__main__":
    asyncio.run(main())