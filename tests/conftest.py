"""
Pytest configuration and custom fixtures for improved test organization and readability.
"""
import pytest
import os
import sys
from datetime import datetime
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

# Custom test output formatting
class HierarchicalTestReporter:
    """Custom test reporter for hierarchical output"""
    
    def __init__(self):
        self.current_module = None
        self.current_class = None
        self.test_count = 0
        self.passed_count = 0
        self.failed_count = 0
        self.skipped_count = 0
        self._printed_headers = set()
        self._total_tests = 0
        self._session_total = 0
        
    def _get_test_path_parts(self, nodeid):
        """Extract hierarchical parts from test nodeid"""
        # Example: tests/unit/domain/test_value_objects.py::TestTaskId::test_method
        parts = nodeid.split('::')
        file_path = parts[0]
        class_name = parts[1] if len(parts) > 1 else None
        method_name = parts[2] if len(parts) > 2 else None
        
        # Extract directory structure
        path_parts = file_path.split('/')
        if path_parts[0] == 'tests':
            # Remove 'tests' and 'test_' prefix from files
            test_type = path_parts[1] if len(path_parts) > 1 else 'unknown'
            layer = path_parts[2] if len(path_parts) > 2 else 'unknown'
            component = path_parts[3].replace('test_', '').replace('.py', '') if len(path_parts) > 3 else 'unknown'
        else:
            test_type = 'unknown'
            layer = 'unknown'
            component = 'unknown'
        
        return {
            'test_type': test_type,
            'layer': layer,
            'component': component,
            'class_name': class_name,
            'method_name': method_name,
            'file_path': file_path
        }
    
    def _print_header(self, test_type, layer, component):
        """Print hierarchical header"""
        indent = ""  # No base indent for test organization (reduced from 1)
        # Add newline before first header to separate from pytest output
        if not self._printed_headers:
            print()
        print(f"{indent}{test_type.title()}/")
        print(f"{indent}  {layer.title()}/")
        print(f"{indent}    {component.replace('_', ' ').title()}/")
    
    def _print_test_result(self, nodeid, outcome, duration=None):
        """Print individual test result with proper indentation"""
        parts = self._get_test_path_parts(nodeid)
        indent = "  " * 2  # Indent for individual tests (reduced from 3)
        
        # Format test name
        if parts['class_name']:
            test_name = f"{parts['class_name']}::{parts['method_name']}"
        else:
            test_name = parts['method_name']
        
        # Color codes
        colors = {
            'passed': '\033[92m',  # Green
            'failed': '\033[91m',  # Red
            'skipped': '\033[93m',  # Yellow
            'reset': '\033[0m'     # Reset
        }
        
        # Status symbol
        status_symbols = {
            'passed': '✓',
            'failed': '✗',
            'skipped': '○'
        }
        
        color = colors.get(outcome, colors['reset'])
        symbol = status_symbols.get(outcome, '?')
        
        # Calculate percentage
        self._total_tests += 1
        
        # Get total test count from session
        if self._session_total > 0:
            percentage = int((self._total_tests / self._session_total) * 100)
            percentage_str = f" [{percentage:3d}%]"
        else:
            percentage_str = ""
        
        # Print result with percentage right after the check mark
        result_line = f"{indent}{color}{symbol}{percentage_str} {test_name}"
        if duration:
            result_line += f" ({duration:.3f}s)"
        result_line += colors['reset']
        print(result_line)
    
    def pytest_runtest_logreport(self, report):
        """Custom test result reporting"""
        if report.when == 'call':  # Only report on actual test execution
            parts = self._get_test_path_parts(report.nodeid)
            
            # Check if we need to print a new header
            current_key = f"{parts['test_type']}/{parts['layer']}/{parts['component']}"
            
            if current_key not in self._printed_headers:
                self._print_header(parts['test_type'], parts['layer'], parts['component'])
                self._printed_headers.add(current_key)
            
            # Print test result with "." prefix for first test in each file
            outcome = report.outcome
            duration = report.duration if hasattr(report, 'duration') else None
            
            # Add "." prefix for the first test to match pytest output
            if self.test_count == 0:
                print(".", end="", flush=True)
            
            self._print_test_result(report.nodeid, outcome, duration)
            
            # Update counters
            self.test_count += 1
            if outcome == 'passed':
                self.passed_count += 1
            elif outcome == 'failed':
                self.failed_count += 1
            elif outcome == 'skipped':
                self.skipped_count += 1
    
    def pytest_collection_modifyitems(self, session, config, items):
        """Capture total test count after collection and modify items"""
        self._session_total = len(items)
        
        # Add category marker based on path
        for item in items:
            category = categorize_test_by_path(item.nodeid)
            item.add_marker(pytest.mark.category(category))
            
            # Add layer marker based on path
            if 'domain' in item.nodeid:
                item.add_marker(pytest.mark.domain)
            elif 'application' in item.nodeid:
                item.add_marker(pytest.mark.application)
            elif 'infrastructure' in item.nodeid:
                item.add_marker(pytest.mark.infrastructure)
            elif 'api' in item.nodeid:
                item.add_marker(pytest.mark.api)
    
    def pytest_sessionfinish(self, session, exitstatus):
        """Print summary at the end"""
        # Clear the line that contains the [100%] by overwriting it
        import sys
        sys.stdout.write('\r' + ' ' * 100 + '\r')
        sys.stdout.flush()
        
        # Add a newline before our custom summary to separate from pytest output
        print()
        print("="*60)
        print("📊 TEST SUMMARY")
        print("="*60)
        print(f"Total Tests: {self.test_count}")
        print(f"Passed: {self.passed_count}")
        print(f"Failed: {self.failed_count}")
        print(f"Skipped: {self.skipped_count}")
        
        if self.failed_count == 0:
            print("\n🎉 All tests passed!")
        else:
            print(f"\n❌ {self.failed_count} test(s) failed")

