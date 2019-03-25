from uuid import uuid1
import pytest
from conftest import uuid_to_bin, bin_to_uuid


@pytest.mark.parametrize('uuid', [uuid1() for i in range(5)])
def test_uuid_to_bin(cursor, uuid):
    cursor.execute('SELECT UUID_TO_BIN(%s, 1)', str(uuid))
    assert uuid_to_bin(uuid) == cursor.fetchone()[0]
    cursor.execute('SELECT BIN_TO_UUID(%s, 1)', uuid_to_bin(uuid))
    assert str(uuid) == cursor.fetchone()[0]


@pytest.mark.parametrize(
    'binid', [uuid_to_bin(uuid1()) for i in range(5)])
def test_bin_to_uuid(cursor, binid):
    cursor.execute('SELECT BIN_TO_UUID(%s, 1)', binid)
    assert str(bin_to_uuid(binid)) == cursor.fetchone()[0]
    cursor.execute('SELECT UUID_TO_BIN(%s, 1)', str(bin_to_uuid(binid)))
    assert binid == cursor.fetchone()[0]
