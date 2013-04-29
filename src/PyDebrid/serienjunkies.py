import urllib
import http
import hashlib
from pyquery import PyQuery as pq

class SerienjunkiesLink:
	def __init__(self, link):
		self.link = link
		self.id = hashlib.md5(link.encode("utf-8")).hexdigest()
		self.cookiejar = http.cookiejar.CookieJar()
		self.opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(self.cookiejar))
		page = self.opener.open(link)
		self.pagequery = pq(page.read())
		self.s = self.pagequery("#postit input").attr('value')
		self.secureurl = self.pagequery('#postit table tr td').children('img').attr('src')
		self.img = self.opener.open("http://download.serienjunkies.org/" + self.secureurl)

	def reload(self):
		self.__init__(self.link)

	def getLinks(self, password):
		data=urllib.parse.urlencode({'s': self.s, 'c': password}).encode("utf-8")
		page = self.opener.open(self.link, data=data).read()
		pagequery = pq(page)
		links = pagequery('table').items('form')
		validLinks = []
		for link in links:
			if link.attr('action').startswith("http://download.serienjunkies.org"):
				p = self.opener.open(link.attr('action')).geturl()
				validLinks.append(p)
		return validLinks
