# Software Requirements Specification (SRS)

## Project Name

**EntraSim: Azure Tenant and Identity Simulation Tool**

---

## 1. Introduction

### 1.1 Purpose

EntraSim is a command-line software tool designed to automate the creation of realistic Azure Active Directory (Entra ID) environments for simulation purposes. Given a descriptive input of a company's profile and operational roles, EntraSim generates an Azure tenant populated with representative user accounts and security groups. The resulting environment facilitates realistic security scenarios and training exercises without requiring actual customer data or large-scale deployments.

### 1.2 Scope

The software will:

- Accept descriptive information of a simulated company.
- Generate representative Azure Entra ID tenant structures.
- Create security groups and user accounts representative of the company's operational roles.
- Allow configurable parameters for complexity (number and type of roles).
- Use provided Azure tenant and subscription details for creating resources.
- Include built-in command-line help.
- Manage sensitive configurations via environment variables or a `.env` file.

The software will **NOT**:

- Copy or manage real customer data.
- Create massive-scale tenants; it will focus on representative complexity.

### 1.3 Intended Users

- Security researchers
- IT administrators and cloud architects
- Security training scenario developers
- Developers building simulations for security exercises

---

## 2. Functional Requirements

### 2.1 Command-Line Interface (CLI)

#### 2.1.1 User Story: Command-Line Interface

**As a** security researcher or scenario developer,  
**I want** a simple, intuitive command-line interface (CLI)  
**so that** I can easily configure and generate simulated Azure environments without a complex GUI.

**Acceptance Criteria:**

- CLI provides built-in help via standard flags (`--help` or `-h`).
- CLI clearly documents required and optional parameters.
- CLI displays meaningful error messages if incorrect input is provided.

### 2.2 Input and Configuration Management

#### 2.2.1 User Story: Environment Configuration

**As an** administrator or scenario developer,  
**I want** to manage configuration secrets via environment variables or `.env` files  
**so that** sensitive information such as Azure credentials are not exposed in commands or stored directly in code.

**Acceptance Criteria:**

- Software reads required secrets (tenant ID, client ID, secret, and subscription ID) from environment variables or `.env` file.
- Software provides descriptive error messages if required secrets are missing or invalid.

#### 2.2.2 User Story: Tenant and Subscription Input

**As a** scenario developer,  
**I want** to input an Azure tenant ID and subscription ID  
**so that** the generated simulation is created in the correct Azure environment.

**Acceptance Criteria:**

- CLI accepts tenant ID and subscription ID as inputs from configuration.
- Software validates the format and presence of these inputs before performing operations.

#### 2.2.3 User Story: Company Description Input

**As a** scenario developer,  
**I want** to input a structured description of the simulated company and its required operational roles and complexity parameters  
**so that** the generated tenant accurately reflects the desired complexity and role coverage.

**Acceptance Criteria:**

- CLI supports input via structured file (e.g., JSON or YAML) describing the simulated company, roles, and complexity parameters.
- CLI validates the correctness and completeness of the descriptive input before proceeding with tenant creation.

### 2.3 Azure Tenant and Identity Creation

#### 2.3.1 User Story: Azure Entra ID Tenant Creation

**As a** scenario developer,  
**I want** the software to automatically provision an Azure Entra ID tenant and configure it appropriately  
**so that** the simulation environment is consistently reproducible and realistic.

**Acceptance Criteria:**

- Software can provision an Azure Entra ID tenant or use an existing tenant (based on configuration).
- Software validates successful tenant creation or connection.