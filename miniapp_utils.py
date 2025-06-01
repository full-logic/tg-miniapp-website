
import datetime
import json
import random
import re
import requests

import psycopg2

conn = psycopg2.connect(dbname='dbname', user='postgres', password='passwd', host='localhost')
conn.autocommit = True


def add_count_to_miniapp_ads(ad_id, ip):
	try:
		stop = False
		with conn.cursor() as cursor:
			cursor.execute(f"SELECT statistics, data FROM miniapp_ads WHERE ad_id='{ad_id}'")
			res = cursor.fetchall()
			if res:
				cdate = str(datetime.date.today())
				statistics = res[0][0]
				data = res[0][1]
				# statistics: {"watches": {}, "watches_counter": 0}
				if not statistics.get('watches').get(cdate):
					statistics.get('watches')[cdate] = {}

				if not statistics['watches'][cdate].get(ip):
					statistics['watches'][cdate][ip] = [ad_id]
				else:
					statistics['watches'][cdate][ip].append(ad_id)
				statistics['watches_counter'] += 1

				if data.get('limit') == 'limit':
					limit_value = int(data.get('limit_value'))
					if statistics['watches_counter'] >= limit_value:
						statistics = json.dumps(statistics)
						cursor.execute(f"UPDATE miniapp_ads SET statistics = '{statistics}', activity = False WHERE ad_id='{ad_id}'")
						stop = True
				if not stop:
					statistics = json.dumps(statistics)
					cursor.execute(f"UPDATE miniapp_ads SET statistics = '{statistics}' WHERE ad_id='{ad_id}'")
			else:
				print('Error: attempt to increase counter to ad that does not exist')
	except Exception as e:
		print('ERROR (add_count_to_miniapp_ads): ', str(e))


def clear_text_variable(text):
	if "'" in text:
		text = text.replace("'", "")
	if "&#39;" in text:
		text = text.replace("&#39;", "")
	if "\\" in text:
		text = text.replace("\\", "")
	if '"' in text:
		text = text.replace('"', '')
	if ',' in text:
		text = text.replace('"',' ').replace(',', ' ')
	return text


def create_ident(dataset):
	ident = str(random.randint(0, 100000))
	while ident in dataset:
		ident = str(random.randint(0, 100000))
	return ident


def create_miniapp_ad_id():
	ads_ids = []
	with conn.cursor() as cursor:
		cursor.execute(f"SELECT ad_id FROM miniapp_ads")
		res = cursor.fetchall()
	ads_ids = [item[0] for item in res]
	return create_ident(ads_ids)


def create_miniapp_ads_identifier():
	with conn.cursor() as cursor:
		cursor.execute(f"SELECT ident FROM miniapp_ads_idents")
		res = cursor.fetchall()
		idents = [item[0] for item in res]
		new_ident = create_ident(idents)
		cursor.execute(f"INSERT INTO miniapp_ads_idents (ident, dt) VALUES ('{new_ident}', '{datetime.datetime.now()}')")
	return new_ident


def create_rec_ident():
	with conn.cursor() as cursor:
		cursor.execute("SELECT ident FROM miniapp_recomendations_results")
		res = cursor.fetchall()
	idents = [item[0] for item in res]
	return create_ident(idents)


def create_miniapp_notification_ident():
	with conn.cursor() as cursor:
		cursor.execute(f"SELECT ident FROM miniapp_notifications")
		res = cursor.fetchall()
	idents = [item[0] for item in res]
	return create_ident(idents)


def create_download_queue_ident(filetype):
	with conn.cursor() as cursor:
		cursor.execute(f"SELECT ident FROM miniapp_download_queue")
		res = cursor.fetchall()
	idents = [item[0] for item in res]
	random_number = str(random.randint(0, 500000))
	new_ident = f'{filetype}_{random_number}'
	while new_ident in idents:
		random_number = str(random.randint(0, 500000))
		new_ident = f'{filetype}_{random_number}'
	return new_ident


