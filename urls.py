from devel0per.vk_album import url_manager,authorize

urlpatterns = [
    url(r'^projects/vk_album/$', url_manager, name='Form'),
    url(r'^projects/vk_album/download/$', url_manager, name='Form'),
    url(r'^projects/vk_album/authorize/$', authorize, name='authorize'),
]
