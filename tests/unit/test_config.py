"""Unit tests for configuration management."""

import pytest
import os
import tempfile
from pathlib import Path
from unittest.mock import patch, Mock

from entrasim.config import Config, get_config, validate_azure_environment
from tests.utils import create_test_env_file


class TestConfig:
    """Test the Config class."""
    
    @pytest.mark.unit
    def test_valid_config_creation(self):
        """Test creating a config with valid data."""
        config = Config(
            azure_tenant_id="12345678-1234-1234-1234-123456789abc",
            azure_client_id="87654321-4321-4321-4321-cba987654321",
            azure_client_secret="test-client-secret-12345",
            azure_subscription_id="11111111-2222-3333-4444-555555555555",
            log_level="INFO"
        )
        
        assert config.azure_tenant_id == "12345678-1234-1234-1234-123456789abc"
        assert config.azure_client_id == "87654321-4321-4321-4321-cba987654321"
        assert config.azure_client_secret == "test-client-secret-12345"
        assert config.azure_subscription_id == "11111111-2222-3333-4444-555555555555"
        assert config.log_level == "INFO"
    
    @pytest.mark.unit
    def test_invalid_guid_format(self):
        """Test that invalid GUID formats are rejected."""
        with pytest.raises(ValueError, match="valid GUIDs"):
            Config(
                azure_tenant_id="invalid-guid",
                azure_client_id="87654321-4321-4321-4321-cba987654321",
                azure_client_secret="test-secret",
                azure_subscription_id="11111111-2222-3333-4444-555555555555"
            )
    
    @pytest.mark.unit
    def test_short_guid_rejected(self):
        """Test that short GUIDs are rejected."""
        with pytest.raises(ValueError, match="36 characters"):
            Config(
                azure_tenant_id="12345678-1234-1234-1234-12345678",  # Too short
                azure_client_id="87654321-4321-4321-4321-cba987654321",
                azure_client_secret="test-secret",
                azure_subscription_id="11111111-2222-3333-4444-555555555555"
            )
    
    @pytest.mark.unit
    def test_empty_client_secret_rejected(self):
        """Test that empty client secret is rejected."""
        with pytest.raises(ValueError, match="cannot be empty"):
            Config(
                azure_tenant_id="12345678-1234-1234-1234-123456789abc",
                azure_client_id="87654321-4321-4321-4321-cba987654321",
                azure_client_secret="",
                azure_subscription_id="11111111-2222-3333-4444-555555555555"
            )
    
    @pytest.mark.unit
    def test_short_client_secret_rejected(self):
        """Test that very short client secrets are rejected."""
        with pytest.raises(ValueError, match="too short"):
            Config(
                azure_tenant_id="12345678-1234-1234-1234-123456789abc",
                azure_client_id="87654321-4321-4321-4321-cba987654321",
                azure_client_secret="short",
                azure_subscription_id="11111111-2222-3333-4444-555555555555"
            )
    
    @pytest.mark.unit
    def test_invalid_log_level_rejected(self):
        """Test that invalid log levels are rejected."""
        with pytest.raises(ValueError, match="Log level must be one of"):
            Config(
                azure_tenant_id="12345678-1234-1234-1234-123456789abc",
                azure_client_id="87654321-4321-4321-4321-cba987654321",
                azure_client_secret="test-client-secret-12345",
                azure_subscription_id="11111111-2222-3333-4444-555555555555",
                log_level="INVALID"
            )
    
    @pytest.mark.unit
    def test_log_level_case_insensitive(self):
        """Test that log levels are case insensitive."""
        config = Config(
            azure_tenant_id="12345678-1234-1234-1234-123456789abc",
            azure_client_id="87654321-4321-4321-4321-cba987654321",
            azure_client_secret="test-client-secret-12345",
            azure_subscription_id="11111111-2222-3333-4444-555555555555",
            log_level="debug"
        )
        assert config.log_level == "DEBUG"


