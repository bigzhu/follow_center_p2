--anki
INSERT INTO public.anki(
	id, created_at, updated_at, user_id, user_name, password, csrf_token, mid, cookie)
SELECT id, created_date, stat_date, user_id, user_name, password, csrf_token, mid, cookie
	FROM public_save.anki;

INSERT INTO public.oauth_info(
	id, created_at, updated_at, out_id, type, name, avatar, email, location)
SELECT id, created_date, stat_date, out_id, type, name, avatar, email, location
	FROM public_save.oauth_info;
    
