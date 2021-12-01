import datetime
from conftest import newuuid, bin_to_uuid


import pymysql
import pytest


@pytest.fixture()
def add_perm(cursor, new_permission, valueset):
    # Add a permission to user0, role0 of valueset
    role_id = valueset[2][0]['id']
    org = valueset[0][0]

    def fcn(action, what):
        perm = new_permission(action, what, True, org=org)
        cursor.execute(
            'INSERT INTO role_permission_mapping (role_id, permission_id) '
            'VALUES (%s, %s)', (role_id, perm['id'])
        )
    return fcn


@pytest.fixture
def one_system_outage(cursor):
    some_uuid = bin_to_uuid(newuuid())
    start = datetime.datetime(2021, 4, 14, 12, 0)
    end = datetime.datetime(2021, 4, 14, 13, 0)

    cursor.execute(
        'CALL store_system_outage(%s, %s, %s)',
        (some_uuid,
         start.strftime('%Y-%m-%d %H:%M'),
         end.strftime('%Y-%m-%d %H:%M')
         )
    )
    return some_uuid


def test_get_system_outages(cursor):
    cursor.execute('CALL list_system_outages()')
    assert cursor.fetchall() == ()


def test_add_remove_system_otuage(cursor):
    some_uuid = bin_to_uuid(newuuid())
    start = datetime.datetime(2021, 4, 14, 12, 0)
    end = datetime.datetime(2021, 4, 14, 13, 0)

    cursor.execute(
        'CALL store_system_outage(%s, %s, %s)',
        (some_uuid,
         start.strftime('%Y-%m-%d %H:%M'),
         end.strftime('%Y-%m-%d %H:%M')
         )
    )
    cursor.execute('CALL list_system_outages()')
    outages = cursor.fetchall()
    assert len(outages) == 1
    outage = outages[0]

    assert outage[0] == some_uuid
    assert outage[1] == start
    assert outage[2] == end
    cursor.execute('CALL delete_system_outage(%s)', some_uuid)

    cursor.execute('CALL list_system_outages()')
    outages = cursor.fetchall()
    assert len(outages) == 0


def test_report_outage_no_perms(cursor, valueset, new_report):
    org = valueset[0][0]
    user = valueset[1]
    auth0_id = user[0]['auth0_id']
    report = new_report(org=org)
    report_id = bin_to_uuid(report['id'])
    some_uuid = bin_to_uuid(newuuid())
    start = datetime.datetime(2021, 4, 14, 12, 0)
    end = datetime.datetime(2021, 4, 14, 13, 0)
    with pytest.raises(pymysql.err.OperationalError):
        cursor.execute(
            "CALL store_report_outage(%s, %s, %s, %s, %s)",
            (auth0_id, report_id, some_uuid,
             start.strftime('%Y-%m-%d %H:%M'),
             end.strftime('%Y-%m-%d %H:%M'))
        )


def test_store_and_read_report_outage(cursor, valueset, new_report, add_perm):
    org = valueset[0][0]
    user = valueset[1]
    auth0_id = user[0]['auth0_id']
    add_perm("read", "reports")
    add_perm("update", "reports")
    report = new_report(org=org)
    report_id = bin_to_uuid(report['id'])
    some_uuid = bin_to_uuid(newuuid())
    start = datetime.datetime(2021, 4, 14, 12, 0)
    end = datetime.datetime(2021, 4, 14, 13, 0)
    cursor.execute(
        "CALL store_report_outage(%s, %s, %s, %s, %s)",
        (auth0_id, report_id, some_uuid,
         start.strftime('%Y-%m-%d %H:%M'),
         end.strftime('%Y-%m-%d %H:%M'))
    )
    cursor.execute(
        "CALL list_report_outages(%s, %s)",
        (auth0_id, report_id)
    )
    outages = cursor.fetchall()
    assert len(outages) == 1
    outage = outages[0]
    assert outage[0] == some_uuid
    assert outage[1] == report_id
    assert outage[2] == start
    assert outage[3] == end


def test_delete_report_outage(cursor, valueset, new_report, add_perm):
    org = valueset[0][0]
    user = valueset[1]
    auth0_id = user[0]['auth0_id']
    add_perm("read", "reports")
    add_perm("update", "reports")
    report = new_report(org=org)
    report_id = report['id']
    some_uuid = newuuid()
    start = datetime.datetime(2021, 4, 14, 12, 0)
    end = datetime.datetime(2021, 4, 14, 13, 0)
    cursor.execute(
        "INSERT INTO report_outages (id, report_id, start, end) "
        "VALUES (%s, %s, %s, %s)",
        (some_uuid, report_id,
         start.strftime('%Y-%m-%d %H:%M'),
         end.strftime('%Y-%m-%d %H:%M'))
    )
    cursor.execute(
        "SELECT * FROM report_outages WHERE report_id = %s",
        (report_id,)
    )
    assert len(cursor.fetchall()) == 1
    cursor.execute(
        "CALL delete_report_outage(%s, %s, %s)",
        (auth0_id, bin_to_uuid(report_id), bin_to_uuid(some_uuid))
    )
    cursor.execute(
        "SELECT * FROM report_outages WHERE report_id = %s",
        (report_id,)
    )
    assert len(cursor.fetchall()) == 0