class TestConfigLoading:
    """Test configuration loading from environment."""
    
    @pytest.mark.unit
    def test_load_from_env_variables(self, mock_env_vars):
        """Test loading config from environment variables."""
        config = Config.load_from_env()
        
        assert config.azure_tenant_id == mock_env_vars['AZURE_TENANT_ID']
        assert config.azure_client_id == mock_env_vars['AZURE_CLIENT_ID']
        assert config.azure_client_secret == mock_env_vars['AZURE_CLIENT_SECRET']
        assert config.azure_subscription_id == mock_env_vars['AZURE_SUBSCRIPTION_ID']
        assert config.log_level == mock_env_vars['LOG_LEVEL']
    
    @pytest.mark.unit
    def test_load_from_env_file(self, temp_dir):
        """Test loading config from .env file."""
        env_file = create_test_env_file(temp_dir)
        
        # Clear environment variables to ensure we're loading from file
        with patch.dict(os.environ, {}, clear=True):
            config = Config.load_from_env(str(env_file))
        
        assert config.azure_tenant_id == "12345678-1234-1234-1234-123456789abc"
        assert config.azure_client_id == "87654321-4321-4321-4321-cba987654321"
        assert config.azure_client_secret == "test-client-secret-12345"
        assert config.azure_subscription_id == "11111111-2222-3333-4444-555555555555"
        assert config.log_level == "INFO"
    
    @pytest.mark.unit
    def test_load_from_nonexistent_env_file(self):
        """Test loading config from nonexistent .env file raises error."""
        with pytest.raises(ValueError, match="not found"):
            Config.load_from_env("/path/to/nonexistent/.env")
    
    @pytest.mark.unit
    def test_load_with_missing_variables(self):
        """Test loading config with missing environment variables."""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ValueError, match="Missing required Azure credentials"):
                config = Config.load_from_env()
                config.validate_required_credentials()


class TestCredentialValidation:
    """Test credential validation methods."""
    
    @pytest.mark.unit
    def test_validate_required_credentials_success(self, mock_config):
        """Test successful credential validation."""
        # Should not raise any exception
        mock_config.validate_required_credentials()
    
    @pytest.mark.unit
    def test_validate_missing_tenant_id(self):
        """Test validation fails with missing tenant ID."""
        config = Config(
            azure_tenant_id="",
            azure_client_id="87654321-4321-4321-4321-cba987654321",
            azure_client_secret="test-client-secret-12345",
            azure_subscription_id="11111111-2222-3333-4444-555555555555"
        )
        
        with pytest.raises(ValueError, match="AZURE_TENANT_ID"):
            config.validate_required_credentials()
    
    @pytest.mark.unit
    def test_validate_missing_multiple_credentials(self):
        """Test validation fails with multiple missing credentials."""
        config = Config(
            azure_tenant_id="",
            azure_client_id="",
            azure_client_secret="test-client-secret-12345",
            azure_subscription_id="11111111-2222-3333-4444-555555555555"
        )
        
        with pytest.raises(ValueError, match="AZURE_TENANT_ID.*AZURE_CLIENT_ID"):
            config.validate_required_credentials()
    
    @pytest.mark.unit
    def test_credential_setup_suggestions_included(self):
        """Test that credential setup suggestions are included in error messages."""
        config = Config(
            azure_tenant_id="",
            azure_client_id="87654321-4321-4321-4321-cba987654321",
            azure_client_secret="test-client-secret-12345",
            azure_subscription_id="11111111-2222-3333-4444-555555555555"
        )
        
        with pytest.raises(ValueError, match="How to set up Azure credentials"):
            config.validate_required_credentials()


class TestTenantConnectivity:
    """Test tenant connectivity methods."""
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_test_tenant_connectivity_success(self, mock_config):
        """Test successful tenant connectivity."""
        mock_credential = Mock()
        mock_graph_client = Mock()
        
        # Mock organization response
        org_mock = Mock()
        org_mock.value = [Mock(display_name="Test Organization")]
        mock_graph_client.organization.get = Mock(return_value=org_mock)
        
        with patch('entrasim.config.ClientSecretCredential', return_value=mock_credential), \
             patch('entrasim.config.GraphServiceClient', return_value=mock_graph_client):
            
            success, message = await mock_config.test_tenant_connectivity()
            
            assert success is True
            assert "Test Organization" in message
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_test_tenant_connectivity_failure(self, mock_config):
        """Test failed tenant connectivity."""
        mock_credential = Mock()
        mock_graph_client = Mock()
        mock_graph_client.organization.get = Mock(side_effect=Exception("Connection failed"))
        
        with patch('entrasim.config.ClientSecretCredential', return_value=mock_credential), \
             patch('entrasim.config.GraphServiceClient', return_value=mock_graph_client):
            
            success, message = await mock_config.test_tenant_connectivity()
            
            assert success is False
            assert "Connection failed" in message
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_test_tenant_connectivity_unauthorized(self, mock_config):
        """Test tenant connectivity with unauthorized error."""
        mock_credential = Mock()
        mock_graph_client = Mock()
        mock_graph_client.organization.get = Mock(side_effect=Exception("unauthorized"))
        
        with patch('entrasim.config.ClientSecretCredential', return_value=mock_credential), \
             patch('entrasim.config.GraphServiceClient', return_value=mock_graph_client):
            
            success, message = await mock_config.test_tenant_connectivity()
            
            assert success is False
            assert "Invalid client credentials" in message


