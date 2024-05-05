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


import os, sys, re, xbmc, xbmcgui, xbmcplugin, xbmcaddon, base64, random, string, struct, locale, json, time
from resources.lib.modules import client, xmltodict
from resources.lib.modules.utils import py2_encode, py2_decode, safeopen

if sys.version_info[0] == 3:
    import urllib.parse as urlparse
    from urllib.parse import quote, quote_plus, unquote_plus
    from xbmcvfs import translatePath
else:
    import urlparse
    from urllib import quote, quote_plus, unquote_plus
    from xbmc import translatePath


sysaddon = sys.argv[0] ; syshandle = int(sys.argv[1])
addonFanart = xbmcaddon.Addon().getAddonInfo('fanart')

base_url = 'https://videa.hu'

class navigator:

    def __init__(self):
        try:
            locale.setlocale(locale.LC_ALL, "hu_HU.UTF-8")
        except:
            try:
                locale.setlocale(locale.LC_ALL, "")
            except:
                pass
        self.base_path = py2_decode(translatePath(xbmcaddon.Addon().getAddonInfo('profile')))
        self.searchFileName = os.path.join(self.base_path, "search.history")
        self.downloadsubtitles = xbmcaddon.Addon().getSettingBool('downloadsubtitles')
        self.base_path = py2_decode(translatePath(xbmcaddon.Addon().getAddonInfo('profile')))
        self.login()

    def root(self):
        mainMenu = {'menu-categories': 'Kategóriák', 'menu-channels': 'Csatornák'}
        for menuItem in mainMenu:
            self.addDirectoryItem(mainMenu[menuItem], 'submenus&url=%s' % menuItem, '', 'DefaultFolder.png')
        self.addDirectoryItem('Közvetlen Videa URL lejátszása', 'playdirecturl', '', 'DefaultMovies.png', isFolder=False)
        self.addDirectoryItem('Keresés', 'search', '', 'DefaultFolder.png')
        self.endDirectory()

    def getSubmenus(self, url):
        url_content = client.request('%s' % base_url, cookie=self.getCookie(None))
        mainMenu = client.parseDOM(url_content, 'ul', attrs={'class': 'main-menu-list'})[0]
        menuItems = client.parseDOM(mainMenu, 'li')
        for menuItem in menuItems:
            if ('id="%s"' % url in menuItem):
                ul = client.parseDOM(menuItem, 'ul')[0]
                subMenuItems = client.parseDOM(ul, 'li')
                for subMenuItem in subMenuItems:
                    name = client.parseDOM(subMenuItem, 'a')[0].encode('utf-8')
                    href = client.parseDOM(subMenuItem, 'a', ret='href')[0].replace(base_url, '')
                    self.addDirectoryItem(name, 'videos&url=%s' % quote_plus(href), '', 'DefaultFolder.png')
        self.endDirectory('movies')

    def doSearch(self):
        search_text = self.getText(u'Add meg a keresend\xF5 film c\xEDm\xE9t')
        if search_text != '':
            if not os.path.exists(self.base_path):
                os.mkdir(self.base_path)
            file = open(self.searchFileName, "a")
            file.write("%s\n" % search_text)
            file.close()
            self.getVideos(url="/video_kereses/", search = search_text, params=None)

    def getVideos(self, url, params=None, search=None):
        searchExt = ''
        if not search == None:
            url_content = client.request('%s%s' % (base_url, url), cookie=self.getCookie(None))
            categoriesSelect = client.parseDOM(url_content, 'select', attrs={'name': 'sift'})[0]
            categories = client.parseDOM(categoriesSelect, 'option')
            allCategories = []
            for category in categories:
                allCategories.append(category)
            selectedCategory = xbmcgui.Dialog().select("Kategória választás", allCategories, preselect = 0)
            if selectedCategory >= 0:
                searchExt = client.parseDOM(categoriesSelect, 'option', ret='value')[selectedCategory]
            else:
                return
        url_content = client.request('%s%s%s%s%s' % (base_url, quote(url), '' if search == None else quote_plus(search), '' if params == None else params, searchExt), cookie=self.getCookie("session_adult=1" if xbmcaddon.Addon().getSetting('enableAdult') == 'true' else None))
        if "adult-content" in url_content:
            xbmcgui.Dialog().ok('Felnőtt tartalom!', 'Ez a tartalom olyan elemeket tartalmazhat, amelyek a hatályos jogszabályok kategóriái szerint kiskorúakra károsak lehetnek. A  hozzáférés jelenleg tiltott!')
            return                
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
            lis = client.parseDOM(pagination, 'li')[-1]
            kovetkezo = client.parseDOM(lis, 'a', ret='href')[0]
            self.addDirectoryItem(u'[I]K\u00F6vetkez\u0151 oldal >>[/I]', 'videos&url=%s%s&params=%s' % (quote_plus(url), '' if search == None else quote_plus(search), quote_plus(kovetkezo)), '', 'DefaultFolder.png')
        self.endDirectory('movies')

    def playmovie(self, url):
        def rc4(cipher_text, key):
            def compat_ord(c):
                return c if isinstance(c, int) else ord(c)
                
            res = b''

            key_len = len(key)
            S = list(range(256))

            j = 0
            for i in range(256):
                j = (j + S[i] + ord(key[i % key_len])) % 256
                S[i], S[j] = S[j], S[i]

            i = 0
            j = 0
            for m in range(len(cipher_text)):
                i = (i + 1) % 256
                j = (j + S[i]) % 256
                S[i], S[j] = S[j], S[i]
                k = S[(S[i] + S[j]) % 256]
                res += struct.pack('B', k ^ compat_ord(cipher_text[m]))

            if sys.version_info[0] == 3:
                return res.decode()
            else:
                return res

        url = "%s%s" % ("" if "http" in url else "https:", url)
        STATIC_SECRET = 'xHb0ZvME5q8CBcoQi6AngerDu3FGO9fkUlwPmLVY_RTzj2hJIS4NasXWKy1td7p'
        xbmc.log('VideaNG: resolving url: %s' % url, xbmc.LOGINFO)
        video_page = client.request(url, cookie=self.getCookie("session_adult=1"))
        if '/player' in url:
            player_url = url
            player_page = video_page
        else:
            player_url = re.search(r'<iframe.*?src="(/player\?[^"]+)"', video_page).group(1)
            player_url = urlparse.urljoin(url, player_url)
            player_page = client.request(player_url, cookie=self.getCookie(None))
        nonce = re.search(r'_xt\s*=\s*"([^"]+)"', player_page).group(1)
        l = nonce[:32]
        s = nonce[32:]
        result = ''
        for i in range(0, 32):
            result += s[i - (STATIC_SECRET.index(l[i]) - 31)]
        query = urlparse.parse_qs(urlparse.urlparse(player_url).query)
        random_seed = ''
        for i in range(8):
            random_seed += random.choice(string.ascii_letters + string.digits)
        _s = random_seed
        _t = result[:16]
        if 'f' in query or 'v' in query:
            _param = 'f=%s' % query['f'][0] if 'f' in query else 'v=%s' % query['v'][0]
        videaXml, headers, cookie = client.request('https://videa.hu/player/xml?platform=desktop&%s&_s=%s&_t=%s' % (_param, _s, _t), output='extended', cookie=self.getCookie(None))
        if not videaXml.startswith('<?xml'):
            key = result[16:] + random_seed + headers['x-videa-xs']
            videaXml = rc4(base64.b64decode(videaXml), key)
        videaData = xmltodict.parse(videaXml)
        sources = []
        sourcesList = []
        if not isinstance(videaData['videa_video']['video_sources']['video_source'], list):
            sourcesList.append(videaData['videa_video']['video_sources']['video_source'])
        else:
            sourcesList = videaData['videa_video']['video_sources']['video_source']
        for source in sourcesList:
            src = {}
            src["resolution"] = source["@name"]
            src["width"] = source["@width"]
            src["height"] = source["@height"]
            src["hd"] = source["@is_hd"]
            src["expiration"] = source["@exp"]
            src["url"] = "%s%s" % ('' if 'http' in source["#text"] else 'https:', source["#text"])
            src["hash"] = videaData['videa_video']['hash_values']['hash_value_%s' % src["resolution"]]
            sources.append(src)
        try:
            sources.sort(key=lambda x: int(x['resolution'].replace('p', '')), reverse=True)
        except:
            pass
        auto_pick = xbmcaddon.Addon().getSetting('autopick') == '1'
        if len(sources) > 0:
            if len(sources) == 1 or auto_pick == True:
                result = 0
            else:
                result = xbmcgui.Dialog().select(u'Min\u0151s\u00E9g', [source["resolution"] for source in sources])
            if result > -1:
                direct_url = "%s?md5=%s&expires=%s" % (sources[result]["url"], sources[result]["hash"], sources[result]["expiration"])
                xbmc.log('VideaNG: final url: %s' % direct_url, xbmc.LOGINFO)
                play_item = xbmcgui.ListItem(path=direct_url)
                subtitles = []
                subtitlesList = []
                if self.downloadsubtitles:
                    try:
                        if not isinstance(videaData['videa_video']['subtitles']['subtitle'], list):
                            subtitlesList.append(videaData['videa_video']['subtitles']['subtitle'])
                        else:
                            subtitlesList = videaData['videa_video']['subtitles']['subtitle']
                    except:
                        pass
                    if len(subtitlesList) > 0:
                        try:
                            errMsg = ""
                            if not os.path.exists(os.path.join(self.base_path, "subtitles")):
                                errMsg = "Hiba a felirat könyvtár létrehozásakor!"
                                os.mkdir(os.path.join(self.base_path, "subtitles"))
                            for f in os.listdir(os.path.join(self.base_path, "subtitles")):
                                errMsg = "Hiba a korábbi feliratok törlésekor!"
                                os.remove(os.path.join(self.base_path, "subtitles", f))
                            xbmc.log('VideaNG: subtitle count: %d' % len(subtitlesList), xbmc.LOGINFO)
                            for subtitle in subtitlesList:
                                subtitleUrl = "%s%s" % ("" if "http" in subtitle["@src"] else "https:", subtitle["@src"])
                                subtitleTxt = client.request(subtitleUrl, cookie=self.getCookie(None))
                                if len(subtitleTxt) > 0:
                                    errMsg = "Hiba a sorozat felirat file kiírásakor!"
                                    file = safeopen(os.path.join(self.base_path, "subtitles", "%s.srt" % subtitle["@title"].strip()), "w")
                                    file.write(subtitleTxt)
                                    file.close()
                                    errMsg = "Hiba a sorozat felirat file hozzáadásakor!"
                                    subtitles.append("%s/subtitles/%s.srt" % (self.base_path, subtitle["@title"].strip()))
                                else:
                                    xbmc.log("VideaNG: Subtitles not found in source", xbmc.LOGERROR)
                            if len(subtitles)>0:
                                errMsg = "Hiba a feliratok beállításakor!"
                                play_item.setSubtitles(subtitles)
                        except:
                            xbmcgui.Dialog().notification("Videa Next Generation hiba", errMsg, xbmcgui.NOTIFICATION_ERROR)
                            xbmc.log("VideaNG: Hiba a %s URL-hez tartozó felirat letöltésekor, hiba: %s" % (py2_encode(final_url), py2_encode(errMsg)), xbmc.LOGERROR)
                    else:
                        xbmc.log("VideaNG: Could not find any subtitles", xbmc.LOGINFO)
                xbmc.log("VideaNG: Playing url: %s" % direct_url, xbmc.LOGINFO)
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


    def endDirectory(self, type='addons', cache=True):
        xbmcplugin.setContent(syshandle, type)
        #xbmcplugin.addSortMethod(syshandle, xbmcplugin.SORT_METHOD_TITLE)
        xbmcplugin.endOfDirectory(syshandle, cacheToDisc=cache)

    def getText(self, caption):
        search_text = ''
        keyb = xbmc.Keyboard('', caption)
        keyb.doModal()

        if (keyb.isConfirmed()):
            search_text = keyb.getText()

        return py2_encode(search_text)

    def getSearches(self):
        self.addDirectoryItem('[COLOR lightblue]Új keresés[/COLOR]', 'newsearch', '', 'DefaultFolder.png')
        try:
            file = open(self.searchFileName, "r")
            olditems = file.read().splitlines()
            file.close()
            items = list(set(olditems))
            items.sort(key=locale.strxfrm)
            if len(items) != len(olditems):
                file = open(self.searchFileName, "w")
                file.write("\n".join(items))
                file.close()
            for item in items:
                self.addDirectoryItem(item, 'videos&url=/video_kereses/&search=%s' % quote_plus(item), '', 'DefaultFolder.png')
            if len(items) > 0:
                self.addDirectoryItem('[COLOR red]Keresési előzmények törlése[/COLOR]', 'deletesearchhistory', '', 'DefaultFolder.png')
        except:
            pass
        self.endDirectory(cache=False)

    def deleteSearchHistory(self):
        if os.path.exists(self.searchFileName):
            os.remove(self.searchFileName)

    def playDirectUrl(self):
        url = self.getText(u'Add meg a teljes videa URL-t!')
        if url != '':
            self.playmovie(url)

    def login(self):
        loggedIn = False
        if xbmcaddon.Addon().getSetting('username') and xbmcaddon.Addon().getSetting('password'):
            if xbmcaddon.Addon().getSetting('logincookie'):
                t1 = int(xbmcaddon.Addon().getSetting('logincookie.timestamp'))
                t2 = int(time.time())
                if (abs(t2 - t1) / 3600) >= 24 or t1 == 0:
                    content = client.request(base_url, cookie="sid=%s" % xbmcaddon.Addon().getSetting('logincookie'))
                    if "top-menu-user-name" in content:
                        loggedIn = True
                        xbmcaddon.Addon().setSetting('logincookie.timestamp', str(t2))
                else:
                    loggedIn = True
            if not loggedIn:
                loginData={"cmd": "tryLoginByRequest", "userid": xbmcaddon.Addon().getSetting('username'), "password": xbmcaddon.Addon().getSetting('password')}
                content, headers, cookie = client.request("%s/interface?logcmd=tryLoginByRequest" % base_url, post='json=%s' % json.dumps(loginData), output='extended')
                if json.loads(content)["response"]["code"] == 0:
                    cookies = (dict(i.split('=', 1) for i in cookie.split('; ')))
                    xbmcaddon.Addon().setSetting('logincookie', cookies["sid"])
                    xbmcaddon.Addon().setSetting('logincookie.timestamp', str(int(time.time())))
                else:
                    xbmcgui.Dialog().ok("Bejelentkezési hiba", "Hiba a bejelentkezés során! Kérlek ellenőrizd a felhasználó nevet, illetve a jelszavát!")
                    xbmcaddon.Addon().setSetting('logincookie', "")
                    xbmcaddon.Addon().setSetting('logincookie.timestamp', "0")

    def getCookie(self, cookie):
        retCookie = None
        if cookie:
            if xbmcaddon.Addon().getSetting('logincookie') != "":
                retCookie = "sid=%s; %s" % (xbmcaddon.Addon().getSetting('logincookie'), cookie)
            else:
                retCookie = cookie
        else:
            retCookie = None if xbmcaddon.Addon().getSetting('logincookie') == "" else "sid=%s" % xbmcaddon.Addon().getSetting('logincookie')
        return retCookie

    def logout(self):
        if 1 == xbmcgui.Dialog().yesno("Videa Next Generation", "Valóban ki szeretnél jelentkezni?", "", ""):
            xbmcaddon.Addon().setSetting('username', "")
            xbmcaddon.Addon().setSetting('password', "")
            xbmcaddon.Addon().setSetting('logincookie', "")
            xbmcaddon.Addon().setSetting('logincookie.timestamp', "0")
            xbmcaddon.Addon().setSetting('enableAdult', "false")