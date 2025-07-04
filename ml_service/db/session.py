from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from ml_service.settings.config import PostgresConfig


def create_async_session(
    config: PostgresConfig | None = None,
    *,
    pool_size: int = 16,
    echo: bool = False,
) -> async_sessionmaker:
    """Creates an asynchronous session maker for the PostgreSQL database."""
    if config is None:
        config = PostgresConfig()
        non_autocommit_engine = create_async_engine(
            config.url,
            pool_size=pool_size,
            pool_pre_ping=True,
            echo=echo,
        )
    # The session is not autocommit, so we can use it with SQLAlchemy ORM
    # and manage transactions manually.
    # This is useful for applications that require explicit transaction control.
    # The session is not set to autoflush, so changes are not automatically flushed
    # to the database after each operation. This allows for more control over when
    # changes are persisted to the database.
    # The session is set to expire on commit, so objects are reloaded from the database
    # after a commit. This ensures that the session always has the most up-to-date data
    # after a commit operation, which is useful for applications that require the latest
    # data after a transaction is completed.
    return async_sessionmaker(
        non_autocommit_engine,
        autoflush=False,
        autocommit=False,
        expire_on_commit=False,
    )
