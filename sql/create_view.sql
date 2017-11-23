

drop VIEW all_message;

 CREATE VIEW all_message AS
 select * from (
 SELECT m.id,
    m.god_id,
    m.god_name,
    m.name,
    m.out_id,
    m.m_type,
    m.out_created_at,
    m.created_at,
    m.content,
    m.text,
    m.extended_entities,
    m.href,
    m.type,
    g.cat,
    case 
        when m.m_type = 'twitter' then g.twitter-> 'avatar'
        when m.m_type = 'github' then g.github-> 'avatar'
        when m.m_type = 'instagram' then g.instagram-> 'avatar'
        when m.m_type = 'tumblr' then g.tumblr-> 'avatar'
        when m.m_type = 'facebook' then g.facebook-> 'avatar'
    end as avatar,
    case 
        when m.m_type = 'twitter' then g.twitter-> 'name'
        when m.m_type = 'github' then g.github-> 'name'
        when m.m_type = 'instagram' then g.instagram-> 'name'
        when m.m_type = 'tumblr' then g.tumblr-> 'name'
        when m.m_type = 'facebook' then g.facebook-> 'name'
    end as social_name
   FROM message m,
    god g
  WHERE m.god_name = g.name
  ) q
  where social_name = to_jsonb(name)
