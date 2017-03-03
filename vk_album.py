from django import forms
from django.shortcuts import render, redirect
from django.http import HttpResponseRedirect, HttpResponse
from django.core.urlresolvers import reverse
from zipfile import ZipFile
import os.path
import requests, re, os


# Исходные данные
VK_CLIENT_ID = ''
VK_CLIENT_SECRET = ''
REDIRECT_URL = ''


# Авторищация
def authorize(request):
    
    code = request.GET.get('code')
    
    response = requests.get(
        'https://oauth.vk.com/access_token?client_id=%s&client_secret=%s&redirect_uri=%s&code=%s'
        % (VK_CLIENT_ID, VK_CLIENT_SECRET, REDIRECT_URL, code)).json()
    
    request.session['access_token'] = response['access_token']
    
    return redirect('Form')


# Главная форма
class FormAlbum(forms.Form):
    
    url_album = forms.CharField(
        widget=forms.Textarea(
            attrs={
                'class': 'form-control materail_input',
                'rows': '1', 'style': 'resize:none',
                'placeholder':'https://vk.com/album-72495085_214965919',
            }))


# Обработчик формы
def url_manager(request):
    
    if request.method == 'POST':
        form = FormAlbum(request.POST)
        # Проверяем введенные пользователем данные на наличие слова альбом, т.к все альбомы вконтакте содержат слово.
        if re.findall('album',request.POST.get('url_album')) == ['album']:

            # Удаляем все символы заканчивающиеся слово album и разделяем
            url_album = re.sub('.*album', '', request.POST.get('url_album')).split("_")
            
            if 'access_token' in request.session:
                token = '&access_token=%s' % request.session['access_token']
            else:
                token = ''

            # фотографии на странице
            if url_album[1] == '0':
                
                photos_get = requests.post(
                    'https://api.vk.com/method/photos.get?owner_id=%s&count=1000&album_id=profile&v=5.50%s'
                    % (str(url_album[0]), token)).json()
                
                return DownloadUrl(photos_get, url_album)

            # фотографии на стене
            elif url_album[1] == '00?rev=1':
                
                photos_get = requests.post(
                    'https://api.vk.com/method/photos.get?owner_id=%s&count=1000&album_id=wall&v=5.50%s'
                    % (str(url_album[0], token))).json()
                
                return DownloadUrl(photos_get, url_album)

            # сохраненные фотографии
            elif url_album[1] == '000':
                
                photos_get = requests.post(
                    'https://api.vk.com/method/photos.get?owner_id=%s&count=1000&album_id=saved&v=5.50%s'
                    % (str(url_album[0]), token)).json()
                
                return DownloadUrl(photos_get, url_album)

            # Обычный альбом
            elif re.match ('\d', str(url_album [1])) != None:
                photos_get = requests.post(
                    'https://api.vk.com/method/photos.get?owner_id=%s&count=1000&album_id=%s&v=5.50%s'
                    % (str(url_album[0]), str(url_album[1]), token)).json()
                
                return DownloadUrl(photos_get, url_album)
            
            else:
                # Ошибка пользователю, что не правильно введена ссылка
                return render(request, 'vk_album.html', {'error': 'Введите правильную ссылку','form': form})

        else:
            # Ошибка пользователю, что не правильно введена ссылка
            return render(request, 'vk_album.html', {'error': 'Введите правильную ссылку','form': form})
        
    else:
        form = FormAlbum()

    # отрисовка страницы с формой
    return render(request, 'vk.html', {'form': form})


# Обработка и загрузка
def DownloadUrl(photos_get, url_album):

    # директория для загрузки
    download_dir = '/home/ilya/%s' % url_album[0]
    
    if os.path.exists(download_dir) is True:
        os.rmdir(download_dir)
    else:
        os.mkdir(download_dir)
    
    # Выборка у каждого объекта лучшего разрешения
    for photo in photos_get['response']['items']:
            if 'photo_1280' in photo:
                os.system('wget -P %s %s' % (download_dir, photo['photo_1280']))
            elif 'photo_807' in photo:
                os.system('wget -P %s %s' % (download_dir, photo['photo_807']))
            elif 'photo_604' in photo:
                os.system('wget -P %s %s' %( download_dir, photo['photo_604']))
            elif 'photo_130' in photo:
                os.system('wget -P %s %s' % (download_dir, photo['photo_130']))
            elif 'photo_75' in photo:
                os.system('wget -P %s %s' % (download_dir, photo['photo_75']))

    # Архивирование изображений
    zip=ZipFile('%s.zip' % download_dir,mode='w')
    for root, dirs, files in os.walk(download_dir):
        for file in files:
            zip.write(os.path.join(root,file),arcname=os.path.join('Album', file))
    zip.close()

    # Удаялем директорию в которую производилась закачка
    os.system('rm -R %s' % download_dir)

    # Отдаем файл пользователю
    response = HttpResponse(open('%s.zip' % download_dir, 'rb').read(),content_type='application/zip')
    response['Content-Disposition'] = 'attachment; filename=%s.zip' % url_album[1]

    return response
