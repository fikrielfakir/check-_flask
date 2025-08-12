# Système de Gestion des Chèques (Cheque Management System)

## Vue d'ensemble
Application web complète développée en Flask pour la gestion des chèques et des transactions financières, optimisée pour une utilisation hors ligne sur Windows. Le système offre une fonctionnalité complète pour le suivi des chèques, la gestion des clients, des banques et des agences, avec un contrôle d'accès basé sur les rôles et une gestion avancée de classeurs Excel.

## Fonctionnalités Principales

### 🏦 Gestion des Chèques
- **Création et modification** : Interface intuitive pour créer et modifier des chèques
- **Suivi de statut** : EN_ATTENTE → DÉPOSÉ → ENCAISSÉ/REJETÉ
- **Validation automatique** : Détection de doublons avec alertes intelligentes
- **Synchronisation Excel** : Mise à jour automatique des fichiers Excel
- **Gestion des échéances** : Alertes pour les chèques en retard ou à échéance proche

### 👥 Gestion des Clients et Déposants
- **Clients** : Personnes physiques et entreprises avec informations complètes
- **Déposants** : Système complet de gestion des personnes qui déposent les chèques
- **Création rapide** : Modales popup pour créer clients/déposants depuis le formulaire de chèque
- **Recherche avancée** : Autocomplétion et filtrage intelligent
- **Évaluation des risques** : Système d'évaluation automatique des risques clients

### 🏛️ Gestion Bancaire
- **Banques** : Base de données complète des institutions bancaires
- **Agences** : Gestion détaillée des succursales avec coordonnées
- **Banques de dépôt** : Suivi séparé des banques où les chèques sont déposés

### 📊 Analytics et Rapports Avancés
- **Tableau de bord exécutif** : Métriques en temps réel et KPI
- **Analyse de vieillissement** : Suivi des chèques par durée de statut
- **Tendances saisonnières** : Analyse des flux entrants/sortants
- **Prédiction de trésorerie** : Modèles prédictifs basés sur l'IA
- **Évaluation des risques** : Scoring automatique des clients à risque

### 📁 Gestion Excel Avancée
- **Classeurs annuels** : Un classeur par année avec 12 feuilles mensuelles
- **Synchronisation automatique** : Mise à jour en temps réel base de données ↔ Excel
- **Système de sauvegarde** : Sauvegardes automatiques et nettoyage
- **Gestion des conflits** : Résolution intelligente des doublons

### 🔐 Sécurité et Authentification
- **Contrôle d'accès basé sur les rôles** :
  - **Admin** : Accès complet au système
  - **Comptable** : Gestion des chèques et clients
  - **Agent** : Saisie et consultation limitée
  - **User** : Accès en lecture seule
- **Authentification sécurisée** : Hash des mots de passe avec Werkzeug
- **Sessions sécurisées** : Gestion des sessions avec Flask-Login

### 🤖 Automatisation Intelligente
- **Détection de doublons** : Algorithmes ML pour identifier les doublons
- **Notifications automatiques** : Système d'alertes personnalisables
- **Workflows automatisés** : Gestion automatique des processus
- **Optimisation des performances** : Métriques et optimisations automatiques

## Architecture Technique

### Frontend
- **Framework** : Flask avec templating Jinja2
- **UI Framework** : Bootstrap 5.3.0 pour design responsive
- **JavaScript** : jQuery pour interactions côté client
- **Icônes** : Font Awesome 6.4.0
- **Styling** : CSS personnalisé avec variables CSS pour le thème

### Backend
- **Framework** : Flask (framework web Python)
- **ORM** : SQLAlchemy avec Flask-SQLAlchemy
- **Authentification** : Flask-Login pour la gestion des sessions
- **Formulaires** : Flask-WTF avec WTForms pour validation
- **Sécurité** : Protection CSRF activée, ProxyFix pour déploiement
- **Gestion de fichiers** : Uploads sécurisés avec limites de taille (16MB)

### Base de Données
- **Développement** : SQLite pour développement (`sqlite:///cheques.db`)
- **Production** : PostgreSQL configurable via `DATABASE_URL`
- **Gestion des connexions** : Pool recycling et pre-ping pour la fiabilité

### Fonctionnalités Avancées
- **Machine Learning** : scikit-learn pour analyse prédictive
- **Traitement de données** : pandas et numpy pour analytics
- **Cache intelligent** : Flask-Caching pour optimisation
- **Limitation de taux** : Flask-Limiter pour sécurité
- **Planificateur** : APScheduler pour tâches automatisées

## Modèles de Données

