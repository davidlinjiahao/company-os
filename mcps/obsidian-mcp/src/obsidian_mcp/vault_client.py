"""Obsidian Vault file operations client."""
import logging
import os
import re
from pathlib import Path
from typing import Any

from .config import config
from .converters import (
    file_list_to_markdown,
    folder_tree_to_markdown,
    note_to_markdown,
    search_results_to_markdown,
    tags_to_markdown,
)
from .git_sync import GitSync, create_git_sync, get_file_hash

logger = logging.getLogger(__name__)


class VaultError(Exception):
    """Vault operation error."""

    def __init__(self, message: str):
        self.message = message
        super().__init__(message)


class VaultClient:
    """Client for Obsidian vault file operations."""

    def __init__(self):
        self._vault_path: Path | None = None
        self._git_sync: GitSync | None = None

    @property
    def vault(self) -> Path:
        """Get validated vault path."""
        if self._vault_path is None:
            self._vault_path = config.vault
            if not self._vault_path.exists():
                raise VaultError(f"Vault not found: {self._vault_path}")
            if not self._vault_path.is_dir():
                raise VaultError(f"Vault path is not a directory: {self._vault_path}")
        return self._vault_path

    @property
    def git_sync(self) -> GitSync:
        """Get or create the GitSync instance."""
        if self._git_sync is None:
            self._git_sync = create_git_sync(self.vault)
        return self._git_sync

    def _resolve_path(self, path: str) -> Path:
        """Resolve relative path to absolute, ensuring it's within vault."""
        # Handle absolute paths that are already in vault
        if path.startswith(str(self.vault)):
            full_path = Path(path)
        else:
            # Relative path
            full_path = self.vault / path

        # Security: ensure path is within vault
        try:
            full_path.resolve().relative_to(self.vault.resolve())
        except ValueError:
            raise VaultError(f"Path outside vault: {path}")

        return full_path

    def _get_file_info(self, path: Path) -> dict[str, Any]:
        """Get file metadata."""
        stat = path.stat()
        return {
            "name": path.name,
            "path": str(path.relative_to(self.vault)),
            "modified": stat.st_mtime,
            "size": stat.st_size,
        }

    def _is_valid_note(self, path: Path) -> bool:
        """Check if path is a valid note file."""
        return (
            path.is_file()
            and path.suffix == ".md"
            and not path.name.startswith(".")
            and ".trash" not in path.parts
        )

    @staticmethod
    def _ensure_md_ext(path: str) -> str:
        """Ensure path has .md extension."""
        return path if path.endswith(".md") else path + ".md"

    def _require_existing_note(self, path: str) -> Path:
        """Resolve path, verify note exists and is valid. Returns full path."""
        full_path = self._resolve_path(path)
        if not full_path.exists():
            raise VaultError(f"Note not found: {path}")
        if not self._is_valid_note(full_path):
            raise VaultError(f"Not a valid note file: {path}")
        return full_path

    # --- Read Operations ---

    def read_note(self, path: str) -> str:
        """Read a note's content.

        Args:
            path: Relative path to note (with or without .md extension)

        Returns:
            Markdown-formatted note with metadata and content_hash
        """
        self.git_sync.pull_if_stale()

        path = self._ensure_md_ext(path)
        full_path = self._require_existing_note(path)

        content = full_path.read_text(encoding="utf-8")
        metadata = self._get_file_info(full_path)
        metadata["content_hash"] = get_file_hash(full_path)

        return note_to_markdown(path, content, metadata)

    def list_folder(self, folder: str = "", recursive: bool = False) -> str:
        """List contents of a folder.

        Args:
            folder: Relative folder path (empty for root)
            recursive: Include subfolders recursively

        Returns:
            Markdown-formatted file list
        """
        self.git_sync.pull_if_stale()

        folder_path = self._resolve_path(folder) if folder else self.vault

        if not folder_path.exists():
            raise VaultError(f"Folder not found: {folder}")

        if not folder_path.is_dir():
            raise VaultError(f"Not a folder: {folder}")

        files = []
        pattern = "**/*.md" if recursive else "*.md"

        for path in folder_path.glob(pattern):
            if self._is_valid_note(path):
                files.append(self._get_file_info(path))

        # Sort by modified time, newest first
        files.sort(key=lambda x: x["modified"], reverse=True)

        title = f"Files in `{folder}`" if folder else "Files in vault root"
        return file_list_to_markdown(files[:config.max_search_results], title)

    def get_folder_structure(self, folder: str = "", max_depth: int = 3) -> str:
        """Get folder tree structure.

        Args:
            folder: Starting folder (empty for root)
            max_depth: Maximum depth to traverse

        Returns:
            Markdown-formatted folder tree
        """
        self.git_sync.pull_if_stale()

        folder_path = self._resolve_path(folder) if folder else self.vault

        if not folder_path.exists():
            raise VaultError(f"Folder not found: {folder}")

        def build_tree(path: Path, depth: int) -> dict[str, Any]:
            result: dict[str, Any] = {"files": [], "folders": {}}

            if depth <= 0:
                return result

            for item in sorted(path.iterdir()):
                if item.name.startswith(".") or item.name == ".trash":
                    continue

                if item.is_dir():
                    result["folders"][item.name] = build_tree(item, depth - 1)
                elif item.suffix == ".md":
                    result["files"].append(item.name)

            return result

        tree = build_tree(folder_path, max_depth)
        title = f"Structure of `{folder}`" if folder else "Vault Structure"
        return folder_tree_to_markdown(tree, title)

    def search_content(self, query: str, folder: str = "", limit: int | None = None) -> str:
        """Search for text within notes.

        Args:
            query: Text to search for (case-insensitive)
            folder: Limit search to folder
            limit: Max results

        Returns:
            Markdown-formatted search results
        """
        self.git_sync.pull_if_stale()

        limit = limit or config.default_search_limit
        search_path = self._resolve_path(folder) if folder else self.vault

        results = []
        pattern = re.compile(re.escape(query), re.IGNORECASE)

        for path in search_path.rglob("*.md"):
            if not self._is_valid_note(path):
                continue

            try:
                content = path.read_text(encoding="utf-8")
            except Exception:
                continue

            matches = []
            for i, line in enumerate(content.split("\n"), 1):
                if pattern.search(line):
                    matches.append({"line": i, "context": line.strip()})

            if matches:
                results.append({
                    "path": str(path.relative_to(self.vault)),
                    "matches": matches,
                })

            if len(results) >= limit:
                break

        return search_results_to_markdown(results, query, "content")

    def search_filename(self, query: str, folder: str = "", limit: int | None = None) -> str:
        """Search for notes by filename.

        Args:
            query: Filename pattern (case-insensitive)
            folder: Limit search to folder
            limit: Max results

        Returns:
            Markdown-formatted search results
        """
        self.git_sync.pull_if_stale()

        limit = limit or config.default_search_limit
        search_path = self._resolve_path(folder) if folder else self.vault

        results = []
        pattern = re.compile(re.escape(query), re.IGNORECASE)

        for path in search_path.rglob("*.md"):
            if not self._is_valid_note(path):
                continue

            if pattern.search(path.stem):
                results.append({
                    "path": str(path.relative_to(self.vault)),
                    "matches": [{"line": 0, "context": path.stem}],
                })

            if len(results) >= limit:
                break

        return search_results_to_markdown(results, query, "filename")

    def search_tags(self, tag: str | None = None) -> str:
        """Search for tags or list all tags.

        Args:
            tag: Specific tag to search for (without #), or None for all tags

        Returns:
            Markdown-formatted tag results
        """
        self.git_sync.pull_if_stale()

        tag_pattern = re.compile(r"#([a-zA-Z][a-zA-Z0-9_/-]*)")
        tags: dict[str, int] = {}
        files_with_tag: list[dict[str, Any]] = []
        seen_paths: set[Path] = set()

        for path in self.vault.rglob("*.md"):
            if not self._is_valid_note(path):
                continue

            try:
                content = path.read_text(encoding="utf-8")
            except Exception:
                continue

            found_tags = tag_pattern.findall(content)

            for t in found_tags:
                tags[t] = tags.get(t, 0) + 1

                if tag and t.lower() == tag.lower() and path not in seen_paths:
                    seen_paths.add(path)
                    files_with_tag.append(self._get_file_info(path))

        if tag:
            return file_list_to_markdown(files_with_tag, f"Files with tag `#{tag}`")

        return tags_to_markdown(tags)

    def get_recent(self, limit: int = 10) -> str:
        """Get recently modified notes.

        Args:
            limit: Number of notes to return

        Returns:
            Markdown-formatted list of recent notes
        """
        self.git_sync.pull_if_stale()

        files = []

        for path in self.vault.rglob("*.md"):
            if self._is_valid_note(path):
                files.append(self._get_file_info(path))

        files.sort(key=lambda x: x["modified"], reverse=True)
        return file_list_to_markdown(files[:limit], "Recently Modified Notes")

    # --- Write Operations ---

    def create_note(self, path: str, content: str) -> str:
        """Create a new note.

        Args:
            path: Relative path for new note (with or without .md)
            content: Note content

        Returns:
            Confirmation message
        """
        path = self._ensure_md_ext(path)
        full_path = self._resolve_path(path)

        if full_path.exists():
            raise VaultError(f"Note already exists: {path}")

        # Ensure parent directory exists
        full_path.parent.mkdir(parents=True, exist_ok=True)

        full_path.write_text(content, encoding="utf-8")
        logger.info(f"Created note: {path}")

        self.git_sync.commit_and_push(path, f"create {path}")

        return f"Created note: `{path}`"

    def update_note(self, path: str, content: str, expected_hash: str | None = None) -> str:
        """Update an existing note.

        Args:
            path: Relative path to note
            content: New content
            expected_hash: If provided, check that current file hash matches
                before writing. Prevents overwriting concurrent edits.

        Returns:
            Confirmation message
        """
        path = self._ensure_md_ext(path)
        full_path = self._require_existing_note(path)

        # Optimistic concurrency check
        if expected_hash is not None:
            current_hash = get_file_hash(full_path)
            if current_hash != expected_hash:
                raise VaultError(
                    f"File was modified since last read (expected hash {expected_hash}, "
                    f"got {current_hash}). Re-read the note and retry."
                )

        full_path.write_text(content, encoding="utf-8")
        logger.info(f"Updated note: {path}")

        self.git_sync.commit_and_push(path, f"update {path}")

        return f"Updated note: `{path}`"

    def append_to_note(self, path: str, content: str) -> str:
        """Append content to an existing note.

        Args:
            path: Relative path to note
            content: Content to append

        Returns:
            Confirmation message
        """
        path = self._ensure_md_ext(path)
        full_path = self._require_existing_note(path)

        existing = full_path.read_text(encoding="utf-8")
        full_path.write_text(existing + "\n" + content, encoding="utf-8")
        logger.info(f"Appended to note: {path}")

        self.git_sync.commit_and_push(path, f"append to {path}")

        return f"Appended to note: `{path}`"

    def rename_note(self, old_path: str, new_path: str) -> str:
        """Rename/move a note.

        Args:
            old_path: Current path
            new_path: New path

        Returns:
            Confirmation message
        """
        old_path = self._ensure_md_ext(old_path)
        new_path = self._ensure_md_ext(new_path)

        old_full = self._resolve_path(old_path)
        new_full = self._resolve_path(new_path)

        if not old_full.exists():
            raise VaultError(f"Note not found: {old_path}")

        if new_full.exists():
            raise VaultError(f"Destination already exists: {new_path}")

        # Ensure parent directory exists
        new_full.parent.mkdir(parents=True, exist_ok=True)

        old_full.rename(new_full)
        logger.info(f"Renamed note: {old_path} -> {new_path}")

        self.git_sync.commit_and_push_rename(old_path, new_path, f"rename {old_path} -> {new_path}")

        return f"Renamed: `{old_path}` -> `{new_path}`"


# Global client instance
client = VaultClient()
