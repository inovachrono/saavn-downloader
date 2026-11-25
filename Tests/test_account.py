import pytest

from scripts.helper import SaavnError
from scripts.saavnaccount import Account


def make_account(manager, responses, calls):
    account = Account(manager.session, manager, "source@example.com", "source-pw")

    def fake_call(session, call, **fields):
        calls.append(fields)
        return responses.pop(0)

    account._account_call = fake_call
    return account


def test_empty_target_password_does_not_fall_back_to_source(manager):
    calls = []
    account = make_account(manager, [{"data": {"uid": "1"}}], calls)
    account.login("target@example.com", "")
    assert calls[0]["password"] == ""
    assert calls[0]["email"] == "target@example.com"


def test_login_rejects_non_dict_response(manager):
    account = make_account(manager, [[]], [])
    with pytest.raises(SaavnError):
        account.login()


def test_login_reports_api_error(manager):
    account = make_account(manager, [{"error": {"msg": "bad password"}}], [])
    with pytest.raises(SaavnError, match="bad password"):
        account.login()
