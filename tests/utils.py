"""Test utility functions for EntraSim tests."""

import json
import tempfile
from pathlib import Path
from typing import Dict, Any, Optional
from unittest.mock import Mock, AsyncMock

from entrasim.config import Config
from entrasim.models import CompanyDescription, SimulationPlan


def create_test_config(
    tenant_id: str = "12345678-1234-1234-1234-123456789abc",
    client_id: str = "87654321-4321-4321-4321-cba987654321",
    client_secret: str = "test-client-secret-12345",
    subscription_id: str = "11111111-2222-3333-4444-555555555555",
    log_level: str = "INFO"
) -> Config:
    """Create a test configuration with valid Azure GUIDs."""
    return Config(
        azure_tenant_id=tenant_id,
        azure_client_id=client_id,
        azure_client_secret=client_secret,
        azure_subscription_id=subscription_id,
        log_level=log_level
    )


def create_temp_json_file(data: Dict[str, Any], suffix: str = ".json") -> Path:
    """Create a temporary JSON file with the given data."""
    temp_file = tempfile.NamedTemporaryFile(mode='w', suffix=suffix, delete=False)
    json.dump(data, temp_file, indent=2)
    temp_file.close()
    return Path(temp_file.name)


def create_temp_yaml_file(data: Dict[str, Any]) -> Path:
    """Create a temporary YAML file with the given data."""
    import yaml
    temp_file = tempfile.NamedTemporaryFile(mode='w', suffix=".yaml", delete=False)
    yaml.dump(data, temp_file, default_flow_style=False)
    temp_file.close()
    return Path(temp_file.name)


def create_test_company_description(
    name: str = "Test Company",
    domain: str = "test.com",
    user_count: int = 3
) -> CompanyDescription:
    """Create a simple test company description."""
    return CompanyDescription(
        name=name,
        domain=domain,
        industry="Technology",
        size="small",
        roles=[
            {
                "name": "Developer",
                "department": "Engineering",
                "count": user_count,
                "seniority_level": "mid"
            }
        ]
    )


def create_mock_azure_client() -> Mock:
    """Create a mock Azure client with all methods mocked."""
    client = Mock()
    client.authenticate = Mock(return_value=True)
    client.validate_tenant_access = AsyncMock(return_value=True)
    client.create_security_group = AsyncMock(return_value="mock-group-id")
    client.create_user = AsyncMock(return_value="mock-user-id")
    client.add_user_to_group = AsyncMock(return_value=True)
    client.execute_simulation_plan = Mock(return_value=True)
    client.cleanup_resources = AsyncMock(return_value=True)
    return client


def create_mock_graph_client() -> Mock:
    """Create a mock Microsoft Graph client."""
    client = Mock()
    
    # Mock organization response
    org_mock = Mock()
    org_mock.value = [Mock(display_name="Test Organization")]
    client.organization.get = AsyncMock(return_value=org_mock)
    
    # Mock group creation
    group_mock = Mock()
    group_mock.id = "mock-group-id-123"
    group_mock.display_name = "Test Group"
    client.groups.post = AsyncMock(return_value=group_mock)
    
    # Mock user creation
    user_mock = Mock()
    user_mock.id = "mock-user-id-456"
    user_mock.display_name = "Test User"
    user_mock.user_principal_name = "test@test.com"
    client.users.post = AsyncMock(return_value=user_mock)
    
    # Mock group membership
    client.groups.by_group_id.return_value.members.ref.post = AsyncMock()
    
    # Mock search/filter operations
    groups_response = Mock()
    groups_response.value = [group_mock]
    client.groups.get = AsyncMock(return_value=groups_response)
    
    users_response = Mock()
    users_response.value = [user_mock]
    client.users.get = AsyncMock(return_value=users_response)
    
    # Mock delete operations
    client.groups.by_group_id.return_value.delete = AsyncMock()
    client.users.by_user_id.return_value.delete = AsyncMock()
    
    return client


def assert_valid_simulation_plan(plan: SimulationPlan) -> None:
    """Assert that a simulation plan is valid."""
    assert plan.company is not None
    assert plan.tenant_id
    assert plan.subscription_id
    assert plan.total_users > 0
    assert plan.total_groups > 0
    assert len(plan.groups_to_create) == plan.total_groups
    assert len(plan.users_to_create) == plan.total_users
    
    # Validate user structure
    for user in plan.users_to_create:
        assert "display_name" in user
        assert "user_principal_name" in user
        assert "role" in user
        assert "department" in user
        assert "groups" in user
        assert isinstance(user["groups"], list)


