from src.auth.tokens import TokenManager


def test_token_pair_round_trip():
    manager = TokenManager("test-secret-with-at-least-thirty-two-characters", access_minutes=20, refresh_days=14)
    user = {"id": 7, "email": "user@example.com", "display_name": "Test User", "role": "user"}
    pair = manager.issue_pair(user)
    assert manager.read(pair["access_token"])["email"] == "user@example.com"
    assert manager.read(pair["refresh_token"], expected_type="refresh")["role"] == "user"
    assert manager.read(pair["refresh_token"]) is None
