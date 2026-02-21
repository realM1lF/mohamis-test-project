#!/usr/bin/env python3
"""Setup script for customer DDEV environments.

This script creates a new DDEV project for a customer with proper configuration
for Shopware development.

Usage:
    python scripts/setup_customer_ddev.py --customer alp-shopware
    python scripts/setup_customer_ddev.py --customer kraft-shopware --repo https://github.com/agency/kraft-shopware.git
    python scripts/setup_customer_ddev.py --list
"""

import argparse
import logging
import sys
import os
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.infrastructure.workspace_manager import WorkspaceManager, get_workspace_manager
from src.infrastructure.ddev_manager import DDEVManager

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def list_customers(manager: WorkspaceManager):
    """List all configured customers."""
    print("\n" + "="*80)
    print("Configured Customers")
    print("="*80)
    
    workspaces = manager.list_workspaces()
    
    if not workspaces:
        print("No customers configured.")
        return
    
    for ws in workspaces:
        print(f"\n  {ws.customer_id}")
        print(f"    Name:        {ws.display_name}")
        print(f"    Description: {ws.description}")
        print(f"    Status:      {ws.status.value}")
        print(f"    Path:        {ws.workspace_path}")
        print(f"    Shopware:    {ws.shopware_config.get('version', 'N/A')}")
        print(f"    PHP:         {ws.ddev_config.get('php_version', 'N/A')}")
        print(f"    Database:    {ws.ddev_config.get('database', {}).get('type', 'N/A')} {ws.ddev_config.get('database', {}).get('version', 'N/A')}")


def setup_customer(manager: WorkspaceManager, customer_id: str, 
                   repo_url: str = None, start_ddev: bool = False):
    """Setup a customer workspace."""
    print(f"\n{'='*80}")
    print(f"Setting up workspace for: {customer_id}")
    print("="*80)
    
    # Check if customer exists
    workspace = manager.get_workspace(customer_id)
    if not workspace:
        print(f"ERROR: Customer '{customer_id}' not found in configuration.")
        print(f"Available customers:")
        for ws in manager.list_workspaces():
            print(f"  - {ws.customer_id}")
        return False
    
    print(f"\nCustomer: {workspace.display_name}")
    print(f"Description: {workspace.description}")
    print(f"Target path: {workspace.workspace_path}")
    
    if repo_url:
        print(f"Repository: {repo_url}")
    elif workspace.repo_url:
        print(f"Repository: {workspace.repo_url} (from config)")
    else:
        print(f"Repository: None (will create empty structure)")
    
    print(f"\nShopware {workspace.shopware_config.get('version', 'N/A')}")
    print(f"PHP {workspace.ddev_config.get('php_version', 'N/A')}")
    
    # Confirm
    if not input("\nContinue? [Y/n]: ").lower() in ['', 'y', 'yes']:
        print("Cancelled.")
        return False
    
    # Setup workspace
    print("\n→ Setting up workspace...")
    success, message = manager.setup_workspace(customer_id, repo_url)
    
    if not success:
        print(f"ERROR: {message}")
        return False
    
    print(f"✓ {message}")
    
    # Start DDEV if requested
    if start_ddev:
        print("\n→ Starting DDEV environment...")
        success, message = manager.start_ddev(customer_id)
        
        if not success:
            print(f"WARNING: {message}")
            print("You can start DDEV manually later with: ddev start")
        else:
            print(f"✓ {message}")
            
            # Show status
            status = manager.get_status(customer_id)
            if status.get('ddev_status') == 'running':
                print(f"\n✓ DDEV is running")
                print(f"  URLs: {', '.join(status.get('urls', ['N/A']))}")
    
    print(f"\n{'='*80}")
    print(f"Setup complete for {customer_id}")
    print("="*80)
    print(f"\nNext steps:")
    print(f"  cd {workspace.workspace_path}")
    print(f"  ddev status    # Check status")
    print(f"  ddev exec bin/console system:install --basic-setup  # If new project")
    
    return True


def start_customer(manager: WorkspaceManager, customer_id: str):
    """Start DDEV for a customer."""
    print(f"\nStarting DDEV for {customer_id}...")
    
    success, message = manager.start_ddev(customer_id)
    
    if success:
        print(f"✓ {message}")
        
        # Show status
        status = manager.get_status(customer_id)
        if status.get('urls'):
            print(f"\nURLs:")
            for url in status['urls']:
                print(f"  - {url}")
    else:
        print(f"✗ {message}")
        return False
    
    return True


