import os
import queue
import urllib
import urllib.request
import socket
import shutil
import threading
import time
import hashlib
from PyDebrid.alldebrid import AlldebridError

class WentWrong(Exception):
	pass

class AlreadyDownloaded(Exception):
	pass

class Cancled(Exception):
	pass

class DownloadPimp(threading.Thread):
	def __init__(self, max_par, folder, alldebrid):
		super().__init__()
		self.queue = queue.Queue()
		self.loads = queue.Queue(maxsize=max_par)
		self.links = {}
		self.groups = {}
		self.folder = folder
		self.bitchlist = {}
		self.alldebrid = alldebrid

	def addddl(self, link):
		if not 'filesize' in link:
			with urllib.request.urlopen(self.link['link'], timeout = 5) as download:
				self.link['filesize'] = int(download.getheader("Content-Length"))
		link['filename'] = os.path.basename(link['link'])
		link['id'] = hashlib.md5(link['filename'].encode('utf-8')).hexdigest()
		link['loading'] = False

		if not 'completed' in link:
			link['completed'] = 0

		link['rate'] = 0
		self.queue.put(link)
		self.links[link['id']] = link

	def add(self, link):
		if not 'link' in link or not 'filename' in link:
			try:
				link['link'], link['filename'], link['filesize'] = self.alldebrid.getLink(link['olink'])
			except AlldebridError:
				self.add(link)
			link['id'] = hashlib.md5(link['filename'].encode('utf-8')).hexdigest()

		if 'group' in link and not link['group'] in self.groups:
			self.groups[link['group']] = []

		if 'group' in link:
			self.groups[link['group']].append(link['id'])

		if not 'completed' in link:
			link['completed'] = 0

		link['loading'] = False
		link['rate'] = 0
		self.queue.put(link)
		self.links[link['id']] = link

	def run(self):
		while True:
			link = self.queue.get()
			try:
				if link['och']:
					link['link'], link['filename'], link['filesize'] = self.alldebrid.getLink(link['olink']) # Update Link
				self.loads.put(link)
				link['loading'] = True
				bitch = DownloadBitch(link, self)
				self.bitchlist[link['id']] = bitch
				bitch.start()
			except (AlldebridError):
				print("could not get alldebrid Link, putting back into queue")
				self.add(link)

class MyURLOpener(urllib.request.FancyURLopener):
    """Create sub-class in order to overide error 206.  This error means a
       partial file is being sent,
       which is ok in this case.  Do nothing with this error.
    """
    def http_error_206(self, url, fp, errcode, errmsg, headers, data=None):
        pass

class DownloadBitch(threading.Thread):
	def __init__(self, link, pimp, chunksize=2**18):
		threading.Thread.__init__(self)
		self.link = link
		self.pimp = pimp
		self.chunksize = chunksize
		self._cancled = False

	def cancle(self):
		self.link['cancled'] = True
		self._cancled = True

	def load(self, timeout):
		try:
			request = urllib.request.Request(self.link['link'])
			dlFile = os.path.join(self.pimp.folder, self.link['filename'] + '.fuck')
			if os.path.exists(os.path.join(self.pimp.folder, self.link['filename'])):
				print("already downloaded")
				raise AlreadyDownloaded
			if os.path.exists(dlFile):
				print("file exists")
				mode = 'ab'
				existSize = os.path.getsize(dlFile)
				#If the file exists, then only download the remainder
				self.link['completed'] = existSize
				request.headers['Range'] = "bytes=%s-" % self.link['completed']
			else:
				mode = 'wb'
			if self._cancled:
				raise Cancled
			with urllib.request.urlopen(request, timeout = timeout) as download:
				toLoad = download.getheader("Content-Length")
				if download.getcode() == 206:
					print("appending")
					mode = 'ab'
				else:
					mode = 'wb'
				if toLoad == None:
					raise WentWrong
				with open(dlFile, mode) as fuck:
					chunk = download.read(self.chunksize)
					print(self.link['olink'] + ": " + download.getheader('Content-Type'))
					while chunk != b'':
						stime = time.time()
						if self._cancled:
							raise Cancled
						fuck.write(chunk)
						self.link['completed'] = os.path.getsize(fuck.name)
						chunk = download.read(self.chunksize)
						etime = time.time()
						self.link['rate'] = self.chunksize / (etime - stime)
		except (urllib.error.URLError, socket.timeout, ConnectionResetError):
			if self._cancled:
				raise Cancled
			print("Timeout retrying " + self.link['filename'])
			time.sleep(2)
			raise WentWrong


	def run(self):
		timeout = 10
		print("Downloading " + self.link['filename'] + " (" + self.link['link'] + ")")
		try:
			self.load(timeout)
			print("Finished " + self.link['filename'])
			print(self.link)
			shutil.move(os.path.join(self.pimp.folder, self.link['filename'] + ".fuck"), os.path.join(self.pimp.folder, self.link['filename']))
			if self.link['och']:
				print("An OCH Link is completed")
				self.pimp.groups[self.link['group']].remove(self.link['id'])
				print(self.pimp.groups)
				if self.pimp.groups[self.link['group']] == []:
					print("Finished Group " + self.link['group'])
					if self.link['unpack']:
						if self.link['password']:
							print("Unpacking " + self.link['filename'] + " with password \"" + self.link['password'] + "\"")
						else:
							print("Unpacking " + self.link['filename'])
			del self.pimp.links[self.link['id']]

		except AlreadyDownloaded:
			self.pimp.groups[self.link['group']].remove(self.link['id'])
			del self.pimp.links[self.link['id']]

		except Cancled:
			print("Cancled " + self.link['filename'])
			os.remove(os.path.join(self.pimp.folder, self.link['filename'] + '.fuck'))
			self.pimp.groups[self.link['group']].remove(self.link['id'])
			del self.pimp.links[self.link['id']]

		except WentWrong:
			if self.link['och']:
				self.pimp.groups[self.link['group']].remove(self.link['id'])
			del self.pimp.links[self.link['id']]
			if self.link['och']:
				self.pimp.add(self.link)
			else:
				self.pimp.addddl(self.link)

		self.pimp.loads.get()


