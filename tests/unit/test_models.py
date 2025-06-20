"""Unit tests for Pydantic models."""

import pytest
from pydantic import ValidationError

from entrasim.models import RoleDefinition, CompanyDescription, SimulationPlan


class TestRoleDefinition:
    """Test the RoleDefinition model."""
    
    @pytest.mark.unit
    def test_valid_role_definition(self):
        """Test creating a valid role definition."""
        role = RoleDefinition(
            name="Software Engineer",
            department="Engineering",
            count=5,
            permissions=["developers", "code_access"],
            seniority_level="mid"
        )
        
        assert role.name == "Software Engineer"
        assert role.department == "Engineering"
        assert role.count == 5
        assert role.permissions == ["developers", "code_access"]
        assert role.seniority_level == "mid"
    
    @pytest.mark.unit
    def test_role_definition_defaults(self):
        """Test role definition with default values."""
        role = RoleDefinition(
            name="Developer",
            department="IT",
            count=1
        )
        
        assert role.permissions == []
        assert role.seniority_level == "junior"
    
    @pytest.mark.unit
    def test_role_definition_invalid_count(self):
        """Test role definition with invalid count."""
        with pytest.raises(ValidationError, match="greater than or equal to 1"):
            RoleDefinition(
                name="Developer",
                department="IT",
                count=0
            )
    
    @pytest.mark.unit
    def test_role_definition_negative_count(self):
        """Test role definition with negative count."""
        with pytest.raises(ValidationError, match="greater than or equal to 1"):
            RoleDefinition(
                name="Developer",
                department="IT",
                count=-1
            )
    
    @pytest.mark.unit
    def test_role_definition_missing_required_fields(self):
        """Test role definition with missing required fields."""
        with pytest.raises(ValidationError):
            RoleDefinition(count=1)  # Missing name and department


class TestCompanyDescription:
    """Test the CompanyDescription model."""
    
    @pytest.mark.unit
    def test_valid_company_description(self, sample_company_data):
        """Test creating a valid company description."""
        company = CompanyDescription(**sample_company_data)
        
        assert company.name == "Test Corporation"
        assert company.domain == "test.com"
        assert company.industry == "Technology"
        assert company.size == "medium"
        assert company.description == "A test company for unit testing"
        assert company.complexity == "medium"
        assert len(company.roles) == 2
        assert len(company.departments) == 2
    
    @pytest.mark.unit
    def test_company_description_defaults(self):
        """Test company description with default values."""
        company = CompanyDescription(
            name="Test Company",
            domain="test.com",
            industry="Technology",
            size="small",
            roles=[
                RoleDefinition(name="Developer", department="IT", count=1)
            ]
        )
        
        assert company.description == ""
        assert company.departments == []
        assert company.complexity == "medium"
    
    @pytest.mark.unit
    def test_get_total_users(self, sample_company_data):
        """Test calculating total users."""
        company = CompanyDescription(**sample_company_data)
        assert company.get_total_users() == 3  # 2 + 1 from roles
    
    @pytest.mark.unit
    def test_get_departments(self, sample_company_data):
        """Test getting all departments."""
        company = CompanyDescription(**sample_company_data)
        departments = company.get_departments()
        
        assert "Engineering" in departments
        assert "Sales" in departments
        assert len(departments) == 2
        assert departments == sorted(departments)  # Should be sorted
    
    @pytest.mark.unit
    def test_get_departments_with_role_departments(self):
        """Test getting departments includes departments from roles."""
        company = CompanyDescription(
            name="Test Company",
            domain="test.com",
            industry="Technology",
            size="small",
            departments=["HR"],
            roles=[
                RoleDefinition(name="Developer", department="Engineering", count=1),
                RoleDefinition(name="Analyst", department="Finance", count=1)
            ]
        )
        
        departments = company.get_departments()
        assert "HR" in departments
        assert "Engineering" in departments
        assert "Finance" in departments
        assert len(departments) == 3
    
    @pytest.mark.unit
    def test_company_description_missing_required_fields(self):
        """Test company description with missing required fields."""
        with pytest.raises(ValidationError):
            CompanyDescription(name="Test")  # Missing other required fields
    
    @pytest.mark.unit
    def test_empty_roles_list(self):
        """Test company description with empty roles list."""
        company = CompanyDescription(
            name="Test Company",
            domain="test.com",
            industry="Technology",
            size="small",
            roles=[]
        )
        
        assert company.get_total_users() == 0
        assert company.get_departments() == []


