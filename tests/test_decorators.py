import pytest
from sqlalchemy.exc import IntegrityError

from src.shortener.decorators import retry_on_integrity_error
from src.shortener.exceptions import ShortCodeAlreadyExists


class TestRetryOnIntegrityError:
    async def test_success_on_first_attempt(self):
        calls = 0

        @retry_on_integrity_error(max_attempts=3)
        async def func():
            nonlocal calls
            calls += 1
            return 'ok'

        result = await func()
        assert result == 'ok'
        assert calls == 1

    async def test_success_after_retry(self):
        calls = 0

        @retry_on_integrity_error(max_attempts=3)
        async def func():
            nonlocal calls
            calls += 1
            if calls < 3:
                raise IntegrityError(None, None, None)
            return 'ok'

        result = await func()
        assert result == 'ok'
        assert calls == 3

    async def test_raises_short_code_already_exists_after_max_attempts(self):
        @retry_on_integrity_error(max_attempts=3)
        async def func():
            raise IntegrityError(None, None, None)

        with pytest.raises(ShortCodeAlreadyExists):
            await func()

    async def test_custom_max_attempts(self):
        calls = 0

        @retry_on_integrity_error(max_attempts=1)
        async def func():
            nonlocal calls
            calls += 1
            raise IntegrityError(None, None, None)

        with pytest.raises(ShortCodeAlreadyExists):
            await func()

        assert calls == 1
