import logging
from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional, Tuple

import falcon
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from django_redis import get_redis_connection
from redis import Redis

logger = logging.getLogger("mcod-api")


# KEYS: List of Redis keys
# ARGV: List of [limit, window, limit, window...]
# Returns: {is_blocked, max_retry_after}

LUA_MULTI_RATE_LIMIT = """
local blocked = 0
local max_retry_after = 0

for i, key in ipairs(KEYS) do
    local limit_idx = (i * 2) - 1
    local window_idx = i * 2

    local limit = tonumber(ARGV[limit_idx])
    local window = tonumber(ARGV[window_idx])

    local current = redis.call('INCR', key)

    -- Scenario A: First request - start an initial window
    if current == 1 then
        redis.call('EXPIRE', key, window)

    -- Scenario B: EXACT request/occurrence which exceeds the limit
    -- We reset the time to a full window (penalty), but only ONCE.
    elseif current == limit + 1 then
        redis.call('EXPIRE', key, window)
    end

    -- Scenario C: User continues to spam (current > limit + 1)
    -- Here we DO NOT perform EXPIRE, so the time naturally counts down.

    if current > limit then
        blocked = 1
        local ttl = redis.call('TTL', key)
        if ttl > max_retry_after then
            max_retry_after = ttl
        end
    end
end

return {blocked, max_retry_after}
"""


@dataclass
class LimitConfig:
    """
    Represents a normalized rate limiting threshold.
    """

    limit: int
    time_window_in_seconds: int

    def __post_init__(self):
        if self.limit <= 0:
            raise ValueError(f"limit must be greater than 0, got {self.limit}")
        if self.time_window_in_seconds <= 0:
            raise ValueError(f"time_window_in_seconds must be greater than 0, got {self.time_window_in_seconds}")


