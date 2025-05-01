# Documentation des API ERPNext

## Introduction

Ce document décrit les principales API disponibles dans ERPNext. Ces API permettent d'interagir avec le système depuis des applications externes ou d'étendre les fonctionnalités existantes.

## Principes de base

### Structure des appels API

Dans ERPNext, basé sur Frappe Framework, les API sont exposées via des méthodes Python décorées avec `@frappe.whitelist()`. Ces méthodes peuvent être appelées via des requêtes HTTP POST vers le point d'entrée :
/api/method/[nom_du_module].[nom_du_fichier].[nom_de_la_fonction]
Exemple :
/api/method/erpnext.stock.get_item.get_item_details


### Authentification

Toutes les API nécessitent une authentification, sauf mention contraire. L'authentification peut être effectuée de plusieurs façons :

1. **Session basée sur les cookies** : Utilisée principalement par l'interface web d'ERPNext
2. **API Key et API Secret** : Pour les intégrations système à système
   - Créez un utilisateur API dans "User" et générez une clé API
   - Utilisez l'en-tête `Authorization: token [api_key]:[api_secret]`
3. **Basic Auth** : Username et mot de passe en en-tête HTTP
   - Utilisez l'en-tête `Authorization: Basic [base64(username:password)]`

## API principales par module

### 1. API Générales

#### Obtenir la version d'ERPNext
GET /api/method/erpnext.setup.utils.get_app_version


#### Vérifier les autorisations d'application
POST /api/method/erpnext.check_app_permission


#### Obtenir l'entreprise par défaut
POST /api/method/erpnext.get_default_company


### 2. API de réinitialisation de base de données

Ces API font partie du module développé pour réinitialiser la base de données.

#### Obtenir toutes les tables disponibles
POST /api/method/erpnext.reset_database.page.reset_database.reset_database.get_all_tables

Cette méthode renvoie la liste de toutes les tables disponibles dans la base de données, à l'exception des tables système protégées. Les informations retournées incluent :
- Nom de la table
- Nombre d'enregistrements
- Description (lorsque disponible)

#### Réinitialiser les tables sélectionnées
POST /api/method/erpnext.reset_database.page.reset_database.reset_database.reset_selected_tables

Paramètres :
- `tables` : Liste des noms de tables à réinitialiser

Cette méthode supprime toutes les données des tables spécifiées et réinitialise leurs compteurs d'auto-incrémentation.

#### Réinitialiser toutes les tables
POST /api/method/erpnext.reset_database.page.reset_database.reset_database.reset_all_tables

Cette méthode supprime toutes les données de toutes les tables non système, mais préserve les informations utilisateur.

### 3. API Document

ERPNext utilise une API REST pour manipuler les documents. Les opérations CRUD peuvent être effectuées sur n'importe quel DocType.

#### Obtenir un document
GET /api/resource/:doctype/:name
Exemple : /api/resource/Customer/CUST-001

#### Créer un document
POST /api/resource/:doctype
{
    "doctype": "Customer",
    "customer_name": "Nouveau Client",
    "customer_type": "Company"
}

#### Mettre à jour un document
PUT /api/resource/:doctype/:name
{
    "credit_limit": 100000
}

#### Supprimer un document
DELETE /api/resource/:doctype/:name

#### Exécuter une méthode sur un document
POST /api/method/frappe.client.set_value
{
    "doctype": "Customer",
    "name": "CUST-001",
    "fieldname": "credit_limit", 
    "value": 150000
}

### 4. API Liste et Requêtes

#### Obtenir une liste de documents
GET /api/resource/:doctype
Paramètres :
- fields: ["name", "customer_name", "credit_limit"]
- filters: [["Customer", "customer_type", "=", "Company"]]
- order_by: "name desc"
- limit_start: 0
- limit_page_length: 20

#### Exécuter une requête personnalisée
POST /api/method/frappe.desk.reportview.get
{
    "doctype": "Customer",
    "fields": ["name", "customer_name", "credit_limit"],
    "filters": [["Customer", "customer_type", "=", "Company"]],
    "order_by": "name desc",
    "limit_start": 0,
    "limit_page_length": 20
}

### 5. API Fichiers et Pièces jointes

#### Télécharger un fichier
GET /api/method/frappe.core.doctype.file.file.download_file?file_url=:file_url

