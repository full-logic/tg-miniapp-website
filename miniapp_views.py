
from miniapp_utils import *

import base64
import os

from django.http import JsonResponse, HttpResponseRedirect
from django.shortcuts import render

from googleapiclient.discovery import build

PAGES_CONST = 10


def bye_view(request):
	chat_id = request.headers.get('chatid')
	action = request.headers.get('action')
	ip = get_client_ip(request)

	with conn.cursor() as cursor:
		try:
			cursor.execute(f"SELECT event FROM miniapp_statistics_tracking_time_today WHERE ip='{ip}' ORDER BY dt DESC")
			res = cursor.fetchall()
			if res:
				last_rec = res[0][0]
				if last_rec == 'start':
					cursor.execute(f"INSERT INTO miniapp_statistics_tracking_time_today (ip, event, dt) VALUES ('{ip}', 'end', '{str(datetime.datetime.now())}')")
				elif last_rec == 'end':
					pass
		except Exception as e:
			print('ERROR (bye view): ', str(e))
	context = {}
	response = JsonResponse(context)
	return response


def hello_view(request):
	chat_id = request.headers.get('chatid')
	ip = get_client_ip(request)
	autoplay = False
	try:
		with conn.cursor() as cursor:
			cursor.execute(f"SELECT * FROM miniapp_user_information_storage WHERE chat_id='{chat_id}' AND ip='{ip}'")
			res = cursor.fetchall()
			if not res:
				miniapp_notification(f'ADD A NEW USER {ip} | {chat_id}')
				cursor.execute(f"INSERT INTO miniapp_user_information_storage (chat_id, ip, dt) VALUES ('{chat_id}', '{ip}', '{datetime.datetime.now()}')")

			try:
				# USER'S STATISTICS: tracking time on the site
				cursor.execute(f"SELECT event, dt FROM miniapp_statistics_tracking_time_today WHERE ip='{ip}' ORDER BY dt DESC")
				res = cursor.fetchall()
				if res:
					last_rec = res[0][0]
					if last_rec == 'start':
						dt = res[0][1]
						cursor.execute(f"DELETE FROM miniapp_statistics_tracking_time_today WHERE ip='{ip}' AND event='start' AND dt='{dt}'")
						cursor.execute(f"INSERT INTO miniapp_statistics_tracking_time_today (ip, event, dt) VALUES ('{ip}', 'start', '{str(datetime.datetime.now())}')")
					elif last_rec == 'end':
						cursor.execute(f"INSERT INTO miniapp_statistics_tracking_time_today (ip, event, dt) VALUES ('{ip}', 'start', '{str(datetime.datetime.now())}')")
				else:
					cursor.execute(f"INSERT INTO miniapp_statistics_tracking_time_today (ip, event, dt) VALUES ('{ip}', 'start', '{str(datetime.datetime.now())}')")

				# NEW USER: if user is new - create unique user-today record
				cursor.execute(f"SELECT * FROM miniapp_statistics_new_users_full WHERE ip='{ip}'")
				resone = cursor.fetchall()
				if not resone:
					cursor.execute(f"INSERT INTO miniapp_statistics_new_users_today (ip, chat_id, dt) VALUES ('{ip}', '{chat_id}', '{datetime.datetime.now()}')")
					cursor.execute(f"INSERT INTO miniapp_statistics_new_users_full (ip, chat_id, dt) VALUES ('{ip}', '{chat_id}', '{datetime.datetime.now()}')")

				# VISITS: if user visit site today IN THE first time - write for visited today OR put him on repeated visits today
				cursor.execute(f"SELECT * FROM miniapp_statistics_site_visits_unique_today WHERE ip='{ip}'")
				ures = cursor.fetchall()
				if ures:
					# insert into repeated visits
					cursor.execute(f"INSERT INTO miniapp_statistics_site_visits_repeated_today (ip, chat_id, dt) VALUES ('{ip}', '{chat_id}', '{datetime.datetime.now()}')")
				else:
					# unique visit
					cursor.execute(f"INSERT INTO miniapp_statistics_site_visits_unique_today (ip, chat_id, dt) VALUES ('{ip}', '{chat_id}', '{datetime.datetime.now()}')")

			except Exception as e:
				print('ERROR (hello_view). Statistics operations: ', str(e))

			cursor.execute(f"SELECT autoplay FROM miniapp_autoplay_cache WHERE chat_id = '{chat_id}'")
			res = cursor.fetchall()
			if res:
				autoplay = res[0][0]

	except Exception as e:
		print('ERROR (hello_view): ', str(e))

	context = {'autoplay': autoplay}
	response = JsonResponse(context)
	return response


def init_view(request):
	return render(request, 'miniapp.html', {})


