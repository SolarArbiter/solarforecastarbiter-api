import pytest
import pandas as pd
from requests.exceptions import HTTPError


from sfa_api.utils import trial_jobs


source_index = pd.date_range(
    '2019-04-14T07:00Z',
    '2019-04-14T07:09Z',
    freq='1T'
)

source_data = pd.DataFrame(
    [(x, x) for x in range(0, 10)],
    index=source_index,
    columns=['value', 'quality_flag']
)

target_data = pd.DataFrame(
    [(0, 0)],
    index=source_index[:0],
    columns=['value', 'quality_flag']
)


@pytest.fixture()
def mock_session(mocker):
    mock_sess = mocker.MagicMock()
    mock_sess.get_observation_time_range = mocker.MagicMock(
        return_value=(
            pd.Timestamp('2019-04-14T07:00Z'),
            pd.Timestamp('2019-04-14T07:00Z')
        )
    )
    mock_sess.get_observation_values = mocker.MagicMock(
        return_value=source_data[1:]
    )
    mock_sess.post_observation_values = mocker.MagicMock(return_value=None)

    mocker.patch('sfa_api.utils.trial_jobs.APISession', return_value=mock_sess)
    return mock_sess


@pytest.fixture()
def mock_logging(mocker):
    mock_logger = mocker.MagicMock()
    mocker.patch(
        'sfa_api.utils.trial_jobs.logging.getLogger',
        return_value=mock_logger
    )
    return mock_logger


def test_copy_data(mocker, mock_session, observation_id, mock_logging):
    trial_jobs.copy_observation_data("token", observation_id, observation_id)
    mock_logging.info.assert_called_with(
        "Copied %s points from obs %s to %s.", 9,
        observation_id, observation_id
    )
    post_args = mock_session.post_observation_values.call_args_list
    post_args_df = post_args[0][0][1]
    qfs = post_args_df['quality_flag'].values
    assert (qfs == [1, 0, 1, 0, 1, 0, 1, 0, 1]).all()


def test_copy_data_no_copy_from_read(
        mocker, mock_session, observation_id):
    resp = mocker.MagicMock()
    resp.status_code = 404
    mock_session.get_observation_values = mocker.MagicMock(
        side_effect=HTTPError(response=resp)
    )
    with pytest.raises(ValueError) as e:
        trial_jobs.copy_observation_data(
            "token", observation_id, observation_id
        )
    assert "Read values failure for copy_from " in str(e.value)


def test_copy_data_no_copy_to_read(
        mocker, mock_session, observation_id):
    resp = mocker.MagicMock()
    resp.status_code = 404
    mock_session.get_observation_time_range = mocker.MagicMock(
        side_effect=HTTPError(response=resp)
    )
    with pytest.raises(ValueError) as e:
        trial_jobs.copy_observation_data(
            "token", observation_id, observation_id
        )
    assert "Read values failure for copy_to " in str(e.value)


def test_copy_data_no_copy_to_write(
        mocker, mock_session, observation_id):
    resp = mocker.MagicMock()
    resp.status_code = 404
    mock_session.post_observation_values = mocker.MagicMock(
        side_effect=HTTPError(response=resp)
    )
    with pytest.raises(ValueError) as e:
        trial_jobs.copy_observation_data(
            "token", observation_id, observation_id
        )
    assert "Write values failure for copy_to " in str(e.value)


def test_copy_data_nothing_to_copy(
        mocker, mock_session, observation_id, mock_logging):
    mock_session.get_observation_values = mocker.MagicMock(
        return_value=pd.DataFrame()
    )
    trial_jobs.copy_observation_data("token", observation_id, observation_id)
    mock_logging.info.assert_called_with(
        "No points to copy from %s to %s.", observation_id, observation_id
    )
