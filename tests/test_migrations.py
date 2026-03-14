from sqlalchemy import inspect


class TestDatabaseSchema:
    async def test_short_url_table_exists(self, db_session):
        def check(conn):
            inspector = inspect(conn.get_bind())
            assert 'short_url' in inspector.get_table_names()

        await db_session.run_sync(check)

    async def test_short_url_columns(self, db_session):
        def check(conn):
            inspector = inspect(conn.get_bind())
            columns = {col['name'] for col in inspector.get_columns('short_url')}
            assert {'short_code', 'original_url', 'clicks', 'created_at'}.issubset(columns)

        await db_session.run_sync(check)

    async def test_short_code_is_primary_key(self, db_session):
        def check(conn):
            inspector = inspect(conn.get_bind())
            pk = inspector.get_pk_constraint('short_url')
            assert 'short_code' in pk['constrained_columns']

        await db_session.run_sync(check)
