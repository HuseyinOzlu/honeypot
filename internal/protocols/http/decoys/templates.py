# HTTP Decoy Templates for catching automated scanners and targeted exploit attempts

WORDPRESS_LOGIN_HTML = """<!DOCTYPE html>
<html lang="en-US">
<head>
    <meta http-equiv="Content-Type" content="text/html; charset=UTF-8" />
    <title>Log In &lsaquo; Enterprise Portal &#8212; WordPress</title>
    <link rel='stylesheet' id='dashicons-css' href='/wp-includes/css/dashicons.min.css' media='all' />
    <link rel='stylesheet' id='buttons-css' href='/wp-includes/css/buttons.min.css' media='all' />
    <link rel='stylesheet' id='forms-css' href='/wp-admin/css/forms.min.css' media='all' />
    <link rel='stylesheet' id='l10n-css' href='/wp-admin/css/l10n.min.css' media='all' />
    <link rel='stylesheet' id='login-css' href='/wp-admin/css/login.min.css' media='all' />
</head>
<body class="login no-js login-action-login wp-core-ui  locale-en-us">
<div id="login">
    <h1><a href="https://wordpress.org/">Powered by WordPress</a></h1>
    <form name="loginform" id="loginform" action="/wp-login.php" method="post">
        <p>
            <label for="user_login">Username or Email Address</label>
            <input type="text" name="log" id="user_login" class="input" value="" size="20" autocapitalize="off" />
        </p>
        <p>
            <label for="user_pass">Password</label>
            <input type="password" name="pwd" id="user_pass" class="input" value="" size="20" />
        </p>
        <p class="submit">
            <input type="submit" name="wp-submit" id="wp-submit" class="button button-primary button-large" value="Log In" />
        </p>
    </form>
</div>
</body>
</html>"""

PHPMYADMIN_LOGIN_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="utf-8">
    <title>phpMyAdmin</title>
    <style>body{font-family:sans-serif;background:#f3f3f3;padding:50px;text-align:center;} .box{background:#fff;padding:30px;border-radius:5px;display:inline-block;box-shadow:0 0 10px rgba(0,0,0,0.1);}</style>
</head>
<body>
<div class="box">
    <img src="https://www.phpmyadmin.net/static/images/logo.png" alt="phpMyAdmin" height="50"><br><br>
    <form method="post" action="index.php">
        <input type="text" name="pma_username" placeholder="Username" required><br><br>
        <input type="password" name="pma_password" placeholder="Password" required><br><br>
        <input type="submit" value="Go">
    </form>
</div>
</body>
</html>"""

GIT_CONFIG_EXPOSED = """[core]
	repositoryformatversion = 0
	filemode = true
	bare = false
	logallrefupdates = true
[remote "origin"]
	url = https://github.com/enterprise-internal/infrastructure-secrets.git
	fetch = +refs/heads/*:refs/remotes/origin/*
[branch "main"]
	remote = origin
	merge = refs/heads/main
[user]
	name = DevOps Admin
	email = admin@enterprise-portal.internal
"""
