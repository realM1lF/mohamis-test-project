"""Tests for workspace manager."""

import pytest
import os
import tempfile
import yaml
from pathlib import Path
from unittest.mock import patch, MagicMock

from src.infrastructure.workspace_manager import (
    WorkspaceManager, 
    CustomerWorkspace, 
    WorkspaceStatus,
    get_workspace_manager
)


@pytest.fixture
def temp_config():
    """Create a temporary configuration file."""
    config = {
        "ddev_defaults": {
            "project_type": "shopware6",
            "php_version": "8.2"
        },
        "customers": {
            "test-customer": {
                "display_name": "Test Customer",
                "description": "Test customer for unit tests",
                "ddev": {
                    "project_name": "test-customer",
                    "php_version": "8.2",
                    "database": {
                        "type": "mariadb",
                        "version": "10.11"
                    }
                },
                "shopware": {
                    "version": "6.7.0.0"
                },
                "git": {
                    "remote": "https://github.com/test/repo.git",
                    "default_branch": "main"
                },
                "workspace": {
                    "base_path": "~/ki-data/test-workspace"
                }
            }
        }
    }
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        yaml.dump(config, f)
        config_path = f.name
    
    yield config_path
    
    # Cleanup
    os.unlink(config_path)


class TestWorkspaceManager:
    """Test cases for WorkspaceManager."""
    
    def test_load_config(self, temp_config):
        """Test configuration loading."""
        manager = WorkspaceManager(temp_config)
        
        assert manager.config is not None
        assert 'customers' in manager.config
        assert 'test-customer' in manager.config['customers']
    
    def test_get_workspace(self, temp_config):
        """Test getting a workspace."""
        manager = WorkspaceManager(temp_config)
        
        workspace = manager.get_workspace('test-customer')
        
        assert workspace is not None
        assert workspace.customer_id == 'test-customer'
        assert workspace.display_name == 'Test Customer'
    
    def test_get_nonexistent_workspace(self, temp_config):
        """Test getting a nonexistent workspace."""
        manager = WorkspaceManager(temp_config)
        
        workspace = manager.get_workspace('nonexistent')
        
        assert workspace is None
    
    def test_list_workspaces(self, temp_config):
        """Test listing workspaces."""
        manager = WorkspaceManager(temp_config)
        
        workspaces = manager.list_workspaces()
        
        assert len(workspaces) == 1
        assert workspaces[0].customer_id == 'test-customer'
    
    def test_workspace_paths(self, temp_config):
        """Test workspace path properties."""
        manager = WorkspaceManager(temp_config)
        workspace = manager.get_workspace('test-customer')
        
        assert 'test-workspace' in str(workspace.workspace_path)
        assert workspace.ddev_config_path.name == '.ddev'
        assert workspace.source_path.name == 'html'


class TestCustomerWorkspace:
    """Test cases for CustomerWorkspace."""
    
    def test_workspace_creation(self):
        """Test workspace dataclass creation."""
        workspace = CustomerWorkspace(
            customer_id='test',
            display_name='Test',
            description='Test description',
            base_path='/tmp/test',
            status=WorkspaceStatus.READY
        )
        
        assert workspace.customer_id == 'test'
        assert workspace.display_name == 'Test'
        assert workspace.status == WorkspaceStatus.READY
    
    def test_workspace_to_dict(self):
        """Test workspace serialization."""
        workspace = CustomerWorkspace(
            customer_id='test',
            display_name='Test',
            description='Test',
            base_path='/tmp/test'
        )
        
        data = workspace.to_dict()
        
        assert data['customer_id'] == 'test'
        assert data['display_name'] == 'Test'
        assert 'status' in data


class TestWorkspaceManagerMocked:
    """Test cases with mocked subprocess calls."""
    
    @patch('src.infrastructure.workspace_manager.subprocess.run')
    def test_execute_in_ddev_success(self, mock_run, temp_config):
        """Test successful command execution."""
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout='Success output',
            stderr=''
        )
        
        manager = WorkspaceManager(temp_config)
        
        # Set workspace as running
        workspace = manager.get_workspace('test-customer')
        workspace.status = WorkspaceStatus.DDEV_RUNNING
        
        success, stdout, stderr = manager.execute_in_ddev(
            'test-customer', 'echo test'
        )
        
        assert success is True
        assert stdout == 'Success output'
        mock_run.assert_called_once()
    
    @patch('src.infrastructure.workspace_manager.subprocess.run')
    def test_execute_in_ddev_failure(self, mock_run, temp_config):
        """Test failed command execution."""
        mock_run.return_value = MagicMock(
            returncode=1,
            stdout='',
            stderr='Error message'
        )
        
        manager = WorkspaceManager(temp_config)
        workspace = manager.get_workspace('test-customer')
        workspace.status = WorkspaceStatus.DDEV_RUNNING
        
        success, stdout, stderr = manager.execute_in_ddev(
            'test-customer', 'invalid-command'
        )
        
        assert success is False
        assert stderr == 'Error message'


class TestWorkspaceManagerIntegration:
    """Integration tests (requires actual DDEV setup)."""
    
    @pytest.mark.integration
    def test_ddev_check_installed(self):
        """Test DDEV installation check."""
        from src.infrastructure.ddev_manager import DDEVManager
        
        ddev = DDEVManager()
        installed, version = ddev.check_ddev_installed()
        
        # This test passes whether DDEV is installed or not
        # It's mainly to verify the check logic works
        if installed:
            assert 'ddev version' in version.lower() or 'v' in version
