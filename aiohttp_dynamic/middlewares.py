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

import typing
import functools

from aiohttp import web_request
from aiohttp import web_response
from aiohttp import hdrs
from .routing import Handler

class DynamicMiddleware(typing.Sized,
						typing.Iterable[typing.Tuple[str, typing.Callable[[web_request.Request, Handler], typing.Awaitable[web_response.StreamResponse]]]], 
						typing.Callable[[web_request.Request, Handler], typing.Awaitable[web_response.StreamResponse]]):
	
	"""
	Allows dynamically changing existing middlewares on the server. Supports
	add, get, and deletion of existing middleware handlers after run_app().
	"""

	# Compability with old aiohttp version
	__middleware_version__: int = 1

	# List of middlewares tuples
	# (domain_suffix, middleware_name, middleware_handler)
	_handlers: typing.List[typing.Tuple[str, str, typing.Callable[[web_request.Request, Handler], typing.Awaitable[web_response.StreamResponse]]]]

	def __init__(self, 
				middlewares: typing.List[typing.Callable[[web_request.Request, Handler], typing.Awaitable[web_response.StreamResponse]]] = [],
				named_middlewares: typing.List[typing.Tuple[str, str, typing.Callable[[web_request.Request, Handler], typing.Awaitable[web_response.StreamResponse]]]] = []) -> None:
		super().__init__()

		# Append unnamed and named middlewares
		self._handlers = [] if middlewares is None else [ ('', None, m) for m in middlewares ]
		self._handlers.extend([] if named_middlewares is None else named_middlewares)

		# Sort by suffix match
		self._handlers.sort(key=functools.cmp_to_key(lambda x, y: 1 if y.endswith(x) else -1))

	@property
	def handlers(self) -> typing.List[typing.Tuple[str, str, typing.Callable[[web_request.Request, Handler], typing.Awaitable[web_response.StreamResponse]]]]:
		"""
		Returns list of tuples (domain_suffix, middleware_name, middleware_handler)
		"""
		return self.handlers
	
	def add_handler(self, middleware: typing.Callable[[web_request.Request, Handler], typing.Awaitable[web_response.StreamResponse]], domain: str='', overwrite: bool = True) -> None:
		"""
		Append middleware to the end of middlewares list. Domain is optional and
		defines suffix for middleware.
		"""

		if domain is None:
			return False
		
		self._handlers.append((domain, None, middleware))

		# TODO: Insert without sort
		# Sort by suffix match
		self._handlers.sort(key=functools.cmp_to_key(lambda x, y: 1 if y[0].endswith(x[0]) else -1))

		return True
	
	def add_named_handler(self, middleware: typing.Callable[[web_request.Request, Handler], typing.Awaitable[web_response.StreamResponse]], name: str, domain: str='', overwrite: bool = True) -> bool:
		"""
		Append middleware to the end of middlewares list or replace existing by
		the same name if `overwrite` is set to True. Domain is optional and
		defines suffix for middleware.
		Named handler overwrites only by name. in case when domain match with
		another record, it is ignored.
		Returns True if added.
		"""

		if domain is None:
			return False

		if name is not None:
			for i, m in enumerate(self._handlers):
				if m[1] == name:
					if overwrite:
						self._handlers[i] = (domain, name, middleware)

						# TODO: Insert without sort
						# Sort by suffix match
						self._handlers.sort(key=functools.cmp_to_key(lambda x, y: 1 if y[0].endswith(x[0]) else -1))

						return True
					else:
						return False

		self._handlers.append((domain, name, middleware))

		# TODO: Insert without sort
		# Sort by suffix match
		self._handlers.sort(key=functools.cmp_to_key(lambda x, y: 1 if y[0].endswith(x[0]) else -1))
		
		return True
	
	def get_handler(self, index: int) -> typing.Callable[[web_request.Request, Handler], typing.Awaitable[web_response.StreamResponse]]:
		"""
		Returns middleware handler by index.
		"""

		return self._handlers[index][2]
	
	def get_named_handler(self, name: str) -> typing.Callable[[web_request.Request, Handler], typing.Awaitable[web_response.StreamResponse]]:
		"""
		Returns named middleware handler by it's name.
		"""
		
		if name is not None:
			for m in self._handlers:
				if m[1] == name:
					return m[2]
		
		return None
	
	def get_domain_handlers(self, domain: str) -> typing.Callable[[web_request.Request, Handler], typing.Awaitable[web_response.StreamResponse]]:
		"""
		Returns handlers for given domain suffix.
		"""
		
		result = []

		if domain is not None:
			for m in self._handlers:
				if m[0] == domain:
					result.append(m[2])
		
		return result
	
	def get_matching_domain_handlers(self, domain: str) -> typing.Callable[[web_request.Request, Handler], typing.Awaitable[web_response.StreamResponse]]:
		"""
		Returns handlers with domain matching given domain suffix.
		"""
		
		result = []

		if domain is not None:
			for m in self._handlers:
				if m[0].endswith(domain):
					result.append(m[2])
		
		return result
	
	def contains_named_handler(self, name: str) -> bool:
		"""
		Checks if there exists middleware with specified name.
		"""
		
		if name is not None:
			for m in self._handlers:
				if m[1] == name:
					return True
		
		return False
	
	def contains_domain_handler(self, domain: str) -> bool:
		"""
		Checks if there exists middleware with given domain suffix.
		"""
		
		if domain is not None:
			for m in self._handlers:
				if m[0] == domain:
					return True
		
		return False
	
	def contains_matching_domain_handler(self, domain: str) -> bool:
		"""
		Checks if there exists middleware matching given domain suffix.
		"""
		
		if domain is not None:
			for m in self._handlers:
				if m[0].endswith(domain):
					return True
		
		return False

	def del_handler(self, index: int) -> None:
		"""
		Delete middleware by index.
		"""

		self._handlers.pop(index)
	
	def del_named_handler(self, name: str) -> None:
		"""
		Deletes named middleware handler by it's name.
		"""
		
		if name is not None:
			for i, m in enumerate(self._handlers):
				if m[1] == name:
					self._handlers.pop(i)
					return
	
	def del_domain_handlers(self, domain: str) -> None:
		"""
		Deletes handlers for given domain suffix.
		"""
		
		if domain is not None:
			self._handlers[:] = [m for m in self._handlers if m[0] != domain]

	def del_matching_domain_handlers(self, domain: str) -> None:
		"""
		Deletes handlers matching given domain suffix.
		"""
		
		if domain is not None:
			self._handlers[:] = [m for m in self._handlers if not m[0].endswith(domain)]

	def del_handlers(self) -> None:
		"""
		Remove all existing middleware handlers.
		"""

		self._handlers.clear()
	
	def __iter__(self) -> typing.Iterator[typing.Tuple[str, str, typing.Callable[[web_request.Request, Handler], typing.Awaitable[web_response.StreamResponse]]]]:
		return iter(self._handlers)
	
	def __len__(self) -> int:
		return len(self._handlers)
	
	async def __call__(self, request: web_request.Request, handler: Handler) -> web_response.StreamResponse:
		domain = request.headers.get(hdrs.HOST, None)

		if domain is None:
			# Rewrap and return
			for s, n, h in reversed(self._handlers): # Do not remove n, 
				handler = functools.update_wrapper(functools.partial(h, handler=handler), handler)
			
			return await handler(request)
		else:
			# Rewrap only matching suffix and return
			for s, n, h in reversed(self._handlers): # Do not remove n, 
				if domain.endswith(s):
					handler = functools.update_wrapper(functools.partial(h, handler=handler), handler)
			
			return await handler(request)
