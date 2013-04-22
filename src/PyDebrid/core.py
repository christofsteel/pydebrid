#!/usr/bin/env python3

import threading
import shutil
import http.cookiejar
import http.server
import urllib
import argparse
import getpass
import json
import hashlib
import os
import queue
from jinja2 import FileSystemLoader, Environment, PackageLoader
from cgi import parse_header, parse_multipart

data_path = os.path.join(os.path.dirname(__file__),'data')

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
		json_response['id'] = hashlib.md5(json_response['filename'].encode('utf-8')).hexdigest()
		return json_response

class DownloadPimp(threading.Thread):
	def __init__(self, max_par, folder, alldebrid):
		super().__init__()
		self.queue = queue.Queue()
		self.loads = queue.Queue(maxsize=max_par)
		self.links = {}
		self.folder = folder
		self.bitchlist = {}
		self.alldebrid = alldebrid

	def addddl(self, link):
		dlink = {}
		dlink['link'] = link
		dlink['filename'] = os.path.basename(link)
		dlink['id'] = hashlib.md5(dlink['filename'].encode('utf-8')).hexdigest()
		dlink['loading'] = False
		dlink['perc'] = 0
		self.queue.put(dlink)
		self.links[dlink['id']] = dlink

	def add(self, link):
		dlink = self.alldebrid.getLink(link)
		dlink['loading'] = False
		dlink['perc'] = 0
		self.queue.put(dlink)
		self.links[dlink['id']] = dlink

	def run(self):
		while True:
			print("Empty Queue")
			link = self.queue.get()
			self.loads.put(link)
			link['loading'] = True
			bitch = DownloadBitch(link, self)
			self.bitchlist[link['id']] = bitch
			bitch.start()

class DownloadBitch(threading.Thread):
	def __init__(self, link, pimp, chunksize=2**18):
		threading.Thread.__init__(self)
		self.link = link
		self.pimp = pimp
		self.chunksize = chunksize
		self.downloaded = 0
		self._cancled = False

	def cancle(self):
		self.link['cancled'] = True
		self._cancled = True

	def run(self):
		print("Downloading " + self.link['filename'] + " (" + self.link['link'] + ")")
		with open(os.path.join(self.pimp.folder, self.link['filename'] + '.fuck'), 'wb') as fuck:
			with urllib.request.urlopen(self.link['link']) as download:
				self.clength = download.getheader("Content-Length")
				chunk = download.read(self.chunksize)
				while chunk != b'' and not self._cancled:
					self.link['perc'] = round(self.downloaded / int(self.clength)  * 100, 1)
					fuck.write(chunk)
					self.downloaded += len(chunk)
					chunk = download.read(self.chunksize)
		if self._cancled:
			print("Cancled " + self.link['filename'])
			os.remove(os.path.join(self.pimp.folder, self.link['filename'] + '.fuck'))
		else:
			print("Finished " + self.link['filename'])
			shutil.move(os.path.join(self.pimp.folder, self.link['filename'] + ".fuck"), os.path.join(self.pimp.folder, self.link['filename']))
		self.pimp.loads.get()
		del self.pimp.links[self.link['id']]

class MyPimpServer(http.server.HTTPServer):
	def __init__(self, host, port, handler, pimp):
		self.env = Environment(loader=FileSystemLoader(data_path))
		http.server.HTTPServer.__init__(self, (host, port), handler)
		self.pimp = pimp
		self.env.filters['urlquote_plus'] = urllib.parse.quote_plus

class MyResponseHandler(http.server.BaseHTTPRequestHandler):
	def do_HEAD(self):
		self.send_std_header()

	def parse_POST(self):
		ctype, pdict = parse_header(self.headers['content-type'])
		if ctype == 'multipart/form-data':
			postvars = parse_multipart(self.rfile, pdict)
		elif ctype == 'application/x-www-form-urlencoded':
			length = int(self.headers['content-length'])
			postvars = urllib.parse.parse_qs(self.rfile.read(length), keep_blank_values=1)
		else:
			postvars = {}
		return postvars

	def post_addddl(self):
		self.send_std_header()
		data = self.parse_POST()
		links = data[b'ddl_links'][0].split()
		for link in links:
			self.server.pimp.addddl(str(link, 'utf-8'))
		self.write(json.dumps({'message': 'Added Direct Donwload Links'}))

	def post_addoch(self):
		self.send_std_header()
		data = self.parse_POST()
		links = data[b'och_links'][0].split()
		for link in links:
			self.server.pimp.add(str(link, 'utf-8'))
		self.write(json.dumps({'message': 'Added One Click Hoster Links'}))

	def get_index(self):
		self.send_std_header()
		template = self.server.env.get_template('pydebrid.html')
		self.write(template.render(queue = self.server.pimp.links))

	def get_list(self):
		self.send_std_header()
		self.write(json.dumps(self.server.pimp.links))

	def do_POST(self):
		if self.path == "/add_och":
			self.post_addoch()
		elif self.path == "/add_ddl":
			self.post_addddl()
		else:
			self.send_response(404)
			self.end_headers()

	def get_remove(self, queries):
		self.send_std_header()
		if queries['link'][0] in self.server.pimp.links:
			self.server.pimp.bitchlist[queries['link'][0]].cancle()
		self.write(json.dumps({'message': 'Removed Link'}))

	def get_bootstrap_css(self):
		self.send_response(200)
		self.send_header("Content-type", "text/css")
		send.end_headers()
		with open(os.path.join(data_path,"bootstrap.min.css"), "r") as file:
			self.write(file.read())

	def get_bootstrap_js(self):
		self.send_std_header()
		with open(os.path.join(data_path,"bootstrap.min.js"), "r") as file:
			self.write(file.read())

	def do_GET(self):
		self.url = urllib.parse.urlparse(self.path)
		if self.url.path == "/":
			self.get_index()
		elif self.url.path == "/list":
			self.get_list()
		elif self.url.path == "/remove":
			self.get_remove(urllib.parse.parse_qs(self.url.query))
		elif self.url.path == "/bootstrap.css":
			self.get_bootstrap_css()
		elif self.url.path == "/bootstrap.js":
			self.get_bootstrap_js()
		else:
			self.send_response(200)
			self.end_headers()
			self.write(self.path)

	def write(self, s):
		self.wfile.write(s.encode('utf-8'))

	def send_std_header(self):
		self.send_response(200)
		self.send_header("Content-type", "text/html; charset=utf-8")
		self.end_headers()

class PyDebrid:
	def createDaemon(self):
		try:
			pid = os.fork()
		except OSError as e:
			raise Exception("%s [%d]" % (e.strerror, e.errno))

		if (pid == 0):   # The first child.
			os.setsid()
			try:
				pid = os.fork()    # Fork a second child.
			except OSError as e:
				raise Exception("%s [%d]" % (e.strerror, e.errno))

			os._exit(0)    # Exit parent (the first child) of the second child.
		else:
			os._exit(0)   # Exit parent of the first child.

	def __init__(self, user, password, folder="/tmp", host="0.0.0.0", port=8180, max_par=2, background=False):
		if background:
			self.createDaemon()
		ar = AlldebridRequest()
		ar.login(user, password)
		pimp = DownloadPimp(max_par, folder, ar)
		pimp.start()
		server = MyPimpServer(host, port, MyResponseHandler, pimp)
		server.serve_forever();

