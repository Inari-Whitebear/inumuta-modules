# coding=utf-8
"""
imgur.py - Sopel imgur Information Module
Copyright 2014, Max Gurela
Copyright © 2014, iceTwy, <icetwy@icetwy.re>

Licensed under the Eiffel Forum License 2.
"""
from __future__ import unicode_literals
import json
import re
import os.path
import sys
if sys.version_info.major < 3:
    from urllib2 import HTTPError
    from urlparse import urlparse
else:
    from urllib.error import HTTPError
    from urllib.parse import urlparse
from sopel.config.types import StaticSection, ValidatedAttribute
from sopel.config import ConfigurationError
from sopel import web, tools
from sopel.module import rule


class ImgurSection(StaticSection):
    client_id = ValidatedAttribute('client_id', default=None)


class ImgurClient(object):
    def __init__(self, client_id):
        """
        Sets the client_id (obtain yours here: https://api.imgur.com/oauth2/addclient)
        and the imgur API URL.
        """
        self.client_id = client_id
        self.api_url = "https://api.imgur.com/3/"

    def request(self, input):
        """
        Sends a request to the API. Only publicly available data is accessible.
        Returns data as JSON.
        """
        headers = {'Authorization': 'Client-ID ' + self.client_id,
                   'Accept': 'application/json'}
        request = web.get(self.api_url + input, headers=headers)
        #FIXME: raise for status
        return json.loads(request)

    def resource(self, resource, id):
        """
        Retrieves a resource from the imgur API.
        Returns data as JSON.
        """
        api_request_path = '{0}/{1}'.format(resource, id)
        return self.request(api_request_path)


def configure(config):
    config.define_section('imgur', ImgurSection, validate=False)
    config.imgur.configure_setting('client_id', 'Imgur API Client ID')


def setup(bot):
    bot.config.define_section('imgur', ImgurSection)
    """
    Tests the validity of the client ID given in the configuration.
    If it is not, initializes sopel's memory callbacks for imgur URLs,
    and uses them as the trigger for the link parsing function.
    """
    if not bot.config.imgur.client_id:
        raise ConfigurationError('Could not setup the Imgur module. Is '
                                 'the API key configured properly?')
    try:
        client = ImgurClient(bot.config.imgur.client_id)
        client.request('gallery.json')
    except HTTPError:
        raise ConfigurationError('Could not validate the client ID with Imgur.'
                     ' Have you run "sopel --configure-modules" or specified '
                     'the Imgur API key in the config?')
    imgur_regex = re.compile('(?:https?://)?(?:i\.)?imgur\.com/(.*)$')
    if not bot.memory.contains('url_callbacks'):
        bot.memory['url_callbacks'] = tools.SopelMemory()
    bot.memory['url_callbacks'][imgur_regex] = imgur


def album(link_id, bot):
    """
    Handles information retrieval for non-gallery albums.
    The bot will output the title, the number of images and the number of views
    of the album.
    """
    try:
        client = ImgurClient(bot.config.imgur.client_id)
        api_response = client.resource('album', link_id)
        album = api_response['data']
        return bot.say('[imgur] [{0} - {1} images, ' \
                       '{2} views]'.format(album['title'],
                                           str(album['images_count']), \
                                           str(album['views'])))
    except:
        return


def gallery(link_id, bot):
    """
    Handles information retrieval for gallery images and albums.
    The bot will output the title, the type (image/album/gif), the number of
    views, the number of upvotes/downvotes of the gallery resource.
    """
    try:
        client = ImgurClient(bot.config.imgur.client_id)
        api_response = client.resource('gallery', link_id)
        gallery = api_response['data']
        if gallery['is_album']:
            return bot.say('[imgur] [{0} - {1} views ' \
                           '({2}+ and {3}-)]'.format(gallery['title'], \
                                                             str(gallery['views']), \
                                                             str(gallery['ups']), \
                                                             str(gallery['downs'])))
        if gallery['animated'] is True:
            return bot.say('[imgur] [{0} - {1} views ' \
                           '({2}+ and {3}-)]'.format(gallery['title'], \
                                                             str(gallery['views']), \
                                                             str(gallery['ups']), \
                                                             str(gallery['downs'])))
        else:
            return bot.say('[imgur] [{0} - {1} views ' \
                           '({2}+ and {3}-)]'.format(gallery['title'], \
                                                             str(gallery['views']),
                                                             str(gallery['ups']),
                                                             str(gallery['downs'])))
    except:
        return


