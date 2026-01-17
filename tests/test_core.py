from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from mgit.git.branch import branch
from mgit.git.commit import commit_repos
from mgit.git.foreach import foreach
from mgit.git.push import push_repos
from mgit.git.status import status
from mgit.git.tag import tag_repos
from mgit.test.sync import sync_repos
from mgit.test.test import run_tests
from mgit.fold import prep, summary


def test_branch_create():
    root = Path("/tmp/test")
    with patch('mgit.git.branch.load_config') as mock_config, \
         patch('mgit.git.branch.get_repo_paths') as mock_paths, \
         patch('mgit.git.branch.run_command') as mock_run:
        mock_config.return_value = MagicMock(profiles={'all': ['repo1']})
        mock_paths.return_value = [root / 'repo1']
        mock_run.return_value = MagicMock(returncode=0, stdout='', stderr='')
        branch(root, 'new_branch')
        mock_run.assert_called_with(['git', 'checkout', '-b', 'new_branch'], cwd=root / 'repo1')


def test_branch_delete():
    root = Path("/tmp/test")
    with patch('mgit.git.branch.load_config') as mock_config, \
         patch('mgit.git.branch.get_repo_paths') as mock_paths, \
         patch('mgit.git.branch.run_command') as mock_run:
        mock_config.return_value = MagicMock(profiles={'all': ['repo1']})
        mock_paths.return_value = [root / 'repo1']
        mock_run.return_value = MagicMock(returncode=0, stdout='', stderr='')
        branch(root, 'old_branch', delete=True)
        mock_run.assert_called_with(['git', 'branch', '-D', 'old_branch'], cwd=root / 'repo1')


def test_branch_sync():
    root = Path("/tmp/test")
    with patch('mgit.git.branch.load_config') as mock_config, \
         patch('mgit.git.branch.get_repo_paths') as mock_paths, \
         patch('mgit.git.branch.run_command') as mock_run:
        mock_config.return_value = MagicMock(profiles={'all': ['repo1', 'repo2']})
        mock_paths.return_value = [root / 'repo1', root / 'repo2']
        mock_run.side_effect = [
            MagicMock(returncode=0, stdout='main\n', stderr=''),
            MagicMock(returncode=0, stdout='', stderr=''),
            MagicMock(returncode=0, stdout='', stderr='')
        ]
        branch(root, 'dummy', sync=True)
        assert mock_run.call_count == 3


def test_foreach():
    root = Path("/tmp/test")
    with patch('mgit.git.foreach.load_config') as mock_config, \
         patch('mgit.git.foreach.get_repo_paths') as mock_paths, \
         patch('mgit.git.foreach.run_command') as mock_run:
        mock_config.return_value = MagicMock(profiles={'all': ['repo1']})
        mock_paths.return_value = [root / 'repo1']
        mock_run.return_value = MagicMock(returncode=0, stdout='', stderr='')
        foreach(root, 'echo hello')
        mock_run.assert_called_with(['echo', 'hello'], cwd=root / 'repo1')


def test_push():
    root = Path("/tmp/test")
    with patch('mgit.git.push.load_config') as mock_config, \
         patch('mgit.git.push.get_repo_paths') as mock_paths, \
         patch('mgit.git.push.run_command') as mock_run:
        mock_config.return_value = MagicMock(profiles={'all': ['repo1']})
        mock_paths.return_value = [root / 'repo1']
        mock_run.side_effect = [
            MagicMock(returncode=0, stdout='main', stderr=''),
            MagicMock(returncode=1, stdout='', stderr=''),  # No upstream
            MagicMock(returncode=0, stdout='', stderr='')  # Push with upstream
        ]
        push_repos(root)
        assert mock_run.call_count == 3


def test_status():
    root = Path("/tmp/test")
    with patch('mgit.git.status.load_config') as mock_config, \
         patch('mgit.git.status.get_repo_paths') as mock_paths, \
         patch('mgit.git.status.run_command') as mock_run, \
         patch('rich.print') as mock_print:
        mock_config.return_value = MagicMock(profiles={'all': ['repo1']})
        mock_paths.return_value = [root / 'repo1']
        mock_run.side_effect = [
            MagicMock(returncode=0, stdout='main\n', stderr=''),
            MagicMock(returncode=0, stdout='', stderr=''),
            MagicMock(returncode=0, stdout='## main...origin/main [ahead 1] \n', stderr='')
        ]
        status(root)
        mock_print.assert_called_once()


