import pytest
from sqlalchemy import inspect


@pytest.mark.slow
class TestDatabaseMigrations:
    async def test_database_schema(self, db_session):
        def check_schema(sync_session):
            inspector = inspect(sync_session.get_bind())
            
            tables = inspector.get_table_names()
            assert "short_url" in tables
            
            columns = {col["name"] for col in inspector.get_columns("short_url")}
            expected_columns = {"short_code", "original_url", "clicks"}
            assert expected_columns.issubset(columns)
        
        await db_session.run_sync(check_schema)
