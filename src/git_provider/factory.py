"""Factory for creating Git provider instances."""

from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field

from .base import GitProvider
from .github import GitHubProvider
from .bitbucket import BitbucketProvider


class ProviderType(str, Enum):
    """Supported Git provider types."""
    GITHUB = "github"
    BITBUCKET = "bitbucket"


class GitHubConfig(BaseModel):
    """Configuration for GitHub provider."""
    token: str = Field(..., description="GitHub Personal Access Token")
    # Optional: for GitHub Enterprise
    base_url: Optional[str] = Field(None, description="GitHub Enterprise URL (optional)")


class BitbucketConfig(BaseModel):
    """Configuration for Bitbucket provider."""
    token: str = Field(..., description="Bitbucket App Password or OAuth Token")
    workspace: Optional[str] = Field(None, description="Default workspace")


class GitProviderConfig(BaseModel):
    """Main configuration for Git provider."""
    provider: ProviderType = Field(..., description="Git provider type")
    github: Optional[GitHubConfig] = Field(None, description="GitHub config (if provider=github)")
    bitbucket: Optional[BitbucketConfig] = Field(None, description="Bitbucket config (if provider=bitbucket)")


class GitProviderFactory:
    """Factory for creating GitProvider instances.
    
    Usage:
        config = GitProviderConfig(
            provider=ProviderType.GITHUB,
            github=GitHubConfig(token="ghp_xxx")
        )
        provider = GitProviderFactory.create(config)
        
        # Or simply:
        provider = GitHubProvider("ghp_xxx")
    """
    
    @staticmethod
    def create(config: GitProviderConfig) -> GitProvider:
        """Create a GitProvider instance from configuration.
        
        Args:
            config: GitProviderConfig with provider type and credentials
            
        Returns:
            GitProvider instance (GitHubProvider or BitbucketProvider)
            
        Raises:
            ValueError: If configuration is invalid
        """
        if config.provider == ProviderType.GITHUB:
            if not config.github or not config.github.token:
                raise ValueError("GitHub config with token required")
            return GitHubProvider(config.github.token)
        
        elif config.provider == ProviderType.BITBUCKET:
            if not config.bitbucket or not config.bitbucket.token:
                raise ValueError("Bitbucket config with token required")
            return BitbucketProvider(
                config.bitbucket.token,
                workspace=config.bitbucket.workspace
            )
        
        else:
            raise ValueError(f"Unknown provider type: {config.provider}")
    
    @staticmethod
    def create_from_dict(config_dict: dict) -> GitProvider:
        """Create a GitProvider instance from a dictionary.
        
        This is useful for loading from environment variables or config files.
        
        Example config_dict:
            {
                "provider": "github",
                "github": {
                    "token": "ghp_xxx"
                }
            }
            
        Or for Bitbucket:
            {
                "provider": "bitbucket",
                "bitbucket": {
                    "token": "ATBBxxx",
                    "workspace": "myworkspace"
                }
            }
        """
        config = GitProviderConfig.model_validate(config_dict)
        return GitProviderFactory.create(config)


# Convenience function for simple creation
def create_provider(provider_type: str, token: str, **kwargs) -> GitProvider:
    """Create a GitProvider with minimal parameters.
    
    Args:
        provider_type: "github" or "bitbucket"
        token: API token
        **kwargs: Additional provider-specific args (e.g., workspace for Bitbucket)
        
    Returns:
        GitProvider instance
    """
    if provider_type.lower() == "github":
        return GitHubProvider(token)
    elif provider_type.lower() == "bitbucket":
        return BitbucketProvider(token, workspace=kwargs.get("workspace"))
    else:
        raise ValueError(f"Unknown provider type: {provider_type}")
