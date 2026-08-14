# -*- coding: utf-8 -*-

'''
    videa Add-on
    Copyright (C) 2020

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.
'''


import sys, xbmcgui

if sys.version_info[0] == 3:
    from urllib.parse import parse_qsl
else:
    from urlparse import parse_qsl

params = dict(parse_qsl(sys.argv[2].replace('?','')))

action = params.get('action')

url = params.get('url')

ulclass = params.get('ulclass')

cacheId = params.get('cacheid')

lastItemId = params.get('lastitemid')

itemCount = params.get('itemcount')

itemCount = int(itemCount or 0)

from resources.lib.indexers import navigator

if action == None:
    navigator.navigator().root()

if action == 'menus':
    navigator.navigator().menus(url)

elif action == 'submenus':
    navigator.navigator().getSubmenus(url, ulclass)

elif action == 'videos':
    navigator.navigator().getVideos(url, cacheId, lastItemId, itemCount)

elif action == 'playmovie':
    navigator.navigator().playmovie(url)

elif action == 'search':
    navigator.navigator().getSearches(url)

elif action == 'newsearch':
    navigator.navigator().doSearch(url)

elif action == 'deletesearchhistory':
    navigator.navigator().deleteSearchHistory(url)

elif action == 'playvideaurl':
    navigator.navigator().playVideaUrl()

elif action == 'playdirecturl':
    navigator.navigator().playDirectUrl()

elif action == 'logout':
    navigator.navigator().logout()