### Chèque (Core Entity)
```python
- id, cheque_number, amount, currency
- issue_date, due_date, status
- client_id, branch_id, depositor_id, deposit_branch_id
- notes, unpaid_reason, attachment_path
- created_by, created_at, updated_at
```

### Client
```python
- id, type (personne/entreprise), name
- id_number, vat_number, phone, email
- address, city, postal_code, is_active
```

### Déposant (Depositor)
```python
- id, name, type (personne/entreprise/mandataire)
- phone, email, address, city, postal_code
- id_number, id_type, company_name, job_title
- bank_account_number, bank_name, bank_branch
- risk_level, is_active, blocked, notes
```

### Banque et Agence
```python
Bank: id, name, code, swift_code, country
Branch: id, bank_id, name, code, address, phone, email
```

### Utilisateur
```python
- id, username, email, password_hash
- role (admin/comptable/agent/user)
- is_active, created_at, last_login
```

## Flux de Travail

### 1. Cycle de Vie d'un Chèque
1. **Création** : Saisie avec validation et détection de doublons
2. **Dépôt** : Changement de statut avec suivi bancaire
3. **Encaissement/Rejet** : Mise à jour finale avec raisons
4. **Rapports** : Export automatique pour analyse

### 2. Gestion des Accès Utilisateurs
- **Admin** : Gestion complète système, banques, utilisateurs
- **Comptable/Agent** : Gestion chèques, clients, déposants
- **User** : Consultation données assignées

### 3. Synchronisation Excel
- **Création automatique** : Génération des 12 feuilles mensuelles
- **Mise à jour temps réel** : Sync bidirectionnelle base ↔ Excel
- **Gestion des conflits** : Résolution automatique des doublons

## Déploiement et Configuration

### Variables d'Environnement
```bash
DATABASE_URL=postgresql://user:pass@host:port/db
SESSION_SECRET=your-secret-key
FLASK_ENV=production
```

### Structure des Fichiers
```
/data/                 # Données locales
  /excel/             # Classeurs Excel
  /exports/           # Exports PDF/Excel
  /uploads/           # Fichiers uploadés
/routes/              # Routes modulaires
/templates/           # Templates Jinja2
/static/              # Assets statiques
/utils/               # Utilitaires et services
```

### Fonctionnalités de Sécurité
- Protection CSRF globale
- Validation sécurisée des uploads
- Contrôle d'accès basé sur les rôles
- Middleware ProxyFix pour reverse proxy

### Optimisations de Performance
- Pool de connexions base de données
- Planification de tâches en arrière-plan
- Structure applicative modulaire
- Support du cache de templates

## Utilisation

### Création d'un Chèque
1. Accéder au formulaire de création
2. Rechercher/créer client et déposant via modales
3. Sélectionner banque et agence
4. Saisir Mont et dates
5. Validation automatique et sauvegarde

### Tableau de Bord
- **Métriques en temps réel** : Statuts, Monts, échéances
- **Graphiques interactifs** : Évolution mensuelle, répartition bancaire
- **Alertes intelligentes** : Chèques en retard, clients à risque
- **Top clients** : Classement par Mont encaissé

### Analytics Avancées
- **Analyse de vieillissement** : Durée dans chaque statut
- **Tendances saisonnières** : Flux entrants/sortants
- **Prédictions** : Modèles de trésorerie basés sur l'IA
- **Évaluation des risques** : Scoring automatique des clients

### Gestion Excel
- **Classeurs automatiques** : Création des 12 feuilles mensuelles
- **Synchronisation** : Mise à jour bidirectionnelle
- **Sauvegardes** : Système automatique de backup
- **Export flexible** : PDF, Excel avec filtres personnalisés

## Avantages Clés

### 🚀 Performance
- Base de données optimisée avec indexation
- Cache intelligent pour requêtes fréquentes
- Pagination efficace pour grandes listes
- Requêtes SQL optimisées avec jointures explicites

### 🔒 Sécurité
- Authentification robuste multi-niveaux
- Protection contre les attaques CSRF
- Validation stricte des données d'entrée
- Audit trail complet des actions

### 📱 Ergonomie
- Interface responsive Bootstrap
- Autocomplétion intelligente
- Modales pour création rapide
- Notifications temps réel

### 🔧 Maintenance
- Code modulaire et extensible
- Documentation complète
- Tests automatisés
- Logging détaillé pour débogage

### 📊 Intelligence
- Détection automatique de doublons
- Prédictions basées sur l'IA
- Alertes proactives
- Analytics avancées

Cette application représente une solution complète et moderne pour la gestion financière des chèques, combinant robustesse technique, sécurité avancée et intelligence artificielle pour optimiser les processus métier.