"""Unit tests for Azure client with mocking."""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from kiota_abstractions.api_error import APIError

from entrasim.azure_client import AzureClient, create_azure_client
from entrasim.models import SimulationPlan, CompanyDescription, RoleDefinition


class TestAzureClient:
    """Test the AzureClient class."""
    
    @pytest.mark.unit
    def test_azure_client_initialization(self, mock_config):
        """Test Azure client initialization."""
        client = AzureClient(mock_config)
        assert client.config == mock_config
        assert client._graph_client is None
        assert client._credential is None
    
    @pytest.mark.unit
    def test_authenticate_success(self, mock_config):
        """Test successful authentication."""
        client = AzureClient(mock_config)
        
        mock_credential = Mock()
        mock_graph_client = Mock()
        
        with patch('entrasim.azure_client.ClientSecretCredential', return_value=mock_credential), \
             patch('entrasim.azure_client.GraphServiceClient', return_value=mock_graph_client), \
             patch('entrasim.azure_client.console'):
            
            result = client.authenticate()
            assert result is True
            assert client._credential == mock_credential
            assert client._graph_client == mock_graph_client
    
    @pytest.mark.unit
    def test_authenticate_failure(self, mock_config):
        """Test authentication failure."""
        client = AzureClient(mock_config)
        
        with patch('entrasim.azure_client.ClientSecretCredential', side_effect=Exception("Auth error")), \
             patch('entrasim.azure_client.console'):
            
            result = client.authenticate()
            assert result is False
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_validate_tenant_access_success(self, mock_config):
        """Test successful tenant access validation."""
        client = AzureClient(mock_config)
        client._graph_client = Mock()
        
        # Mock organization response
        org_mock = Mock()
        org_mock.value = [Mock(display_name="Test Organization")]
        client._graph_client.organization.get = AsyncMock(return_value=org_mock)
        
        with patch('entrasim.azure_client.console'):
            result = await client.validate_tenant_access()
            assert result is True
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_validate_tenant_access_no_client(self, mock_config):
        """Test tenant access validation without graph client."""
        client = AzureClient(mock_config)
        # _graph_client is None
        
        with patch('entrasim.azure_client.console'):
            result = await client.validate_tenant_access()
            assert result is False
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_validate_tenant_access_api_error(self, mock_config):
        """Test tenant access validation with API error."""
        client = AzureClient(mock_config)
        client._graph_client = Mock()
        
        api_error = APIError("Unauthorized", Mock())
        api_error.message = "Unauthorized access"
        client._graph_client.organization.get = AsyncMock(side_effect=api_error)
        
        with patch('entrasim.azure_client.console'):
            result = await client.validate_tenant_access()
            assert result is False
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_validate_tenant_access_general_exception(self, mock_config):
        """Test tenant access validation with general exception."""
        client = AzureClient(mock_config)
        client._graph_client = Mock()
        
        client._graph_client.organization.get = AsyncMock(side_effect=Exception("Network error"))
        
        with patch('entrasim.azure_client.console'):
            result = await client.validate_tenant_access()
            assert result is False
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_create_security_group_success(self, mock_config):
        """Test successful security group creation."""
        client = AzureClient(mock_config)
        client._graph_client = Mock()
        
        group_mock = Mock()
        group_mock.id = "group-id-123"
        client._graph_client.groups.post = AsyncMock(return_value=group_mock)
        
        with patch('entrasim.azure_client.console'):
            result = await client.create_security_group("Test Group", "Test Description")
            assert result == "group-id-123"
            
            # Verify group creation was called
            client._graph_client.groups.post.assert_called_once()
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_create_security_group_no_client(self, mock_config):
        """Test security group creation without graph client."""
        client = AzureClient(mock_config)
        # _graph_client is None
        
        with patch('entrasim.azure_client.console'):
            result = await client.create_security_group("Test Group")
            assert result is None
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_create_security_group_api_error(self, mock_config):
        """Test security group creation with API error."""
        client = AzureClient(mock_config)
        client._graph_client = Mock()
        
        api_error = APIError("Conflict", Mock())
        api_error.message = "Group already exists"
        client._graph_client.groups.post = AsyncMock(side_effect=api_error)
        
        with patch('entrasim.azure_client.console'):
            with pytest.raises(APIError):
                await client.create_security_group("Test Group")
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_create_security_group_no_id_returned(self, mock_config):
        """Test security group creation when no ID is returned."""
        client = AzureClient(mock_config)
        client._graph_client = Mock()
        
        group_mock = Mock()
        group_mock.id = None  # No ID returned
        client._graph_client.groups.post = AsyncMock(return_value=group_mock)
        
        with patch('entrasim.azure_client.console'):
            result = await client.create_security_group("Test Group")
            assert result is None
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_create_user_success(self, mock_config):
        """Test successful user creation."""
        client = AzureClient(mock_config)
        client._graph_client = Mock()
        
        user_mock = Mock()
        user_mock.id = "user-id-456"
        client._graph_client.users.post = AsyncMock(return_value=user_mock)
        
        user_data = {
            "display_name": "Test User",
            "user_principal_name": "test@test.com",
            "password": "TempPass123!",
            "job_title": "Developer",
            "department": "Engineering"
        }
        
        with patch('entrasim.azure_client.console'):
            result = await client.create_user(user_data)
            assert result == "user-id-456"
            
            # Verify user creation was called
            client._graph_client.users.post.assert_called_once()
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_create_user_minimal_data(self, mock_config):
        """Test user creation with minimal data."""
        client = AzureClient(mock_config)
        client._graph_client = Mock()
        
        user_mock = Mock()
        user_mock.id = "user-id-456"
        client._graph_client.users.post = AsyncMock(return_value=user_mock)
        
        user_data = {
            "display_name": "Test User",
            "user_principal_name": "test@test.com"
        }
        
        with patch('entrasim.azure_client.console'):
            result = await client.create_user(user_data)
            assert result == "user-id-456"
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_create_user_api_error(self, mock_config):
        """Test user creation with API error."""
        client = AzureClient(mock_config)
        client._graph_client = Mock()
        
        api_error = APIError("Conflict", Mock())
        api_error.message = "User already exists"
        client._graph_client.users.post = AsyncMock(side_effect=api_error)
        
        user_data = {
            "display_name": "Test User",
            "user_principal_name": "test@test.com"
        }
        
        with patch('entrasim.azure_client.console'):
            with pytest.raises(APIError):
                await client.create_user(user_data)
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_add_user_to_group_success(self, mock_config):
        """Test successful user addition to group."""
        client = AzureClient(mock_config)
        client._graph_client = Mock()
        
        # Mock the group membership API
        client._graph_client.groups.by_group_id.return_value.members.ref.post = AsyncMock()
        
        with patch('entrasim.azure_client.console'):
            result = await client.add_user_to_group("user-id", "group-id")
            assert result is True
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_add_user_to_group_already_member(self, mock_config):
        """Test adding user to group when already a member."""
        client = AzureClient(mock_config)
        client._graph_client = Mock()
        
        api_error = APIError("Bad Request", Mock())
        api_error.message = "User is already a member of this group"
        client._graph_client.groups.by_group_id.return_value.members.ref.post = AsyncMock(side_effect=api_error)
        
        with patch('entrasim.azure_client.console'):
            result = await client.add_user_to_group("user-id", "group-id")
            assert result is True  # Should return True for "already a member"
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_add_user_to_group_api_error(self, mock_config):
        """Test adding user to group with API error."""
        client = AzureClient(mock_config)
        client._graph_client = Mock()
        
        api_error = APIError("Forbidden", Mock())
        api_error.message = "Insufficient permissions"
        client._graph_client.groups.by_group_id.return_value.members.ref.post = AsyncMock(side_effect=api_error)
        
        with patch('entrasim.azure_client.console'):
            with pytest.raises(APIError):
                await client.add_user_to_group("user-id", "group-id")


