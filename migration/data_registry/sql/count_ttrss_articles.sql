-- Count total number of articles in TTRSS
select
    COUNT(*)
from
    ttrss_entries e
    inner join ttrss_user_entries ue on ue.ref_id = e.id;

