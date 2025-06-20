# Software Design Specification (SDS)

## Project Name

**EntraSim: Azure Tenant and Identity Simulation Tool**

---

## 1. Overview

This Software Design Specification (SDS) outlines the architecture and design of **EntraSim**, a command-line tool developed in Python 3.12. EntraSim generates Azure Entra ID environments, security groups, and user accounts based on company descriptions, tenant IDs, and configurations. It leverages Azure SDKs (Microsoft Graph SDK) for managing Entra ID resources.

---

## 2. Technology Stack and Tooling

| Item                | Selection                              |
|---------------------|----------------------------------------|
| Language            | Python 3.12                            |
| Package Management  | uv                                     |
| CLI Framework       | rich                                   |
| Azure SDK           | Microsoft Graph SDK for Python         |
| Linting/Formatting  | ruff                                   |
| Type Checking       | pyright                                |
| Testing Framework   | pytest                                 |
| Configuration Files | .env files and environment variables   |

---

## 3. System Architecture

The design is modular, with a clear separation of concerns:

```
EntraSim
├── CLI Layer (rich CLI)
│   ├── Command Parsing
│   ├── CLI Display & Logging
│   └── Help & Usage Documentation
├── Core Logic Layer
│   ├── Input Validation
│   ├── Configuration Management (.env, env vars)
│   ├── Simulation Generation Logic
│   └── Company Description Parsing
├── Azure Integration Layer (Azure SDK)
│   ├── Authentication & Authorization
│   ├── Tenant Management
│   ├── Entra ID User Management
│   └── Entra ID Group Management
└── Testing Layer (pytest)
    ├── Unit tests
    └── Integration tests
```

---

## 4. Module and Component Design

### 4.1 CLI Layer (`cli.py`)

**Purpose:**  
Provides a user-friendly CLI interface for user interaction.

**Dependencies:**  
- `rich` (for CLI display and logging)
- Core logic layer components (`core.py`)

**Key Functions:**
- `parse_args()`: Parses command-line arguments.
- `main()`: Entry point; executes actions based on parsed arguments.

---

### 4.2 Core Logic Layer (`core.py`, `config.py`, `models.py`)

**Purpose:**  
Handles business logic, configuration management, and input validation.

**Dependencies:**  
- `pydantic` (optional, recommended for structured input validation)
- `python-dotenv` (for `.env` file loading)

**Key Components:**

- **config.py**
  - `Config`: Loads environment variables and manages sensitive data.

- **models.py**
  - `CompanyDescription`: Structured representation of the simulated company.
  - `RoleDefinition`: Representation of user roles and complexity parameters.

- **core.py**
  - `validate_input()`: Validates user input and configuration.
  - `parse_company_description()`: Parses structured input (YAML/JSON) into internal data models.
  - `generate_simulation_plan()`: Creates a structured plan detailing Azure resources to create.

---

### 4.3 Azure Integration Layer (`azure_client.py`)

**Purpose:**  
Interacts with Azure SDK (Microsoft Graph SDK) for resource creation and tenant management.

**Dependencies:**  
- Microsoft Graph SDK for Python
- Azure identity libraries (for authentication)

**Key Components:**
- `AzureClient`: Class encapsulating Graph SDK interactions
