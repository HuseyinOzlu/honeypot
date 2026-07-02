from flask import Blueprint, request, render_template_string, Response
from services.log_service import LogService

honeypot_bp = Blueprint('honeypot', __name__)
logger = LogService()

@honeypot_bp.before_request
def log_incoming_request():
    ip = request.remote_addr
    method = request.method
    path = request.path
    params = request.args
    headers = request.headers
    
    body = ""
    if request.form:
        body = dict(request.form)
    elif request.json:
        body = request.json
    else:
        body = request.get_data(as_text=True)
        
    logger.log_request(ip, method, path, params, headers, body)

@honeypot_bp.route('/', methods=['GET', 'POST'])
def index():
    return render_template_string("""
<!DOCTYPE html>
<html>
<head>
<title>Apache2 Ubuntu Default Page: It works</title>
<style>
body { font-family: sans-serif; background-color: #f0f0f0; margin: 40px; }
.card { background: white; padding: 20px; border: 1px solid #ccc; border-top: 5px solid #2e7d32; }
h1 { color: #2e7d32; }
</style>
</head>
<body>
<div class="card">
<h1>Apache2 Ubuntu Default Page</h1>
<h3>It works!</h3>
<p>This is the default welcome page used to test the correct operation of the Apache2 server after installation on Ubuntu systems.</p>
</div>
</body>
</html>
""")

@honeypot_bp.route('/robots.txt', methods=['GET'])
def robots():
    content = """User-agent: *
Disallow: /admin
Disallow: /wp-login.php
Disallow: /phpmyadmin
Disallow: /.git
"""
    return Response(content, mimetype="text/plain")

@honeypot_bp.route('/.git/config', methods=['GET'])
def git_config():
    content = """[core]
	repositoryformatversion = 0
	filemode = true
	bare = false
	logallrefupdates = true
[remote "origin"]
	url = https://github.com/admin/secrets-vault.git
	fetch = +refs/heads/*:refs/remotes/origin/*
[branch "main"]
	remote = origin
	merge = refs/heads/main
"""
    return Response(content, mimetype="text/plain")

@honeypot_bp.route('/wp-login.php', methods=['GET', 'POST'])
def wp_login():
    if request.method == 'POST':
        return render_template_string("""
<!DOCTYPE html>
<html>
<head><title>Log In ‹ Test Site — WordPress</title></head>
<body style="font-family: sans-serif; background: #f1f1f1; display: flex; justify-content: center; align-items: center; height: 100vh;">
<div style="background: white; padding: 20px; border: 1px solid #ccc; width: 320px; text-align: center;">
<h3 style="color: #d63638;">ERROR: The username or password you entered is incorrect.</h3>
<p><a href="/wp-login.php">Lost your password?</a></p>
<p><a href="/wp-login.php">← Go to Test Site</a></p>
</div>
</body>
</html>
"""), 401
    return render_template_string("""
<!DOCTYPE html>
<html>
<head>
<title>Log In ‹ Test Site — WordPress</title>
<style>
body { background: #f1f1f1; font-family: sans-serif; }
.login-form { background: white; width: 320px; margin: 100px auto; padding: 26px; border: 1px solid #c3c4c7; box-shadow: 0 1px 3px rgba(0,0,0,.04); }
.input { width: 100%; padding: 10px; margin: 10px 0; border: 1px solid #8c8f94; box-sizing: border-box; }
.submit { background: #2271b1; border-color: #2271b1; color: #fff; padding: 10px 15px; border-style: solid; border-width: 1px; cursor: pointer; }
</style>
</head>
<body>
<div class="login-form">
<form method="POST" action="/wp-login.php">
<label>Username or Email Address</label>
<input type="text" name="log" class="input" required>
<label>Password</label>
<input type="password" name="pwd" class="input" required>
<input type="submit" value="Log In" class="submit">
</form>
</div>
</body>
</html>
""")

@honeypot_bp.route('/admin', methods=['GET', 'POST'])
@honeypot_bp.route('/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        return render_template_string("<h3 style='color: red;'>Invalid Credentials. Access Denied.</h3><a href='/admin'>Back</a>"), 401
    return render_template_string("""
<!DOCTYPE html>
<html>
<head>
<title>Admin Portal Login</title>
<style>
body { background: #263238; font-family: sans-serif; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; }
.login-box { background: #37474f; padding: 40px; border-radius: 8px; box-shadow: 0 4px 10px rgba(0,0,0,0.3); width: 300px; color: white; }
.input { width: 100%; padding: 10px; margin: 10px 0; border: none; border-radius: 4px; box-sizing: border-box; }
.submit { width: 100%; background: #00bcd4; color: white; border: none; padding: 10px; border-radius: 4px; cursor: pointer; }
</style>
</head>
<body>
<div class="login-box">
<h2>Control Panel</h2>
<form method="POST">
<input type="text" name="username" placeholder="Username" class="input" required>
<input type="password" name="password" placeholder="Password" class="input" required>
<input type="submit" value="Login" class="submit">
</form>
</div>
</body>
</html>
""")

@honeypot_bp.route('/phpmyadmin', methods=['GET', 'POST'])
@honeypot_bp.route('/phpmyadmin/', methods=['GET', 'POST'])
def pma_login():
    if request.method == 'POST':
        return render_template_string("<h3 style='color: red;'>#1045 - Access denied for user.</h3><a href='/phpmyadmin'>Back</a>"), 401
    return render_template_string("""
<!DOCTYPE html>
<html>
<head>
<title>phpMyAdmin</title>
<style>
body { background: #ebebeb; font-family: sans-serif; }
.pma-box { background: white; border: 1px solid #aaa; width: 450px; margin: 100px auto; padding: 20px; border-radius: 5px; }
.input { width: 100%; padding: 8px; margin: 8px 0; box-sizing: border-box; }
.submit { background: #ff9900; border: 1px solid #ff9900; color: white; padding: 8px 16px; cursor: pointer; }
</style>
</head>
<body>
<div class="pma-box">
<h2>Welcome to phpMyAdmin</h2>
<form method="POST">
<label>Username:</label>
<input type="text" name="pma_username" class="input" required>
<label>Password:</label>
<input type="password" name="pma_password" class="input">
<input type="submit" value="Go" class="submit">
</form>
</div>
</body>
</html>
""")
