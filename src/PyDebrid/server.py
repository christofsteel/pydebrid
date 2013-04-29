from bottle import request, response, route, run, Bottle, TEMPLATE_PATH
from bottle import jinja2_view as view, jinja2_template as template
from PyDebrid import __path__
from PyDebrid.application import app
from PyDebrid.serienjunkies import SerienjunkiesLink
import hashlib

TEMPLATE_PATH.insert(0,__path__[0]+"/data/")

@app.route("/")
def index():
	return template("pydebrid.html", queue=app.pydebrid.pimp.links)

@app.route("/list")
def list():
	return app.pydebrid.pimp.links

@app.route("/remove/<link>")
def remove(link):
	if link in app.pydebrid.pimp.links:
		app.pydebrid.pimp.bitchlist[link].cancle()
		return {'message': 'Removed Link'}

@app.post("/add_och")
def add_och():
	links = request.POST.get('och_links', '').strip().split()
	gname = hashlib.md5(str.join("", links).encode("utf-8")).hexdigest()
#	unpack = (data[b'unpack'][0].split() == b'unpack') if b'unpack' in data else False
	for link in links:
		app.pydebrid.pimp.add(link, gname, False)
	return {'message': 'Added links to queue'}

@app.post("/add_ddl")
def add_ddl():
	links = request.POST.get('ddl_links', '').strip().split()
	for link in links:
		app.pydebrid.pimp.addddl(link)
	return {'message': 'Added Direct Download Links'}


@app.get("/<id>/captcha.jpg")
def captcha(id):
	response.content_type = "image/png"
	return app.pydebrid.sj[id].img

@app.post("/sj")
def serienjunkies():
	link = request.POST.get('link', '').strip()
	sj = SerienjunkiesLink(link)
	app.pydebrid.sj[sj.id] = sj
	return {'id': sj.id}

@app.post("/sjcaptcha")
def sjcaptcha():
	captcha = request.POST.get('captcha', '').strip()
	id = request.POST.get('captchaid', '').strip()
	links = app.pydebrid.sj[id].getLinks(captcha)
	gname = hashlib.md5(str.join("", links).encode("utf-8")).hexdigest()
#	unpack = (data[b'unpack'][0].split() == b'unpack') if b'unpack' in data else False
	for link in links:
		app.pydebrid.pimp.add(link, gname, False)
	return {'message': 'Added links to queue'}

