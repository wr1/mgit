"""Apply structured JSON patches across repos.

Patch file format (JSON):
{
  "repos": {
    "repo_name": {
      "write": {
        "relative/path/to/file.py": "full file content as string"
      },
      "delete": ["relative/path/to/old.py"]
    }
  }
}
"""

import json
from pathlib import Path
from typing import Optional

from ..utils.repo_paths import get_repo_paths
from ..config import load_config
from ..utils.logger import logger
from ..utils.run_command import run_command
from ..utils.output import emit


def apply_patch(
    root: Path,
    patch_file: str,
    dry_run: bool = False,
    commit: bool = False,
    message: str = "mgit apply patch",
    fmt: str = "rich",
) -> None:
    """Apply a JSON patch file across repos."""
    patch_path = Path(patch_file) if Path(patch_file).is_absolute() else root / patch_file
    if not patch_path.exists():
        print(f"Error: patch file not found: {patch_path}")
        return

    try:
        patch = json.loads(patch_path.read_text())
    except json.JSONDecodeError as e:
        print(f"Error: invalid JSON in patch file: {e}")
        return

    if "repos" not in patch:
        print("Error: patch file must have a top-level 'repos' key")
        return

    config = load_config(root)
    results: dict[str, dict] = {}

    for repo_name, ops in patch["repos"].items():
        repo_path = root / repo_name
        if not repo_path.is_dir():
            results[repo_name] = {"status": "error", "error": "repo directory not found", "applied": [], "deleted": []}
            continue

        applied: list[str] = []
        deleted: list[str] = []
        errors: list[str] = []

        # Write files
        for rel_path, content in ops.get("write", {}).items():
            target = repo_path / rel_path
            if dry_run:
                applied.append(f"[dry-run] would write {rel_path}")
                logger.info(f"dry-run: write {repo_name}/{rel_path}")
                continue
            try:
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text(content)
                applied.append(rel_path)
                logger.info(f"Wrote {repo_name}/{rel_path}")
            except Exception as e:
                errors.append(f"write {rel_path}: {e}")
                logger.error(f"Failed to write {repo_name}/{rel_path}: {e}")

        # Delete files
        for rel_path in ops.get("delete", []):
            target = repo_path / rel_path
            if dry_run:
                deleted.append(f"[dry-run] would delete {rel_path}")
                continue
            if target.exists():
                try:
                    target.unlink()
                    deleted.append(rel_path)
                    logger.info(f"Deleted {repo_name}/{rel_path}")
                except Exception as e:
                    errors.append(f"delete {rel_path}: {e}")
            else:
                logger.warning(f"{repo_name}/{rel_path} not found, skipping delete")

        # Commit if requested
        commit_sha = None
        if commit and not dry_run and (applied or deleted):
            all_paths = list(ops.get("write", {}).keys()) + ops.get("delete", [])
            add_result = run_command(["git", "add"] + all_paths, cwd=repo_path)
            if add_result.returncode != 0:
                errors.append(f"git add failed: {add_result.stderr}")
            else:
                commit_result = run_command(["git", "commit", "-m", message, "--no-edit"], cwd=repo_path)
                if commit_result.returncode == 0:
                    sha_result = run_command(["git", "rev-parse", "--short", "HEAD"], cwd=repo_path)
                    commit_sha = sha_result.stdout.strip()
                else:
                    errors.append(f"git commit failed: {commit_result.stderr or commit_result.stdout}")

        results[repo_name] = {
            "status": "error" if errors else "ok",
            "applied": applied,
            "deleted": deleted,
            "errors": errors,
            "commit": commit_sha,
            "dry_run": dry_run,
        }

    if fmt != "rich":
        emit({"patch_file": str(patch_path), "dry_run": dry_run, "repos": results}, fmt)
        return

    # Rich terminal output
    total_ok = sum(1 for v in results.values() if v["status"] == "ok")
    total_err = sum(1 for v in results.values() if v["status"] == "error")
    prefix = "[DRY RUN] " if dry_run else ""
    for repo_name, info in results.items():
        marker = "✓" if info["status"] == "ok" else "✗"
        print(f"{marker} {prefix}{repo_name}")
        for f in info["applied"]:
            print(f"    write  {f}")
        for f in info["deleted"]:
            print(f"    delete {f}")
        if info.get("commit"):
            print(f"    committed {info['commit']}")
        for e in info.get("errors", []):
            print(f"    ERROR: {e}")
    print(f"\n{prefix}{total_ok} repos ok  {total_err} errors")
