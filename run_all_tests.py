#!/usr/bin/env python3
"""
Master Test Runner
Runs all test suites and provides comprehensive results
"""

import subprocess
import sys
import time
from datetime import datetime

class TestRunner:
    def __init__(self):
        self.test_suites = [
            {
                "name": "RAG Backend Tests",
                "script": "test_rag_backend.py",
                "description": "Basic RAG functionality and endpoints"
            },
            {
                "name": "Abuse Protection Tests", 
                "script": "test_abuse_protection.py",
                "description": "Security and abuse prevention mechanisms"
            },
            {
                "name": "Data Quality Tests",
                "script": "test_data_quality.py", 
                "description": "Data validation and quality checks"
            },
            {
                "name": "Comprehensive Integration Tests",
                "script": "test_integration_comprehensive.py",
                "description": "End-to-end system functionality"
            }
        ]
        
    def run_single_test(self, test_info):
        """Run a single test suite"""
        print(f"\n{'='*80}")
        print(f"🧪 RUNNING: {test_info['name']}")
        print(f"📋 Description: {test_info['description']}")
        print(f"📄 Script: {test_info['script']}")
        print(f"{'='*80}")
        
        start_time = time.time()
        
        try:
            result = subprocess.run(
                [sys.executable, test_info['script']],
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )
            
            elapsed = time.time() - start_time
            
            # Print the output
            if result.stdout:
                print(result.stdout)
            if result.stderr:
                print("STDERR:", result.stderr)
            
            success = result.returncode == 0
            status = "✅ PASSED" if success else "❌ FAILED"
            print(f"\n📊 {test_info['name']}: {status} (took {elapsed:.1f}s)")
            
            return {
                "name": test_info['name'],
                "success": success,
                "elapsed": elapsed,
                "returncode": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr
            }
            
        except subprocess.TimeoutExpired:
            print(f"⏰ {test_info['name']}: TIMEOUT after 5 minutes")
            return {
                "name": test_info['name'], 
                "success": False,
                "elapsed": 300,
                "returncode": -1,
                "stdout": "",
                "stderr": "Test timed out after 5 minutes"
            }
        except Exception as e:
            print(f"❌ {test_info['name']}: ERROR - {e}")
            return {
                "name": test_info['name'],
                "success": False, 
                "elapsed": 0,
                "returncode": -1,
                "stdout": "",
                "stderr": str(e)
            }
    
    def check_server_status(self):
        """Check if the application server is running"""
        print("🔍 Checking server status...")
        
        try:
            import requests
            response = requests.get("http://localhost:8000/api/health", timeout=5)
            if response.status_code == 200:
                print("✅ Server is running and healthy")
                return True
            else:
                print(f"⚠️ Server responded with status {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Server not accessible: {e}")
            print("💡 Start the server with: python app.py")
            return False
    
    def run_all_tests(self, continue_on_failure=True):
        """Run all test suites"""
        print("🚀 COMPREHENSIVE TEST SUITE RUNNER")
        print(f"📅 Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"🧪 Test suites to run: {len(self.test_suites)}")
        print("="*80)
        
        # Check server status first
        if not self.check_server_status():
            print("\n🚨 Server not running - some tests will fail")
            if not continue_on_failure:
                print("Aborting test run. Start server and try again.")
                return False
        
        # Run all test suites
        results = []
        total_start_time = time.time()
        
        for test_info in self.test_suites:
            result = self.run_single_test(test_info)
            results.append(result)
            
            # Stop on first failure if requested
            if not continue_on_failure and not result['success']:
                print(f"\n🛑 Stopping test run due to failure in {result['name']}")
                break
        
        total_elapsed = time.time() - total_start_time
        
        # Generate summary report
        self.generate_summary_report(results, total_elapsed)
        
        # Return overall success
        overall_success = all(r['success'] for r in results)
        return overall_success
    
    def generate_summary_report(self, results, total_elapsed):
        """Generate a comprehensive summary report"""
        print(f"\n{'='*80}")
        print("📊 COMPREHENSIVE TEST RESULTS SUMMARY")
        print(f"{'='*80}")
        
        passed = sum(1 for r in results if r['success'])
        total = len(results)
        success_rate = (passed / total) * 100 if total > 0 else 0
        
        print(f"🎯 Overall Results: {passed}/{total} test suites passed ({success_rate:.1f}%)")
        print(f"⏱️ Total execution time: {total_elapsed:.1f} seconds")
        print(f"📅 Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        print(f"\n📋 Individual Test Suite Results:")
        for result in results:
            status_icon = "✅" if result['success'] else "❌"
            print(f"   {status_icon} {result['name']:<40} ({result['elapsed']:.1f}s)")
            if not result['success'] and result['stderr']:
                print(f"      Error: {result['stderr'][:100]}...")
        
        # Overall assessment
        print(f"\n🏆 SYSTEM ASSESSMENT:")
        if success_rate == 100:
            print("🎉 EXCELLENT: All tests passed! System is production-ready.")
        elif success_rate >= 80:
            print("✅ GOOD: Most tests passed. Minor issues to address.")
        elif success_rate >= 60:
            print("⚠️ FAIR: Some major issues. Needs work before production.")
        else:
            print("🚨 POOR: Critical failures detected. Major work needed.")
        
        # Specific recommendations
        print(f"\n💡 RECOMMENDATIONS:")
        
        failed_tests = [r for r in results if not r['success']]
        if failed_tests:
            print("   Priority fixes needed:")
            for failed in failed_tests:
                if "Abuse Protection" in failed['name']:
                    print("   • Implement abuse protection mechanisms (rate limiting, content filtering)")
                elif "Data Quality" in failed['name']:
                    print("   • Add data validation and quality checks")
                elif "Integration" in failed['name']:
                    print("   • Fix core system integration issues")
                else:
                    print(f"   • Fix issues in {failed['name']}")
        else:
            print("   • All tests passing - system ready for production!")
            print("   • Consider adding performance monitoring")
            print("   • Consider adding more edge case tests")
        
        print(f"\n📖 For detailed logs, check individual test outputs above.")

def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Run comprehensive test suite')
    parser.add_argument('--stop-on-failure', action='store_true',
                       help='Stop running tests after first failure')
    parser.add_argument('--suite', choices=['rag', 'abuse', 'data', 'integration', 'all'],
                       default='all', help='Run specific test suite')
    
    args = parser.parse_args()
    
    runner = TestRunner()
    
    if args.suite != 'all':
        # Run specific suite
        suite_map = {
            'rag': 'test_rag_backend.py',
            'abuse': 'test_abuse_protection.py', 
            'data': 'test_data_quality.py',
            'integration': 'test_integration_comprehensive.py'
        }
        
        script = suite_map[args.suite]
        test_info = next(t for t in runner.test_suites if t['script'] == script)
        result = runner.run_single_test(test_info)
        
        success = result['success']
    else:
        # Run all tests
        success = runner.run_all_tests(continue_on_failure=not args.stop_on_failure)
    
    # Exit with appropriate code
    exit_code = 0 if success else 1
    sys.exit(exit_code)

if __name__ == "__main__":
    main()
