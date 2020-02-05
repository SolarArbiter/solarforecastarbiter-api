import hashlib
from io import BytesIO
import logging
from zipfile import ZipFile


logger = logging.getLogger(__name__)


class SigningError(Exception):
    """Exception raised when PGP signing fails"""
    pass  # pragma: no cover


def sign_doc(doc, key_id, passphrase_file):
    """
    Create an OpenGPG signature for the doc.

    Parameters
    ----------
    doc : bytes
        Message to clear-sign with OpenGPG
    key_id : str
        The key to use for signing
    passphrase_file : path
        Path to a file with the passphrase for the PGP
        key as the first line

    Returns
    -------
    signature : bytes
        The ASCII armored signature of the document.

    Raises
    ------
    SigningError
        If the document could not be signed for any reason
    """
    try:
        import gpg
        from gpg.constants.sig import mode
        from gpg import constants
    except ImportError:
        raise SigningError('Could not import gpg')
    with gpg.Context(
            armor=True,
            pinentry_mode=constants.PINENTRY_MODE_LOOPBACK
    ) as c:
        try:
            key = list(c.keylist(key_id))[0]
        except IndexError:
            raise SigningError(
                f'No key found in keyring with ID: {key_id}')
        c.signers = [key]
        c.set_passphrase_cb(
            lambda *args: open(passphrase_file, 'rb').readline())
        try:
            signed_body, _ = c.sign(doc, mode=mode.DETACH)
        except gpg.errors.GPGMEError as e:
            raise SigningError(f'Internal GPGME error: {str(e)}')
        except FileNotFoundError:
            raise SigningError('No GPG password file found')

    return signed_body


def make_hashes(doc, algs=['sha256']):
    """
    Create hashes of the document.

    Parameters
    ----------
    doc : bytes
        Document to hash.
    algs : list
        List of algorithms to use for hashes

    Returns
    -------
    dict
        Keys are the algorithm with the hash as the value
    """
    out = {}
    for alg in algs:
        h = getattr(hashlib, alg)
        out[alg] = h(doc).hexdigest()
    return out


def check_sign_zip(bytes_, filename, key_id, passphrase_file):
    """
    For a given input, compute hashes and PGP signature, then
    save everything into a zip archive

    Parameters
    ----------
    bytes_ : bytes
        Input data
    filename : str
        Filename to save data as in zip archive
    key_id : str
        PGP key to sign data with
    passphrase_file : str
        File with passphrase for the PGP key

    Returns
    -------
    io.BytesIO
        Byte stream of the zip archive
    """
    out = BytesIO()
    try:
        sig = sign_doc(bytes_, key_id, passphrase_file)
    except SigningError as e:
        logger.error('Failed to sign data: %s', e)
        sig = False
    with ZipFile(out, 'w') as z:
        z.writestr(filename, bytes_)
        for alg, hsh in make_hashes(bytes_).items():
            z.writestr(f'{alg}.txt', f'{hsh}  {filename}')
        if sig:
            z.writestr(f'{filename}.asc', sig)
    out.seek(0)
    return out