def miniapp_admin(request):
	action = request.headers.get('action')
	ip = get_client_ip(request)
	context = {}
	try:
		if not action:
			with conn.cursor() as cursor:
				cursor.execute(f"SELECT dt FROM miniapp_admins_sessions WHERE ip='{ip}' ORDER BY dt")
				res = cursor.fetchall()
				if res:
					miniapp_notification('User logged in into administrator profile: ' + str(ip))
					return render(request, 'miniapp_admin.html', context)
				else:
					return HttpResponseRedirect('/')

		if action:
			if action == 'upload-file':
				content = request.headers.get('content')
				file = request.FILES.get('file')
				with open('/home/malcolm/u2btgbot/u2bapp/' + str(file), 'wb') as dest:
					for chunk in file.chunks():
						dest.write(chunk)

			elif action == 'get-statistics':
				output = '== MiniApp statistics ==<br/><br/>'
				with conn.cursor() as cursor:
					# Number of new users today | new users are recorded in two tables at once, no need to add variables
					cursor.execute("SELECT ip, chat_id, dt FROM miniapp_statistics_new_users_today")
					ares = cursor.fetchall()
					cursor.execute("SELECT ip, chat_id, dt FROM miniapp_statistics_new_users_full")
					bres = cursor.fetchall()
					output += f"Number of new users today: {len(ares)} ({len(bres)})<br/>"

					# Visits to the site. Unique
					cursor.execute("SELECT ip, chat_id, dt FROM miniapp_statistics_site_visits_unique_today")
					cres = cursor.fetchall()
					cursor.execute("SELECT data FROM miniapp_statistics_site_visits_unique_full")
					dres = cursor.fetchall()
					dres = dres[0][0].get('data')
					# Repeated
					cursor.execute("SELECT ip, chat_id, dt FROM miniapp_statistics_site_visits_repeated_today")
					eres = cursor.fetchall()
					eres_data = {}
					if eres:
						for item in eres:
							ip = item[0]
							if eres_data.get(ip):
								eres_data[ip] += 1
							else:
								eres_data[ip] = 1
					eres_unique = len(eres_data.keys())
					eres_total = 0
					for k in eres_data.keys():
						eres_total += eres_data[k]
					cursor.execute("SELECT data FROM miniapp_statistics_site_visits_repeated_full")
					fres = cursor.fetchall()
					fres_data = fres[0][0]
					fres_unique = len(fres_data.keys())
					fres_total = 0
					for k in fres_data.keys():
						fres_total += fres_data[k]
					dres = len(cres) + len(dres)
					fres = len(eres) + len(fres)
					output += f"<br/>Visits to the site today:<br/>Unique: {len(cres)} ({dres})"
					output += f"<br/>Repeated. Today: {eres_unique}/{eres_total} | All the time (except today) {fres_unique}/{fres_total}<br/>"

					# Video plays (unique videos)
					cursor.execute("SELECT ip, chat_id FROM miniapp_statistics_videos_opened_today")
					gres = cursor.fetchall()
					cursor.execute("SELECT data FROM miniapp_statistics_videos_opened_full")
					hres = cursor.fetchall()
					data = hres[0][0]
					hcounter = 0
					if data.get('counter'):
						hcounter = int(data.get('counter'))
					hres = len(gres) + hcounter
					output += f"<br/>Video plays (unique videos): {len(gres)} ({hres})"

					# Transitions to a specific menu button
					output += '<br/><br/>Transitions to a specific menu button:'
					cursor.execute("SELECT button, ip, chat_id, dt FROM miniapp_statistics_main_navigation_today")
					ires = cursor.fetchall()
					today_data_map = {}
					data_map = {}
					for item in ires:
						button = item[0]
						if not today_data_map.get(button):
							today_data_map[button] = 0
						today_data_map[button] += 1
					for k in today_data_map.keys():
						k_ident = k.capitalize() if k else None
						if k_ident:
							output += f"<br/>{k_ident}: {today_data_map.get(k)}"

					output += '<br/><br/>Menu button clicks for all time:'
					cursor.execute("SELECT button, q FROM miniapp_statistics_main_navigation_full")
					jres = cursor.fetchall()
					for item in jres:
						button = item[0]
						q = int(item[1])
						data_map[button] = q

					for k in today_data_map.keys():
						if today_data_map.get(k) and not data_map.get(k):
							k_ident = k.capitalize() if k else None
							if k_ident:
								output += f"<br/>{k_ident}: {today_data_map.get(k)}"

					for k in data_map.keys():
						counter = 0
						if today_data_map.get(k):
							counter = today_data_map.get(k)
						full = data_map.get(k) + counter
						k_ident = k.capitalize() if k else None
						if k_ident:
							output += f"<br/>{k_ident}: {full}"

					# Number of searches
					cursor.execute("SELECT query, ip, chat_id, dt FROM miniapp_statistics_searches_today")
					kres = cursor.fetchall()
					cursor.execute("SELECT data FROM miniapp_statistics_searches_full")
					lres = cursor.fetchall()
					lres = int(lres[0][0].get('counter'))
					full = len(kres) + lres
					output += f'<br/><br/>Search statistics: {len(kres)} ({full})'

					output += '<br/><br/>Buttons under the video:'
					# Download Audio: Today (All Time)
					cursor.execute("SELECT * FROM miniapp_statistics_download_audio_today")
					mres = cursor.fetchall()
					cursor.execute("SELECT data FROM miniapp_statistics_download_audio_full")
					nres = cursor.fetchall()
					nres = int(nres[0][0].get('counter'))
					full = len(mres) + nres
					output += f'<br/>Download audio: {len(mres)} ({full})'

					# Download Video: Today (All Time)
					cursor.execute("SELECT * FROM miniapp_statistics_download_video_today")
					ores = cursor.fetchall()
					cursor.execute("SELECT data FROM miniapp_statistics_download_video_full")
					pres = cursor.fetchall()
					pres = int(pres[0][0].get('counter'))
					full = len(ores) + pres
					output += f'<br/>Download video: {len(ores)} ({full})'

					# Add to playlist: Today (All Time)
					cursor.execute("SELECT * FROM miniapp_statistics_add_to_playlist_today")
					qres = cursor.fetchall()
					cursor.execute("SELECT data FROM miniapp_statistics_add_to_playlist_full")
					rres = cursor.fetchall()
					rres = int(rres[0][0].get('counter'))
					full = len(qres) + rres
					output += f'<br/>Add to playlist: {len(qres)} ({full})'

					# Subscribe: Today (All Time)
					cursor.execute("SELECT * FROM miniapp_statistics_subscribe_today")
					sres = cursor.fetchall()
					cursor.execute("SELECT data FROM miniapp_statistics_subscribe_full")
					tres = cursor.fetchall()
					tres = int(tres[0][0].get('counter'))
					full = len(sres) + tres
					output += f'<br/>Subscribe: {len(sres)} ({full})'

					# Top by time
					output += miniapp_statistics_sort_user_by_time()
					context = {'statistics': output}
					response = JsonResponse(context)
					return response

			elif action == 'get-all-ads':
				with conn.cursor() as cursor:
					cursor.execute("SELECT * FROM miniapp_ads")
					res = cursor.fetchall()
				ads = {'ads': []}
				for item in res:
					inst = {'name': item[0], 'data': item[1], 'activity': item[2], 'statistics': item[3], 'ad_id': item[4], 'dt': str(item[5].strftime('%d %b %Y, %I:%M%p'))}
					ads['ads'].append(inst)
				context = {'ads': get_all_miniapp_ads_by_dt()}
				response = JsonResponse(context)
				return response

			elif action == 'open-ads':
				response = JsonResponse({'ads': get_miniapp_ads_by_id(request.headers.get('id'))})
				return response

			elif action == 'remove-ads':
				ad_id = request.headers.get('id')
				context = {'success': True}
				try:
					with conn.cursor() as cursor:
						cursor.execute(f"SELECT data FROM miniapp_ads WHERE ad_id='{ad_id}'")
						res = cursor.fetchall()
						data = res[0][0]
						filename = data.get('file')
						os.system(f'rm /home/malcolm/u2btgbot{filename}')
						cursor.execute(f"DELETE FROM miniapp_ads WHERE ad_id='{ad_id}'")
				except Exception as e:
					print('ERROR (removing ad): ', str(e))
					context['success'] = False
				print("AD remove: ", ad_id)
				context['ads'] = get_all_miniapp_ads_by_dt()
				response = JsonResponse(context)
				return response

			elif action == 'create-ads':
				name = request.POST.get('name')
				link = request.POST.get('link')
				limit = request.POST.get('limit')
				limit_value = None
				file = None

				if limit == 'limit':
					limit_value = request.POST.get('limit_value')

				activity = request.POST.get('activity')
				content_type = request.POST.get('content_type')
				if content_type == 'button':
					file = request.POST.get('file')
				else:
					file = request.FILES.get('file')
					with open('/home/malcolm/u2btgbot/static/miniapp_ads/' + str(file), 'wb') as dest:
						for chunk in file.chunks():
							dest.write(chunk)
					file = '/static/miniapp_ads/' + str(file)

				true_showns = []
				showns = json.loads(request.POST.get('showns'))
				for k in showns.keys():
					if showns.get(k) == True:
						true_showns.append(k)

				# Exceptions handle
				exc = []
				if not name:
					exc.append('You have not entered an ad name.')
				else:
					if name in get_miniapp_ads_names():
						exc.append('An ad with this name already exists.')
					if len(name) > 299:
						exc.append('Ad name is too long. Limit: 299 characters.')
				if not limit:
					exc.append('You have not set a limit value.')
				if limit == 'limit' and not limit_value:
					exc.append('You have set a limit value, but have not specified the limit itself in numerical form.')
				if limit == 'limit':
					try:
						int(limit_value)
					except:
						exc.append('You have set a limit value, but have not specified the limit itself in numerical form.')
				if not content_type:
					exc.append('You have not selected what content will be presented in the advertisement.')
				if content_type != 'button' and file is None:
					exc.append('You specified content, but the corresponding file was not found.')
				if content_type == 'button' and file is None:
					exc.append('You specified that the content will be a button, but you did not add text for it.')
				if not true_showns:
					exc.append('You have not specified any locations where the ad will be displayed.')

				if exc:
					context['success'] = False
					err_output = 'Creation error!'
					for e in exc:
						err_output += '<br/>- ' + str(e)
					context['error'] = err_output
				else:
					ad_data = {'name': name, 'link': link if link else False, 'limit': limit, 'content_type': content_type, 'file': file}
					if limit_value:
						ad_data['limit_value'] = limit_value

					if 'anywhere' in true_showns:
						ad_data['shown'] = ['anywhere']
					else:
						ad_data['shown'] = true_showns

					ad_id = create_miniapp_ad_id()
					data = json.dumps(ad_data)
					ad_statistics = json.dumps({'watches': {}, 'watches_counter': 0, 'clicks': 0})
					dt = datetime.datetime.now()
					with conn.cursor() as cursor:
						cursor.execute(f"INSERT INTO miniapp_ads (name, data, activity, statistics, ad_id, dt) VALUES ('{name}', '{data}', {activity}, '{ad_statistics}', '{ad_id}', '{dt}')")
					context['success'] = True

				context['ads'] = get_all_miniapp_ads_by_dt()
	except Exception as e:
		if 'chunks' in str(e):
			context['success'] = False
			err_output = 'Creation error!'
		else:
			err_output = 'Creation error! No file selected.'
		context['error'] = err_output

	response = JsonResponse(context)
	return response


