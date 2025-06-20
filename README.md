# EntraSim: Azure Tenant and Identity Simulation Tool

EntraSim is a command-line tool that automates the creation of realistic Azure Active Directory (Entra ID) environments for simulation purposes. Given a company description, it generates an Azure tenant populated with representative user accounts and security groups.

## Features

- ✅ **Company Description Input**: Accepts JSON/YAML files describing company structure and roles
- ✅ **Azure Integration**: Uses Microsoft Graph SDK for Azure AD operations
- ✅ **Rich CLI Interface**: Beautiful command-line interface with colored output and progress indicators
- ✅ **Configuration Management**: Secure handling of Azure credentials via environment variables
- ✅ **Validation**: Input validation and error handling with helpful messages
- ✅ **Dry Run Mode**: Test configurations without making actual changes
- ✅ **Modular Architecture**: Clean separation of concerns for easy extension

## Quick Start

### 1. Installation

```bash
# Clone the repository
git clone <repository-url>
cd entra-id-gen-exp

# Install dependencies using uv
uv sync

# Activate the virtual environment
source .venv/bin/activate
```

### 2. Configuration

Create a `.env` file with your Azure credentials:

```bash
cp .env.example .env
# Edit .env with your actual Azure credentials
```

Required environment variables:
- `AZURE_TENANT_ID`: Your Azure tenant ID
- `AZURE_CLIENT_ID`: Your Azure application client ID  
- `AZURE_CLIENT_SECRET`: Your Azure application client secret
- `AZURE_SUBSCRIPTION_ID`: Your Azure subscription ID

### 3. Usage

#### Validate a company description file:
```bash
entrasim validate sample_company.json
```

#### Create a simulation (dry run):
```bash
entrasim create sample_company.json --dry-run
```

#### Create a simulation (actual):
```bash
entrasim create sample_company.json
```

#### Get help:
```bash
entrasim --help
entrasim create --help
```

## Sample Company Description

See [`sample_company.json`](sample_company.json:1) for an example company description that creates:
- 37 users across 6 departments
- 19 security groups (department + role-based)
- Multiple role types with different seniority levels

## Project Structure

```
entrasim/
├── cli.py          # CLI interface using rich framework
├── config.py       # Configuration management
├── models.py       # Pydantic data models
├── core.py         # Core business logic
├── azure_client.py # Azure integration layer
└── __main__.py     # Entry point for python -m entrasim
```

## Current Status

This is the initial implementation focusing on core functionality:

- ✅ Project structure and package management with uv
- ✅ CLI interface with argument parsing and help system
- ✅ Input validation and company description parsing
- ✅ Simulation plan generation
- ✅ Dry-run mode for testing
- 🚧 Azure integration (placeholder implementation)
- 📋 Documentation and comprehensive testing (upcoming)

## Development

### Requirements

- Python 3.12+
- uv package manager
- Azure subscription and service principal

### Contributing

1. Create a feature branch from `main`
2. Make your changes following the existing architecture
3. Test your changes with dry-run mode
4. Submit a pull request

## License

MIT License - see [LICENSE](LICENSE) for details.