class TestSimulationPlanExecution:
    """Test simulation plan execution."""
    
    @pytest.mark.unit
    def test_execute_simulation_plan_success(self, mock_config, simulation_plan):
        """Test successful simulation plan execution."""
        client = AzureClient(mock_config)
        
        with patch.object(client, '_execute_simulation_plan_async', return_value=True), \
             patch('asyncio.run', return_value=True):
            result = client.execute_simulation_plan(simulation_plan)
            assert result is True
    
    @pytest.mark.unit
    def test_execute_simulation_plan_failure(self, mock_config, simulation_plan):
        """Test simulation plan execution failure."""
        client = AzureClient(mock_config)
        
        with patch('asyncio.run', side_effect=Exception("Execution error")), \
             patch('entrasim.azure_client.console'):
            result = client.execute_simulation_plan(simulation_plan)
            assert result is False
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_execute_simulation_plan_async_success(self, mock_config):
        """Test async simulation plan execution."""
        client = AzureClient(mock_config)
        
        # Create a simple simulation plan
        company = CompanyDescription(
            name="Test Company",
            domain="test.com",
            industry="Technology",
            size="small",
            roles=[
                RoleDefinition(name="Developer", department="IT", count=1)
            ]
        )
        
        plan = SimulationPlan.from_company_description(
            company=company,
            tenant_id=mock_config.azure_tenant_id,
            subscription_id=mock_config.azure_subscription_id
        )
        
        # Mock authentication and client methods
        with patch.object(client, 'authenticate', return_value=True), \
             patch.object(client, 'validate_tenant_access', return_value=True), \
             patch.object(client, 'create_security_group', return_value="group-id"), \
             patch.object(client, 'create_user', return_value="user-id"), \
             patch.object(client, 'add_user_to_group', return_value=True), \
             patch('entrasim.azure_client.console'):
            
            result = await client._execute_simulation_plan_async(plan)
            assert result is True
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_execute_simulation_plan_async_auth_failure(self, mock_config, simulation_plan):
        """Test async simulation plan execution with auth failure."""
        client = AzureClient(mock_config)
        
        with patch.object(client, 'authenticate', return_value=False), \
             patch('entrasim.azure_client.console'):
            
            result = await client._execute_simulation_plan_async(simulation_plan)
            assert result is False
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_execute_simulation_plan_async_tenant_validation_failure(self, mock_config, simulation_plan):
        """Test async simulation plan execution with tenant validation failure."""
        client = AzureClient(mock_config)
        
        with patch.object(client, 'authenticate', return_value=True), \
             patch.object(client, 'validate_tenant_access', return_value=False), \
             patch('entrasim.azure_client.console'):
            
            result = await client._execute_simulation_plan_async(simulation_plan)
            assert result is False
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_execute_simulation_plan_async_group_creation_failure(self, mock_config, simulation_plan):
        """Test async simulation plan execution with group creation failure."""
        client = AzureClient(mock_config)
        
        with patch.object(client, 'authenticate', return_value=True), \
             patch.object(client, 'validate_tenant_access', return_value=True), \
             patch.object(client, 'create_security_group', return_value=None), \
             patch('entrasim.azure_client.console'):
            
            result = await client._execute_simulation_plan_async(simulation_plan)
            assert result is False
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_execute_simulation_plan_async_user_creation_failure(self, mock_config, simulation_plan):
        """Test async simulation plan execution with user creation failure."""
        client = AzureClient(mock_config)
        
        with patch.object(client, 'authenticate', return_value=True), \
             patch.object(client, 'validate_tenant_access', return_value=True), \
             patch.object(client, 'create_security_group', return_value="group-id"), \
             patch.object(client, 'create_user', return_value=None), \
             patch('entrasim.azure_client.console'):
            
            result = await client._execute_simulation_plan_async(simulation_plan)
            assert result is False


