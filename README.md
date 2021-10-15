# aiohttp-dynamic

aiohttp-dynamic is python extension for [aiohttp module](github.com/aio-libs/aiohttp) that provides creation and modification of custom request handlers after Application is frozen.
Why? Because I can.

## Overview

- Support for routing by domain, method and path of the request
- Overwrite existing routes safely
- Support for dynamically changeable middlewares
- Update your routes and middlewares after `run_app()` without breaking anything

aiohttp-dynamic provides interfaces for routing your requests by domain, method and path parameters with certain priorities:
- Strict domain (foo.bar) has more priority rather than Mask domain (*.bar)
- Strict HTTP Method (GET, PUT, ..) has more priority rather than widecast Any method (*)

Also, middlewares can be changed in runtime

## Installation

Install using pip for python3.5+:
```
pip3 install aiohttp-dynamic
```

Manual installation:
```
pip install -r requirements.txt
pip install .
```

## Dynamic routing

Dynamic routing is provided by `DynamicRouter` class implementing `aiohttp.AbstractResource`. After attaching an instace of `DynamicRouter` to the existing application, it will handle all requests that match stored (domain, method, path) set.
An example of attaching handlers after `run_app()` call is shown below:

```python
import aiohttp
from aiohttp import web
import aiohttp_dynamic

# Create Application, DynamicRouter and attach it
dyn = aiohttp_dynamic.DynamicRouter()
app = web.Application()
dyn.attach(app) # or app.router.register_resource(dyn)

# Run app, not it is frozen and does not allow adding new routes
web.run_app(app)

# Example of attaching after app was frozen
def handler(request):
    return web.json_response({ 'message': 'ok' })

dyn.add_get('/myroute', handler)
```

It also supports overwriting and deletion of the existing routes:

```python
# overwrite is True by default, but do it explicitly
dyn.add_get('/myroute', handler, overwrite=True)

# Delete this route
dyn.del_handler('GET', '/myroute')
```

In case when a widecast (*) method handler exists for the same path, it can be overwritten or simply ignored by creating a strict method handler:

```python
# Create a widecast handler
dyn.add_any('/myroute', handler_1)

# Do not overwrite it and create a separate strict GET handler
# Now, if there is GET request, handler_2 will be executed instead of handler_1, but handler_1 still works for other methods
dyn.add_get('/myroute', handler_2, overwrite_widecast=False)
```

You can check if there exists any handler for specified path:

```python
# Will return True if there is GET of Any (*) handler
dyn.contains_handler('GET', '/myroute')

# Will return True only if there is GET handler
dyn.contains_handler('GET', '/myroute', match_widecast=False)
```

Finally you can clear all handlers:

```python
dyn.del_handlers()
```

### Dynamic domain routing

This extension soppurts routing based on domans too:

```python
import aiohttp
from aiohttp import web
import aiohttp_dynamic

# Create Application, DynamicRouter and attach it
dyn = aiohttp_dynamic.DynamicRouter()
app = web.Application()
dyn.attach(app) # or app.router.register_resource(dyn)

# Run app, not it is frozen and does not allow adding new routes
web.run_app(app)

# Example of attaching after app was frozen
def handler(request):
    return web.json_response({ 'message': 'ok' })

# This handler works only for requests to foo.bar
dyn.add_get('/myroute', handler, domain='foo.bar')
```

`add_get` and other handler adding methods support `domain` parameter to explicitly dfine supported domain or masked domain:

```python
# Add route handler for domain foo.bar
dyn.add_get('/myroute2', handler_2, domain='foo.bar')

# Add route handler for domain *.bar
# This route has less priority than foo.bar and will be called for bar.bar, but not for foo.bar defined earlier
# By default domain='*', mathing everything
dyn.add_get('/myroute2', handler_2, domain='*.bar')
```

You can delete all routes that belong to certain domain (or mask):

```python
dyn.del_domain('*.bar')
```

## Dynamic middlewares

By default middlewares are specified on app creation `web.Application(middlewares=..)`, however you can modify them in runtime using `DynamicMiddleware` class:

```python
import aiohttp
from aiohttp import web
import aiohttp_dynamic

# Create Application and DynamicMiddleware container
dynmw = aiohttp_dynamic.DynamicMiddleware()
app = web.Application(middlewares=[dynmw])

# Run app, not it is frozen and does not allow adding new routes
web.run_app(app)

# Example of attaching after app was frozen
def middleware(request, handler):
    return await handler(erquest)

# Add middlewares after server was started
dynmw.add_handler(middleware)
```

Middlewares are executed in a strict order:

```python
def middleware_1(request, handler):
    print('middleware 1')
    return await handler(erquest)
    
def middleware_2(request, handler):
    print('middleware 2')
    return await handler(erquest)
    
def middleware_3(request, handler):
    print('middleware 3')
    return await handler(erquest)
    
dynmw.add_handler(middleware_1)
dynmw.add_handler(middleware_2)
dynmw.add_handler(middleware_2)
```

This will output the following on request:

```
middleware 1
middleware 2
middleware 3
```

You can always delete a middleware, delete all middlewares or even iterate over this class (why?)

```python
# Delete all
dynmw.del_handlers()

# Add again
dynmw.add_handler(middleware_1)
dynmw.add_handler(middleware_2)
dynmw.add_handler(middleware_2)

# Delete middleware_2
dynmw.del_handler(1)

# Iterate if you're brave enough
for mw in dynmw:
    print('Hellow World!')
```

## A bit explaination about priorities

There are two king of priorities: Method priority and Domain priority:
- Strict method (like GET, POST, ..) is preferred to be executed rather than widecast Any (*). So, if you have a handler for View, you can add handlers for unused methods on the same path without removing your View
- Domains are always sorted using regular expression matching: Domain A is less than Domain B when B matches A. (Example: foo.bar < *.bar and in case when request contains foo.bar, handler for foo.bar will be executed even if there is also handler for the same path on domain *.bar). This allows you to simply create multiple domain masks ans exclusive rules for certain domains stayinf confident about the selection priority.

## A bit explaination about motivation

1. Because I can
2. Because aiohttp is flexible asynchronous framework that supports static scheme definition, validation (using aiohttp-pydantic), but in case when you need to define your routes dynamically, you won't be able to do it, so here i am.