class RateLimiter:
    """
    Rate limiter for Falcon API resources using Redis and Lua scripting.

    This implementation supports multiple concurrent time windows (e.g., per minute and per day)
    and utilizes a 'penalty' mechanism: exceeding the limit resets the window expiration,
    effectively enforcing a cooldown period.

    Key Features:
    - **Atomic Operations**: Uses Lua scripts to ensure consistency and prevent race conditions.
    - **Multi-Window Support**: Allows defining several limits in a single decorator.
    - **Fail-Open Design**: In case of Redis connectivity issues or key generation errors,
      the limiter logs an error and allows the request to proceed.
    - **Zero Overhead**: When `settings.FALCON_LIMITER_ENABLED` is False, the decorator
      returns the original method without any runtime hooks.

    ### Usage

    1. **Initialization**:
       Typically instantiated once at the app level:
       ```python
       limiter = RateLimiter(redis_con=get_redis_connection(alias="limiter"))
       ```

    2. **Endpoint Decoration**:
       Apply as a decorator to Falcon responder methods (`on_get`, `on_post`, etc.).
       The `key_gen` callable should return a unique string (e.g., based on IP or User ID).

       ```python
       def user_id_key(req):
           return str(req.context.user.id)

       class MyResource:
           @rate_limiter(limits="10/minute, 500/day", key_gen=user_id_key)
           def on_get(self, req, resp):
               resp.media = {"status": "success"}
       ```

    ### Limit Syntax
    The `limits` string accepts comma-separated values in the format `count/unit` or `count per unit`.

    **Supported Units:**
    - `s`, `second` (Seconds)
    - `m`, `minute` (Minutes)
    - `h`, `hour` (Hours)
    - `d`, `day` (Days)

    **Examples:**
    - `"5/s, 100/hour"`
    - `"10 per minute, 1000 per day"`

    ### Decorator Placement (Critical)

    **The order of decoration is strictly enforced.**

    When using this limiter with the `@versioned` decorator, you MUST place `@rate_limiter`
    **BELOW** `@versioned` (closer to the function definition).
    """

    def __init__(self, redis_con: Optional[Redis] = None) -> None:
        self.redis_con = redis_con
        if redis_con is not None:
            self.lua_script = redis_con.register_script(LUA_MULTI_RATE_LIMIT)

    @staticmethod
    def _is_identifier_valid(identifier: str) -> Tuple[bool, str]:
        if not isinstance(identifier, str):
            return False, f"Wrong identifier type: {type(identifier)}, expected str"
        if not identifier:
            return False, "Empty identifier"
        return True, ""

    def __call__(
        self,
        limits: str,
        key_gen: Callable[[falcon.Request], str],
    ) -> Callable:

        parsed_limits: List[LimitConfig] = self._parse_limits(limits)

        def internal_hook(
            req: falcon.Request,
            resp: falcon.Response,
            resource: object,
            params: Dict[str, Any],
            *args: Any,
            **kwargs: Any,
        ) -> None:

            if not settings.FALCON_LIMITER_ENABLED:
                # This check must happen at request time, not at decoration/import time.
                # The limiter decorator is applied when the resource module is imported,
                # so checking settings in __call__ would permanently freeze the limiter
                # in the state seen during import. By checking here, runtime setting
                # overrides (for example in tests) work correctly and the request is
                # simply allowed to proceed when the limiter is disabled.
                return None

            resource_name: str = resource.__class__.__name__

            try:
                identifier: str = key_gen(req)
                is_valid_identifier, msg = self._is_identifier_valid(identifier)
                if not is_valid_identifier:
                    logger.error(f"Wrong rate limiter key for resource: {resource_name}; reason: {msg}")
                    return  # Fail-open
            except Exception as e:
                logger.error(f"Rate limiter key generation failed: {e}")
                return  # Fail-open

            keys: List[str] = []
            args_list: List[int] = []
            cfg: LimitConfig
            for cfg in parsed_limits:
                key: str = f"rl:{resource_name}:{identifier}:{cfg.time_window_in_seconds}"
                keys.append(key)

                args_list.append(cfg.limit)
                args_list.append(cfg.time_window_in_seconds)

            try:
                result: List[int] = self.lua_script(keys=keys, args=args_list)
            except Exception as e:
                logger.error(f"Redis rate limiter connection error: {e}")
                return  # Fail-open

            is_blocked: bool = result[0] == 1
            retry_after: int = result[1]

            if is_blocked:
                exc_title: str = str(_("Rate limit exceeded"))
                description: str = str(_("Too many requests. Please try again later."))
                raise falcon.HTTPTooManyRequests(
                    title=exc_title,
                    description=description,
                    retry_after=retry_after,
                )

        return falcon.before(internal_hook)

    @staticmethod
    def _parse_limits(limits_str: str) -> List[LimitConfig]:
        """
        Parses a full string (e.g., "5/m, 10 per hour") into a list of LimitConfig.
        Strictly validates units: s/second, m/minute, h/hour, d/day.
        """
        unit_mapping: Dict[str, int] = {
            "s": 1,
            "second": 1,
            "m": 60,
            "minute": 60,
            "h": 3600,
            "hour": 3600,
            "d": 86400,
            "day": 86400,
        }

        configs: List[LimitConfig] = []
        # Split by comma to handle multiple limits at once
        raw_parts: List[str] = [p.strip() for p in limits_str.split(",") if p.strip()]

        for part in raw_parts:
            try:
                # Normalize 'per' to '/' and split
                clean_part: str = part.lower().replace("per", "/")
                segments: List[str] = [s.strip() for s in clean_part.split("/") if s.strip()]

                if len(segments) != 2:
                    raise ValueError

                count: int = int(segments[0])
                unit: str = segments[1]

                if unit not in unit_mapping:
                    raise ValueError(f"Unsupported unit: {unit}")

                configs.append(LimitConfig(limit=count, time_window_in_seconds=unit_mapping[unit]))

            except (ValueError, IndexError):
                allowed = ", ".join(unit_mapping.keys())
                raise ValueError(f"Invalid limit format in '{part}'. " f"Expected 'X/Y' or 'X per Y'. Valid units: {allowed}")

        if not configs:
            raise ValueError("No limits specified.")

        return configs


rate_limiter = RateLimiter(
    redis_con=get_redis_connection(alias="limiter"),
)
