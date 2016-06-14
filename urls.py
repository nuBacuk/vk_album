from devel0per.vk_album import Url_Manager,Authorize

urlpatterns = [
    url(r'^projects/vk_album/$', Url_Manager, name='Form'),
    url(r'^projects/vk_album/download/$', Url_Manager, name='Form'),
    url(r'^projects/vk_album/authorize/$', Authorize, name='Authorize'),
]