"""CLI interface for EntraSim using rich framework."""

import argparse
import logging
import sys
from pathlib import Path
from typing import Optional

from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich import print as rprint

from .config import get_config, Config
from .core import EntraSimCore
from .azure_client import create_azure_client

console = Console()


def setup_logging(verbose: bool = False):
    """Set up logging configuration."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('entrasim.log'),
            logging.StreamHandler() if verbose else logging.NullHandler()
        ]
    )


def create_parser() -> argparse.ArgumentParser:
    """Create and configure the argument parser."""
    parser = argparse.ArgumentParser(
        prog="entrasim",
        description="Azure Tenant and Identity Simulation Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  entrasim create company.json
  entrasim create company.yaml --force
  entrasim create company.json --env-file custom.env
  entrasim validate company.json
  entrasim cleanup company.json
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Create command
    create_parser = subparsers.add_parser(
        'create',
        help='Create Azure tenant simulation from company description'
    )
    create_parser.add_argument(
        'input_file',
        type=str,
        help='Path to company description file (JSON or YAML)'
    )
    create_parser.add_argument(
        '--force',
        action='store_true',
        help='Force creation without confirmation prompts (dangerous!)'
    )
    create_parser.add_argument(
        '--env-file',
        type=str,
        help='Path to custom .env file for configuration'
    )
    
    # Validate command
    validate_parser = subparsers.add_parser(
        'validate',
        help='Validate company description file format'
    )
    validate_parser.add_argument(
        'input_file',
        type=str,
        help='Path to company description file to validate'
    )
    
    # Cleanup command
    cleanup_parser = subparsers.add_parser(
        'cleanup',
        help='Clean up resources created by a simulation'
    )
    cleanup_parser.add_argument(
        'input_file',
        type=str,
        help='Path to company description file used for original simulation'
    )
    cleanup_parser.add_argument(
        '--force',
        action='store_true',
        help='Force cleanup without confirmation prompts (dangerous!)'
    )
    cleanup_parser.add_argument(
        '--env-file',
        type=str,
        help='Path to custom .env file for configuration'
    )
    
    # Global options
    parser.add_argument(
        '--version',
        action='version',
        version='EntraSim 0.1.0'
    )
    parser.add_argument(
        '--verbose',
        '-v',
        action='store_true',
        help='Enable verbose output and detailed logging'
    )
    
    return parser


def display_banner():
    """Display the EntraSim banner."""
    banner_text = Text("EntraSim", style="bold blue")
    subtitle = Text("Azure Tenant and Identity Simulation Tool", style="dim")
    
    panel = Panel(
        f"{banner_text}\n{subtitle}",
        border_style="blue",
        padding=(1, 2)
    )
    console.print(panel)


def confirm_operation(operation: str, details: str, force: bool = False) -> bool:
    """Confirm a potentially dangerous operation."""
    if force:
        console.print(f"[yellow]Force mode enabled. Proceeding with {operation}...[/yellow]")
        return True
    
    console.print(f"\n[bold red]⚠️  WARNING: {operation}[/bold red]")
    console.print(f"[yellow]{details}[/yellow]")
    console.print("\n[red]This will make real changes to your Azure tenant![/red]")
    
    response = console.input("\n[bold]Are you sure you want to continue? (type 'yes' to confirm): [/bold]")
    return response.lower() == 'yes'


def validate_azure_credentials(config: Config) -> bool:
    """Validate that Azure credentials are properly configured."""
    try:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task("Validating Azure credentials...", total=None)
            
            # Validate credentials format
            config.validate_required_credentials()
            progress.update(task, description="✓ Credential format validated")
            
            # Test actual connectivity
            azure_client = create_azure_client(config)
            if azure_client.authenticate():
                progress.update(task, description="✓ Azure authentication successful")
                return True
            else:
                progress.update(task, description="✗ Azure authentication failed")
                return False
                
    except Exception as e:
        console.print(f"[red]Credential validation failed: {e}[/red]")
        return False


def handle_create_command(args, config: Config) -> bool:
    """Handle the create command."""
    try:
        input_file = Path(args.input_file)
        
        console.print(f"[blue]Creating simulation from: {input_file}[/blue]")
        
        # Initialize core logic
        core = EntraSimCore(config)
        
        # Validate input
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task("Validating input file...", total=None)
            if not core.validate_input(input_file):
                return False
            progress.update(task, description="✓ Input file validated")
        
        # Parse company description
        company_desc = core.parse_company_description(input_file)
        
        # Generate simulation plan
        plan = core.generate_simulation_plan(company_desc)
        
        # Confirm the operation
        details = f"""
This will create the following resources in your Azure tenant:
- {plan.total_groups} security groups
- {plan.total_users} users
- Group memberships for all users

