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
						typing.Iterable[typing.Callable[[web_request.Request, Handler], typing.Awaitable[web_response.StreamResponse]]], 
						typing.Callable[[web_request.Request, Handler], typing.Awaitable[web_response.StreamResponse]]):
	
	"""
	Allows dynamically changing existing middlewares on the server. Supports
	add, get, and deletion of existing middleware handlers after run_app().
	"""

	_handlers: typing.List[typing.Callable[[web_request.Request, Handler], typing.Awaitable[web_response.StreamResponse]]]

	def __init__(self, middlewares: typing.List[typing.Callable[[web_request.Request, Handler], typing.Awaitable[web_response.StreamResponse]]] = []) -> None:
		super().__init__()

		self._handlers = [] if middlewares is None else middlewares

	@property
	def handlers(self) -> typing.List[typing.Callable[[web_request.Request, Handler], typing.Awaitable[web_response.StreamResponse]]]:
		return self.handlers
	
	def add_handler(self, middleware: typing.Callable[[web_request.Request, Handler], typing.Awaitable[web_response.StreamResponse]]) -> None:
		"""
		Append middleware to the end of middlewares list.
		"""

		self._handlers.append(middleware)
	
	def get_handler(self, index: int) -> typing.Callable[[web_request.Request, Handler], typing.Awaitable[web_response.StreamResponse]]:
		"""
		Returns middleware by index.
		"""

		return self._handlers[index]

	def del_handler(self, index: int) -> None:
		"""
		Delete middleware by index.
		"""

		self._handlers.pop(index)

	def del_handlers(self) -> None:
		"""
		Remove all existing middleware handlers.
		"""

		self._handlers.clear()
	
	def __iter__(self) -> typing.Iterator[typing.Callable[[web_request.Request, Handler], typing.Awaitable[web_response.StreamResponse]]]:
		return iter(self._handlers)
	
	def __len__(self) -> int:
		return len(self._handlers)
	
	async def __call__(self, request: web_request.Request, handler: Handler) -> web_response.StreamResponse:
		# Rewrap and return
		for h in reversed(self._handlers):
			handler = functools.update_wrapper(functools.partial(h, handler=handler), handler)
		
		return handler