#### Téléverser un fichier
POST /api/method/upload_file
Paramètres :
- doctype (facultatif)
- docname (facultatif)
- folder (facultatif, défaut: Home)
- is_private (facultatif, 0 ou 1)
- file : fichier à téléverser

### 6. API Comptabilité
#### Générer une entrée de journal
POST /api/method/erpnext.accounts.doctype.journal_entry.journal_entry.make_journal_entry
{
    "posting_date": "2023-01-01",
    "accounts": [
        {
            "account": "Espèces - ABC",
            "debit": 100000,
            "credit": 0,
            "cost_center": "Centre principal - ABC"
        },
        {
            "account": "Ventes - ABC",
            "debit": 0,
            "credit": 100000,
            "cost_center": "Centre principal - ABC"
        }
    ],
    "company": "ABC Corporation",
    "user_remark": "Vente en espèces"
}

#### Réconcilier des paiements
POST /api/method/erpnext.accounts.doctype.payment_reconciliation.payment_reconciliation.reconcile

### 7. API Ventes
#### Créer une cotation à partir d'une opportunité
POST /api/method/erpnext.selling.doctype.quotation.quotation.make_quotation
{
    "source_name": "OPTY-001"
}

#### Créer une commande client à partir d'une cotation
POST /api/method/erpnext.selling.doctype.quotation.quotation.make_sales_order
{
    "source_name": "QTN-001"
}

### 8. API Achats
#### Créer une demande d'achat
POST /api/method/erpnext.buying.doctype.purchase_order.purchase_order.make_purchase_request
{
    "items": [
        {
            "item_code": "ITEM-001",
            "qty": 5
        }
    ],
    "company": "ABC Corporation"
}

#### Créer un bon de commande à partir d'une demande d'achat
POST /api/method/erpnext.buying.doctype.purchase_order.purchase_order.make_purchase_order
{
    "source_name": "PR-001"
}

### 9. API Inventaire
#### Obtenir le solde de stock
POST /api/method/erpnext.stock.get_item_details.get_stock_balance_for
{
    "item_code": "ITEM-001",
    "warehouse": "Entrepôt principal - ABC",
    "posting_date": "2023-01-01",
    "posting_time": "12:00:00"
}

#### Faire une entrée de stock
POST /api/method/erpnext.stock.doctype.stock_entry.stock_entry.make_stock_entry
{
    "purpose": "Material Receipt",
    "items": [
        {
            "item_code": "ITEM-001",
            "qty": 10,
            "to_warehouse": "Entrepôt principal - ABC"
        }
    ],
    "company": "ABC Corporation"
}

#### Obtenir le prix d'un article
POST /api/method/erpnext.stock.get_item_details.get_item_price
{
    "item_code": "ITEM-001",
    "price_list": "Prix de vente standard"
}

### 10. API Fabrication
#### Créer un ordre de fabrication à partir d'un BOM
POST /api/method/erpnext.manufacturing.doctype.production_plan.production_plan.make_work_order
{
    "production_plan": "PP-001",
    "company": "ABC Corporation"
}

#### Obtenir la liste des BOM (nomenclatures)
GET /api/resource/BOM
Paramètres :
- filters: [["BOM", "item", "=", "ITEM-001"]]

### 11. API CRM
#### Créer un lead
POST /api/resource/Lead
{
    "doctype": "Lead",
    "lead_name": "John Doe",
    "company_name": "ABC Inc.",
    "email_id": "john@example.com",
    "source": "Campaign"
}

#### Convertir un lead en opportunité
POST /api/method/erpnext.crm.doctype.lead.lead.make_opportunity
{
    "lead": "LEAD-001",
    "transaction_date": "2023-01-01"
}

#### Créer un client à partir d'un lead
POST /api/method/erpnext.crm.doctype.lead.lead.make_customer
{
    "lead": "LEAD-001"
}

### 12. API Ressources Humaines
#### Créer un employé
POST /api/resource/Employee
{
    "first_name": "Pierre",
    "last_name": "Dupont",
    "gender": "Male",
    "date_of_birth": "1985-01-15",
    "date_of_joining": "2023-01-01",
    "department": "IT",
    "designation": "Développeur",
    "company": "ABC Corporation",
    "status": "Active"
}

#### Créer une feuille de présence
POST /api/resource/Attendance
{
    "employee": "EMP-001",
    "attendance_date": "2023-01-02",
    "status": "Present",
    "company": "ABC Corporation"
}

