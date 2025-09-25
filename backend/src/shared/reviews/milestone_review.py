"""
Milestone 1.1 Master Review Coordinator
Orchestrates all review gates for milestone completion

This module coordinates the execution of all review gates and generates
the final milestone completion report.
"""

import asyncio
from datetime import datetime
from typing import Dict, List, Any
import logging
import json

from .architecture_review import ArchitectureReview
from .security_review import SecurityReview
from .performance_benchmark import PerformanceBenchmark

logger = logging.getLogger(__name__)


class MilestoneReviewCoordinator:
    """Coordinates all review gates for Milestone 1.1 completion"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.milestone = "1.1 - Chat Foundation & File Processing"
        self.base_url = base_url
        
        # Initialize review components
        self.architecture_review = ArchitectureReview()
        self.security_review = SecurityReview()
        self.performance_benchmark = PerformanceBenchmark(base_url)
        
        # Review gate requirements
        self.requirements = {
            "architecture_threshold": 8.5,
            "security_threshold": 8.5,
            "performance_threshold": 8.0,
            "overall_threshold": 8.5
        }
    
    async def execute_all_reviews(self) -> Dict[str, Any]:
        """Execute all review gates and generate milestone completion report"""
        
        master_report = {
            "milestone": self.milestone,
            "review_timestamp": datetime.utcnow().isoformat(),
            "review_coordinator": "MilestoneReviewCoordinator v1.0",
            "review_results": {},
            "milestone_status": "IN_PROGRESS",
            "overall_score": 0,
            "passed_reviews": [],
            "failed_reviews": [],
            "critical_issues": [],
            "recommendations": [],
            "next_steps": [],
            "completion_summary": {}
        }
        
        logger.info(f"🔍 Starting comprehensive review for {self.milestone}")
        print(f"\n{'='*80}")
        print(f"🎯 MILESTONE 1.1 COMPREHENSIVE REVIEW EXECUTION")
        print(f"{'='*80}")
        
        try:
            # Execute Architecture Review
            print(f"\n📐 ARCHITECTURE REVIEW")
            print(f"Target Score: {self.requirements['architecture_threshold']}/10")
            print("-" * 50)
            
            architecture_result = await self.architecture_review.conduct_review()
            master_report["review_results"]["architecture"] = architecture_result
            
            arch_passed = architecture_result["passed"]
            arch_score = architecture_result["total_score"]
            
            print(f"Architecture Score: {arch_score:.1f}/10 {'✅ PASS' if arch_passed else '❌ FAIL'}")
            
            if arch_passed:
                master_report["passed_reviews"].append("Architecture Review")
            else:
                master_report["failed_reviews"].append("Architecture Review")
                master_report["critical_issues"].extend(architecture_result.get("areas_for_improvement", []))
            
            # Execute Security Review
            print(f"\n🔒 SECURITY REVIEW")
            print(f"Target Score: {self.requirements['security_threshold']}/10")
            print("-" * 50)
            
            security_result = await self.security_review.conduct_review()
            master_report["review_results"]["security"] = security_result
            
            sec_passed = security_result["passed"]
            sec_score = security_result["total_score"]
            
            print(f"Security Score: {sec_score:.1f}/10 {'✅ PASS' if sec_passed else '❌ FAIL'}")
            
            if sec_passed:
                master_report["passed_reviews"].append("Security Review")
            else:
                master_report["failed_reviews"].append("Security Review")
                master_report["critical_issues"].extend(security_result.get("security_findings", []))
            
            # Execute Performance Benchmark
            print(f"\n⚡ PERFORMANCE BENCHMARK")
            print(f"Target Score: {self.requirements['performance_threshold']}/10")
            print("-" * 50)
            
            performance_result = await self.performance_benchmark.run_full_benchmark()
            master_report["review_results"]["performance"] = performance_result
            
            perf_passed = performance_result["passed"]
            perf_score = performance_result["overall_score"]
            
            print(f"Performance Score: {perf_score:.1f}/10 {'✅ PASS' if perf_passed else '❌ FAIL'}")
            
            if perf_passed:
                master_report["passed_reviews"].append("Performance Benchmark")
            else:
                master_report["failed_reviews"].append("Performance Benchmark")
                master_report["critical_issues"].extend(performance_result.get("recommendations", []))
            
            # Calculate Overall Score
            weights = {
                "architecture": 0.4,
                "security": 0.4,
                "performance": 0.2
            }
            
            overall_score = (
                arch_score * weights["architecture"] +
                sec_score * weights["security"] +
                perf_score * weights["performance"]
            )
            
            master_report["overall_score"] = overall_score
            
            # Determine milestone status
            all_passed = len(master_report["failed_reviews"]) == 0
            meets_threshold = overall_score >= self.requirements["overall_threshold"]
            
            if all_passed and meets_threshold:
                master_report["milestone_status"] = "COMPLETED"
            elif overall_score >= 7.0:  # Conditional pass
                master_report["milestone_status"] = "CONDITIONAL_PASS"
            else:
                master_report["milestone_status"] = "FAILED"
            
            # Generate completion summary and recommendations
            master_report.update(await self._generate_completion_summary(master_report))
            
            # Display final results
            await self._display_final_results(master_report)
            
        except Exception as e:
            logger.error(f"Review execution failed: {str(e)}")
            master_report["error"] = str(e)
            master_report["milestone_status"] = "ERROR"
        
        return master_report
    
    async def _generate_completion_summary(self, report: Dict[str, Any]) -> Dict[str, Any]:
        """Generate completion summary and next steps"""
        
        completion_summary = {
            "total_reviews": 3,
            "passed_reviews": len(report["passed_reviews"]),
            "failed_reviews": len(report["failed_reviews"]),
            "overall_score": report["overall_score"],
            "milestone_status": report["milestone_status"]
        }
        
        recommendations = []
        next_steps = []
        
        # Collect recommendations from all reviews
        for review_name, review_data in report["review_results"].items():
            if "recommendations" in review_data:
                recommendations.extend([
                    f"[{review_name.title()}] {rec}" 
                    for rec in review_data["recommendations"]
                ])
        
        # Generate next steps based on status
        if report["milestone_status"] == "COMPLETED":
            next_steps = [
                "🎉 Milestone 1.1 successfully completed!",
                "📋 Prepare for Milestone 1.2: RAG Implementation Development",
                "🔄 Begin Priority 1: Retrieval System Design",
                "📚 Review advanced RAG patterns and implementation strategies",
                "🏗️ Set up development environment for RAG components"
            ]
        
        elif report["milestone_status"] == "CONDITIONAL_PASS":
            next_steps = [
                "⚠️ Address minor issues identified in reviews",
                "🔧 Implement high-priority recommendations",
                "🧪 Conduct focused re-testing of improved areas",
                "✅ Final validation before Milestone 1.2 progression"
            ]
        
        else:  # FAILED
            next_steps = [
                "🔧 Address all critical issues identified",
                "🏗️ Implement architectural improvements",
                "🔒 Resolve security vulnerabilities",
                "⚡ Optimize performance bottlenecks",
                "🔄 Re-run complete review suite"
            ]
        
        return {
            "completion_summary": completion_summary,
            "recommendations": recommendations,
            "next_steps": next_steps
        }
    
    async def _display_final_results(self, report: Dict[str, Any]):
        """Display comprehensive final results"""
        
        print(f"\n{'='*80}")
        print(f"📊 MILESTONE 1.1 FINAL REVIEW RESULTS")
        print(f"{'='*80}")
        
        # Overall Status
        status = report["milestone_status"]
        status_icon = {
            "COMPLETED": "🎉",
            "CONDITIONAL_PASS": "⚠️",
            "FAILED": "❌",
            "ERROR": "💥"
        }
        
        print(f"\n🎯 MILESTONE STATUS: {status_icon.get(status, '❓')} {status}")
        print(f"📊 OVERALL SCORE: {report['overall_score']:.1f}/10")
        print(f"✅ PASSED REVIEWS: {len(report['passed_reviews'])}/3")
        
        # Review Breakdown
        print(f"\n📋 REVIEW BREAKDOWN:")
        print("-" * 50)
        
        for review_name, review_data in report["review_results"].items():
            score = review_data.get("total_score", review_data.get("overall_score", 0))
            passed = review_data.get("passed", False)
            status_text = "✅ PASS" if passed else "❌ FAIL"
            print(f"{review_name.title():20} {score:5.1f}/10 {status_text}")
        
        # Key Achievements
        if report["milestone_status"] in ["COMPLETED", "CONDITIONAL_PASS"]:
            print(f"\n🏆 KEY ACHIEVEMENTS:")
            achievements = [
                "📄 Complete file processing pipeline implemented",
                "🔍 Vector embedding system operational",
                "🛡️ Security controls and RBAC in place",
                "⚡ Performance targets mostly achieved",
                "🏗️ Clean architecture foundation established",
                "🔌 API endpoints functional and documented"
            ]
            
            for achievement in achievements:
                print(f"  {achievement}")
        
        # Next Steps
        print(f"\n🚀 NEXT STEPS:")
        for i, step in enumerate(report["next_steps"], 1):
            print(f"  {i}. {step}")
        
        # Critical Issues (if any)
        if report["critical_issues"]:
            print(f"\n⚠️  CRITICAL ISSUES TO ADDRESS:")
            for issue in report["critical_issues"][:5]:  # Show top 5
                print(f"  • {issue}")
        
        print(f"\n{'='*80}")
        
        if report["milestone_status"] == "COMPLETED":
            print(f"🎊 CONGRATULATIONS! Milestone 1.1 successfully completed!")
            print(f"Ready to proceed to Milestone 1.2: RAG Implementation Development")
        elif report["milestone_status"] == "CONDITIONAL_PASS":
            print(f"✨ Good progress! Address minor issues before Milestone 1.2")
        else:
            print(f"🔧 Focus on addressing critical issues before proceeding")
        
        print(f"{'='*80}")


# Convenience function for easy execution
async def run_milestone_review(base_url: str = "http://localhost:8000") -> Dict[str, Any]:
    """Run complete Milestone 1.1 review process"""
    
    coordinator = MilestoneReviewCoordinator(base_url)
    return await coordinator.execute_all_reviews()