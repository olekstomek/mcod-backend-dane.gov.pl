import uuid
from typing import Any, Generator, List, Tuple
from unittest.mock import MagicMock

import falcon
import pytest
from django.test import override_settings
from django_redis import get_redis_connection
from falcon import testing
from redis import Redis
from redis.commands.core import Script

from mcod.core.api.limiter import LUA_MULTI_RATE_LIMIT, LimitConfig, RateLimiter, rate_limiter
from mcod.users.models import User


class TestLimitParser:
    """
    Unit tests for the RateLimiter._parse_limits method.
    """

    @pytest.mark.parametrize(
        "input_str, expected_configs",
        [
            # Single limits
            ("10/s", [LimitConfig(limit=10, time_window_in_seconds=1)]),
            ("5/m", [LimitConfig(limit=5, time_window_in_seconds=60)]),
            ("100/hour", [LimitConfig(limit=100, time_window_in_seconds=3600)]),
            ("50 per day", [LimitConfig(limit=50, time_window_in_seconds=86400)]),
            ("  20 / minute ", [LimitConfig(limit=20, time_window_in_seconds=60)]),
            # Multi-limits (comma separated)
            ("5/s, 10/m", [LimitConfig(limit=5, time_window_in_seconds=1), LimitConfig(limit=10, time_window_in_seconds=60)]),
            (
                "1/s, 5 per minute, 100/h",
                [
                    LimitConfig(limit=1, time_window_in_seconds=1),
                    LimitConfig(limit=5, time_window_in_seconds=60),
                    LimitConfig(limit=100, time_window_in_seconds=3600),
                ],
            ),
        ],
    )
    def test_parse_valid_formats(self, input_str: str, expected_configs: List[LimitConfig]):
        # Now calling the static method from the class
        configs = RateLimiter._parse_limits(input_str)
        assert configs == expected_configs

    @pytest.mark.parametrize(
        "invalid_input",
        [
            "bad_format",
            "10/x",  # Invalid unit shorthand
            "5 per month",  # Unit not in our strict allowed list
            "10/marmolada",  # Matches first letter but should fail strict check
            "",
            "10/",
            "/m",
        ],
    )
    def test_parse_invalid_formats(self, invalid_input: str):
        with pytest.raises(ValueError):
            RateLimiter._parse_limits(invalid_input)


class TestRateLimiterIntegration:
    @pytest.fixture
    def mock_api_objects(self) -> Tuple[MagicMock, MagicMock, MagicMock]:
        req = MagicMock(spec=falcon.Request)
        resp = MagicMock(spec=falcon.Response)
        dummy_endpoint = MagicMock()
        dummy_endpoint.__class__.__name__ = "TestView"
        return req, resp, dummy_endpoint

    @pytest.fixture
    def unique_key(self) -> str:
        """Unique key generator
        Note: this ensures tests separation
        """
        return str(uuid.uuid4())

    @override_settings(FALCON_LIMITER_ENABLED=True)
    @pytest.mark.parametrize(
        ("limits", "requests_number", "retry_after"),
        (
            ("1/s", 1, "1"),
            ("3/m", 3, "60"),
            ("5/h", 5, "3600"),
            ("10/d", 10, "86400"),
            ("1/s,5/m", 1, "1"),
            ("3/m,5/h", 3, "60"),
            ("4/m,5/d", 4, "60"),
            ("5/d,4/m", 4, "60"),  # order does not matter
        ),
    )
    def test_limits_trigger_too_many_requests_with_correct_delay(
        self,
        mock_api_objects: Tuple[MagicMock, MagicMock, MagicMock],
        unique_key: str,
        limits: str,
        requests_number: int,
        retry_after: str,
    ):
        req, resp, endpoint = mock_api_objects
        decorator = rate_limiter(limits, key_gen=lambda x: unique_key)
        limited_endpoint = decorator(endpoint)

        for _ in range(requests_number):
            limited_endpoint(object(), req, resp)

        with pytest.raises(falcon.HTTPTooManyRequests) as exc:
            limited_endpoint(object(), req, resp)

        assert endpoint.call_count == requests_number
        assert exc.value.headers["Retry-After"] == retry_after

    @override_settings(FALCON_LIMITER_ENABLED=True)
    def test_redis_connection_failure_fails_open(
        self,
        unique_key: str,
        mock_api_objects: Tuple[MagicMock, MagicMock, MagicMock],
    ):
        req, resp, endpoint = mock_api_objects
        rate_limiter.lua_script = MagicMock(side_effect=Exception)

        decorator = rate_limiter("5/m", key_gen=lambda x: unique_key)
        limited_endpoint = decorator(endpoint)
        limited_endpoint(object(), req, resp)
        assert endpoint.call_count == 1

    @override_settings(FALCON_LIMITER_ENABLED=True)
    def test_key_generation_failure_fails_open(
        self,
        mock_api_objects: Tuple[MagicMock, MagicMock, MagicMock],
    ):
        req, resp, endpoint = mock_api_objects

        def broken_key_gen(req):
            raise ValueError("Something went wrong with extracting IP")

        decorator = rate_limiter("7/m", key_gen=broken_key_gen)
        limited_endpoint = decorator(endpoint)
        limited_endpoint(object(), req, resp)

        assert endpoint.call_count == 1

    @override_settings(FALCON_LIMITER_ENABLED=True)
    @pytest.mark.parametrize("key_gen_return_value", ("", None, False, True, 1, 2.0, object()))
    def test_key_generation_returns_wrong_value_fails_open(
        self,
        mock_api_objects: Tuple[MagicMock, MagicMock, MagicMock],
        key_gen_return_value: Any,
    ):
        req, resp, endpoint = mock_api_objects

        decorator = rate_limiter("7/m", key_gen=lambda x: key_gen_return_value)
        limited_endpoint = decorator(endpoint)
        limited_endpoint(object(), req, resp)

        assert endpoint.call_count == 1

    @override_settings(FALCON_LIMITER_ENABLED=True)
    def test_key_generation_wrong_definition_fails_open(
        self,
        mock_api_objects: Tuple[MagicMock, MagicMock, MagicMock],
    ):
        req, resp, endpoint = mock_api_objects

        # Key gen function with no arguments
        decorator = rate_limiter("7/m", key_gen=lambda: "key_gen_return_value")
        limited_endpoint = decorator(endpoint)
        limited_endpoint(object(), req, resp)

        assert endpoint.call_count == 1

    @pytest.mark.parametrize(
        ("limiter_enabled", "expected_status"),
        [
            (False, falcon.HTTP_401),
            (True, falcon.HTTP_429),
        ],
    )
    def test_limiter_disabled_via_settings(
        self, client: testing.TestClient, admin: User, limiter_enabled: bool, expected_status: str, clear_limiter_redis_db: None
    ):
        """
        Should allow requests to proceed without applying rate-limit checks
        when the limiter is disabled via settings.

        The limiter hook is always registered, but when
        FALCON_LIMITER_ENABLED is False it exits early at runtime.
        That means repeated failed login attempts should keep returning
        401 Unauthorized instead of being blocked with 429 Too Many Requests.
        It's a system logic test.
        """
        limit_per_minute = 3
        with override_settings(
            FALCON_LIMITER_ENABLED=limiter_enabled, FALCON_LIMITER_LOGIN_LIMITS=f"{limit_per_minute} per minute,10 per hour"
        ):
            for _ in range(limit_per_minute):
                resp = client.simulate_post(
                    path="/auth/login",
                    json={
                        "data": {
                            "type": "user",
                            "attributes": {
                                "email": admin.email,
                                "password": "wrong password",
                            },
                        }
                    },
                )

            assert resp.status == falcon.HTTP_401

            resp = client.simulate_post(
                path="/auth/login",
                json={
                    "data": {
                        "type": "user",
                        "attributes": {
                            "email": admin.email,
                            "password": "wrong password",
                        },
                    }
                },
            )

            assert resp.status == expected_status