Company: {company_desc.name}
Domain: {company_desc.domain}
Tenant: {config.azure_tenant_id}
        """
        
        if not confirm_operation("Create Azure Resources", details.strip(), args.force):
            console.print("[yellow]Operation cancelled by user[/yellow]")
            return False
        
        # Validate Azure connection
        if not validate_azure_credentials(config):
            return False
        
        # Execute the plan
        success = core.execute_simulation_plan(plan)
        
        if success:
            console.print("\n[green]✓ Simulation created successfully![/green]")
            
            # Display summary
            console.print("\n[bold]Simulation Summary:[/bold]")
            console.print(f"  Company: {company_desc.name}")
            console.print(f"  Domain: {company_desc.domain}")
            console.print(f"  Users created: {plan.total_users}")
            console.print(f"  Groups created: {plan.total_groups}")
            
            console.print(f"\n[blue]Simulation details logged to: entrasim.log[/blue]")
            console.print(f"[yellow]To clean up these resources later, use: entrasim cleanup {input_file}[/yellow]")
            
        return success
        
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        return False


def handle_validate_command(args) -> bool:
    """Handle the validate command."""
    try:
        input_file = Path(args.input_file)
        console.print(f"[blue]Validating: {input_file}[/blue]")
        
        # We don't need full config for validation, just basic parsing
        from .core import validate_input_file
        success = validate_input_file(input_file)
        
        if success:
            console.print("[green]✓ File validation successful![/green]")
        
        return success
        
    except Exception as e:
        console.print(f"[red]Validation error: {e}[/red]")
        return False


def handle_cleanup_command(args, config: Config) -> bool:
    """Handle the cleanup command."""
    try:
        input_file = Path(args.input_file)
        
        console.print(f"[blue]Preparing cleanup from: {input_file}[/blue]")
        
        # Initialize core logic
        core = EntraSimCore(config)
        
        # Parse the original company description to understand what to clean up
        if not core.validate_input(input_file):
            return False
        
        company_desc = core.parse_company_description(input_file)
        plan = core.generate_simulation_plan(company_desc)
        
        # Confirm the cleanup operation
        details = f"""
This will DELETE the following resources from your Azure tenant:
- {plan.total_groups} security groups
- {plan.total_users} users

Company: {company_desc.name}
Domain: {company_desc.domain}
Tenant: {config.azure_tenant_id}

⚠️  This action CANNOT be undone!
        """
        
        if not confirm_operation("DELETE Azure Resources", details.strip(), args.force):
            console.print("[yellow]Cleanup cancelled by user[/yellow]")
            return False
        
        # Validate Azure connection
        if not validate_azure_credentials(config):
            return False
        
        # Execute cleanup
        success = core.cleanup_simulation(plan)
        
        if success:
            console.print("\n[green]✓ Cleanup completed successfully![/green]")
        else:
            console.print("\n[red]Cleanup encountered errors. Check logs for details.[/red]")
        
        return success
        
    except Exception as e:
        console.print(f"[red]Cleanup error: {e}[/red]")
        return False


def main():
    """Main entry point for the CLI."""
    try:
        parser = create_parser()
        
        # Show help if no arguments provided
        if len(sys.argv) == 1:
            display_banner()
            parser.print_help()
            return
        
        args = parser.parse_args()
        
        # Set up logging
        setup_logging(args.verbose)
        
        # Display banner for all commands
        display_banner()
        
        # Set up configuration if needed
        config = None
        if args.command in ['create', 'cleanup']:
            try:
                env_file = getattr(args, 'env_file', None)
                config = get_config(env_file)
                
                if args.verbose:
                    config.log_level = 'DEBUG'
                    
            except Exception as e:
                console.print(f"[red]Configuration error: {e}[/red]")
                console.print("\n[yellow]Make sure to set the following environment variables:[/yellow]")
                console.print("  - AZURE_TENANT_ID")
                console.print("  - AZURE_CLIENT_ID") 
                console.print("  - AZURE_CLIENT_SECRET")
                console.print("  - AZURE_SUBSCRIPTION_ID")
                console.print("\n[yellow]Or create a .env file with these values.[/yellow]")
                sys.exit(1)
        
        # Execute commands
        success = False
        
        if args.command == 'create':
            success = handle_create_command(args, config)
        elif args.command == 'validate':
            success = handle_validate_command(args)
        elif args.command == 'cleanup':
            success = handle_cleanup_command(args, config)
        else:
            parser.print_help()
            return
        
        sys.exit(0 if success else 1)
        
    except KeyboardInterrupt:
        console.print("\n[yellow]Operation cancelled by user[/yellow]")
        sys.exit(1)
    except Exception as e:
        console.print(f"[red]Unexpected error: {e}[/red]")
        if "--verbose" in sys.argv or "-v" in sys.argv:
            import traceback
            console.print(traceback.format_exc())
        sys.exit(1)


if __name__ == "__main__":
    main()