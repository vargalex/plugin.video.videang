# -*- coding: utf-8 -*-

'''
    videaNG Addon
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


import os,sys,re,xbmc,xbmcgui,xbmcplugin,xbmcaddon,urllib,urlparse,base64,time, json
import urlresolver
from resources.lib.modules import client

sysaddon = sys.argv[0] ; syshandle = int(sys.argv[1])
addonFanart = xbmcaddon.Addon().getAddonInfo('fanart')

base_url = 'aHR0cHM6Ly92aWRlYS5odQ=='.decode('base64')
base_url_http = 'aHR0cDovL3ZpZGVhLmh1'.decode('base64')

class navigator:
    def root(self):
        mainMenu = {'menu-categories': 'Kategóriák', 'menu-channels': 'Csatornák'}
        for menuItem in mainMenu:
            self.addDirectoryItem(mainMenu[menuItem], 'submenus&url=%s' % menuItem, '', 'DefaultFolder.png')
        self.addDirectoryItem('Keresés', 'search', '', 'DefaultFolder.png')
        self.endDirectory()

    def getSubmenus(self, url):
        url_content = client.request('%s' % base_url)
        mainMenu = client.parseDOM(url_content, 'ul', attrs={'class': 'main-menu-list'})[0]
        menuItems = client.parseDOM(mainMenu, 'li')
        for menuItem in menuItems:
            if ('id="%s"' % url in menuItem):
                ul = client.parseDOM(menuItem, 'ul')[0]
                subMenuItems = client.parseDOM(ul, 'li')
                for subMenuItem in subMenuItems:
                    name = client.parseDOM(subMenuItem, 'a')[0].encode('utf-8')
                    href = client.parseDOM(subMenuItem, 'a', ret='href')[0].replace(base_url, '')
                    self.addDirectoryItem(name, 'videos&url=%s' % urllib.quote_plus(href), '', 'DefaultFolder.png')
        self.endDirectory('movies')

    def doSearch(self):
        search_text = self.getSearchText()
        if search_text != '':
            self.getVideos(url="/video_kereses/%s" % urllib.quote(search_text, safe='*'), params=None)

    def getVideos(self, url, params):
        url_content = client.request('%s%s%s' % (base_url, url, '' if params == None else params))
        if "adult-content" in url_content:
            if not xbmcgui.Dialog().yesno('Felnőtt tartalom!', 'Ez a tartalom olyan elemeket tartalmazhat, amelyek a hatályos jogszabályok kategóriái szerint kiskorúakra károsak lehetnek. Ha azt szeretnéd, hogy az ilyen tartalmakhoz erről a számítógépről kiskorú ne férhessen hozzá, használj szűrőprogramot!', line2='Ha elmúltál 18 éves, az "Elmúltam 18 éves" gombra kattinthatsz és a tartalom a számodra elérhető lesz.', line3='Ha nem múltál el 18 éves, kattints a "Nem múltam el 18 éves" gombra; ez a tartalom a számodra nem lesz elérhető.', nolabel='Nem múltam el 18 éves', yeslabel='Elmúltam 18 éves'):
                return                
            url_content = client.request('%s%s' % (base_url, url), cookie="session_adult=1")
        videos = client.parseDOM(url_content, 'div', attrs={'class': 'panel panel-video'})
        for video in videos:
            heading = client.parseDOM(video, 'div', attrs={'class': 'panel-heading'})
            href = client.parseDOM(heading, 'a', attrs={'class': 'video-link'}, ret='href')[0]
            img = client.parseDOM(heading, 'a', attrs={'class': 'video-link'})[0]
            img = client.parseDOM(img, 'img', attrs={'class': 'video-thumbnail'}, ret='src')[0]
            durationStr = client.parseDOM(heading, 'span', attrs={'class': 'label label-black video-length'})[0]
            duration = sum(x * int(t) for x, t in zip([3600, 60, 1], durationStr.split(":")))
            body = client.parseDOM(video, 'div', attrs={'class': 'panel-body'})[0]
            videotext = client.parseDOM(body, 'div', attrs={'class': 'panel-video-text'})[0]
            videotitle = client.parseDOM(videotext, 'div', attrs={'class': 'panel-video-title'})[0]
            title = client.replaceHTMLCodes(client.parseDOM(videotitle, 'a')[0]).encode('utf-8')
            self.addDirectoryItem(title, 'playmovie&url=%s' % href, "%s%s" % ('' if 'http' in img else base_url, img), 'DefaultMovies.png', meta={'title': title, 'plot': '', 'duration': duration}, isFolder=False)
        if "pagination" in url_content:
            pagination = client.parseDOM(url_content, 'ul', attrs={'class': 'pagination'})
            lis = client.parseDOM(pagination, 'li')
            kovetkezo = client.parseDOM(lis[len(lis)-1], 'a', ret='href')[0]
            self.addDirectoryItem(u'[I]K\u00F6vetkez\u0151 oldal >>[/I]', 'videos&url=%s&params=%s' % (urllib.quote_plus(url), urllib.quote_plus(kovetkezo)), '', 'DefaultFolder.png')
        self.endDirectory('movies')

    def playmovie(self, url):
        xbmc.log('VideaNG: resolving url: %s' % url, xbmc.LOGNOTICE)
        try:
            direct_url = urlresolver.resolve(url)
            if direct_url:
                direct_url = direct_url.encode('utf-8')
        except Exception as e:
            xbmcgui.Dialog().notification(urlparse.urlparse(url).hostname, e.message)
            return
        if direct_url:
            xbmc.log('VideaNG: playing URL: %s' % direct_url, xbmc.LOGNOTICE)
            play_item = xbmcgui.ListItem(path=direct_url)
            xbmcplugin.setResolvedUrl(syshandle, True, listitem=play_item)

    def addDirectoryItem(self, name, query, thumb, icon, context=None, queue=False, isAction=True, isFolder=True, Fanart=None, meta=None, banner=None):
        url = '%s?action=%s' % (sysaddon, query) if isAction == True else query
        if thumb == '': thumb = icon
        cm = []
        if queue == True: cm.append((queueMenu, 'RunPlugin(%s?action=queueItem)' % sysaddon))
        if not context == None: cm.append((context[0].encode('utf-8'), 'RunPlugin(%s?action=%s)' % (sysaddon, context[1])))
        item = xbmcgui.ListItem(label=name)
        item.addContextMenuItems(cm)
        item.setArt({'icon': thumb, 'thumb': thumb, 'poster': thumb, 'banner': banner})
        if Fanart == None: Fanart = addonFanart
        item.setProperty('Fanart_Image', Fanart)
        if isFolder == False: item.setProperty('IsPlayable', 'true')
        if not meta == None: item.setInfo(type='Video', infoLabels = meta)
        xbmcplugin.addDirectoryItem(handle=syshandle, url=url, listitem=item, isFolder=isFolder)


    def endDirectory(self, type='addons'):
        xbmcplugin.setContent(syshandle, type)
        #xbmcplugin.addSortMethod(syshandle, xbmcplugin.SORT_METHOD_TITLE)
        xbmcplugin.endOfDirectory(syshandle, cacheToDisc=True)

    def getSearchText(self):
        search_text = ''
        keyb = xbmc.Keyboard('',u'Add meg a keresend\xF5 film c\xEDm\xE9t')
        keyb.doModal()

        if (keyb.isConfirmed()):
            search_text = keyb.getText()

        return search_text
