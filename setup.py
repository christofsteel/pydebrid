#!/usr/bin/env python3
from distutils.core import setup

files = ["data/*"]

setup(name="pydebrid",
	version = "0.1",
	description = "Python webdownloader for Alldebrid",
	author = "Christoph \"Hammy\" Stahl",
	author_email = "christoph.stahl@uni-dortmund.de",
	url = "https://github.com/christofsteel/pydebrid",
	packages=['PyDebrid'],
	package_dir={'' : 'src/'},
	scripts=['src/pydebrid'],
	package_data={'PyDebrid': files},
	install_requires=['jinja2', 'bottle', 'pyquery', 'rarlib'])
