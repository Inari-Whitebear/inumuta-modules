"""
ud.py - A communication tool to aid Europe and USA understand each other in #crude on irc.freenode.net
Copyright 2014, justFen
Licensed under the Eiffel Forum License 2.

http://justfen.com
"""

import re
from willie import web
from willie.module import commands, example
from willie.formatting import color
from urllib2 import quote
import json
import sys

@commands('ud', 'udefine', 'urbandictionary', 'urbandict', 'udict')
@example('.ud bruh')
def ud_search(bot, trigger):
    query = trigger.group(2).strip()
    
    url = 'http://api.urbandictionary.com/v0/define?%s' %(web.urlencode({'term': quote(query.encode('utf-8'))}))
    url = url.replace(u'%25', u'%')
    #bot.say(url)
    try:
      response = urllib.urlopen(url)
    except UnicodeError:
      bot.say('[UrbanDictionary] ENGLISH MOTHERFUCKER, DO YOU SPEAK IT?')
      return
    else:
      data = json.loads(response.read())
      #bot.say(str(data))
    try:
      definition = data['list'][0]['definition']
    except KeyError:
      bot.say('[UrbanDictionary] Something went wrong bruh')
    except IndexError:
      bot.say('[UrbanDictionary] No results, do you even spell bruh?')
    else:
      thumbsup = data['list'][0]['thumbs_up']
      thumbsdown = data['list'][0]['thumbs_down']
      udoutput = "[UrbanDictionary] %s; %s >> %s %s" % (query, definition, color(str(thumbsup)+'+', u'03'), color(str(thumbsdown)+'-', u'04'))
      if not "spam spam" in udoutput:
          bot.say(udoutput)
      else:
          bot.say('[UrbanDictionary] Negative ghostrider')
