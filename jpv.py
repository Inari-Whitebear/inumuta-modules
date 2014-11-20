# coding=utf8
"""
jpv.py - J-Pop and Vocaloid songs
Copyright 2014 Max Gurela

Licensed under the Eiffel Forum License 2.
"""

from willie.module import commands,rule
import willie.web as web
import urllib
import json

@rule('https?://jpv\.everythingisawesome\.us/song/\?genre=(.+)&song=(.+)')
def jpv_info(bot, trigger):
    song = None
    try:
        song = info(trigger.group(1).strip(), trigger.group(2).strip())
    except Exception:
        return
    bot.say('[JPV] ' + song['artist'] + ' - ' + song['title'] + ' | ' + song['album'] + ' | ' + song['album_artist'] + ' | ' + song['genre'])

def info(genre, title):
    if '.mp3' not in title:
        title = title+'.mp3'
    genre = urllib.unquote(genre)
    title = urllib.unquote(title)
    request = web.get('http://jpv.everythingisawesome.us/api/v1/song/'+genre+'/'+title)
    return json.loads(request)

def search(title):
    request = web.get('http://jpv.everythingisawesome.us/api/v1/list.php?genre=all&format=json')
    songs = json.loads(request)
    for song in songs:
        if song['title'].lower() == title.lower():
            return song
    return None

@commands('jpv')
def jpv(bot, trigger): 
    song = search(trigger.group(2).strip())
    if song is None:
        bot.say('[JPV] Unable to find a song matching \"'+trigger.group(2).strip()+'\"')
    else:
        bot.say('[JPV] ' + song['artist'] + ' - ' + song['title'] + ' | ' + song['album'] + ' | ' + song['album_artist'] + ' | ' + song['genre'] + ' | http://jpv.everythingisawesome.us/song/?song={}'.format(song['filename'].replace('.mp3', '')))

