#    Copyright 2021 bitrate16
#
#    Licensed under the Apache License, Version 2.0 (the "License");
#    you may not use this file except in compliance with the License.
#    You may obtain a copy of the License at
#
#        http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS,
#    WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#    See the License for the specific language governing permissions and
#    limitations under the License.

import abc
import yarl
import typing
import re
import functools

from aiohttp import web
from aiohttp import web_urldispatcher
from aiohttp import web_request
from aiohttp import web_response
from aiohttp import hdrs


# From: aiohttp: web_urldispatcher.py
ROUTE_RE = re.compile(r'(\{[_a-zA-Z][^{}]*(?:\{[^{}]*\}[^{}]*)*\})')

Handler = typing.Callable[[web_request.Request], typing.Awaitable[web_response.StreamResponse]]


# From: aiohttp: web_urldispatcher.py
def _quote_path(value: str) -> str:
    if web_urldispatcher.YARL_VERSION < (1, 6):
        value = value.replace("%", "%25")
    return yarl.URL.build(path=value, encoded=False).raw_path

# From: aiohttp: web_urldispatcher.py
def _unquote_path(value: str) -> str:
    return yarl.URL.build(path=value, encoded=True).path

# From: aiohttp: web_urldispatcher.py
def _requote_path(value: str) -> str:
    # Quote non-ascii characters and other characters which must be quoted,
    # but preserve existing %-sequences.
    result = _quote_path(value)
    if "%" in value:
        result = result.replace("%25", "%")
    return result