class TestCleanupResources:
    """Test resource cleanup functionality."""
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_cleanup_resources_success(self, mock_config, simulation_plan):
        """Test successful resource cleanup."""
        client = AzureClient(mock_config)
        client._graph_client = Mock()
        
        # Mock user and group search responses
        users_response = Mock()
        users_response.value = [Mock(id="user-id-1")]
        
        groups_response = Mock()
        groups_response.value = [Mock(id="group-id-1")]
        
        client._graph_client.users.get = AsyncMock(return_value=users_response)
        client._graph_client.groups.get = AsyncMock(return_value=groups_response)
        
        # Mock delete operations
        client._graph_client.users.by_user_id.return_value.delete = AsyncMock()
        client._graph_client.groups.by_group_id.return_value.delete = AsyncMock()
        
        with patch('entrasim.azure_client.console'):
            result = await client.cleanup_resources(simulation_plan)
            assert result is True
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_cleanup_resources_no_client(self, mock_config, simulation_plan):
        """Test resource cleanup without graph client."""
        client = AzureClient(mock_config)
        # _graph_client is None
        
        with patch('entrasim.azure_client.console'):
            result = await client.cleanup_resources(simulation_plan)
            assert result is False
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_cleanup_resources_with_errors(self, mock_config, simulation_plan):
        """Test resource cleanup with some errors (should continue)."""
        client = AzureClient(mock_config)
        client._graph_client = Mock()
        
        # Mock user search to fail for one user
        users_response = Mock()
        users_response.value = []  # No users found
        
        groups_response = Mock()
        groups_response.value = [Mock(id="group-id-1")]
        
        client._graph_client.users.get = AsyncMock(return_value=users_response)
        client._graph_client.groups.get = AsyncMock(return_value=groups_response)
        
        # Mock group deletion
        client._graph_client.groups.by_group_id.return_value.delete = AsyncMock()
        
        with patch('entrasim.azure_client.console'):
            result = await client.cleanup_resources(simulation_plan)
            assert result is True  # Should succeed despite user cleanup "failures"
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_cleanup_resources_exception(self, mock_config, simulation_plan):
        """Test resource cleanup with exception."""
        client = AzureClient(mock_config)
        client._graph_client = Mock()
        
        client._graph_client.users.get = AsyncMock(side_effect=Exception("Cleanup error"))
        
        with patch('entrasim.azure_client.console'):
            result = await client.cleanup_resources(simulation_plan)
            assert result is False


