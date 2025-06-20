"""CLI interface for EntraSim using rich framework."""

import argparse
import sys
from pathlib import Path
from typing import Optional

from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich import print as rprint

from .config import get_config, Config
from .core import EntraSimCore
from .azure_client import create_azure_client

console = Console()


def create_parser() -> argparse.ArgumentParser:
    """Create and configure the argument parser."""
    parser = argparse.ArgumentParser(
        prog="entrasim",
        description="Azure Tenant and Identity Simulation Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  entrasim create company.json
  entrasim create company.yaml --dry-run
  entrasim create company.json --env-file custom.env
  entrasim validate company.json
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
        '--dry-run',
        action='store_true',
        help='Perform dry run without making actual changes'
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
        help='Enable verbose output'
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


def handle_create_command(args, config: Config) -> bool:
    """Handle the create command."""
    try:
        input_file = Path(args.input_file)
        
        console.print(f"[blue]Creating simulation from: {input_file}[/blue]")
        
        # Initialize core logic
        core = EntraSimCore(config)
        
        # Validate input
        if not core.validate_input(input_file):
            return False
        
        # Parse company description
        company_desc = core.parse_company_description(input_file)
        
        # Generate simulation plan
        plan = core.generate_simulation_plan(company_desc)
        
        # Validate Azure connection
        if not core.validate_azure_connection():
            return False
        
        # Create Azure client and execute plan
        azure_client = create_azure_client(config)
        success = azure_client.execute_simulation_plan(plan)
        
        if success:
            console.print("[green]✓ Simulation created successfully![/green]")
            
            # Display summary
            console.print("\n[bold]Simulation Summary:[/bold]")
            console.print(f"  Company: {company_desc.name}")
            console.print(f"  Domain: {company_desc.domain}")
            console.print(f"  Users created: {plan.total_users}")
            console.print(f"  Groups created: {plan.total_groups}")
            
            if config.dry_run:
                console.print("\n[yellow]Note: This was a dry run. No actual resources were created.[/yellow]")
            
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
        
        # Display banner for all commands
        display_banner()
        
        # Set up configuration if needed
        config = None
        if args.command == 'create':
            try:
                # Override dry_run if specified in args
                env_file = getattr(args, 'env_file', None)
                config = get_config(env_file)
                
                if hasattr(args, 'dry_run') and args.dry_run:
                    config.dry_run = True
                
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