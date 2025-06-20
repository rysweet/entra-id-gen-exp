#!/usr/bin/env python3
"""Test runner script for EntraSim."""

import sys
import subprocess
import argparse
from pathlib import Path


def run_command(cmd, description="", exit_on_error=True):
    """Run a command and handle output."""
    print(f"\n{'='*60}")
    print(f"Running: {description or ' '.join(cmd)}")
    print(f"{'='*60}")
    
    try:
        result = subprocess.run(cmd, check=True, capture_output=False)
        print(f"✓ {description or 'Command'} completed successfully")
        return result.returncode == 0
    except subprocess.CalledProcessError as e:
        print(f"✗ {description or 'Command'} failed with exit code {e.returncode}")
        if exit_on_error:
            sys.exit(e.returncode)
        return False
    except FileNotFoundError:
        print(f"✗ Command not found: {cmd[0]}")
        if exit_on_error:
            sys.exit(1)
        return False


def check_pytest_available():
    """Check if pytest is available."""
    try:
        subprocess.run(['pytest', '--version'], check=True, capture_output=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False


def install_test_dependencies():
    """Install test dependencies."""
    print("Installing test dependencies...")
    dependencies = [
        'pytest>=7.0.0',
        'pytest-asyncio>=0.21.0',
        'pytest-mock>=3.10.0',
        'pytest-cov>=4.0.0',
        'pytest-xdist>=3.0.0'
    ]
    
    for dep in dependencies:
        cmd = [sys.executable, '-m', 'pip', 'install', dep]
        if not run_command(cmd, f"Installing {dep}", exit_on_error=False):
            print(f"Failed to install {dep}, continuing...")


def run_unit_tests(verbose=False, coverage=False):
    """Run unit tests."""
    cmd = ['pytest', 'tests/unit/']
    
    if verbose:
        cmd.append('-v')
    
    if coverage:
        cmd.extend(['--cov=entrasim', '--cov-report=term-missing', '--cov-report=html'])
    
    cmd.extend(['-m', 'unit'])
    
    return run_command(cmd, "Unit Tests", exit_on_error=False)


def run_integration_tests(verbose=False):
    """Run integration tests."""
    cmd = ['pytest', 'tests/integration/']
    
    if verbose:
        cmd.append('-v')
    
    cmd.extend(['-m', 'integration'])
    
    return run_command(cmd, "Integration Tests", exit_on_error=False)


def run_all_tests(verbose=False, coverage=False, parallel=False):
    """Run all tests."""
    cmd = ['pytest', 'tests/']
    
    if verbose:
        cmd.append('-v')
    
    if coverage:
        cmd.extend(['--cov=entrasim', '--cov-report=term-missing', '--cov-report=html'])
    
    if parallel:
        cmd.extend(['-n', 'auto'])
    
    return run_command(cmd, "All Tests", exit_on_error=False)


def run_specific_test(test_path, verbose=False):
    """Run a specific test file or test."""
    cmd = ['pytest', test_path]
    
    if verbose:
        cmd.append('-v')
    
    return run_command(cmd, f"Test: {test_path}", exit_on_error=False)


def generate_coverage_report():
    """Generate coverage report."""
    print("\nGenerating coverage report...")
    
    # Run tests with coverage
    cmd = [
        'pytest', 'tests/',
        '--cov=entrasim',
        '--cov-report=html',
        '--cov-report=term-missing',
        '--cov-report=xml'
    ]
    
    if run_command(cmd, "Coverage Report Generation", exit_on_error=False):
        print("\n📊 Coverage reports generated:")
        print("  - HTML: htmlcov/index.html")
        print("  - XML: coverage.xml")
        print("  - Terminal output above")


def lint_code():
    """Run code linting."""
    print("Running code linting...")
    
    # Try ruff first
    if run_command(['ruff', 'check', 'entrasim/', 'tests/'], "Ruff Linting", exit_on_error=False):
        print("✓ Code linting passed")
        return True
    else:
        print("ℹ Ruff not available, skipping linting")
        return False


def type_check():
    """Run type checking."""
    print("Running type checking...")
    
    # Try pyright
    if run_command(['pyright', 'entrasim/'], "Type Checking", exit_on_error=False):
        print("✓ Type checking passed")
        return True
    else:
        print("ℹ Pyright not available, skipping type checking")
        return False


def validate_test_fixtures():
    """Validate test fixtures."""
    print("Validating test fixtures...")
    
    fixtures_dir = Path("tests/fixtures")
    if not fixtures_dir.exists():
        print("✗ Test fixtures directory not found")
        return False
    
    json_files = list(fixtures_dir.glob("*.json"))
    if not json_files:
        print("✗ No JSON fixture files found")
        return False
    
    import json
    valid_count = 0
    
    for json_file in json_files:
        try:
            with open(json_file) as f:
                json.load(f)
            print(f"✓ {json_file.name} is valid JSON")
            valid_count += 1
        except json.JSONDecodeError as e:
            print(f"✗ {json_file.name} has invalid JSON: {e}")
    
    print(f"Validated {valid_count}/{len(json_files)} fixture files")
    return valid_count == len(json_files)


def main():
    """Main test runner function."""
    parser = argparse.ArgumentParser(description="EntraSim Test Runner")
    parser.add_argument(
        'test_type',
        choices=['unit', 'integration', 'all', 'specific', 'coverage', 'lint', 'type-check', 'fixtures'],
        help="Type of tests to run"
    )
    parser.add_argument(
        '--test-path',
        help="Path to specific test file or test (for 'specific' test type)"
    )
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help="Enable verbose output"
    )
    parser.add_argument(
        '--coverage', '-c',
        action='store_true',
        help="Generate coverage report"
    )
    parser.add_argument(
        '--parallel', '-p',
        action='store_true',
        help="Run tests in parallel (requires pytest-xdist)"
    )
    parser.add_argument(
        '--install-deps',
        action='store_true',
        help="Install test dependencies before running tests"
    )
    parser.add_argument(
        '--no-exit-on-error',
        action='store_true',
        help="Continue running even if tests fail"
    )
    
    args = parser.parse_args()
    
    # Install dependencies if requested
    if args.install_deps:
        install_test_dependencies()
    
    # Check if pytest is available
    if args.test_type in ['unit', 'integration', 'all', 'specific', 'coverage']:
        if not check_pytest_available():
            print("✗ pytest is not available. Install it with: pip install pytest")
            if args.install_deps:
                install_test_dependencies()
            else:
                print("Or run with --install-deps to install automatically")
                sys.exit(1)
    
    success = True
    
    # Run requested tests
    if args.test_type == 'unit':
        success = run_unit_tests(args.verbose, args.coverage)
    
    elif args.test_type == 'integration':
        success = run_integration_tests(args.verbose)
    
    elif args.test_type == 'all':
        success = run_all_tests(args.verbose, args.coverage, args.parallel)
    
    elif args.test_type == 'specific':
        if not args.test_path:
            print("✗ --test-path is required for specific tests")
            sys.exit(1)
        success = run_specific_test(args.test_path, args.verbose)
    
    elif args.test_type == 'coverage':
        success = generate_coverage_report()
    
    elif args.test_type == 'lint':
        success = lint_code()
    
    elif args.test_type == 'type-check':
        success = type_check()
    
    elif args.test_type == 'fixtures':
        success = validate_test_fixtures()
    
    # Exit with appropriate code
    if success:
        print(f"\n✓ {args.test_type.title()} completed successfully!")
        sys.exit(0)
    else:
        print(f"\n✗ {args.test_type.title()} failed!")
        if not args.no_exit_on_error:
            sys.exit(1)


def quick_test():
    """Run a quick test suite for development."""
    print("Running quick test suite...")
    
    steps = [
        ("Fixtures validation", validate_test_fixtures),
        ("Unit tests", lambda: run_unit_tests(verbose=False, coverage=False)),
        ("Code linting", lint_code),
    ]
    
    all_passed = True
    for name, func in steps:
        print(f"\n{'-'*40}")
        print(f"Running: {name}")
        print(f"{'-'*40}")
        
        if not func():
            all_passed = False
            print(f"✗ {name} failed")
        else:
            print(f"✓ {name} passed")
    
    print(f"\n{'='*60}")
    if all_passed:
        print("✓ Quick test suite passed!")
    else:
        print("✗ Quick test suite failed!")
    print(f"{'='*60}")
    
    return all_passed


if __name__ == "__main__":
    # If no arguments provided, run quick test
    if len(sys.argv) == 1:
        sys.argv.extend(['all', '--verbose'])
    
    main()