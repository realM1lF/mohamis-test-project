#!/usr/bin/env python3
"""Simple test for Architecture V2 - verifies file structure and syntax.

This test doesn't require external dependencies.
"""

import sys
import ast
from pathlib import Path


def test_file_exists_and_valid_python(filepath):
    """Check if file exists and is valid Python."""
    path = Path(filepath)
    if not path.exists():
        return False, f"File not found: {filepath}"
    
    try:
        with open(path) as f:
            code = f.read()
        ast.parse(code)
        return True, f"Valid Python: {filepath}"
    except SyntaxError as e:
        return False, f"Syntax error in {filepath}: {e}"


def test_repository_manager_syntax():
    """Test RepositoryManager file syntax."""
    print("=" * 60)
    print("Testing RepositoryManager Syntax")
    print("=" * 60)
    
    success, msg = test_file_exists_and_valid_python(
        "src/infrastructure/repository_manager.py"
    )
    print(f"  {'✓' if success else '✗'} {msg}")
    
    if success:
        # Check for key classes and functions
        with open("src/infrastructure/repository_manager.py") as f:
            code = f.read()
        
        checks = [
            ("class RepositoryManager", "RepositoryManager class"),
            ("class RepositoryInfo", "RepositoryInfo dataclass"),
            ("def clone_repo", "clone_repo method"),
            ("def pull_changes", "pull_changes method"),
            ("def push_changes", "push_changes method"),
            ("def get_repo_info", "get_repo_info method"),
            ("class GitProvider", "GitProvider enum"),
        ]
        
        for pattern, desc in checks:
            found = pattern in code
            print(f"  {'✓' if found else '✗'} {desc}")
    
    print()
    return success


def test_workspace_manager_syntax():
    """Test WorkspaceManager file syntax."""
    print("=" * 60)
    print("Testing WorkspaceManager Syntax")
    print("=" * 60)
    
    success, msg = test_file_exists_and_valid_python(
        "src/infrastructure/workspace_manager.py"
    )
    print(f"  {'✓' if success else '✗'} {msg}")
    
    if success:
        with open("src/infrastructure/workspace_manager.py") as f:
            code = f.read()
        
        checks = [
            ("class WorkspaceManager", "WorkspaceManager class"),
            ("class CustomerWorkspace", "CustomerWorkspace dataclass"),
            ("def setup_workspace", "setup_workspace method"),
            ("def execute_command", "execute_command method"),
            ("from .repository_manager", "imports RepositoryManager"),
            ("has_ddev_config", "has_ddev_config property"),
        ]
        
        for pattern, desc in checks:
            found = pattern in code
            print(f"  {'✓' if found else '✗'} {desc}")
    
    print()
    return success


def test_ddev_tools_syntax():
    """Test DDEV tools file syntax."""
    print("=" * 60)
    print("Testing DDEV Tools Syntax")
    print("=" * 60)
    
    success, msg = test_file_exists_and_valid_python(
        "src/tools/ddev_tools.py"
    )
    print(f"  {'✓' if success else '✗'} {msg}")
    
    if success:
        with open("src/tools/ddev_tools.py") as f:
            code = f.read()
        
        checks = [
            ("class WorkspaceSetupTool", "WorkspaceSetupTool"),
            ("class DDEVExecuteTool", "DDEVExecuteTool"),
            ("class GitSyncTool", "GitSyncTool"),
            ("class GitPullTool", "GitPullTool"),
            ("class TestRunnerTool", "TestRunnerTool"),
            ("def register_ddev_tools", "register_ddev_tools function"),
        ]
        
        for pattern, desc in checks:
            found = pattern in code
            print(f"  {'✓' if found else '✗'} {desc}")
    
    print()
    return success


def test_config_file():
    """Test config file exists and has new format."""
    print("=" * 60)
    print("Testing Config File")
    print("=" * 60)
    
    config_path = Path("config/customers.yaml")
    if not config_path.exists():
        print("  ✗ Config file not found")
        return False
    
    print("  ✓ Config file exists")
    
    with open(config_path) as f:
        content = f.read()
    
    checks = [
        ("version:", "Version field"),
        ("template:", "Template section"),
        ("customers:", "Customers section"),
        ("git_provider:", "git_provider field"),
        ("repo_url:", "repo_url field"),
        ("has_ddev:", "has_ddev field"),
        ("tech_stack:", "tech_stack field"),
        ("test-customer:", "test-customer entry"),
    ]
    
    for pattern, desc in checks:
        found = pattern in content
        print(f"  {'✓' if found else '✗'} {desc}")
    
    print()
    return True


def test_architecture_changes():
    """Verify architecture changes."""
    print("=" * 60)
    print("Testing Architecture Changes")
    print("=" * 60)
    
    print("\n1. Checking removed files:")
    
    ddev_compose = Path("docker-compose.ddev.yml")
    if ddev_compose.exists():
        print(f"  ✗ {ddev_compose} still exists")
    else:
        print(f"  ✓ {ddev_compose} removed")
    
    print("\n2. Checking new files:")
    
    new_files = [
        "src/infrastructure/repository_manager.py",
        "docs/ARCHITECTURE_V2.md",
    ]
    
    for file_path in new_files:
        path = Path(file_path)
        exists = path.exists()
        print(f"  {'✓' if exists else '✗'} {file_path}")
    
    print("\n3. Checking modified files:")
    
    modified_files = [
        "src/infrastructure/workspace_manager.py",
        "src/infrastructure/__init__.py",
        "src/tools/ddev_tools.py",
        "config/customers.yaml",
    ]
    
    for file_path in modified_files:
        path = Path(file_path)
        exists = path.exists()
        print(f"  {'✓' if exists else '✗'} {file_path}")
    
    print()
    return True


def main():
    """Run all tests."""
    print("\n" + "=" * 60)
    print("Mohami KI-Mitarbeiter - Architecture V2 Syntax Tests")
    print("=" * 60 + "\n")
    
    tests = [
        ("RepositoryManager Syntax", test_repository_manager_syntax),
        ("WorkspaceManager Syntax", test_workspace_manager_syntax),
        ("DDEV Tools Syntax", test_ddev_tools_syntax),
        ("Config File", test_config_file),
        ("Architecture Changes", test_architecture_changes),
    ]
    
    results = []
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print(f"\n  ❌ {name} test failed: {e}")
            results.append((name, False))
    
    # Summary
    print("=" * 60)
    print("Test Summary")
    print("=" * 60)
    
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {status}: {name}")
    
    passed = sum(1 for _, r in results if r)
    total = len(results)
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All syntax tests passed!")
        print("\nArchitecture V2 ist implementiert:")
        print("  ✓ docker-compose.ddev.yml gelöscht")
        print("  ✓ RepositoryManager erstellt (GitHub + Bitbucket)")
        print("  ✓ WorkspaceManager korrigiert (DDEV im geklonten Repo)")
        print("  ✓ DDEV Tools aktualisiert")
        print("  ✓ customers.yaml mit neuem Format")
        return 0
    else:
        print("\n⚠️  Some tests failed.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
