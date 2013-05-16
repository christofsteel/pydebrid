import urllib
import http
import hashlib
import threading
from pyquery import PyQuery as pq
from PyDebrid.application import app

class SerienjunkiesLink(threading.Thread):
	def __init__(self, link):
		super().__init__()
		self.link = link
		self.id = hashlib.md5(link.encode("utf-8")).hexdigest()
		self.cookiejar = http.cookiejar.CookieJar()
		self.opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(self.cookiejar))
		page = self.opener.open(link)
		self.pagequery = pq(page.read())
		self.s = self.pagequery("#postit input").attr('value')
		self.secureurl = self.pagequery('#postit table tr td').children('img').attr('src')
		self.img = self.opener.open("http://download.serienjunkies.org/" + self.secureurl)

	def setCaptcha(self, captcha):
		self.captcha = captcha

	def reload(self):
		self.__init__(self.link)

	def run(self):
		links = self.getLinks()
		gname = hashlib.md5(str.join("", links).encode("utf-8")).hexdigest()
		for link in links:
			app.pydebrid.pimp.add({'olink': link, 'group': gname, 'unpack': "unpack", 'password': 'serienjunkies.org', 'och': True})

	def getLinks(self):
		data=urllib.parse.urlencode({'s': self.s, 'c': self.captcha }).encode("utf-8")
		page = self.opener.open(self.link, data=data).read()
		pagequery = pq(page)
		links = pagequery('table').items('form')
		validLinks = []
		for link in links:
			if link.attr('action').startswith("http://download.serienjunkies.org"):
				p = self.opener.open(link.attr('action')).geturl()
				validLinks.append(p)
		return validLinks