def miniapp_admin_authentication_view(request):
	try:
		login = request.headers.get('login')
		pwd = request.headers.get('password')
		ip = get_client_ip(request)
		context = {}
		stop = False
		with conn.cursor() as cursor:
			cursor.execute(f"SELECT * FROM miniapp_admins_ban WHERE ip='{ip}'")
			res = cursor.fetchall()
			if res:
				if len(res) > 3:
					context['success'] = False
					stop = True
					miniapp_notification(f"User try to log-in as administrator but he already blocked. IP: {ip}\nLogin: {login}\nPassword: {password}")
			if not stop:
				try:
					cursor.execute(f"SELECT * FROM miniapp_admins_credentials WHERE login='{login}' AND password='{pwd}'")
					res = cursor.fetchall()
					if res:
						cursor.execute(f"INSERT INTO miniapp_admins_sessions (ip, dt) VALUES ('{ip}', '{str(datetime.datetime.now())}')")
						return HttpResponseRedirect('/miniapp/adm')
					else:
						context['success'] = False
						cursor.execute(f"INSERT INTO miniapp_admins_ban (ip, dt) VALUES ('{ip}', '{str(datetime.datetime.now())}')")
						miniapp_notification(f"Unsuccessfull try to log-in into administrator account. IP: {ip}\nLogin: {login}\nPassword: {pwd}")
				except Exception as e:
					print('ERROR (miniapp_admin_authentication_view). Not stop then err: ', str(e))
	except Exception as e:
		print('ERROR (miniapp_admin_authentication_view): ', str(e))
		context = {}
	response = JsonResponse(context)
	return response


