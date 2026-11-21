"""Double-click entry point for source or packaged macOS SuxenAI."""
import json
import os
from pathlib import Path
import subprocess
import sys
import urllib.request
import webbrowser


def alert(message):
    if sys.platform == 'darwin':
        subprocess.run(['/usr/bin/osascript','-e','on run argv\n display alert "SuxenAI" message (item 1 of argv)\nend run',message],check=False)
    else:
        print(message,file=sys.stderr)


def main():
    if '--self-test' in sys.argv:
        import tempfile
        with tempfile.TemporaryDirectory() as directory:
            os.environ['SUXENAI_DATA_DIR']=directory
            import server
            server.setup()
            assert server.one('SELECT id FROM projects')
            assert (server.STATIC/'connections.js').is_file()
            assert (server.STATIC/'features.js').is_file()
            assert (server.STATIC/'future.css').is_file()
            assert (server.STATIC/'graphite.css').is_file()
            assert (server.STATIC/'web-workspace.js').is_file()
            import pypdf
            assert (server.STATIC/'index.html').is_file()
            server.connections.MacKeychain()  # load native API only; no keychain access
            server.connections.opener()  # initialize HTTPS trust store
        return
    source=Path(__file__).resolve().parent
    if not getattr(sys,'frozen',False) and (source/'data'/'suxenai.sqlite3').exists():
        data=source/'data'
    else:
        data=Path.home()/'Library'/'Application Support'/'SuxenAI'
    os.environ.setdefault('SUXENAI_DATA_DIR',str(data))
    import server
    url=f'http://127.0.0.1:{server.PORT}'
    try:
        with urllib.request.urlopen(url+'/api/health',timeout=1) as response:
            running=json.load(response)
        if running=={'app':'SuxenAI','version':server.v9.VERSION}:
            webbrowser.open(url);return
    except (OSError,ValueError):
        pass
    try:
        httpd=server.ThreadingHTTPServer((server.HOST,server.PORT),server.Handler)
    except OSError:
        alert('Fermez l’ancienne version de SuxenAI ou l’application utilisant le port 8765, puis réessayez.');return
    try:
        server.setup()
        webbrowser.open(url)
        httpd.serve_forever()
    except Exception:
        alert('Impossible de démarrer SuxenAI. Vérifiez les permissions du dossier de données.')
    finally:
        httpd.server_close()


if __name__=='__main__':main()
