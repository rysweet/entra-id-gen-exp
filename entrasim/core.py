"""Core business logic for EntraSim."""

import json
import logging
from pathlib import Path
try:
    import yaml
except ImportError:
    yaml = None
from typing import Dict, Any, Union
from rich.console import Console

from .models import CompanyDescription, SimulationPlan
from .config import Config
from .azure_client import create_azure_client

console = Console()
logger = logging.getLogger(__name__)


class EntraSimCore:
    """Core business logic for EntraSim operations."""
    
    def __init__(self, config: Config):
        """Initialize with configuration."""
        self.config = config
        self.azure_client = None
    
    def validate_input(self, input_file: Path) -> bool:
        """Validate input file format and content."""
        if not input_file.exists():
            console.print(f"[red]Error: Input file {input_file} does not exist[/red]")
            return False
        
        if input_file.suffix.lower() not in ['.json', '.yaml', '.yml']:
            console.print(f"[red]Error: Input file must be JSON or YAML format[/red]")
            return False
        
        try:
            self.parse_company_description(input_file)
            console.print(f"[green]✓ Input file validation successful[/green]")
            return True
        except Exception as e:
            console.print(f"[red]Error validating input file: {e}[/red]")
            logger.error(f"Error validating input file: {e}")
            return False
    
    def parse_company_description(self, input_file: Path) -> CompanyDescription:
        """Parse structured input (YAML/JSON) into CompanyDescription model."""
        try:
            with open(input_file, 'r', encoding='utf-8') as f:
                if input_file.suffix.lower() == '.json':
                    data = json.load(f)
                else:  # YAML
                    if yaml is None:
                        raise ValueError("PyYAML is not installed. Install it with: pip install pyyaml")
                    data = yaml.safe_load(f)
            
            # Validate and create CompanyDescription
            company_desc = CompanyDescription(**data)
            
            console.print(f"[green]✓ Parsed company: {company_desc.name}[/green]")
            console.print(f"  Domain: {company_desc.domain}")
            console.print(f"  Industry: {company_desc.industry}")
            console.print(f"  Size: {company_desc.size}")
            console.print(f"  Total users to create: {company_desc.get_total_users()}")
            console.print(f"  Departments: {', '.join(company_desc.get_departments())}")
            
            return company_desc
            
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON format: {e}")
        except Exception as e:
            if yaml is not None and hasattr(yaml, 'YAMLError') and isinstance(e, yaml.YAMLError):
                raise ValueError(f"Invalid YAML format: {e}")
            elif str(type(e)).find('yaml') >= 0:
                raise ValueError(f"Invalid YAML format: {e}")
            else:
                raise ValueError(f"Error parsing company description: {e}")
    
    def generate_simulation_plan(
        self, 
        company_desc: CompanyDescription
    ) -> SimulationPlan:
        """Create a structured plan detailing Azure resources to create."""
        try:
            plan = SimulationPlan.from_company_description(
                company=company_desc,
                tenant_id=self.config.azure_tenant_id,
                subscription_id=self.config.azure_subscription_id
            )
            
            console.print("[green]✓ Simulation plan generated[/green]")
            console.print(f"  Total users: {plan.total_users}")
            console.print(f"  Total groups: {plan.total_groups}")
            console.print(f"  Groups to create: {', '.join(plan.groups_to_create)}")
            
            if self.config.log_level == 'DEBUG':
                console.print("\n[yellow]User details:[/yellow]")
                for user in plan.users_to_create:
                    console.print(f"  - {user['display_name']} ({user['user_principal_name']})")
            
            return plan
            
        except Exception as e:
            logger.error(f"Error generating simulation plan: {e}")
            raise ValueError(f"Error generating simulation plan: {e}")
    
    def validate_azure_connection(self) -> bool:
        """Validate Azure connection and credentials."""
        try:
            # Validate that credentials are present
            self.config.validate_required_credentials()
            
            console.print("[green]✓ Azure credentials validated[/green]")
            console.print(f"  Tenant ID: {self.config.azure_tenant_id}")
            console.print(f"  Subscription ID: {self.config.azure_subscription_id}")
            
            # Test actual connectivity by creating and testing the Azure client
            try:
                self.azure_client = create_azure_client(self.config)
                if self.azure_client.authenticate():
                    console.print("[green]✓ Azure authentication successful[/green]")
                    return True
                else:
                    console.print("[red]Azure authentication failed[/red]")
                    return False
            except Exception as auth_error:
                console.print(f"[red]Azure authentication error: {auth_error}[/red]")
                logger.error(f"Azure authentication error: {auth_error}")
                return False
            
        except Exception as e:
            console.print(f"[red]Error validating Azure connection: {e}[/red]")
            logger.error(f"Error validating Azure connection: {e}")
            return False
    
    def execute_simulation_plan(self, plan: SimulationPlan) -> bool:
        """Execute the simulation plan using real Azure operations."""
        try:
            console.print(f"[blue]Executing simulation plan for {plan.company.name}...[/blue]")
            
            # Ensure we have an authenticated Azure client
            if not self.azure_client:
                self.azure_client = create_azure_client(self.config)
            
            # Execute the plan using the Azure client
            success = self.azure_client.execute_simulation_plan(plan)
            
            if success:
                console.print("[green]✓ Simulation plan executed successfully[/green]")
                console.print(f"  Created {plan.total_groups} security groups")
                console.print(f"  Created {plan.total_users} users")
                console.print(f"  Configured group memberships")
                
                # Log important information for cleanup later
                logger.info(f"Successfully created simulation for {plan.company.name}")
                logger.info(f"Groups created: {', '.join(plan.groups_to_create)}")
                logger.info(f"Users created: {len(plan.users_to_create)}")
            else:
                console.print("[red]Failed to execute simulation plan[/red]")
            
            return success
            
        except Exception as e:
            console.print(f"[red]Error executing simulation plan: {e}[/red]")
            logger.error(f"Error executing simulation plan: {e}")
            return False
    
    def cleanup_simulation(self, plan: SimulationPlan) -> bool:
        """Clean up resources created by a simulation."""
        try:
            console.print(f"[yellow]Cleaning up simulation for {plan.company.name}...[/yellow]")
            
            # Ensure we have an authenticated Azure client
            if not self.azure_client:
                self.azure_client = create_azure_client(self.config)
                if not self.azure_client.authenticate():
                    console.print("[red]Failed to authenticate for cleanup[/red]")
                    return False
            
            # Execute cleanup
            import asyncio
            success = asyncio.run(self.azure_client.cleanup_resources(plan))
            
            if success:
                console.print("[green]✓ Simulation cleanup completed successfully[/green]")
            else:
                console.print("[red]Simulation cleanup encountered errors[/red]")
            
            return success
            
        except Exception as e:
            console.print(f"[red]Error during cleanup: {e}[/red]")
            logger.error(f"Error during cleanup: {e}")
            return False


