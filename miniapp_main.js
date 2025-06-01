
const componentPagination = {
	data() {
		return {
		}
	},
	emits: ['subscribe-pagination-action', 'search-pagination-action', 'recomendations-pagination-action', 'playlists-pagination-action'],
	props: ['pages', 'section', 'current_page'],
	methods: {
		paginationAction(event) {
			if (this.section == 'subscribes') {
				this.$emit('subscribe-pagination-action', event);
			}
			if (this.section == 'search') {
				this.$emit('search-pagination-action', event);
			}
			if (this.section == 'recomendations') {
				this.$emit('recomendations-pagination-action', event);
			}
			if (this.section == 'playlists') {
				this.$emit('playlists-pagination-action', event);
			}
			window.scrollTo({top: -1, behavior: 'smooth'});
		},
		getDataItem() {
			return this.section;
		},
		isPageDrawning(op) {
			if (op == '-') {
				return parseInt(this.current_page)-1 > 0;
			}
			else if (op == '+') {
				return parseInt(this.current_page)+1 <= this.pages;
			}
		}
	},
        mounted: function() {
	},
        created: function() {
        },
	template: `
		<ul class='pagination pagination-sm pagination-md' style='display: flex; justify-content: center;' :data-item='getDataItem()'>
			<li v-if='isPageDrawning("-")' class='page-item'>
				<a href='' @click.prevent='paginationAction' :data-page='parseInt(current_page)-1' class='pagination-page left-pagination page-link'>Back</a>
			</li>
			<li class='page-item'>
				<a href='' @click.prevent :data-page='current_page' class='is-active pagination-page page-link'>{{ current_page }}</a>
			</li>
			<li v-if='isPageDrawning("+")' class='page-item'>
				<a href='' @click.prevent='paginationAction' :data-page='parseInt(current_page)+1' class='pagination-page right-pagination page-link'>Forward</a>
			</li>
		</ul>
	`
}