def create_subscribe_queue_ident(chat_id, ip, video_id):
	with conn.cursor() as cursor:
		cursor.execute(f"SELECT ident FROM miniapp_subscribe_queue")
		res = cursor.fetchall()
		idents = [item[0] for item in res]
		ident = create_ident(idents)
		cursor.execute(f"INSERT INTO miniapp_subscribe_queue (chat_id, ip, video_id, ident, dt) VALUES ('{chat_id}', '{ip}', '{video_id}', '{ident}', '{datetime.datetime.now()}')")


def get_client_ip(request):
	x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
	if x_forwarded_for:
		ip = x_forwarded_for.split(',')[0]
	else:
		ip = request.META.get('REMOTE_ADDR')
	return ip


def get_youtube_api_key_for_mini_app():
	x = ['first_api_key', 'second_api_key', 'third_api_key']
	use_key = x[random.randint(0, len(x)-1)]
	return use_key


def get_youtube_instance():
	youtube = None
	try:
		youtube = build("youtube", "v3", developerKey=get_youtube_api_key_for_mini_app())
	except Exception as e:
		print('INIT YOUTUBE ERROR: ', str(e))
	return youtube


def get_youtube_recomendations(ident, location):
	youtube = get_youtube_instance()
	videos = []
	try:
		vid_request = youtube.search().list(
			part="snippet",
			location=location,
			locationRadius="10mi",
			type="video",
			maxResults=50
		)
		vid_response = vid_request.execute()
		for item in vid_response['items']:
			tt = html.unescape(tclear_text_variable(str(item["snippet"]["title"])))
			channel_title = clear_text_variable(item["snippet"]["channelTitle"])
			videos.append({"id": item["id"]["videoId"], "title": tt, "path": "https://www.youtube.com/watch?v=" + str(item["id"]["videoId"]), 'channel_title': channel_title})
	except Exception as e:
		print('ERROR (get_youtube_recomendations): ', str(e))
		if 'quota' in str(e):
			update_youtube_api_key()
			return 'refresh'
	return videos


def get_miniapp_ads_names():
	with conn.cursor() as cursor:
		cursor.execute(f"SELECT name FROM miniapp_ads")
		res = cursor.fetchall()
	names = [item[0] for item in res]
	return names


def get_miniapp_ads_by_id(ad_id):
	try:
		with conn.cursor() as cursor:
			cursor.execute(f"SELECT * FROM miniapp_ads WHERE ad_id='{ad_id}'")
			res = cursor.fetchall()
			if res:
				result = {'statistics': res[0][3], 'data': res[0][1], 'dt': str(res[0][5].strftime('%d %b %Y, %I:%M%p')), 'name': res[0][0], 'activity': res[0][2]}
				return result
	except Exception as e:
		print('ERROR (get_miniapp_ads_by_id): ', str(e))
	return False


def get_random_active_miniapp_ads():
	try:
		with conn.cursor() as cursor:
			cursor.execute("SELECT * FROM miniapp_ads WHERE activity=True ORDER BY RANDOM() LIMIT 1")
			res = cursor.fetchall()
			data = res[0][1]
			ad_id = res[0][4]
			template = ''
			url = data.get('link') if data.get('link') else 'false'
			new_ident = create_miniapp_ads_identifier()
			if data.get('content_type') == 'banner':
				file = data.get('file')
				template = f'<img data-ident="{new_ident}" data-id="{ad_id}" class="card-img-top ad-el" src="{file}" data-url="{url}"/>'

			if data.get('content_type') == 'gif':
				file = data.get('file')
				template = f'<video data-ident="{new_ident}" autoplay loop muted width="100%" class="ads-iframe ad-el" data-id="{ad_id}" id="player" type="text/html" src="{file}" allow="encrypted-media" gesture="media" referrerpolicy="no-referrer-when-downgrade" frameborder="0" data-url="{url}"></video>'

			if data.get('content_type') == 'video':
				file = data.get('file')
				template = f'<video data-ident="{new_ident}" autoplay loop muted width="100%" class="ads-iframe ad-el" data-id="{ad_id}" id="player" type="text/html" src="{file}" gesture="media" referrerpolicy="no-referrer-when-downgrade" frameborder="0" data-url="{url}"></video>'

			if data.get('content_type') == 'button':
				text = data.get('file')
				template = f'<button data-ident="{new_ident}" data-id="{ad_id}" class="ad-button-style-one ad-el" data-url="{url}">{text}</button>'
	except Exception as e:
		print('ERROR (get_random_active_miniapp_ads): ', str(e))
	return template


