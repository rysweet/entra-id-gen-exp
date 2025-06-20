"""Unit tests for core business logic."""

import pytest
import json
import tempfile
from pathlib import Path
from unittest.mock import Mock, AsyncMock, patch

from entrasim.core import EntraSimCore, validate_input_file
from entrasim.models import CompanyDescription, SimulationPlan
from tests.utils import create_temp_json_file, create_invalid_json_file, create_malformed_yaml_file


class TestEntraSimCore:
    """Test the EntraSimCore class."""
    
    @pytest.mark.unit
    def test_core_initialization(self, mock_config):
        """Test core initialization."""
        core = EntraSimCore(mock_config)
        assert core.config == mock_config
        assert core.azure_client is None
    
    @pytest.mark.unit
    def test_validate_input_success(self, mock_config, sample_company_file):
        """Test successful input validation."""
        core = EntraSimCore(mock_config)
        assert core.validate_input(sample_company_file) is True
    
    @pytest.mark.unit
    def test_validate_input_file_not_exists(self, mock_config):
        """Test input validation with non-existent file."""
        core = EntraSimCore(mock_config)
        non_existent_file = Path("/path/to/nonexistent/file.json")
        assert core.validate_input(non_existent_file) is False
    
    @pytest.mark.unit
    def test_validate_input_invalid_extension(self, mock_config, temp_dir):
        """Test input validation with invalid file extension."""
        core = EntraSimCore(mock_config)
        
        # Create a file with invalid extension
        invalid_file = temp_dir / "test.txt"
        invalid_file.write_text("test content")
        
        assert core.validate_input(invalid_file) is False
    
    @pytest.mark.unit
    def test_validate_input_invalid_json(self, mock_config):
        """Test input validation with invalid JSON."""
        core = EntraSimCore(mock_config)
        invalid_file = create_invalid_json_file()
        
        try:
            assert core.validate_input(invalid_file) is False
        finally:
            invalid_file.unlink()
    
    @pytest.mark.unit
    def test_parse_company_description_json(self, mock_config, sample_company_data):
        """Test parsing JSON company description."""
        core = EntraSimCore(mock_config)
        json_file = create_temp_json_file(sample_company_data)
        
        try:
            company = core.parse_company_description(json_file)
            assert isinstance(company, CompanyDescription)
            assert company.name == sample_company_data["name"]
            assert company.domain == sample_company_data["domain"]
        finally:
            json_file.unlink()
    
    @pytest.mark.unit
    def test_parse_company_description_yaml(self, mock_config, sample_company_data):
        """Test parsing YAML company description."""
        core = EntraSimCore(mock_config)
        
        # Create YAML file
        yaml_content = """
name: Test Corporation
domain: test.com
industry: Technology
size: medium
roles:
  - name: Developer
    department: Engineering
    count: 1
"""
        yaml_file = tempfile.NamedTemporaryFile(mode='w', suffix=".yaml", delete=False)
        yaml_file.write(yaml_content)
        yaml_file.close()
        yaml_path = Path(yaml_file.name)
        
        try:
            company = core.parse_company_description(yaml_path)
            assert isinstance(company, CompanyDescription)
            assert company.name == "Test Corporation"
            assert company.domain == "test.com"
        finally:
            yaml_path.unlink()
    
    @pytest.mark.unit
    def test_parse_company_description_invalid_json(self, mock_config):
        """Test parsing invalid JSON raises appropriate error."""
        core = EntraSimCore(mock_config)
        invalid_file = create_invalid_json_file()
        
        try:
            with pytest.raises(ValueError, match="Invalid JSON format"):
                core.parse_company_description(invalid_file)
        finally:
            invalid_file.unlink()
    
    @pytest.mark.unit
    def test_parse_company_description_yaml_not_available(self, mock_config):
        """Test parsing YAML when PyYAML is not available."""
        core = EntraSimCore(mock_config)
        
        yaml_file = tempfile.NamedTemporaryFile(mode='w', suffix=".yaml", delete=False)
        yaml_file.write("name: Test\n")
        yaml_file.close()
        yaml_path = Path(yaml_file.name)
        
        try:
            with patch('entrasim.core.yaml', None):
                with pytest.raises(ValueError, match="PyYAML is not installed"):
                    core.parse_company_description(yaml_path)
        finally:
            yaml_path.unlink()
    
    @pytest.mark.unit
    def test_generate_simulation_plan(self, mock_config, company_description):
        """Test simulation plan generation."""
        core = EntraSimCore(mock_config)
        plan = core.generate_simulation_plan(company_description)
        
        assert isinstance(plan, SimulationPlan)
        assert plan.company == company_description
        assert plan.tenant_id == mock_config.azure_tenant_id
        assert plan.subscription_id == mock_config.azure_subscription_id
        assert plan.total_users == company_description.get_total_users()
        assert plan.total_groups > 0
    
    @pytest.mark.unit
    def test_generate_simulation_plan_debug_logging(self, mock_config, company_description):
        """Test simulation plan generation with debug logging."""
        mock_config.log_level = 'DEBUG'
        core = EntraSimCore(mock_config)
        
        # Should not raise any exceptions
        plan = core.generate_simulation_plan(company_description)
        assert isinstance(plan, SimulationPlan)
    
    @pytest.mark.unit
    def test_validate_azure_connection_success(self, mock_config, mock_azure_client):
        """Test successful Azure connection validation."""
        core = EntraSimCore(mock_config)
        
        with patch('entrasim.core.create_azure_client', return_value=mock_azure_client):
            assert core.validate_azure_connection() is True
            assert core.azure_client == mock_azure_client
    
    @pytest.mark.unit
    def test_validate_azure_connection_auth_failure(self, mock_config):
        """Test Azure connection validation with auth failure."""
        core = EntraSimCore(mock_config)
        
        mock_client = Mock()
        mock_client.authenticate.return_value = False
        
        with patch('entrasim.core.create_azure_client', return_value=mock_client):
            assert core.validate_azure_connection() is False
    
    @pytest.mark.unit
    def test_validate_azure_connection_exception(self, mock_config):
        """Test Azure connection validation with exception."""
        core = EntraSimCore(mock_config)
        
        mock_client = Mock()
        mock_client.authenticate.side_effect = Exception("Connection error")
        
        with patch('entrasim.core.create_azure_client', return_value=mock_client):
            assert core.validate_azure_connection() is False
    
    @pytest.mark.unit
    def test_execute_simulation_plan_success(self, mock_config, simulation_plan, mock_azure_client):
        """Test successful simulation plan execution."""
        core = EntraSimCore(mock_config)
        core.azure_client = mock_azure_client
        
        assert core.execute_simulation_plan(simulation_plan) is True
        mock_azure_client.execute_simulation_plan.assert_called_once_with(simulation_plan)
    
    @pytest.mark.unit
    def test_execute_simulation_plan_no_client(self, mock_config, simulation_plan, mock_azure_client):
        """Test simulation plan execution creates client if needed."""
        core = EntraSimCore(mock_config)
        # No azure_client set initially
        
        with patch('entrasim.core.create_azure_client', return_value=mock_azure_client):
            assert core.execute_simulation_plan(simulation_plan) is True
            mock_azure_client.execute_simulation_plan.assert_called_once_with(simulation_plan)
    
    @pytest.mark.unit
    def test_execute_simulation_plan_failure(self, mock_config, simulation_plan):
        """Test simulation plan execution failure."""
        core = EntraSimCore(mock_config)
        
        mock_client = Mock()
        mock_client.execute_simulation_plan.return_value = False
        core.azure_client = mock_client
        
        assert core.execute_simulation_plan(simulation_plan) is False
    
    @pytest.mark.unit
    def test_execute_simulation_plan_exception(self, mock_config, simulation_plan):
        """Test simulation plan execution with exception."""
        core = EntraSimCore(mock_config)
        
        mock_client = Mock()
        mock_client.execute_simulation_plan.side_effect = Exception("Execution error")
        core.azure_client = mock_client
        
        assert core.execute_simulation_plan(simulation_plan) is False
    
    @pytest.mark.unit
    def test_cleanup_simulation_success(self, mock_config, simulation_plan, mock_azure_client):
        """Test successful simulation cleanup."""
        core = EntraSimCore(mock_config)
        core.azure_client = mock_azure_client
        
        with patch('asyncio.run', return_value=True):
            assert core.cleanup_simulation(simulation_plan) is True
            mock_azure_client.cleanup_resources.assert_called_once_with(simulation_plan)
    
    @pytest.mark.unit
    def test_cleanup_simulation_no_client(self, mock_config, simulation_plan, mock_azure_client):
        """Test simulation cleanup creates and authenticates client if needed."""
        core = EntraSimCore(mock_config)
        
        with patch('entrasim.core.create_azure_client', return_value=mock_azure_client), \
             patch('asyncio.run', return_value=True):
            assert core.cleanup_simulation(simulation_plan) is True
    
    @pytest.mark.unit
    def test_cleanup_simulation_auth_failure(self, mock_config, simulation_plan):
        """Test simulation cleanup with authentication failure."""
        core = EntraSimCore(mock_config)
        
        mock_client = Mock()
        mock_client.authenticate.return_value = False
        
        with patch('entrasim.core.create_azure_client', return_value=mock_client):
            assert core.cleanup_simulation(simulation_plan) is False
    
    @pytest.mark.unit
    def test_cleanup_simulation_failure(self, mock_config, simulation_plan, mock_azure_client):
        """Test simulation cleanup failure."""
        core = EntraSimCore(mock_config)
        core.azure_client = mock_azure_client
        
        with patch('asyncio.run', return_value=False):
            assert core.cleanup_simulation(simulation_plan) is False
    
    @pytest.mark.unit
    def test_cleanup_simulation_exception(self, mock_config, simulation_plan, mock_azure_client):
        """Test simulation cleanup with exception."""
        core = EntraSimCore(mock_config)
        core.azure_client = mock_azure_client
        
        with patch('asyncio.run', side_effect=Exception("Cleanup error")):
            assert core.cleanup_simulation(simulation_plan) is False


