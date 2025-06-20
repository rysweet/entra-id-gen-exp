"""Unit tests for CLI interface."""

import pytest
import sys
import argparse
from unittest.mock import Mock, patch, call
from pathlib import Path

from entrasim.cli import (
    create_parser, 
    display_banner,
    confirm_operation,
    validate_azure_credentials,
    handle_create_command,
    handle_validate_command,
    handle_cleanup_command,
    main
)
from tests.utils import create_cli_args_mock, MockConsole


class TestCLIParser:
    """Test CLI argument parser."""
    
    @pytest.mark.unit
    def test_create_parser(self):
        """Test parser creation and structure."""
        parser = create_parser()
        assert isinstance(parser, argparse.ArgumentParser)
        assert parser.prog == "entrasim"
    
    @pytest.mark.unit
    def test_parser_create_command(self):
        """Test create command parsing."""
        parser = create_parser()
        args = parser.parse_args(['create', 'test.json'])
        
        assert args.command == 'create'
        assert args.input_file == 'test.json'
        assert args.force is False
        assert args.env_file is None
    
    @pytest.mark.unit
    def test_parser_create_command_with_options(self):
        """Test create command with all options."""
        parser = create_parser()
        args = parser.parse_args([
            'create', 'test.json', 
            '--force', 
            '--env-file', 'custom.env'
        ])
        
        assert args.command == 'create'
        assert args.input_file == 'test.json'
        assert args.force is True
        assert args.env_file == 'custom.env'
    
    @pytest.mark.unit
    def test_parser_validate_command(self):
        """Test validate command parsing."""
        parser = create_parser()
        args = parser.parse_args(['validate', 'test.json'])
        
        assert args.command == 'validate'
        assert args.input_file == 'test.json'
    
    @pytest.mark.unit
    def test_parser_cleanup_command(self):
        """Test cleanup command parsing."""
        parser = create_parser()
        args = parser.parse_args(['cleanup', 'test.json', '--force'])
        
        assert args.command == 'cleanup'
        assert args.input_file == 'test.json'
        assert args.force is True
    
    @pytest.mark.unit
    def test_parser_global_options(self):
        """Test global options parsing."""
        parser = create_parser()
        args = parser.parse_args(['--verbose', 'create', 'test.json'])
        
        assert args.verbose is True
        assert args.command == 'create'
    
    @pytest.mark.unit
    def test_parser_version(self):
        """Test version option."""
        parser = create_parser()
        
        with pytest.raises(SystemExit):
            parser.parse_args(['--version'])


class TestCLIUtilityFunctions:
    """Test CLI utility functions."""
    
    @pytest.mark.unit
    def test_display_banner(self):
        """Test banner display."""
        with patch('entrasim.cli.console') as mock_console:
            display_banner()
            mock_console.print.assert_called_once()
    
    @pytest.mark.unit
    def test_confirm_operation_force_mode(self):
        """Test operation confirmation in force mode."""
        with patch('entrasim.cli.console') as mock_console:
            result = confirm_operation("Test Operation", "Test details", force=True)
            assert result is True
            mock_console.print.assert_called()
    
    @pytest.mark.unit
    def test_confirm_operation_user_confirms(self):
        """Test operation confirmation when user confirms."""
        with patch('entrasim.cli.console') as mock_console:
            mock_console.input.return_value = "yes"
            result = confirm_operation("Test Operation", "Test details", force=False)
            assert result is True
    
    @pytest.mark.unit
    def test_confirm_operation_user_rejects(self):
        """Test operation confirmation when user rejects."""
        with patch('entrasim.cli.console') as mock_console:
            mock_console.input.return_value = "no"
            result = confirm_operation("Test Operation", "Test details", force=False)
            assert result is False
    
    @pytest.mark.unit
    def test_confirm_operation_case_insensitive(self):
        """Test operation confirmation is case insensitive."""
        with patch('entrasim.cli.console') as mock_console:
            mock_console.input.return_value = "YES"
            result = confirm_operation("Test Operation", "Test details", force=False)
            assert result is True
    
    @pytest.mark.unit
    def test_validate_azure_credentials_success(self, mock_config, mock_azure_client):
        """Test successful Azure credential validation."""
        with patch('entrasim.cli.create_azure_client', return_value=mock_azure_client), \
             patch('entrasim.cli.console'):
            result = validate_azure_credentials(mock_config)
            assert result is True
    
    @pytest.mark.unit
    def test_validate_azure_credentials_failure(self, mock_config):
        """Test failed Azure credential validation."""
        mock_client = Mock()
        mock_client.authenticate.return_value = False
        
        with patch('entrasim.cli.create_azure_client', return_value=mock_client), \
             patch('entrasim.cli.console'):
            result = validate_azure_credentials(mock_config)
            assert result is False
    
    @pytest.mark.unit
    def test_validate_azure_credentials_exception(self, mock_config):
        """Test Azure credential validation with exception."""
        mock_config.validate_required_credentials.side_effect = Exception("Validation error")
        
        with patch('entrasim.cli.console'):
            result = validate_azure_credentials(mock_config)
            assert result is False