class TestLuaRateLimiter:
    @pytest.fixture(scope="class")
    def redis_conn(self) -> Redis:
        """Connects to a real Redis instance."""
        return get_redis_connection(alias="limiter")

    @pytest.fixture(scope="class")
    def lua_script(self, redis_conn) -> Script:
        """Registers the script in Redis."""
        return redis_conn.register_script(LUA_MULTI_RATE_LIMIT)

    @pytest.fixture
    def unique_key(self, redis_conn) -> Generator[str, Any, None]:
        """Generates a unique key for every test to avoid collisions."""
        key = f"test_rl:{uuid.uuid4()}"
        yield key
        redis_conn.delete(key)  # Cleanup after test

    def test_first_request_sets_ttl(self, lua_script: Script, unique_key: str, redis_conn: Redis):
        """
        Verify that the first request initializes the counter
        and sets the expiration time.
        """
        limit, window = 5, 60
        blocked, retry_after = lua_script(keys=[unique_key], args=[limit, window])

        assert blocked == 0
        assert 50 < redis_conn.ttl(unique_key) <= window

    def test_limit_exceeded_resets_ttl(self, lua_script: Script, unique_key: str, redis_conn: Redis):
        """
        Verify that hitting the limit + 1 (first violation)
        resets the TTL to the full window (Penalty).
        """
        limit, window = 5, 60

        # 1. Fill the limit
        for _ in range(limit):
            lua_script(keys=[unique_key], args=[limit, window])

        # 2. Artificially lower the TTL to simulate time passing
        redis_conn.expire(unique_key, 10)

        # 3. Trigger the penalty (request number 6)
        blocked, retry_after = lua_script(keys=[unique_key], args=[limit, window])

        assert blocked == 1
        # TTL should be reset back to 60s instead of the 10s we set
        assert retry_after == window

    def test_spamming_does_not_reset_ttl(self, lua_script, redis_conn, unique_key):
        """
        Verify that further requests beyond the first violation
        do NOT reset the TTL again.
        """
        limit, window = 5, 60

        # 1. Trigger the penalty (6th request)
        for _ in range(limit + 1):
            lua_script(keys=[unique_key], args=[limit, window])

        # 2. Set a specific TTL
        redis_conn.expire(unique_key, 30)

        # 3. Spam again (7th request)
        blocked, retry_after = lua_script(keys=[unique_key], args=[limit, window])

        assert blocked == 1
        # TTL should still be 30s, not reset to 60s
        assert retry_after == 30
