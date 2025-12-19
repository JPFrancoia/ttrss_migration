-- Fetch articles from TTRSS with all necessary fields for migration
-- Including entries, user_entries, feeds, tags, and labels
-- Supports pagination with LIMIT and OFFSET
with article_tags as (
    select
        ue.int_id,
        COALESCE(array_agg(t.tag_name) filter (where t.tag_name is not null), array[]::varchar[]) as tags
    from
        ttrss_user_entries ue
        left join ttrss_tags t on t.post_int_id = ue.int_id
    group by
        ue.int_id
),
article_labels as (
    select
        e.id,
        COALESCE(array_agg(l.caption) filter (where l.caption is not null), array[]::varchar[]) as labels
    from
        ttrss_entries e
        left join ttrss_user_labels2 ul on ul.article_id = e.id
        left join ttrss_labels2 l on l.id = ul.label_id
    group by
        e.id
)
select
    -- From ttrss_entries
    e.id,
    e.title,
    e.guid,
    e.link,
    e.updated,
    e.content,
    e.author,
    e.date_entered,
    e.comments,
    e.lang,
    -- From ttrss_user_entries
    ue.int_id,
    ue.feed_id,
    ue.owner_uid,
    ue.marked,
    ue.published,
    ue.unread,
    ue.last_read,
    ue.last_marked,
    ue.last_published,
    ue.score,
    ue.note,
    -- From ttrss_feeds
    f.title as feed_title,
    f.feed_url,
    -- Aggregated data
    COALESCE(at.tags, array[]::varchar[]) as tags,
    COALESCE(al.labels, array[]::varchar[]) as labels
from
    ttrss_entries e
    inner join ttrss_user_entries ue on ue.ref_id = e.id
    left join ttrss_feeds f on f.id = ue.feed_id
    left join article_tags at on at.int_id = ue.int_id
    left join article_labels al on al.id = e.id
order by
    e.id
limit %(limit)s offset %(offset)s;
