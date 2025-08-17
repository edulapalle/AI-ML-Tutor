#!/usr/bin/env python3
"""Comprehensive Test Suite Runner

Runs all test suites for the AI/ML Educational Platform:
- Authentication system tests
- RAG system tests 
- Agentic learning tests
- Feature tests (quiz, bookmarks, email)
- Security and abuse protection tests
- Data quality tests
- Integration tests
"""

import sys
import subprocess
import argparse
import time
from datetime import datetime

class ComprehensiveTestRunner:
    """Master test runner for all platform features"""
    
    def __init__(self):
        self.test_suites = {
            "auth": {
                "name": "Authentication System",
                "script": "test_comprehensive_auth.py",
                "description": "User registration, login, JWT tokens, profile management"
            },
            "rag": {
                "name": "RAG System", 
                "script": "test_comprehensive_rag.py",
                "description": "Chat, intent classification, retrieval, response quality"
            },
            "agentic": {
                "name": "Agentic Learning System",
                "script": "test_comprehensive_agentic.py", 
                "description": "Learning paths, comprehension monitoring, recommendations"
            },
            "features": {
                "name": "Platform Features",
                "script": "test_comprehensive_features.py",
                "description": "Quiz, bookmarks, email, YouTube endpoints, learning paths"
            },
            "security": {
                "name": "Security & Abuse Protection",
                "script": "test_comprehensive_security.py",
                "description": "Rate limiting, input validation, prompt injection, profanity"
            },
            "integration": {
                "name": "Integration Tests",
                "script": "test_integration_comprehensive.py",
                "description": "End-to-end system validation"
            },
            "data_quality": {
                "name": "Data Quality",
                "script": "test_data_quality.py", 
                "description": "Milvus collections, data integrity checks"
            },
            "rag_backend": {
                "name": "RAG Backend",
                "script": "test_rag_backend.py",
                "description": "Core RAG functionality and performance"
            }
        }
        
        self.results = {}
        self.total_start_time = None
    
    def run_test_suite(self, suite_name, suite_info):
        """Run a single test suite"""
        print(f"\n{'='*80}")
        print(f"🧪 RUNNING: {suite_info['name']}")
        print(f"📝 Description: {suite_info['description']}")
        print(f"📄 Script: {suite_info['script']}")
        print(f"{'='*80}")
        
        start_time = time.time()
        
        try:
            # Run the test script
            result = subprocess.run(
                [sys.executable, suite_info['script']], 
                capture_output=True, 
                text=True,
                timeout=300  # 5 minute timeout per suite
            )
            
            end_time = time.time()
            duration = end_time - start_time
            
            success = result.returncode == 0
            
            self.results[suite_name] = {
                "success": success,
                "duration": duration,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "returncode": result.returncode
            }
            
            # Print results
            status = "✅ PASSED" if success else "❌ FAILED"
            print(f"\n{status} {suite_info['name']} ({duration:.1f}s)")
            
            if success:
                print("📊 Test output:")
                print(result.stdout[-500:])  # Last 500 chars
            else:
                print("❌ Error output:")
                print(result.stderr[-500:] if result.stderr else "No error output")
                print("\n📊 Test output:")
                print(result.stdout[-500:] if result.stdout else "No output")
            
            return success
            
        except subprocess.TimeoutExpired:
            print(f"⏰ TIMEOUT: {suite_info['name']} exceeded 5 minutes")
            self.results[suite_name] = {
                "success": False,
                "duration": 300,
                "stdout": "",
                "stderr": "Test suite timed out after 5 minutes",
                "returncode": -1
            }
            return False
            
        except Exception as e:
            print(f"💥 EXCEPTION: {suite_info['name']} failed with exception: {e}")
            self.results[suite_name] = {
                "success": False,
                "duration": 0,
                "stdout": "",
                "stderr": str(e),
                "returncode": -1
            }
            return False
    
    def run_selected_suites(self, selected_suites=None):
        """Run selected test suites or all if none specified"""
        if selected_suites is None:
            selected_suites = list(self.test_suites.keys())
        
        self.total_start_time = time.time()
        
        print("🎯 COMPREHENSIVE AI/ML EDUCATIONAL PLATFORM TESTS")
        print(f"📅 Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"🧪 Test Suites: {', '.join(selected_suites)}")
        print("=" * 80)
        
        results = []
        for suite_name in selected_suites:
            if suite_name not in self.test_suites:
                print(f"⚠️ Unknown test suite: {suite_name}")
                continue
                
            suite_info = self.test_suites[suite_name]
            success = self.run_test_suite(suite_name, suite_info)
            results.append((suite_name, success))
        
        return results
    
    def print_summary(self, results):
        """Print comprehensive test summary"""
        total_end_time = time.time()
        total_duration = total_end_time - self.total_start_time
        
        passed = sum(1 for _, success in results if success)
        failed = len(results) - passed
        
        print("\n" + "=" * 80)
        print("📊 COMPREHENSIVE TEST RESULTS SUMMARY")
        print("=" * 80)
        
        for suite_name, success in results:
            suite_info = self.test_suites[suite_name]
            result_info = self.results.get(suite_name, {})
            duration = result_info.get('duration', 0)
            
            status = "✅ PASS" if success else "❌ FAIL"
            print(f"{status} {suite_info['name']:<30} ({duration:>5.1f}s)")
        
        print("\n" + "-" * 80)
        
        # Overall statistics
        success_rate = (passed / len(results)) * 100 if results else 0
        print(f"🎯 OVERALL RESULTS:")
        print(f"   ✅ Passed: {passed}")
        print(f"   ❌ Failed: {failed}")
        print(f"   📊 Success Rate: {success_rate:.1f}%")
        print(f"   ⏱️  Total Time: {total_duration:.1f}s")
        print(f"   📅 Completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Detailed failure analysis
        if failed > 0:
            print(f"\n🔍 FAILURE ANALYSIS:")
            for suite_name, success in results:
                if not success:
                    suite_info = self.test_suites[suite_name]
                    result_info = self.results.get(suite_name, {})
                    stderr = result_info.get('stderr', 'No error info')
                    
                    print(f"\n❌ {suite_info['name']}:")
                    print(f"   Error: {stderr[:200]}...")
        
        # Success celebration or failure warning
        if success_rate >= 90:
            print("\n🎉 EXCELLENT! All major systems are working correctly!")
        elif success_rate >= 75:
            print("\n✅ GOOD! Most systems are working, minor issues detected.")
        elif success_rate >= 50:
            print("\n⚠️ WARNING! Significant issues detected, review needed.")
        else:
            print("\n🚨 CRITICAL! Major system failures detected!")
        
        print("=" * 80)
        
        return success_rate >= 75  # 75% pass rate required
    
    def run_quick_tests(self):
        """Run quick essential tests"""
        quick_suites = ["auth", "rag", "security"]
        print("🚀 Running QUICK TEST SUITE (essential features only)")
        results = self.run_selected_suites(quick_suites)
        return self.print_summary(results)
    
    def run_all_tests(self):
        """Run complete test suite"""
        print("🎯 Running COMPLETE TEST SUITE (all features)")
        results = self.run_selected_suites()
        return self.print_summary(results)

def main():
    """Main test runner entry point"""
    parser = argparse.ArgumentParser(description="Comprehensive AI/ML Educational Platform Test Runner")
    
    parser.add_argument(
        "--suite", 
        choices=["auth", "rag", "agentic", "features", "security", "integration", "data_quality", "rag_backend"],
        help="Run specific test suite only"
    )
    
    parser.add_argument(
        "--quick",
        action="store_true", 
        help="Run quick tests only (auth, rag, security)"
    )
    
    parser.add_argument(
        "--list",
        action="store_true",
        help="List available test suites"
    )
    
    args = parser.parse_args()
    
    runner = ComprehensiveTestRunner()
    
    if args.list:
        print("📋 Available Test Suites:")
        print("=" * 60)
        for suite_name, suite_info in runner.test_suites.items():
            print(f"  {suite_name:<15} - {suite_info['name']}")
            print(f"  {' '*15}   {suite_info['description']}")
            print()
        return
    
    if args.suite:
        # Run specific suite
        if args.suite in runner.test_suites:
            results = runner.run_selected_suites([args.suite])
            success = runner.print_summary(results)
        else:
            print(f"❌ Unknown test suite: {args.suite}")
            success = False
    elif args.quick:
        # Run quick tests
        success = runner.run_quick_tests()
    else:
        # Run all tests
        success = runner.run_all_tests()
    
    # Exit with appropriate code
    if success:
        print("\n🎉 All tests completed successfully!")
        sys.exit(0)
    else:
        print("\n❌ Some tests failed!")
        sys.exit(1)

if __name__ == "__main__":
    main()