class TestValidateInputFile:
    """Test the standalone validate_input_file function."""
    
    @pytest.mark.unit
    def test_validate_input_file_success(self, sample_company_file):
        """Test successful input file validation."""
        assert validate_input_file(sample_company_file) is True
    
    @pytest.mark.unit
    def test_validate_input_file_string_path(self, sample_company_file):
        """Test validation with string path."""
        assert validate_input_file(str(sample_company_file)) is True
    
    @pytest.mark.unit
    def test_validate_input_file_not_exists(self):
        """Test validation with non-existent file."""
        assert validate_input_file("/path/to/nonexistent/file.json") is False
    
    @pytest.mark.unit
    def test_validate_input_file_invalid_extension(self, temp_dir):
        """Test validation with invalid file extension."""
        invalid_file = temp_dir / "test.txt"
        invalid_file.write_text("test content")
        
        assert validate_input_file(invalid_file) is False
    
    @pytest.mark.unit
    def test_validate_input_file_invalid_json(self):
        """Test validation with invalid JSON."""
        invalid_file = create_invalid_json_file()
        
        try:
            assert validate_input_file(invalid_file) is False
        finally:
            invalid_file.unlink()
    
    @pytest.mark.unit
    def test_validate_input_file_yaml_not_available(self):
        """Test validation when PyYAML is not available."""
        yaml_file = tempfile.NamedTemporaryFile(mode='w', suffix=".yaml", delete=False)
        yaml_file.write("name: Test\n")
        yaml_file.close()
        yaml_path = Path(yaml_file.name)
        
        try:
            with patch('entrasim.core.yaml', None):
                assert validate_input_file(yaml_path) is False
        finally:
            yaml_path.unlink()
    
    @pytest.mark.unit
    def test_validate_input_file_minimal_valid(self, minimal_company_data):
        """Test validation with minimal valid company data."""
        json_file = create_temp_json_file(minimal_company_data)
        
        try:
            assert validate_input_file(json_file) is True
        finally:
            json_file.unlink()
    
    @pytest.mark.unit
    def test_validate_input_file_invalid_company_data(self, invalid_company_data):
        """Test validation with invalid company data."""
        json_file = create_temp_json_file(invalid_company_data)
        
        try:
            assert validate_input_file(json_file) is False
        finally:
            json_file.unlink()


