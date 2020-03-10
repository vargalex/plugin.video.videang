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


import urlparse,sys, xbmcgui

params = dict(urlparse.parse_qsl(sys.argv[2].replace('?','')))

action = params.get('action')

url = params.get('url')

search = params.get('search')

params = params.get('params')

if action == None:
    from resources.lib.indexers import navigator
    navigator.navigator().root()

elif action == 'submenus':
    from resources.lib.indexers import navigator
    navigator.navigator().getSubmenus(url)


elif action == 'videos':
    from resources.lib.indexers import navigator
    navigator.navigator().getVideos(url, params)

elif action == 'playmovie':
    from resources.lib.indexers import navigator
    navigator.navigator().playmovie(url)

elif action == 'search':
    from resources.lib.indexers import navigator
    navigator.navigator().doSearch()