class TestAzureClientFactory:
    """Test Azure client factory function."""
    
    @pytest.mark.unit
    def test_create_azure_client(self, mock_config):
        """Test Azure client factory function."""
        client = create_azure_client(mock_config)
        assert isinstance(client, AzureClient)
        assert client.config == mock_config


class TestAzureClientEdgeCases:
    """Test edge cases and error conditions."""
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_create_security_group_with_special_characters(self, mock_config):
        """Test security group creation with special characters in name."""
        client = AzureClient(mock_config)
        client._graph_client = Mock()
        
        group_mock = Mock()
        group_mock.id = "group-id-123"
        client._graph_client.groups.post = AsyncMock(return_value=group_mock)
        
        with patch('entrasim.azure_client.console'):
            result = await client.create_security_group("Test Group (Special-Chars)")
            assert result == "group-id-123"
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_create_user_password_generation(self, mock_config):
        """Test user creation with password generation."""
        client = AzureClient(mock_config)
        client._graph_client = Mock()
        
        user_mock = Mock()
        user_mock.id = "user-id-456"
        client._graph_client.users.post = AsyncMock(return_value=user_mock)
        
        user_data = {
            "display_name": "Test User",
            "user_principal_name": "test@test.com"
            # No password provided - should be generated
        }
        
        with patch('entrasim.azure_client.console'):
            result = await client.create_user(user_data)
            assert result == "user-id-456"
            
            # Check that password was added
            call_args = client._graph_client.users.post.call_args[0][0]
            assert call_args.password_profile.password == "TempPass123!"
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_validate_tenant_access_empty_org_response(self, mock_config):
        """Test tenant access validation with empty organization response."""
        client = AzureClient(mock_config)
        client._graph_client = Mock()
        
        # Mock empty organization response
        org_mock = Mock()
        org_mock.value = []  # Empty list
        client._graph_client.organization.get = AsyncMock(return_value=org_mock)
        
        with patch('entrasim.azure_client.console'):
            result = await client.validate_tenant_access()
            assert result is False
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_add_user_to_group_general_exception(self, mock_config):
        """Test adding user to group with general exception."""
        client = AzureClient(mock_config)
        client._graph_client = Mock()
        
        client._graph_client.groups.by_group_id.return_value.members.ref.post = AsyncMock(
            side_effect=Exception("Network error")
        )
        
        with patch('entrasim.azure_client.console'):
            result = await client.add_user_to_group("user-id", "group-id")
            assert result is False