#### Créer une demande de congé
POST /api/resource/Leave Application
{
    "employee": "EMP-001",
    "from_date": "2023-02-01",
    "to_date": "2023-02-05",
    "leave_type": "Congés payés",
    "description": "Vacances familiales"
}

### 13. API Projet
#### Créer un projet
POST /api/resource/Project
{
    "project_name": "Implémentation ERP",
    "status": "Open",
    "expected_start_date": "2023-03-01",
    "expected_end_date": "2023-06-30",
    "company": "ABC Corporation"
}

#### Ajouter une tâche au projet
POST /api/resource/Task
{
    "subject": "Configuration initiale",
    "project": "PRJ-001",
    "status": "Open",
    "exp_start_date": "2023-03-01",
    "exp_end_date": "2023-03-15",
    "description": "Configuration des paramètres de base"
}

### 14. API Webhooks
#### Créer un webhook
POST /api/resource/Webhook
{
    "webhook_doctype": "Sales Order",
    "webhook_docevent": "on_submit",
    "request_url": "https://example.com/webhook",
    "request_method": "POST",
    "request_structure": "Form URL-Encoded",
    "enable_security": 1,
    "webhook_secret": "votre_secret_ici"
}

### 15. API Rapports
#### Exécuter un rapport
POST /api/method/frappe.desk.query_report.run
{
    "report_name": "Rapport d'analyse des ventes",
    "filters": {
        "company": "ABC Corporation",
        "from_date": "2023-01-01",
        "to_date": "2023-03-31"
    }
}

### 16. API d'Authentification et Login

#### Login (Connexion)
POST /api/method/login
```json
{
  "usr": "utilisateur@exemple.com",
  "pwd": "votre_mot_de_passe"
}
```

#### Vérifier l'utilisateur connecté
GET /api/method/frappe.auth.get_logged_user

#### Se déconnecter
POST /api/method/logout

#### Inscrire un nouvel utilisateur
POST /api/method/frappe.core.doctype.user.user.sign_up
```json
{
  "email": "nouveau@exemple.com",
  "full_name": "Nouvel Utilisateur",
  "redirect_to": "/app"
}
```

### 17. API de Gestion des Articles (Items)

#### Récupérer la liste des articles
GET /api/resource/Item
Paramètres optionnels:
fields=["item_code", "item_name", "description", "stock_uom"]
filters=[["Item", "is_stock_item", "=", 1]]

#### Créer un article
POST /api/resource/Item
```json
{
  "item_code": "ITEM-00001",
  "item_name": "Nom de l'article",
  "description": "Description de l'article",
  "item_group": "Produits",
  "stock_uom": "Nos",
  "is_stock_item": 1,
  "is_sales_item": 1,
  "is_purchase_item": 1
}
```

### 18. API de Demande de Besoin (Material Request)

#### Récupérer les demandes de besoin
GET /api/resource/Material Request
```
Paramètres:
fields=["name", "status", "transaction_date", "material_request_type"]
filters=[["Material Request", "status", "=", "Pending"]]
```

#### Créer une demande de besoin
POST /api/resource/Material Request
```json
{
  "material_request_type": "Purchase",
  "transaction_date": "2023-01-15",
  "company": "Votre Entreprise",
  "items": [
    {
      "item_code": "ITEM-00001",
      "qty": 10,
      "schedule_date": "2023-01-20",
      "warehouse": "Entrepôt Principal - VE"
    }
  ]
}
```

#### Mettre à jour le statut d'une demande
POST /api/method/erpnext.stock.doctype.material_request.material_request.update_status
```json
{
  "name": "MAT-MR-2023-00001",
  "status": "Pending"
}
```

### 19. API de Demande de Devis (Request for Quotation)

#### Récupérer toutes les demandes de devis
GET /api/resource/Request for Quotation
```
Paramètres:
fields=["name", "transaction_date", "status"]
filters=[["Request for Quotation", "docstatus", "=", 1]]
```

#### Voir les demandes de devis par fournisseur
GET /api/resource/Request for Quotation Supplier
```
filters=[["Request for Quotation Supplier", "supplier", "=", "FOURNISSEUR-001"]]
```

#### Créer une demande de devis à partir d'une demande de besoin
POST /api/method/erpnext.stock.doctype.material_request.material_request.make_request_for_quotation
```json
{
  "source_name": "MAT-MR-2023-00001"
}
```

