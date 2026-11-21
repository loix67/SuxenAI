# SuxenAI

**Une discussion, plusieurs IA. Sans chef obligatoire.**

SuxenAI est un prototype libre et local de conversation collaborative entre plusieurs modèles. Il peut fonctionner sans projet, ou conserver un projet et l'URL d'un dépôt GitHub comme référence. **Cette version ne lit ni ne modifie encore le contenu d'un dépôt GitHub.**

## Démarrage

Python 3.10+ requis, aucune dépendance Python externe.

```bash
python3 server.py
```

Ouvrir **http://127.0.0.1:8765**.

Pour les modèles réels, fournir une clé API dans les variables d'environnement `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, `MISTRAL_API_KEY`, `GEMINI_API_KEY`, ou installer [Ollama](https://ollama.com) localement puis télécharger un modèle avec `ollama pull llama3.2`. Les abonnements web ChatGPT Plus, Claude Pro et Le Chat ne sont **pas** des clés API et ne sont pas connectés.

Pour essayer sans compte : ajouter un agent avec le fournisseur `demo`. Ses messages sont **simulés**, avec une mention visible.

## Fonctionnalités v0.2

- Une **conversation collective** avec plusieurs modèles, tours de parole successifs et contexte partagé.
- Trois modes : **libre** (défaut), **ciblé** (avec `@Nom`), **coordonné** (coordinateur choisi facultativement).
- Participants personnalisables : fournisseur, modèle, nom, spécialité optionnelle et activation/désactivation.
- Projets, instructions communes, historique SQLite, branches de discussion.
- Export JSON d'une conversation et de son équipe ; interface sombre responsive.
- Maximum six participants et trois tours par action pour limiter les boucles et coûts.

**Limites à connaître :** les appels multi-IA sont séquentiels et non parallèles ; il n'y a pas encore d'import de documents, de gestion de fichiers Git, d'édition de code ou de tests automatiques d'un projet. Les fournisseurs peuvent facturer leurs appels API. Les modèles sélectionnés dans le code sont des valeurs par défaut à adapter selon les offres disponibles.

## Sécurité et confidentialité

Le serveur n'écoute que sur `127.0.0.1`, sans compte utilisateur. N'exposez pas ce serveur sur Internet. Les messages et instructions de projet sont transmis aux fournisseurs choisis pour générer leurs réponses. Les clés API restent dans l'environnement du serveur. Ne chargez pas de données sensibles sans contrôler les fournisseurs utilisés.


## v0.3 : connecter des fichiers GitHub (lecture seule)

Dans **Projet → Configurer**, saisir une URL du type `https://github.com/owner/repo`.
Puis, dans **Fichiers du projet**, cliquer sur **↻**. Le navigateur de fichiers présente les fichiers texte du dépôt (branche par défaut). Cliquer sur **Voir** pour examiner le contenu, puis **Partager avec les IA** pour l'inclure dans le contexte commun. Le bouton **Retirer** permet de supprimer cette copie du contexte.

**Dépôts privés :** définir `GITHUB_TOKEN` dans l'environnement du serveur avant de le démarrer, avec accès en lecture au contenu des dépôts concernés. Ne jamais mettre le token dans l'interface, le code ou un fichier versionné. Exemple macOS :

```bash
export GITHUB_TOKEN="<token-personnel-a-creer>"
python3 server.py
```

Limites : 8 fichiers par projet, 80 Ko par fichier, 120 Ko au total. Les fichiers sensibles courants comme `.env`, les clés privées et certificats sont exclus. La sélection est enregistrée localement en SQLite et partagée avec **tous** les fournisseurs IA activés sur le projet lors des prochains appels. Ne pas partager de secrets ou de données confidentielles. Les fichiers ne sont **pas synchronisés automatiquement** après une modification du dépôt ; il faut les sélectionner de nouveau. L'API GitHub peut appliquer ses quotas.

Cette v0.3 ne permet **ni de modifier le dépôt, ni de committer, ni d'exécuter du code**. Elle constitue l'étape de lecture du projet avant le développement des outils d'édition sécurisée.

## Tests

```bash
python3 -m unittest discover -s tests -v
```

## Licence

MIT. Voir `LICENSE`.