class AbstractPathRouter(abc.ABC, web_urldispatcher.AbstractResource):

	_routes: typing.Dict[str, web_urldispatcher.ResourceRoute]

	def __init__(self, name: typing.Optional[str] = None, domain: str = None):
		"""
		Create instance of AbstractPathRouter.
		`name` is set to 'dymanic' by DomainRouter.
		`domain` is optional parameter added automatically by DomainRouter for
		introspection `get_info()`.
		"""

		super().__init__(name=name)
		self._routes = {}
		self._domain = domain
	
	@property
	def routes(self) -> typing.Dict[str, typing.Union[Handler, web_urldispatcher.AbstractView]]:
		"""
		Property to return handler of current path
		"""
		return self._routes
	
	# Modify existing handlers by method

	def add_handler(self, method: str, handler: typing.Union[Handler, web_urldispatcher.AbstractView], overwrite: bool = True, overwrite_widecast: bool = True) -> bool:
		"""
		Sets handler for specified method. 
		If `overwrite` is set to True, it will overwrite any existing strict
		method (GET, PUT, POST, ..., but not *) handler.
		If no strict method handler found and `overwrite_widecast` is set to
		True, it will overwrite widecast (*) handlet than. In other case it
		explicitly adds new handler for strict method. If `method` parameter is
		already widecast (= '*'), it will ignore `overwrite_widecast` value and
		write new handler for widecast.
		"""
		
		method = method.upper()

		# Widecast check
		if method == hdrs.METH_ANY:
			if method in self._routes:
				if overwrite:
					self._routes[method] = web_urldispatcher.ResourceRoute(method, handler, self)
					return True
				else:
					return False
			else:
				self._routes[method] = web_urldispatcher.ResourceRoute(method, handler, self)
				return True
		
		# Strict check
		if method in self._routes:
			if overwrite:
				self._routes[method] = web_urldispatcher.ResourceRoute(method, handler, self)
				return True
			else:
				return False
		else:
			if hdrs.METH_ANY in self._routes:
				if overwrite_widecast:
					self._routes[hdrs.METH_ANY] = web_urldispatcher.ResourceRoute(method, handler, self)
					return True
				else:
					self._routes[method] = web_urldispatcher.ResourceRoute(method, handler, self)
					return True
			else:
				self._routes[method] = web_urldispatcher.ResourceRoute(method, handler, self)
				return True

	def contains_handler(self, method: str, match_widecast: bool = True) -> bool:
		"""
		Returns True if found handler for the matching HTTP method. 
		If `match_widecast` is set to True, it will first try to find handler
		for strict method name and if it is not found, returns handler for
		widecast METH_ANY.
		"""

		method = method.upper()

		# Try to find strict
		if method in self._routes:
			return True
		
		# Try to find widecast
		if match_widecast and hdrs.METH_ANY in self._routes:
			return True
		
		return False

	def get_handler(self, method: str, match_widecast: bool = True) -> typing.Union[Handler, web_urldispatcher.AbstractView]:
		"""
		Returns handler for the matching HTTP method. 
		If `match_widecast` is set to True, it will first try to find handler
		for strict method name and if it is not found, returns handler for
		widecast METH_ANY.
		"""

		method = method.upper()

		# Try to find strict
		if method in self._routes:
			return self._routes[method].handler
		
		# Try to find widecast
		if match_widecast and hdrs.METH_ANY in self._routes:
			return self._routes[hdrs.METH_ANY].handler
		
		return None
	
	def get_handler_with_method(self, method: str, match_widecast: bool = True) -> typing.Tuple[str, typing.Union[Handler, web_urldispatcher.AbstractView]]:
		"""
		Returns method and handler for the matching HTTP method. 
		If `match_widecast` is set to True, it will first try to find handler
		for strict method name and if it is not found, returns handler for
		widecast METH_ANY.
		"""

		method = method.upper()

		# Try to find strict
		if method in self._routes:
			return method, self._routes[method].handler
		
		# Try to find widecast
		if match_widecast and hdrs.METH_ANY in self._routes:
			return hdrs.METH_ANY, self._routes[hdrs.METH_ANY].handler
		
		return None, None
	
	def get_handler_route(self, method: str, match_widecast: bool = True) -> web_urldispatcher.AbstractRoute:
		"""
		Returns handler route for the matching HTTP method. 
		If `match_widecast` is set to True, it will first try to find handler
		for strict method name and if it is not found, returns handler for
		widecast METH_ANY.
		"""

		method = method.upper()

		# Try to find strict
		if method in self._routes:
			return self._routes[method]
		
		# Try to find widecast
		if match_widecast and hdrs.METH_ANY in self._routes:
			return self._routes[hdrs.METH_ANY]
		
		return None
	
	def get_handler_route_with_method(self, method: str, match_widecast: bool = True) -> typing.Tuple[str, web_urldispatcher.AbstractRoute]:
		"""
		Returns method and handler route for the matching HTTP method. 
		If `match_widecast` is set to True, it will first try to find handler
		for strict method name and if it is not found, returns handler for
		widecast METH_ANY.
		"""

		method = method.upper()

		# Try to find strict
		if method in self._routes:
			return method, self._routes[method]
		
		# Try to find widecast
		if match_widecast and hdrs.METH_ANY in self._routes:
			return hdrs.METH_ANY, self._routes[hdrs.METH_ANY]
		
		return None, None
	
	def del_handler(self, method: str) -> bool:
		"""
		Removes method handler if it exists, returns True if removed.
		"""

		method = method.upper()

		if method in self._routes:
			del self._routes[method]
			return True
		
		return False

	def del_handlers(self) -> None:
		"""
		Remove all existing handlers.
		"""

		self._routes.clear()

	def has_method(self, method: str, match_widecast: bool = True):
		"""
		Checks if this router has handler for specified method.
		`match_widecast` allows the given method match if handler for METH_ANY
		exists.
		"""

		return method.upper() in self._routes or match_widecast and hdrs.METH_ANY in self._routes

	@property
	def allowed_methods(self) -> typing.List[str]:
		"""
		Returns list of allowed methods
		"""

		return hdrs.METH_ALL if hdrs.METH_ANY in self._routes else self._routes.keys()

	@abc.abstractmethod
	def raw_match(self, path: str) -> bool:
		"""
		Performs raw match of path string
		"""
		pass
	
	@abc.abstractmethod
	def match(self, path: str) -> bool:
		"""
		Performs full match of path string
		"""
		pass

	@abc.abstractmethod
	def match_info(self, path: str) -> typing.Optional[typing.Dict[str, str]]:
		"""
		Performs full match of path string with parameters extraction
		"""
		pass
	
	async def resolve(self, request: web_request.Request) -> typing.Tuple[typing.Optional[web_urldispatcher.AbstractMatchInfo], typing.Set[str]]:
		"""
		Resolve resource
		Return (UrlMappingMatchInfo, allowed_methods) pair.
		"""

		match_info = self.match_info(request.path)

		# Path does not match
		if match_info is None:
			return None, set()
		
		# Try to get handler for this method
		method = request.method.upper()
		existing_handler_route = self.get_handler_route(method)

		# METH_ANY is extracted to METH_ALL
		allowed_methods = set(hdrs.METH_ALL if hdrs.METH_ANY in self._routes else self._routes.keys())

		if existing_handler_route is None:
			return None, allowed_methods
		
		return web_urldispatcher.UrlMappingMatchInfo(match_info, existing_handler_route), allowed_methods	

	def __len__(self) -> int:
		return len(self._routes)

	def __iter__(self) -> typing.Iterator[web_urldispatcher.AbstractRoute]:
		return iter(self._routes.values())


