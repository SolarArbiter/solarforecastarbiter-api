from uuid import uuid1
import pytest
from conftest import uuid_to_bin


@pytest.mark.parametrize('uuid', [uuid1() for i in range(5)])
def test_uuid_to_bin(cursor, uuid):
    cursor.execute('SELECT UUID_TO_BIN(%s, 1)', str(uuid))
    assert uuid_to_bin(uuid) == cursor.fetchone()[0]
    cursor.execute('SELECT BIN_TO_UUID(%s, 1)', uuid_to_bin(uuid))
    assert str(uuid) == cursor.fetchone()[0]
