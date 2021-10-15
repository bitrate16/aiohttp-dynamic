from setuptools import setup

setup(
	name = 'aiohttp_dynamic',
	packages = ['aiohttp_dynamic'],
	version = '1.0.0',
	license='Apache License 2.0',
	description = 'aiohttp extension to build and modify dynamic routes in runtime',
	author = 'bitrate16',
	author_email = 'bitrate16@gmail.com',
	url = 'https://github.com/bitrate16/aiohttp-dynamic',
	download_url = 'https://github.com/bitrate16/aiohttp-dynamic/archive/1.0.0.tar.gz',
	keywords = ['aiohttp', 'dynamic', 'routing', 'mutable'],
	install_requires = [
		'aiohttp',
		'yarl'
	],
	classifiers = [
		# Chose either "3 - Alpha", "4 - Beta" or "5 - Production/Stable" as the current state of your package
		'Development Status :: 5 - Production/Stable',
		'Intended Audience :: Developers',
		'Topic :: Software Development :: Libraries :: Python Modules',
		'License :: OSI Approved :: Apache Software License',
		'Programming Language :: Python :: 3.5',
		'Programming Language :: Python :: 3.6',
		'Programming Language :: Python :: 3.7',
		'Programming Language :: Python :: 3.8',
		'Programming Language :: Python :: 3.9',
		'Programming Language :: Python :: 3.10',
		'Programming Language :: Python :: 3.11'
	]
)
