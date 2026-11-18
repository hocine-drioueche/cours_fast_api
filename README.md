# TaskFlow API — Synthèse du cours FastAPI

API REST de gestion de tâches construite pour apprendre **FastAPI**. Le projet couvre les briques essentielles d'un backend moderne : routes CRUD, validation Pydantic, base de données SQLAlchemy, authentification par token Bearer et notifications temps réel via WebSocket.


## Fonctionnalités

- CRUD complet sur les tâches
- **Priorité des tâches** (1 = haute, 2 = moyenne, 3 = basse)
- **Tri automatique par priorité** sur `GET /tasks`
- **Date de création** (`created_at`) en lecture seule
- **Règle métier** : une tâche terminée ne peut pas être supprimée
- **Liste des utilisateurs** via `GET /users`
- Validation Pydantic
- Base de données SQLite avec SQLAlchemy
- Authentification par token Bearer
- Notifications temps réel via WebSocket
- Documentation Swagger automatique (`/docs`)
- Architecture modulaire (routers, dépendances, schémas)


## 1. Stack technique

| Brique | Rôle |
|---|---|
| **FastAPI** | Framework web (routes, injection de dépendances, doc OpenAPI auto) |
| **Uvicorn** | Serveur ASGI |
| **SQLAlchemy** | ORM, base SQLite (`taskflow.db`) |
| **Pydantic** | Schémas de validation / sérialisation |
| **websockets** | Client de test WebSocket (`ws_client.py`) |

Python ≥ 3.10 requis (syntaxe `int | None`).

## 2. Architecture

```
taskflow-api/
├── requirements.txt
├── taskflow.db              # base SQLite (générée au démarrage)
├── ws_client.py             # client WebSocket de démonstration
└── app/
    ├── main.py              # création de l'app, tables, seed, routers
    ├── database.py          # engine, SessionLocal, Base
    ├── models.py            # modèles SQLAlchemy (UserDB, TaskDB)
    ├── schemas.py           # schémas Pydantic (entrées/sorties)
    ├── dependencies.py      # get_session, tokens, get_current_user
    ├── websocket.py         # ConnectionManager (diffusion)
    └── routers/
        ├── auth.py          # POST /login
        ├── tasks.py         # CRUD /tasks
        ├── users.py         # GET /users
        └── ws.py            # WebSocket /ws/tasks
```

Principe : **séparation des responsabilités** — modèles de données (DB), schémas (API), dépendances (infra), routers (endpoints).

## 3. Concepts clés vus dans le cours

### 3.1 Base de données (`database.py`, `models.py`)
- `create_engine` avec `check_same_thread=False` (nécessaire pour SQLite avec FastAPI).
- `sessionmaker` → une session par requête.
- `declarative_base()` → classe mère des modèles.
- Deux tables : `users` (id, username) et `tasks` (id, title, completed, user_id → FK vers users, nullable).
- `Base.metadata.create_all()` crée les tables au démarrage ; `seed_data()` insère `alice` et `bob` si la table est vide.

### 3.2 Schémas Pydantic (`schemas.py`)
Un schéma par usage :
- `TaskCreate` : corps du POST (`completed` défaut `False`, `user_id` optionnel)
- `TaskUpdate` : tous les champs optionnels (mise à jour partielle)
- `Task` : réponse (utilisée en `response_model`)
- `LoginData`, `User`

Intérêt : validation automatique (erreur 422), filtrage de la réponse, documentation Swagger.

### 3.3 Injection de dépendances (`dependencies.py`)
- `get_session` : générateur avec `yield` → ouvre la session, la ferme dans `finally`.
- `get_current_user` : extrait le token via `HTTPBearer`, le résout en utilisateur, sinon renvoie **401**.
- Usage : `db: Session = Depends(get_session)`.

### 3.4 Authentification (`routers/auth.py`)
1. `POST /login` avec `{"username": "alice"}`
2. Le serveur génère un token (`secrets.token_hex(16)`) stocké dans un dict en mémoire `token → user_id`.
3. Le client envoie `Authorization: Bearer <token>` sur les routes protégées.

### 3.5 CRUD des tâches (`routers/tasks.py`)

