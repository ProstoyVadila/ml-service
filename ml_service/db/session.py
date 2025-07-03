# from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

# from src.core.config.postgres import PostgresConfig


# def create_async_session(
#     cfg: PostgresConfig | None = None,
#     *,
#     pool_size: int = 15,
#     echo: bool = False,
# ) -> async_sessionmaker:
#     if cfg is None:
#         cfg = PostgresConfig()
#     non_autocommit_engine = create_async_engine(
#         cfg.get_connection_url(),
#         pool_size=pool_size,
#         pool_pre_ping=True,
#         echo=echo,
#     )

#     # TODO (k.tribunskii): place sessionmaker on module-level
#     #                      https://fhl-world.atlassian.net/browse/ML-807
#     return async_sessionmaker(
#         non_autocommit_engine,
#         autoflush=False,
#         autocommit=False,
#         expire_on_commit=False,
#     )
