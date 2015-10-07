# coding=utf8
"""
twitter.py - Sopel Twitter Module
Copyright 2014 Max Gurela
Copyright 2008-10, Michael Yanovich, opensource.osu.edu/~yanovich/wiki/
Copyright 2011, Edward Powell, embolalia.net
Licensed under the Eiffel Forum License 2.

http://sopel.dftba.net
"""
from __future__ import unicode_literals
import tweepy
import time
import re
from sopel.config import ConfigurationError
from sopel import tools
from sopel.module import rule
import sys
import HTMLParser

if sys.version_info.major < 3:
    str = unicode


def configure(config):
    """
    These values are all found by signing up your bot at
    [https://dev.twitter.com/apps/new](https://dev.twitter.com/apps/new).

    | [twitter] | example | purpose |
    | --------- | ------- | ------- |
    | consumer_key | 09d8c7b0987cAQc7fge09 | OAuth consumer key |
    | consumer_secret | LIaso6873jI8Yasdlfi76awer76yhasdfi75h6TFJgf | OAuth consumer secret |
    | access_token | 564018348-Alldf7s6598d76tgsadfo9asdf56uUf65aVgdsf6 | OAuth access token |
    | access_token_secret | asdfl7698596KIKJVGvJDcfcvcsfdy85hfddlku67 | OAuth access token secret |
    """

    if config.option('Configure Twitter? (You will need to register on http://api.twitter.com)', False):
        config.interactive_add('twitter', 'consumer_key', 'Consumer key')
        config.interactive_add('twitter', 'consumer_secret', 'Consumer secret')
        config.interactive_add('twitter', 'access_token', 'Access token')
        config.interactive_add('twitter', 'access_token_secret', 'Access token secret')


def setup(sopel):
    try:
        auth = tweepy.OAuthHandler(sopel.config.twitter.consumer_key, sopel.config.twitter.consumer_secret)
        auth.set_access_token(sopel.config.twitter.access_token, sopel.config.twitter.access_token_secret)
        api = tweepy.API(auth)
    except:
        raise ConfigurationError('Could not authenticate with Twitter. Are the'
                                 ' API keys configured properly?')
    regex = re.compile('twitter.com\/(\S*)\/status\/([\d]+)')
    user_regex = re.compile('twitter.com\/([^\/]+)$')
    if not sopel.memory.contains('url_callbacks'):
        sopel.memory['url_callbacks'] = tools.SopelMemory()
    sopel.memory['url_callbacks'][regex] = gettweet
    sopel.memory['url_callbacks'][user_regex] = f_info


def format_thousands(integer):
    """Returns string of integer, with thousands separated by ','"""
    return re.sub(r'(\d{3})(?=\d)', r'\1,', str(integer)[::-1])[::-1]


def tweet_url(status):
    """Returns a URL to Twitter for the given status object"""
    return 'https://twitter.com/' + status.user.screen_name + '/status/' + status.id_str


@rule('.*twitter.com\/(\S*)\/status\/([\d]+).*')
def gettweet(sopel, trigger, found_match=None):
    """Show the last tweet by the given user"""
    try:
        auth = tweepy.OAuthHandler(sopel.config.twitter.consumer_key, sopel.config.twitter.consumer_secret)
        auth.set_access_token(sopel.config.twitter.access_token, sopel.config.twitter.access_token_secret)
        api = tweepy.API(auth)

        if found_match:
            status = api.get_status(found_match.group(2))
        else:
            parts = trigger.group(2).split()
            if parts[0].isdigit():
                status = api.get_status(parts[0])
            else:
                twituser = parts[0]
                twituser = str(twituser)
                statusnum = 0
                if len(parts) > 1 and parts[1].isdigit():
                    statusnum = int(parts[1]) - 1
                status = api.user_timeline(twituser)[statusnum]
        twituser = '@' + status.user.screen_name.strip()
        h = HTMLParser.HTMLParser()
        if trigger.group(1) == 'twit':
            sopel.say('[Twitter] ' + twituser + ": " + h.unescape(str(status.text).replace('\n', ' ')) + ' <' + tweet_url(status) + '>')
        else:
            sopel.say('[Twitter] ' + twituser + ": " + h.unescape(str(status.text).replace('\n', ' ')))
    except:
        sopel.reply("You have input an invalid user.")
gettweet.commands = ['twit', 'twitter']
gettweet.priority = 'medium'
gettweet.example = '.twit aplusk [tweetNum] or .twit 381982018927853568'


@rule(r'(.*)twitter.com\/([^\/]+)(?:\s.*)?$')
def f_info(sopel, trigger):
    """Show information about the given Twitter account"""
    try:
        auth = tweepy.OAuthHandler(sopel.config.twitter.consumer_key, sopel.config.twitter.consumer_secret)
        auth.set_access_token(sopel.config.twitter.access_token, sopel.config.twitter.access_token_secret)
        api = tweepy.API(auth)

        twituser = trigger.group(2)
        twituser = str(twituser)
        if '@' in twituser:
            twituser = twituser.translate(None, '@')

        info = api.get_user(twituser)
        friendcount = format_thousands(info.friends_count)
        name = info.name
        id = info.id
        favourites = info.favourites_count
        followers = format_thousands(info.followers_count)
        location = info.location
        description = info.description
        sopel.reply("@" + str(twituser) + ": " + str(name) + ". " + "ID: " + str(id) + ". Friend Count: " + friendcount + ". Followers: " + followers + ". Favourites: " + str(favourites) + ". Location: " + str(location) + ". Description: " + str(description))
    except:
        sopel.reply("You have input an invalid user.")
f_info.commands = ['twitinfo', 'twitter-info', 'twituser']
f_info.priority = 'medium'
f_info.example = '.twitinfo aplsuk'


def f_update(sopel, trigger):
    """Tweet with Sopel's account. Admin-only."""
    if trigger.admin:
        auth = tweepy.OAuthHandler(sopel.config.twitter.consumer_key, sopel.config.twitter.consumer_secret)
        auth.set_access_token(sopel.config.twitter.access_token, sopel.config.twitter.access_token_secret)
        api = tweepy.API(auth)

        print(api.me().name)

        update = str(trigger.group(2))
        if len(update) <= 140:
            api.update_status(update)
            sopel.reply("Successfully posted to my twitter account.")
        else:
            toofar = len(update) - 140
            sopel.reply("Please shorten the length of your message by: " + str(toofar) + " characters.")
f_update.commands = ['tweet']
f_update.priority = 'medium'
f_update.example = '.tweet Hello World!'


def f_reply(sopel, trigger):
    auth = tweepy.OAuthHandler(sopel.config.twitter.consumer_key, sopel.config.twitter.consumer_secret)
    auth.set_access_token(sopel.config.twitter.access_token, sopel.config.twitter.access_token_secret)
    api = tweepy.API(auth)

    incoming = str(trigger.group(2))
    incoming = incoming.split()
    statusid = incoming[0]
    if statusid.isdigit():
        update = incoming[1:]
        if len(update) <= 140:
            statusid = int(statusid)
            #api3.PostUpdate(str(" ".join(update)), in_reply_to_status_id=10503164300)
            sopel.reply("Successfully posted to my twitter account.")
        else:
            toofar = len(update) - 140
            sopel.reply("Please shorten the length of your message by: " + str(toofar) + " characters.")
    else:
        sopel.reply("Please provide a status ID.")
#f_reply.commands = ['reply']
f_reply.priority = 'medium'
f_reply.example = '.reply 892379487 I like that idea!'

if __name__ == '__main__':
    print(__doc__.strip())