class TestCLICommandHandlers:
    """Test CLI command handlers."""
    
    @pytest.mark.unit
    def test_handle_create_command_success(self, mock_config, sample_company_file):
        """Test successful create command handling."""
        args = create_cli_args_mock('create', str(sample_company_file), force=True)
        
        mock_core = Mock()
        mock_core.validate_input.return_value = True
        mock_core.parse_company_description.return_value = Mock(name="Test Company", domain="test.com")
        mock_core.generate_simulation_plan.return_value = Mock(
            total_users=3, total_groups=2, 
            company=Mock(name="Test Company", domain="test.com")
        )
        mock_core.execute_simulation_plan.return_value = True
        
        with patch('entrasim.cli.EntraSimCore', return_value=mock_core), \
             patch('entrasim.cli.validate_azure_credentials', return_value=True), \
             patch('entrasim.cli.console'):
            result = handle_create_command(args, mock_config)
            assert result is True
    
    @pytest.mark.unit
    def test_handle_create_command_validation_failure(self, mock_config, sample_company_file):
        """Test create command with validation failure."""
        args = create_cli_args_mock('create', str(sample_company_file))
        
        mock_core = Mock()
        mock_core.validate_input.return_value = False
        
        with patch('entrasim.cli.EntraSimCore', return_value=mock_core), \
             patch('entrasim.cli.console'):
            result = handle_create_command(args, mock_config)
            assert result is False
    
    @pytest.mark.unit
    def test_handle_create_command_user_cancels(self, mock_config, sample_company_file):
        """Test create command when user cancels."""
        args = create_cli_args_mock('create', str(sample_company_file), force=False)
        
        mock_core = Mock()
        mock_core.validate_input.return_value = True
        mock_core.parse_company_description.return_value = Mock(name="Test Company", domain="test.com")
        mock_core.generate_simulation_plan.return_value = Mock(
            total_users=3, total_groups=2,
            company=Mock(name="Test Company", domain="test.com")
        )
        
        with patch('entrasim.cli.EntraSimCore', return_value=mock_core), \
             patch('entrasim.cli.confirm_operation', return_value=False), \
             patch('entrasim.cli.console'):
            result = handle_create_command(args, mock_config)
            assert result is False
    
    @pytest.mark.unit
    def test_handle_create_command_azure_auth_failure(self, mock_config, sample_company_file):
        """Test create command with Azure authentication failure."""
        args = create_cli_args_mock('create', str(sample_company_file), force=True)
        
        mock_core = Mock()
        mock_core.validate_input.return_value = True
        mock_core.parse_company_description.return_value = Mock(name="Test Company", domain="test.com")
        mock_core.generate_simulation_plan.return_value = Mock(
            total_users=3, total_groups=2,
            company=Mock(name="Test Company", domain="test.com")
        )
        
        with patch('entrasim.cli.EntraSimCore', return_value=mock_core), \
             patch('entrasim.cli.validate_azure_credentials', return_value=False), \
             patch('entrasim.cli.console'):
            result = handle_create_command(args, mock_config)
            assert result is False
    
    @pytest.mark.unit
    def test_handle_create_command_exception(self, mock_config):
        """Test create command with exception."""
        args = create_cli_args_mock('create', 'nonexistent.json')
        
        with patch('entrasim.cli.console'):
            result = handle_create_command(args, mock_config)
            assert result is False
    
    @pytest.mark.unit
    def test_handle_validate_command_success(self, sample_company_file):
        """Test successful validate command handling."""
        args = create_cli_args_mock('validate', str(sample_company_file))
        
        with patch('entrasim.cli.validate_input_file', return_value=True), \
             patch('entrasim.cli.console'):
            result = handle_validate_command(args)
            assert result is True
    
    @pytest.mark.unit
    def test_handle_validate_command_failure(self):
        """Test validate command failure."""
        args = create_cli_args_mock('validate', 'invalid.json')
        
        with patch('entrasim.cli.validate_input_file', return_value=False), \
             patch('entrasim.cli.console'):
            result = handle_validate_command(args)
            assert result is False
    
    @pytest.mark.unit
    def test_handle_validate_command_exception(self):
        """Test validate command with exception."""
        args = create_cli_args_mock('validate', 'invalid.json')
        
        with patch('entrasim.cli.validate_input_file', side_effect=Exception("Test error")), \
             patch('entrasim.cli.console'):
            result = handle_validate_command(args)
            assert result is False
    
    @pytest.mark.unit
    def test_handle_cleanup_command_success(self, mock_config, sample_company_file):
        """Test successful cleanup command handling."""
        args = create_cli_args_mock('cleanup', str(sample_company_file), force=True)
        
        mock_core = Mock()
        mock_core.validate_input.return_value = True
        mock_core.parse_company_description.return_value = Mock(name="Test Company", domain="test.com")
        mock_core.generate_simulation_plan.return_value = Mock(
            total_users=3, total_groups=2,
            company=Mock(name="Test Company", domain="test.com")
        )
        mock_core.cleanup_simulation.return_value = True
        
        with patch('entrasim.cli.EntraSimCore', return_value=mock_core), \
             patch('entrasim.cli.validate_azure_credentials', return_value=True), \
             patch('entrasim.cli.console'):
            result = handle_cleanup_command(args, mock_config)
            assert result is True
    
    @pytest.mark.unit
    def test_handle_cleanup_command_user_cancels(self, mock_config, sample_company_file):
        """Test cleanup command when user cancels."""
        args = create_cli_args_mock('cleanup', str(sample_company_file), force=False)
        
        mock_core = Mock()
        mock_core.validate_input.return_value = True
        mock_core.parse_company_description.return_value = Mock(name="Test Company", domain="test.com")
        mock_core.generate_simulation_plan.return_value = Mock(
            total_users=3, total_groups=2,
            company=Mock(name="Test Company", domain="test.com")
        )
        
        with patch('entrasim.cli.EntraSimCore', return_value=mock_core), \
             patch('entrasim.cli.confirm_operation', return_value=False), \
             patch('entrasim.cli.console'):
            result = handle_cleanup_command(args, mock_config)
            assert result is False


