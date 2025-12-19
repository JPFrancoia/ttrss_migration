from functools import lru_cache
from importlib.resources import files
import logging
from typing import LiteralString, cast

from psycopg import AsyncConnection
from psycopg.rows import DictRow, dict_row
from psycopg_pool import AsyncConnectionPool

from migration import config
from migration.entities import TTRSSArticle

logger = logging.getLogger(__name__)


# For explanation about type hinting, see:
# https://www.psycopg.org/psycopg3/docs/advanced/typing.html#generic-pool-types
ttrss_global_pool = AsyncConnectionPool(
    config.TTRSS_DATABASE_URL,
    open=False,
    connection_class=AsyncConnection[DictRow],  # provides type hints
    kwargs={
        "row_factory": dict_row,
    },
    max_size=10,
    max_lifetime=10 * 60,
    max_idle=5 * 60,
)

miniflux_global_pool = AsyncConnectionPool(
    config.MINIFLUX_DATABASE_URL,
    open=False,
    connection_class=AsyncConnection[DictRow],  # provides type hints
    kwargs={
        "row_factory": dict_row,
    },
    max_size=10,
    max_lifetime=10 * 60,
    max_idle=5 * 60,
)


# We limit the maxsize to prevent any foot gun
@lru_cache(maxsize=100)
def _get_query_from_file(filename: str) -> LiteralString:
    query = files("migration.data_registry.sql").joinpath(filename).read_text().strip()

    query = cast(LiteralString, query)

    return query


async def get_all_ttrss_articles() -> list[TTRSSArticle]:
    query = _get_query_from_file("get_all_ttrss_articles.sql")

    async with ttrss_global_pool.connection() as conn, conn.cursor() as cur:
        await cur.execute(query)
        data = await cur.fetchall()

    return [TTRSSArticle(**dict(article)) for article in data]