# Duck (important):
#	__
# <(o )___
#  ( ._> /
#   `---'   hjw

class PlainPathRouter(AbstractPathRouter):

	_raw_path: str
	_path: str

	def __init__(self, path: str, name: typing.Optional[str] = None, domain: str = None):
		super().__init__(name, domain)
		self._raw_path = path
		self._path = _requote_path(path)

	@property
	def canonical(self) -> str:
		"""
		Exposes the resource's canonical path.
		For example '/foo/bar/{name}'
		"""
		return self._raw_path
	
	def url_for(self, **kwargs: str) -> yarl.URL:
		"""
		Construct url for resource with additional params.
		"""
		return self._path
	
	def add_prefix(self, prefix: str) -> None:
		# TODO: Add support for subapps
		raise RuntimeError('Prefixes are not supported in PlainPathHandler')

	def get_info(self) -> typing.TypedDict:
		"""
		Return a dict with additional info useful for introspection (c)
		"""
		return {
			'path': self._path,
			'formatter': None,
			'pattern': None,
			'directory': None,
			'prefix': None,
			'routes': None,
			'app': None,
			'domain': self._domain,
			'rule': None,
			'http_exception': None
		}

	def raw_match(self, path: str) -> bool:
		return self._raw_path == path
	
	def match(self, path: str) -> bool:
		return self._path == path
	
	def match_info(self, path: str) -> typing.Optional[typing.Dict[str, str]]:
		if self._path == path:
			return {}
		else:
			return None

