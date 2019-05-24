import pytest


def test_list_roles():
    assert req.status_code == 200


def test_list_roles_missing_perms():
    assert req.status_code == 404


def test_create_role():
    assert req.status_code == 404


def test_create_role_invalid_json():
    assert req.status_code == 404


def test_create_role_missing_perms():
    assert req.status_code == 404


def test_get_role():
    assert req.status_code == 200


def test_get_role_dne():
    assert req.status_code == 404


def test_get_role_missing_perms():
    assert req.status_code == 404


def test_delete_role():
    assert req.status_code == 204


def test_delete_role_dne():
    assert req.status_code == 404


def test_delete_role_missing_perms():
    assert req.status_code == 404


def test_add_perm_to_role():
    assert req.status_Code == 204


def test_add_perm_to_role_perm_dne():
    assert req.status_code == 404


def test_add_perm_to_role_role_dne():
    assert req.status_code == 404

def test_add_perm_to_role_missing_perm():
    # parametrize with:
    # no update role
    # to read role
    # no read permission
    assert req.status_code == 404
