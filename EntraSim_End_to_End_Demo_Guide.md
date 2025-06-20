# EntraSim End-to-End Demo Guide

## Overview

EntraSim is a command-line tool that creates realistic Azure Active Directory (Entra ID) tenant simulations using the Microsoft Graph SDK. It generates users, security groups, and organizational structures based on company descriptions defined in JSON or YAML files.

## Table of Contents

1. [Prerequisites and Azure Setup](#1-prerequisites-and-azure-setup)
2. [Environment Configuration](#2-environment-configuration)
3. [Installation and Setup](#3-installation-and-setup)
4. [Complete Walkthrough](#4-complete-walkthrough)
5. [Available CLI Commands](#5-available-cli-commands)
6. [Verification Steps](#6-verification-steps)
7. [Cleanup Procedures](#7-cleanup-procedures)
8. [Azure Permissions and Setup](#8-azure-permissions-and-setup)
9. [Troubleshooting](#9-troubleshooting)
10. [Security Considerations](#10-security-considerations)

---

## 1. Prerequisites and Azure Setup

### System Requirements
- **Python**: 3.10 or higher
- **Operating System**: Windows, macOS, or Linux
- **Package Manager**: uv (recommended) or pip
- **Azure CLI**: Latest version (for initial setup)

### Azure Requirements
- Active Azure subscription
- Azure AD/Entra ID tenant with administrative access
- Permissions to create and manage:
  - Users and user accounts
  - Security groups
  - Application registrations (service principals)

### Required Azure Roles
Your account must have one of the following roles:
- **Global Administrator** (recommended for setup)
- **User Administrator** + **Application Administrator**
- **Privileged Role Administrator**

---

## 2. Environment Configuration

### Step 1: Create Azure Service Principal

First, create a service principal that EntraSim will use to authenticate with Azure:

```bash
# Login to Azure CLI
az login

# Get your subscription ID
az account show --query id --output tsv

# Create service principal with required permissions
az ad sp create-for-rbac \
  --name "EntraSim-ServicePrincipal" \
  --role "User Administrator" \
  --scopes /subscriptions/{your-subscription-id}
```

**Expected Output:**
```json
{
  "appId": "12345678-1234-1234-1234-123456789abc",
  "displayName": "EntraSim-ServicePrincipal",
  "password": "your-client-secret-here",
  "tenant": "87654321-4321-4321-4321-cba987654321"
}
```

### Step 2: Grant Additional Permissions

The service principal needs specific Microsoft Graph API permissions:

```bash
# Get the service principal object ID
SP_ID=$(az ad sp list --display-name "EntraSim-ServicePrincipal" --query "[0].id" -o tsv)

# Grant Microsoft Graph permissions
az ad app permission add \
  --id {appId-from-above} \
  --api 00000003-0000-0000-c000-000000000000 \
  --api-permissions \
    741f803b-c850-494e-b5df-cde7c675a1ca=Role \
    62a82d76-70ea-41e2-9197-370581804d09=Role \
    19dbc75e-c2e2-444c-a770-ec69d8559fc7=Role

# Grant admin consent
az ad app permission admin-consent --id {appId-from-above}
```

### Step 3: Configure Environment Variables

Create a `.env` file in your project directory:

```bash
# Copy the example file
cp .env.example .env
```

Edit the `.env` file with your Azure credentials:

```bash
# Azure Configuration
AZURE_TENANT_ID=87654321-4321-4321-4321-cba987654321
AZURE_CLIENT_ID=12345678-1234-1234-1234-123456789abc
AZURE_CLIENT_SECRET=your-client-secret-here
AZURE_SUBSCRIPTION_ID=your-subscription-id-here

# Optional Configuration
LOG_LEVEL=INFO
```

**Security Note**: Never commit the `.env` file to version control. It contains sensitive credentials.

---

## 3. Installation and Setup

### Option 1: Using uv (Recommended)

```bash
# Install uv if not already installed
curl -LsSf https://astral.sh/uv/install.sh | sh

# Clone the repository
git clone <repository-url>
cd entra-id-gen-exp

# Create virtual environment and install dependencies
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install EntraSim in development mode
uv pip install -e .

# Verify installation
entrasim --version
```

**Expected Output:**
```
EntraSim 0.1.0
```

### Option 2: Using pip

```bash
# Clone the repository
git clone <repository-url>
cd entra-id-gen-exp

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -e .

# Verify installation
entrasim --version
```

---

## 4. Complete Walkthrough

### Step 1: Validate Company Description

First, validate the sample company file to ensure it's properly formatted:

```bash
entrasim validate sample_company.json
```

**Expected Output:**
```
┌────────────────────────────────────────────────────────────┐
│                         EntraSim                           │
│            Azure Tenant and Identity Simulation Tool      │
└────────────────────────────────────────────────────────────┘

✓ File validation successful!
  Company: Contoso Corporation
  Domain: contoso.com
  Total users: 37
  Departments: Engineering, Finance, Human Resources, Marketing, Operations, Sales
```

### Step 2: Review What Will Be Created

The sample company will create:
- **37 users** across 6 departments
- **19 security groups** (6 department groups + 13 role-based groups)
- Realistic user profiles with job titles and departmental assignments
- Proper group memberships based on roles and departments

### Step 3: Create the Simulation

Run the creation command with confirmation prompts:

```bash
entrasim create sample_company.json
```

**Expected Output:**
```
┌────────────────────────────────────────────────────────────┐
│                         EntraSim                           │
│            Azure Tenant and Identity Simulation Tool      │
└────────────────────────────────────────────────────────────┘

Creating simulation from: sample_company.json
✓ Input file validated
✓ Parsed company: Contoso Corporation
  Domain: contoso.com
  Industry: Technology
  Size: medium
  Total users to create: 37
  Departments: Engineering, Finance, Human Resources, Marketing, Operations, Sales
✓ Simulation plan generated
  Total users: 37
  Total groups: 19
  Groups to create: Engineering, Finance, Human Resources, Marketing, Operations, Sales, software_engineer_group, senior_software_engineer_group, engineering_manager_group, sales_representative_group, sales_manager_group, marketing_specialist_group, marketing_manager_group, hr_specialist_group, hr_manager_group, financial_analyst_group, finance_manager_group, operations_coordinator_group, operations_manager_group

⚠️  WARNING: Create Azure Resources

This will create the following resources in your Azure tenant:
- 19 security groups
- 37 users
- Group memberships for all users

Company: Contoso Corporation
Domain: contoso.com
Tenant: your-tenant-id

🔴 This will make real changes to your Azure tenant!

Are you sure you want to continue? (type 'yes' to confirm): yes
```

### Step 4: Monitor Creation Process

After confirmation, EntraSim will:

```
✓ Validating Azure credentials...
✓ Credential format validated
✓ Azure authentication successful
Executing simulation for Contoso Corporation...
Authenticating with Azure...
✓ Authenticated with tenant: your-tenant-id
Validating tenant access...
✓ Tenant access validated for: Your Organization Name
Creating 19 security groups...
✓ Created security group: Engineering (ID: group-id-1)
✓ Created security group: Finance (ID: group-id-2)
✓ Created security group: Human Resources (ID: group-id-3)
[... continues for all groups ...]

Creating 37 users...
✓ Created user: Software Engineer 1 (user1@contoso.com) - ID: user-id-1
✓ Added user user-id-1 to group group-id-engineering
✓ Added user user-id-1 to group group-id-software-engineer
[... continues for all users ...]

✓ Successfully executed simulation plan
  Created 19 groups
  Created 37 users

✓ Simulation created successfully!

Simulation Summary:
  Company: Contoso Corporation
  Domain: contoso.com
  Users created: 37
  Groups created: 19

Simulation details logged to: entrasim.log
To clean up these resources later, use: entrasim cleanup sample_company.json
```

---

## 5. Available CLI Commands

### 5.1 Command Overview

```bash
entrasim --help
```

**Available Commands:**
- [`validate`](#validate-command) - Validate company description file format
- [`create`](#create-command) - Create Azure tenant simulation
- [`cleanup`](#cleanup-command) - Clean up simulation resources

### 5.2 Validate Command

Validates the structure and format of a company description file without making any Azure changes.

```bash
# Basic validation
entrasim validate sample_company.json

# Validate YAML file
entrasim validate company_config.yaml

# With verbose output
entrasim validate sample_company.json --verbose
```

**Use Cases:**
- Verify file format before creation
- Test company description modifications
- Troubleshoot configuration issues

### 5.3 Create Command

Creates the complete simulation in your Azure tenant.

```bash
# Interactive creation (with confirmation prompts)
entrasim create sample_company.json

# Force creation without prompts (dangerous!)
entrasim create sample_company.json --force

# Use custom environment file
entrasim create sample_company.json --env-file production.env

# Enable verbose logging
entrasim create sample_company.json --verbose
```

**Options:**
- `--force` - Skip confirmation prompts (use with extreme caution)
- `--env-file PATH` - Use custom environment file
- `--verbose` - Enable detailed logging output

### 5.4 Cleanup Command

Removes all resources created by a simulation.

```bash
# Interactive cleanup (with confirmation prompts)
entrasim cleanup sample_company.json

# Force cleanup without prompts
entrasim cleanup sample_company.json --force

# Use custom environment file
entrasim cleanup sample_company.json --env-file production.env
```

**⚠️ Warning**: Cleanup permanently deletes users and groups. This action cannot be undone.

---

## 6. Verification Steps

### 6.1 Verify in Azure Portal

1. **Navigate to Azure Portal**:
   - Go to [portal.azure.com](https://portal.azure.com)
   - Select your tenant

2. **Check Users**:
   - Navigate to **Azure Active Directory > Users**
   - Filter by domain (e.g., `contoso.com`)
   - Verify 37 users were created with proper names and roles

3. **Check Groups**:
   - Navigate to **Azure Active Directory > Groups**
   - Look for department groups (Engineering, Sales, etc.)
   - Look for role-specific groups (software_engineer_group, etc.)
   - Verify group memberships by clicking on individual groups

### 6.2 Verify Using Azure CLI

```bash
# List all users from the simulation domain
az ad user list --query "[?contains(userPrincipalName,'contoso.com')].{Name:displayName,UPN:userPrincipalName,Department:department}" --output table

# List all groups created
az ad group list --query "[?contains(displayName,'Engineering')||contains(displayName,'Sales')||contains(displayName,'software_engineer')].{Name:displayName,Description:description}" --output table

# Check group membership for a specific user
az ad group member list --group "Engineering" --query "[].displayName" --output table
```

### 6.3 Verify Using PowerShell

```powershell
# Connect to Azure AD
Connect-AzureAD

# List users from simulation
Get-AzureADUser -Filter "userType eq 'Member'" | Where-Object {$_.UserPrincipalName -like "*contoso.com"} | Select-Object DisplayName, UserPrincipalName, Department

# List groups
Get-AzureADGroup | Where-Object {$_.DisplayName -like "*Engineering*" -or $_.DisplayName -like "*Sales*"} | Select-Object DisplayName, Description

# Check group members
Get-AzureADGroupMember -ObjectId (Get-AzureADGroup -Filter "DisplayName eq 'Engineering'").ObjectId | Select-Object DisplayName
```

### 6.4 Check Logs

Review the detailed log file for complete operation details:

```bash
# View recent log entries
tail -50 entrasim.log

# Search for specific operations
grep "Created user" entrasim.log
grep "Created security group" entrasim.log
grep "ERROR" entrasim.log
```

---

## 7. Cleanup Procedures

### 7.1 Standard Cleanup

Remove all resources created by the simulation:

```bash
entrasim cleanup sample_company.json
```

**Expected Output:**
```
┌────────────────────────────────────────────────────────────┐
│                         EntraSim                           │
│            Azure Tenant and Identity Simulation Tool      │
└────────────────────────────────────────────────────────────┘

Preparing cleanup from: sample_company.json
✓ Input file validation successful
✓ Parsed company: Contoso Corporation

⚠️  WARNING: DELETE Azure Resources

This will DELETE the following resources from your Azure tenant:
- 19 security groups
- 37 users

Company: Contoso Corporation
Domain: contoso.com
Tenant: your-tenant-id

⚠️  This action CANNOT be undone!

Are you sure you want to continue? (type 'yes' to confirm): yes

✓ Validating Azure credentials...
✓ Azure authentication successful
Cleaning up simulation for Contoso Corporation...
✓ Deleted user: user1@contoso.com
✓ Deleted user: user2@contoso.com
[... continues for all users ...]
✓ Deleted group: Engineering
✓ Deleted group: Sales
[... continues for all groups ...]

✓ Cleanup completed successfully!
```

### 7.2 Force Cleanup

For automated scenarios or when confirmation prompts are not desired:

```bash
entrasim cleanup sample_company.json --force
```

### 7.3 Partial Cleanup (Manual)

If needed, you can manually clean up specific resources using Azure CLI:

```bash
# Delete specific users
az ad user delete --id user1@contoso.com

# Delete specific groups
az ad group delete --group "Engineering"

# Bulk delete users by domain
az ad user list --query "[?contains(userPrincipalName,'contoso.com')].id" --output tsv | \
xargs -I {} az ad user delete --id {}
```

### 7.4 Verify Cleanup

Confirm all resources were removed:

```bash
# Check for remaining users
az ad user list --query "[?contains(userPrincipalName,'contoso.com')]" --output table

# Check for remaining groups
az ad group list --query "[?contains(displayName,'Engineering')||contains(displayName,'software_engineer')]" --output table
```

---

## 8. Azure Permissions and Setup

### 8.1 Required API Permissions

The service principal needs these Microsoft Graph permissions:

| Permission | Type | Purpose |
|------------|------|---------|
| `User.ReadWrite.All` | Application | Create and manage users |
| `Group.ReadWrite.All` | Application | Create and manage groups |
| `Directory.Read.All` | Application | Read organization information |

### 8.2 Setting Up Service Principal

#### Method 1: Azure Portal

1. **Navigate to App Registrations**:
   - Go to Azure Portal > Azure Active Directory > App registrations
   - Click "New registration"

2. **Register Application**:
   - Name: "EntraSim"
   - Supported account types: "Accounts in this organizational directory only"
   - Click "Register"

3. **Create Client Secret**:
   - Go to "Certificates & secrets"
   - Click "New client secret"
   - Description: "EntraSim CLI Secret"
   - Expires: Choose appropriate duration
   - Copy the secret value (you won't see it again)

4. **Configure API Permissions**:
   - Go to "API permissions"
   - Click "Add a permission" > "Microsoft Graph" > "Application permissions"
   - Add: `User.ReadWrite.All`, `Group.ReadWrite.All`, `Directory.Read.All`
   - Click "Grant admin consent for [tenant]"

5. **Note Required Values**:
   - Application (client) ID
   - Directory (tenant) ID
   - Client secret value

#### Method 2: Azure CLI (Automated)

```bash
# Create app registration
APP_ID=$(az ad app create \
  --display-name "EntraSim" \
  --query appId --output tsv)

# Create service principal
az ad sp create --id $APP_ID

# Create client secret
CLIENT_SECRET=$(az ad app credential reset \
  --id $APP_ID \
  --append \
  --credential-description "EntraSim CLI Secret" \
  --query password --output tsv)

# Grant permissions
az ad app permission add --id $APP_ID --api 00000003-0000-0000-c000-000000000000 --api-permissions 741f803b-c850-494e-b5df-cde7c675a1ca=Role
az ad app permission add --id $APP_ID --api 00000003-0000-0000-c000-000000000000 --api-permissions 62a82d76-70ea-41e2-9197-370581804d09=Role
az ad app permission add --id $APP_ID --api 00000003-0000-0000-c000-000000000000 --api-permissions 19dbc75e-c2e2-444c-a770-ec69d8559fc7=Role

# Grant admin consent
az ad app permission admin-consent --id $APP_ID

echo "App ID: $APP_ID"
echo "Client Secret: $CLIENT_SECRET"
echo "Tenant ID: $(az account show --query tenantId --output tsv)"
```

### 8.3 Tenant Administrator Requirements

The user setting up EntraSim must have sufficient privileges to:

1. **Create App Registrations**: Application Administrator or Global Administrator
2. **Grant Admin Consent**: Privileged Role Administrator or Global Administrator
3. **Assign Administrative Roles**: Privileged Role Administrator or Global Administrator

### 8.4 Role Assignments

Assign the User Administrator role to the service principal:

```bash
# Get service principal object ID
SP_OBJECT_ID=$(az ad sp list --display-name "EntraSim" --query "[0].id" --output tsv)

# Get User Administrator role template ID
USER_ADMIN_ROLE_ID=$(az rest --method GET --url https://graph.microsoft.com/v1.0/directoryRoleTemplates --query "value[?displayName=='User Administrator'].id" --output tsv)

# Activate the role if not already active
az rest --method POST --url https://graph.microsoft.com/v1.0/directoryRoles --body "{\"roleTemplateId\":\"$USER_ADMIN_ROLE_ID\"}"

# Get the active role ID
ACTIVE_ROLE_ID=$(az rest --method GET --url https://graph.microsoft.com/v1.0/directoryRoles --query "value[?roleTemplateId=='$USER_ADMIN_ROLE_ID'].id" --output tsv)

# Assign the role to service principal
az rest --method POST --url https://graph.microsoft.com/v1.0/directoryRoles/$ACTIVE_ROLE_ID/members/\$ref --body "{\"@odata.id\":\"https://graph.microsoft.com/v1.0/servicePrincipals/$SP_OBJECT_ID\"}"
```

---

## 9. Troubleshooting

### 9.1 Authentication Errors

#### Error: "Authentication failed: unauthorized"

**Symptoms:**
```
[red]Authentication failed: AADSTS7000215: Invalid client secret is provided.[/red]
```

**Solutions:**
1. **Check client secret**: Verify the `AZURE_CLIENT_SECRET` in your `.env` file
2. **Regenerate secret**: Client secrets expire - create a new one in Azure Portal
3. **Verify credentials**: Ensure all GUIDs are correctly formatted

**Verification Commands:**
```bash
# Test authentication manually
az login --service-principal \
  --username $AZURE_CLIENT_ID \
  --password $AZURE_CLIENT_SECRET \
  --tenant $AZURE_TENANT_ID
```

#### Error: "Tenant validation failed: Forbidden"

**Symptoms:**
```
[red]Tenant validation failed: Insufficient privileges to complete the operation.[/red]
```

**Solutions:**
1. **Check role assignment**: Ensure service principal has User Administrator role
2. **Verify admin consent**: Confirm API permissions have admin consent granted
3. **Check permission scope**: Verify permissions are Application-type, not Delegated

**Verification Commands:**
```bash
# Check service principal roles
az rest --method GET \
  --url https://graph.microsoft.com/v1.0/servicePrincipals/{service-principal-id}/appRoleAssignments
```

### 9.2 Configuration Errors

#### Error: "Configuration error: Missing required Azure credentials"

**Symptoms:**
```
[red]Configuration error: Missing required Azure credentials: AZURE_TENANT_ID, AZURE_CLIENT_ID[/red]
```

**Solutions:**
1. **Check .env file**: Ensure file exists and has correct variable names
2. **Verify file location**: `.env` file should be in the working directory
3. **Check environment variables**: Verify variables are set in the shell

**Verification Commands:**
```bash
# Check if .env file exists and has correct format
cat .env

# Verify environment variables are loaded
echo $AZURE_TENANT_ID
echo $AZURE_CLIENT_ID
```

#### Error: "Invalid GUID format"

**Symptoms:**
```
[red]Azure IDs must be valid GUIDs in format: xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx[/red]
```

**Solutions:**
1. **Check GUID format**: Ensure all Azure IDs follow the pattern `xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx`
2. **Remove extra characters**: No spaces, quotes, or special characters
3. **Verify source**: Copy IDs directly from Azure Portal

### 9.3 Network and Connectivity Issues

#### Error: "Connection timeout"

**Symptoms:**
```
[red]Error executing simulation plan: HTTPSConnectionPool timeout[/red]
```

**Solutions:**
1. **Check internet connection**: Verify connectivity to `graph.microsoft.com`
2. **Firewall settings**: Ensure outbound HTTPS (443) is allowed
3. **Proxy configuration**: Configure proxy settings if required

**Verification Commands:**
```bash
# Test connectivity
curl -I https://graph.microsoft.com/v1.0/

# Test with proxy (if needed)
curl -I https://graph.microsoft.com/v1.0/ --proxy your-proxy:port
```

### 9.4 Resource Creation Failures

#### Error: "Failed to create user: Domain not verified"

**Symptoms:**
```
[red]Failed to create user 'user1@contoso.com': Domain 'contoso.com' is not verified[/red]
```

**Solutions:**
1. **Use verified domain**: Change domain in company description to your verified domain
2. **Add domain verification**: Add and verify the domain in Azure AD
3. **Use default domain**: Use `{tenant}.onmicrosoft.com` format

#### Error: "Group already exists"

**Symptoms:**
```
[red]Failed to create group 'Engineering': Group already exists[/red]
```

**Solutions:**
1. **Use cleanup command**: Run cleanup to remove existing resources
2. **Manual cleanup**: Delete conflicting groups in Azure Portal
3. **Modify group names**: Edit company description to use different group names

### 9.5 Rate Limiting Issues

#### Error: "Too many requests"

**Symptoms:**
```
[red]Failed to create user: TooManyRequests - Rate limit exceeded[/red]
```

**Solutions:**
1. **Wait and retry**: EntraSim has built-in retry logic with exponential backoff
2. **Reduce concurrency**: Modify company description to create fewer resources
3. **Check tenant limits**: Verify tenant is not hitting service limits

**Mitigation:**
The tool automatically implements retry logic, but for large simulations:
```bash
# Enable verbose logging to monitor retries
entrasim create sample_company.json --verbose
```

### 9.6 Common Resolution Steps

1. **Check logs first**:
   ```bash
   tail -50 entrasim.log
   ```

2. **Validate configuration**:
   ```bash
   entrasim validate sample_company.json
   ```

3. **Test with minimal config**:
   Create a minimal company description with 1-2 users to test connectivity

4. **Verify Azure setup**:
   ```bash
   # Test service principal authentication
   az login --service-principal \
     --username $AZURE_CLIENT_ID \
     --password $AZURE_CLIENT_SECRET \
     --tenant $AZURE_TENANT_ID
   ```

5. **Check Azure service health**:
   Visit [Azure Status](https://status.azure.com/) for service outages

---

## 10. Security Considerations

### 10.1 Credential Management

#### Best Practices

1. **Use .env files**: Never hardcode credentials in scripts or code
2. **Restrict file permissions**: Set `.env` file permissions to 600
   ```bash
   chmod 600 .env
   ```
3. **Rotate secrets regularly**: Set calendar reminders to rotate client secrets
4. **Use Azure Key Vault**: For production deployments, consider Azure Key Vault integration

#### Secret Rotation

Set up automated secret rotation:

```bash
# Create new secret
NEW_SECRET=$(az ad app credential reset --id $AZURE_CLIENT_ID --append --query password --output tsv)

# Update .env file
sed -i "s/AZURE_CLIENT_SECRET=.*/AZURE_CLIENT_SECRET=$NEW_SECRET/" .env

# Test with new secret
entrasim validate sample_company.json
```

### 10.2 Production vs Testing Environments

#### Development Environment
- Use dedicated development Azure tenant
- Implement resource quotas and spending limits
- Regular cleanup schedules

#### Testing Environment
- Isolated from production resources
- Automated cleanup after test completion
- Monitoring and alerting for unexpected resource creation

#### Production Considerations
- **Never use in production tenants**: EntraSim is designed for simulation and testing only
- **Implement approval workflows**: For any production-like environments
- **Audit and compliance**: Ensure simulations comply with organizational policies

### 10.3 Resource Management

#### Cost Control
```bash
# Set up Azure Budget alerts
az consumption budget create \
  --budget-name "EntraSim-Budget" \
  --amount 100 \
  --category cost \
  --time-grain monthly
```

#### Resource Monitoring
```bash
# Monitor created resources
az resource list --tag createdBy=EntraSim --output table

# Set up automatic cleanup (example cron job)
# 0 2 * * 0 /path/to/cleanup-script.sh
```

#### Cleanup Automation
Create automated cleanup scripts:

```bash
#!/bin/bash
# cleanup-entrasim.sh

echo "Starting EntraSim cleanup..."
cd /path/to/entrasim

# Cleanup all known simulations
for company_file in companies/*.json; do
    if [ -f "$company_file" ]; then
        echo "Cleaning up $company_file"
        entrasim cleanup "$company_file" --force
    fi
done

echo "Cleanup completed"
```

### 10.4 Compliance and Auditing

#### Audit Logging
All EntraSim operations are logged to `entrasim.log`:

```bash
# Monitor operations
tail -f entrasim.log | grep -E "(Created|Deleted|ERROR)"

# Export audit logs
grep "Created\|Deleted" entrasim.log > audit-$(date +%Y%m%d).log
```

#### Compliance Checks
- Ensure simulations don't violate data residency requirements
- Verify user data doesn't contain real personal information
- Document all simulations for compliance audits

#### Data Protection
- Use synthetic data only
- No real email addresses or personal information
- Implement data retention policies

---

## Company Description File Format

### JSON Structure

The company description file defines the organizational structure for simulation. Here's the complete schema:

```json
{
  "name": "Company Name",
  "domain": "company.com",
  "industry": "Technology|Healthcare|Finance|Manufacturing|Retail|Other",
  "size": "small|medium|large|enterprise",
  "description": "Brief company description",
  "complexity": "simple|medium|complex",
  "departments": [
    "Engineering",
    "Sales",
    "Marketing"
  ],
  "roles": [
    {
      "name": "Software Engineer",
      "department": "Engineering",
      "count": 10,
      "seniority_level": "junior|mid|senior|lead",
      "permissions": ["permission1", "permission2"]
    }
  ]
}
```

### Field Descriptions

- **name**: Company name for the simulation
- **domain**: Domain name (must be verified in your Azure tenant or use `.onmicrosoft.com`)
- **industry**: Industry classification
- **size**: Organization size affecting default role distributions
- **description**: Optional company description
- **complexity**: Affects the depth of role hierarchies and permissions
- **departments**: List of organizational departments
- **roles**: Array of role definitions with user counts and properties

### Example Modifications

Create custom company configurations by modifying [`sample_company.json`](sample_company.json):

1. **Small Startup** (10 users):
```json
{
  "name": "Startup Inc",
  "domain": "startup.onmicrosoft.com",
  "industry": "Technology",
  "size": "small",
  "roles": [
    {"name": "Founder", "department": "Leadership", "count": 2, "seniority_level": "lead"},
    {"name": "Developer", "department": "Engineering", "count": 4, "seniority_level": "mid"},
    {"name": "Sales Rep", "department": "Sales", "count": 2, "seniority_level": "junior"},
    {"name": "Designer", "department": "Design", "count": 2, "seniority_level": "mid"}
  ]
}
```

2. **Large Enterprise** (500+ users):
```json
{
  "name": "Enterprise Corp",
  "domain": "enterprise.com",
  "industry": "Finance",
  "size": "enterprise",
  "complexity": "complex",
  "roles": [
    {"name": "Software Engineer", "department": "IT", "count": 50, "seniority_level": "mid"},
    {"name": "Manager", "department": "IT", "count": 10, "seniority_level": "senior"},
    {"name": "Analyst", "department": "Finance", "count": 30, "seniority_level": "mid"},
    {"name": "Sales Rep", "department": "Sales", "count": 100, "seniority_level": "junior"}
  ]
}
```

---

## Advanced Usage

### Custom Environment Configurations

For different environments, create separate configuration files:

```bash
# Development environment
entrasim create company.json --env-file dev.env

# Testing environment  
entrasim create company.json --env-file test.env

# Production testing (use with extreme caution)
entrasim create company.json --env-file prod.env
```

### Batch Operations

Process multiple company configurations:

```bash
#!/bin/bash
# batch-simulate.sh

for company in companies/*.json; do
    echo "Processing $company..."
    entrasim create "$company" --force
    sleep 30  # Rate limiting
done
```

### Integration with CI/CD

Example GitHub Actions workflow:

```yaml
name: EntraSim Test
on: [push]
jobs:
  test-simulation:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - name: Install EntraSim
        run: pip install -e .
      - name: Validate configurations
        run: |
          entrasim validate sample_company.json
          entrasim validate test_company.json
      - name: Test creation (dry run)
        env:
          AZURE_TENANT_ID: ${{ secrets.AZURE_TENANT_ID }}
          AZURE_CLIENT_ID: ${{ secrets.AZURE_CLIENT_ID }}
          AZURE_CLIENT_SECRET: ${{ secrets.AZURE_CLIENT_SECRET }}
          AZURE_SUBSCRIPTION_ID: ${{ secrets.AZURE_SUBSCRIPTION_ID }}
        run: |
          entrasim create sample_company.json --force
          entrasim cleanup sample_company.json --force
```

---

## Conclusion

This comprehensive guide covers all aspects of using EntraSim to create realistic Azure AD/Entra ID tenant simulations. The tool provides a safe, controlled way to generate test environments for security research, training, and development purposes.

### Key Takeaways

1. **Always test in development environments** before any production-like usage
2. **Properly configure Azure permissions** to ensure smooth operation
3. **Use the cleanup functionality** to maintain resource hygiene
4. **Monitor costs and resource usage** to prevent unexpected charges
5. **Follow security best practices** for credential management

### Next Steps

- Start with the sample company configuration
- Modify the company description to match your specific needs
- Implement regular cleanup schedules
- Consider automation for recurring simulation needs
- Share feedback and contribute to the project's improvement

### Support Resources

- **Log Files**: Check `entrasim.log` for detailed operation logs
- **Validation**: Use `entrasim validate` to test configurations
- **Verbose Mode**: Add `--verbose` flag for detailed output
- **Azure Status**: Monitor [Azure Status](https://status.azure.com/) for service issues

For additional support, consult the troubleshooting section or check the project's issue tracker for known problems and solutions.