class DynamicPathRouter(AbstractPathRouter):
	
	# From: aiohttp: web_urldispatcher.py
	DYN         = re.compile(r'\{(?P<var>[_a-zA-Z][_a-zA-Z0-9]*)\}')
	DYN_WITH_RE = re.compile(r'\{(?P<var>[_a-zA-Z][_a-zA-Z0-9]*):(?P<re>.+)\}')
	GOOD        = r'[^{}/]+'
	
	_raw_path: str

	def __init__(self, path: str, name: typing.Optional[str] = None, domain: str = None):
		super().__init__(name, domain)
		self._raw_path = path

		# From: aiohttp.web_urldispatcher.DynamicResource.__init__
		pattern = ''
		formatter = ''

		for part in ROUTE_RE.split(path):

			match = self.DYN.fullmatch(part)
			if match:
				pattern += '(?P<{}>{})'.format(match.group('var'), self.GOOD)
				formatter += '{' + match.group('var') + '}'
				continue

			match = self.DYN_WITH_RE.fullmatch(part)
			if match:
				pattern += '(?P<{var}>{re})'.format(**match.groupdict())
				formatter += '{' + match.group('var') + '}'
				continue

			if '{' in part or '}' in part:
				raise ValueError(f"Invalid path '{path}'['{part}']")
			
			part = _requote_path(part)
			formatter += part
			pattern += re.escape(part)
			
		try:
			compiled = re.compile(pattern)
		except re.error as exc:
			raise ValueError(f"Bad pattern '{pattern}': {exc}") from None
		
		assert compiled.pattern.startswith(re.escape('/'))
		assert formatter.startswith('/')
		self._pattern = compiled
		self._formatter = formatter
	
	@property
	def canonical(self) -> str:
		"""
		Exposes the resource's canonical path.
		For example '/foo/bar/{name}'
		"""
		return self._formatter
	
	def url_for(self, **kwargs: str) -> yarl.URL:
		"""
		Construct url for resource with additional params.
		"""
		url = self._formatter.format_map({k: _quote_path(v) for k, v in kwargs.items()})
		return yarl.URL.build(path=url, encoded=True)
	
	def add_prefix(self, prefix: str) -> None:
		# TODO: Add support for subapps
		raise RuntimeError('Prefixes are not supported in DynamicPathHandler')

	def get_info(self) -> typing.TypedDict:
		"""
		Return a dict with additional info useful for introspection (c)
		"""
		return {
			'path': self._raw_path,
			'formatter': self._formatter,
			'pattern': self._pattern,
			'directory': None,
			'prefix': None,
			'routes': None,
			'app': None,
			'domain': self._domain,
			'rule': None,
			'http_exception': None
		}
	
	def raw_match(self, path: str) -> bool:
		return self._raw_path == path
	
	def match(self, path: str) -> bool:
		return self._pattern.fullmatch(path)
	
	def match_info(self, path: str) -> typing.Optional[typing.Dict[str, str]]:
		match = self._pattern.fullmatch(path)
		if match is None:
			return None
		else:
			return { key: _unquote_path(value) for key, value in match.groupdict().items() }


