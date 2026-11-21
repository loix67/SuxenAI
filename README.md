# SuxenAI

**Plusieurs IA, une seule discussion.**
SuxenAI réunit ChatGPT, Claude, Gemini, Mistral et des modèles locaux (Ollama) dans un même espace de travail : vous posez une question une fois, les IA répondent, se lisent et se complètent. Tout reste sur votre ordinateur.

Logiciel libre (licence MIT), gratuit, en français, pour macOS et Windows.

---

## Sommaire

1. [Ce que fait SuxenAI](#ce-que-fait-suxenai)
2. [Installation](#installation)
3. [Premier lancement](#premier-lancement)
4. [Les trois modes : Web, API, Local](#les-trois-modes--web-api-local)
5. [Utiliser l'application](#utiliser-lapplication)
6. [Réglages](#réglages)
7. [Confidentialité et sécurité](#confidentialité-et-sécurité)
8. [Questions fréquentes](#questions-fréquentes)
9. [Pour les développeurs](#pour-les-développeurs)
10. [Licence](#licence)

---

## Ce que fait SuxenAI

- **Une discussion commune** : vous écrivez à « l'équipe », chaque IA active répond dans le même fil et voit les réponses des autres.
- **Vos abonnements, sans clé API** (mode Web) : ChatGPT, Claude, Gemini et Le Chat s'affichent **dans la fenêtre de l'application**, à côté de la discussion. Plus besoin de jongler entre les onglets.
- **Collaboration automatique** (mode API) : avec vos clés API, les IA échangent entre elles, en un ou plusieurs tours.
- **IA locales gratuites** (mode Local) : modèles Ollama exécutés sur votre machine, sans Internet ni crédits.
- **Contexte partagé** : documents (PDF, Word, Excel, texte), notes et fichiers d'un dépôt GitHub, transmis aux IA uniquement si vous le décidez.
- **Atelier de code** : une IA propose une modification, une autre l'audite, vous validez avant l'ouverture d'une pull request brouillon.
- **Import de vos anciennes conversations** ChatGPT et Claude, recherche dans tous vos projets, sauvegarde complète.

---

## Installation

### Application de bureau (recommandé)

C'est la version qui affiche les sites des IA directement dans la fenêtre.

1. Ouvrez la page [Releases](https://github.com/loix67/SuxenAI/releases) (ou l'onglet **Actions** → dernière exécution réussie de **Desktop Chromium** → *Artifacts*).
2. Téléchargez l'archive correspondant à votre ordinateur :

   | Fichier | Ordinateur |
   |---|---|
   | `SuxenAI-Mac-Apple-Silicon.zip` | Mac M1, M2, M3, M4… |
   | `SuxenAI-Mac-Intel.zip` | Mac Intel |
   | `SuxenAI-Windows-x64.zip` | Windows 10 / 11 (64 bits) |

3. Décompressez l'archive.
   - **Mac** : glissez `SuxenAI.app` dans **Applications**.
   - **Windows** : placez le dossier où vous voulez et lancez `SuxenAI.exe`.

Aucun Python ni Node.js n'est nécessaire : tout est inclus.

> **Premier lancement sur Mac.** L'application n'est pas signée par Apple (projet gratuit, sans compte développeur payant), macOS la bloque donc la première fois :
> 1. Double-cliquez sur `SuxenAI.app`, puis fermez l'alerte.
> 2. Ouvrez **Réglages Système → Confidentialité et sécurité**, descendez jusqu'au message concernant SuxenAI et cliquez **Ouvrir quand même**.
>
> Si macOS indique que l'app est « endommagée », lancez dans le Terminal :
> ```bash
> xattr -dr com.apple.quarantine /Applications/SuxenAI.app
> ```
>
> **Sur Windows**, SmartScreen peut afficher « Windows a protégé votre ordinateur » : cliquez **Informations complémentaires → Exécuter quand même**.

### Version navigateur (sans installation)

Pour essayer rapidement, ou sur Linux. Les sites des IA s'ouvrent alors dans des onglets de votre navigateur, pas dans la fenêtre.

Prérequis : [Python 3.10 ou plus récent](https://www.python.org/downloads/).

```bash
git clone https://github.com/loix67/SuxenAI.git
cd SuxenAI
python3 server.py
```

Puis ouvrez **http://127.0.0.1:8765**. Pour utiliser un autre port : `SUXENAI_PORT=8766 python3 server.py`.
Sur Mac, vous pouvez aussi double-cliquer sur `SuxenAI.app` à la racine du dépôt : il démarre le serveur et ouvre le navigateur.

La lecture des PDF nécessite `pypdf` (`python3 -m pip install pypdf`). Tout le reste fonctionne sans dépendance.

---

## Premier lancement

Au démarrage, SuxenAI crée :

- un projet **« Premier projet »** avec une discussion **« Discussion collective »** ;
- une équipe d'exemple (GPT, Claude, Mistral) ;
- le mode **Web**, qui ne fait **aucun appel payant**.

Vous pouvez commencer tout de suite en mode Web avec vos abonnements, sans rien configurer.

---

## Les trois modes : Web, API, Local

Le sélecteur **Web · API · Local**, en haut au centre, s'applique au projet en cours. Une ligne sous la barre rappelle le mode actif.

| | **Web** | **API** | **Local** |
|---|---|---|---|
| Utilise | Vos abonnements (ChatGPT Plus, Claude Pro…) sur les sites officiels | Vos clés API | Modèles Ollama sur votre machine |
| Coût | Rien de plus que vos abonnements | Facturé à l'usage par chaque fournisseur | Gratuit |
| Les IA se répondent automatiquement | Non : copier-coller manuel | **Oui** | **Oui** |
| Configuration | Aucune | Clés dans **Réglages → Connexions IA** | Installer [Ollama](https://ollama.com) |

> Un abonnement ChatGPT Plus ou Claude Pro **ne fournit pas** de clé API : ce sont deux offres différentes. Le passage en mode API demande une confirmation.

### Mode Web : vos abonnements, dans la fenêtre

1. Choisissez **Web**.
2. *(Application de bureau)* Choisissez **Panneau 1** ou **Panneau 2**, puis cliquez sur **ChatGPT**, **Claude**, **Gemini** ou **Le Chat**. Le site officiel s'ouvre à droite de l'application ; deux IA peuvent être affichées côte à côte. Connectez-vous normalement : la session est conservée pour les fois suivantes.
3. **Préparer la demande** : écrivez votre question, cochez si besoin *Inclure les 6 derniers messages* pour donner le contexte, cliquez **Aperçu** puis **Copier**, et collez dans le site de l'IA.
4. **Rapporter la réponse** : copiez la réponse de l'IA, choisissez le service utilisé, collez-la et cliquez **Ajouter à la discussion**.

Toutes les réponses sont ainsi réunies dans la même discussion : vous pouvez par exemple transmettre la réponse de ChatGPT à Claude pour qu'il la critique.

Si un site refuse la connexion intégrée (c'est parfois le cas de « Se connecter avec Google »), utilisez le bouton **Navigateur externe**. SuxenAI ne lit jamais le contenu de ces pages, ni vos cookies, ni vos mots de passe : le transfert reste volontairement manuel.

### Mode API : collaboration automatique

1. Ouvrez **⚙ Réglages → Connexions IA**.
2. Pour chaque fournisseur, cliquez **Obtenir une clé ↗**, créez la clé sur son site, collez-la, puis **Enregistrer** et **Tester**.
3. Choisissez **API** et écrivez dans la discussion.

| Fournisseur | Où créer la clé |
|---|---|
| OpenAI | platform.openai.com/api-keys |
| Anthropic (Claude) | console.anthropic.com/settings/keys |
| Mistral | console.mistral.ai/api-keys |
| Google Gemini | aistudio.google.com/apikey |

Une IA sans clé apparaît grisée avec la mention **clé requise** ; elle est ignorée.

### Mode Local : gratuit et hors ligne

1. Installez et démarrez [Ollama](https://ollama.com).
2. **⚙ Réglages → Modèles locaux** : saisissez un nom de modèle (par exemple `llama3.2`, `mistral` ou `qwen2.5`), cliquez **Télécharger** (plusieurs Go), puis **Ajouter à la discussion**.
3. Choisissez **Local**. Aucun appel ne part vers un service en ligne.

---

## Utiliser l'application

L'écran comporte trois zones.

### À gauche : projets et discussions

- **＋ Nouvelle discussion** crée un fil dans le projet en cours.
- **Rechercher…** : tapez un mot puis Entrée. Cochez **Tous les projets** pour chercher partout.
- **Projets** (＋ pour en créer un) : chaque projet a ses discussions, ses consignes, son équipe et son mode.
- Menu **⋯** en bas : importer des conversations, importer ou exporter un projet, exporter la discussion, sauvegarde complète.

### Au centre : la discussion

- Écrivez à l'équipe puis **Envoyer** (ou Entrée ; Maj+Entrée pour aller à la ligne).
- **@Nom** s'adresse à une IA précise, par exemple : `@Claude peux-tu vérifier ce raisonnement ?`
- **↻ Relancer** fait faire un tour de plus aux IA, pour qu'elles réagissent aux réponses des autres.
- En haut à droite : **⑂** duplique la discussion (pour explorer une autre piste sans perdre l'originale) et **⛶** active le mode concentration (masque les panneaux latéraux).

### À droite : équipe et contexte

**Équipe IA** (modes API et Local)
- **＋** ajoute une IA : nom, fournisseur, modèle (facultatif), rôle (facultatif : « Audit », « Conception »…).
- **●** met une IA en pause, **✎** la modifie.
- **Libre / Ciblée / Coordonnée** :
  - *Libre* : toutes les IA actives répondent ;
  - *Ciblée* : seules les IA mentionnées avec `@Nom` répondent ;
  - *Coordonnée* : un coordinateur répond d'abord, puis les autres.
- **Tours** : nombre d'échanges successifs entre les IA (1 à 3).

**Contexte** (repliable)
- **Importer un document** : PDF, Word (.docx), Excel (.xlsx), texte, Markdown, CSV ou JSON, 6 Mo maximum. Le texte est extrait sur votre machine.
- **＋** ajoute une note ou une décision à retenir.
- Chaque élément est **Privé** par défaut ; cliquez dessus pour le passer en **Partagé** et le transmettre aux IA.
- **Dépôt GitHub** : après avoir indiqué l'URL d'un dépôt dans *Réglages → Projet*, **↻** liste ses fichiers ; **Voir** puis **Partager avec les IA** ajoute un fichier au contexte (lecture seule, 8 fichiers et 120 Ko au maximum).

**Atelier de code** (visible si un dépôt est associé, hors mode Web)
1. **＋ Un fichier** ou **＋ Plusieurs fichiers** (jusqu'à 6) : choisissez l'IA développeuse et les chemins, puis décrivez le changement.
2. Ouvrez la proposition : différences ligne à ligne et contrôle de syntaxe Python/JSON.
3. **Auditer** avec une autre IA. Un avis favorable est obligatoire pour publier.
4. **Créer une PR brouillon** : une nouvelle branche `suxenai/…` est créée, sans jamais de fusion automatique. Le bouton *État des tests GitHub* affiche le résultat de la CI du dépôt.

L'atelier nécessite un jeton GitHub (*Réglages → Connexions IA → GitHub*) avec les permissions **Contents** et **Pull requests** en lecture et écriture sur le dépôt concerné.

### Importer vos anciennes conversations

Menu **⋯ → Importer des conversations** :

1. Exportez vos données depuis ChatGPT (*Paramètres → Contrôles des données → Exporter* ; l'archive ZIP est acceptée telle quelle) ou depuis Claude (export JSON).
2. Sélectionnez le fichier (8 Mo maximum) : un aperçu liste les conversations ; rien n'est importé sans votre sélection.
3. Cochez celles à garder (100 maximum par import) puis **Importer la sélection**. Chacune devient une discussion du projet.

Seul le texte est importé (ni images, ni pièces jointes). Les exports Gemini et Mistral ne sont pas encore pris en charge.

---

## Réglages

Bouton **⚙ Réglages** en haut à droite :

| Section | Contenu |
|---|---|
| **Projet** | Nom, URL du dépôt GitHub, consignes communes envoyées à toutes les IA (par exemple « Réponds en français, sois concis »). |
| **Connexions IA** | Clés API OpenAI, Anthropic, Mistral et Gemini, jeton GitHub, détection d'Ollama. |
| **Modèles locaux** | Liste, téléchargement et ajout des modèles Ollama. |
| **Mémoire** | Si elle est activée, retrouve jusqu'à 5 extraits pertinents des autres discussions du projet et les transmet aux IA. |
| **Consommation** | Appels et tokens par fournisseur et par modèle, coût estimé selon les tarifs que vous saisissez (ce n'est pas une facture). |
| **Sauvegarde** | Télécharger une sauvegarde complète (JSON) ou la restaurer sous forme de copies, sans rien écraser. Les clés API n'y figurent jamais. |
| **À propos** | Version et vérification des mises à jour sur GitHub. |

---

## Confidentialité et sécurité

- **Tout est local.** Projets, discussions et documents sont stockés dans une base SQLite sur votre ordinateur :
  - Mac : `~/Library/Application Support/SuxenAI`
  - Windows : `%APPDATA%\SuxenAI`
  - version navigateur lancée avec `python3 server.py` : dossier `data/` du dépôt (ou celui indiqué par `SUXENAI_DATA_DIR`).
- **Clés API** : stockées dans le **trousseau macOS** ou le **Gestionnaire d'identification Windows**, jamais dans la base ni dans les sauvegardes, et plus jamais affichées après leur enregistrement.
- **Ce qui part chez les fournisseurs** : en modes API et Local uniquement, les messages de la discussion, les consignes du projet et les éléments que vous avez explicitement **partagés**. Ne partagez pas de secrets.
- **Mode Web** : aucun appel automatique. Les sites des IA tournent dans des profils isolés ; SuxenAI ne lit ni leurs pages, ni leurs cookies, ni vos identifiants.
- **Serveur local** : il n'écoute que sur `127.0.0.1`. Dans l'application de bureau, il exige en plus un jeton aléatoire propre à chaque session. N'exposez jamais la version navigateur sur un réseau.
- **Atelier de code** : le code proposé n'est jamais exécuté sur votre machine, et l'audit par une IA n'est pas une garantie de sécurité.

Chaque service d'IA reste soumis à ses propres conditions d'utilisation et à ses limites d'abonnement.

---

## Questions fréquentes

**Les IA de mes abonnements peuvent-elles se parler automatiquement ?**
Non. Les abonnements web n'offrent pas d'accès programmable, et automatiser leurs sites enfreindrait leurs conditions d'utilisation. Pour une collaboration automatique, utilisez le mode API ou Local.

**Une IA ne répond pas.**
Vérifiez le mode (en Web, les IA de l'équipe sont en pause), la mention *clé requise*, le bouton **●** (pause), et, en mode *Ciblée*, que vous l'avez bien mentionnée avec `@Nom`.

**La connexion Google ne fonctionne pas dans le panneau intégré.**
Google bloque parfois les navigateurs intégrés. Utilisez **Navigateur externe**, ou connectez-vous avec une adresse e-mail et un mot de passe.

**« Address already in use » au lancement de la version navigateur.**
Une autre copie de SuxenAI utilise déjà le port 8765. Fermez-la, ou lancez `SUXENAI_PORT=8766 python3 server.py`.

**Où sont mes données ? Comment tout supprimer ?**
Voir [Confidentialité et sécurité](#confidentialité-et-sécurité). Supprimez le dossier de données, et retirez les clés depuis *Réglages → Connexions IA → Retirer*.

**Les mises à jour sont-elles automatiques ?**
Non. *Réglages → À propos* indique si une nouvelle version existe ; le téléchargement reste manuel.

---

## Pour les développeurs

### Architecture

```
server.py            Serveur HTTP local (Python, bibliothèque standard) et base SQLite
connections.py       Trousseau macOS / Windows, test des connexions
features_v9.py       Modes Web/API/Local, mémoire, consommation, mises à jour
web_workspace.py     Préparation et import manuels du mode Web
repository.py        Lecture d'un dépôt GitHub
workbench.py, batch.py, github_workflow.py   Atelier de code et pull requests
importer.py          Import des exports ChatGPT et Claude
documents_v9.py      Extraction PDF, DOCX, XLSX
backup_v9.py         Sauvegarde et restauration
static/              Interface (HTML, JavaScript sans framework, suxen.css)
desktop/             Application Electron (vues Chromium isolées)
tests/               Tests Python
```

### Lancer les tests

```bash
python3 -m unittest discover -s tests -v
```

### Compiler l'application de bureau

Nécessite Python 3.12+, Node.js 24 et pnpm 11.

```bash
python -m pip install pyinstaller certifi pypdf
python -m PyInstaller --noconfirm --onedir --console --name backend --add-data 'static:static' --distpath desktop-build --workpath desktop-build/work --specpath . server.py
pnpm --dir desktop install --frozen-lockfile
pnpm --dir desktop test
pnpm --dir desktop package
```

Le résultat se trouve dans `desktop-release/`. Le workflow GitHub Actions **Desktop Chromium**, à lancer depuis l'onglet Actions (*Run workflow*), produit les archives Mac Apple Silicon, Mac Intel et Windows x64.

### Variables d'environnement

| Variable | Rôle |
|---|---|
| `SUXENAI_PORT` | Port du serveur (`8765` par défaut) |
| `SUXENAI_DATA_DIR` | Dossier des données |
| `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, `MISTRAL_API_KEY`, `GEMINI_API_KEY`, `GITHUB_TOKEN` | Clés fournies par l'environnement (prioritaires sur le trousseau) |
| `OLLAMA_URL` | Adresse d'Ollama (`http://127.0.0.1:11434` par défaut) |

### Contribuer

Les contributions sont les bienvenues : ouvrez une *issue* pour discuter d'une idée, ou une *pull request* accompagnée de tests. L'historique des versions se trouve dans [CHANGELOG.md](CHANGELOG.md).

---

## Licence

[MIT](LICENSE) : libre d'utilisation, de modification et de redistribution.
