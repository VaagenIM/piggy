from flask import Flask


def inject_devtools(app: Flask):
    # Inject livereload script into HTML responses
    @app.after_request
    def after_request(response):
        if response.status_code != 200:
            return response

        mimetype = response.mimetype or ""
        if not mimetype.startswith("text/html"):
            return response

        if not isinstance(response.response, list):
            return response

        script = '<script src="http://localhost:35729/livereload.js"></script>'
        body = b"".join(response.response).decode()
        body = body.replace("</body>", f"{script}</body>")
        response.response = [body.encode("utf8")]
        response.content_length = len(response.response[0])
        return response
