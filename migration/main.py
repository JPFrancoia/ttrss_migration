import asyncio
import logging

from tqdm.asyncio import tqdm

from custom_logging import init_logging
from migration import config
from migration.data_registry import data_registry as dr

logger = logging.getLogger(__name__)

MINIFLUX_USER_ID = 1
MINIFLUX_DEFAULT_CATEGORY_ID = 1
CHUNK_SIZE = 500


async def main():
    await dr.ttrss_global_pool.open()
    await dr.miniflux_global_pool.open()

    try:
        logger.info("Starting TTRSS to Miniflux migration")

        # Count total articles
        total_articles = await dr.count_ttrss_articles()
        logger.info(f"Found {total_articles} articles to migrate")

        if total_articles == 0:
            logger.warning("No articles to migrate")
            return

        # Fetch feeds from TTRSS
        ttrss_feeds = await dr.get_all_ttrss_feeds()
        logger.info(f"Fetched {len(ttrss_feeds)} feeds from TTRSS")

        # Convert and insert feeds
        miniflux_feeds = [
            feed.to_miniflux_feed(
                user_id=MINIFLUX_USER_ID, category_id=MINIFLUX_DEFAULT_CATEGORY_ID
            )
            for feed in ttrss_feeds
        ]
        await dr.insert_miniflux_feeds_batch(miniflux_feeds)
        logger.info(f"Inserted {len(miniflux_feeds)} feeds into Miniflux")

        # Fetch feeds to build mapping
        miniflux_feeds_data = await dr.get_all_miniflux_feeds(user_id=MINIFLUX_USER_ID)
        feed_mapping = {feed.feed_url: feed.id for feed in miniflux_feeds_data}

        # Migrate articles in chunks with progress bar
        articles_processed = 0
        with tqdm(
            total=total_articles, desc="Migrating articles", unit="articles"
        ) as pbar:
            async for ttrss_articles_chunk in dr.get_all_ttrss_articles(
                chunk_size=CHUNK_SIZE
            ):
                # Convert articles
                miniflux_articles = []
                for ttrss_article in ttrss_articles_chunk:
                    # Skip articles without a feed (deleted feeds)
                    if not ttrss_article.feed_url:
                        logger.debug(
                            f"Article {ttrss_article.id} has no feed (likely deleted), skipping"
                        )
                        pbar.update(1)
                        continue

                    miniflux_feed_id = feed_mapping.get(ttrss_article.feed_url)
                    if not miniflux_feed_id:
                        logger.warning(
                            f"No feed mapping for {ttrss_article.feed_url}, skipping article {ttrss_article.id}"
                        )
                        pbar.update(1)
                        continue

                    miniflux_article = ttrss_article.to_miniflux_article(
                        user_id=MINIFLUX_USER_ID, miniflux_feed_id=miniflux_feed_id
                    )
                    miniflux_articles.append(miniflux_article)

                # Insert chunk
                if miniflux_articles:
                    await dr.insert_miniflux_articles_batch(miniflux_articles)
                    articles_processed += len(miniflux_articles)
                    pbar.update(len(miniflux_articles))

        logger.info(
            f"Migration completed successfully - {articles_processed} articles migrated"
        )

    finally:
        await dr.ttrss_global_pool.close()
        await dr.miniflux_global_pool.close()


if __name__ == "__main__":
    init_logging(config.LOGGING_CONFIG)
    asyncio.run(main())
