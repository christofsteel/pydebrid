import hashlib
import os
import queue
import urllib
import urllib.request
import socket
import shutil
import threading

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
		dlink = {}
		dlink['link'] = link
		dlink['filename'] = os.path.basename(link)
		dlink['id'] = hashlib.md5(dlink['filename'].encode('utf-8')).hexdigest()
		dlink['loading'] = False
		dlink['perc'] = 0
		self.queue.put(dlink)
		self.links[dlink['id']] = dlink

	def add(self, link, gname, unpack):
		if not gname in self.groups:
			self.groups[gname] = []
		dlink = self.alldebrid.getLink(link)
		self.groups[gname].append(dlink['id'])
		dlink['loading'] = False
		dlink['group'] = gname
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
		self.downloaded = 0
		self._cancled = False

	def cancle(self):
		self.link['cancled'] = True
		self._cancled = True

	def load(self, timeout, resume):
		try:
			myUrlclass = MyURLOpener()
			dlFile = os.path.join(self.pimp.folder, self.link['filename'] + '.fuck')
			if os.path.exists(dlFile):
				print("file exists")
				mode = 'ab'
				existSize = os.path.getsize(dlFile)
				#If the file exists, then only download the remainder
				myUrlclass.addheader("Range","bytes=%s-" % (existSize))
				self.downloaded = existSize
			else:
				mode = 'wb'
			if not self._cancled:
				with open(dlFile, mode) as fuck:
					with urllib.request.urlopen(self.link['link'], timeout = timeout) as download:
						self.clength = download.getheader("Content-Length")
						print(download.getcode())
						chunk = download.read(self.chunksize)
						while chunk != b'' and not self._cancled:
							self.link['perc'] = round(self.downloaded / int(self.clength)  * 100, 1)
							fuck.write(chunk)
							self.downloaded += len(chunk)
							chunk = download.read(self.chunksize)
		except socket.timeout:
			resume = os.path.getsize(os.path.join(self.pimp.folder, self.link['filename'] + '.fuck'))
			print("Timeout retrying " + self.link['filename'] + " (" + str(resume) + ")")
			self.load(timeout, resume)


	def run(self):
		timeout = 10
		print("Downloading " + self.link['filename'] + " (" + self.link['link'] + ")")
		self.load(timeout, 0)
		if self._cancled:
			print("Cancled " + self.link['filename'])
			os.remove(os.path.join(self.pimp.folder, self.link['filename'] + '.fuck'))
		else:
			print("Finished " + self.link['filename'])
			self.pimp.groups[self.link['group']].remove(self.link['id'])
			if self.pimp.groups[self.link['group']] == []:
				print("Finished Group " + self.link['group'])
			shutil.move(os.path.join(self.pimp.folder, self.link['filename'] + ".fuck"), os.path.join(self.pimp.folder, self.link['filename']))
		self.pimp.loads.get()
		del self.pimp.links[self.link['id']]


