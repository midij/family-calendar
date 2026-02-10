#!/usr/bin/env python3
"""
Complete End-to-End Test Runner for Family Calendar
Runs all comprehensive tests including performance, compatibility, and user workflows
"""

import sys
import time
import argparse
from datetime import datetime

# Import our test suites
from tests.test_e2e_comprehensive import E2ETestSuite
from tests.test_frontend_performance import FrontendPerformanceTest
from tests.test_browser_compatibility import BrowserCompatibilityTest


class CompleteE2ETestRunner:
    """Complete end-to-end test runner"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.test_suites = []
        self.results = {}
    
    def add_test_suite(self, suite_name: str, suite_class):
        """Add a test suite to run"""
        self.test_suites.append((suite_name, suite_class))
    
    def run_all_tests(self, verbose: bool = False):
        """Run all test suites"""
        print("🧪 Starting Complete End-to-End Test Suite for Family Calendar")
        print("=" * 80)
        print(f"🕐 Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"🌐 Base URL: {self.base_url}")
        print("=" * 80)
        
        total_start_time = time.time()
        all_passed = True
        
        for suite_name, suite_class in self.test_suites:
            print(f"\n🔍 Running {suite_name}...")
            print("-" * 60)
            
            suite_start_time = time.time()
            
            try:
                # Create and run the test suite
                suite = suite_class(self.base_url)
                
                if hasattr(suite, 'run_comprehensive_tests'):
                    success = suite.run_comprehensive_tests()
                elif hasattr(suite, 'run_frontend_tests'):
                    success = suite.run_frontend_tests()
                elif hasattr(suite, 'run_browser_compatibility_tests'):
                    success = suite.run_browser_compatibility_tests()
                else:
                    print(f"❌ Unknown test suite method for {suite_name}")
                    success = False
                
                suite_end_time = time.time()
                suite_duration = suite_end_time - suite_start_time
                
                self.results[suite_name] = {
                    "success": success,
                    "duration": suite_duration,
                    "timestamp": datetime.now().isoformat()
                }
                
                if success:
                    print(f"✅ {suite_name} PASSED ({suite_duration:.2f}s)")
                else:
                    print(f"❌ {suite_name} FAILED ({suite_duration:.2f}s)")
                    all_passed = False
                
            except Exception as e:
                suite_end_time = time.time()
                suite_duration = suite_end_time - suite_start_time
                
                self.results[suite_name] = {
                    "success": False,
                    "duration": suite_duration,
                    "error": str(e),
                    "timestamp": datetime.now().isoformat()
                }
                
                print(f"❌ {suite_name} FAILED with exception ({suite_duration:.2f}s): {str(e)}")
                all_passed = False
        
        total_end_time = time.time()
        total_duration = total_end_time - total_start_time
        
        # Print summary
        print("\n" + "=" * 80)
        print("📊 TEST SUMMARY")
        print("=" * 80)
        
        passed_count = sum(1 for result in self.results.values() if result["success"])
        total_count = len(self.results)
        
        print(f"🕐 Total Duration: {total_duration:.2f}s")
        print(f"✅ Passed: {passed_count}/{total_count}")
        print(f"❌ Failed: {total_count - passed_count}/{total_count}")
        
        print("\n📋 Detailed Results:")
        for suite_name, result in self.results.items():
            status = "✅ PASSED" if result["success"] else "❌ FAILED"
            duration = result["duration"]
            print(f"   {status} {suite_name} ({duration:.2f}s)")
            
            if not result["success"] and "error" in result:
                print(f"      Error: {result['error']}")
        
        if all_passed:
            print("\n🎉 ALL TESTS PASSED! Family Calendar is ready for production!")
        else:
            print("\n⚠️  SOME TESTS FAILED! Please review the results above.")
        
        print("=" * 80)
        
        return all_passed
    
    def generate_report(self, filename: str = None):
        """Generate a detailed test report"""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"e2e_test_report_{timestamp}.json"
        
        import json
        
        report = {
            "timestamp": datetime.now().isoformat(),
            "base_url": self.base_url,
            "total_suites": len(self.results),
            "passed_suites": sum(1 for r in self.results.values() if r["success"]),
            "failed_suites": sum(1 for r in self.results.values() if not r["success"]),
            "results": self.results
        }
        
        with open(filename, 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"📄 Test report saved to: {filename}")
        return filename


def main():
    """Main function to run all E2E tests"""
    parser = argparse.ArgumentParser(description="Run complete end-to-end tests for Family Calendar")
    parser.add_argument("--url", default="http://localhost:8000", help="Base URL for the API")
    parser.add_argument("--wait", type=int, default=0, help="Wait N seconds before starting tests")
    parser.add_argument("--report", help="Generate test report to specified file")
    parser.add_argument("--suite", choices=["all", "comprehensive", "frontend", "browser"], 
                       default="all", help="Which test suite to run")
    parser.add_argument("--verbose", action="store_true", help="Verbose output")
    
    args = parser.parse_args()
    
    if args.wait > 0:
        print(f"⏳ Waiting {args.wait} seconds before starting tests...")
        time.sleep(args.wait)
    
    # Create test runner
    runner = CompleteE2ETestRunner(args.url)
    
    # Add test suites based on selection
    if args.suite in ["all", "comprehensive"]:
        runner.add_test_suite("Comprehensive E2E Tests", E2ETestSuite)
    
    if args.suite in ["all", "frontend"]:
        runner.add_test_suite("Frontend Performance Tests", FrontendPerformanceTest)
    
    if args.suite in ["all", "browser"]:
        runner.add_test_suite("Browser Compatibility Tests", BrowserCompatibilityTest)
    
    # Run tests
    success = runner.run_all_tests(verbose=args.verbose)
    
    # Generate report if requested
    if args.report:
        runner.generate_report(args.report)
    
    # Exit with appropriate code
    exit(0 if success else 1)


if __name__ == "__main__":
    main()
