"""Test for prep function."""

from pathlib import Path
from unittest.mock import patch

from mgit.core import prep


def test_prep():
    """Test that prep calls fold_files without NameError."""
    root = Path("/tmp")
    target = "test"
    with patch("mgit.core.load_config") as mock_load, patch(
        "mgit.core.get_repos_from_config",
    ) as mock_get, patch("mgit.core.get_repo_paths") as mock_paths, patch(
        "mgit.core.fold_files",
    ) as mock_fold:
        mock_load.return_value = {"profiles": {"all": ["repo1"]}}
        mock_get.return_value = ["repo1"]
        mock_paths.return_value = [Path("/tmp/repo1")]
        # Should not raise NameError
        prep(root, target)
        mock_fold.assert_called_once()