def test_tag():
    root = Path("/tmp/test")
    with patch('mgit.git.tag.load_config') as mock_config, \
         patch('mgit.git.tag.get_repo_paths') as mock_paths, \
         patch('mgit.git.tag.run_command') as mock_run:
        mock_config.return_value = MagicMock(profiles={'all': ['repo1']})
        mock_paths.return_value = [root / 'repo1']
        mock_run.return_value = MagicMock(returncode=0, stdout='', stderr='')
        tag_repos(root, 'v1.0.0', push=True)
        assert mock_run.call_count == 2  # tag and push


def test_commit_repos():
    root = Path("/tmp/test")
    with patch('mgit.git.commit.load_config') as mock_config, \
         patch('mgit.git.commit.get_repo_paths') as mock_paths, \
         patch('mgit.git.commit.run_command') as mock_run:
        mock_config.return_value = MagicMock(profiles={'all': ['repo1']})
        mock_paths.return_value = [root / 'repo1']
        mock_run.side_effect = [
            MagicMock(returncode=0, stdout='', stderr=''),  # add
            MagicMock(returncode=1, stdout='', stderr=''),  # diff --cached --quiet (has changes)
            MagicMock(returncode=0, stdout='', stderr=''),  # commit
            MagicMock(returncode=0, stdout='diff', stderr='')  # show
        ]
        commit_repos(root, all=True)
        mock_run.assert_any_call(['git', 'commit', '-m', 'Auto commit new files', '--no-edit'], cwd=root / 'repo1')


def test_sync_repos():
    root = Path("/tmp/test")
    with patch('mgit.test.sync.load_config') as mock_config, \
         patch('mgit.test.sync.get_repo_paths') as mock_paths, \
         patch('mgit.test.sync.run_command') as mock_run:
        mock_config.return_value = MagicMock(profiles={'all': ['repo1']})
        mock_paths.return_value = [root / 'repo1']
        mock_run.return_value = MagicMock(returncode=0, stdout='', stderr='')
        sync_repos(root)
        mock_run.assert_called_with(['uv', 'sync', '--dev'], cwd=root / 'repo1')


def test_run_tests():
    root = Path("/tmp/test")
    with patch('mgit.test.test.load_config') as mock_config, \
         patch('mgit.test.test.get_repo_paths') as mock_paths, \
         patch('mgit.test.test.find_matching_repos') as mock_find, \
         patch('mgit.test.test.run_command') as mock_run:
        mock_config.return_value = MagicMock(profiles={'all': ['repo1']})
        mock_paths.return_value = [root / 'repo1']
        mock_find.return_value = ['repo1']
        mock_run.return_value = MagicMock(returncode=0, stdout='', stderr='')
        run_tests(root, glob='test_*')
        mock_find.assert_called_with(['repo1'], 'test_*')
        mock_run.assert_called_with(['uv', 'run', '--active', 'pytest', '-n', 'auto'], cwd=root / 'repo1')


def test_prep():
    root = Path("/tmp/test")
    with patch('mgit.fold.load_config') as mock_config, \
         patch('mgit.fold.resolve_targets') as mock_resolve, \
         patch('mgit.fold.fold_files') as mock_fold, \
         patch('mgit.fold.run_command') as mock_run:
        mock_config.return_value = MagicMock(profiles={'all': ['repo1']})
        mock_resolve.return_value = (set(['repo1']), set())
        mock_run.return_value = MagicMock(returncode=0, stdout='', stderr='')
        prep(root, ['repo1'])
        mock_fold.assert_called()


def test_summary():
    root = Path("/tmp/test")
    with patch('mgit.fold.load_config') as mock_config, \
         patch('mgit.fold.run_command') as mock_run:
        mock_config.return_value = MagicMock(profiles={'all': ['repo1']})
        mock_run.return_value = MagicMock(returncode=0, stdout='', stderr='')
        summary(root, ['repo1'])
        mock_run.assert_called_with(['cfold', 'sum'] + [str(root / 'repo1')] + ['--output', str(root / 'summary.txt')], cwd=root)
