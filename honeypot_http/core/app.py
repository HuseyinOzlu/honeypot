from flask import Flask, render_template_string
from config.settings import Settings
from core.handlers import honeypot_bp

def create_app():
    app = Flask(__name__)
    
    app.register_blueprint(honeypot_bp)
    
    @app.after_request
    def set_headers(response):
        response.headers["Server"] = Settings.SERVER_BANNER
        return response

    @app.errorhandler(404)
    def not_found(e):
        return render_template_string(f"""
<!DOCTYPE html>
<html>
<head><title>404 Not Found</title></head>
<body>
<h1>Not Found</h1>
<p>The requested URL was not found on this server.</p>
<hr>
<address>{Settings.SERVER_BANNER} Server at localhost Port {Settings.PORT}</address>
</body>
</html>
"""), 404

    return app
