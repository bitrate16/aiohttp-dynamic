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
	# (middleware_name, middleware_handler)
	_handlers: typing.List[typing.Tuple[str, typing.Callable[[web_request.Request, Handler], typing.Awaitable[web_response.StreamResponse]]]]

	def __init__(self, 
				middlewares: typing.List[typing.Callable[[web_request.Request, Handler], typing.Awaitable[web_response.StreamResponse]]] = [],
				named_middlewares: typing.List[typing.Tuple[str, typing.Callable[[web_request.Request, Handler], typing.Awaitable[web_response.StreamResponse]]]] = []) -> None:
		super().__init__()

		# Append unnamed and named middlewares
		self._handlers = [] if middlewares is None else [ (None, m) for m in middlewares ]
		self._handlers.extend([] if named_middlewares is None else named_middlewares)

	@property
	def handlers(self) -> typing.List[typing.Tuple[str, typing.Callable[[web_request.Request, Handler], typing.Awaitable[web_response.StreamResponse]]]]:
		return self.handlers
	
	def add_handler(self, middleware: typing.Callable[[web_request.Request, Handler], typing.Awaitable[web_response.StreamResponse]]) -> None:
		"""
		Append middleware to the end of middlewares list.
		"""

		self._handlers.append((None, middleware))
	
	def add_named_handler(self, middleware: typing.Callable[[web_request.Request, Handler], typing.Awaitable[web_response.StreamResponse]], name: str, overwrite: bool = True) -> bool:
		"""
		Append middleware to the end of middlewares list or replace existing by
		the same name if `overwrite` is set to True.
		Returns True if added.
		"""

		if name is not None:
			for i, m in enumerate(self._handlers):
				if m[0] == name:
					if overwrite:
						self._handlers[i] = (name, middleware)
						return True
					else:
						return False

		self._handlers.append((name, middleware))
		return True
	
	def get_handler(self, index: int) -> typing.Callable[[web_request.Request, Handler], typing.Awaitable[web_response.StreamResponse]]:
		"""
		Returns middleware handler by index.
		"""

		return self._handlers[index][1]
	
	def get_named_handler(self, name: str) -> typing.Callable[[web_request.Request, Handler], typing.Awaitable[web_response.StreamResponse]]:
		"""
		Returns named middleware handler by it's name.
		"""
		
		if name is not None:
			for m in self._handlers:
				if m[0] == name:
					return m[1]
		
		return None
	
	def contains_named_handler(self, name: str) -> bool:
		"""
		Checks if there exists middleware with specified name.
		"""
		
		if name is not None:
			for m in self._handlers:
				if m[0] == name:
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
				if m[0] == name:
					self._handlers.pop(i)

	def del_handlers(self) -> None:
		"""
		Remove all existing middleware handlers.
		"""

		self._handlers.clear()
	
	def __iter__(self) -> typing.Iterator[typing.Tuple[str, typing.Callable[[web_request.Request, Handler], typing.Awaitable[web_response.StreamResponse]]]]:
		return iter(self._handlers)
	
	def __len__(self) -> int:
		return len(self._handlers)
	
	async def __call__(self, request: web_request.Request, handler: Handler) -> web_response.StreamResponse:
		# Rewrap and return
		for n, h in reversed(self._handlers): # Do not remove n, 
			handler = functools.update_wrapper(functools.partial(h, handler=handler), handler)
		
		return await handler(request)