const componentMainPage = {
        data() {
               return {
			section: 'main',
			main_page_subscribes: [],
			subscribe_please: false,

			search_current_page: 1,
			search_results_pages: 0,
			search_container: [],
			current_query: null,

			subscribe_current_page: 1,
			subscribes_pages: 0,
			subscribes_container: {},
			subscribe_active_channel: '',
			sended_to_subscribe: [],
			subscribes_view: '',
			channels: [],

			recomendations_current_page: 1,
			recomendations_results_pages: 0,
			recomendations_container: {},
			recomendations_ident: null,

			playlists_current_page: 1,
			playlists_results_pages: 0,
			playlist_container: [],
			playlists_names: [],
			to_playlists_names: [],
			active_playlist: null,
			playlist_sorting: true,
			playlist_creation_statement: false,
			video_into_playlist: '',
			inPlaylistData: [],
			isShuffle: null,

			opened_videos: [],
			downloads: {'audio': [], 'video': []}
	        }
        },
        emits: ['clear-watched-ads-array'],
        props: [],
        methods: {
		getHeaders() {
			var csrf = $('input[name="csrfmiddlewaretoken"]').attr('value');
			var headers = {
				'Access-Control-Allow-Origin': '*',
				'withCredentials': true,
				'X-CSRFTOKEN': csrf
			}
			if (window.tg && window.tg.initDataUnsafe.user) {
				headers['chatid'] = window.tg.initDataUnsafe.user.id;
			}
			else {
				headers['chatid'] = 'no';
			}
			return headers
		},
		clearWatchedAds() {
			this.$emit('clear-watched-ads-array');
		},
		clearAds() {
			$('.ads-container').html('');
		},
		insertAds() {
			var to_ads_container = $('.to-ads-container');
			var headers = this.getHeaders();
			headers['action'] = 'get-random-ads';
			for (var i=0; i<to_ads_container.length; i++) {
				var el = $(to_ads_container[i]).find('.ads-container');
				const index = $(el).parent()[0].dataset.index;
				if ($(el).html() == '') {
			              axios.get('/miniapp/ads/', {headers: headers})
			              .then(function(response) {
						$('#ads_'+index).append(response.data.template);
					})
					.catch(function (error) {
						console.log('15CATCHANERROR: ', error);
					})
				}
			}
		},
		onPlayerStateChange(event) {
			if (event.data == 3 && this.opened_videos.indexOf(event.target.options.videoId) < 0) {
				this.opened_videos.push(event.target.options.videoId);
				var headers = this.getHeaders();
				headers['action'] = 'open-video';
				headers['videoid'] = event.target.options.videoId;
		              axios.post('/miniapp/st/', {}, {headers:headers})
		              .then(function(response) {
				})
			}
			if (!window.autoplay) {
				return;
			}
			if (event.data == 0) {
				let g = event.target.g;
				let next_idx = parseInt($(g).parent()[0].dataset.index);
				next_idx += 1;
				let next_player = $('.subscribe-item').find("[data-index='" + next_idx + "']");
				if (next_player.length > 0) {
					let video_id = next_player[0].dataset.videoid;
					window.players[video_id].playVideo();
				}
			}
		},
		runPlayers(cln) {
			const vm = this;
			window.players = {}
			setTimeout(function() {
				var i = 0;
				var els = $(cln);
				var toset = setInterval(function() {
					if (!$(els).find('.card-body').length) {
						return;
					}
					let video_id = $(els[i]).find('.card-body')[0].dataset.videoid;
					let player = $(els[i]).find('.card-body').find('#player')[0];
					player = new YT.Player(player, {
						videoId: video_id,
						playerVars: {
							'playsinline': 1
						},
						events: {
							'onStateChange': vm.onPlayerStateChange,
						}
					});
					window.players[video_id] = player;
					i+=1
					if (i==10) {
						vm.insertAds();
						clearInterval(toset);
					}
					else if (i==els.length) {
						clearInterval(toset);
					}
				}, 80);
			}, 300)
		},
		setSectionActive(which) {
			const vm = this;
			this.clearWatchedAds();
			this.section = which;
			var headers = this.getHeaders();

			if (which == 'subscribes') {
				if ($('.subscribe-item').length > 0) {
					for (var j=0; j<$('.subscribe-item').length; j++) {
						$($('.subscribe-item')[j]).find('.card-body').html('<div id="player"></div>');
					}
				}
				this.subscribes_view = 'last-updates';
				headers['page'] = 1;
				headers['which'] = 'subscribes';
				this.subscribe_active_channel = '';
				axios.post('/miniapp/subs/', {}, {headers: headers})
		              .then(function(response) {
					vm.subscribes_container = response.data.last_updates;
					vm.subscribes_pages = response.data.subscribes_pages;
					vm.subscribe_current_page = 1;
					$(document).find('.subscribe-mini-nav-button').removeClass('mini-nav-button-active');
					$(document).find('#last_updates_mini_nav').addClass('mini-nav-button-active');
					if (vm.subscribes_container.length > 0) {
						vm.runPlayers('.subscribe-item');
					}
				})
				.catch(function (error) {
					console.log('2CATCHANERROR: ', error);
				})
			}
			else if (which == 'search') {
			}
			else if (which == 'recomendations') {
				if ($('.recomendation-item').length > 0) {
					for (var j=0; j<$('.recomendation-item').length; j++) {
						$($('.recomendation-item')[j]).find('.card-body').html('<div id="player"></div>');
					}
				}
				headers['which'] = 'recomendations';
				axios.post('/miniapp/recs/', {}, {headers: headers})
				.then(function(response) {
					vm.recomendations_container = response.data.recomendations_results;
					vm.recomendations_results_pages = response.data.recomendations_results_pages;
					vm.recomendations_ident = response.data.ident;
					if (vm.recomendations_container.length > 0) {
						vm.runPlayers('.recomendation-item');
					}
				})
				.catch(function (error) {
					console.log('3CATCHANERROR: ', error);
				})
			}
			else if (which == 'playlists') {
				this.isShuffle = false;
				headers['iss'] = 'delete';
				headers['which'] = 'playlists';
				axios.post('/miniapp/playlists/', {}, {headers: headers})
				.then(function(response) {
					vm.playlists_names = response.data.playlists_names['playlists_names'];
					vm.playlists_results_pages = response.data.playlists_pages;
					vm.playlist_container = null;
					vm.playlist_sorting = true;
					vm.active_playlist = null;
					vm.playlists_current_page = 1;
					setTimeout(function() {
						vm.insertAds();
					}, 300);
				})
				.catch(function (error) {
					console.log('4CATCHANERROR: ', error);
				})
			}
			if (which != 'subscribes') {
	              	this.subscribes_container = [];
			}
			if (which != 'playlists') {
				this.playlists_names = [];
			}
			if (which != 'recomendations') {
				this.recomendations_container = [];
			}
		},
		searchTheQuery() {
			this.setSectionActive("search");
			var q = document.getElementById('query').value;
			const vm = this;
			if (q) {
				if ($('.search-item').length > 0) {
					for (var j=0; j<$('.search-item').length; j++) {
						$($('.search-item')[j]).find('.card-body').html('<div id="player"></div>');
					}
				}
				this.current_query = q;
				var headers = this.getHeaders();
				headers['query'] = btoa(unescape(encodeURIComponent(q)));
				headers['page'] = 1;
	                     axios.post('/miniapp/search/', {}, {headers: headers})
		              .then(function(response) {
					vm.search_container = response.data.search_results;
					vm.search_results_pages = response.data.search_results_pages;
					vm.search_current_page = 1;

					async function checkElementExists(element, timeout = Infinity) {
						let startTime = Date.now();
						return new Promise((resolve) => {
							const intervalId = setInterval(() => {
								if ($(element).length > 0) {
									clearInterval(intervalId);
									resolve(true);
								} else if (Date.now() - startTime >= timeout * 1000) {
									clearInterval(intervalId);
									resolve(false);
								}
							}, 100);
						});
					}

					let timeout = 20;
					checkElementExists(".search-item", timeout)
					.then((result) => {
						if (result) {
							vm.runPlayers('.search-item');
						} else {
							console.log("The element does not exist after " + timeout + " seconds");
						}
					});

				})
				.catch(function (error) {
					console.log('5CATCHANERROR: ', error);
				})
			}
		},
		getCopyBtnAttr(video_url) {
			return 'videourl_' + video_url;
		},
		refreshPlaylists(event) {
			const vm  = this;
			var headers = this.getHeaders();
			if (this.playlists_current_page) {
				headers['page'] = this.playlists_current_page;
			}
			else {
				headers['page'] = null;
			}

			headers['iss'] = this.isShuffle;
			axios.post('/miniapp/playlists/', {}, {headers: headers})
			.then(function(response) {
				vm.playlists_names = response.data.playlists_names['playlists_names'];
				vm.playlists_results_pages = response.data.playlists_pages;
				vm.active_playlist = null;
				vm.playlist_container = null;
				vm.playlist_sorting = true;
			})
			.catch(function (error) {
				console.log('6CATCHANERROR: ', error);
			})
		},
		deletePlaylist(event) {
			Swal.fire({
				title: "Delete playlist?",
				text: "It will be impossible to restore it.",
				icon: "warning",
				showCancelButton: true,
				confirmButtonColor: "#3085d6",
				cancelButtonColor: "#d33",
				confirmButtonText: "Delete",
				cancelButtonText: "Cancel"
			}).then((result) => {
				if (result.isConfirmed) {
					const vm = this;
					var headers = vm.getHeaders();
					headers['name'] = btoa(unescape(encodeURIComponent(vm.active_playlist))),
					headers['action'] = 'delete';
					axios.post('/miniapp/playlists/', {}, {headers: headers})
					.then(function(response) {
						if (response.data.success) {
							Swal.fire({
								title: "Playlist deleted",
								icon: "success"
							});
							vm.refreshPlaylists();
						}
					})
					.catch(function (error) {
						console.log('7CATCHANERROR: ', error);
					})
				}
			});
		},
		shuffle(array) {
			return array.sort(() => Math.random() - 0.5);
		},
		shuffleInsidePlaylist() {
			this.playlist_container.playlist = this.shuffle(this.playlist_container.playlist);
			if ($('.playlist-item').length > 0) {
				for (var j=0; j<$('.playlist-item').length; j++) {
					$($('.playlist-item')[j]).find('.card-body').html('<div id="player"></div>');
				}
			}
			if (this.playlist_container && this.playlist_container.playlist.length > 0) {
				this.runPlayers('.playlist-item');
			}
		},
		openPlaylist(event) {
			const vm = this;
			var el = event.target;
			var playlist = btoa(unescape(encodeURIComponent(event.target.dataset.name)));
			var headers = this.getHeaders();
			headers['getplaylist'] =  playlist;
	              axios.post('/miniapp/playlists/', {}, {headers:headers})
	              .then(function(response) {
				if (response.data.active_playlist) {
					vm.active_playlist = response.data.active_playlist['name'];
					vm.playlist_container = response.data.active_playlist['playlist'];
					vm.playlist_sorting = false;
					if (response.data.active_playlist.playlist['playlist'].length > 0) {
						vm.runPlayers('.playlist-item');
					}
				}
			}).catch(function (err) {
			});
		},
		downloadVideo(event) {
			var vm = this;
			var el = event.target;
			var video_url = event.target.dataset.videourl;
			var type = event.target.dataset.type;
			if (type == 'video') {
				vm.downloads['video'].push(video_url);
				console.log('Inserted video into downloads');
			}
			else if (type == 'audio') {
				vm.downloads['audio'].push(video_url);
				console.log('Inserted audio into downloads');
			}
 			var send_confirm_to_element = $(el).parent().find('.copy-confirm');
			var headers = this.getHeaders();
			headers['type'] = type;
			headers['videourl'] = video_url;
	              axios.post('/miniapp/download/', {}, {headers:headers})
	              .then(function(response) {
				if ($(send_confirm_to_element)[0].innerHTML.length == 0) {
					$(send_confirm_to_element).append('The file is already in the bot');
					setTimeout(function() {
						$(send_confirm_to_element)[0].innerHTML = '';
					}, 2500);
				}
			}).catch(function (err) {
			});
		},
		subscribeTo(event) {
			const vm = this;
			var el = event.target;
			if (el.innerHTML != 'Subscribe to the channel') {
				return;
			}
			var video_url = event.target.dataset.videourl;
			var headers = this.getHeaders();
			headers['action'] = 'subscribe';
			headers['videourl'] = video_url;
	              axios.post('/miniapp/subs/', {}, {headers:headers})
	              .then(function(response) {
				if (response.data.success == true) {
					$(el)[0].innerHTML = 'Subscription is being processed...';
					vm.sended_to_subscribe.push(video_url);
				}
			}).catch(function (err) {
			});
		},
		isSendedToSubscribe(videoid, source) {
			if (this.sended_to_subscribe.indexOf(videoid) < 0) {
				return 'Subscribe to the channel'
			}
			return 'Subscription is being processed...'
		},
		clearPlaylistNames() {
			this.to_playlists_names = [];
		},
		addToPlaylistVideo(event) {
			this.clearPlaylistNames();
			const vm = this;
			var headers = this.getHeaders();
			headers['action'] = 'getplaylists';
			axios.get('/miniapp/playlists/', {headers: headers})
	              .then(function(response) {
				vm.to_playlists_names = response.data.playlists_names['playlists_names'];
				var el = event.target;
				var video_url = event.target.dataset.videourl;
				var channel_title = event.target.dataset.channel_title;
				vm.video_into_playlist = {'video_url': video_url, 'channel_title': channel_title};
				var headers = vm.getHeaders();
				headers['action'] = 'inplaylists';
				headers['videoid'] = vm.video_into_playlist['video_url'];
	                     axios.get('/miniapp/playlists/', {headers: headers})
		              .then(function(response) {
					var inPlaylistData = response.data.playlists['playlists'];
					var els = $('input[data-target="pl-name-checkbox"]');
					for (var i=0; i<els.length; i++) {
						if (inPlaylistData.indexOf(els[i].dataset.name) >= 0) {
							els[i].checked = true;
						}
						else {
							els[i].checked = false;
						}
					}
					$(document).find('.add-to-playlist-modal').show();
				})
				.catch(function (error) {
					console.log('9CATCHANERROR: ', error);
				})
			})
			.catch(function (error) {
				console.log('1CATCHANERROR: ', error);
			})
			return;
		},
		closeModal(classname) {
			$("." + classname).hide();
		},
		insertIntoPlaylist(event) {
			var el = event.target;
			var headers = this.getHeaders();
			headers['action'] = 'add';
			headers['videoid'] = this.video_into_playlist['video_url'];
			headers['channeltitle'] = btoa(unescape(encodeURIComponent(this.video_into_playlist['channel_title'])));
			headers['name'] = btoa(unescape(encodeURIComponent(el.dataset.name))),
                     axios.post('/miniapp/playlists/', {}, {headers: headers})
	              .then(function(response) {
				if (response.data.error) {
					Swal.fire(response.data.error);
				}
			})
			.catch(function (error) {
				console.log('10CATCHANERROR: ', error);
			})
		},
		deleteVideoFromPlaylist(event) {
			const vm = this;
			var el = event.target;
			var video_id = event.target.dataset.videoid;
			var headers = vm.getHeaders();
			headers['action'] = 'remove';
			headers['videoid'] = video_id;
			headers['name'] = btoa(unescape(encodeURIComponent(vm.active_playlist)));
	              axios.post('/miniapp/playlists/', {}, {headers: headers})
	              .then(function(response) {
				if (response.data.success) {
					$(el).parent().parent().parent().parent().html('');
				}
			})
			.catch(function (error) {
				console.log('11CATCHANERROR: ', error);
			})
		},
		autoplayChecked(event) {
			return window.autoplay;
		},
		changeAutoplay(event) {
			const vm = this;
			var headers = this.getHeaders();
			headers['autoplay'] = event.target.checked;
	              axios.get('/miniapp/autoplay/', {headers: headers})
			window.autoplay = event.target.checked;
		},
		searchPaginationAction(event) {
			var el = event.target;
                     var opening_page = event.target.dataset.page;
			const vm = this;
			var headers = this.getHeaders();
			headers['query'] = btoa(unescape(encodeURIComponent(this.current_query)));
			headers['page'] = opening_page;
	              axios.post('/miniapp/search/', {}, {headers: headers})
	              .then(function(response) {
				vm.clearWatchedAds();
				vm.search_container = response.data.search_results;
				vm.search_results_pages = response.data.search_results_pages;
				if (opening_page == 'last') {
					vm.search_current_page = vm.search_results_pages;
				}
				else if (opening_page == 'first') {
					vm.search_current_page = 1;
				}
				else {
					vm.search_current_page = opening_page;
				}

				if ($('.search-item').length > 0) {
					for (var j=0; j<$('.search-item').length; j++) {
						$($('.search-item')[j]).find('.card-body').html('<div id="player"></div>');
					}
				}
				if (vm.search_container.length > 0) {
					vm.runPlayers('.search-item');
				}
			})
		},
		subscribePaginationAction(event) {
			var el = event.target;
                     var opening_page = event.target.dataset.page;
			const vm = this;
			var headers = this.getHeaders();
			headers['page'] = opening_page;
			if (this.subscribe_active_channel) {
				headers['channel'] = this.subscribe_active_channel;
			}

			if ($('.subscribe-item').length > 0) {
				for (var j=0; j<$('.subscribe-item').length; j++) {
					$($('.subscribe-item')[j]).find('.card-body').html('<div id="player"></div>');
				}
			}

	              axios.post('/miniapp/subs/', {}, {headers: headers})
	              .then(function(response) {
				vm.clearWatchedAds();
				vm.subscribes_container = response.data.last_updates;
				vm.subscribes_pages = response.data.subscribes_pages;
				vm.subscribe_current_page = opening_page;
				if (vm.subscribes_container.length > 0) {
					vm.runPlayers('.subscribe-item');
				}
			})
		},
		recomendationsPaginationAction(event) {
			if ($('.recomendation-item').length > 0) {
				for (var j=0; j<$('.recomendation-item').length; j++) {
					$($('.recomendation-item')[j]).find('.card-body').html('<div id="player"></div>');
				}
			}

			const vm = this;
			var el = event.target;
                     var opening_page = event.target.dataset.page;
			var headers = this.getHeaders();
			headers['page'] = opening_page;
			headers['ident'] = this.recomendations_ident;
	              axios.post('/miniapp/recs/', {}, {headers: headers})
	              .then(function(response) {
				vm.clearWatchedAds();
				vm.recomendations_container = response.data.recomendations_results;
				vm.recomendations_results_pages = response.data.recomendations_results_pages;
				if (opening_page == 'last') {
					vm.recomendations_current_page = vm.recomendations_results_pages;
				}
				else if (opening_page == 'first') {
					vm.recomendations_current_page = 1;
				}
				else {
					vm.recomendations_current_page = opening_page;
				}
				if (vm.recomendations_container.length > 0) {
					vm.runPlayers('.recomendation-item');
				}
			})
		},
		playlistsPaginationAction(event) {
			const vm = this;
			var el = event.target;
                     var opening_page = event.target.dataset.page;
			var headers = this.getHeaders();
			headers['page'] = opening_page;
			headers['iss'] = this.isShuffle;
	              axios.post('/miniapp/playlists/', {}, {headers: headers})
	              .then(function(response) {
				vm.clearWatchedAds();
				vm.playlists_names = response.data.playlists_names['playlists_names'];
				vm.playlists_results_pages = response.data.playlists_pages;
				if (opening_page == 'last') {
					vm.playlists_current_page = vm.playlists_results_pages;
				}
				else if (opening_page == 'first') {
					vm.playlists_current_page = 1;
				}
				else {
					vm.playlists_current_page = opening_page;
				}
				setTimeout(function() {
					vm.clearAds();
					vm.insertAds();
				}, 300);
			})
		},
		showChannelSubscribe(event) {
			var el = event.target;
 			var channelurl = event.target.dataset.channelurl;
			const vm = this;
			var headers = this.getHeaders();
			headers['channel'] = channelurl;
	              axios.post('/miniapp/subs/', {}, {headers: headers})
	              .then(function(response) {
				if (response.data.last_updates.length == 0) {
					Swal.fire("No video updates for this channel!");
					return;
				}
				window.scrollTo({top: -1, behavior: 'smooth'});
				vm.subscribes_container = response.data.last_updates;
				vm.subscribes_pages = response.data.subscribes_pages;
				vm.subscribe_current_page = 1;
				vm.subscribe_active_channel = response.data.channel_name;
				if ($('.subscribe-item').length > 0) {
					for (var j=0; j<$('.subscribe-item').length; j++) {
						$($('.subscribe-item')[j]).find('.card-body').html('<div id="player"></div>');
					}
				}
				if (vm.subscribes_container.length > 0) {
					vm.runPlayers('.subscribe-item');
				}

			})
		},
		subscribeView(event) {
			var el = event.target;
			var view = event.target.dataset.name;
			const vm = this;
			vm.subscribe_active_channel = '';
			var headers = this.getHeaders();
			headers['getchannels'] = true;
			$(document).find('.subscribe-mini-nav-button').removeClass('mini-nav-button-active');
			if (view == 'last-updates') {
				$(document).find('#last_updates_mini_nav').addClass('mini-nav-button-active');
				this.setSectionActive('subscribes');
				this.subscribes_view = 'last-updates';
			}
			else if (view == 'channels') {
				$(document).find('#channels_mini_nav').addClass('mini-nav-button-active');
				vm.subscribes_container = [];
				vm.subscribes_pages = 0;
				this.subscribes_view = 'channels';
	                     axios.post('/miniapp/subs/', {}, {headers: headers})
		              .then(function(response) {
					vm.channels = response.data.channels;
				})
				.catch(function (error) {
					console.log('12CATCHANERROR: ', error);
				})
			}
		},
		getCurrentSortingValue() {
			if (!this.isShuffle) {
				return "Sort"
			}
			if (this.isShuffle == 'shuffle') {
				return "Shuffle"
			}
			if (this.isShuffle == 'oldest') {
				return "First the old ones"
			}
			if (this.isShuffle == 'newest') {
				return "New ones first."
			}
		},
		sortingPlaylists(param, title) {
			this.clearWatchedAds();
			if (param == 'shuffle') {
				this.isShuffle = 'shuffle';
			}
			if (param == 'oldest') {
				this.isShuffle = 'oldest';
			}
			if (param == 'newest') {
				this.isShuffle = 'newest';
			}
			var headers = this.getHeaders();
			headers['iss'] = this.isShuffle;
			headers['page'] = 1;
			this.playlists_current_page = 1;
			var headers = this.getHeaders();
			headers['sorting'] = true;
			headers['param'] = param;
			const vm  = this;

			axios.post('/miniapp/playlists/', {}, {headers: headers})
	              .then(function(response) {
				vm.playlists_names = response.data.playlists_names['playlists_names'];
				vm.playlists_results_pages = response.data.playlists_pages;
			})
			.catch(function (error) {
				console.log('13CATCHANERROR: ', error);
			})
		},
		createPlaylistView(event) {
			var el = event.target;
			var action = event.target.dataset.name;
			const vm = this;
			if (action == 'create') {
				if (vm.playlist_creation_statement == true) {
					vm.playlist_creation_statement = false;
				}
				else {
					vm.playlist_creation_statement = true;
				}
			}
		},
		createPlaylist(event) {
			var pl_name = $(document).find('.create-playlist-form').find('#new_playlist_name')[0].value;
			const vm = this;
			var headers = this.getHeaders();
			headers['action'] = 'create';
			headers['name'] = btoa(unescape(encodeURIComponent(pl_name)));
                     axios.post('/miniapp/playlists/', {}, {headers: headers})
	              .then(function(response) {
				if (response.data.success == true) {
					vm.playlist_creation_statement = false;
					vm.playlists_names = response.data.playlists_names['playlists_names'];
				}
				else if (response.data.success == false) {
					Swal.fire('Error. ' + response.data.error);
				}
			})
			.catch(function (error) {
				console.log('14CATCHANERROR: ', error);
			})
		},
		setAdsId(index) {
			return 'ads_' + index;
		},
		clickOnAds(index) {
			var ad_id = $('#ads_' + index).find('.ad-el')[0].dataset.id;
			var url = $('#ads_' + index).find('.ad-el')[0].dataset.url;
			var headers = this.getHeaders();
			headers['action'] = 'click-on-ads';
			headers['id'] = ad_id;
	              axios.post('/miniapp/st/', {}, {headers:headers})
	              .then(function(response) {
			})
			.catch(function (error) {
				console.log('8CATCHANERROR: ', error);
			})
			if (url != false && url != 'false') {
				window.open(url, '_blank');
			}
		},
		getRandomAds(index) {
			if ($('.ads-container').length > 0) {
				$('.ads-container').html('');
			}
			var headers = this.getHeaders();
			headers['action'] = 'get-random-ads';
                     axios.post('/miniapp/ads/', {}, {headers: headers})
	              .then(function(response) {
				$('#ads_'+index).append(response.data.template);
			})
			.catch(function (error) {
				console.log('15CATCHANERROR: ', error);
			})
		},
        },
        created: function() {
		const vm = this;
		this.to_playlists_names = [];
		var headers = this.getHeaders();
		headers['action'] = 'getplaylists';
		headers['init-loading'] = true;
		axios.post('/miniapp/playlists/', {}, {headers: headers})
              .then(function(response) {
			vm.to_playlists_names = response.data.playlists_names['playlists_names'];
			if (response.data.main_page_subscribes.length > 0) {
				vm.main_page_subscribes = response.data.main_page_subscribes;
				vm.runPlayers('.subscribe-item');
			}
			else {
				vm.subscribe_please = true;
			}
		})
		.catch(function (error) {
			console.log('1CATCHANERROR: ', error);
		})

        },
        template: `
                <div class='main container-fluid'>
			<form id='search_form' class='search-form'>
				<input type="text" class="form-control" id="query" name="query">
				<button type="submit" class="btn btn-primary" @click.prevent="searchTheQuery()"><img class='search-button-ico' src='/static/search_ico.svg'></img></button>
			</form>
			<div class='nav-container'>
				<button class='nav-button' @click='setSectionActive("subscribes")'>Subscriptions</button>
				<button class='nav-button' @click='setSectionActive("recomendations")'>Recommendations</button>
				<button class='nav-button' @click='setSectionActive("playlists")'>Playlists</button>
			</div>
			<div class='main-container'>
				<div v-if='section == "search"' class='search-section'>
					<div v-if='search_current_page > 0' class='search-pagination'>
						<pagination @search-pagination-action='searchPaginationAction' @subscribe-pagination-action='subscribePaginationAction' @recomendations-pagination-action='recomendationsPaginationAction' @playlists-pagination-action='playlistsPaginationAction' :pages='search_results_pages' :section='section' :current_page='search_current_page'></pagination>
					</div>
					<div v-if='search_current_page > 0' class='autoplay-container'>
						<div class='autoplay-checkbox-container' style='width: 100%; text-align: center;'>
							<div class="checkbox-wrapper-6">
								<span class='autoplay-title'>Autoplay: </span>
								<input @change.prevent='changeAutoplay' :checked="autoplayChecked()" class="tgl tgl-light" id="cb1-6" type="checkbox"/>
								<label class="tgl-btn" for="cb1-6">
							</div>
						</div>
					</div>
					<div id="faq" role="tablist" aria-multiselectable="true">
						<div v-for='(i, index) in search_container' class='search-data card search-item' :data-videoid='i.id' :data-video_container='i.id'>
							<div class='video-information'>
								<p class='video-information-p'><span class='video-information-title'>{{ i.title }}</span></p>
							</div>
							<div class="card-body" :data-index='index' :data-videoid='i.id'>
								<div id='player'></div>
							</div>
							<div class="card-footer">
								<div class='copy-btn-container search-btn-container' :id=getCopyBtnAttr(index)>
									<button v-if="downloads.video.indexOf(i.id)<0" class='download-this-link pannel-button' :data-videourl='i.id' data-type='video' @click.prevent='downloadVideo'>Download video</button>
									<button v-if="downloads.audio.indexOf(i.id)<0" class='download-this-link pannel-button' :data-videourl='i.id' data-type='audio' @click.prevent='downloadVideo'>Download audio</button>
									<button class='subscribe-this-link pannel-button' :data-videourl='i.id' @click.prevent='subscribeTo'>{{ isSendedToSubscribe(i.id, 'search') }}</button>
									<button type='button' class='download-this-link pannel-button' :data-videourl='i.id' @click.prevent='addToPlaylistVideo' :data-channel_title='i.channel_title'>Add to playlist</button>
									<div class='copy-confirm'></div>
								</div>
							</div>
							<div v-if="index == 4 || index == 8" class='to-ads-container' :data-index="index">
								<div class='search-ads ads-container' @click.prevent='clickOnAds(index)' :id='setAdsId(index)'>
								</div>
							</div>
						</div>
					</div>
					<div v-if='search_current_page > 0' class='search-pagination'>
						<pagination @search-pagination-action='searchPaginationAction' @subscribe-pagination-action='subscribePaginationAction' @recomendations-pagination-action='recomendationsPaginationAction' @playlists-pagination-action='playlistsPaginationAction' :pages='search_results_pages' :section='section' :current_page='search_current_page'></pagination>
					</div>
				</div>

				<div v-else-if='section == "subscribes"' class='subs-section'>
					<div class='subscribe-mini-nav'>
						<button @click.prevent='subscribeView' data-name="last-updates" id='last_updates_mini_nav' class="subscribe-mini-nav-button" role="button">Latest updates</button>
						<button @click.prevent='subscribeView' data-name="channels" id='channels_mini_nav' class="subscribe-mini-nav-button" role="button">My channels</button>
					</div>
					<div v-if='subscribe_active_channel.length > 0' class='subscribe-channel-title'>
						<span>You are viewing the channel<br/>{{ subscribe_active_channel }}</span>
					</div>
					<div v-if='subscribes_pages > 0'>
						<pagination @recomendations-pagination-action='recomendationsPaginationAction' @playlists-pagination-action='playlistsPaginationAction' @subscribe-pagination-action='subscribePaginationAction' @search-pagination-action='searchPaginationAction' :pages='subscribes_pages' :section='section' :current_page='subscribe_current_page'></pagination>
					</div>
					<div v-if='subscribes_pages > 0' class='autoplay-container'>
						<div class='autoplay-checkbox-container' style='width: 100%; text-align: center;'>
							<div class="checkbox-wrapper-6">
								<span class='autoplay-title'>Autoplay: </span>
								<input @change.prevent='changeAutoplay' :checked="autoplayChecked()" class="tgl tgl-light" id="cb1-6" type="checkbox"/>
								<label class="tgl-btn" for="cb1-6">
							</div>
						</div>
					</div>
					<div v-for='(upd, index) in subscribes_container' class='subscribe-item card'>
						<div class="sub-card-header">
							<span class='sub-card-channel'>{{ upd.channel_name }}</span>
							<span class='sub-card-datetime'>{{ upd.dt }}</span>
						</div>
						<div class="card-body" :data-index='index' :data-videoid='upd.video'>
							<div id='player'></div>
						</div>
						<div class="card-footer">
							<div class='copy-btn-container'>
								<button v-if="downloads.video.indexOf(upd.video)<0" class='download-this-link pannel-button' data-type='video' :data-videourl='upd.video' @click.prevent='downloadVideo'>Download video</button>
								<button v-if="downloads.audio.indexOf(upd.video)<0" class='download-this-link pannel-button' data-type='audio' :data-videourl='upd.video' @click.prevent='downloadVideo'>Download audio</button>
								<button type='button' class='download-this-link pannel-button' :data-videourl='upd.video' @click.prevent.stop='addToPlaylistVideo' :data-channel_title='upd.channel_name'>Add to playlist</button>
								<div class='copy-confirm'></div>
							</div>
						</div>
						<div v-if="index == 4 || index == 8" class='to-ads-container' :data-index="index">
							<div class='search-ads ads-container' @click.prevent='clickOnAds(index)' :id='setAdsId(index)'>
							</div>
						</div>
					</div>
					<div v-if='subscribes_pages > 0'>
						<pagination @search-pagination-action='searchPaginationAction' @subscribe-pagination-action='subscribePaginationAction' @recomendations-pagination-action='recomendationsPaginationAction' @playlists-pagination-action='playlistsPaginationAction' :pages='subscribes_pages' :section='section' :current_page='subscribe_current_page'></pagination>
					</div>
					<div v-for='channel in channels' class="card channel-list-card">
						<a class="card-body channel-name" :data-index='index' :href='channel.url' :data-channelurl='channel.url' @click.prevent='showChannelSubscribe'>
							{{ channel.name }}
						</a>
					</div>
					<div v-if='(subscribes_view=="channels" && channels.length == 0) || (subscribes_view=="last-updates" && subscribes_container.length == 0)'>
						<h4>No data to display</h4>
					</div>
				</div>

				<div v-else-if='section == "recomendations"' class='recs-section'>
					<div v-if='recomendations_current_page > 0' class='recomendations-pagination'>
						<pagination @search-pagination-action='searchPaginationAction' @subscribe-pagination-action='subscribesPaginationAction' @recomendations-pagination-action='recomendationsPaginationAction' @playlists-pagination-action='playlistsPaginationAction' :pages='recomendations_results_pages' :section='section' :current_page='recomendations_current_page'></pagination>
					</div>
					<div v-if='recomendations_container.length > 0' class='autoplay-container'>
						<div class='autoplay-checkbox-container' style='width: 100%; text-align: center;'>
							<div class="checkbox-wrapper-6">
								<span class='autoplay-title'>Autoplay: </span>
								<input @change.prevent='changeAutoplay' :checked="autoplayChecked()" class="tgl tgl-light" id="cb1-6" type="checkbox"/>
								<label class="tgl-btn" for="cb1-6">
							</div>
						</div>
					</div>
					<div v-for='(i, index) in recomendations_container' class='recomendation-item card'>
						<div class="sub-card-header">
							<div class='video-information'>
								<p class='video-information-p'><span class='video-information-title'>{{ i.channel_title }} | {{ i.title }}</span></p>
							</div>
						</div>
						<div class="card-body" :data-index='index' :data-videoid='i.id'>
							<div id='player'></div>
						</div>
						<div class="card-footer">
							<div class='copy-btn-container'>
								<button v-if="downloads.video.indexOf(i.id)<0" class='download-this-link pannel-button' data-type='video' :data-videourl='i.id' @click.prevent='downloadVideo'>Download video</button>
								<button v-if="downloads.audio.indexOf(i.id)<0" class='download-this-link pannel-button' data-type='audio' :data-videourl='i.id' @click.prevent='downloadVideo'>Download audio</button>
								<button class='subscribe-this-link pannel-button' :data-videourl='i.id' @click.prevent='subscribeTo'>{{ isSendedToSubscribe(i.id, 'recs') }}</button>
								<button type='button' class='download-this-link pannel-button' :data-videourl='i.id' @click.prevent='addToPlaylistVideo' :data-channel_title='i.title'>Add to playlist</button>
								<div class='copy-confirm'></div>
							</div>
						</div>
						<div v-if="index == 4 || index == 8" class='to-ads-container' :data-index="index">
							<div class='search-ads ads-container' @click.prevent='clickOnAds(index)' :id='setAdsId(index)'>
							</div>
						</div>
					</div>
					<div v-if='recomendations_current_page > 0' class='recomendations-pagination'>
						<pagination @subscribe-pagination-action='subscribesPaginationAction' @search-pagination-action='searchPaginationAction' @recomendations-pagination-action='recomendationsPaginationAction' @playlists-pagination-action='playlistsPaginationAction' :pages='recomendations_results_pages' :section='section' :current_page='recomendations_current_page'></pagination>
					</div>
				</div>

				<div v-else-if='section == "playlists"' class='playlists-section'>
					<div class='playlists-mini-nav'>
						<div v-if='playlist_sorting == true' class='btn-playlist-container'>
							<button @click.prevent='createPlaylistView' data-name="create" id='create_playlist_mini_nav' class="btn btn-playlist-sorting btn-primary playlists-mini-nav-button" role="button">Add</button>
						</div>
						<div v-if='playlist_sorting == true' class="dropleft sorting-dropdown">
							<button class="btn btn-playlist-sorting btn-primary dropdown-toggle" type="button" id="about-us" data-toggle="dropdown" aria-haspopup="true" aria-expanded="false">{{ getCurrentSortingValue() }}</button>
							<div class="dropdown-menu" aria-labelledby="about-us">
								<a class="dropdown-item" @click.prevent="sortingPlaylists('newest', 'Newest')" href="">Newest</a>
								<a class="dropdown-item" @click.prevent="sortingPlaylists('oldest', 'Oldest')" href="">Oldest</a>
								<a class="dropdown-item" @click.prevent="sortingPlaylists('shuffle', 'Shuffle')" href="">Shuffle</a>
							</div>
						</div>
					</div>
					<div v-if='playlist_creation_statement == true' class='playlist-creation-container'>
						<form id='create_playlist_form' class='create-playlist-form'>
							<fieldset class="form-group">
								<label for="new_playlist_name">Title</label>
								<input type="text" class="form-control" id="new_playlist_name" name="new_playlist_name" />
							</fieldset>
							<div class='creation-pl-btn-container'>
								<button @click.prevent='createPlaylist' type="submit" class="btn btn-primary">Add</button>
							</div>
						</form>

					</div>

					<div v-if='!active_playlist' class='playlists-pagination'>
						<pagination @search-pagination-action='searchPaginationAction' @recomendations-pagination-action='recomendationsPaginationAction' @playlists-pagination-action='playlistsPaginationAction' @subscribe-pagination-action='subscribePaginationAction' :pages='playlists_results_pages' :section='section' :current_page='playlists_current_page'></pagination>
					</div>

					<div v-if='!playlists_names || playlists_names.length == 0'>
						<h4>There are no playlists created yet.</h4>
					</div>

					<div v-if='!active_playlist' class='playlists-container'>
						<div v-for='(n, index) in playlists_names' class='playlists-names list-group'>
							<a @click.prevent='openPlaylist' :data-name='n.name' href='' class='playlist-link list-group-item list-group-item-action'><span @click.prevent='openPlaylist' :data-name='n.name' class='playlist-creation-date'>{{ n.dt }}</span><br/>{{ n.name }}</a>
							<div v-if="index == 4 || index == 8" class='to-ads-container' :data-index="index">
								<div class='search-ads ads-container' @click.prevent='clickOnAds(index)' :id='setAdsId(index)'>
								</div>
							</div>
						</div>
					</div>

					<div v-if='active_playlist'>
						<div class='autoplay-container'>
							<div v-if='playlist_container.playlist.length' class='playlist-nav-second-row'>
								<button class='button-6' role='button' @click='shuffleInsidePlaylist'>Random Play</button>
							</div>
							<div class='autoplay-checkbox-container' style='width: 100%; text-align: center;'>
								<div class="checkbox-wrapper-6">
									<span class='autoplay-title'>Autoplay: </span>
									<input @change.prevent='changeAutoplay' :checked="autoplayChecked()" class="tgl tgl-light" id="cb1-6" type="checkbox"/>
									<label class="tgl-btn" for="cb1-6">
								</div>
							</div>
						</div>

						<div class='playlist-nav'>
							<div class='playlist-nav-first-row'>
								<button class='refresh-pl-btn' @click='refreshPlaylists'><svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" class="bi bi-backspace" viewBox="0 0 16 16"><path d="M5.83 5.146a.5.5 0 0 0 0 .708L7.975 8l-2.147 2.146a.5.5 0 0 0 .707.708l2.147-2.147 2.146 2.147a.5.5 0 0 0 .707-.708L9.39 8l2.146-2.146a.5.5 0 0 0-.707-.708L8.683 7.293 6.536 5.146a.5.5 0 0 0-.707 0z"/><path d="M13.683 1a2 2 0 0 1 2 2v10a2 2 0 0 1-2 2h-7.08a2 2 0 0 1-1.519-.698L.241 8.65a1 1 0 0 1 0-1.302L5.084 1.7A2 2 0 0 1 6.603 1zm-7.08 1a1 1 0 0 0-.76.35L1 8l4.844 5.65a1 1 0 0 0 .759.35h7.08a1 1 0 0 0 1-1V3a1 1 0 0 0-1-1z"/></svg></button>
								<p class='current-pl-title'>{{ active_playlist }}</p>
								<button class='delete-pl-btn' @click='deletePlaylist'><svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" class="bi bi-trash" viewBox="0 0 16 16"><path d="M5.5 5.5A.5.5 0 0 1 6 6v6a.5.5 0 0 1-1 0V6a.5.5 0 0 1 .5-.5m2.5 0a.5.5 0 0 1 .5.5v6a.5.5 0 0 1-1 0V6a.5.5 0 0 1 .5-.5m3 .5a.5.5 0 0 0-1 0v6a.5.5 0 0 0 1 0z"/><path d="M14.5 3a1 1 0 0 1-1 1H13v9a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V4h-.5a1 1 0 0 1-1-1V2a1 1 0 0 1 1-1H6a1 1 0 0 1 1-1h2a1 1 0 0 1 1 1h3.5a1 1 0 0 1 1 1zM4.118 4 4 4.059V13a1 1 0 0 0 1 1h6a1 1 0 0 0 1-1V4.059L11.882 4zM2.5 3h11V2h-11z"/></svg></button>
							</div>
						</div>

						<div v-if='!playlist_container || playlist_container.playlist.length == 0' style='text-align: center'>
							<h4>The playlist does not contain any videos yet.</h4>
						</div>

						<div v-if='playlist_container.playlist && playlist_container.playlist.length > 0'>
							<div v-for='(i, index) in playlist_container.playlist' class='playlists-data playlist-item'>
								<div class='pl-information'>
									<p class='pl-information-p'><span class='pl-channel-title'>{{ i.channel_title }}</span> <span class='pl-video-dt'>Added: {{ i.dt }} <a href='' @click.prevent='deleteVideoFromPlaylist' class='delete-from-pl' :data-videoid='i.video_id'>Delete</a></span></p>
								</div>
								<div class="card-body" :data-index='index' :data-videoid='i.video_id'>
									<div id='player'></div>
								</div>
								<div class="card-footer">
									<div class='copy-btn-container' :id=getCopyBtnAttr(index)>
										<button v-if="downloads.video.indexOf(i.video_id)<0" class='download-this-link pannel-button' :data-videourl='i.video_id' data-type='video' @click.prevent='downloadVideo'>Download video</button>
										<button v-if="downloads.audio.indexOf(i.video_id)<0" class='download-this-link pannel-button' :data-videourl='i.video_id' data-type='audio' @click.prevent='downloadVideo'>Download audio</button>
										<div class='copy-confirm'></div>
									</div>
								</div>
							</div>
						</div>
					</div>

					<div v-if='!active_playlist' class='playlists-pagination'>
						<pagination @search-pagination-action='searchPaginationAction' @recomendations-pagination-action='recomendationsPaginationAction' @playlists-pagination-action='playlistsPaginationAction' @subscribe-pagination-action='subscribePaginationAction' :pages='playlist_results_pages' :section='section' :current_page='playlists_current_page'></pagination>
					</div>
				</div>
				<div v-else-if='section == "main"'>
					<div v-if="subscribe_please == true" style='text-align: center'>
						<h4>Subscribe to channels to see updates!</h4>
					</div>
					<div v-if='main_page_subscribes.length > 0'>
						<div v-for='(upd, index) in main_page_subscribes' class='subscribe-item card'>
							<div class="sub-card-header">
								<span class='sub-card-channel'>{{ upd.channel_name }}</span>
								<span class='sub-card-datetime'>{{ upd.dt }}</span>
							</div>
							<div class="card-body" :data-index='index' :data-videoid='upd.video'>
								<div id='player'></div>
							</div>
							<div class="card-footer">
								<div class='copy-btn-container'>
									<button v-if="downloads.video.indexOf(upd.video)<0" class='download-this-link pannel-button' data-type='video' :data-videourl='upd.video' @click.prevent='downloadVideo'>Download video</button>
									<button v-if="downloads.audio.indexOf(upd.video)<0" class='download-this-link pannel-button' data-type='audio' :data-videourl='upd.video' @click.prevent='downloadVideo'>Download audio</button>
									<button type='button' class='download-this-link pannel-button' :data-videourl='upd.video' @click.prevent.stop='addToPlaylistVideo' :data-channel_title='upd.channel_name'>Add to playlist</button>
									<div class='copy-confirm'></div>
								</div>
							</div>
							<div v-if="index == 4 || index == 8" class='to-ads-container' :data-index="index">
								<div class='ads-container' @click.prevent='clickOnAds(index)' :id='setAdsId(index)'>
								</div>
							</div>
						</div>
					</div>
				</div>
			</div>
                </div>


		<div class="add-to-playlist-modal modal">
			<div class="modal-dialog" role="document">
				<div class="modal-content">
					<div class="modal-header">
						<h4 class="modal-title" id="modalLabel">Select playlists:</h4>
						<button type="button" @click.prevent='closeModal("modal")' class="close" data-dismiss="modal" aria-label="Close">
							<span aria-hidden="true">&times;</span>
						</button>
					</div>
					<div class="modal-body">
	                                        <div v-for='pl in to_playlists_names' class="form-group form-check">
				                        <input @click='insertIntoPlaylist' :id='pl.name' :data-name='pl.name' data-target='pl-name-checkbox' class="form-check-input" type="checkbox" />
	                                                <label class="form-check-label" :for="pl.name">{{ pl.name }}</label>
	                                        </div>
					</div>
					<div class="modal-footer">
						<button type="button" @click.prevent='closeModal("modal")' class="btn btn-primary" data-dismiss="modal">Close</button>
					</div>
				</div>
			</div>
		</div>
        `,
        components: {
		'pagination': componentPagination,
        }
}


