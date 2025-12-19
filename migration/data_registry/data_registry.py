from functools import lru_cache
from importlib.resources import files
import logging
from typing import AsyncGenerator, LiteralString, cast

from psycopg import AsyncConnection
from psycopg.rows import DictRow, dict_row
from psycopg_pool import AsyncConnectionPool

from migration import config
from migration.entities import MinifluxArticle, MinifluxFeed, TTRSSArticle, TTRSSFeed

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


async def get_all_ttrss_feeds() -> list[TTRSSFeed]:
    query = _get_query_from_file("get_all_ttrss_feeds.sql")

    async with ttrss_global_pool.connection() as conn, conn.cursor() as cur:
        await cur.execute(query)
        data = await cur.fetchall()

    return [TTRSSFeed(**dict(feed)) for feed in data]


async def count_ttrss_articles() -> int:
    """Count total number of articles in TTRSS database."""
    query = _get_query_from_file("count_ttrss_articles.sql")

    async with ttrss_global_pool.connection() as conn, conn.cursor() as cur:
        await cur.execute(query)
        result = await cur.fetchone()

    return result["count"] if result else 0


async def get_all_ttrss_articles(
    chunk_size: int = 500,
) -> AsyncGenerator[list[TTRSSArticle], None]:
    """
    Fetch all TTRSS articles in chunks.
    Yields lists of TTRSSArticle objects, chunk_size articles at a time.
    """
    query = _get_query_from_file("get_all_ttrss_articles.sql")
    offset = 0

    while True:
        async with ttrss_global_pool.connection() as conn, conn.cursor() as cur:
            await cur.execute(query, {"limit": chunk_size, "offset": offset})
            data = await cur.fetchall()

        if not data:
            break

        articles = [TTRSSArticle(**dict(article)) for article in data]
        yield articles

        offset += chunk_size

        if len(articles) < chunk_size:
            break


async def insert_miniflux_feeds_batch(feeds: list[MinifluxFeed]) -> None:
    """
    Insert multiple feeds into Miniflux database using COPY.
    """
    query = _get_query_from_file("copy_miniflux_feeds.sql")

    async with (
        miniflux_global_pool.connection() as conn,
        conn.cursor() as cur,
        cur.copy(query) as copy,
    ):
        for feed in feeds:
            row = (
                feed.user_id,
                feed.category_id,
                feed.title,
                feed.feed_url,
                feed.site_url,
                feed.checked_at,
                feed.etag_header,
                feed.last_modified_header,
                feed.parsing_error_msg,
                feed.parsing_error_count,
                feed.scraper_rules,
                feed.rewrite_rules,
                feed.crawler,
                feed.username,
                feed.password,
                feed.user_agent,
                feed.disabled,
                feed.next_check_at,
                feed.ignore_http_cache,
                feed.fetch_via_proxy,
                feed.blocklist_rules,
                feed.keeplist_rules,
                feed.allow_self_signed_certificates,
                feed.cookie,
                feed.hide_globally,
                feed.url_rewrite_rules,
                feed.no_media_player,
                feed.apprise_service_urls,
                feed.disable_http2,
                feed.description,
                feed.ntfy_enabled,
                feed.ntfy_priority,
                feed.webhook_url,
                feed.pushover_enabled,
                feed.pushover_priority,
                feed.ntfy_topic,
                feed.proxy_url,
                feed.block_filter_entry_rules,
                feed.keep_filter_entry_rules,
            )
            await copy.write_row(row)

    logger.info(f"Inserted {len(feeds)} feeds in Miniflux")


async def get_all_miniflux_feeds(user_id: int) -> list[MinifluxFeed]:
    """
    Fetch all feeds from Miniflux for a specific user.
    Returns list of MinifluxFeed objects.
    """
    query = _get_query_from_file("get_all_miniflux_feeds.sql")

    async with miniflux_global_pool.connection() as conn, conn.cursor() as cur:
        await cur.execute(query, {"user_id": user_id})
        data = await cur.fetchall()

    return [MinifluxFeed(**dict(feed)) for feed in data]


async def insert_miniflux_articles_batch(articles: list[MinifluxArticle]) -> None:
    """
    Insert multiple articles into Miniflux database using COPY.
    """
    query = _get_query_from_file("copy_miniflux_articles.sql")

    async with (
        miniflux_global_pool.connection() as conn,
        conn.cursor() as cur,
        cur.copy(query) as copy,
    ):
        for article in articles:
            row = (
                article.user_id,
                article.feed_id,
                article.hash,
                article.published_at,
                article.title,
                article.url,
                article.author,
                article.content,
                article.status,
                article.starred,
                article.comments_url,
                article.changed_at,
                article.reading_time,
                article.created_at,
                article.tags,
                article.vote,
            )
            await copy.write_row(row)

    logger.info(f"Inserted {len(articles)} articles in Miniflux")
