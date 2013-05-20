import urllib
import json
import http.cookiejar
import os
import hashlib

class AlldebridError(Exception):
	pass

class AlldebridRequest:
	def __init__(self):
		self.cookiejar = http.cookiejar.CookieJar()
		self.opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(self.cookiejar))

	def login(self, user, password):
		params = urllib.parse.urlencode({'action': 'login', 'returnpage': '', 'login_login': user, 'login_password': password})
		return self.opener.open("http://www.alldebrid.de/register/?" + params)

	def getLink(self, link):
		params = urllib.parse.urlencode({'link': link, 'nb': '0', 'json':'true', 'pw':''})
		try:
			response = self.opener.open("http://www.alldebrid.de/service.php?" + params)
			json_str = str(response.read(), "utf-8")
		except urllib.error.URLError:
			raise AlldebridError
		json_response = json.loads(json_str)
		json_response['filename'] = os.path.basename(json_response['link'])
		if json_response['error']:
			print("[ALLDEBRID ERROR] (" + link + ") " + json_response['error'])
			raise AlldebridError
		return (json_response['link'], json_response['filename'], json_response['filesize'])