### 20. API de Devis Fournisseur (Supplier Quotation)

#### Récupérer les devis fournisseur
GET /api/resource/Supplier Quotation
```
Paramètres:
fields=["name", "supplier", "grand_total", "status"]
filters=[["Supplier Quotation", "supplier", "=", "FOURNISSEUR-001"]]
```

#### Créer un devis fournisseur
POST /api/resource/Supplier Quotation
```json
{
  "supplier": "FOURNISSEUR-001",
  "transaction_date": "2023-01-20",
  "valid_till": "2023-02-20",
  "company": "Votre Entreprise",
  "items": [
    {
      "item_code": "ITEM-00001",
      "qty": 10,
      "rate": 100,
      "schedule_date": "2023-01-25"
    }
  ]
}
```

### 21. API de Bon de Commande (Purchase Order)

#### Récupérer les bons de commande
GET /api/resource/Purchase Order
```
Paramètres:
fields=["name", "supplier", "grand_total", "status"]
filters=[["Purchase Order", "status", "=", "To Receive and Bill"]]
```

#### Voir les bons de commande par fournisseur
GET /api/resource/Purchase Order
```
filters=[["Purchase Order", "supplier", "=", "FOURNISSEUR-001"]]
```

#### Créer un bon de commande à partir d'un devis fournisseur
POST /api/method/erpnext.buying.doctype.supplier_quotation.supplier_quotation.make_purchase_order
```json
{
  "source_name": "QUOTE-2023-00001"
}
```

### 22. API de Facture et Paiement

#### Récupérer les factures d'achat
GET /api/resource/Purchase Invoice
```
Paramètres:
fields=["name", "supplier", "grand_total", "status", "outstanding_amount"]
filters=[["Purchase Invoice", "status", "=", "Unpaid"]]
```

#### Créer une facture à partir d'un bon de commande
POST /api/method/erpnext.buying.doctype.purchase_order.purchase_order.make_purchase_invoice
```json
{
  "source_name": "PO-2023-00001"
}
```

#### Créer un paiement pour une facture
POST /api/resource/Payment Entry
```json
{
  "payment_type": "Pay",
  "party_type": "Supplier",
  "party": "FOURNISSEUR-001",
  "company": "Votre Entreprise",
  "paid_amount": 1000,
  "received_amount": 1000,
  "reference_no": "REF-001",
  "reference_date": "2023-02-01",
  "paid_from": "Compte Bancaire - VE",
  "paid_to": "Créditeurs - VE",
  "references": [
    {
      "reference_doctype": "Purchase Invoice",
      "reference_name": "PINV-2023-00001",
      "allocated_amount": 1000
    }
  ]
}
```

### 23. API de Fournisseurs

#### Récupérer la liste des fournisseurs
GET /api/resource/Supplier
```
Paramètres:
fields=["name", "supplier_name", "supplier_group", "country"]
filters=[["Supplier", "disabled", "=", 0]]
```

#### Créer un fournisseur
POST /api/resource/Supplier
```json
{
  "supplier_name": "Nouveau Fournisseur",
  "supplier_group": "Matières Premières",
  "supplier_type": "Company",
  "country": "France"
}
```

## Gestion des erreurs

Les réponses d'erreur suivent un format standard :
```json
{
    "exc_type": "ValidationError",
    "message": "Description de l'erreur",
    "http_status_code": 417
}
```

Codes d'erreur courants :
- 401 : Non autorisé (problème d'authentification)
- 403 : Interdit (problème d'autorisation)
- 404 : Non trouvé (ressource inexistante)
- 417 : Échec de la validation
- 500 : Erreur interne du serveur

## Bonnes pratiques

1. **Limiter les requêtes** : Évitez d'envoyer un grand nombre de requêtes en peu de temps
2. **Mise en cache** : Mettez en cache les réponses qui ne changent pas souvent
3. **Gestion des erreurs** : Implémentez une logique robuste de gestion des erreurs
4. **Sécurité** : Protégez vos clés API et ne les exposez jamais côté client
5. **Pagination** : Utilisez la pagination pour les requêtes qui retournent de grandes quantités de données

## Ressources additionnelles

- [Documentation Frappe Framework](https://frappeframework.com/docs/user/en)
- [Guide de développement ERPNext](https://frappe.io/docs/user/en/api)
- [Forum de la communauté ERPNext](https://discuss.erpnext.com)