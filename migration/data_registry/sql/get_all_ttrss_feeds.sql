-- Fetch all feeds from TTRSS with category information
select
    f.id,
    f.owner_uid,
    f.title,
    f.feed_url,
    f.site_url,
    f.cat_id,
    fc.title as category_title,
    f.last_updated,
    f.update_interval,
    f.order_id
from
    ttrss_feeds f
    left join ttrss_feed_categories fc on fc.id = f.cat_id
order by
    f.id;

