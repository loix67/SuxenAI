"""Read-only GitHub repository explorer for SuxenAI.

Only requests api.github.com over HTTPS; credentials never leave the server.
Repository contents are never fetched from arbitrary user-provided hosts.
"""
import base64
import json
import os
import re
import urllib.error
import urllib.parse
import urllib.request
import connections

MAX_FILE_BYTES = 80_000
MAX_TREE_ITEMS = 1200
MAX_CONTEXT_FILES = 8
MAX_CONTEXT_BYTES = 120_000
REPO_PATTERN = re.compile(
    r"^(?:https://github\.com/)?(?P<owner>[A-Za-z0-9][A-Za-z0-9-]{0,38})/"
    r"(?P<repo>[A-Za-z0-9_.-]{1,100})(?:\.git)?/?$"
)
SECRET_NAMES = re.compile(r"(^|/)(\.env(?:\..*)?|id_rsa|id_ed25519|.*\.pem|.*\.key|.*credentials.*|.*secrets.*|.*\.p12)$", re.I)


def parse_repo(value):
    value = (value or "").strip().removesuffix(".git").rstrip("/")
    match = REPO_PATTERN.fullmatch(value)
    if not match:
        raise ValueError("Dépôt GitHub invalide. Format attendu : https://github.com/compte/depot")
    owner, repo = match.group("owner", "repo")
    if repo in (".", ".."):
        raise ValueError("Nom de dépôt invalide")
    return owner, repo


def validate_path(path):
    if not isinstance(path, str) or not path or len(path) > 400:
        raise ValueError("Chemin de fichier invalide")
    parts = path.split("/")
    if any(p in ("", ".", "..") for p in parts) or "\\" in path or any(ord(c)<32 for c in path):
        raise ValueError("Chemin de fichier non autorisé")
    if SECRET_NAMES.search(path):
        raise ValueError("Fichier sensible bloqué par défaut")
    return path


def new_file_snapshot(repo_url,path):
    path=validate_path(path)
    if path.startswith(('.github/','.git/')):raise ValueError('Chemin réservé')
    info=repository_info(repo_url)
    tree=github_get('/repos/'+info['name']+'/git/trees/'+urllib.parse.quote(info['branch'],safe='')+'?recursive=1')
    ensure_new_path(tree,path)
    return {'path':path,'content':'','sha':'','branch':info['branch'],'bytes':0}


def ensure_new_path(tree,path):
    if tree.get('truncated'):raise ValueError('Arborescence tronquée : création refusée')
    for entry in tree.get('tree',[]):
        existing=entry.get('path','')
        if existing==path or existing.startswith(path+'/') or (path.startswith(existing+'/') and entry.get('type')!='tree'):
            raise ValueError('Chemin déjà présent ou incompatible : '+path)


def github_get(route):
    token = connections.key('github')
    url = "https://api.github.com" + route
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "SuxenAI-local/0.3",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    if token:
        headers["Authorization"] = "Bearer " + token
    request = urllib.request.Request(url, headers=headers)
    try:
        with connections.opener().open(request, timeout=20) as resp:
            if int(resp.headers.get("Content-Length", 0)) > 2_500_000:
                raise ValueError("Réponse GitHub trop volumineuse")
            return json.load(resp)
    except urllib.error.HTTPError as e:
        if e.code == 404:
            raise ValueError("Dépôt ou fichier introuvable ou inaccessible. Pour un dépôt privé, définir GITHUB_TOKEN.")
        if e.code in (401, 403):
            raise ValueError("Accès GitHub refusé ou quota dépassé : vérifier GITHUB_TOKEN et ses permissions.")
        raise ValueError("GitHub HTTP " + str(e.code))
    except urllib.error.URLError:
        raise ValueError("Impossible de contacter l'API GitHub")


def repository_info(repo_url):
    owner, repo = parse_repo(repo_url)
    info = github_get("/repos/" + urllib.parse.quote(owner) + "/" + urllib.parse.quote(repo))
    return {"name": info["full_name"], "branch": info["default_branch"], "private": info["private"]}


def repository_tree(repo_url):
    info = repository_info(repo_url)
    name, branch = info["name"], info["branch"]
    route = "/repos/" + name + "/git/trees/" + urllib.parse.quote(branch, safe="") + "?recursive=1"
    data = github_get(route)
    if data.get("truncated"):
        raise ValueError("Arborescence GitHub tronquée. Dépôt trop volumineux pour ce prototype.")
    files = []
    for entry in data.get("tree", []):
        path = entry.get("path", "")
        if entry.get("type") != "blob" or entry.get("size", MAX_FILE_BYTES + 1) > MAX_FILE_BYTES:
            continue
        if SECRET_NAMES.search(path):
            continue
        try:
            validate_path(path)
        except ValueError:
            continue
        files.append({"path": path, "size": entry.get("size", 0), "sha": entry.get("sha", "")})
        if len(files) >= MAX_TREE_ITEMS:
            break
    return {"repository": info, "files": files}


def repository_file(repo_url, path):
    owner, repo = parse_repo(repo_url)
    path = validate_path(path)
    info = repository_info(repo_url)
    encoded = "/".join(urllib.parse.quote(x, safe="") for x in path.split("/"))
    route = "/repos/" + urllib.parse.quote(owner) + "/" + urllib.parse.quote(repo) + "/contents/" + encoded
    route += "?ref=" + urllib.parse.quote(info["branch"], safe="")
    data = github_get(route)
    if not isinstance(data, dict) or data.get("type") != "file":
        raise ValueError("Ce chemin n'est pas un fichier")
    if data.get("size", MAX_FILE_BYTES + 1) > MAX_FILE_BYTES:
        raise ValueError("Fichier trop volumineux (80 Ko maximum)")
    if data.get("encoding") != "base64":
        raise ValueError("Encodage de fichier non pris en charge")
    raw = base64.b64decode(data.get("content", ""), validate=False)
    if len(raw) > MAX_FILE_BYTES or b"\x00" in raw:
        raise ValueError("Fichier binaire ou trop volumineux")
    try:
        content = raw.decode("utf-8")
    except UnicodeDecodeError:
        raise ValueError("Seuls les fichiers texte UTF-8 sont pris en charge")
    return {"path": path, "content": content, "sha": data["sha"], "branch": info["branch"], "bytes": len(raw)}
