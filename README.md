# SuxenAI v1.0

## Nouveautés v1.0 — espace multi-IA

- Trois modes de travail par projet : **Web** (transfert manuel avec les sites officiels et les abonnements existants), **API** (automatisation avec des clés), **Local** (Ollama, sans crédits API).
- Mode Web : ouverture de ChatGPT, Claude, Gemini et Le Chat dans des onglets indépendants du navigateur système. Préparation locale d'une demande, aperçu avec contexte optionnel, copie explicite et import manuel d'une réponse avec sa provenance. Aucun accès aux sessions, cookies, identifiants ou contenu des onglets par SuxenAI ; aucune injection de prompt automatique. Les fournisseurs conservent leurs propres conditions et limites d'abonnement.
- Le mode Web bloque les appels automatiques aux fournisseurs par le serveur, y compris l'atelier de code. Le passage en mode API demande une confirmation, car les appels peuvent être facturés.
- Nouvelle identité visuelle futuriste : palette nocturne cyan/violet, navigation par modes, espace Web en deux étapes et interface adaptative.

Le mode Web ouvre les sites officiels dans le navigateur plutôt que dans une iframe : certains fournisseurs bloquent les connexions intégrées. Il ne peut pas faire collaborer automatiquement les modèles des abonnements web. Les échanges restent manuels.

## Nouveautés v0.9

- **Outils → Mode IA** : mode local gratuit par projet (bloque les modèles cloud côté serveur), désactivation temporaire des IA non connectées, messages d'erreur quota/clé améliorés.
- **Outils → Modèles locaux** : détection d'Ollama, liste des modèles installés, téléchargement explicite et ajout à la discussion. Ollama doit être installé et démarré séparément.
- **Outils → Consommation** : appels et tokens rapportés par chaque fournisseur, estimations USD sur les tarifs saisis par modèle. Les tarifs inconnus sont signalés, aucun prix inventé.
- **Documents & mémoire** : extraction locale PDF, DOCX, XLSX et texte (6 Mo par fichier, texte limité à 80 Ko, PDF 100 pages maximum). Pas d'OCR, de macros ni de calcul de formules. Les documents restent privés par défaut.
- Mémoire intelligente optionnelle, recherche locale par mots dans les anciennes discussions du même projet, recherche globale et mode concentration.
- Atelier : jusqu'à six fichiers existants ou nouveaux, chemins nouveaux explicitement sélectionnés ; vérification de non-écrasement avant publication, audit et confirmation conservés.
- Sauvegarde JSON de tous les projets, conversations, équipes, documents, historique d'atelier et consommation. Restauration en copies sans écraser les données, propositions restaurées en archive, dépôt à reconnecter et partage/rappel désactivés. Les clés API sont exclues.
- Recherche manuelle ou automatique (sur activation) des nouvelles versions dans GitHub Releases. L'installation automatique reste désactivée tant que les distributions ne sont pas signées/notariées.

Le paquet Mac autonome inclut les dépendances PDF et HTTPS. Pour la version source, installer `pypdf` si la lecture PDF est nécessaire.

## Démarrage simplifié (macOS)

1. Téléchargez et décompressez SuxenAI. Dans le dossier, double-cliquez sur **SuxenAI.app** : le navigateur s'ouvre automatiquement.
2. Au premier lancement, l'assistant **Connexions IA** permet de créer, coller, enregistrer et tester les clés OpenAI, Claude, Mistral, Gemini et GitHub. Ollama est détecté localement sans clé API.
3. Ajoutez ensuite vos modèles dans **Équipe IA**. Vous pouvez rouvrir **Connexions IA** en haut à tout moment, remplacer ou retirer une clé. Les clés sont conservées dans le trousseau macOS, pas dans la base de données ; les variables d'environnement existantes restent prioritaires.