def miniapp_admin_hello_view(request):
	chat_id = request.headers.get('chatid')
	ip = get_client_ip(request)
	response = JsonResponse({})
	return response


def miniapp_admin_login(request):
	context = {}
	try:
		ip = get_client_ip(request)
		with conn.cursor() as cursor:
			cursor.execute(f"SELECT dt FROM miniapp_admins_sessions WHERE ip='{ip}' ORDER BY dt")
			res = cursor.fetchall()
			if res:
				return render(request, 'miniapp_admin.html', context)
	except Exception as e:
		print('ERROR (miniapp_admin_login): ', str(e))
	return render(request, 'miniapp_admin_login.html', context)


def miniapp_ads_view(request):
	ip = get_client_ip(request)
	action = request.headers.get('action')
	chat_id = request.headers.get('chatid')
	context = {}

	with conn.cursor() as cursor:
		if action:
			if action == 'get-random-ads':
				template = get_random_active_miniapp_ads()
				context['template'] = template

			elif action == 'watch':
				ad_id = request.headers.get('ad-id')
				add_count_to_miniapp_ads(ad_id, ip)

	response = JsonResponse(context)
	return response


def miniapp_autoplay_view(request):
	val = request.headers.get('autoplay')
	chat_id = request.headers.get('chatid')
	autoplay = False
	if val == 'true':
		autoplay = True
	try:
		with conn.cursor() as cursor:
			cursor.execute(f"SELECT autoplay FROM miniapp_autoplay_cache WHERE chat_id='{chat_id}'")
			res = cursor.fetchall()
			if not res:
				cursor.execute(f"INSERT INTO miniapp_autoplay_cache (chat_id, autoplay) VALUES ('{chat_id}', {autoplay})")
			else:
				cursor.execute(f"UPDATE miniapp_autoplay_cache SET autoplay = {autoplay} WHERE chat_id = '{chat_id}'")
	except Exception as e:
		print('ERROR (miniapp_autoplay_view): ', str(e))
	return JsonResponse({})