def get_all_miniapp_ads_by_dt():
	with conn.cursor() as cursor:
		cursor.execute(f"SELECT * FROM miniapp_ads ORDER BY dt")
		res = cursor.fetchall()
	ads = {'ads': []}
	for item in res:
		ads['ads'].append({'name': item[0], 'data': item[1], 'activity': item[2], 'statistics': item[3], 'ad_id': item[4], 'dt': str(item[5].strftime('%d %b %Y, %I:%M%p'))})
	return ads


def get_user_location(ip):
	try:
		url = f'https://ipinfo.io/{ip}'
		res = requests.get(url, headers={
			"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36",
			'user-agent': "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36"
		})
		x = str(res.content)
		x = x[x.index('"GeoCoordinates"'):x.index("creator")]
		x =  re.findall("(\d+)", x)
		x = f"{x[0]}.{x[1]},{x[2]}.{x[3]}"
	except Exception as e:
		x = False
	return x


def get_location(ident):
	with conn.cursor() as cursor:
		cursor.execute(f"SELECT location FROM miniapp_recomendations_results WHERE ident='{ident}'")
		res = cursor.fetchall()
		if res:
			return res[0][0]
	return None


def get_random_location():
	# Kyiv, Warszawa, Astana, Berlin, Rome
	locations = ['50.4776941,30.4978725', '52.2330974,20.8966156', '51.0012852,70.8503438', '52.5069386,13.2599276', '41.9081806,12.3925274']
	return locations[random.randint(0, len(locations)-1)]


def get_user_playlists(chat_id):
	playlists_names = []
	with conn.cursor() as cursor:
		cursor.execute(f"SELECT name, dt FROM miniapp_users_playlists WHERE chat_id='{chat_id}' ORDER BY dt")
		ext_pl_res = cursor.fetchall()
		if ext_pl_res:
			for i in ext_pl_res:
				playlists_names.append({'name': i[0], 'dt': str(i[1].strftime('%d %b %Y, %I:%M%p'))})
	return playlists_names


def get_user_playlists_names(chat_id):
	playlists_names = []
	with conn.cursor() as cursor:
		cursor.execute(f"SELECT name, dt FROM miniapp_users_playlists WHERE chat_id='{chat_id}' ORDER BY dt")
		ext_pl_res = cursor.fetchall()
		if ext_pl_res:
			for i in ext_pl_res:
				playlists_names.append(i[0])
	return playlists_names


def make_youtube_search(query):
	videos = []
	youtube = get_youtube_instance()
	if youtube:
		try:
			vid_request = youtube.search().list(q=str(query), type="video", part="id, snippet", maxResults=50)
			vid_response = vid_request.execute()
			for item in vid_response['items']:
				tt = clear_text_variable(str(item["snippet"]["title"]))
				channel_title = clear_text_variable(item["snippet"]["channelTitle"])
				tt = html.unescape(tt)
				videos.append({"id": item["id"]["videoId"], "title": tt, "path": "https://www.youtube.com/watch?v=" + str(item["id"]["videoId"]), 'channel_title': channel_title})
		except Exception as e:
			print('ERROR (make_youtube_search): ', str(e))
			if 'quota' in str(e):
				update_youtube_api_key()
				return 'refresh'

	results = json.dumps({'results': videos})
	with conn.cursor() as cursor:
		cursor.execute(f"INSERT INTO miniapp_search_results (q, results, dt) VALUES ('{query}', '{results}', '{datetime.datetime.now()}')")
	return videos