| Méthode | Route | Auth | Description |
|---|---|---|---|
| GET | `/tasks` | non | Liste, filtres `?completed=` et `?user_id=` |
| GET | `/tasks/{id}` | non | Détail (404 si absent) |
| POST | `/tasks` | **oui** | Création (400 si `user_id` inconnu) |
| PUT | `/tasks/{id}` | **oui** | Mise à jour partielle |
| DELETE | `/tasks/{id}` | **oui** | Suppression |
| POST | `/login` | non | Obtention du token |
| WS | `/ws/tasks` | non | Flux d'événements temps réel |

Points d'apprentissage : paramètres de chemin et de requête, `HTTPException`, `response_model`, pattern `db.add → commit → refresh`.

### 3.6 WebSocket temps réel (`websocket.py`, `routers/ws.py`)
- `ConnectionManager` garde la liste des connexions actives (`connect`, `disconnect`, `broadcast`).
- Les endpoints d'écriture appellent `await manager.broadcast({...})` après le commit.
- Événements émis : `task_created`, `task_updated`, `task_deleted`, chacun avec le payload de la tâche.
- Les connexions mortes sont nettoyées pendant le broadcast.

## 4. Lancer le projet

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

uvicorn app.main:app --reload
```

- Documentation interactive : http://127.0.0.1:8000/docs
- Écouter les événements temps réel (dans un 2ᵉ terminal) :
  ```bash
  python ws_client.py
  ```

### Exemple d'utilisation

```bash
# 1. Login
curl -X POST http://127.0.0.1:8000/login \
  -H "Content-Type: application/json" \
  -d '{"username": "alice"}'
# → {"access_token": "<TOKEN>", "token_type": "bearer"}

# 2. Créer une tâche
curl -X POST http://127.0.0.1:8000/tasks \
  -H "Authorization: Bearer <TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{"title": "Apprendre FastAPI", "user_id": 1}'

# 3. Lister les tâches non terminées
curl "http://127.0.0.1:8000/tasks?completed=false"

# 4. Terminer la tâche
curl -X PUT http://127.0.0.1:8000/tasks/1 \
  -H "Authorization: Bearer <TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{"completed": true}'
```

Le terminal `ws_client.py` affiche alors chaque événement reçu.

## 5. Points d'amélioration (pistes pour aller plus loin)

Le cours est un bon support d'apprentissage ; voici ce qui le séparerait d'une application de production.

**Sécurité**
- `/login` n'exige **aucun mot de passe** : il faut ajouter un hash (`passlib`/`bcrypt`) ou passer à OAuth2 + JWT (`OAuth2PasswordBearer`).
- Les tokens sont dans un dict en mémoire : perdus au redémarrage, non partagés entre workers, sans expiration. → JWT ou table de sessions/Redis.
- Le WebSocket `/ws/tasks` est public et diffuse les tâches de tous les utilisateurs.
- Aucune vérification de propriété : tout utilisateur connecté peut modifier ou supprimer n'importe quelle tâche.

**Correction / robustesse**
- `PUT` avec `if task_update.user_id is not None` : impossible de **désassigner** une tâche (mettre `user_id` à `null`). Solution : `task_update.model_dump(exclude_unset=True)`.
- Les routes sont `async def` mais utilisent SQLAlchemy **synchrone** : cela bloque la boucle d'événements. Soit `def` simple pour ces routes, soit SQLAlchemy async.
- Les utilisateurs ne sont pas uniques (`username` sans `unique=True`).
- `seed_data()` et `create_all()` s'exécutent à l'import : préférer un événement `lifespan`, et **Alembic** pour les migrations.

**Qualité du projet**
- Configuration en dur (`DATABASE_URL`) → variables d'environnement (`pydantic-settings`).
- Versions non épinglées dans `requirements.txt`.
- Pas de tests : ajouter `pytest` + `TestClient` (et un `WebSocketTestSession`).
- Pas de pagination sur `GET /tasks` (`skip` / `limit`).
- Le dict de payload est dupliqué 3 fois : réutiliser le schéma `Task` (`Task.model_validate(db_task).model_dump()` avec `from_attributes=True`).

## 6. Résumé : ce qu'on retient

1. **Structurer** l'application en modules (models / schemas / routers / dependencies).
2. **Valider** avec Pydantic, **documenter** gratuitement avec OpenAPI.
3. **Injecter** les dépendances (`Depends`) : session DB, utilisateur courant.
4. **Protéger** les routes avec un schéma Bearer.
5. **Diffuser** des événements temps réel avec les WebSockets.
6. Savoir **où s'arrête le prototype** : mot de passe, JWT, async, tests, migrations.
