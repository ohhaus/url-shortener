class RedisKeys:
    """Ключи для Redis."""

    @staticmethod
    def redirect_key(short_code: str) -> str:
        return f'redirect:{short_code}'

    @staticmethod
    def click_key(short_code: str) -> str:
        return f'clicks:{short_code}'

    @staticmethod
    def rate_limit_key(identifier: str) -> str:
        return f'rate_limit:{identifier}'

    @staticmethod
    def real_time_stats() -> str:
        return 'real_time:stats'
