"""Data models for EntraSim."""

from typing import List, Optional
from pydantic import BaseModel, Field


class RoleDefinition(BaseModel):
    """Represents a role definition in the simulated company."""
    
    name: str = Field(description="Name of the role (e.g., 'Software Engineer', 'Manager')")
    department: str = Field(description="Department the role belongs to")
    count: int = Field(description="Number of users to create for this role", ge=1)
    permissions: Optional[List[str]] = Field(
        default_factory=list,
        description="List of permissions or groups this role should belong to"
    )
    seniority_level: Optional[str] = Field(
        default="junior",
        description="Seniority level (junior, mid, senior, lead)"
    )


class CompanyDescription(BaseModel):
    """Represents the simulated company description and structure."""
    
    name: str = Field(description="Name of the simulated company")
    domain: str = Field(description="Domain name for the company (e.g., 'contoso.com')")
    industry: str = Field(description="Industry the company operates in")
    size: str = Field(description="Company size (small, medium, large, enterprise)")
    description: Optional[str] = Field(
        default="",
        description="Brief description of the company"
    )
    roles: List[RoleDefinition] = Field(
        description="List of roles to create in the organization"
    )
    departments: Optional[List[str]] = Field(
        default_factory=list,
        description="List of departments in the organization"
    )
    complexity: Optional[str] = Field(
        default="medium",
        description="Complexity level for the simulation (simple, medium, complex)"
    )
    
    def get_total_users(self) -> int:
        """Calculate the total number of users to be created."""
        return sum(role.count for role in self.roles)
    
    def get_departments(self) -> List[str]:
        """Get all unique departments from roles and explicit departments list."""
        role_departments = {role.department for role in self.roles}
        all_departments = set(self.departments or []) | role_departments
        return sorted(list(all_departments))


class SimulationPlan(BaseModel):
    """Represents the plan for creating Azure resources."""
    
    company: CompanyDescription
    tenant_id: str
    subscription_id: str
    total_users: int
    total_groups: int
    groups_to_create: List[str] = Field(description="List of group names to create")
    users_to_create: List[dict] = Field(description="List of user details to create")
    
    @classmethod
    def from_company_description(
        cls,
        company: CompanyDescription,
        tenant_id: str,
        subscription_id: str
    ) -> "SimulationPlan":
        """Create a simulation plan from a company description."""
        groups = company.get_departments()
        
        # Add role-based groups
        role_groups = [f"{role.name.replace(' ', '_').lower()}_group" for role in company.roles]
        groups.extend(role_groups)
        
        users = []
        user_counter = 1
        
        for role in company.roles:
            for i in range(role.count):
                user = {
                    "display_name": f"{role.name} {user_counter}",
                    "user_principal_name": f"user{user_counter}@{company.domain}",
                    "role": role.name,
                    "department": role.department,
                    "seniority": role.seniority_level,
                    "groups": [role.department, f"{role.name.replace(' ', '_').lower()}_group"]
                }
                users.append(user)
                user_counter += 1
        
        return cls(
            company=company,
            tenant_id=tenant_id,
            subscription_id=subscription_id,
            total_users=len(users),
            total_groups=len(groups),
            groups_to_create=groups,
            users_to_create=users
        )