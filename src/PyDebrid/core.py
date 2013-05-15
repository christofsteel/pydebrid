from PyDebrid.application import app
from PyDebrid.alldebrid import AlldebridRequest
from PyDebrid.download import DownloadPimp

class PyDebrid:
	"""	def createDaemon(self):
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
			os._exit(0)   # Exit parent of the first child."""

	def __init__(self, user, password, folder="/tmp", host="0.0.0.0", port=8180, max_par=2, background=False):
		self.ar = AlldebridRequest()
		self.ar.login(user, password)
		self.pimp = DownloadPimp(max_par, folder, self.ar)
		self.pimp.start()
		self.sj = {}
		app.pydebrid = self
		app.run(host=host, port=port, reloader=False, debug=True, quiet=True)