def miniapp_download_view(request):
	video_id = request.headers.get('videourl')
	chat_id = request.headers.get('chatid')
	filetype = request.headers.get('type')
	ip = get_client_ip(request)

	if not miniapp_is_user_verified(chat_id, ip, 'downloads'):
		response = JsonResponse({})
		return response

	try:
		with conn.cursor() as cursor:
			ident = create_download_queue_ident(filetype)
			cursor.execute(f"INSERT INTO miniapp_download_queue (chat_id, video_id, dt, ident) VALUES ('{chat_id}', '{video_id}', '{datetime.datetime.now()}', '{ident}')")
			print('Video inserted into a downloads queue')
			if filetype == 'audio':
				cursor.execute(f"INSERT INTO miniapp_statistics_download_audio_today (url, ip, chat_id, dt) VALUES ('{video_id}', '{ip}', '{chat_id}', '{datetime.datetime.now()}')")
			elif filetype == 'video':
				cursor.execute(f"INSERT INTO miniapp_statistics_download_video_today (url, ip, chat_id, dt) VALUES ('{video_id}', '{ip}', '{chat_id}', '{datetime.datetime.now()}')")
	except Exception as e:
		print('ERROR (miniapp_download_view): ', str(e))

	context = {'success': True}
	response = JsonResponse(context)
	return response


def miniapp_not_from_tg(request):
	try:
		return render(request, 'not_from_telegram.html', {})
	except Exception as e:
		print('ERROR (miniapp_not_from_tg): ', str(e))


def miniapp_subs_view(request):
	chat_id = request.headers.get('chatid')
	page = request.headers.get('page')
	channel = request.headers.get('channel')
	get_channels = request.headers.get('getchannels')
	action = request.headers.get('action')

	ip = get_client_ip(request)
	if not miniapp_is_user_verified(chat_id, ip, 'subscribes'):
		response = JsonResponse({})
		return response

	results = {}
	channels = []
	context = {}
	last_updates = []

	try:
		with conn.cursor() as cursor:
			which = request.headers.get('which')
			if which == 'subscribes':
				cursor.execute(f"INSERT INTO miniapp_statistics_main_navigation_today (button, ip, chat_id, dt) VALUES ('{which}', '{ip}', '{chat_id}', '{datetime.datetime.now()}')")

			context['success'] = True
			if action:
				if action == 'subscribe':
					try:
						video_id = request.headers.get('videourl')
						cursor.execute(f"INSERT INTO miniapp_statistics_subscribe_today (url, ip, chat_id, dt) VALUES ('{video_id}', '{ip}', '{chat_id}', '{datetime.datetime.now()}')")
						create_subscribe_queue_ident(chat_id, ip, video_id)
						context = {'success': True}
					except Exception as e:
						context = {'success': False}
				response = JsonResponse(context)
				return response

			if get_channels:
				subscribes_channels = []
				cursor.execute(f"SELECT channel, channel_name, url, last_videos FROM users_subscribes WHERE chat_id='{chat_id}' AND source = 'youtube'")
				subs_res = cursor.fetchall()
				for item in subs_res:
					results[channel_name] = {'url': item[2], 'channel': item[0], 'last_videos': item[3], 'channel_name': item[1]}
					channels.append({'url': item[2], 'name': item[1], 'channel': item[0]})
				context['channels'] = channels

			elif channel:
				if 'https:' not in channel:
					cursor.execute(f"SELECT channel_name, channel_url, url, dt FROM miniapp_last_subscribe_updates WHERE channel_name='{channel}' AND chat_id='{chat_id}' ORDER BY dt")
				else:
					cursor.execute(f"SELECT channel_name, channel_url, url, dt FROM miniapp_last_subscribe_updates WHERE channel_url='{channel}' AND chat_id='{chat_id}' ORDER BY dt")
				channel_last_videos_res = cursor.fetchall()
				for item in channel_last_videos_res:
					last_updates.append({'video': item[2], 'channel_name': item[0], 'channel_url': item[1], 'dt': str(item[3].strftime('%d %b %Y'))})
				context['channel_name'] = channel_name
			else:
				cursor.execute(f"SELECT channel_name, channel_url, url, dt FROM miniapp_last_subscribe_updates WHERE chat_id='{chat_id}' ORDER BY dt")
				last_videos_res = cursor.fetchall()
				for item in last_videos_res:
					last_updates.append({'video': item[2], 'channel_name': item[0], 'channel_url': item[1], 'dt': str(item[3].strftime('%d %b %Y'))})
				context['playlists_names'] = {'playlists_names': get_user_playlists(chat_id)}

	except Exception as e:
		print('ERROR (miniapp_subs_view): ', str(e))

	if last_updates:
		last_updates.reverse()

	last_updates, subscribes_pages = miniapp_create_pagination_butch(PAGES_CONST, page, last_updates)
	context['last_updates'] = last_updates
	context['subscribes_pages'] = subscribes_pages
	response = JsonResponse(context)
	return response