class TestSimulationPlan:
    """Test the SimulationPlan model."""
    
    @pytest.mark.unit
    def test_valid_simulation_plan(self, company_description, mock_config):
        """Test creating a valid simulation plan."""
        plan = SimulationPlan(
            company=company_description,
            tenant_id=mock_config.azure_tenant_id,
            subscription_id=mock_config.azure_subscription_id,
            total_users=3,
            total_groups=4,
            groups_to_create=["Engineering", "Sales", "software_engineer_group", "sales_representative_group"],
            users_to_create=[
                {
                    "display_name": "Software Engineer 1",
                    "user_principal_name": "user1@test.com",
                    "role": "Software Engineer",
                    "department": "Engineering",
                    "seniority": "mid",
                    "groups": ["Engineering", "software_engineer_group"]
                }
            ]
        )
        
        assert plan.company == company_description
        assert plan.tenant_id == mock_config.azure_tenant_id
        assert plan.subscription_id == mock_config.azure_subscription_id
        assert plan.total_users == 3
        assert plan.total_groups == 4
        assert len(plan.groups_to_create) == 4
        assert len(plan.users_to_create) == 1
    
    @pytest.mark.unit
    def test_simulation_plan_from_company_description(self, company_description, mock_config):
        """Test creating simulation plan from company description."""
        plan = SimulationPlan.from_company_description(
            company=company_description,
            tenant_id=mock_config.azure_tenant_id,
            subscription_id=mock_config.azure_subscription_id
        )
        
        assert plan.company == company_description
        assert plan.tenant_id == mock_config.azure_tenant_id
        assert plan.subscription_id == mock_config.azure_subscription_id
        assert plan.total_users == company_description.get_total_users()
        assert plan.total_groups > 0
        
        # Check that department groups are included
        assert "Engineering" in plan.groups_to_create
        assert "Sales" in plan.groups_to_create
        
        # Check that role-based groups are included
        assert "software_engineer_group" in plan.groups_to_create
        assert "sales_representative_group" in plan.groups_to_create
        
        # Check user creation structure
        assert len(plan.users_to_create) == plan.total_users
        
        for user in plan.users_to_create:
            assert "display_name" in user
            assert "user_principal_name" in user
            assert "role" in user
            assert "department" in user
            assert "seniority" in user
            assert "groups" in user
            assert isinstance(user["groups"], list)
            assert len(user["groups"]) >= 1  # At least department group
    
    @pytest.mark.unit
    def test_simulation_plan_user_naming(self, company_description, mock_config):
        """Test user naming in simulation plan."""
        plan = SimulationPlan.from_company_description(
            company=company_description,
            tenant_id=mock_config.azure_tenant_id,
            subscription_id=mock_config.azure_subscription_id
        )
        
        # Check user naming pattern
        user_names = [user["display_name"] for user in plan.users_to_create]
        upns = [user["user_principal_name"] for user in plan.users_to_create]
        
        # Should have numbered users
        assert "Software Engineer 1" in user_names
        assert "Software Engineer 2" in user_names
        assert "Sales Representative 3" in user_names
        
        # UPNs should follow pattern
        assert "user1@test.com" in upns
        assert "user2@test.com" in upns
        assert "user3@test.com" in upns
    
    @pytest.mark.unit
    def test_simulation_plan_group_assignments(self, company_description, mock_config):
        """Test group assignments in simulation plan."""
        plan = SimulationPlan.from_company_description(
            company=company_description,
            tenant_id=mock_config.azure_tenant_id,
            subscription_id=mock_config.azure_subscription_id
        )
        
        # Find a software engineer user
        engineer_user = next(
            user for user in plan.users_to_create 
            if user["role"] == "Software Engineer"
        )
        
        # Should be in both department and role groups
        assert "Engineering" in engineer_user["groups"]
        assert "software_engineer_group" in engineer_user["groups"]
        
        # Find sales representative user
        sales_user = next(
            user for user in plan.users_to_create 
            if user["role"] == "Sales Representative"
        )
        
        assert "Sales" in sales_user["groups"]
        assert "sales_representative_group" in sales_user["groups"]
    
    @pytest.mark.unit
    def test_simulation_plan_with_minimal_company(self, minimal_company_data, mock_config):
        """Test simulation plan with minimal company data."""
        company = CompanyDescription(**minimal_company_data)
        plan = SimulationPlan.from_company_description(
            company=company,
            tenant_id=mock_config.azure_tenant_id,
            subscription_id=mock_config.azure_subscription_id
        )
        
        assert plan.total_users == 1
        assert plan.total_groups == 2  # IT department + developer_group
        assert "IT" in plan.groups_to_create
        assert "developer_group" in plan.groups_to_create
        
        user = plan.users_to_create[0]
        assert user["display_name"] == "Developer 1"
        assert user["user_principal_name"] == "user1@minimal.com"
        assert user["role"] == "Developer"
        assert user["department"] == "IT"
        assert "IT" in user["groups"]
        assert "developer_group" in user["groups"]
    
    @pytest.mark.unit
    def test_simulation_plan_role_group_naming(self):
        """Test role group naming convention."""
        company = CompanyDescription(
            name="Test Company",
            domain="test.com",
            industry="Technology",
            size="small",
            roles=[
                RoleDefinition(name="Senior Software Engineer", department="Engineering", count=1),
                RoleDefinition(name="Product Manager", department="Product", count=1),
                RoleDefinition(name="UX Designer", department="Design", count=1)
            ]
        )
        
        plan = SimulationPlan.from_company_description(
            company=company,
            tenant_id="12345678-1234-1234-1234-123456789abc",
            subscription_id="11111111-2222-3333-4444-555555555555"
        )
        
        # Check role group naming (spaces replaced with underscores, lowercase)
        assert "senior_software_engineer_group" in plan.groups_to_create
        assert "product_manager_group" in plan.groups_to_create
        assert "ux_designer_group" in plan.groups_to_create


