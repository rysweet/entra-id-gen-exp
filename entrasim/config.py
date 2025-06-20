"""Configuration management for EntraSim."""

import os
from typing import Optional
from dotenv import load_dotenv
from pydantic import BaseModel, Field, validator


class Config(BaseModel):
    """Configuration class for managing environment variables and settings."""
    
    # Azure credentials
    azure_tenant_id: str = Field(description="Azure Tenant ID")
    azure_client_id: str = Field(description="Azure Client ID")
    azure_client_secret: str = Field(description="Azure Client Secret")
    azure_subscription_id: str = Field(description="Azure Subscription ID")
    
    # Optional settings
    log_level: str = Field(default="INFO", description="Logging level")
    dry_run: bool = Field(default=False, description="Perform dry run without actual changes")
    
    @validator('azure_tenant_id', 'azure_client_id', 'azure_subscription_id')
    def validate_guid_format(cls, v):
        """Validate that Azure IDs are in GUID format."""
        if not v or len(v) != 36:
            raise ValueError("Azure IDs must be valid GUIDs (36 characters)")
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
            load_dotenv(env_file)
        elif os.path.exists('.env'):
            load_dotenv('.env')
        
        # Load from environment variables
        config_data = {
            'azure_tenant_id': os.getenv('AZURE_TENANT_ID', ''),
            'azure_client_id': os.getenv('AZURE_CLIENT_ID', ''),
            'azure_client_secret': os.getenv('AZURE_CLIENT_SECRET', ''),
            'azure_subscription_id': os.getenv('AZURE_SUBSCRIPTION_ID', ''),
            'log_level': os.getenv('LOG_LEVEL', 'INFO'),
            'dry_run': os.getenv('DRY_RUN', 'false').lower() in ('true', '1', 'yes', 'on')
        }
        
        return cls(**config_data)
    
    def validate_required_credentials(self) -> None:
        """Validate that all required Azure credentials are present."""
        missing_creds = []
        
        if not self.azure_tenant_id:
            missing_creds.append('AZURE_TENANT_ID')
        if not self.azure_client_id:
            missing_creds.append('AZURE_CLIENT_ID')
        if not self.azure_client_secret:
            missing_creds.append('AZURE_CLIENT_SECRET')
        if not self.azure_subscription_id:
            missing_creds.append('AZURE_SUBSCRIPTION_ID')
        
        if missing_creds:
            raise ValueError(
                f"Missing required Azure credentials: {', '.join(missing_creds)}. "
                "Please set these environment variables or add them to your .env file."
            )


def get_config(env_file: Optional[str] = None) -> Config:
    """Get configuration instance with validation."""
    config = Config.load_from_env(env_file)
    config.validate_required_credentials()
    return config