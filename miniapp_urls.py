from django.urls import path
from u2bapp.views import init_view, miniapp_search, hello_view, bye_view, miniapp_subs_view, miniapp_download_view, miniapp_recomendations, miniapp_playlists, miniapp_admin, miniapp_admin_login, miniapp_admin_hello_view, miniapp_admin_authentication_view, miniapp_ads_view, miniapp_statistics_view, miniapp_not_from_tg, miniapp_autoplay_view
from django.conf import settings
from django.conf.urls.static import static


urlpatterns = [
    path('miniapp/', init_view, name='abcde'),
    path('miniapp/search/', miniapp_search, name='miniapp_search'),
    path('miniapp/hello/', hello_view, name='miniapp_hello'),
    path('miniapp/bye/', bye_view, name='miniapp_bye'),
    path('miniapp/st/', miniapp_statistics_view, name='miniapp_statistics'),
    path('miniapp/subs/', miniapp_subs_view, name='miniapp_subs'),
    path('miniapp/download/', miniapp_download_view, name='miniapp_download'),
    path('miniapp/recs/', miniapp_recomendations, name='miniapp_recomendations'),
    path('miniapp/playlists/', miniapp_playlists, name='miniapp_playlists'),
    path('miniapp/adm/', miniapp_admin, name='miniapp_admin'),
    path('miniapp/admin_login/', miniapp_admin_login, name='miniapp_admin_login'),
    path('miniapp/admin_hello/', miniapp_admin_hello_view, name='miniapp_admin_hello'),
    path('miniapp/i_am_admin/', miniapp_admin_authentication_view, name='miniapp_admin_authentication'),
    path('miniapp/ads/', miniapp_ads_view, name='miniapp_ads'),
    path('miniapp/not_from_telegram/', miniapp_not_from_tg, name='miniapp_not_from_tg'),
    path('miniapp/autoplay/', miniapp_autoplay_view, name='miniapp_autoplay'),
]

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