class DomainRouter:

	_raw_domain: str
	_domain: web_urldispatcher.Domain
	_routes: typing.List[AbstractPathRouter]
	
	def __init__(self, domain: str):
		if domain is None:
			raise TypeError("Domain must be str")
		elif '*' in domain:
			self._domain = web_urldispatcher.MaskDomain(domain)
		else:
			self._domain = web_urldispatcher.Domain(domain)
		
		self._raw_domain = domain
		self._routes = []
	
	def canonical(self) -> str:
		return self._domain.canonical()
	
	@property
	def routes(self) -> typing.List[AbstractPathRouter]:
		return self._routes

	@property
	def domain(self) -> web_urldispatcher.Domain:
		return self._domain
	
	@property
	def raw_domain(self) -> str:
		return self._raw_domain
	
	def raw_domain_match(self, raw_domain: str) -> bool:
		"""
		Checks if argument equals to raw_domain value
		"""
		return self._raw_domain == raw_domain
	
	def domain_match(self, domain: str) -> bool:
		"""
		Checks if passed domain match with aiohttp.Domain.domain_match. Uses
		regular expression in case of MaskDomain and regular domain string else.
		By default None matches nothing.
		"""
		return domain is not None and self._domain.match_domain(domain)

	# Modify existing handlers by path

	def contains_router(self, raw_path: str) -> bool:
		"""
		Checks if this router contains AbstractPathRouter that raw_match the
		given raw_path and method.
		"""

		for r in self._routes:
			if r.raw_match(raw_path):
				return True

		return False

	def get_router(self, raw_path: str) -> AbstractPathRouter:
		"""
		Checks if this router contains AbstractPathRouter that raw_match the
		given raw_path and method.
		Returns this router.
		"""

		for r in self._routes:
			if r.raw_match(raw_path):
				return r

		return None 

	def add_router(self, raw_path: str, overwrite: bool = True) -> AbstractPathRouter:
		"""
		Sets router for given raw_path. If handler for this path already exists,
		it will overwrite it if `overwrite` is set to True.
		Returns the result router (new in case of overwrite, old else).
		"""

		for i, r in enumerate(self._routes):
			if r.raw_match(raw_path):
				if overwrite:
					if not ('{' in raw_path or '}' in raw_path or ROUTE_RE.search(raw_path)):
						self._routes[i] = PlainPathRouter(raw_path, name='<dynamic>', domain=self._raw_domain)
					else:
						self._routes[i] = DynamicPathRouter(raw_path, name='<dynamic>', domain=self._raw_domain)
					
					return self._routes[i]
				else:
					return r

		# Not found, create
		if not ('{' in raw_path or '}' in raw_path or ROUTE_RE.search(raw_path)):
			self._routes.append(PlainPathRouter(raw_path, name='<dynamic>', domain=self._raw_domain))
		else:
			self._routes.append(DynamicPathRouter(raw_path, name='<dynamic>', domain=self._raw_domain))
			
		return self._routes[-1]

	def del_router(self, raw_path: str) -> bool:
		"""
		Returns router that has the same raw_path.
		Returns True if route was deleted.
		"""

		for i, r in enumerate(self._routes):
			if r.raw_match(raw_path):
				self._routes.pop(i)
				return True
		
		return False

	def del_routers(self) -> None:
		"""
		Delete all routers
		"""

		self._routes.clear()

	async def resolve(self, request: web_request.Request) -> typing.Tuple[typing.Optional[web_urldispatcher.AbstractMatchInfo], typing.Set[str]]:
		"""
		Resolve resource
		Return (UrlMappingMatchInfo, allowed_methods) pair.
		"""

		# Search for the first matching AbstractPathRouter
		for r in self._routes:
			match_info = r.match_info(request.path)

			# Path does not match
			if match_info is None:
				continue
			
			# Try to get handler for this method
			method = request.method.upper()
			existing_handler_route = r.get_handler_route(method)

			# METH_ANY is extracted to METH_ALL
			allowed_methods = set(r.allowed_methods)

			if existing_handler_route is None:
				return None, allowed_methods
			
			return web_urldispatcher.UrlMappingMatchInfo(match_info, existing_handler_route), allowed_methods

		# No route found
		return None, set()


