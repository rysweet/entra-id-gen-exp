"""Pytest configuration and shared fixtures for EntraSim tests."""

import pytest
import tempfile
import json
import os
from pathlib import Path
from unittest.mock import Mock, AsyncMock, patch
from typing import Dict, Any

from entrasim.config import Config
from entrasim.models import CompanyDescription, SimulationPlan
from entrasim.azure_client import AzureClient


@pytest.fixture
def temp_dir():
    """Create a temporary directory for test files."""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield Path(temp_dir)


@pytest.fixture
def mock_config():
    """Create a mock configuration for testing."""
    return Config(
        azure_tenant_id="12345678-1234-1234-1234-123456789abc",
        azure_client_id="87654321-4321-4321-4321-cba987654321",
        azure_client_secret="test-client-secret-12345",
        azure_subscription_id="11111111-2222-3333-4444-555555555555",
        log_level="INFO"
    )


@pytest.fixture
def sample_company_data():
    """Sample company data for testing."""
    return {
        "name": "Test Corporation",
        "domain": "test.com",
        "industry": "Technology",
        "size": "medium",
        "description": "A test company for unit testing",
        "complexity": "medium",
        "departments": ["Engineering", "Sales"],
        "roles": [
            {
                "name": "Software Engineer",
                "department": "Engineering",
                "count": 2,
                "seniority_level": "mid",
                "permissions": ["developers", "code_access"]
            },
            {
                "name": "Sales Representative",
                "department": "Sales",
                "count": 1,
                "seniority_level": "junior",
                "permissions": ["sales_tools"]
            }
        ]
    }


@pytest.fixture
def minimal_company_data():
    """Minimal valid company data for testing."""
    return {
        "name": "Minimal Corp",
        "domain": "minimal.com",
        "industry": "Technology",
        "size": "small",
        "roles": [
            {
                "name": "Developer",
                "department": "IT",
                "count": 1
            }
        ]
    }


@pytest.fixture
def invalid_company_data():
    """Invalid company data for testing error handling."""
    return {
        "name": "",  # Invalid: empty name
        "domain": "invalid-domain",  # Invalid: no TLD
        # Missing required fields: industry, size, roles
        "roles": []  # Invalid: empty roles list
    }


@pytest.fixture
def company_description(sample_company_data):
    """Create a CompanyDescription instance for testing."""
    return CompanyDescription(**sample_company_data)


@pytest.fixture
def simulation_plan(company_description, mock_config):
    """Create a SimulationPlan instance for testing."""
    return SimulationPlan.from_company_description(
        company=company_description,
        tenant_id=mock_config.azure_tenant_id,
        subscription_id=mock_config.azure_subscription_id
    )


@pytest.fixture
def sample_company_file(temp_dir, sample_company_data):
    """Create a temporary JSON file with sample company data."""
    file_path = temp_dir / "test_company.json"
    with open(file_path, 'w') as f:
        json.dump(sample_company_data, f, indent=2)
    return file_path


@pytest.fixture
def invalid_company_file(temp_dir, invalid_company_data):
    """Create a temporary JSON file with invalid company data."""
    file_path = temp_dir / "invalid_company.json"
    with open(file_path, 'w') as f:
        json.dump(invalid_company_data, f, indent=2)
    return file_path


@pytest.fixture
def mock_azure_client():
    """Create a mock Azure client for testing."""
    client = Mock(spec=AzureClient)
    client.authenticate = Mock(return_value=True)
    client.validate_tenant_access = AsyncMock(return_value=True)
    client.create_security_group = AsyncMock(return_value="mock-group-id")
    client.create_user = AsyncMock(return_value="mock-user-id")
    client.add_user_to_group = AsyncMock(return_value=True)
    client.execute_simulation_plan = Mock(return_value=True)
    client.cleanup_resources = AsyncMock(return_value=True)
    return client


@pytest.fixture
def mock_graph_client():
    """Create a mock Microsoft Graph client."""
    client = Mock()
    
    # Mock organization response
    org_mock = Mock()
    org_mock.value = [Mock(display_name="Test Organization")]
    client.organization.get = AsyncMock(return_value=org_mock)
    
    # Mock group creation
    group_mock = Mock()
    group_mock.id = "mock-group-id"
    client.groups.post = AsyncMock(return_value=group_mock)
    
    # Mock user creation
    user_mock = Mock()
    user_mock.id = "mock-user-id"
    client.users.post = AsyncMock(return_value=user_mock)
    
    # Mock group membership
    client.groups.by_group_id.return_value.members.ref.post = AsyncMock()
    
    return client


@pytest.fixture
def mock_credential():
    """Create a mock Azure credential."""
    return Mock()


@pytest.fixture
def mock_env_vars():
    """Mock environment variables for testing."""
    env_vars = {
        'AZURE_TENANT_ID': '12345678-1234-1234-1234-123456789abc',
        'AZURE_CLIENT_ID': '87654321-4321-4321-4321-cba987654321',
        'AZURE_CLIENT_SECRET': 'test-client-secret-12345',
        'AZURE_SUBSCRIPTION_ID': '11111111-2222-3333-4444-555555555555',
        'LOG_LEVEL': 'INFO'
    }
    
    with patch.dict(os.environ, env_vars, clear=False):
        yield env_vars


@pytest.fixture
def mock_dotenv_file(temp_dir):
    """Create a mock .env file for testing."""
    env_content = """
AZURE_TENANT_ID=12345678-1234-1234-1234-123456789abc
AZURE_CLIENT_ID=87654321-4321-4321-4321-cba987654321
AZURE_CLIENT_SECRET=test-client-secret-12345
AZURE_SUBSCRIPTION_ID=11111111-2222-3333-4444-555555555555
LOG_LEVEL=INFO
    """.strip()
    
    env_file = temp_dir / ".env"
    env_file.write_text(env_content)
    return env_file


@pytest.fixture(autouse=True)
def reset_logging():
    """Reset logging configuration after each test."""
    import logging
    yield
    # Clear any handlers that might have been added during tests
    logger = logging.getLogger('entrasim')
    logger.handlers.clear()
    logger.setLevel(logging.NOTSET)


@pytest.fixture
def capture_console_output():
    """Capture console output for testing CLI interactions."""
    from io import StringIO
    from unittest.mock import patch
    
    output_buffer = StringIO()
    
    with patch('sys.stdout', output_buffer):
        yield output_buffer


# Test markers
def pytest_configure(config):
    """Configure pytest markers."""
    config.addinivalue_line(
        "markers", "unit: unit tests that don't require external dependencies"
    )
    config.addinivalue_line(
        "markers", "integration: integration tests that may require mocked Azure services"
    )
    config.addinivalue_line(
        "markers", "slow: tests that take a longer time to run"
    )
    config.addinivalue_line(
        "markers", "azure: tests that interact with Azure services (mocked)"
    )


# Async test helpers
@pytest.fixture
def event_loop():
    """Create an event loop for async tests."""
    import asyncio
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()