def miniapp_statistics_view(request):
	chat_id = request.headers.get('chatid')
	action = request.headers.get('action')
	ip = get_client_ip(request)
	try:
		with conn.cursor() as cursor:
			if action == 'click-on-ads':
				ad_id = request.headers.get('id')
				cursor.execute(f"SELECT statistics FROM miniapp_ads WHERE ad_id='{ad_id}'")
				res = cursor.fetchall()
				if res:
					statistics = res[0][0]
					statistics['clicks'] += 1
					statistics = json.dumps(statistics)
					cursor.execute(f"UPDATE miniapp_ads SET statistics = '{statistics}' WHERE ad_id='{ad_id}'")

			if action == 'open-video':
				cursor.execute(f"INSERT INTO miniapp_statistics_videos_opened_today (ip, chat_id) VALUES ('{ip}', '{chat_id}')")
	except Exception as e:
		print('ERROR (miniapp_statistics_view): ', str(e))

	context = {}
	response = JsonResponse(context)
	return response


def miniapp_search(request):
	try:
		ip = get_client_ip(request)
		page = request.headers.get('page')
		query = request.headers.get('query')
		q = base64.b64decode(query).decode('utf8').lower()
		chat_id = request.headers.get('chatid')

		if not miniapp_is_user_verified(chat_id, ip, 'search'):
			response = JsonResponse({})
			return response

		with conn.cursor() as cursor:
			if len(q) <= 299:
				cursor.execute(f"INSERT INTO miniapp_statistics_searches_today (query, ip, chat_id, dt) VALUES ('{q}', '{ip}', '{chat_id}', '{datetime.datetime.now()}')")
			today = datetime.datetime.now()
			td = today - datetime.timedelta(minutes=10)
			cursor.execute(f"SELECT results from miniapp_search_results WHERE q='{q}' AND dt < '{today}' AND dt > '{td}'")
			res = cursor.fetchall()
		if res:
			result_data = res[0][0].get('results')
		else:
			result = make_youtube_search(q)
			counter = 0
			if result == 'refresh':
				counter = 1
				while result == 'refresh' or counter < 4:
					result = make_youtube_search(q)
					counter += 1
			try:
				if result == 'refresh':
					return False

				result_data = []
				for item in result:
					#thumbnail = item.get('thumbnail')
					channel_title = item.get('channel_title')
					result_data.append({'id': item.get('id'), 'title': item.get('title'), 'url': item.get('path')})
			except Exception as e:
				print('ERROR (miniapp_search). Try to collect result data: ', str(e))

		search_results, search_results_pages = miniapp_create_pagination_butch(PAGES_CONST, page, result_data)

		context = {'search_results': search_results, 'search_results_pages': search_results_pages}
	except Exception as e:
		print('ERROR (miniapp_search): ', str(e))
		context = {}
	response = JsonResponse(context)
	return response


