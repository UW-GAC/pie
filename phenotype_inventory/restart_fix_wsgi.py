# Replace the wsgi.py file with this one to trigger a restart
# of the Apache server when necessary.

import os


def application(environ, start_response):
    if environ['mod_wsgi.process_group'] != '':
        import signal
        os.kill(os.getpid(), signal.SIGINT)
    return ["killed"]