Le lanceur inclus dans le code source nécessite Python 3.10+ déjà installé (aucune commande à saisir). Le workflow **macOS app** construit des archives distinctes Intel et Apple Silicon avec Python intégré, téléchargeables depuis GitHub Actions après compilation. Les builds ne sont pas encore signés/notariés pour une distribution publique. Les données d'un nouveau lancement sont enregistrées dans `~/Library/Application Support/SuxenAI` ; le lanceur source conserve un dossier `data` existant.

La vérification des connexions consulte uniquement les listes de modèles (ou le profil GitHub) : aucun message du projet n'est envoyé. Les clés API peuvent être facturées indépendamment des abonnements web. GitHub : la vérification confirme l'authentification, pas toutes les permissions sur un dépôt donné.

## Nouveautés v0.7

- Import/export JSON d'un projet (discussions et documents/mémoire texte). Le dépôt doit être reconnecté manuellement après import ; les éléments restent privés.
- Documents UTF-8 et mémoire locale partagée sur activation explicite, disponibles dans toutes les discussions du projet.
- Lots coordonnés de 1 à 6 fichiers existants, audit indépendant et nouvelle proposition de correction après audit négatif.
- Diff unifié par fichier et vérification statique Python/JSON sans exécution du code proposé. Les autres formats sont signalés comme non vérifiés.
- Publication explicite en un commit sur une nouvelle branche et PR brouillon, contrôle des versions sources. Aucun merge automatique. Les workflows GitHub existants peuvent exécuter des tests après publication ; aucun test généré n'est lancé sur la machine locale.

Les analyses statiques ne prouvent pas le bon fonctionnement du code. L'exécution isolée de tests générés n'est pas encore prise en charge.

**Une discussion, plusieurs IA, un espace de travail partagé. Aucun coordinateur obligatoire.**

SuxenAI est un prototype gratuit et local, conçu pour réunir plusieurs modèles d'IA dans une conversation unique. Les participants sont configurables (OpenAI, Anthropic, Mistral, Gemini, Ollama) et peuvent recevoir des rôles facultatifs. L'interface est sombre, sobre, responsive.

## Installation

Python 3.10 minimum. Aucune dépendance Python à installer.

```bash
python3 server.py
```

Ouvrir `http://127.0.0.1:8765`.

Pour utiliser les modèles réels, utilisez **Connexions IA** sur macOS. Les variables d'environnement `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, `MISTRAL_API_KEY`, `GEMINI_API_KEY` restent disponibles en mode avancé ou sur les autres systèmes. Pour Ollama, installez [Ollama](https://ollama.com), puis téléchargez un modèle. L'agent `demo` simule des réponses : il ne peut ni coder ni auditer.

**Important :** ChatGPT Plus et Claude Pro ne fournissent pas automatiquement des clés API. Les connexions web aux abonnements ne sont pas intégrées. L'utilisation des API peut occasionner des frais chez chaque fournisseur.

## Collaboration

- Conversation collective, messages adressables avec `@Nom`, rôles libres et coordinateur facultatif
- Modes libre, ciblé, coordonné
- Projets, instructions partagées, branches de conversation, historique SQLite, export JSON
- Explorateur GitHub en lecture seule ; prévisualisation et sélection des fichiers injectés dans le contexte des modèles

### Atelier de code (v0.5)

1. Associer le dépôt dans les paramètres du projet.
2. Cliquer sur `+` dans la section **Atelier de code**.
3. Choisir une IA, le **chemin exact d'un fichier existant**, puis saisir la modification à réaliser.
4. L'IA produit une **proposition de contenu complet**, enregistrée en SQLite, sans écriture sur GitHub.
5. Ouvrir la proposition pour comparer le contenu initial et la nouvelle version.
6. Lancer un **audit par une autre IA** participante. Un verdict positif est obligatoire pour publier.
7. **Confirmer manuellement** la création d'une nouvelle branche `suxenai/...` et d'une **pull request brouillon**. Aucune fusion automatique.
8. Consulter l'état des tests GitHub de la PR. Les tests ne s'exécutent **que si le dépôt cible dispose d'un workflow CI**. Sinon SuxenAI indique explicitement qu'aucun test n'a été détecté.

