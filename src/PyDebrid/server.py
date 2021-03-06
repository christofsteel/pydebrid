from bottle import request, response, TEMPLATE_PATH, static_file
from bottle import jinja2_template as template
from PyDebrid import __path__
from PyDebrid.application import app
from PyDebrid.serienjunkies import SerienjunkiesLink
from PyDebrid.container import ContainerDecrypter
import hashlib

TEMPLATE_PATH.insert(0,__path__[0]+"/data/")

@app.route("/")
def index():
	return template("pydebrid.html", queue=app.pydebrid.pimp.links)

@app.route("/favicon.ico")
def favicon():
	return static_file("favicon.ico", root=__path__[0]+"/data/")

@app.route("/list")
def list():
	#return {'links': sorted(app.pydebrid.pimp.links.values(), key = lambda link: link['perc'])}
	return app.pydebrid.pimp.links

@app.route("/remove/<link>")
def remove(link):
	if link in app.pydebrid.pimp.links:
		app.pydebrid.pimp.bitchlist[link].cancle()
		return {'message': 'Removed Link'}

@app.post("/add_och")
def add_och():
	links = request.POST.get('och_links', '').strip().split()
	unpack = request.POST.get('unpack', '')
	password = request.POST.get('password', '')
	gname = hashlib.md5(str.join("", links).encode("utf-8")).hexdigest()
	for link in links:
		app.pydebrid.pimp.add({'olink': link, 'group': gname, 'unpack': unpack, 'password': password, 'och': True})
	return {'message': 'Added links to queue'}

@app.post("/add_ddl")
def add_ddl():
	links = request.POST.get('ddl_links', '').strip().split()
	for link in links:
		app.pydebrid.pimp.addddl({'link': link, 'och': False})
	return {'message': 'Added Direct Download Links'}


@app.get("/<id>/captcha.jpg")
def captcha(id):
	response.content_type = "image/png"
	return app.pydebrid.sj[id].img

@app.post("/sj")
def serienjunkies():
	link = request.POST.get('link', '').strip()
	print("SJ " + link)
	sj = SerienjunkiesLink(link)
	app.pydebrid.sj[sj.id] = sj
	return {'id': sj.id}

@app.post("/sjcaptcha")
def sjcaptcha():
	captcha = request.POST.get('captcha', '').strip()
	id = request.POST.get('captchaid', '').strip()
	app.pydebrid.sj[id].setCaptcha(captcha)
	app.pydebrid.sj[id].start()
	
	return {'message': 'Added links to queue'}

@app.post("/add_dlc")
def add_dlc():
	dlc_file = str(request.files.get('dlc_file').file.read(), "utf-8")
	unpack = request.POST.get('unpack', '')
	password = request.POST.get('password', '')
	if unpack == "true":
		unpack = "unpack"
	else:
		unpack = ""
	cd = ContainerDecrypter(dlc_file, unpack = unpack, password = password)
	cd.start()
	return {'message': 'Decrypting DLC'}