def validate_input_file(input_file: Union[str, Path]) -> bool:
    """Standalone function to validate input file."""
    try:
        input_path = Path(input_file)
        
        if not input_path.exists():
            console.print(f"[red]Error: Input file {input_path} does not exist[/red]")
            return False
        
        if input_path.suffix.lower() not in ['.json', '.yaml', '.yml']:
            console.print(f"[red]Error: Input file must be JSON or YAML format[/red]")
            return False
        
        # Parse the file to validate structure
        with open(input_path, 'r', encoding='utf-8') as f:
            if input_path.suffix.lower() == '.json':
                data = json.load(f)
            else:  # YAML
                if yaml is None:
                    raise ValueError("PyYAML is not installed. Install it with: pip install pyyaml")
                data = yaml.safe_load(f)
        
        # Validate using pydantic model
        company_desc = CompanyDescription(**data)
        
        console.print(f"[green]✓ File validation successful![/green]")
        console.print(f"  Company: {company_desc.name}")
        console.print(f"  Domain: {company_desc.domain}")
        console.print(f"  Total users: {company_desc.get_total_users()}")
        console.print(f"  Departments: {', '.join(company_desc.get_departments())}")
        
        return True
        
    except Exception as e:
        console.print(f"[red]Validation error: {e}[/red]")
        logger.error(f"Validation error: {e}")
        return False