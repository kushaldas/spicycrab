actix-web Support
=================

spicycrab provides stubs for `actix-web <https://actix.rs/>`_, a powerful, pragmatic, and
extremely fast web framework for Rust. This allows you to write Python code using familiar
actix-web patterns and transpile it to idiomatic Rust.

Installation
------------

Generate and install actix-web stubs:

.. code-block:: bash

   # Generate stubs
   cookcrab generate actix-web -o ./stubs

   # Install in your environment
   pip install -e ./stubs/actix-web

Basic Example
-------------

Python input:

.. code-block:: python

   from spicycrab_actix_web import App, HttpServer, HttpResponse, get

   async def hello() -> HttpResponse:
       return HttpResponse.Ok().body("Hello World!")

   async def main() -> None:
       HttpServer.new(App.new().route("/", get().to(hello))).bind("127.0.0.1:8080").run()

Rust output:

.. code-block:: rust

   pub async fn hello() -> actix_web::HttpResponse {
       actix_web::HttpResponse::Ok().body("Hello World!".to_string())
   }

   #[actix_web::main]
   pub async fn main() {
       actix_web::HttpServer::new(move || {
           actix_web::App::new().route("/", actix_web::web::get().to(hello))
       }).bind("127.0.0.1:8080").unwrap().run().await;
   }

Supported Types
---------------

HttpResponse
^^^^^^^^^^^^

Build HTTP responses with various status codes and content:

.. code-block:: python

   from spicycrab_actix_web import HttpResponse

   # Success responses
   HttpResponse.Ok().body("Success")
   HttpResponse.Created().body('{"id": 1}')
   HttpResponse.NoContent().finish()

   # Error responses
   HttpResponse.BadRequest().body("Invalid input")
   HttpResponse.Unauthorized().body("Not authorized")
   HttpResponse.Forbidden().body("Access denied")
   HttpResponse.NotFound().body("Not found")
   HttpResponse.InternalServerError().body("Server error")

Custom headers and content types:

.. code-block:: python

   # JSON response with content-type
   HttpResponse.Ok().content_type("application/json").body('{"status": "ok"}')

   # Custom headers
   HttpResponse.Ok().insert_header(("Cache-Control", "max-age=3600")).body("Cached content")
   HttpResponse.Ok().insert_header(("X-Custom-Header", "value")).body("Custom header")

App
^^^

Create application instances with routes:

.. code-block:: python

   from spicycrab_actix_web import App, get, post

   # Single route
   App.new().route("/", get().to(handler))

   # Multiple routes (must be chained, see note below)
   App.new().route("/users", get().to(list_users)).route("/users", post().to(create_user))

HttpServer
^^^^^^^^^^

Bind and run the server:

.. code-block:: python

   from spicycrab_actix_web import App, HttpServer, get

   async def main() -> None:
       HttpServer.new(App.new().route("/", get().to(handler))).bind("0.0.0.0:8080").run()

HTTP Methods
^^^^^^^^^^^^

All standard HTTP methods are supported:

.. code-block:: python

   from spicycrab_actix_web import get, post, put, delete, patch

   App.new().route("/resource", get().to(get_handler))      # GET
   App.new().route("/resource", post().to(create_handler))  # POST
   App.new().route("/resource", put().to(update_handler))   # PUT
   App.new().route("/resource", delete().to(delete_handler)) # DELETE
   App.new().route("/resource", patch().to(patch_handler))  # PATCH

Example Patterns
----------------

REST API
^^^^^^^^

.. code-block:: python

   from spicycrab_actix_web import App, HttpServer, HttpResponse, get, post, put, delete

   async def list_items() -> HttpResponse:
       return HttpResponse.Ok().content_type("application/json").body('{"items": []}')

   async def create_item() -> HttpResponse:
       return HttpResponse.Created().content_type("application/json").body('{"id": 1}')

   async def update_item() -> HttpResponse:
       return HttpResponse.Ok().content_type("application/json").body('{"updated": true}')

   async def delete_item() -> HttpResponse:
       return HttpResponse.NoContent().finish()

   async def main() -> None:
       HttpServer.new(
           App.new()
               .route("/items", get().to(list_items))
               .route("/items", post().to(create_item))
               .route("/items/{id}", put().to(update_item))
               .route("/items/{id}", delete().to(delete_item))
       ).bind("127.0.0.1:8080").run()

