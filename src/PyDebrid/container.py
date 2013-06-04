import threading
import hashlib
import urllib
from PyDebrid.application import app

class ContainerDecrypter(threading.Thread):
	def __init__(self, dlc_file, unpack = "", password = ""):
		super().__init__()
		self.dlc_file = dlc_file
		self.unpack = unpack
		self.password = password
		self.id = hashlib.md5(dlc_file.encode('utf-8')).hexdigest()

	def run(self):
		links = self.getLinks()
		gname = hashlib.md5(str.join("", links).encode("utf-8")).hexdigest()
		for link in links:
			app.pydebrid.pimp.add({'olink': link, 'group': gname, 'unpack':
				self.unpack, 'password': self.password, 'och': True})

	def getLinks(self):
		data=urllib.parse.urlencode({'data': self.dlc_file}).encode('utf-8')
		links = urllib.request.urlopen("http://posativ.org/decrypt/dlc",
										data = data).read()
		return str(links, 'utf-8').strip().split()

