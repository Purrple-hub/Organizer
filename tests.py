import os
import shutil
import tempfile
import pytest
from file_handler import FileHandler
from io_handler import Logger

@pytest.fixture
def temp_dir():
    d = tempfile.mkdtemp()
    yield d
    shutil.rmtree(d)

def test_organize_by_type(temp_dir):
    # Create test files
    os.makedirs(os.path.join(temp_dir, 'sub'), exist_ok=True)
    with open(os.path.join(temp_dir, 'test.txt'), 'w') as f:
        f.write('text')
    with open(os.path.join(temp_dir, 'sub', 'test.jpg'), 'w') as f:
        f.write('image')
    handler = FileHandler()
    result = handler.organize_files(temp_dir, dry_run=False)
    assert os.path.exists(os.path.join(temp_dir, 'organized_', 'Text', 'test.txt'))
    assert os.path.exists(os.path.join(temp_dir, 'organized_', 'Media', 'test.jpg'))

def test_undo(temp_dir):
    handler = FileHandler()
    with open(os.path.join(temp_dir, 'test.txt'), 'w') as f:
        f.write('text')
    handler.organize_files(temp_dir, dry_run=False)
    assert os.path.exists(os.path.join(temp_dir, 'organized_', 'Text', 'test.txt'))
    handler.undo_organization()
    assert not os.path.exists(os.path.join(temp_dir, 'organized_', 'Text', 'test.txt'))
    assert os.path.exists(os.path.join(temp_dir, 'test.txt'))

def test_deduplicate(temp_dir):
    handler = FileHandler()
    with open(os.path.join(temp_dir, 'a.txt'), 'w') as f:
        f.write('same')
    with open(os.path.join(temp_dir, 'b.txt'), 'w') as f:
        f.write('same')
    dup = handler.deduplicate(temp_dir, action='list')
    assert len(dup) == 1

def test_upload_discord_mock(mocker):
    # Mock requests.post to test webhook
    mock_post = mocker.patch('requests.post')
    mock_post.return_value.status_code = 204
    handler = FileHandler()
    handler.send_discord_webhook('https://discord.com/webhook', '/tmp')
    mock_post.assert_called_once()