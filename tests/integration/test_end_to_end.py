"""End-to-end integration tests that exercise all commands and scenarios from the demo guide."""

import pytest
import os
import subprocess
import tempfile
from pathlib import Path
from unittest.mock import Mock, AsyncMock, patch, call
import json

from entrasim.core import EntraSimCore
from entrasim.cli import main, handle_create_command, handle_validate_command, handle_cleanup_command
from entrasim.config import Config, get_config
from entrasim.azure_client import AzureClient
from tests.utils import create_test_config, create_temp_json_file, MockConsole


class TestEndToEndWorkflow:
    """Test the complete end-to-end workflow from the demo guide."""
    
    @pytest.mark.integration
    def test_complete_workflow_validate_create_cleanup(self, mock_env_vars, temp_dir):
        """Test the complete workflow: validate → create → cleanup."""
        # Create test company file
        test_company = {
            "name": "Integration Test Corp",
            "domain": "integration-test.com",
            "industry": "Technology",
            "size": "small",
            "roles": [
                {
                    "name": "Test Engineer",
                    "department": "Engineering",
                    "count": 2,
                    "seniority_level": "mid"
                }
            ]
        }
        
        company_file = temp_dir / "test_company.json"
        with open(company_file, 'w') as f:
            json.dump(test_company, f, indent=2)
        
        config = create_test_config()
        
        # Mock Azure client for all operations
        mock_azure_client = Mock()
        mock_azure_client.authenticate.return_value = True
        mock_azure_client.validate_tenant_access = AsyncMock(return_value=True)
        mock_azure_client.execute_simulation_plan.return_value = True
        mock_azure_client.cleanup_resources = AsyncMock(return_value=True)
        
        with patch('entrasim.core.create_azure_client', return_value=mock_azure_client), \
             patch('entrasim.cli.create_azure_client', return_value=mock_azure_client), \
             patch('entrasim.cli.console'), \
             patch('entrasim.core.console'), \
             patch('asyncio.run', return_value=True):
            
            # Step 1: Validate
            core = EntraSimCore(config)
            assert core.validate_input(company_file) is True
            
            # Step 2: Parse and generate plan
            company_desc = core.parse_company_description(company_file)
            plan = core.generate_simulation_plan(company_desc)
            
            assert plan.total_users == 2
            assert plan.total_groups >= 2  # At least Engineering + test_engineer_group
            assert "Engineering" in plan.groups_to_create
            assert "test_engineer_group" in plan.groups_to_create
            
            # Step 3: Execute creation
            assert core.execute_simulation_plan(plan) is True
            mock_azure_client.execute_simulation_plan.assert_called_once_with(plan)
            
            # Step 4: Cleanup
            assert core.cleanup_simulation(plan) is True
            mock_azure_client.cleanup_resources.assert_called_once_with(plan)
    
    @pytest.mark.integration
    def test_cli_validate_command_workflow(self, temp_dir):
        """Test CLI validate command as described in demo guide."""
        # Create test company file matching sample_company.json structure
        test_company = {
            "name": "CLI Test Corporation",
            "domain": "cli-test.com",
            "industry": "Technology",
            "size": "medium",
            "departments": ["Engineering", "Sales"],
            "roles": [
                {
                    "name": "Software Engineer",
                    "department": "Engineering",
                    "count": 3,
                    "seniority_level": "mid"
                }
            ]
        }
        
        company_file = temp_dir / "cli_test.json"
        with open(company_file, 'w') as f:
            json.dump(test_company, f, indent=2)
        
        # Mock CLI args
        args = Mock()
        args.input_file = str(company_file)
        
        with patch('entrasim.cli.console') as mock_console:
            result = handle_validate_command(args)
            assert result is True
            
            # Verify output messages
            print_calls = [call[0][0] for call in mock_console.print.call_args_list]
            assert any("validation successful" in str(call).lower() for call in print_calls)
    
    @pytest.mark.integration
    def test_cli_create_command_workflow(self, mock_env_vars, temp_dir):
        """Test CLI create command as described in demo guide."""
        test_company = {
            "name": "CLI Create Test Corp",
            "domain": "cli-create-test.com",
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
        
        company_file = temp_dir / "create_test.json"
        with open(company_file, 'w') as f:
            json.dump(test_company, f, indent=2)
        
        # Mock CLI args
        args = Mock()
        args.input_file = str(company_file)
        args.force = True  # Skip confirmation
        args.env_file = None
        
        config = create_test_config()
        
        # Mock Azure operations
        mock_azure_client = Mock()
        mock_azure_client.authenticate.return_value = True
        mock_azure_client.execute_simulation_plan.return_value = True
        
        with patch('entrasim.cli.EntraSimCore') as mock_core_class, \
             patch('entrasim.cli.validate_azure_credentials', return_value=True), \
             patch('entrasim.cli.console'):
            
            # Setup mock core
            mock_core = Mock()
            mock_core.validate_input.return_value = True
            mock_core.parse_company_description.return_value = Mock(
                name="CLI Create Test Corp",
                domain="cli-create-test.com"
            )
            mock_core.generate_simulation_plan.return_value = Mock(
                total_users=1,
                total_groups=2,
                company=Mock(name="CLI Create Test Corp", domain="cli-create-test.com")
            )
            mock_core.execute_simulation_plan.return_value = True
            mock_core_class.return_value = mock_core
            
            result = handle_create_command(args, config)
            assert result is True
    
    @pytest.mark.integration
    def test_cli_cleanup_command_workflow(self, mock_env_vars, temp_dir):
        """Test CLI cleanup command as described in demo guide."""
        test_company = {
            "name": "CLI Cleanup Test Corp",
            "domain": "cli-cleanup-test.com",
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
        
        company_file = temp_dir / "cleanup_test.json"
        with open(company_file, 'w') as f:
            json.dump(test_company, f, indent=2)
        
        # Mock CLI args
        args = Mock()
        args.input_file = str(company_file)
        args.force = True  # Skip confirmation
        args.env_file = None
        
        config = create_test_config()
        
        with patch('entrasim.cli.EntraSimCore') as mock_core_class, \
             patch('entrasim.cli.validate_azure_credentials', return_value=True), \
             patch('entrasim.cli.console'):
            
            # Setup mock core
            mock_core = Mock()
            mock_core.validate_input.return_value = True
            mock_core.parse_company_description.return_value = Mock(
                name="CLI Cleanup Test Corp",
                domain="cli-cleanup-test.com"
            )
            mock_core.generate_simulation_plan.return_value = Mock(
                total_users=1,
                total_groups=2,
                company=Mock(name="CLI Cleanup Test Corp", domain="cli-cleanup-test.com")
            )
            mock_core.cleanup_simulation.return_value = True
            mock_core_class.return_value = mock_core
            
            result = handle_cleanup_command(args, config)
            assert result is True


class TestErrorHandlingScenarios:
    """Test error handling scenarios from the demo guide."""
    
    @pytest.mark.integration
    def test_missing_credentials_error(self):
        """Test error handling when Azure credentials are missing."""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ValueError, match="Missing required Azure credentials"):
                config = get_config()
                config.validate_required_credentials()
    
    @pytest.mark.integration
    def test_invalid_file_format_error(self, temp_dir):
        """Test error handling with invalid file formats."""
        # Test invalid JSON
        invalid_json_file = temp_dir / "invalid.json"
        invalid_json_file.write_text('{"invalid": json syntax}')
        
        config = create_test_config()
        core = EntraSimCore(config)
        
        assert core.validate_input(invalid_json_file) is False
    
    @pytest.mark.integration
    def test_network_failure_simulation(self, mock_env_vars, temp_dir):
        """Test handling of network failures during Azure operations."""
        test_company = {
            "name": "Network Test Corp",
            "domain": "network-test.com",
            "industry": "Technology",
            "size": "small",
            "roles": [{"name": "Developer", "department": "IT", "count": 1}]
        }
        
        company_file = temp_dir / "network_test.json"
        with open(company_file, 'w') as f:
            json.dump(test_company, f, indent=2)
        
        config = create_test_config()
        core = EntraSimCore(config)
        
        # Mock network failure
        mock_azure_client = Mock()
        mock_azure_client.authenticate.side_effect = Exception("Network timeout")
        
        with patch('entrasim.core.create_azure_client', return_value=mock_azure_client), \
             patch('entrasim.core.console'):
            
            assert core.validate_azure_connection() is False
    
    @pytest.mark.integration
    def test_azure_authentication_failure(self, mock_env_vars):
        """Test handling of Azure authentication failures."""
        config = create_test_config()
        core = EntraSimCore(config)
        
        # Mock authentication failure
        mock_azure_client = Mock()
        mock_azure_client.authenticate.return_value = False
        
        with patch('entrasim.core.create_azure_client', return_value=mock_azure_client), \
             patch('entrasim.core.console'):
            
            assert core.validate_azure_connection() is False
    
    @pytest.mark.integration
    def test_invalid_company_data_validation(self, temp_dir):
        """Test validation of invalid company data."""
        invalid_company = {
            "name": "",  # Invalid: empty name
            "domain": "invalid-domain",  # Invalid: no TLD
            "industry": "",
            "size": "invalid_size",
            "roles": []  # Invalid: empty roles
        }
        
        company_file = temp_dir / "invalid_company.json"
        with open(company_file, 'w') as f:
            json.dump(invalid_company, f, indent=2)
        
        config = create_test_config()
        core = EntraSimCore(config)
        
        # Should fail validation due to invalid data
        assert core.validate_input(company_file) is False


class TestConfigurationScenarios:
    """Test configuration scenarios from the demo guide."""
    
    @pytest.mark.integration
    def test_custom_env_file_loading(self, temp_dir):
        """Test loading configuration from custom .env file."""
        # Create custom .env file
        custom_env = temp_dir / "custom.env"
        custom_env.write_text("""
AZURE_TENANT_ID=custom-tenant-id-1234-5678-9abc-def012345678
AZURE_CLIENT_ID=custom-client-id-1234-5678-9abc-def012345678
AZURE_CLIENT_SECRET=custom-client-secret-abcdef123456
AZURE_SUBSCRIPTION_ID=custom-sub-id-1234-5678-9abc-def012345678
LOG_LEVEL=DEBUG
        """.strip())
        
        with patch.dict(os.environ, {}, clear=True):
            config = Config.load_from_env(str(custom_env))
            
            assert config.azure_tenant_id == "custom-tenant-id-1234-5678-9abc-def012345678"
            assert config.azure_client_id == "custom-client-id-1234-5678-9abc-def012345678"
            assert config.azure_client_secret == "custom-client-secret-abcdef123456"
            assert config.azure_subscription_id == "custom-sub-id-1234-5678-9abc-def012345678"
            assert config.log_level == "DEBUG"
    
    @pytest.mark.integration
    def test_verbose_logging_mode(self, mock_env_vars, temp_dir):
        """Test verbose logging mode functionality."""
        test_company = {
            "name": "Verbose Test Corp",
            "domain": "verbose-test.com",
            "industry": "Technology",
            "size": "small",
            "roles": [{"name": "Developer", "department": "IT", "count": 1}]
        }
        
        company_file = temp_dir / "verbose_test.json"
        with open(company_file, 'w') as f:
            json.dump(test_company, f, indent=2)
        
        config = create_test_config()
        config.log_level = 'DEBUG'  # Verbose mode
        
        core = EntraSimCore(config)
        company_desc = core.parse_company_description(company_file)
        
        # Should generate plan without errors in debug mode
        plan = core.generate_simulation_plan(company_desc)
        assert plan is not None
    
    @pytest.mark.integration
    def test_force_mode_operations(self, mock_env_vars, temp_dir):
        """Test force mode operations (skip confirmations)."""
        test_company = {
            "name": "Force Mode Test Corp",
            "domain": "force-test.com",
            "industry": "Technology",
            "size": "small",
            "roles": [{"name": "Developer", "department": "IT", "count": 1}]
        }
        
        company_file = temp_dir / "force_test.json"
        with open(company_file, 'w') as f:
            json.dump(test_company, f, indent=2)
        
        # Test create command with force mode
        args = Mock()
        args.input_file = str(company_file)
        args.force = True
        args.env_file = None
        
        config = create_test_config()
        
        mock_azure_client = Mock()
        mock_azure_client.authenticate.return_value = True
        mock_azure_client.execute_simulation_plan.return_value = True
        
        with patch('entrasim.cli.EntraSimCore') as mock_core_class, \
             patch('entrasim.cli.validate_azure_credentials', return_value=True), \
             patch('entrasim.cli.confirm_operation') as mock_confirm, \
             patch('entrasim.cli.console'):
            
            mock_core = Mock()
            mock_core.validate_input.return_value = True
            mock_core.parse_company_description.return_value = Mock(
                name="Force Mode Test Corp",
                domain="force-test.com"
            )
            mock_core.generate_simulation_plan.return_value = Mock(
                total_users=1,
                total_groups=2,
                company=Mock(name="Force Mode Test Corp", domain="force-test.com")
            )
            mock_core.execute_simulation_plan.return_value = True
            mock_core_class.return_value = mock_core
            
            result = handle_create_command(args, config)
            assert result is True
            
            # In force mode, confirm_operation should be called with force=True
            mock_confirm.assert_called_once()
            assert mock_confirm.call_args[1]['force'] is True


class TestFileFormatSupport:
    """Test support for different file formats."""
    
    @pytest.mark.integration
    def test_json_file_support(self, temp_dir):
        """Test JSON file format support."""
        test_company = {
            "name": "JSON Test Corp",
            "domain": "json-test.com",
            "industry": "Technology",
            "size": "small",
            "roles": [{"name": "Developer", "department": "IT", "count": 1}]
        }
        
        json_file = temp_dir / "test.json"
        with open(json_file, 'w') as f:
            json.dump(test_company, f, indent=2)
        
        config = create_test_config()
        core = EntraSimCore(config)
        
        assert core.validate_input(json_file) is True
        company_desc = core.parse_company_description(json_file)
        assert company_desc.name == "JSON Test Corp"
    
    @pytest.mark.integration
    def test_yaml_file_support(self, temp_dir):
        """Test YAML file format support."""
        yaml_content = """
name: YAML Test Corp
domain: yaml-test.com
industry: Technology
size: small
roles:
  - name: Developer
    department: IT
    count: 1
"""
        
        yaml_file = temp_dir / "test.yaml"
        yaml_file.write_text(yaml_content)
        
        config = create_test_config()
        core = EntraSimCore(config)
        
        # Test depends on PyYAML being available
        try:
            assert core.validate_input(yaml_file) is True
            company_desc = core.parse_company_description(yaml_file)
            assert company_desc.name == "YAML Test Corp"
        except ValueError as e:
            if "PyYAML is not installed" in str(e):
                pytest.skip("PyYAML not available for testing")
            else:
                raise
    
    @pytest.mark.integration
    def test_yml_extension_support(self, temp_dir):
        """Test .yml file extension support."""
        yml_content = """
name: YML Test Corp
domain: yml-test.com
industry: Technology
size: small
roles:
  - name: Developer
    department: IT
    count: 1
"""
        
        yml_file = temp_dir / "test.yml"
        yml_file.write_text(yml_content)
        
        config = create_test_config()
        core = EntraSimCore(config)
        
        # Test depends on PyYAML being available
        try:
            assert core.validate_input(yml_file) is True
            company_desc = core.parse_company_description(yml_file)
            assert company_desc.name == "YML Test Corp"
        except ValueError as e:
            if "PyYAML is not installed" in str(e):
                pytest.skip("PyYAML not available for testing")
            else:
                raise


class TestAzureConnectivityMocking:
    """Test Azure connectivity with comprehensive mocking."""
    
    @pytest.mark.integration
    @pytest.mark.azure
    def test_azure_authentication_flow(self, mock_env_vars):
        """Test complete Azure authentication flow."""
        config = create_test_config()
        
        # Mock Azure SDK components
        mock_credential = Mock()
        mock_graph_client = Mock()
        
        # Mock organization response for tenant validation
        org_mock = Mock()
        org_mock.value = [Mock(display_name="Test Organization")]
        mock_graph_client.organization.get = AsyncMock(return_value=org_mock)
        
        with patch('entrasim.azure_client.ClientSecretCredential', return_value=mock_credential), \
             patch('entrasim.azure_client.GraphServiceClient', return_value=mock_graph_client), \
             patch('entrasim.azure_client.console'):
            
            client = AzureClient(config)
            
            # Test authentication
            assert client.authenticate() is True
            assert client._credential == mock_credential
            assert client._graph_client == mock_graph_client
    
    @pytest.mark.integration
    @pytest.mark.azure
    @pytest.mark.asyncio
    async def test_azure_resource_creation_simulation(self, mock_env_vars):
        """Test Azure resource creation simulation."""
        config = create_test_config()
        client = AzureClient(config)
        
        # Mock graph client
        mock_graph_client = Mock()
        client._graph_client = mock_graph_client
        
        # Mock group creation
        group_mock = Mock()
        group_mock.id = "test-group-id-123"
        mock_graph_client.groups.post = AsyncMock(return_value=group_mock)
        
        # Mock user creation
        user_mock = Mock()
        user_mock.id = "test-user-id-456"
        mock_graph_client.users.post = AsyncMock(return_value=user_mock)
        
        # Mock group membership
        mock_graph_client.groups.by_group_id.return_value.members.ref.post = AsyncMock()
        
        with patch('entrasim.azure_client.console'):
            # Test group creation
            group_id = await client.create_security_group("Test Group", "Test Description")
            assert group_id == "test-group-id-123"
            
            # Test user creation
            user_data = {
                "display_name": "Test User",
                "user_principal_name": "test@test.com"
            }
            user_id = await client.create_user(user_data)
            assert user_id == "test-user-id-456"
            
            # Test group membership
            result = await client.add_user_to_group(user_id, group_id)
            assert result is True
    
    @pytest.mark.integration
    @pytest.mark.azure
    @pytest.mark.asyncio
    async def test_azure_cleanup_simulation(self, mock_env_vars, simulation_plan):
        """Test Azure resource cleanup simulation."""
        config = create_test_config()
        client = AzureClient(config)
        
        # Mock graph client
        mock_graph_client = Mock()
        client._graph_client = mock_graph_client
        
        # Mock search responses
        users_response = Mock()
        users_response.value = [Mock(id="user-to-delete")]
        
        groups_response = Mock()
        groups_response.value = [Mock(id="group-to-delete")]
        
        mock_graph_client.users.get = AsyncMock(return_value=users_response)
        mock_graph_client.groups.get = AsyncMock(return_value=groups_response)
        
        # Mock delete operations
        mock_graph_client.users.by_user_id.return_value.delete = AsyncMock()
        mock_graph_client.groups.by_group_id.return_value.delete = AsyncMock()
        
        with patch('entrasim.azure_client.console'):
            result = await client.cleanup_resources(simulation_plan)
            assert result is True