def miniapp_playlists(request):
	ip = get_client_ip(request)
	page = request.headers.get('page')
	chat_id = request.headers.get('chatid')
	action = request.headers.get('action')
	get_playlist = request.headers.get('getplaylist')
	sorting_playlists = request.headers.get('sorting')
	is_shuffle = request.headers.get('iss')

	if not miniapp_is_user_verified(chat_id, ip, 'playlists'):
		response = JsonResponse({})
		return response

	context = {}
	playlists = {}
	playlists_pages = 0
	playlists_names = []

	with conn.cursor() as cursor:
		which = request.headers.get('which')
		if which == 'playlists':
			cursor.execute(f"INSERT INTO miniapp_statistics_main_navigation_today (button, ip, chat_id, dt) VALUES ('{which}', '{ip}', '{chat_id}', '{datetime.datetime.now()}')")

		if action:
			if action == 'inplaylists':
				video_id = request.headers.get('videoid')
				data = []
				cursor.execute(f"SELECT playlist, name FROM miniapp_users_playlists WHERE chat_id='{chat_id}'")
				res = cursor.fetchall()
				for pl in res:
					playlist = pl[0]
					name = pl[1]
					for item in playlist.get('playlist'):
						if video_id == item.get('video_id'):
							data.append(name)
							continue
				context['playlists'] = {'playlists': data}
				cursor.execute(f"INSERT INTO miniapp_statistics_add_to_playlist_today (url, pl_name, ip, chat_id, dt) VALUES ('{video_id}', '-', '{ip}', '{chat_id}', '{datetime.datetime.now()}')")
				response = JsonResponse(context)
				return response

			if action == 'add':
				video_id = request.headers.get('videoid')
				name = base64.b64decode(request.headers.get('name')).decode('utf8')
				channel_title = base64.b64decode(request.headers.get('channeltitle')).decode('utf8')
				cursor.execute(f"SELECT playlist FROM miniapp_users_playlists WHERE chat_id='{chat_id}' AND name='{name}'")
				res = cursor.fetchall()
				if res:
					playlist = res[0][0]
					try:
						if (len(playlist.get('playlist')) + 1) >= 101:
							context['error'] = f'The "{name}" playlist already have 100 videos! For now, it is impossible to add more than a hundred.'
							response = JsonResponse(context)
							return response
					except Exception as e:
						print('ERROR (miniapp_playlists). Check playlist: ', str(e))

					playlist['playlist'].insert(0, {'video_id': video_id, 'dt': datetime.datetime.now().strftime('%d %b %Y, %I:%M%p'), 'channel_title': channel_title})
					playlist = json.dumps(playlist)
					cursor.execute(f"UPDATE miniapp_users_playlists SET playlist='{playlist}' WHERE chat_id='{chat_id}' AND name='{name}'")
				else:
					print('No res?!')
				response = JsonResponse(context)
				return response

			elif action == 'remove':
				video_id = request.headers.get('videoid')
				name = base64.b64decode(request.headers.get('name')).decode('utf8')
				cursor.execute(f"SELECT playlist, dt FROM miniapp_users_playlists WHERE chat_id='{chat_id}' AND name='{name}'")
				res = cursor.fetchall()
				success = False
				if res:
					playlist = res[0][0]
					dt = res[0][2]
					idx = None
					counter = 0
					for item in playlist.get('playlist'):
						if item.get('video_id') == video_id:
							idx = counter
							playlist.get('playlist').pop(idx)
							break
						counter += 1
					context['active_playlist'] = {'playlist': playlist, 'name': name, 'dt': dt}
					playlist = json.dumps(playlist)
					cursor.execute(f"UPDATE miniapp_users_playlists SET playlist = '{playlist}' WHERE chat_id='{chat_id}' AND name='{name}'")
					success = True
				else:
					print('No res?!')
				context['success'] = success
				response = JsonResponse(context)
				return response

			elif action == 'delete':  # delete the playlist
				name = base64.b64decode(request.headers.get('name')).decode('utf8')
				cursor.execute(f"SELECT playlist FROM miniapp_users_playlists WHERE chat_id='{chat_id}' AND name='{name}'")
				res = cursor.fetchall()
				if res:
					playlist = res[0][0]
					cursor.execute(f"DELETE FROM miniapp_users_playlists WHERE chat_id='{chat_id}' AND name='{name}'")
					context['success'] = True
				else:
					print('No res?!')

			elif action == 'create':
				name = base64.b64decode(request.headers.get('name')).decode('utf8')
				playlists_names = get_user_playlists_names(chat_id)

				# check for errors
				if len(playlists_names) > 50:
					context['success'] = False
					context['error'] = 'You have reached the limit of the number of created playlists. Before creating a new one, we recommend that you delete the old ones.'
				if len(name) > 150:
					context['success'] = False
					context['error'] = 'The playlist name is too long.'
				elif len(name) == 0:
					context['success'] = False
					context['error'] = 'Enter a name for the playlist.'
				elif name in playlists_names:
					context['success'] = False
					context['error'] = 'This name already exists.'
				else:
					playlist = json.dumps({'playlist': []})
					cursor.execute(f"INSERT INTO miniapp_users_playlists (chat_id, ip, name, dt, playlist) VALUES ('{chat_id}', '{ip}', '{name}', '{datetime.datetime.now()}', '{playlist}')")
					print('Created new playlist! Name: ', name)
					context['success'] = True

			elif action == 'getplaylists':
				playlists_names = get_user_playlists(chat_id)
				playlists_names.reverse()
				context = {'playlists_names': {'playlists_names': playlists_names}}
				if request.headers.get('init-loading') == 'true':
					main_page_updates = []
					cursor.execute(f"SELECT channel_name, channel_url, url, dt FROM miniapp_last_subscribe_updates WHERE chat_id='{chat_id}' ORDER BY dt DESC LIMIT 10")
					last_videos_res = cursor.fetchall()
					for item in last_videos_res:
						main_page_updates.append({'video': item[2], 'channel_name': item[0], 'channel_url': item[1], 'dt': str(item[3].strftime('%d %b %Y'))})
					context['main_page_subscribes'] = main_page_updates

				response = JsonResponse(context)
				return response

		elif get_playlist:
			name = base64.b64decode(request.headers.get('getplaylist')).decode('utf8')
			cursor.execute(f"SELECT * FROM miniapp_users_playlists WHERE chat_id='{chat_id}' AND name='{name}'")
			res = cursor.fetchall()
			if res:
				name = res[0][2]
				dt = res[0][3]
				playlist = res[0][4]
				context['active_playlist'] = {'name': name, 'dt': dt, 'playlist': playlist}

		shuffle_res = None
		if is_shuffle == 'shuffle' or is_shuffle == 'oldest' or is_shuffle == 'newest':
			cursor.execute(f"SELECT playlists_names FROM miniapp_playlists_shuffled_instances WHERE chat_id = '{chat_id}'")
			shuffle_res = cursor.fetchall()
		elif is_shuffle == 'delete':  # shuffle was refreshed by click on the "playlist" navigation button
			cursor.execute(f"DELETE FROM miniapp_playlists_shuffled_instances where chat_id='{chat_id}'")

		if shuffle_res:
			playlists_names = shuffle_res[0][0]
		else:  # create shuffle instance
			playlists_names = get_user_playlists(chat_id)

			if sorting_playlists:
				cursor.execute(f"DELETE FROM miniapp_playlists_shuffled_instances WHERE chat_id='{chat_id}'")
				if request.headers.get('param') == 'oldest':
					pl = json.dumps(playlists_names)
					cursor.execute(f"INSERT INTO miniapp_playlists_shuffled_instances (chat_id, playlists_names) VALUES ('{chat_id}', '{pl}')")
				if request.headers.get('param') == 'newest':
					playlists_names.reverse()
					pl = json.dumps(playlists_names)
					cursor.execute(f"INSERT INTO miniapp_playlists_shuffled_instances (chat_id, playlists_names) VALUES ('{chat_id}', '{pl}')")
				if request.headers.get('param') == 'shuffle':
					random.shuffle(playlists_names)
					pl = json.dumps(playlists_names)
					cursor.execute(f"INSERT INTO miniapp_playlists_shuffled_instances (chat_id, playlists_names) VALUES ('{chat_id}', '{pl}')")
			else:
				playlists_names.reverse()

		if not page:
			playlists_names, playlists_pages = miniapp_create_pagination_butch(PAGES_CONST, 1, playlists_names)
		elif page:
			playlists_names, playlists_pages = miniapp_create_pagination_butch(PAGES_CONST, page, playlists_names)

	context['playlists_names'] = {'playlists_names': playlists_names}
	context['playlists_pages'] = playlists_pages

	response = JsonResponse(context)
	return response