def miniapp_statistics_sort_user_by_time():
	def by_max_seconds(data):
		return data['seconds']

	data = []
	full_ips = []

	with conn.cursor() as cursor:
		cursor.execute(f"SELECT ip FROM miniapp_statistics_tracking_time_full")
		full_ip_res = cursor.fetchall()
		full_ips = [item[0] for item in full_ip_res]

		cursor.execute(f"SELECT DISTINCT ip FROM miniapp_statistics_tracking_time_today")
		res = cursor.fetchall()
		if res:
			for i in res:
				ip = i[0]
				if ip in full_ips:
					try:
						full_ips.pop(full_ips.index(ip))
					except Exception as e:
						print('ERROR (miniapp_statistics_sort_user_by_time). Remove item from full_ips error: ', str(e))
				prev_val = ''
				time_val = 0
				prev_time_val = None
				cursor.execute(f"SELECT event, dt FROM miniapp_statistics_tracking_time_today where ip='{ip}' ORDER BY dt")
				ip_res = cursor.fetchall()
				for item in ip_res:
					event = item[0]
					dt = item[1]
					if event == 'start' and prev_val != 'start':
						prev_time_val = dt
					elif event == 'end' and prev_val != 'end':
						seconds = (dt - prev_time_val).seconds
						time_val += seconds
					prev_val = event

				cursor.execute(f"select all_time from miniapp_statistics_tracking_time_full where ip='{ip}'")
				full_res = cursor.fetchall()
				if full_res:
					all_time = full_res[0][0]
					time_val = int(time_val) + int(all_time)

				data.append({'seconds': time_val, 'ip': ip})
		for ip in full_ips:
			cursor.execute(f"select all_time from miniapp_statistics_tracking_time_full where ip='{ip}'")
			full_res = cursor.fetchall()
			time_val = int(full_res[0][0])
			data.append({'seconds': time_val, 'ip': ip})

		if data:
			data.sort(key=by_max_seconds)

	data = data[-5:]
	data.reverse()
	output = '<br/><br/>Top users by time on site:'
	for item in data:
		session_time = str(datetime.timedelta(seconds=item.get("seconds")))
		output += f'<br/>{item.get("ip")}: {session_time}'
	return output


def miniapp_notification(text):
	ident = create_miniapp_notification_ident()
	with conn.cursor() as cursor:
		cursor.execute(f"INSERT INTO miniapp_notifications (text, dt, ident) VALUES ('{text}', '{datetime.datetime.now()}', '{ident}')")


def miniapp_is_user_verified(chat_id, ip, source):
	with conn.cursor() as cursor:
		cursor.execute(f"SELECT chat_id FROM miniapp_user_information_storage WHERE ip='{ip}' AND chat_id='{chat_id}")
		res = cursor.fetchall()
	if res:
		return True
	miniapp_notification(f'Unmatched IP + Chat id\nIP: {ip}\nChat ID: {chat_id}\nCalled from {source}')
	return False


def miniapp_create_pagination_butch(items_q, page, result_data):
	try:
		pages_counter = divmod(len(result_data), items_q)
		if pages_counter[1] == 0:
			pages_counter = divmod(len(result_data), items_q)[0]
		else:
			pages_counter = divmod(len(result_data), items_q)[0]+1

		if not page:
			result_data = result_data[0:items_q]
		elif page == 'last':
			result_data = result_data[-items_q:]
		elif page == 'first' or int(page) == 1:
			result_data = result_data[0:items_q]
		else:
			bgn = (int(page)-1) * items_q
			end = bgn + items_q
			result_data = result_data[bgn:end]
	except Exception as e:
		print('ERROR (miniapp_create_pagination_butch). Preparing data context error: ', str(e))
	return result_data, pages_counter


def update_youtube_api_key():
        with conn.cursor() as cursor:
                cursor.execute("select * from youtube_api_key")
                parame = cursor.fetchall()
        x = ['commands/youtube_api_key_1.txt', 'commands/youtube_api_key_2.txt', 'commands/youtube_api_key_3.txt']
        key = ''
        if parame[0][0]== x[0]:
                val = random.randint(1,2)
                if val == 1:
                        key = x[1]
                if val == 2:
                        key = x[2]
        elif parame[0][0] == x[1]:
                val = random.randrange(1,4,2)
                if val == 1:
                        key = x[0]
                if val == 3:
                        key = x[2]
        elif parame[0][0] == x[2]:
                val = random.randint(2,3)
                if val == 2:
                        key = x[0]
                if val == 3:
                        key = x[1]
        with conn.cursor() as cursor:
                cursor.execute(f"UPDATE youtube_api_key SET key='{key}'")
