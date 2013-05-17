import os
import queue
import urllib
import urllib.request
import socket
import shutil
import threading
import time
import hashlib
import http
import rarfile
from PyDebrid.alldebrid import AlldebridError

class NoPasswordError(Exception):
	pass

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
			self.groups[link['group']] = {}
			self.groups[link['group']]['ids'] = []
			self.groups[link['group']]['filenames'] = []

		if 'group' in link:
			self.groups[link['group']]['ids'].append(link['id'])
			self.groups[link['group']]['filenames'].append(link['filename'])

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
		except (urllib.error.URLError, socket.timeout, ConnectionResetError, http.client.BadStatusLine):
			if self._cancled:
				raise Cancled
			print("Retrying " + self.link['filename'])
			raise WentWrong


	def run(self):
		timeout = 15
		print("Downloading " + self.link['filename'] + " (" + self.link['link'] + ")")
		try:
			self.pimp.loads.get()
			del self.pimp.links[self.link['id']]
			self.load(timeout)
			print("Finished " + self.link['filename'])
			shutil.move(os.path.join(self.pimp.folder, self.link['filename'] + ".fuck"), os.path.join(self.pimp.folder, self.link['filename']))
			if self.link['och']:
				self.pimp.groups[self.link['group']]['ids'].remove(self.link['id'])
				if self.pimp.groups[self.link['group']]['ids'] == []:
					if self.link['unpack']:
						firstVolume = None
						for filename in self.pimp.groups[self.link['group']]['filenames']:
							try:
								rf = rarfile.RarFile(os.path.join(self.pimp.folder, filename))
								firstVolume = filename
							except rarfile.NeedFirstVolume:
								pass
						rf = rarfile.RarFile(os.path.join(self.pimp.folder, firstVolume))
						if self.link['password']:
							print("Unpacking " + firstVolume+ " with password \"" + self.link['password'] + "\"")
						else:
							print("Unpacking " + firstVolume)
						if rf.needs_password() and not self.link['password']:
							raise NoPasswordError
						rf.extractall(path=self.pimp.folder, pwd=self.link['password'])
						for filename in self.pimp.groups[self.link['group']]['filenames']:
							os.remove(os.path.join(self.pimp.folder, filename))
						print("Done extracting and deleting")
					del self.pimp.groups[self.link['group']]

		except AlreadyDownloaded:
			self.pimp.loads.get()
			del self.pimp.links[self.link['id']]
			if self.link['och']:
				self.pimp.groups[self.link['group']]['ids'].remove(self.link['id'])
				if self.pimp.groups[self.link['group']]['ids'] == []:
					if self.link['unpack']:
						firstVolume = None
						for filename in self.pimp.groups[self.link['group']]['filenames']:
							try:
								rf = rarfile.RarFile(os.path.join(self.pimp.folder, filename))
								firstVolume = filename
							except rarfile.NeedFirstVolume:
								pass
						rf = rarfile.RarFile(os.path.join(self.pimp.folder, firstVolume))
						if self.link['password']:
							print("Unpacking " + firstVolume + " with password \"" + self.link['password'] + "\"")
						else:
							print("Unpacking " + firstVolume)
						if rf.needs_password() and not self.link['password']:
							raise NoPasswordError
						rf.extractall(path=self.pimp.folder, pwd=self.link['password'])
						for filename in self.pimp.groups[self.link['group']]['filenames']:
							os.remove(os.path.join(self.pimp.folder, filename))
						print("Done extracting and deleting")
					del self.pimp.groups[self.link['group']]

		except Cancled:
			print("Cancled " + self.link['filename'])
			os.remove(os.path.join(self.pimp.folder, self.link['filename'] + '.fuck'))
			self.pimp.groups[self.link['group']]['ids'].remove(self.link['id'])
			del self.pimp.links[self.link['id']]
			self.pimp.loads.get()

		except WentWrong:
			if self.link['och']:
				self.pimp.groups[self.link['group']]['ids'].remove(self.link['id'])
				self.pimp.groups[self.link['group']]['filenames'].remove(self.link['filename'])
			del self.pimp.links[self.link['id']]
			self.pimp.loads.get()
			time.sleep(10)
			if self.link['och']:
				self.pimp.add(self.link)
			else:
				self.pimp.addddl(self.link)



