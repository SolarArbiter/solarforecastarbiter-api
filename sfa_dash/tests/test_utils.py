import re
import subprocess
from zipfile import ZipFile


import pytest


from sfa_dash import utils


def test_sign_doc_no_gpg(mocker):
    mocker.patch.dict('sys.modules', {'gpg': None})
    inp = b'TEST BODY'
    with pytest.raises(utils.SigningError) as e:
        utils.sign_doc(inp, 'key', 'pw')
    assert 'Could not import gpg' in e.value.args[0]


def test_sign_doc_no_keys(mocker, tmpdir, monkeypatch):
    pytest.importorskip('gpg')
    monkeypatch.setenv('GNUPGHOME', str(tmpdir))
    inp = b'thebody'
    with pytest.raises(utils.SigningError) as e:
        utils.sign_doc(inp, 'key', 'pw')
    assert 'No key found in keyring' in e.value.args[0]


def test_sign_doc_invalid_key_id(mocker, tmp_path, monkeypatch):
    pytest.importorskip('gpg')
    tmp_path.chmod(0o700)
    monkeypatch.setenv('GNUPGHOME', str(tmp_path))
    subprocess.run(
            ['gpg', '--yes', '--passphrase', '', '--batch',
             '--quick-generate-key', '--pinentry-mode', 'loopback',
             "'TEST SFA <testing@solarforecastarbiter.org'"],
            check=True, capture_output=True
    )
    inp = b'thebody'
    with pytest.raises(utils.SigningError) as e:
        utils.sign_doc(inp, 'key', '')
    assert 'No key found in keyring' in e.value.args[0]


def test_sign_doc_no_pw_needed(mocker, tmp_path, monkeypatch):
    pytest.importorskip('gpg')
    tmp_path.chmod(0o700)
    monkeypatch.setenv('GNUPGHOME', str(tmp_path))
    key_create = subprocess.run(
            ['gpg', '--yes', '--passphrase', '', '--batch',
             '--quick-generate-key', '--pinentry-mode', 'loopback',
             "'TEST SFA <testing@solarforecastarbiter.org'"],
            check=True, capture_output=True
    )
    key = re.match('(?<=key ).*(?= marked)', key_create.stderr.decode())
    inp = b'thebody'
    out = utils.sign_doc(inp, key, '')
    assert out.startswith(b'-----BEGIN PGP SIGNATURE-----')
    assert out.endswith(b'-----END PGP SIGNATURE-----\n')


def test_sign_doc(mocker, tmp_path, monkeypatch):
    pytest.importorskip('gpg')
    tmp_path.chmod(0o700)
    monkeypatch.setenv('GNUPGHOME', str(tmp_path))
    passwd = b'jaljlj032904u2ojhsdf!@#43ljsdfa jsladf'
    with open(tmp_path / 'passwd', 'wb') as f:
        f.write(passwd)
    key_create = subprocess.run(
            ['gpg', '--yes', '--passphrase', passwd, '--batch',
             '--quick-generate-key', '--pinentry-mode', 'loopback',
             "'TEST SFA <testing@solarforecastarbiter.org'"],
            check=True, capture_output=True
    )
    key = re.match('(?<=key ).*(?= marked)', key_create.stderr.decode())
    inp = b'thebody'
    out = utils.sign_doc(inp, key, tmp_path / 'passwd')
    assert out.startswith(b'-----BEGIN PGP SIGNATURE-----')
    assert out.endswith(b'-----END PGP SIGNATURE-----\n')


@pytest.mark.parametrize('path,msg', [('passwd', 'Internal GPGME'),
                                      ('dne', 'No GPG password')])
def test_sign_doc_wrong_pw(mocker, tmp_path, monkeypatch, path, msg):
    pytest.importorskip('gpg')
    tmp_path.chmod(0o700)
    monkeypatch.setenv('GNUPGHOME', str(tmp_path))
    passwd = b'jaljlj032904u2ojhsdf!@#43ljsdfa jsladf'
    with open(tmp_path / 'passwd', 'wb') as f:
        f.write(b'wrong')
    key_create = subprocess.run(
            ['gpg', '--yes', '--passphrase', passwd, '--batch',
             '--quick-generate-key', '--pinentry-mode', 'loopback',
             "'TEST SFA <testing@solarforecastarbiter.org'"],
            check=True, capture_output=True
    )
    key = re.match('(?<=key ).*(?= marked)', key_create.stderr.decode())
    inp = b'thebody'
    with pytest.raises(utils.SigningError) as e:
        utils.sign_doc(inp, key, tmp_path / path)
    assert msg in e.value.args[0]


def test_make_hashes():
    doc = b'all your base are belong to us'
    out = utils.make_hashes(doc, ['sha1', 'md5', 'sha256'])
    assert out['sha1'] == '3b96fcc52617490cff3d6a8b923a1ef217c099e6'
    assert out['md5'] == '847dbeb849668d30722d8a67bced1c59'
    assert out['sha256'] == '59404c168e9cafda28f960d052a262803e9f1f7ce7a4c856c32fc53b0cc77d8d'  # NOQA


def test_check_sign_zip(mocker):
    mocker.patch('sfa_dash.utils.sign_doc',
                 return_value=b'signed')
    doc = b'all your base?'
    fname = 'mine.txt'
    out = utils.check_sign_zip(doc, fname, '', '')
    with ZipFile(out, 'r') as z:
        assert set(z.namelist()) == {'mine.txt', 'md5.txt', 'sha1.txt',
                                     'sha256.txt', 'mine.txt.asc'}
        for mem in ('md5.txt', 'sha1.txt', 'sha256.txt'):
            assert 'mine.txt' in z.read(mem).decode()


def test_check_sign_zip_sign_fail(mocker):
    mocker.patch('sfa_dash.utils.sign_doc',
                 side_effect=utils.SigningError)
    doc = b'all your base?'
    fname = 'mine.txt'
    out = utils.check_sign_zip(doc, fname, '', '')
    with ZipFile(out, 'r') as z:
        assert set(z.namelist()) == {'mine.txt', 'md5.txt', 'sha1.txt',
                                     'sha256.txt'}
