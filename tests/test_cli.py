"""Test for CLI."""

from unittest.mock import patch

import pytest

from mgit.cli.main import main


def test_cli_help(capsys):
    """Test CLI help output."""
    with patch("sys.argv", ["mgit", "--help"]):
        with pytest.raises(SystemExit):
            main()
        captured = capsys.readouterr()
        assert "CLI for managing multiple git repos" in captured.out
