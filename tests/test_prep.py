"""Test for prep function."""
from pathlib import Path
from unittest.mock import MagicMock, patch

from mgit.prep import prep


def test_prep():
    """Test that prep runs and copies to clipboard."""
    root = Path("/tmp")
    targets = ["test"]
    with patch("mgit.utils.fold_files.pyperclip.copy") as mock_copy, patch("mgit.prep.load_config") as mock_load, patch(
        "mgit.prep.resolve_targets",
    ) as mock_resolve:
        mock_load.return_value = MagicMock(profiles={"all": ["repo1"]})
        mock_resolve.return_value = ({"repo1"}, set())
        prep(root, targets)
        assert mock_copy.called