Health Check Endpoints
^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: python

   from spicycrab_actix_web import App, HttpServer, HttpResponse, get

   async def health() -> HttpResponse:
       return HttpResponse.Ok().content_type("application/json").body('{"status": "healthy"}')

   async def liveness() -> HttpResponse:
       return HttpResponse.Ok().body("OK")

   async def readiness() -> HttpResponse:
       return HttpResponse.Ok().content_type("application/json").body('{"ready": true}')

   async def main() -> None:
       HttpServer.new(
           App.new()
               .route("/health", get().to(health))
               .route("/healthz", get().to(liveness))
               .route("/ready", get().to(readiness))
       ).bind("127.0.0.1:8080").run()

JSON Error Responses
^^^^^^^^^^^^^^^^^^^^

.. code-block:: python

   from spicycrab_actix_web import App, HttpServer, HttpResponse, get

   async def not_found_error() -> HttpResponse:
       return HttpResponse.NotFound().content_type("application/json").body(
           '{"error": "not_found", "message": "Resource not found"}'
       )

   async def validation_error() -> HttpResponse:
       return HttpResponse.BadRequest().content_type("application/json").body(
           '{"error": "validation_failed", "message": "Invalid input"}'
       )

Security Headers
^^^^^^^^^^^^^^^^

.. code-block:: python

   from spicycrab_actix_web import App, HttpServer, HttpResponse, get

   async def secure_page() -> HttpResponse:
       return HttpResponse.Ok().insert_header((
           "Content-Security-Policy",
           "default-src 'self'"
       )).insert_header((
           "X-Content-Type-Options",
           "nosniff"
       )).insert_header((
           "X-Frame-Options",
           "DENY"
       )).insert_header((
           "Strict-Transport-Security",
           "max-age=31536000; includeSubDomains"
       )).body("<html>Secure content</html>")

Redirects
^^^^^^^^^

.. code-block:: python

   from spicycrab_actix_web import App, HttpServer, HttpResponse, get

   async def redirect_home() -> HttpResponse:
       return HttpResponse.Found().insert_header(("Location", "/")).finish()

   async def redirect_permanent() -> HttpResponse:
       return HttpResponse.MovedPermanently().insert_header(("Location", "/new-location")).finish()

Known Limitations
-----------------

Method Chaining Required
^^^^^^^^^^^^^^^^^^^^^^^^

actix-web's ``App`` type is generic: ``App<T>``. Each ``.route()`` call returns a NEW ``App``
with a DIFFERENT type parameter due to service factory composition. This means you **must**
use method chaining:

.. code-block:: python

   # CORRECT - method chaining, type inferred at end
   HttpServer.new(
       App.new()
           .route("/a", get().to(handler_a))
           .route("/b", get().to(handler_b))
   )

   # WRONG - intermediate variable has wrong type after each route()
   app = App.new()
   app = app.route("/a", get().to(handler_a))  # Type changes!
   app = app.route("/b", get().to(handler_b))  # Type mismatch!

Async Main Required
^^^^^^^^^^^^^^^^^^^

The main function must be declared ``async`` to use the ``#[actix_web::main]`` macro:

.. code-block:: python

   # CORRECT
   async def main() -> None:
       HttpServer.new(...).bind("127.0.0.1:8080").run()

   # WRONG - missing async
   def main() -> None:
       HttpServer.new(...).bind("127.0.0.1:8080").run()

Available Examples
------------------

The following examples are available in ``spicycrab-stubs/examples/actix-web/``:

1. **actix_01_hello.py** - Basic hello world
2. **actix_02_multiple_routes.py** - GET, POST, PUT, DELETE on same path
3. **actix_03_json_response.py** - JSON responses with content-type
4. **actix_04_status_codes.py** - All status codes (200, 201, 204, 400, 401, 403, 404, 500)
5. **actix_05_custom_headers.py** - Cache-Control, CORS, custom headers
6. **actix_06_request_info.py** - Basic request handling patterns
7. **actix_07_content_types.py** - text/plain, text/html, application/json, etc.
8. **actix_08_api_versioning.py** - /api/v1/* and /api/v2/* versioned endpoints
9. **actix_09_health_check.py** - Health, liveness, readiness probes for K8s
10. **actix_10_rest_api.py** - Complete CRUD REST API pattern
11. **actix_11_error_responses.py** - Structured JSON error responses
12. **actix_12_redirect.py** - Location header redirect patterns
13. **actix_13_static_responses.py** - robots.txt, sitemap.xml, manifest.json
14. **actix_14_security_headers.py** - CSP, XSS protection, HSTS
15. **actix_15_webhook.py** - POST-only webhook endpoints
16. **actix_16_combined_app.py** - Complete app combining multiple features

To transpile and run an example:

.. code-block:: bash

   cd demospace
   uv run crabpy transpile ../spicycrab-stubs/examples/actix-web/actix_01_hello.py -o rust_hello -n hello
   cd rust_hello
   cargo run --release
