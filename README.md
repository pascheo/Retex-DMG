# REX DMG – Full Cloud CD78

Application web de **Retour d'Expérience** pour le POC Full Cloud (licence M365 E1)  
de la Direction des Moyens Généraux du Conseil Départemental des Yvelines.

---

## Installation

### Prérequis
- Python 3.10 ou supérieur
- pip

### 1. Installer les dépendances

```bash
pip install -r requirements.txt
```

### 2. Lancer l'application

```bash
uvicorn main:app --host 0.0.0.0 --port 8080
```

La base de données SQLite (`retex_dmg.db`) est créée automatiquement dans le répertoire courant au premier lancement.

---

## Accès

| Page | URL |
|------|-----|
| Formulaire agent | `http://[IP]:8080/` |
| Dashboard admin | `http://[IP]:8080/admin` |
| Export CSV | Bouton dans le dashboard admin |
| API statistiques | `http://[IP]:8080/api/stats` |

Remplacez `[IP]` par l'adresse IP du poste ou du serveur hébergeant l'application.  
En local : `http://localhost:8080/`

---

## Mot de passe administrateur

Par défaut : **`dmg2024`**

Pour le changer, définissez la variable d'environnement `ADMIN_PASSWORD` avant le lancement :

```bash
# Linux / macOS
export ADMIN_PASSWORD=MonMotDePasse2024
uvicorn main:app --host 0.0.0.0 --port 8080

# Windows (PowerShell)
$env:ADMIN_PASSWORD="MonMotDePasse2024"
uvicorn main:app --host 0.0.0.0 --port 8080

# Windows (CMD)
set ADMIN_PASSWORD=MonMotDePasse2024
uvicorn main:app --host 0.0.0.0 --port 8080
```

---

## Fonctionnalités

### Formulaire agent (`/`)
- 24 questions réparties en 5 sections
- Notation de 1 (Très insatisfait) à 4 (Très satisfait) + option "Sans objet"
- Commentaire libre par question
- Calcul en temps réel de la note moyenne pendant la saisie
- Détection des doublons (même nom + même date)

### Dashboard admin (`/admin`)
- Vue d'ensemble de tous les répondants avec note moyenne
- Statistiques par section (moyenne hors "Sans objet")
- Graphique radar des 5 sections
- Filtrage par service/équipe
- Vue détaillée par répondant
- Export CSV de toutes les réponses

---

## Structure des fichiers

```
Retex-DMG/
├── main.py              # Application FastAPI (routes, base de données)
├── requirements.txt     # Dépendances Python
├── static/
│   ├── style.css        # Feuille de styles CD78
│   └── admin.js         # Graphique radar + interactions dashboard
├── templates/
│   ├── form.html        # Formulaire agent
│   └── admin.html       # Dashboard administrateur
├── README.md            # Ce fichier
└── retex_dmg.db         # Base SQLite (créée au premier lancement)
```

---

## Sécurité

> **Usage interne uniquement.** Cette application est conçue pour être déployée sur un réseau local ou intranet.  
> Ne pas exposer sur Internet sans mise en place préalable d'une authentification renforcée (HTTPS, reverse proxy avec authentification, etc.).

- Le mot de passe admin est transmis via cookie HTTP (`httponly`, `samesite=strict`)
- La base de données SQLite est un fichier local — prévoir des sauvegardes régulières
- Aucune donnée n'est envoyée vers des services externes

---

## Déploiement Windows (service)

Pour lancer automatiquement l'application au démarrage de Windows, utiliser **NSSM** (Non-Sucking Service Manager) :

```bash
nssm install RetexDMG "C:\Python310\Scripts\uvicorn.exe" "main:app --host 0.0.0.0 --port 8080"
nssm set RetexDMG AppDirectory "C:\chemin\vers\Retex-DMG"
nssm start RetexDMG
```