def user(username, bot):
    """
    Handles information retrieval for user accounts.
    The bot will output the name, and the numbers of submissions, comments and
    liked resources, of the selected user.
    """
    try:
        client = ImgurClient(bot.config.imgur.client_id)
        api_response_account = client.resource('account', username)
        api_response_gallery_profile = client.resource('account', username + '/gallery_profile')
        account = api_response_account['data']
        gallery_profile = api_response_gallery_profile['data']
        return bot.say('[imgur] [{0} | {1} rep, ' \
                       '{2} gallery submissions, {3} comments ' \
                       'and {4} likes]'.format(account['url'], \
                                               str(account['reputation']), \
                                               str(gallery_profile['total_gallery_submissions']), \
                                               str(gallery_profile['total_gallery_comments']), \
                                               str(gallery_profile['total_gallery_likes'])))
    except:
        return


def image(link_id, bot):
    """
    Handles information retrieval for non-gallery images.
    The bot will output the title, the type (image/gif) and the number of views
    of the selected image.
    """
    try:
        client = ImgurClient(bot.config.imgur.client_id)
        api_response = client.resource('image', link_id)
        img = api_response['data']
        if img['title']:
            title = img['title']
        if not img['title'] and img['description']:
            title = img['description']
        if not img['title'] and not img['description']:
            title = 'untitled'
        if img['animated']:
            return bot.say('[imgur] [{0} - {1} views]'.format(title, str(img['views'])))
        else:
            return bot.say('[imgur] [{0} - {1} views]'.format(title, str(img['views'])))
    except:
        return


@rule('.*(?:i\.)?imgur\.com/(.*)(?: .+)?.*')
def imgur(bot, trigger):
    """
    Parses the input URL and calls the appropriate function for the resource
    (an image or an album).

    imgur has two types of resources: non-gallery and gallery resources.
    Non-gallery resources are images and albums that have not been uploaded
    to the imgur gallery (imgur.com/gallery), whilst gallery resources have
    been.

    * imgur.com/id can refer to two distinct resources (i.e. a non-gallery image
    and a gallery resource, e.g. imgur.com/VlmfH and imgur.com/gallery/VlmfH)

    * i.imgur.com/id refers by default to the same non-gallery resource as
      imgur.com/id, if there are two distinct resources for this ID.
      It refers to the gallery resource if only the gallery resource exists.

    * imgur.com/gallery/id refers solely to a gallery resource.

    * imgur.com/a/id refers solely to an album. Non-gallery data is returned,
      even if it is in the gallery.

    * imgur.com/user/username refers solely to an imgur user account.

    The regex rule above will capture either an ID to a gallery or non-gallery
    image or album, or a path to a certain imgur resource (e.g. gallery/id,
    user/username, and so forth).

    It is more fool-proof to only demand gallery data from the imgur API
    if we get a link that is of the form imgur.com/gallery/id, because
    imgur IDs are not unique (see above) and we can trigger an error if
    we request inexistant gallery data.
    """

    #urlparse does not support URLs without a scheme.
    #Add 'https' scheme to an URL if it has no scheme.
    if not urlparse(trigger).scheme:
        trigger = "https://" + trigger

    """Handle i.imgur.com links first.
    They can link to non-gallery images, so we do not request gallery data,
    but simply image data."""
    if urlparse(trigger).netloc == 'i.imgur.com':
        image_id = os.path.splitext(os.path.basename(urlparse(trigger).path))[0]  # get the ID from the img
        return image(image_id, bot)

    """Handle imgur.com/* links."""
    #Get the path to the requested resource, from the URL (id, gallery/id, user/username, a/id)
    resource_path = urlparse(trigger).path.lstrip('/')

    #The following API endpoints require user authentication, which we do not support.
    unauthorized = ['settings', 'notifications', 'message', 'stats']
    if any(item in resource_path for item in unauthorized):
        return bot.reply("[imgur] Unauthorized action.")

    #Separate the URL path into an ordered list of the form ['gallery', 'id']
    resource_path_parts = filter(None, resource_path.split('/'))[-2:]

    #bot.reply(str(resource_path_parts))

    #Handle a simple link to imgur.com: no ID is given, meaning that the length of the above list is null
    if len(resource_path_parts) == 0:
        return

    #Handle a link with a path that has more than two components
    if len(resource_path_parts) > 2:
        return bot.reply("[imgur] Invalid link.")

    #Handle a link to an ID: imgur.com/id
    if len(resource_path_parts) == 1:
        return image(resource_path_parts[0], bot)

    #Handle a link to a gallery image/album: imgur.com/gallery/id
    if resource_path_parts[0] == 'gallery':
        return gallery(resource_path_parts[1], bot)

    #Handle a link to an user account/profile: imgur.com/user/username
    if resource_path_parts[0] == 'user':
        return user(resource_path_parts[1], bot)

    #Handle a link to an album: imgur.com/a/id
    if resource_path_parts[0] == 'a':
        return album(resource_path_parts[1], bot)