def assert_company_description_valid(company: CompanyDescription) -> None:
    """Assert that a company description is valid."""
    assert company.name
    assert company.domain
    assert company.industry
    assert company.size
    assert len(company.roles) > 0
    
    for role in company.roles:
        assert role.name
        assert role.department
        assert role.count > 0


def create_cli_args_mock(
    command: str,
    input_file: str = "test.json",
    force: bool = False,
    verbose: bool = False,
    env_file: Optional[str] = None
) -> Mock:
    """Create a mock argparse.Namespace object for CLI testing."""
    args = Mock()
    args.command = command
    args.input_file = input_file
    args.force = force
    args.verbose = verbose
    args.env_file = env_file
    return args


def simulate_cli_input(input_text: str = "yes") -> Mock:
    """Create a mock for console input simulation."""
    from unittest.mock import patch
    return patch('builtins.input', return_value=input_text)


def capture_console_output():
    """Context manager to capture console output."""
    from io import StringIO
    from unittest.mock import patch
    from contextlib import contextmanager
    
    @contextmanager
    def _capture():
        stdout_capture = StringIO()
        stderr_capture = StringIO()
        with patch('sys.stdout', stdout_capture), patch('sys.stderr', stderr_capture):
            yield stdout_capture, stderr_capture
    
    return _capture()


class MockConsole:
    """Mock console for testing rich output."""
    
    def __init__(self):
        self.printed_messages = []
        self.input_responses = ["yes"]
        self.input_call_count = 0
    
    def print(self, *args, **kwargs):
        """Mock print method that captures messages."""
        message = " ".join(str(arg) for arg in args)
        self.printed_messages.append(message)
    
    def input(self, prompt: str = "") -> str:
        """Mock input method that returns predefined responses."""
        if self.input_call_count < len(self.input_responses):
            response = self.input_responses[self.input_call_count]
            self.input_call_count += 1
            return response
        return "yes"  # default response
    
    def set_input_responses(self, responses: list):
        """Set the responses for input calls."""
        self.input_responses = responses
        self.input_call_count = 0
    
    def get_printed_messages(self) -> list:
        """Get all printed messages."""
        return self.printed_messages
    
    def clear_messages(self):
        """Clear all captured messages."""
        self.printed_messages.clear()


def create_invalid_json_file() -> Path:
    """Create a temporary file with invalid JSON."""
    temp_file = tempfile.NamedTemporaryFile(mode='w', suffix=".json", delete=False)
    temp_file.write('{"invalid": json syntax}')  # Missing quotes around 'json'
    temp_file.close()
    return Path(temp_file.name)


def create_malformed_yaml_file() -> Path:
    """Create a temporary file with invalid YAML."""
    temp_file = tempfile.NamedTemporaryFile(mode='w', suffix=".yaml", delete=False)
    temp_file.write("""
name: Test Company
roles:
  - name: Developer
    department: IT
      count: 1  # Invalid indentation
""")
    temp_file.close()
    return Path(temp_file.name)


def cleanup_temp_file(file_path: Path) -> None:
    """Clean up a temporary file."""
    try:
        file_path.unlink()
    except FileNotFoundError:
        pass


# Test data generators
def generate_large_company_data(user_count: int = 100) -> Dict[str, Any]:
    """Generate a large company configuration for performance testing."""
    departments = ["Engineering", "Sales", "Marketing", "HR", "Finance", "Operations"]
    roles = []
    
    users_per_dept = user_count // len(departments)
    remainder = user_count % len(departments)
    
    for i, dept in enumerate(departments):
        count = users_per_dept + (1 if i < remainder else 0)
        roles.append({
            "name": f"{dept} Specialist",
            "department": dept,
            "count": count,
            "seniority_level": "mid"
        })
    
    return {
        "name": "Large Test Corporation",
        "domain": "large-test.com",
        "industry": "Technology",
        "size": "large",
        "description": f"Large test company with {user_count} users",
        "complexity": "complex",
        "departments": departments,
        "roles": roles
    }


# Environment helpers
def create_test_env_file(temp_dir: Path, **kwargs) -> Path:
    """Create a test .env file with specified variables."""
    defaults = {
        'AZURE_TENANT_ID': '12345678-1234-1234-1234-123456789abc',
        'AZURE_CLIENT_ID': '87654321-4321-4321-4321-cba987654321',
        'AZURE_CLIENT_SECRET': 'test-client-secret-12345',
        'AZURE_SUBSCRIPTION_ID': '11111111-2222-3333-4444-555555555555',
        'LOG_LEVEL': 'INFO'
    }
    defaults.update(kwargs)
    
    env_file = temp_dir / ".env"
    with open(env_file, 'w') as f:
        for key, value in defaults.items():
            f.write(f"{key}={value}\n")
    
    return env_file