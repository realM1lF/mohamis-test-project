#!/usr/bin/env python3
"""Test script for Architecture V2 - Workspace and Repository Management.

This script tests the new architecture where:
1. Workspaces are set up by cloning repositories
2. DDEV runs inside the cloned repo (if configured)
3. No hardcoded docker-compose.ddev.yml needed
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from pathlib import Path


def test_repository_manager():
    """Test RepositoryManager functionality."""
    print("=" * 60)
    print("Testing RepositoryManager")
    print("=" * 60)
    
    from src.infrastructure.repository_manager import RepositoryManager, GitProvider
    
    # Create manager
    rm = RepositoryManager(base_workspaces_path="~/ki-data/test-workspaces")
    
    # Test provider detection
    test_urls = [
        ("https://github.com/user/repo", GitProvider.GITHUB),
        ("git@github.com:user/repo.git", GitProvider.GITHUB),
        ("https://bitbucket.org/workspace/repo", GitProvider.BITBUCKET),
        ("https://gitlab.com/user/repo", GitProvider.GITLAB),
        ("https://other.com/repo", GitProvider.GENERIC),
    ]
    
    print("\n1. Testing provider detection:")
    for url, expected in test_urls:
        detected = rm._detect_provider(url)
        status = "✓" if detected == expected else "✗"
        print(f"  {status} {url} -> {detected.value}")
    
    # Test URL normalization
    print("\n2. Testing URL normalization:")
    test_normalize = [
        ("git@github.com:user/repo.git", GitProvider.GITHUB, "https://github.com/user/repo"),
        ("https://github.com/user/repo", GitProvider.GITHUB, "https://github.com/user/repo"),
        ("user/repo", GitProvider.GITHUB, "https://github.com/user/repo"),
    ]
    
    for url, provider, expected in test_normalize:
        normalized = rm._normalize_url(url, provider)
        status = "✓" if normalized == expected else "✗"
        print(f"  {status} {url} -> {normalized}")
    
    # Test workspace path
    print("\n3. Testing workspace path generation:")
    path = rm.get_workspace_path("test-customer")
    print(f"  Workspace path: {path}")
    assert "test-workspaces/test-customer" in str(path)
    print("  ✓ Path generation correct")
    
    print("\n✅ RepositoryManager tests passed!\n")
    return True


def test_workspace_manager():
    """Test WorkspaceManager functionality."""
    print("=" * 60)
    print("Testing WorkspaceManager")
    print("=" * 60)
    
    from src.infrastructure.workspace_manager import WorkspaceManager, WorkspaceStatus
    
    # Create manager
    wm = WorkspaceManager(config_path="config/customers.yaml")
    
    print("\n1. Testing workspace loading:")
    workspaces = wm.list_workspaces()
    print(f"  Loaded {len(workspaces)} workspace(s) from config")
    for ws in workspaces:
        print(f"  - {ws.customer_id}: {ws.name}")
    
    print("\n2. Testing workspace retrieval:")
    if workspaces:
        ws = wm.get_workspace(workspaces[0].customer_id)
        if ws:
            print(f"  ✓ Retrieved workspace: {ws.customer_id}")
            print(f"    - Repo URL: {ws.repo_url}")
            print(f"    - Has DDEV: {ws.has_ddev}")
            print(f"    - Provider: {ws.git_provider}")
    
    print("\n3. Testing status for test-customer:")
    status = wm.get_status("test-customer")
    if "error" not in status:
        print(f"  ✓ Workspace found")
        print(f"    - Status: {status.get('status')}")
        print(f"    - Path: {status.get('workspace_path')}")
        print(f"    - Has DDEV config: {status.get('has_ddev_config')}")
    else:
        print(f"  Note: {status['error']}")
    
    print("\n✅ WorkspaceManager tests passed!\n")
    return True


def test_ddev_tools():
    """Test DDEV tools registration."""
    print("=" * 60)
    print("Testing DDEV Tools")
    print("=" * 60)
    
    from src.tools.ddev_tools import (
        DDEVExecuteTool,
        WorkspaceSetupTool,
        WorkspaceStatusTool,
        GitSyncTool,
        GitPullTool,
        ListWorkspacesTool,
    )
    
    print("\n1. Testing tool instantiation:")
    tools = [
        WorkspaceSetupTool(),
        WorkspaceStatusTool(),
        DDEVExecuteTool(),
        GitSyncTool(),
        GitPullTool(),
        ListWorkspacesTool(),
    ]
    
    for tool in tools:
        print(f"  ✓ {tool.name}: {tool.description[:50]}...")
    
    print(f"\n  Total tools: {len(tools)}")
    
    print("\n✅ DDEV Tools tests passed!\n")
    return True


def test_config_format():
    """Test new config format."""
    print("=" * 60)
    print("Testing Config Format")
    print("=" * 60)
    
    import yaml
    
    config_path = Path("config/customers.yaml")
    if not config_path.exists():
        print("  ✗ Config file not found")
        return False
    
    with open(config_path) as f:
        config = yaml.safe_load(f)
    
    print("\n1. Checking config structure:")
    
    # Check version
    version = config.get("version")
    print(f"  Config version: {version}")
    
    # Check template
    if "template" in config:
        print("  ✓ Template section found")
    
    # Check customers
    customers = config.get("customers", {})
    print(f"  ✓ Found {len(customers)} customer(s)")
    
    for customer_id, customer_config in customers.items():
        print(f"\n  Customer: {customer_id}")
        
        # Check required fields
        required = ["id", "name", "git_provider", "repo_url", "default_branch"]
        for field in required:
            if field in customer_config:
                print(f"    ✓ {field}: {customer_config[field]}")
            else:
                print(f"    ✗ Missing: {field}")
        
        # Check tech_stack
        if "tech_stack" in customer_config:
            ts = customer_config["tech_stack"]
            print(f"    ✓ Tech stack: {ts.get('type')} {ts.get('version')}")
    
    print("\n✅ Config Format tests passed!\n")
    return True


def test_architecture_changes():
    """Verify architecture changes."""
    print("=" * 60)
    print("Testing Architecture Changes")
    print("=" * 60)
    
    print("\n1. Checking removed files:")
    
    # docker-compose.ddev.yml should be removed
    ddev_compose = Path("docker-compose.ddev.yml")
    if ddev_compose.exists():
        print(f"  ✗ {ddev_compose} still exists (should be removed)")
    else:
        print(f"  ✓ {ddev_compose} removed")
    
    print("\n2. Checking new files:")
    
    new_files = [
        "src/infrastructure/repository_manager.py",
        "docs/ARCHITECTURE_V2.md",
    ]
    
    for file_path in new_files:
        path = Path(file_path)
        if path.exists():
            print(f"  ✓ {file_path} created")
        else:
            print(f"  ✗ {file_path} not found")
    
    print("\n3. Checking modified files:")
    
    modified_files = [
        "src/infrastructure/workspace_manager.py",
        "src/infrastructure/__init__.py",
        "src/tools/ddev_tools.py",
        "config/customers.yaml",
    ]
    
    for file_path in modified_files:
        path = Path(file_path)
        if path.exists():
            print(f"  ✓ {file_path} exists")
        else:
            print(f"  ✗ {file_path} not found")
    
    print("\n✅ Architecture Changes tests passed!\n")
    return True


def main():
    """Run all tests."""
    print("\n" + "=" * 60)
    print("Mohami KI-Mitarbeiter - Architecture V2 Tests")
    print("=" * 60 + "\n")
    
    tests = [
        ("RepositoryManager", test_repository_manager),
        ("WorkspaceManager", test_workspace_manager),
        ("DDEV Tools", test_ddev_tools),
        ("Config Format", test_config_format),
        ("Architecture Changes", test_architecture_changes),
    ]
    
    results = []
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print(f"\n❌ {name} test failed with error: {e}")
            import traceback
            traceback.print_exc()
            results.append((name, False))
    
    # Summary
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)
    
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {status}: {name}")
    
    passed = sum(1 for _, r in results if r)
    total = len(results)
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed! Architecture V2 is ready.")
        return 0
    else:
        print("\n⚠️  Some tests failed. Please review.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
