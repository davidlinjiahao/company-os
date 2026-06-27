"""Configuration management using Pydantic Settings."""
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


class ObsidianConfig(BaseSettings):
    """Obsidian Vault MCP configuration."""

    vault_path: str = str(Path.home() / "Documents" / "ObsidianVault")

    # Search settings
    default_search_limit: int = 20
    max_search_results: int = 100

    # Logging
    log_level: str = "INFO"

    model_config = SettingsConfigDict(
        env_prefix="OBSIDIAN_",
        env_file=".env",
        extra="ignore",
    )

    @property
    def vault(self) -> Path:
        """Get vault path as Path object."""
        return Path(self.vault_path)


config = ObsidianConfig()