class TestMainFunction:
    """Test the main CLI function."""
    
    @pytest.mark.unit
    def test_main_no_arguments(self):
        """Test main function with no arguments shows help."""
        with patch('sys.argv', ['entrasim']), \
             patch('entrasim.cli.display_banner'), \
             patch('entrasim.cli.create_parser') as mock_parser:
            
            mock_parser_instance = Mock()
            mock_parser.return_value = mock_parser_instance
            
            main()
            mock_parser_instance.print_help.assert_called_once()
    
    @pytest.mark.unit
    def test_main_create_command_success(self, mock_env_vars):
        """Test main function with successful create command."""
        test_args = ['entrasim', 'create', 'test.json', '--force']
        
        with patch('sys.argv', test_args), \
             patch('entrasim.cli.handle_create_command', return_value=True), \
             patch('entrasim.cli.display_banner'), \
             patch('entrasim.cli.get_config') as mock_get_config, \
             patch('entrasim.cli.setup_logging'), \
             patch('sys.exit') as mock_exit:
            
            mock_get_config.return_value = Mock()
            main()
            mock_exit.assert_called_once_with(0)
    
    @pytest.mark.unit
    def test_main_validate_command_success(self):
        """Test main function with successful validate command."""
        test_args = ['entrasim', 'validate', 'test.json']
        
        with patch('sys.argv', test_args), \
             patch('entrasim.cli.handle_validate_command', return_value=True), \
             patch('entrasim.cli.display_banner'), \
             patch('entrasim.cli.setup_logging'), \
             patch('sys.exit') as mock_exit:
            
            main()
            mock_exit.assert_called_once_with(0)
    
    @pytest.mark.unit
    def test_main_command_failure(self, mock_env_vars):
        """Test main function with command failure."""
        test_args = ['entrasim', 'create', 'test.json']
        
        with patch('sys.argv', test_args), \
             patch('entrasim.cli.handle_create_command', return_value=False), \
             patch('entrasim.cli.display_banner'), \
             patch('entrasim.cli.get_config') as mock_get_config, \
             patch('entrasim.cli.setup_logging'), \
             patch('sys.exit') as mock_exit:
            
            mock_get_config.return_value = Mock()
            main()
            mock_exit.assert_called_once_with(1)
    
    @pytest.mark.unit
    def test_main_config_error(self):
        """Test main function with configuration error."""
        test_args = ['entrasim', 'create', 'test.json']
        
        with patch('sys.argv', test_args), \
             patch('entrasim.cli.display_banner'), \
             patch('entrasim.cli.get_config', side_effect=ValueError("Config error")), \
             patch('entrasim.cli.setup_logging'), \
             patch('entrasim.cli.console'), \
             patch('sys.exit') as mock_exit:
            
            main()
            mock_exit.assert_called_once_with(1)
    
    @pytest.mark.unit
    def test_main_keyboard_interrupt(self):
        """Test main function with keyboard interrupt."""
        test_args = ['entrasim', 'create', 'test.json']
        
        with patch('sys.argv', test_args), \
             patch('entrasim.cli.display_banner', side_effect=KeyboardInterrupt()), \
             patch('entrasim.cli.console'), \
             patch('sys.exit') as mock_exit:
            
            main()
            mock_exit.assert_called_once_with(1)
    
    @pytest.mark.unit
    def test_main_unexpected_exception(self):
        """Test main function with unexpected exception."""
        test_args = ['entrasim', 'create', 'test.json']
        
        with patch('sys.argv', test_args), \
             patch('entrasim.cli.display_banner', side_effect=Exception("Unexpected error")), \
             patch('entrasim.cli.console'), \
             patch('sys.exit') as mock_exit:
            
            main()
            mock_exit.assert_called_once_with(1)
    
    @pytest.mark.unit
    def test_main_verbose_mode(self, mock_env_vars):
        """Test main function in verbose mode."""
        test_args = ['entrasim', '--verbose', 'create', 'test.json']
        
        with patch('sys.argv', test_args), \
             patch('entrasim.cli.handle_create_command', return_value=True), \
             patch('entrasim.cli.display_banner'), \
             patch('entrasim.cli.get_config') as mock_get_config, \
             patch('entrasim.cli.setup_logging') as mock_setup_logging, \
             patch('sys.exit'):
            
            mock_config = Mock()
            mock_get_config.return_value = mock_config
            
            main()
            
            # Should set debug log level
            assert mock_config.log_level == 'DEBUG'
            mock_setup_logging.assert_called_with(True)
    
    @pytest.mark.unit
    def test_main_custom_env_file(self, mock_env_vars):
        """Test main function with custom env file."""
        test_args = ['entrasim', 'create', 'test.json', '--env-file', 'custom.env']
        
        with patch('sys.argv', test_args), \
             patch('entrasim.cli.handle_create_command', return_value=True), \
             patch('entrasim.cli.display_banner'), \
             patch('entrasim.cli.get_config') as mock_get_config, \
             patch('entrasim.cli.setup_logging'), \
             patch('sys.exit'):
            
            mock_get_config.return_value = Mock()
            main()
            
            # Should call get_config with custom env file
            mock_get_config.assert_called_with('custom.env')