const main = {
        data() {
                return {
			watched_ads: [],
                }
        },
	methods: {
		clearWatchedAdsArray() {
			this.watched_ads = [];
		},
		getHeaders() {
			var csrf = $('input[name="csrfmiddlewaretoken"]').attr('value');
			var headers = {
				'Access-Control-Allow-Origin': '*',
				'withCredentials': true,
				'X-CSRFTOKEN': csrf
			}
			if (window.tg && window.tg.initDataUnsafe.user) {
				headers['chatid'] = window.tg.initDataUnsafe.user.id;
			}
			else {
				headers['chatid'] = 'no';
			}
			return headers
		},
	},
        created: function() {
		const vm = this;
		$(document).on('scroll', function() {
			if ($(".ads-container").length > 0) {
				var deviceHeight = window.screen.height;
				if ((deviceHeight > $(".ads-container")[0].getBoundingClientRect().top) > 0) {
					// over first ad
					if ($($(".ads-container")[0]).find('.ad-el').length > 0) {
						var ident = $($(".ads-container")[0]).find('.ad-el')[0].dataset.ident;
						if (vm.watched_ads.indexOf(ident) < 0) {
							vm.watched_ads.push(ident);
							var headers = vm.getHeaders();
							headers['action'] = 'watch';
							headers['ad-id'] = $($(".ads-container")[0]).find('.ad-el')[0].dataset.id;
					              axios.post('/miniapp/ads/', {}, {headers: headers})
					              .then(function(response) {
							})
							.catch(function (error) {
								console.log('16CATCHANERROR: ', error);
							})
						}
					}
				}
				if ((deviceHeight - $(".ads-container")[1].getBoundingClientRect().top) > 0) {
					// over second ad
					if ($($(".ads-container")[1]).find('.ad-el').length > 0) {
						var ident = $($(".ads-container")[1]).find('.ad-el')[0].dataset.ident;
						if (vm.watched_ads.indexOf(ident) < 0) {
							vm.watched_ads.push(ident);
							var headers = vm.getHeaders();
							headers['action'] = 'watch';
							headers['ad-id'] = $($(".ads-container")[1]).find('.ad-el')[0].dataset.id;
					              axios.post('/miniapp/ads/', {}, {headers: headers})
					              .then(function(response) {
							})
							.catch(function (error) {
								console.log('17CATCHANERROR: ', error);
							})
						}
					}
				}
			}
		});
        },
        components: {
		'main-page': componentMainPage,
		'pagination': componentPagination,
        }
};

const appEl = document.querySelector('#app');
const app = Vue.createApp(main)
app.mount(appEl);
