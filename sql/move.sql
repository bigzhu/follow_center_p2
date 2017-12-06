--anki
INSERT INTO public.anki(
	id, created_at, updated_at, user_id, user_name, password, csrf_token, mid, cookie)
SELECT id, created_date, stat_date, user_id, user_name, password, csrf_token, mid, cookie
	FROM public_save.anki;

INSERT INTO public.oauth_info(
	id, created_at, updated_at, out_id, type, name, avatar, email, location)
SELECT id, created_date, stat_date, out_id, type, name, avatar, email, location
	FROM public_save.oauth_info;
    
INSERT INTO public.last(
	id, created_at, updated_at, user_id)
SELECT id, created_date, last_time, user_id
	FROM public_save.last;

INSERT INTO public.collect(
	id, created_at, updated_at, user_id, message_id)
SELECT id, created_date, stat_date, user_id, message_id
	FROM public_save.collect;

INSERT INTO public.message(
	id, created_at, updated_at, god_id, god_name, name, out_id, m_type, out_created_at, content, text, title, extended_entities, href, type)
SELECT id, created_date, stat_date, god_id, god_name, name, id_str, m_type, created_at, content, text, title, extended_entities, href, type
	FROM public_save.message;

INSERT INTO public.anki_save(
	id, created_at, updated_at, user_id, message_id)
SELECT id, created_date, stat_date, user_id, message_id
	FROM public_save.anki_save where message_id in (select id from message);

INSERT INTO public.god(
	id, created_at, updated_at, name, bio, twitter, github, instagram, tumblr, facebook, cat, is_public, is_black)
SELECT id, created_date, stat_date, name, bio, twitter, github, instagram, tumblr, facebook, cat, is_public, is_black
	FROM public_save.god;

INSERT INTO public.follow_who(
	id, created_at, updated_at, user_id, god_id)
SELECT id, created_date, stat_date, user_id, god_id
	FROM public_save.follow_who;

INSERT INTO public.remark(
	id, created_at, updated_at, user_id, god_id, remark)
SELECT id, created_date, stat_date, user_id, god_id, remark
	FROM public_save.remark;

update god set who_add = (select user_id from public_save.god g2 where g2.name=god.name)
