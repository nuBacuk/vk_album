from django import forms
from django.shortcuts import render
from django.http import HttpResponseRedirect, HttpResponse
from zipfile import ZipFile,ZIP_DEFLATED
import requests, re, os

#Исходные данные
client_id = '5366333' #client_id вашего приложения
client_secret = 'g8uyxFMdQcnL9Hak5hup'  #Секретный ключи вашего приложения
redirect_uri = 'http://127.0.0.1:8000/projects/vk_album/authorize'  #Ссылка для перееадресации указанная в приложении

#Авторищация
def authorize(request):
    code = request.GET.get('code')
    redirect_url = __get_redirect_url(request)

    response = (requests.get(
        'https://oauth.vk.com/access_token?client_id=%s&client_secret=%s&redirect_uri=%s&code=%s'
        % (client_id, client_secret, redirect_url, code))).json()
    
    request.session['access_token'] = response['access_token']

        return HttpResponseRedirect ('/projects/vk_album/')
    
def __get_redirect_url(request):
    redirect_url = "%s://%s%s" % (
        request.META['wsgi.url_scheme'], request.META['HTTP_HOST'], reverse('auth'))
    return redirect_url

#Главная форма
class Form_Album(forms.Form):
    url_album = forms.CharField(widget=forms.Textarea(attrs={'class': 'form-control materail_input', 'rows': '1', 'style': 'resize:none','placeholder':'https://vk.com/album-72495085_214965919'}))

#Обработчик формы
def Url_Manager(request):
    if request.method == 'POST':
        form = Form_Album(request.POST)
        #Проверяем введенные пользователем данные на наличие слова альбом, т.к все альбомы вконтакте содержат слово.
        if re.findall('album',request.POST.get('url_album')) == ['album']:

            #Удаляем все символы заканчивающиеся слово album и разделяем
            url_album = re.sub('.*album','',request.POST.get('url_album')).split("_")

            #фотографии на странице
            if url_album[1] == '0':
                photos_get = (requests.post('https://api.vk.com/method/photos.get?owner_id=%s&album_id=profile&count=11&v=5.50', %str(url_album[0]))).json()
                return Download_Url(photos_get,url_album)

            #фотографии на стене
            elif url_album[1] == '00?rev=1':
                photos_get = (requests.post('https://api.vk.com/method/photos.get?owner_id=%s&album_id=wall&count=11&v=5.50', %str(url_album[0]))).json()
                return Download_Url(photos_get,url_album)

            #сохраненные фотографии
            elif url_album[1] == '000':
                photos_get = (requests.post('https://api.vk.com/method/photos.get?owner_id=%s&album_id=saved&count=11&v=5.50', %str(url_album[0]))).json()
                return Download_Url(photos_get,url_album)

            #Обычный альбом
            elif re.match ('\d',str(url_album [1])) != None:
                photos_get = (requests.post('https://api.vk.com/method/photos.get?owner_id=%s&album_id=%s&v=5.50', % (str(url_album[0]), str(url_album[1])))).json()
                return Download_Url(photos_get,url_album)
            else:
                #Ошибка пользователю, что не правильно введена ссылка
                return render(request, 'vk_album.html', {'error': 'Введите правильную ссылку','form': form})

        else:
            #Ошибка пользователю, что не правильно введена ссылка
            return render(request, 'vk_album.html', {'error': 'Введите правильную ссылку','form': form})
    else:
        form = Form_Album()

    #отрисовка страницы с формой
    return render(request, 'vk_album.html', {'form': form})


#Обработка и загрузка
def Download_Url(photos_get,url_album):

    #директория для загрузки
    download_dir = '/home/khramtsov/vk_album/'+url_album[0]

    os.mkdir(download_dir)

    #Выборка у каждого объекта лучшего разрешения
    for slice in photos_get['response']['items']:
            if 'photo_1280' in slice:
                os.system('wget -P %s%s', % (download_dir, slice['photo_1280']))
            elif 'photo_807' in slice:
                os.system('wget -P %s%s', % (download_dir, slice['photo_807']))
            elif 'photo_604' in slice:
                os.system('wget -P %s%s', % (download_dir, slice['photo_604']))
            elif 'photo_130' in slice:
                os.system('wget -P %s%s', % (download_dir, slice['photo_130']))
            elif 'photo_75' in slice:
                os.system('wget -P %s%s', % (download_dir, slice['photo_75']))

    #Архивирование изображений
    zip=ZipFile(download_dir+'.zip',mode='w')
    for root, dirs, files in os.walk(download_dir):
        for file in files:
            zip.write(os.path.join(root,file),arcname=os.path.join('Album', file))
    zip.close()

    #Удаялем директорию в которую производилась закачка
    os.system('rm -R '+download_dir)

    #Отдаем файл пользователю
    response = HttpResponse(open(download_dir+'.zip', 'rb').read(),content_type='application/zip')
    response['Content-Disposition'] = 'attachment; filename='+url_album[1]+'.zip'

    return response
