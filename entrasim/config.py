"""Configuration management for EntraSim."""

import os
import logging
from typing import Optional
from dotenv import load_dotenv
from pydantic import BaseModel, Field, validator

logger = logging.getLogger(__name__)


class Config(BaseModel):
    """Configuration class for managing environment variables and settings."""
    
    # Azure credentials
    azure_tenant_id: str = Field(description="Azure Tenant ID")
    azure_client_id: str = Field(description="Azure Client ID")
    azure_client_secret: str = Field(description="Azure Client Secret")
    azure_subscription_id: str = Field(description="Azure Subscription ID")
    
    # Optional settings
    log_level: str = Field(default="INFO", description="Logging level")
    
    @validator('azure_tenant_id', 'azure_client_id', 'azure_subscription_id')
    def validate_guid_format(cls, v):
        """Validate that Azure IDs are in GUID format."""
        if not v or len(v) != 36:
            raise ValueError("Azure IDs must be valid GUIDs (36 characters)")
        
        # Basic GUID format validation (8-4-4-4-12 pattern)
        import re
        guid_pattern = r'^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$'
        if not re.match(guid_pattern, v):
            raise ValueError("Azure IDs must be valid GUIDs in format: xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx")
        
        return v
    
    @validator('azure_client_secret')
    def validate_client_secret(cls, v):
        """Validate that client secret is not empty and has reasonable length."""
        if not v:
            raise ValueError("Azure client secret cannot be empty")
        
        if len(v) < 10:
            raise ValueError("Azure client secret appears to be too short (minimum 10 characters)")
        
        return v
    
    @validator('log_level')
    def validate_log_level(cls, v):
        """Validate log level."""
        valid_levels = {'DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'}
        if v.upper() not in valid_levels:
            raise ValueError(f"Log level must be one of: {', '.join(valid_levels)}")
        return v.upper()
    
    @classmethod
    def load_from_env(cls, env_file: Optional[str] = None) -> "Config":
        """Load configuration from environment variables and .env file."""
        # Load .env file if specified or if .env exists
        if env_file:
            if not os.path.exists(env_file):
                raise ValueError(f"Specified environment file not found: {env_file}")
            load_dotenv(env_file)
            logger.info(f"Loaded configuration from: {env_file}")
        elif os.path.exists('.env'):
            load_dotenv('.env')
            logger.info("Loaded configuration from: .env")
        
        # Load from environment variables
        config_data = {
            'azure_tenant_id': os.getenv('AZURE_TENANT_ID', '').strip(),
            'azure_client_id': os.getenv('AZURE_CLIENT_ID', '').strip(),
            'azure_client_secret': os.getenv('AZURE_CLIENT_SECRET', '').strip(),
            'azure_subscription_id': os.getenv('AZURE_SUBSCRIPTION_ID', '').strip(),
            'log_level': os.getenv('LOG_LEVEL', 'INFO').strip(),
        }
        
        return cls(**config_data)
    
    def validate_required_credentials(self) -> None:
        """Validate that all required Azure credentials are present and properly formatted."""
        missing_creds = []
        invalid_creds = []
        
        # Check for missing credentials
        if not self.azure_tenant_id:
            missing_creds.append('AZURE_TENANT_ID')
        if not self.azure_client_id:
            missing_creds.append('AZURE_CLIENT_ID')
        if not self.azure_client_secret:
            missing_creds.append('AZURE_CLIENT_SECRET')
        if not self.azure_subscription_id:
            missing_creds.append('AZURE_SUBSCRIPTION_ID')
        
        if missing_creds:
            error_msg = f"Missing required Azure credentials: {', '.join(missing_creds)}"
            suggestions = self._get_credential_setup_suggestions()
            raise ValueError(f"{error_msg}\n\n{suggestions}")
        
        # Additional validation for credential format
        try:
            # Re-validate GUIDs to ensure they're properly formatted
            self.validate_guid_format(self.azure_tenant_id)
            self.validate_guid_format(self.azure_client_id)
            self.validate_guid_format(self.azure_subscription_id)
            self.validate_client_secret(self.azure_client_secret)
            
        except ValueError as e:
            invalid_creds.append(str(e))
        
        if invalid_creds:
            error_msg = "Invalid credential format:\n" + "\n".join(f"- {cred}" for cred in invalid_creds)
            suggestions = self._get_credential_setup_suggestions()
            raise ValueError(f"{error_msg}\n\n{suggestions}")
        
        logger.info("Azure credentials validation successful")
    
    def _get_credential_setup_suggestions(self) -> str:
        """Get helpful suggestions for setting up Azure credentials."""
        return """
How to set up Azure credentials:

1. Create a Service Principal in Azure:
   az ad sp create-for-rbac --name "EntraSim" --role "User Administrator" --scopes /subscriptions/{subscription-id}

2. Set environment variables or create a .env file:
   AZURE_TENANT_ID=your-tenant-id
   AZURE_CLIENT_ID=your-client-id
   AZURE_CLIENT_SECRET=your-client-secret
   AZURE_SUBSCRIPTION_ID=your-subscription-id

3. Required Azure permissions:
   - User Administrator role (to create/manage users and groups)
   - Application Administrator role (if creating app registrations)

4. You can find these values in:
   - Azure Portal > Azure Active Directory > App registrations > Your app
   - Tenant ID: Azure Portal > Azure Active Directory > Properties
   - Subscription ID: Azure Portal > Subscriptions

For more information, visit: https://docs.microsoft.com/en-us/azure/active-directory/develop/howto-create-service-principal-portal
        """.strip()
    
    async def test_tenant_connectivity(self) -> tuple[bool, str]:
        """Test connectivity to the Azure tenant."""
        try:
            from azure.identity import ClientSecretCredential
            from msgraph import GraphServiceClient
            
            # Create credential
            credential = ClientSecretCredential(
                tenant_id=self.azure_tenant_id,
                client_id=self.azure_client_id,
                client_secret=self.azure_client_secret
            )
            
            # Create Graph client
            graph_client = GraphServiceClient(
                credentials=credential,
                scopes=["https://graph.microsoft.com/.default"]
            )
            
            # Test with a simple query
            org_request = graph_client.organization
            org_response = await org_request.get()
            
            if org_response and org_response.value:
                org_name = org_response.value[0].display_name or "Unknown Organization"
                return True, f"Successfully connected to: {org_name}"
            else:
                return False, "Unable to retrieve organization information"
                
        except Exception as e:
            error_msg = f"Connectivity test failed: {str(e)}"
            
            # Provide more specific error messages for common issues
            if "unauthorized" in str(e).lower():
                error_msg += "\n\nThis usually means:\n- Invalid client credentials\n- Insufficient permissions\n- Client secret has expired"
            elif "not found" in str(e).lower():
                error_msg += "\n\nThis usually means:\n- Invalid tenant ID\n- Invalid client ID\n- Application not found in tenant"
            elif "forbidden" in str(e).lower():
                error_msg += "\n\nThis usually means:\n- Application lacks required permissions\n- Need User Administrator role\n- Permissions not granted by admin"
            
            return False, error_msg


def get_config(env_file: Optional[str] = None) -> Config:
    """Get configuration instance with validation."""
    try:
        config = Config.load_from_env(env_file)
        config.validate_required_credentials()
        return config
    except Exception as e:
        logger.error(f"Configuration error: {e}")
        raise


def validate_azure_environment() -> tuple[bool, str, Optional[Config]]:
    """Validate Azure environment and return status, message, and config if successful."""
    try:
        config = get_config()
        return True, "Azure environment validation successful", config
    except Exception as e:
        return False, str(e), None