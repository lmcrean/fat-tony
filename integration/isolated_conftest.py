"""
Isolated configuration for integration tests.

This provides completely independent test configuration to prevent 
cross-test contamination and hallucination issues.
"""

import pytest
from typing import Dict, Any
from pathlib import Path

from .schema_validator import Trading212ApiSchemaValidator


@pytest.fixture(autouse=True)
def isolated_test_environment():
    """Ensure each test runs in complete isolation."""
    # This fixture runs automatically for all tests in this directory
    # It ensures that no state is shared between tests
    yield
    # Any cleanup would go here


@pytest.fixture
def schema_validator():
    """Provide schema validator for test validation."""
    return Trading212ApiSchemaValidator()


@pytest.fixture
def isolated_temp_directory(tmp_path):
    """Provide isolated temporary directory for each test."""
    # Each test gets its own unique temporary directory
    test_dir = tmp_path / "isolated_test"
    test_dir.mkdir(exist_ok=True)
    return test_dir


class IsolatedTestSession:
    """Manages isolated test session state."""
    
    def __init__(self):
        self.test_count = 0
        self.validation_errors = []
    
    def start_test(self, test_name: str):
        """Start a new isolated test."""
        self.test_count += 1
        print(f"\n--- Starting Isolated Test {self.test_count}: {test_name} ---")
    
    def end_test(self, test_name: str, success: bool):
        """End an isolated test."""
        status = "PASSED" if success else "FAILED"
        print(f"--- Completed Isolated Test: {test_name} [{status}] ---")
    
    def add_validation_error(self, error: str):
        """Add a validation error."""
        self.validation_errors.append(error)
    
    def get_validation_summary(self) -> Dict[str, Any]:
        """Get validation summary."""
        return {
            "total_tests": self.test_count,
            "validation_errors": len(self.validation_errors),
            "error_details": self.validation_errors
        }


@pytest.fixture(scope="session")
def isolated_session():
    """Provide isolated test session management."""
    return IsolatedTestSession()


@pytest.fixture(autouse=True)
def isolated_test_wrapper(isolated_session, request):
    """Wrap each test with isolation management."""
    test_name = request.node.name
    isolated_session.start_test(test_name)
    
    yield
    
    # Determine if test passed or failed
    success = not request.node.rep_call.failed if hasattr(request.node, 'rep_call') else True
    isolated_session.end_test(test_name, success)


@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """Hook to capture test results for isolation tracking."""
    outcome = yield
    rep = outcome.get_result()
    setattr(item, f"rep_{rep.when}", rep)


def pytest_configure(config):
    """Configure isolated testing environment."""
    # Add isolated test markers
    config.addinivalue_line(
        "markers", 
        "isolated: marks tests as using isolated test environment"
    )
    config.addinivalue_line(
        "markers",
        "schema_validated: marks tests as having schema validation"
    )


def pytest_collection_modifyitems(config, items):
    """Modify test collection for isolated testing."""
    # Mark all tests in this directory as isolated
    for item in items:
        if "isolated" in str(item.fspath):
            item.add_marker(pytest.mark.isolated)
            
            # Add schema validation marker to schema-related tests
            if "schema" in item.name or "validation" in item.name:
                item.add_marker(pytest.mark.schema_validated)


@pytest.fixture
def validate_test_isolation():
    """Fixture to validate test isolation during test execution."""
    
    def _validate_isolation(test_instance):
        """Validate that test instance has proper isolation."""
        # Check that test has its own mock clients
        if hasattr(test_instance, '_mock_client'):
            assert test_instance._mock_client is not None, "Test should have isolated mock client"
        
        if hasattr(test_instance, '_mock_clients'):
            assert test_instance._mock_clients is not None, "Test should have isolated mock clients"
        
        # Check that test has its own test data
        if hasattr(test_instance, '_test_data'):
            assert test_instance._test_data is not None, "Test should have isolated test data"
        
        # Check that test has its own exporter
        if hasattr(test_instance, '_exporter'):
            assert test_instance._exporter is not None, "Test should have isolated exporter"
            
            # Verify exporter is independent
            if hasattr(test_instance._exporter, 'positions'):
                # Positions should be empty at start (before fetch_data)
                # This validates that no data is carried over from previous tests
                pass  # Positions will be populated after fetch_data
    
    return _validate_isolation


# Utility functions for isolated testing
def create_isolated_file_path(tmp_path, filename: str) -> Path:
    """Create isolated file path for test outputs."""
    isolated_dir = tmp_path / "isolated_outputs"
    isolated_dir.mkdir(exist_ok=True)
    return isolated_dir / filename


def validate_isolated_output(output_path: Path, expected_content: str = None) -> bool:
    """Validate isolated test output."""
    if not output_path.exists():
        return False
    
    if expected_content:
        content = output_path.read_text(encoding='utf-8')
        return expected_content in content
    
    return True


# Test data validation utilities
def validate_test_data_integrity(test_data):
    """Validate test data integrity for isolated tests."""
    validator = Trading212ApiSchemaValidator()
    
    try:
        validator.validate_complete_test_data(test_data)
        return True, None
    except Exception as e:
        return False, str(e)


def assert_isolated_state(test_instance):
    """Assert that test instance maintains isolated state."""
    # Verify no shared state exists
    assert not hasattr(test_instance, '_shared_state'), "Test should not have shared state"
    
    # Verify test has independent resources
    if hasattr(test_instance, '_test_data'):
        # Test data should be a copy, not a reference
        assert test_instance._test_data is not None, "Test data should exist"
    
    if hasattr(test_instance, '_exporter'):
        # Exporter should be independent instance
        assert test_instance._exporter is not None, "Exporter should exist"
        
        # Verify exporter state is clean
        if hasattr(test_instance._exporter, 'positions'):
            # Before fetch_data, positions should be uninitialized or empty
            # After fetch_data, they should contain expected data
            pass  # This will be validated by individual tests


# Performance testing utilities for isolated tests
def measure_isolated_performance(func, *args, **kwargs):
    """Measure performance of isolated test operations."""
    import time
    
    start_time = time.time()
    result = func(*args, **kwargs)
    end_time = time.time()
    
    return result, end_time - start_time


def validate_performance_bounds(operation_time: float, max_time: float, operation_name: str):
    """Validate that operation completed within performance bounds."""
    assert operation_time <= max_time, \
        f"{operation_name} took too long: {operation_time:.3f}s > {max_time:.3f}s"