def stop_customer(manager: WorkspaceManager, customer_id: str, delete: bool = False):
    """Stop DDEV for a customer."""
    action = "Deleting" if delete else "Stopping"
    print(f"\n{action} DDEV for {customer_id}...")
    
    success, message = manager.stop_ddev(customer_id, remove_data=delete)
    
    if success:
        print(f"✓ {message}")
    else:
        print(f"✗ {message}")
        return False
    
    return True


def status_customer(manager: WorkspaceManager, customer_id: str = None):
    """Show status of customer workspace(s)."""
    if customer_id:
        print(f"\n{'='*80}")
        print(f"Status: {customer_id}")
        print("="*80)
        
        status = manager.get_status(customer_id)
        
        for key, value in status.items():
            print(f"  {key}: {value}")
    else:
        print(f"\n{'='*80}")
        print("Status: All Customers")
        print("="*80)
        
        for ws in manager.list_workspaces():
            status = manager.get_status(ws.customer_id)
            print(f"\n{ws.customer_id}:")
            print(f"  Status: {status.get('status', 'unknown')}")
            print(f"  DDEV: {status.get('ddev_status', 'N/A')}")
            print(f"  Path: {status.get('workspace_path', 'N/A')}")


def test_customer(manager: WorkspaceManager, customer_id: str, 
                  test_suite: str = None):
    """Run tests in customer DDEV environment."""
    print(f"\n{'='*80}")
    print(f"Running tests for: {customer_id}")
    print("="*80)
    
    success, stdout, stderr = manager.run_tests(customer_id, test_suite)
    
    print(f"\n{stdout}")
    
    if stderr:
        print(f"\nStderr:\n{stderr}")
    
    if success:
        print("✓ Tests passed")
    else:
        print("✗ Tests failed")
    
    return success


def exec_customer(manager: WorkspaceManager, customer_id: str, command: str):
    """Execute command in customer DDEV environment."""
    print(f"\n{'='*80}")
    print(f"Executing in {customer_id}: {command}")
    print("="*80)
    
    success, stdout, stderr = manager.execute_in_ddev(customer_id, command)
    
    print(f"\n{stdout}")
    
    if stderr:
        print(f"\nStderr:\n{stderr}")
    
    return success


def sync_customer(manager: WorkspaceManager, customer_id: str, 
                  branch: str = None, message: str = None):
    """Sync customer workspace to repository."""
    print(f"\n{'='*80}")
    print(f"Syncing {customer_id} to repository")
    print("="*80)
    
    if not message:
        message = f"KI-Mitarbeiter update - {customer_id}"
    
    success, result_message = manager.sync_to_repo(customer_id, branch, message)
    
    if success:
        print(f"✓ {result_message}")
    else:
        print(f"✗ {result_message}")
    
    return success


def check_prerequisites():
    """Check if prerequisites are met."""
    print("Checking prerequisites...")
    
    # Check DDEV
    ddev_manager = DDEVManager()
    installed, version = ddev_manager.check_ddev_installed()
    
    if not installed:
        print("✗ DDEV is not installed or not in PATH")
        print("  Please install DDEV: https://ddev.readthedocs.io/en/stable/users/install/")
        return False
    
    print(f"✓ DDEV installed: {version.split(chr(10))[0] if chr(10) in version else version}")
    
    # Check Docker
    try:
        import subprocess
        result = subprocess.run(
            ["docker", "--version"],
            capture_output=True,
            text=True,
            timeout=10
        )
        if result.returncode == 0:
            print(f"✓ Docker installed: {result.stdout.strip()}")
        else:
            print("✗ Docker check failed")
            return False
    except Exception as e:
        print(f"✗ Docker not available: {e}")
        return False
    
    # Check directory structure
    ki_data = Path.home() / "ki-data" / "customer-workspaces"
    if not ki_data.exists():
        print(f"→ Creating directory: {ki_data}")
        ki_data.mkdir(parents=True, exist_ok=True)
    
    print(f"✓ Workspace directory: {ki_data}")
    
    return True