class TestCLILogging:
    """Test CLI logging setup."""
    
    @pytest.mark.unit
    def test_setup_logging_normal_mode(self):
        """Test logging setup in normal mode."""
        with patch('entrasim.cli.logging.basicConfig') as mock_basic_config:
            from entrasim.cli import setup_logging
            setup_logging(verbose=False)
            
            mock_basic_config.assert_called_once()
            call_args = mock_basic_config.call_args
            assert call_args[1]['level'] == 20  # logging.INFO
    
    @pytest.mark.unit
    def test_setup_logging_verbose_mode(self):
        """Test logging setup in verbose mode."""
        with patch('entrasim.cli.logging.basicConfig') as mock_basic_config:
            from entrasim.cli import setup_logging
            setup_logging(verbose=True)
            
            mock_basic_config.assert_called_once()
            call_args = mock_basic_config.call_args
            assert call_args[1]['level'] == 10  # logging.DEBUG


class TestCLIErrorHandling:
    """Test CLI error handling scenarios."""
    
    @pytest.mark.unit
    def test_handle_create_command_file_not_found(self, mock_config):
        """Test create command with file not found."""
        args = create_cli_args_mock('create', 'nonexistent.json')
        
        with patch('entrasim.cli.console'):
            result = handle_create_command(args, mock_config)
            assert result is False
    
    @pytest.mark.unit
    def test_validate_azure_credentials_network_error(self, mock_config):
        """Test Azure credential validation with network error."""
        mock_config.validate_required_credentials.side_effect = Exception("Network timeout")
        
        with patch('entrasim.cli.console'):
            result = validate_azure_credentials(mock_config)
            assert result is False
    
    @pytest.mark.unit
    def test_confirm_operation_with_invalid_input(self):
        """Test confirmation with various invalid inputs."""
        with patch('entrasim.cli.console') as mock_console:
            # Test with empty input
            mock_console.input.return_value = ""
            result = confirm_operation("Test", "Details", force=False)
            assert result is False
            
            # Test with random text
            mock_console.input.return_value = "maybe"
            result = confirm_operation("Test", "Details", force=False)
            assert result is False