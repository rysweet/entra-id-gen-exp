"""Azure integration using Microsoft Graph SDK."""

import asyncio
import logging
from typing import List, Dict, Any, Optional
from rich.console import Console
from azure.identity import ClientSecretCredential
from msgraph import GraphServiceClient
from msgraph.generated.models.user import User
from msgraph.generated.models.group import Group
from msgraph.generated.models.password_profile import PasswordProfile
from msgraph.generated.models.reference_create import ReferenceCreate
from kiota_abstractions.api_error import APIError
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from .config import Config
from .models import SimulationPlan

console = Console()
logger = logging.getLogger(__name__)


class AzureClient:
    """Class encapsulating Microsoft Graph SDK interactions."""
    
    def __init__(self, config: Config):
        """Initialize Azure client with configuration."""
        self.config = config
        self._graph_client: Optional[GraphServiceClient] = None
        self._credential: Optional[ClientSecretCredential] = None
    
    def authenticate(self) -> bool:
        """Authenticate with Azure and initialize Graph client."""
        try:
            console.print("[blue]Authenticating with Azure...[/blue]")
            
            # Create credential using ClientSecretCredential
            self._credential = ClientSecretCredential(
                tenant_id=self.config.azure_tenant_id,
                client_id=self.config.azure_client_id,
                client_secret=self.config.azure_client_secret
            )
            
            # Initialize Graph service client
            self._graph_client = GraphServiceClient(
                credentials=self._credential,
                scopes=["https://graph.microsoft.com/.default"]
            )
            
            console.print(f"[green]✓ Authenticated with tenant: {self.config.azure_tenant_id}[/green]")
            return True
            
        except Exception as e:
            console.print(f"[red]Authentication failed: {e}[/red]")
            logger.error(f"Authentication failed: {e}")
            return False
    
    async def validate_tenant_access(self) -> bool:
        """Validate access to the specified Azure tenant."""
        try:
            console.print("[blue]Validating tenant access...[/blue]")
            
            if not self._graph_client:
                console.print("[red]Graph client not initialized. Please authenticate first.[/red]")
                return False
            
            # Test access by trying to get the organization info
            org_request = self._graph_client.organization
            org_response = await org_request.get()
            
            if org_response and org_response.value:
                org_name = org_response.value[0].display_name or "Unknown"
                console.print(f"[green]✓ Tenant access validated for: {org_name}[/green]")
                return True
            else:
                console.print("[red]Unable to retrieve organization information[/red]")
                return False
            
        except APIError as e:
            console.print(f"[red]Tenant validation failed: {e.message}[/red]")
            logger.error(f"Tenant validation failed: {e}")
            return False
        except Exception as e:
            console.print(f"[red]Tenant validation failed: {e}[/red]")
            logger.error(f"Tenant validation failed: {e}")
            return False
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type(APIError)
    )
    async def create_security_group(self, group_name: str, description: str = "") -> Optional[str]:
        """Create a security group in Azure AD."""
        try:
            if not self._graph_client:
                console.print("[red]Graph client not initialized. Please authenticate first.[/red]")
                return None
            
            # Create group object
            group = Group()
            group.display_name = group_name
            group.description = description or f"Security group for {group_name}"
            group.mail_nickname = group_name.replace(" ", "").replace("-", "").lower()
            group.security_enabled = True
            group.mail_enabled = False
            group.group_types = []
            
            # Create the group
            created_group = await self._graph_client.groups.post(group)
            
            if created_group and created_group.id:
                console.print(f"[green]✓ Created security group: {group_name} (ID: {created_group.id})[/green]")
                logger.info(f"Created security group: {group_name} with ID: {created_group.id}")
                return created_group.id
            else:
                console.print(f"[red]Failed to create group '{group_name}': No ID returned[/red]")
                return None
            
        except APIError as e:
            console.print(f"[red]Failed to create group '{group_name}': {e.message}[/red]")
            logger.error(f"Failed to create group '{group_name}': {e}")
            raise
        except Exception as e:
            console.print(f"[red]Failed to create group '{group_name}': {e}[/red]")
            logger.error(f"Failed to create group '{group_name}': {e}")
            return None
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type(APIError)
    )
    async def create_user(self, user_data: Dict[str, Any]) -> Optional[str]:
        """Create a user in Azure AD."""
        try:
            if not self._graph_client:
                console.print("[red]Graph client not initialized. Please authenticate first.[/red]")
                return None
            
            display_name = user_data.get('display_name', '')
            upn = user_data.get('user_principal_name', '')
            password = user_data.get('password', 'TempPass123!')
            
            # Create password profile
            password_profile = PasswordProfile()
            password_profile.password = password
            password_profile.force_change_password_next_sign_in = True
            
            # Create user object
            user = User()
            user.display_name = display_name
            user.user_principal_name = upn
            user.mail_nickname = display_name.replace(" ", "").lower()
            user.password_profile = password_profile
            user.account_enabled = True
            user.usage_location = "US"  # Required for license assignment
            
            # Add additional properties if provided
            if user_data.get('job_title'):
                user.job_title = user_data['job_title']
            if user_data.get('department'):
                user.department = user_data['department']
            
            # Create the user
            created_user = await self._graph_client.users.post(user)
            
            if created_user and created_user.id:
                console.print(f"[green]✓ Created user: {display_name} ({upn}) - ID: {created_user.id}[/green]")
                logger.info(f"Created user: {display_name} with ID: {created_user.id}")
                return created_user.id
            else:
                console.print(f"[red]Failed to create user '{display_name}': No ID returned[/red]")
                return None
            
        except APIError as e:
            console.print(f"[red]Failed to create user '{user_data.get('display_name')}': {e.message}[/red]")
            logger.error(f"Failed to create user '{user_data.get('display_name')}': {e}")
            raise
        except Exception as e:
            console.print(f"[red]Failed to create user '{user_data.get('display_name')}': {e}[/red]")
            logger.error(f"Failed to create user '{user_data.get('display_name')}': {e}")
            return None
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type(APIError)
    )
    async def add_user_to_group(self, user_id: str, group_id: str) -> bool:
        """Add a user to a security group."""
        try:
            if not self._graph_client:
                console.print("[red]Graph client not initialized. Please authenticate first.[/red]")
                return False
            
            # Create reference to add user to group
            reference = ReferenceCreate()
            reference.odata_id = f"https://graph.microsoft.com/v1.0/users/{user_id}"
            
            # Add user to group
            await self._graph_client.groups.by_group_id(group_id).members.ref.post(reference)
            
            console.print(f"[green]✓ Added user {user_id} to group {group_id}[/green]")
            logger.info(f"Added user {user_id} to group {group_id}")
            return True
            
        except APIError as e:
            # Check if user is already a member (error code: Request_BadRequest with "already a member" message)
            if "already a member" in str(e.message).lower():
                console.print(f"[yellow]User {user_id} is already a member of group {group_id}[/yellow]")
                return True
            else:
                console.print(f"[red]Failed to add user to group: {e.message}[/red]")
                logger.error(f"Failed to add user {user_id} to group {group_id}: {e}")
                raise
        except Exception as e:
            console.print(f"[red]Failed to add user to group: {e}[/red]")
            logger.error(f"Failed to add user {user_id} to group {group_id}: {e}")
            return False
    
    def execute_simulation_plan(self, plan: SimulationPlan) -> bool:
        """Execute the complete simulation plan."""
        try:
            console.print(f"[blue]Executing simulation for {plan.company.name}...[/blue]")
            
            # Run the async execution
            return asyncio.run(self._execute_simulation_plan_async(plan))
            
        except Exception as e:
            console.print(f"[red]Error executing simulation plan: {e}[/red]")
            logger.error(f"Error executing simulation plan: {e}")
            return False
    
    async def _execute_simulation_plan_async(self, plan: SimulationPlan) -> bool:
        """Async implementation of simulation plan execution."""
        try:
            # Authenticate first
            if not self.authenticate():
                return False
            
            if not await self.validate_tenant_access():
                return False
            
            # Create groups first
            console.print(f"[blue]Creating {plan.total_groups} security groups...[/blue]")
            group_ids = {}
            
            for group_name in plan.groups_to_create:
                group_id = await self.create_security_group(
                    group_name=group_name,
                    description=f"Security group for {group_name} in {plan.company.name}"
                )
                if group_id:
                    group_ids[group_name] = group_id
                else:
                    console.print(f"[red]Failed to create group: {group_name}[/red]")
                    return False
            
            # Create users
            console.print(f"[blue]Creating {plan.total_users} users...[/blue]")
            user_ids = {}
            
            for user_data in plan.users_to_create:
                # Generate a secure temporary password
                import secrets
                import string
                alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
                password = ''.join(secrets.choice(alphabet) for _ in range(12))
                user_data['password'] = f"TempPass{password}!"
                
                # Add job title based on role
                user_data['job_title'] = user_data.get('role', 'Employee')
                
                user_id = await self.create_user(user_data)
                if user_id:
                    user_ids[user_data['display_name']] = user_id
                    
                    # Add user to groups
                    for group_name in user_data.get('groups', []):
                        if group_name in group_ids:
                            success = await self.add_user_to_group(user_id, group_ids[group_name])
                            if not success:
                                console.print(f"[yellow]Warning: Failed to add user {user_data['display_name']} to group {group_name}[/yellow]")
                else:
                    console.print(f"[red]Failed to create user: {user_data['display_name']}[/red]")
                    return False
            
            console.print(f"[green]✓ Successfully executed simulation plan[/green]")
            console.print(f"  Created {len(group_ids)} groups")
            console.print(f"  Created {len(user_ids)} users")
            
            return True
            
        except Exception as e:
            console.print(f"[red]Error executing simulation plan: {e}[/red]")
            logger.error(f"Error executing simulation plan: {e}")
            return False
    
    async def cleanup_resources(self, plan: SimulationPlan) -> bool:
        """Clean up created resources (for testing/development)."""
        try:
            console.print("[yellow]Cleaning up created resources...[/yellow]")
            
            if not self._graph_client:
                console.print("[red]Graph client not initialized. Please authenticate first.[/red]")
                return False
            
            # Delete users first (to avoid dependency issues)
            for user_data in plan.users_to_create:
                upn = user_data.get('user_principal_name', '')
                try:
                    # Find user by UPN
                    users = await self._graph_client.users.get(
                        request_configuration=lambda req: setattr(
                            req.query_parameters, 'filter', f"userPrincipalName eq '{upn}'"
                        )
                    )
                    if users and users.value:
                        user_id = users.value[0].id
                        await self._graph_client.users.by_user_id(user_id).delete()
                        console.print(f"[green]✓ Deleted user: {upn}[/green]")
                except Exception as e:
                    console.print(f"[yellow]Warning: Could not delete user {upn}: {e}[/yellow]")
            
            # Delete groups
            for group_name in plan.groups_to_create:
                try:
                    # Find group by display name
                    groups = await self._graph_client.groups.get(
                        request_configuration=lambda req: setattr(
                            req.query_parameters, 'filter', f"displayName eq '{group_name}'"
                        )
                    )
                    if groups and groups.value:
                        group_id = groups.value[0].id
                        await self._graph_client.groups.by_group_id(group_id).delete()
                        console.print(f"[green]✓ Deleted group: {group_name}[/green]")
                except Exception as e:
                    console.print(f"[yellow]Warning: Could not delete group {group_name}: {e}[/yellow]")
            
            console.print("[green]✓ Resources cleanup completed[/green]")
            return True
            
        except Exception as e:
            console.print(f"[red]Error during cleanup: {e}[/red]")
            logger.error(f"Error during cleanup: {e}")
            return False


def create_azure_client(config: Config) -> AzureClient:
    """Factory function to create an Azure client."""
    return AzureClient(config)