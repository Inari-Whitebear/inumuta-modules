# coding=utf-8
"""
mcstatus.py - Check minecraft server status / services related things -- Uses Dinnerbone's python server status lib
Copyright 2014 Max Gurela

Licensed under the Eiffel Forum License 2.
"""
from __future__ import unicode_literals
from mcstatus import MinecraftServer
from sopel.module import commands
from sopel import web
from sopel.formatting import color, bold
import uuid
import time
import json
import re


@commands('uuid')
def get_uuid(bot, trigger):
    """
    .uuid [username] [timestamp] - Get a minecraft username's UUID. You may specify a timestamp, though UNIX format is the only supported format.
    """
    username = trigger.group(3)
    if not username:
        username = trigger.nick
    timestamp = trigger.group(4)
    if not timestamp:
        timestamp = str(int(time.time()))
    raw = web.get('https://api.mojang.com/users/profiles/minecraft/{0}?at={1}'.format(username, timestamp))
    if raw == '':
        bot.say('{0} does not exist'.format(username))
        return
    response = json.loads(raw)
    bot.say('{0}\'s UUID: {1}'.format(response['name'], str(uuid.UUID(response['id']))))


@commands('status')
def status(bot, trigger):
    """
    .status <server> - Grabs information about a minecraft server!
    """
    try:
        server = MinecraftServer.lookup(trigger.group(3).strip())
    except Exception:
        bot.say('[MCS] Unable to find a Minecraft server running at \'{}\''.format(trigger.group(3).strip()))

    try:
        status = server.status()
        desc = status.description
        if isinstance(status.description, dict):
            desc = status.description['text']
        srv_type = 'Vanilla'
        srv_version = '???'
        if status.version.name:
            srv_version = status.version.name
        modinfo = status.raw.get('modinfo', None)
        if modinfo:
            srv_type = modinfo.get('type', '???')
            mod_count = len(modinfo.get('modList', []))
            srv_version = '{} ({:,} mods)'.format(srv_version, mod_count)
        desc = ' '.join(re.sub('\u00A7.', '', desc).split())
        bot.say('[MCS] {} | {} {} | {} players | {} ms | {}'.format(trigger.group(3).strip(), srv_type, srv_version, status.players.online, status.latency, desc))
    except Exception as e:
        bot.say('[MCS] Unable to fetch info from \'{}\' ({})'.format(trigger.group(3).strip(), e))


@commands('mcstatus', 'mcs')
def mcstats(bot, trigger):
    """
    .mcstatus - Check the status of Mojang's servers
    """
    try:
        raw = web.get('https://status.mojang.com/check')

        response = json.loads(raw.replace("}", "").replace("{", "").replace("]", "}").replace("[", "{"))

        out = []
        # use a loop so we don't have to update it if they add more servers
        for server, status in response.items():
            out.append('{} {} '.format(server, format_status(status)))
        bot.say(''.join(out))
    except Exception as e:
        bot.say('[MCS] Mojang server status check is currently offline. ({})'.format(e))


@commands('mcpaid', 'haspaid')
def mcpaid(bot, trigger):
    """
    .mcpaid <username> - Checks if <username> has a premium Minecraft account.
    """
    users = trigger.nick
    if (trigger.group(2)):
        users = trigger.group(2).strip()
    for user in users.split():
        has_paid(bot, user)


def has_paid(bot, user):
    status = web.get('https://www.minecraft.net/haspaid.jsp?user={}'.format(user))
    if 'true' in status:
        bot.say('The account \'{}\' is a premium Minecraft account!'.format(user))
    else:
        bot.say('The account \'{}\' is not a premium Minecraft account!'.format(user))


def format_status(status):
    return status.replace('red', color('\u2718', 'red')).replace('green', color('\u2713', 'green')).replace('yellow', color('~', 'yellow'))