def pytest_configure(config):
    """Configure pytest with custom settings and metadata."""
    # Add custom metadata
    config.addinivalue_line(
        "markers", "unit: Unit tests (fast, isolated)"
    )
    config.addinivalue_line(
        "markers", "integration: Integration tests (slower, external dependencies)"
    )
    config.addinivalue_line(
        "markers", "e2e: End-to-end tests (slowest, full system)"
    )
    config.addinivalue_line(
        "markers", "domain: Domain layer tests"
    )
    config.addinivalue_line(
        "markers", "application: Application layer tests"
    )
    config.addinivalue_line(
        "markers", "infrastructure: Infrastructure layer tests"
    )
    config.addinivalue_line(
        "markers", "api: API layer tests"
    )
    config.addinivalue_line(
        "markers", "slow: Tests that take longer than 1 second"
    )
    config.addinivalue_line(
        "markers", "critical: Critical path tests that must pass"
    )
    config.addinivalue_line(
        "markers", "flaky: Tests that occasionally fail (for monitoring)"
    )
    config.addinivalue_line(
        "markers", "category: Test category (unit, integration, e2e)"
    )
    
    # Register custom reporter
    config.pluginmanager.register(HierarchicalTestReporter(), "hierarchical_reporter")

# Performance tracking for slow tests
@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """Track test performance and mark slow tests"""
    outcome = yield
    report = outcome.get_result()
    
    if report.when == 'call' and hasattr(report, 'duration'):
        if report.duration > 1.0:  # Mark tests taking more than 1 second
            item.add_marker(pytest.mark.slow)

# Custom HTML report styling
def pytest_html_report_title(report):
    """Custom HTML report title"""
    report.title = "Backend Tutorial DDD - Test Report"

def pytest_html_results_summary(prefix, summary, postfix):
    """Custom HTML report summary"""
    prefix.extend([
        "<h2>Test Organization</h2>",
        "<p>Tests are organized by layer and component:</p>",
        "<ul>",
        "<li><strong>Unit Tests:</strong> Fast, isolated tests for individual components</li>",
        "<li><strong>Integration Tests:</strong> Tests with external dependencies</li>",
        "<li><strong>Domain Layer:</strong> Business logic and value objects</li>",
        "<li><strong>Application Layer:</strong> Service orchestration</li>",
        "<li><strong>Infrastructure Layer:</strong> External service adapters</li>",
        "</ul>"
    ])

# Environment variables to redact from reports
def pytest_html_results_table_header(cells):
    """Customize HTML report table headers"""
    try:
        from py.xml import html
        cells.insert(2, html.th("Duration"))
        cells.pop()
    except ImportError:
        pass

def pytest_html_results_table_row(report, cells):
    """Customize HTML report table rows"""
    try:
        from py.xml import html
        cells.insert(2, html.td(f"{report.duration:.3f}s"))
        cells.pop()
    except ImportError:
        pass

# Custom fixtures for better test organization
@pytest.fixture(scope="session")
def test_session_info():
    """Provide session-level test information."""
    return {
        "start_time": datetime.now(),
        "environment": os.getenv("ENVIRONMENT", "test"),
        "test_type": "unit"
    }

@pytest.fixture(scope="function")
def test_context():
    """Provide test-specific context."""
    return {
        "test_name": None,
        "test_category": None,
        "execution_time": None
    }

# Test categorization helpers
def categorize_test_by_path(nodeid):
    """Categorize test based on its path."""
    if 'unit' in nodeid:
        return 'unit'
    elif 'integration' in nodeid:
        return 'integration'
    elif 'e2e' in nodeid:
        return 'e2e'
    else:
        return 'unknown'



# Environment setup
@pytest.fixture(scope="session", autouse=True)
def setup_test_environment():
    """Set up test environment variables."""
    # Set test environment
    os.environ.setdefault("ENVIRONMENT", "test")
    os.environ.setdefault("TABLE_NAME", "test-tasks")
    os.environ.setdefault("TOPIC_ARN", "arn:aws:sns:us-east-1:123456789012:test-topic")
    
    yield
    
    # Cleanup if needed
    pass 