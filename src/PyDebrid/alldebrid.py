import urllib
import json
import http.cookiejar
import os
import hashlib

class AlldebridRequest:
	def __init__(self):
		self.cookiejar = http.cookiejar.CookieJar()
		self.opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(self.cookiejar))

	def login(self, user, password):
		params = urllib.parse.urlencode({'action': 'login', 'returnpage': '', 'login_login': user, 'login_password': password})
		return self.opener.open("http://www.alldebrid.de/register/?" + params)

	def getLink(self, link):
		print("Decrypring " + link)
		params = urllib.parse.urlencode({'link': link, 'nb': '0', 'json':'true', 'pw':''})
		response = self.opener.open("http://www.alldebrid.de/service.php?" + params)
		json_response = json.loads(str(response.read(), "utf-8"))
		json_response['filename'] = os.path.basename(json_response['link'])
		return json_response
