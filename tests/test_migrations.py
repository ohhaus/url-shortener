import pytest
from sqlalchemy import inspect


@pytest.mark.slow
@pytest.mark.migrations
class TestDatabaseMigrations:
    """Тесты для проверки соответствия моделей и миграций."""

    async def test_models_match_database_schema(self, async_session):
        """Модели создают правильную схему."""
        def sync_inspect():
            inspector = inspect(async_session.get_bind())
            tables = inspector.get_table_names()
            return inspector, tables

        inspector, tables = await async_session.run_sync(
            lambda sync_session: sync_inspect()
        )
        
        assert 'short_url' in tables

        def get_columns():
            return {col['name'] for col in inspector.get_columns('short_url')}
        
        columns = await async_session.run_sync(lambda _: get_columns())
        expected_columns = {'short_code', 'original_url', 'clicks'}
        assert expected_columns.issubset(columns)

        def check_column_types():
            for column in inspector.get_columns('short_url'):
                if column['name'] == 'short_code':
                    assert isinstance(column['type'].length, int)
                    assert column['type'].length == 6
                elif column['name'] == 'original_url':
                    assert isinstance(column['type'].length, int)
                    assert column['type'].length == 2048
        
        await async_session.run_sync(lambda _: check_column_types())

    async def test_table_has_correct_constraints(self, async_session):
        """Тест ограничений таблицы."""
        def check_constraints():
            inspector = inspect(async_session.get_bind())
            
            pk_constraint = inspector.get_pk_constraint('short_url')
            assert 'short_code' in pk_constraint['constrained_columns']
            
            indexes = inspector.get_indexes('short_url')
            
        await async_session.run_sync(lambda _: check_constraints())