L'atelier classique travaille sur un fichier par proposition. **Lot multi-fichiers** propose jusqu'à six fichiers existants dans une seule PR. Les agents n'ont pas de terminal ni d'accès direct au système de fichiers. Il n'y a pas d'exécution automatique de code généré sur la machine locale. L'audit est une analyse par IA, pas une garantie de sécurité.

### GitHub privé

Configurez GitHub dans **Connexions IA**. En mode avancé, définir `GITHUB_TOKEN` dans l'environnement du serveur :

```bash
export GITHUB_TOKEN="VOTRE_JETON"
python3 server.py
```

Pour consulter un dépôt privé, le jeton a besoin de la permission **Contents: Read**. Pour publier une PR depuis SuxenAI, il faut **Contents: Read and write** et **Pull requests: Read and write** sur le dépôt cible. Utiliser un jeton à portée minimale, ne jamais le committer et le révoquer s'il fuit.

Les branches `main` et `master` ne peuvent pas être choisies comme branches de publication. Une nouvelle branche dédiée est créée à chaque publication. En cas de panne réseau au milieu d'une publication, une branche orpheline peut subsister : vérifier GitHub avant de réessayer.

### Données transmises aux IA

Les fichiers que vous sélectionnez sont enregistrés localement puis transmis **aux fournisseurs d'IA participants** lors de la génération de réponses. Ils ne doivent pas contenir de secrets ni de données sensibles. Le navigateur de dépôt bloque certains noms de fichiers sensibles, sans prétendre détecter tous les secrets possibles.

L'explorateur accepte jusqu'à 8 fichiers de contexte par projet, 80 Ko par fichier, 120 Ko au total. Ils ne sont pas synchronisés automatiquement après modification du dépôt. Recharger manuellement un fichier pour actualiser son contenu. Les propositions vérifient le SHA initial avant d'écrire, pour empêcher l'écrasement silencieux d'une modification récente.

Le serveur écoute uniquement sur `127.0.0.1` et n'a pas d'authentification. Ne pas l'exposer sur Internet.


## v0.6 : importer ses anciennes conversations

La section **Discussions** propose maintenant **Importer des conversations** et **Rechercher**.

1. Exporte les conversations depuis ChatGPT ou Claude en JSON. Pour ChatGPT, une archive ZIP contenant `conversations.json` est acceptée.
2. Choisis le projet SuxenAI de destination et ouvre **Importer des conversations**.
3. Sélectionne un fichier JSON ou ZIP (8 Mo maximum) : une **prévisualisation locale** affiche titres, origine et nombre de messages.
4. Coche les conversations à conserver (jusqu'à 100 par import), puis valide.
5. Chaque conversation devient un fil distinct rattaché au projet choisi. L'auteur est identifié (Vous, ChatGPT ou Claude), et l'origine de l'import reste stockée en SQLite.
6. Le bouton **Rechercher** permet une recherche textuelle dans les conversations d'un projet.

Les échanges importés ne sont pas transmis aux fournisseurs pendant l'import ou l'aperçu. Ils peuvent toutefois faire partie du contexte envoyé lorsque tu **lances ensuite une nouvelle réponse d'IA dans le fil importé**. Aucune importation n'est automatique.

**Limites :** import textuel uniquement ; pas de transfert des pièces jointes, des images, de la mémoire interne des fournisseurs ou des métadonnées complètes de projets. Les exports sont de formats évolutifs : les formats non reconnus provoquent un message d'erreur, pas un import fictif. L'import d'exports Gemini et Mistral n'est pas encore implémenté. Certains exports volumineux devront être scindés avant import.

## Tests du logiciel SuxenAI

```bash
python3 -m unittest discover -s tests -v
```

Les workflows GitHub Actions du **projet cible** sont distincts des tests de SuxenAI.

## Licence

MIT. Voir `LICENSE`.