def miniapp_recomendations(request):
	try:
		ip = get_client_ip(request)
		page = request.headers.get('page')
		ident = request.headers.get('ident')
		result_data = []

		with conn.cursor() as cursor:
			which = request.headers.get('which')
			if which == 'recomendations':
				cursor.execute(f"INSERT INTO miniapp_statistics_main_navigation_today (button, ip, chat_id, dt) VALUES ('{which}', '{ip}', '-', '{datetime.datetime.now()}')")

			if not ident:
				location = get_user_location(ip)
				if not location:
					location = get_random_location()
				td = datetime.datetime.now() - datetime.timedelta(hours=2)
				cursor.execute(f"SELECT results from miniapp_recomendations_results WHERE location='{location}' AND dt > '{td}'")
				test_res = cursor.fetchall()
				if test_res:
					result_data = test_res[-1][0].get('results')
				ident = create_rec_ident()
				cursor.execute(f"INSERT INTO miniapp_rec_today_history (ip, location, datetime) VALUES ('{ip}', '{location}', '{datetime.datetime.now()}')")
			else:
				if page:
					cursor.execute(f"SELECT results, location from miniapp_recomendations_results WHERE ident='{ident}'")
					prepared_res = cursor.fetchall()
					result_data = prepared_res[0][0].get('results')
					location = prepared_res[0][1]

		if not result_data:
			result = get_youtube_recomendations(ident, location)
			counter = 0
			if result == 'refresh':
				counter = 1
				while result == 'refresh' or counter < 4:
					result = get_youtube_recomendations(ident, location)
					counter += 1
			try:
				if result == 'refresh':
					return False

				result_data = []
				for item in result:
					#thumbnail: item.get('thumbnail')
					result_data.append({'id': item.get('id'), 'title': item.get('title'), 'url': item.get('path'), 'channel_title': item.get('channel_title')})
			except Exception as e:
				print('ERROR (miniapp_recomendations). Try to collect result data: ', str(e))

		if not page:
			results = json.dumps({'results': result_data})
			with conn.cursor() as cursor:
				cursor.execute(f"INSERT INTO miniapp_recomendations_results (ident, results, location, dt) VALUES ('{ident}', '{results}', '{location}', '{datetime.datetime.now()}')")

		recomendations_results, recomendations_results_pages = miniapp_create_pagination_butch(PAGES_CONST, page, result_data)
		context = {'recomendations_results': recomendations_results, 'recomendations_results_pages': recomendations_results_pages, 'ident': ident}
	except Exception as e:
		print('ERROR (miniapp_recomendations): ', str(e))
		context = {}
	response = JsonResponse(context)
	return response
