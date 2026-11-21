# Historique des versions

## 1.2.0 — Interface simplifiée

- Interface réorganisée : barre latérale réduite à l'essentiel (nouvelle discussion, recherche, projets, discussions), actions rares dans un menu **⋯**.
- Sélecteur **Web · API · Local** au centre de la barre du haut, un seul bouton **Réglages** regroupant projet, connexions, modèles locaux, mémoire, consommation, sauvegarde et informations.
- Panneau de droite en trois blocs : Équipe IA, Contexte (repliable), Atelier de code (visible seulement avec un dépôt, hors mode Web).
- Thème unique « Graphite » (`static/suxen.css`) remplaçant quatre feuilles de style superposées.
- Mode **Web** par défaut pour tout nouveau projet : aucun appel facturable sans choix explicite.
- Correction : la fenêtre pouvait rester vide au tout premier lancement.

## 1.1.0 — Application de bureau Chromium

- Application Electron pour Mac (Apple Silicon, Intel) et Windows x64.
- Mode Web : ChatGPT, Claude, Gemini et Le Chat affichés dans la fenêtre, un ou deux panneaux côte à côte, profils Chromium isolés et persistants, bouton **Navigateur externe**.
- Serveur local protégé par un jeton aléatoire par session ; pages distantes isolées (sans Node.js ni IPC), téléchargements et permissions bloqués.

## 1.0 — Espace multi-IA

- Trois modes de travail par projet : Web (abonnements, transfert manuel), API (automatisation avec des clés), Local (Ollama).
- Mode Web : préparation d'une demande avec aperçu, copie explicite, import manuel des réponses avec leur provenance.
- Le mode Web bloque tout appel automatique côté serveur ; le passage en mode API demande une confirmation.
- 1.0.1 : palette Graphite (anthracite, accent cyan, touches violettes).

## 0.9 — Outils

- Mode local gratuit par projet, désactivation des IA non connectées, messages d'erreur de quota et de clé plus clairs.
- Modèles locaux : détection d'Ollama, liste, téléchargement et ajout à la discussion.
- Consommation : appels et tokens par fournisseur, estimation en USD selon les tarifs saisis.
- Documents : extraction locale PDF, DOCX, XLSX et texte. Mémoire intelligente optionnelle, recherche globale, mode concentration.
- Sauvegarde et restauration JSON complètes (sans les clés API). Vérification des nouvelles versions sur GitHub.

## 0.8 — Connexions simplifiées

- Assistant de connexion des clés OpenAI, Anthropic, Mistral, Gemini et GitHub, stockées dans le trousseau macOS.
- Lanceur macOS autonome avec Python intégré.

## 0.7 — Atelier coordonné et espace local

- Import/export JSON d'un projet, documents et mémoire partagés sur activation.
- Lots de 1 à 6 fichiers, audit indépendant, nouvelle proposition après audit négatif.
- Diff unifié et vérification statique Python/JSON sans exécution ; publication en une PR brouillon.

## 0.6 — Import de conversations

- Import sélectif des exports ChatGPT (JSON ou ZIP) et Claude, avec aperçu local.
- Recherche textuelle dans les conversations d'un projet.

## 0.5 — Atelier de code

- Proposition de modification d'un fichier par une IA, audit par une autre, publication manuelle en PR brouillon, état de la CI.

## Versions antérieures

- Discussion collective multi-IA, modes libre, ciblé et coordonné, projets, branches de discussion, explorateur GitHub en lecture seule.