class TestConfigHelperFunctions:
    """Test configuration helper functions."""
    
    @pytest.mark.unit
    def test_get_config_success(self, mock_env_vars):
        """Test successful config retrieval."""
        config = get_config()
        assert isinstance(config, Config)
        assert config.azure_tenant_id == mock_env_vars['AZURE_TENANT_ID']
    
    @pytest.mark.unit
    def test_get_config_with_env_file(self, temp_dir):
        """Test config retrieval with custom env file."""
        env_file = create_test_env_file(temp_dir)
        
        with patch.dict(os.environ, {}, clear=True):
            config = get_config(str(env_file))
            assert isinstance(config, Config)
            assert config.azure_tenant_id == "12345678-1234-1234-1234-123456789abc"
    
    @pytest.mark.unit
    def test_get_config_failure(self):
        """Test config retrieval failure."""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ValueError):
                get_config()
    
    @pytest.mark.unit
    def test_validate_azure_environment_success(self, mock_env_vars):
        """Test successful Azure environment validation."""
        success, message, config = validate_azure_environment()
        
        assert success is True
        assert "successful" in message
        assert isinstance(config, Config)
    
    @pytest.mark.unit
    def test_validate_azure_environment_failure(self):
        """Test failed Azure environment validation."""
        with patch.dict(os.environ, {}, clear=True):
            success, message, config = validate_azure_environment()
            
            assert success is False
            assert "Missing required" in message
            assert config is None


class TestConfigEdgeCases:
    """Test edge cases and special scenarios."""
    
    @pytest.mark.unit
    def test_config_with_whitespace_in_values(self, temp_dir):
        """Test config handles whitespace in environment values."""
        env_file = create_test_env_file(
            temp_dir,
            AZURE_TENANT_ID="  12345678-1234-1234-1234-123456789abc  ",
            AZURE_CLIENT_SECRET="  test-client-secret-12345  "
        )
        
        with patch.dict(os.environ, {}, clear=True):
            config = Config.load_from_env(str(env_file))
            
            # Values should be stripped
            assert config.azure_tenant_id == "12345678-1234-1234-1234-123456789abc"
            assert config.azure_client_secret == "test-client-secret-12345"
    
    @pytest.mark.unit
    def test_config_default_log_level(self):
        """Test config uses default log level when not specified."""
        config = Config(
            azure_tenant_id="12345678-1234-1234-1234-123456789abc",
            azure_client_id="87654321-4321-4321-4321-cba987654321",
            azure_client_secret="test-client-secret-12345",
            azure_subscription_id="11111111-2222-3333-4444-555555555555"
        )
        assert config.log_level == "INFO"
    
    @pytest.mark.unit
    def test_guid_validation_with_uppercase(self):
        """Test GUID validation accepts uppercase letters."""
        config = Config(
            azure_tenant_id="12345678-1234-1234-1234-123456789ABC",
            azure_client_id="87654321-4321-4321-4321-CBA987654321",
            azure_client_secret="test-client-secret-12345",
            azure_subscription_id="11111111-2222-3333-4444-555555555555"
        )
        # Should not raise any exception
        config.validate_required_credentials()
    
    @pytest.mark.unit
    def test_guid_validation_mixed_case(self):
        """Test GUID validation accepts mixed case."""
        config = Config(
            azure_tenant_id="12345678-1234-1234-1234-123456789aBc",
            azure_client_id="87654321-4321-4321-4321-CbA987654321",
            azure_client_secret="test-client-secret-12345",
            azure_subscription_id="11111111-2222-3333-4444-555555555555"
        )
        # Should not raise any exception
        config.validate_required_credentials()