# SuxenAI v0.6

**Une discussion, plusieurs IA, un espace de travail partagé. Aucun coordinateur obligatoire.**

SuxenAI est un prototype gratuit et local, conçu pour réunir plusieurs modèles d'IA dans une conversation unique. Les participants sont configurables (OpenAI, Anthropic, Mistral, Gemini, Ollama) et peuvent recevoir des rôles facultatifs. L'interface est sombre, sobre, responsive.

## Installation

Python 3.10 minimum. Aucune dépendance Python à installer.

```bash
python3 server.py
```

Ouvrir `http://127.0.0.1:8765`.

Pour utiliser les modèles réels, renseigner les variables d'environnement `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, `MISTRAL_API_KEY`, `GEMINI_API_KEY` ou installer [Ollama](https://ollama.com), puis télécharger un modèle. L'agent `demo` simule des réponses : il ne peut ni coder ni auditer.

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

L'atelier travaille actuellement **un fichier existant par proposition et par PR**. Les changements sont séquentiels, pas parallèles, et les agents n'ont pas de terminal ni d'accès direct au système de fichiers. Il n'y a donc **pas** encore d'exécution automatique de tests locaux ni de modification coordonnée multi-fichiers. L'audit est une analyse par IA, pas une garantie de sécurité.

### GitHub privé

Définir `GITHUB_TOKEN` dans l'environnement du serveur :

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
