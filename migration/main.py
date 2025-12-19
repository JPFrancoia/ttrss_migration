import asyncio

from custom_logging import init_logging
from migration import config
from migration.data_registry import data_registry as dr


async def main():
    await dr.ttrss_global_pool.open()

    print("Fetching 100 sample articles from TTRSS...")
    articles = await dr.get_all_ttrss_articles()

    print(f"\nSuccessfully fetched {len(articles)} articles!")

    if articles:
        print("\n--- First Article Sample ---")
        first = articles[0]
        print(f"ID: {first.id}")
        print(f"Title: {first.title}")
        print(f"Feed: {first.feed_title}")
        print(f"Author: {first.author}")
        print(f"Date: {first.date_entered}")
        print(f"Unread: {first.unread}")
        print(f"Marked (starred): {first.marked}")
        print(f"Published: {first.published}")
        print(f"Tags: {first.tags}")
        print(f"Labels: {first.labels}")
        print(f"Link: {first.link[:100]}...")
        print(f"Content length: {len(first.content)} characters")

    await dr.ttrss_global_pool.close()


if __name__ == "__main__":
    init_logging(config.LOGGING_CONFIG)
    asyncio.run(main())