class TestCoreEdgeCases:
    """Test edge cases and error conditions."""
    
    @pytest.mark.unit
    def test_parse_empty_json_file(self, mock_config, temp_dir):
        """Test parsing empty JSON file."""
        core = EntraSimCore(mock_config)
        
        empty_file = temp_dir / "empty.json"
        empty_file.write_text("")
        
        with pytest.raises(ValueError, match="Invalid JSON format"):
            core.parse_company_description(empty_file)
    
    @pytest.mark.unit
    def test_parse_json_with_missing_required_fields(self, mock_config):
        """Test parsing JSON with missing required fields."""
        core = EntraSimCore(mock_config)
        
        incomplete_data = {"name": "Test Company"}  # Missing required fields
        json_file = create_temp_json_file(incomplete_data)
        
        try:
            with pytest.raises(ValueError, match="Error parsing company description"):
                core.parse_company_description(json_file)
        finally:
            json_file.unlink()
    
    @pytest.mark.unit
    def test_generate_simulation_plan_with_exception(self, mock_config):
        """Test simulation plan generation with exception in model creation."""
        core = EntraSimCore(mock_config)
        
        # Mock a company description that would cause an error
        invalid_company = Mock()
        invalid_company.get_departments.side_effect = Exception("Test error")
        
        with pytest.raises(ValueError, match="Error generating simulation plan"):
            core.generate_simulation_plan(invalid_company)
    
    @pytest.mark.unit
    def test_validate_azure_connection_credential_error(self, mock_config):
        """Test Azure connection validation with credential validation error."""
        # Create a config with invalid credentials
        invalid_config = Mock()
        invalid_config.validate_required_credentials.side_effect = ValueError("Invalid credentials")
        
        core = EntraSimCore(invalid_config)
        assert core.validate_azure_connection() is False
    
    @pytest.mark.unit
    def test_core_with_different_file_extensions(self, mock_config, sample_company_data):
        """Test core handles different valid file extensions."""
        core = EntraSimCore(mock_config)
        
        # Test .yml extension
        yml_file = tempfile.NamedTemporaryFile(mode='w', suffix=".yml", delete=False)
        yml_content = """
name: Test Corporation
domain: test.com
industry: Technology
size: medium
roles:
  - name: Developer
    department: Engineering
    count: 1
"""
        yml_file.write(yml_content)
        yml_file.close()
        yml_path = Path(yml_file.name)
        
        try:
            assert core.validate_input(yml_path) is True
            company = core.parse_company_description(yml_path)
            assert company.name == "Test Corporation"
        finally:
            yml_path.unlink()
    
    @pytest.mark.unit
    def test_logging_during_operations(self, mock_config, sample_company_file):
        """Test that operations generate appropriate log messages."""
        core = EntraSimCore(mock_config)
        
        with patch('entrasim.core.logger') as mock_logger:
            # Test validation logging
            core.validate_input(sample_company_file)
            
            # Test error logging
            with patch.object(core, 'parse_company_description', side_effect=Exception("Test error")):
                core.validate_input(sample_company_file)
                mock_logger.error.assert_called()