class DynamicRouter(web_urldispatcher.AbstractResource):

	"""
	DynamicRouter allows user to modify existing routes in runtime after call
	run_app(). This class handles all operations with request path, method and
	domain matching. If should be added to existing aiohttp.Application before
	call of run_app() to avoid attempt of modifying a frozen server. Each final
	handler implements all required methods to fit into aiohttp hierarchy and is
	mutable. This class acts as an implementation of Abstractresource mapped to
	'/{tail:.*}' but won't handle any path different from already defined with
	add_handler() and similar methods.
	"""

	_routes: typing.List[DomainRouter]

	def __init__(self, *, name: typing.Optional[str] = 'dynamic') -> None:
		super().__init__(name=name)
		self._routes = []
	
	def canonical(self) -> str:
		"""
		Returns canonical path to this resource.
		By default returns regular expression that matches any path because any
		path can be dynamically assigned to this handler.
		"""
		return '/{tail:.*}'
	
	def url_for(self, **kwargs: str) -> yarl.URL:
		"""
		Currently this method returns the same value as `canonical()`.
		"""
		return self.canonical()
	
	def add_prefix(self, prefix: str) -> None:
		# TODO: Add support for subapps
		raise RuntimeError('Prefixes are not supported in DynamicRouter')
	
	def get_info(self) -> typing.TypedDict:
		"""
		Return a dict with additional info useful for introspection (c)
		"""
		return {
			'path': '/{tail:.*}',
			'formatter': None,
			'pattern': None,
			'directory': None,
			'prefix': None,
			'routes': None, # TODO: Return routes to stored resources
			'app': None,
			'domain': '*', # TODO: Return merge of stored domains
			'rule': None,
			'http_exception': None
		}
	
	def raw_match(self, path: str):
		"""
		Performs raw match of given path with each of stored resource's paths.
		Returns true if any of stored reources raw_match required path.
		"""
		for r in self._routes:
			for g in r.routes:
				if g.raw_match(path):
					return True # b
		
		return False

	@property
	def routes(self) -> typing.List[DomainRouter]:
		return self._routes

	async def resolve(self, request: web_request.Request) -> typing.Tuple[typing.Optional[web_urldispatcher.AbstractMatchInfo], typing.Set[str]]:
		"""
		Resolves route that match the given domain, path and method
		"""
		
		# Find matching domain
		for r in self._routes:

			# Propagate resolve
			if r.domain_match(request.headers.get(hdrs.HOST, None)):
				return await r.resolve(request)
		
		# Return empty sets
		return None, set()
	
	def __len__(self) -> int:
		return len(self._routes)

	def __iter__(self) -> typing.Iterator[web_urldispatcher.AbstractRoute]:
		def iterator_wrapper():
			for r in self._routes:
				for g in r.routes:
					for b in g.routes.values():
						yield b
		
		return iterator_wrapper

	# Modify existing routers by domain name (or mask)

	def add_domain(self, raw_domain: str = '*', overwrite: bool = True) -> DomainRouter:
		"""
		Adds DomainRouter for the specified domain. In addition, domains are
		sorted to allow full match domains have more priority than masked
		domains. In such case domain foo.bar will be selected with more priority
		than *.bar.
		if `overwrite` is set to True, it will overwrite the domain with same
		raw_domain.
		Returns created or existing DomainRouter.
		"""

		for i, r in enumerate(self._routes):
			if r.raw_domain_match(raw_domain):
				if overwrite:
					rt = DomainRouter(raw_domain)
					self._routes[i] = rt

					# Sort domains list to make the widecast domain have less priority
					self._routes.sort(key=functools.cmp_to_key(lambda x, y: 1 if x.domain_match(y.raw_domain) else -1))

					return rt
				
				return r
		
		# Create new domain and sort domains list
		rt = DomainRouter(raw_domain)
		self._routes.append(rt)
		self._routes.sort(key=functools.cmp_to_key(lambda x, y: 1 if x.domain_match(y.raw_domain) else -1))

		return rt

	def get_domain(self, raw_domain: str = '*') -> DomainRouter:
		"""
		Returns domain router for the given raw_domain.
		"""

		for r in self._routes:
			if r.raw_domain_match(raw_domain):
				return r
		
		return None
	
	def contains_domain(self, raw_domain: str = '*') -> bool:
		"""
		Checks if there exists router for given raw_domain.
		"""

		for r in self._routes:
			if r.raw_domain_match(raw_domain):
				return True
		
		return False
	
	def del_domain(self, raw_domain: str = '*') -> bool:
		"""
		Removes router for given raw_domain. Does not sort routers list because
		order is not changed.
		Returns True if deleted.
		"""

		for i, r in enumerate(self._routes):
			if r.raw_domain_match(raw_domain):
				self._routes.pop(i)
				return True
		
		return False

	def del_domains(self) -> None:
		"""
		Deletes all domains.
		"""

		self._routes.clear()

	# User-side functions

	def add_handler(self, method: str, path: str, handler: typing.Union[Handler, web_urldispatcher.AbstractView], domain: str = '*', overwrite: bool = True, overwrite_widecast: bool = True) -> bool:
		"""
		Dynamically adds handler for specified domain, method and path by
		checking for existance using raw_match.
		If `overwrite` is set to True, it will overwrite the existing handler.
		If `overwrite_widecast` is set to true, it will overwrite METH_ANY if no
		handler found for strict method.
		"""

		return self.add_domain(domain, overwrite=False).add_router(path, overwrite=False).add_handler(method, handler, overwrite, overwrite_widecast)

	def contains_handler(self, method: str, path: str, domain: str = '*', match_widecast: bool = True) -> bool:
		"""
		Checks if handler for given domain, method and path already exists.
		If `match_widecast` is set to True, it will return True if no strict
		method match found, but there is widecast handler for this path.
		"""

		domain_router = self.get_domain(domain)
		if domain_router is not None:
			path_router = domain_router.get_router(path)
			if path_router is not None:
				return path_router.contains_handler(method, match_widecast)
		
		return False
	
	def get_handler(self, method: str, path: str, domain: str = '*', match_widecast: bool = True) -> typing.Union[Handler, web_urldispatcher.AbstractView]:
		"""
		Returns handler matching the given domain, method and path.
		If `match_widecast` is set to True, it will return handler for widecast
		if there is no handler for strict method.
		"""

		domain_router = self.get_domain(domain)
		if domain_router is not None:
			path_router = domain_router.get_router(path)
			if path_router is not None:
				return path_router.get_handler(method, match_widecast)
		
		return None
		
	def get_handler_with_method(self, method: str, path: str, domain: str = '*', match_widecast: bool = True) -> typing.Tuple[str, typing.Union[Handler, web_urldispatcher.AbstractView]]:
		"""
		Returns method string and handler matching the given domain, method and
		path.
		If `match_widecast` is set to True, it will return handler for widecast
		if there is no handler for strict method.
		"""

		domain_router = self.get_domain(domain)
		if domain_router is not None:
			path_router = domain_router.get_router(path)
			if path_router is not None:
				return path_router.get_handler_with_method(method, match_widecast)
		
		return None, None
	
	def del_handler(self, method: str, path: str, domain: str = '*') -> bool:
		"""
		Deletes handler mathing given domain, path and strict method.
		Returns True if deleted.
		"""

		domain_router = self.get_domain(domain)
		if domain_router is not None:
			path_router = domain_router.get_router(path)
			if path_router is not None:
				if path_router.del_handler(method):

					# Try to delete empty path router
					if len(path_router.routes) == 0:
						domain_router.del_router(path)
					
					# Try to remove empty domain router
					if len(domain_router.routes):
						self.del_domain(domain)
					
					return True

		return False
	
	def del_handlers(self):
		"""
		Deletes all handlers
		"""

		self._routes.clear()

	# More common user-friendly methods

	def add_view(self, path: str, handler: web_urldispatcher.AbstractView, domain: str = '*', overwrite: bool = True) -> bool:
		"""
		Adds view to this container. By default view enforces widecast method
		match (*).
		If `overwrite` is set to True, it will overwrite the existing handler.
		handler.
		"""

		return self.add_handler(hdrs.METH_ANY, path, handler, domain=domain, overwrite=overwrite)
	
	def add_get(self, path: str, handler: Handler, domain: str = '*', overwrite: bool = True, overwrite_widecast: bool = True) -> bool:
		"""
		Adds GET request handler.
		If `overwrite` is set to True, it will overwrite the existing handler.
		If `overwrite_widecast` is set to true, it will overwrite METH_ANY if no
		handler found for strict method.
		handler.
		"""

		return self.add_handler(hdrs.METH_GET, path, handler, domain=domain, overwrite=overwrite, overwrite_widecast=overwrite_widecast)

	def add_post(self, path: str, handler: Handler, domain: str = '*', overwrite: bool = True, overwrite_widecast: bool = True) -> bool:
		"""
		Adds POST request handler.
		If `overwrite` is set to True, it will overwrite the existing handler.
		If `overwrite_widecast` is set to true, it will overwrite METH_ANY if no
		handler found for strict method.
		handler.
		"""

		return self.add_handler(hdrs.METH_POST, path, handler, domain=domain, overwrite=overwrite, overwrite_widecast=overwrite_widecast)
		
	def add_put(self, path: str, handler: Handler, domain: str = '*', overwrite: bool = True, overwrite_widecast: bool = True) -> bool:
		"""
		Adds PUT request handler.
		If `overwrite` is set to True, it will overwrite the existing handler.
		If `overwrite_widecast` is set to true, it will overwrite METH_ANY if no
		handler found for strict method.
		handler.
		"""

		return self.add_handler(hdrs.METH_PUT, path, handler, domain=domain, overwrite=overwrite, overwrite_widecast=overwrite_widecast)
		
	def add_connect(self, path: str, handler: Handler, domain: str = '*', overwrite: bool = True, overwrite_widecast: bool = True) -> bool:
		"""
		Adds CONNECT request handler.
		If `overwrite` is set to True, it will overwrite the existing handler.
		If `overwrite_widecast` is set to true, it will overwrite METH_ANY if no
		handler found for strict method.
		handler.
		"""

		return self.add_handler(hdrs.METH_CONNECT, path, handler, domain=domain, overwrite=overwrite, overwrite_widecast=overwrite_widecast)
		
	def add_head(self, path: str, handler: Handler, domain: str = '*', overwrite: bool = True, overwrite_widecast: bool = True) -> bool:
		"""
		Adds HEAD request handler.
		If `overwrite` is set to True, it will overwrite the existing handler.
		If `overwrite_widecast` is set to true, it will overwrite METH_ANY if no
		handler found for strict method.
		handler.
		"""

		return self.add_handler(hdrs.METH_HEAD, path, handler, domain=domain, overwrite=overwrite, overwrite_widecast=overwrite_widecast)
		
	def add_delete(self, path: str, handler: Handler, domain: str = '*', overwrite: bool = True, overwrite_widecast: bool = True) -> bool:
		"""
		Adds DELETE request handler.
		If `overwrite` is set to True, it will overwrite the existing handler.
		If `overwrite_widecast` is set to true, it will overwrite METH_ANY if no
		handler found for strict method.
		handler.
		"""

		return self.add_handler(hdrs.METH_DELETE, path, handler, domain=domain, overwrite=overwrite, overwrite_widecast=overwrite_widecast)
		
	def add_patch(self, path: str, handler: Handler, domain: str = '*', overwrite: bool = True, overwrite_widecast: bool = True) -> bool:
		"""
		Adds PATCH request handler.
		If `overwrite` is set to True, it will overwrite the existing handler.
		If `overwrite_widecast` is set to true, it will overwrite METH_ANY if no
		handler found for strict method.
		handler.
		"""

		return self.add_handler(hdrs.METH_PATCH, path, handler, domain=domain, overwrite=overwrite, overwrite_widecast=overwrite_widecast)
		
	def add_trace(self, path: str, handler: Handler, domain: str = '*', overwrite: bool = True, overwrite_widecast: bool = True) -> bool:
		"""
		Adds TRACE request handler.
		If `overwrite` is set to True, it will overwrite the existing handler.
		If `overwrite_widecast` is set to true, it will overwrite METH_ANY if no
		handler found for strict method.
		handler.
		"""

		return self.add_handler(hdrs.METH_TRACE, path, handler, domain=domain, overwrite=overwrite, overwrite_widecast=overwrite_widecast)

	def add_any(self, path: str, handler: Handler, domain: str = '*', overwrite: bool = True, overwrite_widecast: bool = True) -> bool:
		"""
		Adds * (Any method) request handler.
		If `overwrite` is set to True, it will overwrite the existing handler.
		If `overwrite_widecast` is set to true, it will overwrite METH_ANY if no
		handler found for strict method.
		handler.
		"""

		return self.add_handler(hdrs.METH_ANY, path, handler, domain=domain, overwrite=overwrite, overwrite_widecast=overwrite_widecast)

	def attach(self, app: web.Application) -> None:
		"""
		Attach this resource to the passed pallication
		"""

		app.router.register_resource(self)