class TestModelValidation:
    """Test model validation edge cases."""
    
    @pytest.mark.unit
    def test_role_definition_with_special_characters(self):
        """Test role definition with special characters in name."""
        role = RoleDefinition(
            name="C# Developer",
            department="Engineering",
            count=1
        )
        assert role.name == "C# Developer"
    
    @pytest.mark.unit
    def test_company_description_unicode_characters(self):
        """Test company description with unicode characters."""
        company = CompanyDescription(
            name="Tëst Cörporation",
            domain="test.com",
            industry="Technology",
            size="small",
            description="A company with ünicode charactërs",
            roles=[
                RoleDefinition(name="Développeur", department="Ingénierie", count=1)
            ]
        )
        
        assert company.name == "Tëst Cörporation"
        assert company.description == "A company with ünicode charactërs"
        assert company.roles[0].name == "Développeur"
        assert company.roles[0].department == "Ingénierie"
    
    @pytest.mark.unit
    def test_simulation_plan_large_numbers(self):
        """Test simulation plan with large numbers of users."""
        roles = [
            RoleDefinition(name="Developer", department="Engineering", count=1000),
            RoleDefinition(name="Tester", department="QA", count=500)
        ]
        
        company = CompanyDescription(
            name="Large Company",
            domain="large.com",
            industry="Technology",
            size="enterprise",
            roles=roles
        )
        
        plan = SimulationPlan.from_company_description(
            company=company,
            tenant_id="12345678-1234-1234-1234-123456789abc",
            subscription_id="11111111-2222-3333-4444-555555555555"
        )
        
        assert plan.total_users == 1500
        assert len(plan.users_to_create) == 1500
        
        # Check that user numbering works correctly for large numbers
        last_user = plan.users_to_create[-1]
        assert "1500" in last_user["user_principal_name"]