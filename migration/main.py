import asyncio
import logging

from custom_logging import init_logging
from migration import config
from migration.data_registry import data_registry as dr

logger = logging.getLogger(__name__)

MINIFLUX_USER_ID = 1
MINIFLUX_DEFAULT_CATEGORY_ID = 1


async def main():
    await dr.ttrss_global_pool.open()
    await dr.miniflux_global_pool.open()

    try:
        logger.info("Starting TTRSS to Miniflux migration")

        # Fetch feeds from TTRSS
        ttrss_feeds = await dr.get_all_ttrss_feeds()
        logger.info(f"Fetched {len(ttrss_feeds)} feeds from TTRSS")

        # Fetch articles from TTRSS
        ttrss_articles = await dr.get_all_ttrss_articles()
        logger.info(f"Fetched {len(ttrss_articles)} articles from TTRSS")

        if not ttrss_articles:
            logger.warning("No articles to migrate")
            return

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
        logger.info(f"Created {len(feed_mapping)} feeds in Miniflux")

        # Convert articles
        miniflux_articles = []
        for ttrss_article in ttrss_articles:
            miniflux_feed_id = feed_mapping.get(ttrss_article.feed_url)
            if not miniflux_feed_id:
                logger.warning(
                    f"No feed mapping for {ttrss_article.feed_url}, skipping article {ttrss_article.id}"
                )
                continue

            miniflux_article = ttrss_article.to_miniflux_article(
                user_id=MINIFLUX_USER_ID, miniflux_feed_id=miniflux_feed_id
            )
            miniflux_articles.append(miniflux_article)

        logger.info(f"Converted {len(miniflux_articles)} articles")

        # Insert articles
        await dr.insert_miniflux_articles_batch(miniflux_articles)

        logger.info("Migration completed successfully")

    finally:
        await dr.ttrss_global_pool.close()
        await dr.miniflux_global_pool.close()


if __name__ == "__main__":
    init_logging(config.LOGGING_CONFIG)
    asyncio.run(main())
