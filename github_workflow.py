"""Guarded GitHub changes for SuxenAI: proposals -> explicitly approved branch -> draft PR.

No code is executed on the local machine. CI is run only by GitHub if the
destination repository has already configured a workflow.
"""
import base64
import json
import os
import re
import urllib.error
import urllib.parse
import urllib.request
from repository import parse_repo, validate_path, github_get

BRANCH_PATTERN = re.compile(r"^[a-zA-Z0-9][a-zA-Z0-9._/-]{0,120}$")
MAX_PROPOSED_BYTES = 80_000


def safe_branch(value):
    if not isinstance(value, str) or not BRANCH_PATTERN.fullmatch(value):
        raise ValueError("Nom de branche invalide")
    if ".." in value or "//" in value or value.endswith(("/", ".", ".lock")):
        raise ValueError("Nom de branche invalide")
    if value in ("main", "master"):
        raise ValueError("Modification de la branche principale interdite")
    if not value.startswith("suxenai/"):
        raise ValueError("Utiliser une branche suxenai/ distincte")
    return value


def safe_content(content):
    if not isinstance(content, str):
        raise ValueError("Contenu texte attendu")
    if len(content.encode("utf-8")) > MAX_PROPOSED_BYTES or "\x00" in content:
        raise ValueError("Taille ou contenu non autorisé (80 Ko maximum)")
    return content


def encode_path(path):
    validate_path(path)
    return "/".join(urllib.parse.quote(part, safe="") for part in path.split("/"))


def github_write(method, route, payload):
    token = os.getenv("GITHUB_TOKEN", "").strip()
    if not token:
        raise ValueError("GITHUB_TOKEN requis avec permission Contents: Read and write; Pull requests: Read and write")
    request = urllib.request.Request(
        "https://api.github.com" + route,
        data=json.dumps(payload).encode("utf-8"),
        method=method,
        headers={
            "Authorization": "Bearer " + token,
            "Accept": "application/vnd.github+json",
            "Content-Type": "application/json",
            "User-Agent": "SuxenAI-local/0.5",
            "X-GitHub-Api-Version": "2022-11-28",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=30) as r:
            return json.load(r)
    except urllib.error.HTTPError as e:
        # Deliberately avoid returning response bodies (could include sensitive data).
        raise ValueError("GitHub a refusé la modification (HTTP %s)" % e.code)
    except urllib.error.URLError:
        raise ValueError("Connexion à GitHub impossible")


def publish(repo_url, path, content, expected_sha, branch, title, description):
    """Explicitly requested by a user. One file per branch and draft PR.

    expected_sha is obtained when the proposal is created. It is compared
    against the default branch, to prevent accidental overwriting of changes.
    """
    owner, repo = parse_repo(repo_url)
    full = owner + "/" + repo
    path, content, branch = validate_path(path), safe_content(content), safe_branch(branch)
    if not content.strip():
        raise ValueError("Contenu vide interdit")
    info = github_get("/repos/" + full)
    default = info["default_branch"]
    ref = github_get("/repos/" + full + "/git/ref/heads/" + urllib.parse.quote(default, safe=""))
    head_sha = ref["object"]["sha"]

    route = "/repos/" + full + "/contents/" + encode_path(path) + "?ref=" + urllib.parse.quote(default, safe="")
    current_sha = ""
    try:
        current = github_get(route)
        current_sha = current.get("sha", "")
    except ValueError as e:
        if "introuvable" not in str(e).lower():
            raise
    if current_sha != (expected_sha or ""):
        raise ValueError("Le fichier du dépôt a changé depuis la proposition : actualiser avant publication")

    # Branch must be new: GitHub returns 422 if already present.
    github_write("POST", "/repos/" + full + "/git/refs", {
        "ref": "refs/heads/" + branch, "sha": head_sha
    })
    payload = {
        "message": "feat(suxenai): " + (title.strip() or "AI-reviewed proposal")[:100],
        "content": base64.b64encode(content.encode()).decode(),
        "branch": branch,
    }
    if current_sha:
        payload["sha"] = current_sha
    result = github_write("PUT", "/repos/" + full + "/contents/" + encode_path(path), payload)
    pr = github_write("POST", "/repos/" + full + "/pulls", {
        "title": (title.strip() or "SuxenAI proposed change")[:140],
        "head": branch, "base": default, "draft": True,
        "body": description[:15000],
        "maintainer_can_modify": False,
    })
    return {
        "branch": branch,
        "pr_number": pr["number"],
        "pr_url": pr["html_url"],
        "commit_sha": result["commit"]["sha"],
        "head_sha": result["commit"]["sha"],
        "base": default,
    }


def ci_status(repo_url, pr_number):
    owner, repo = parse_repo(repo_url)
    full = owner + "/" + repo
    if not isinstance(pr_number, int) or pr_number < 1:
        raise ValueError("Numéro de pull request invalide")
    pr = github_get("/repos/" + full + "/pulls/" + str(pr_number))
    sha = pr["head"]["sha"]
    checks = github_get("/repos/" + full + "/commits/" + sha + "/check-runs")
    runs = [
        {"name": r["name"], "status": r["status"], "conclusion": r.get("conclusion")}
        for r in checks.get("check_runs", [])[:50]
    ]
    return {"sha": sha, "checks": runs, "has_checks": bool(runs),
            "message": ("Aucun test GitHub Actions détecté : configure un workflow CI dans le projet." if not runs else "")}