def main():
    parser = argparse.ArgumentParser(
        description="Setup and manage customer DDEV environments for Mohami KI-Mitarbeiter",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # List all configured customers
  python scripts/setup_customer_ddev.py --list
  
  # Setup a customer workspace
  python scripts/setup_customer_ddev.py --customer alp-shopware
  
  # Setup with custom repo and start DDEV
  python scripts/setup_customer_ddev.py --customer kraft-shopware --repo https://github.com/agency/kraft-shopware.git --start
  
  # Start/stop DDEV for a customer
  python scripts/setup_customer_ddev.py --customer alp-shopware --start
  python scripts/setup_customer_ddev.py --customer alp-shopware --stop
  
  # Check status
  python scripts/setup_customer_ddev.py --customer alp-shopware --status
  
  # Run tests
  python scripts/setup_customer_ddev.py --customer alp-shopware --test
  
  # Execute command in DDEV
  python scripts/setup_customer_ddev.py --customer alp-shopware --exec "bin/console cache:clear"
  
  # Sync changes to repo
  python scripts/setup_customer_ddev.py --customer alp-shopware --sync
        """
    )
    
    parser.add_argument(
        '--customer', '-c',
        help='Customer ID (e.g., alp-shopware, kraft-shopware, lupus)'
    )
    parser.add_argument(
        '--repo', '-r',
        help='Repository URL to clone (overrides config)'
    )
    parser.add_argument(
        '--list', '-l',
        action='store_true',
        help='List all configured customers'
    )
    parser.add_argument(
        '--setup', '-s',
        action='store_true',
        help='Setup workspace for customer'
    )
    parser.add_argument(
        '--start',
        action='store_true',
        help='Start DDEV environment'
    )
    parser.add_argument(
        '--stop',
        action='store_true',
        help='Stop DDEV environment'
    )
    parser.add_argument(
        '--delete',
        action='store_true',
        help='Delete DDEV project (with --stop)'
    )
    parser.add_argument(
        '--status',
        action='store_true',
        help='Show status of workspace'
    )
    parser.add_argument(
        '--test',
        action='store_true',
        help='Run PHPUnit tests'
    )
    parser.add_argument(
        '--test-suite',
        help='Test suite name (with --test)'
    )
    parser.add_argument(
        '--exec',
        dest='exec_cmd',
        help='Execute command in DDEV container'
    )
    parser.add_argument(
        '--sync',
        action='store_true',
        help='Sync workspace to repository'
    )
    parser.add_argument(
        '--branch',
        help='Branch for sync (with --sync)'
    )
    parser.add_argument(
        '--message', '-m',
        help='Commit message for sync'
    )
    parser.add_argument(
        '--config',
        default='config/customers.yaml',
        help='Path to customers configuration file'
    )
    
    args = parser.parse_args()
    
    # Initialize manager
    try:
        manager = get_workspace_manager(args.config)
    except FileNotFoundError as e:
        print(f"ERROR: {e}")
        print(f"\nMake sure you're running from the project root.")
        sys.exit(1)
    
    # Handle list
    if args.list:
        list_customers(manager)
        return
    
    # Check prerequisites
    if not check_prerequisites():
        print("\nPrerequisites not met. Please install required tools.")
        sys.exit(1)
    
    # Handle customer-specific commands
    if not args.customer:
        print("ERROR: --customer is required (unless using --list)")
        parser.print_help()
        sys.exit(1)
    
    if args.setup:
        success = setup_customer(manager, args.customer, args.repo, args.start)
        sys.exit(0 if success else 1)
    
    elif args.start:
        success = start_customer(manager, args.customer)
        sys.exit(0 if success else 1)
    
    elif args.stop:
        success = stop_customer(manager, args.customer, args.delete)
        sys.exit(0 if success else 1)
    
    elif args.status:
        status_customer(manager, args.customer)
    
    elif args.test:
        success = test_customer(manager, args.customer, args.test_suite)
        sys.exit(0 if success else 1)
    
    elif args.exec_cmd:
        success = exec_customer(manager, args.customer, args.exec_cmd)
        sys.exit(0 if success else 1)
    
    elif args.sync:
        success = sync_customer(manager, args.customer, args.branch, args.message)
        sys.exit(0 if success else 1)
    
    else:
        # Default: show status
        status_customer(manager, args.customer)


if __name__ == '__main__':
    main()
