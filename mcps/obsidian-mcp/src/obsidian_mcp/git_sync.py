"""Git sync for vault: pull, commit, push with conflict retry."""
import hashlib
import logging
import os
import subprocess
import time
from pathlib import Path

logger = logging.getLogger(__name__)


def get_file_hash(path: Path) -> str:
    """Return short hash of file content for optimistic concurrency."""
    return hashlib.sha256(path.read_bytes()).hexdigest()[:12]


class GitSync:
    """Handles git pull/commit/push for the vault."""

    def __init__(self, vault_path: Path, enabled: bool = True, pull_interval: int = 120):
        self.vault_path = vault_path
        self.enabled = enabled
        self.pull_interval = pull_interval
        self._last_pull: float = 0

    def _run(self, cmd: list[str], **kwargs) -> subprocess.CompletedProcess:
        """Run a git command in the vault directory."""
        return subprocess.run(
            cmd,
            cwd=self.vault_path,
            capture_output=True,
            text=True,
            timeout=30,
            **kwargs,
        )

    def _is_git_repo(self) -> bool:
        """Check if vault is a git repository."""
        return (self.vault_path / ".git").exists()

    def _push_with_retry(self, message: str) -> None:
        """Commit staged changes and push with retry on conflict."""
        result = self._run(["git", "commit", "-m", f"vault: {message}"])
        if result.returncode != 0:
            logger.debug("Nothing to commit: %s", message)
            return

        for attempt in range(3):
            push = self._run(["git", "push"])
            if push.returncode == 0:
                logger.info("Pushed vault change: %s", message)
                return
            logger.info("Push failed (attempt %d), rebasing...", attempt + 1)
            self._run(["git", "pull", "--rebase", "--autostash"])

        logger.warning("Push failed after 3 attempts for: %s", message)

    def pull_if_stale(self) -> None:
        """Pull from origin if last pull was > pull_interval ago."""
        if not self.enabled or not self._is_git_repo():
            return
        now = time.time()
        if now - self._last_pull < self.pull_interval:
            return
        try:
            result = self._run(["git", "pull", "--rebase", "--autostash"])
            if result.returncode == 0:
                logger.debug("Git pull succeeded")
            else:
                logger.warning("Git pull failed: %s", result.stderr.strip())
        except subprocess.TimeoutExpired:
            logger.warning("Git pull timed out")
        except Exception as e:
            logger.warning("Git pull error: %s", e)
        self._last_pull = now

    def commit_and_push(self, path: str, message: str) -> None:
        """Stage, commit, and push a single file change."""
        if not self.enabled or not self._is_git_repo():
            return
        try:
            self._run(["git", "add", "--", path])
            self._push_with_retry(message)
        except subprocess.TimeoutExpired:
            logger.warning("Git operation timed out for: %s", message)
        except Exception as e:
            logger.warning("Git sync error: %s", e)

    def commit_and_push_rename(self, old_path: str, new_path: str, message: str) -> None:
        """Stage a rename (old delete + new add), commit, and push."""
        if not self.enabled or not self._is_git_repo():
            return
        try:
            self._run(["git", "add", "--", old_path, new_path])
            self._push_with_retry(message)
        except subprocess.TimeoutExpired:
            logger.warning("Git operation timed out for: %s", message)
        except Exception as e:
            logger.warning("Git sync error: %s", e)


def create_git_sync(vault_path: Path) -> GitSync:
    """Factory: create GitSync from environment variables."""
    enabled = os.environ.get("VAULT_GIT_SYNC", "true").lower() in ("true", "1", "yes")
    pull_interval = int(os.environ.get("VAULT_GIT_PULL_INTERVAL", "120"))
    return GitSync(vault_path, enabled=enabled, pull_interval=pull_interval)
