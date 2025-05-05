# Guide des opérations CRUD dans Frappe (Python)

## 1. Création (Create)

### Insérer un nouveau document

```python
# Méthode 1: Utilisation de la classe Document
doc = frappe.get_doc({
    "doctype": "Customer",
    "customer_name": "Nouveau Client",
    "customer_type": "Company",
    "customer_group": "Commercial"
})
doc.insert()
```

```python
# Méthode 2: Création rapide
doc = frappe.new_doc("Customer")
doc.customer_name = "Nouveau Client"
doc.customer_type = "Company"
doc.customer_group = "Commercial"
doc.insert()

```

### Insertion en masse

```python
# Insertion multiple
clients = [
    {"doctype": "Customer", "customer_name": "Client 1", "customer_group": "Commercial"},
    {"doctype": "Customer", "customer_name": "Client 2", "customer_group": "Commercial"}
]
frappe.db.bulk_insert("Customer", clients)
```

## 2. Lecture (Read)

### Récupérer un document complet

```python
# Récupérer un document par nom
doc = frappe.get_doc("Customer", "Nouveau Client")

# Récupérer un document par filtres
doc = frappe.get_doc("Customer", {"customer_name": "Nouveau Client"})
```

### Récupérer des valeurs spécifiques

```python
# Récupérer une valeur simple
phone = frappe.db.get_value("Customer", "Nouveau Client", "phone")

# Récupérer plusieurs valeurs
phone, email = frappe.db.get_value("Customer", "Nouveau Client", ["phone", "email"])

# Récupérer sous forme de dictionnaire
data = frappe.db.get_value("Customer", "Nouveau Client", ["phone", "email"], as_dict=True)
```

### Récupérer plusieurs documents

```python
# Récupérer tous les clients
clients = frappe.get_all("Customer")

# Récupérer avec des filtres
clients = frappe.get_all("Customer", filters={"customer_group": "Commercial"})

# Récupérer avec des champs spécifiques
clients = frappe.get_all("Customer", 
                       filters={"customer_group": "Commercial"}, 
                       fields=["name", "phone", "email"])

# Récupérer avec pagination et tri
clients = frappe.get_all("Customer", 
                       filters={"customer_group": "Commercial"}, 
                       fields=["name", "phone"],
                       limit=10,
                       start=0,
                       order_by="creation desc")
```

### Requêtes SQL directes

```python
# Exécuter une requête SQL directe
results = frappe.db.sql("SELECT name, phone FROM `tabCustomer` WHERE customer_group = 'Commercial'")

# Récupérer sous forme de dictionnaire
results = frappe.db.sql("SELECT name, phone FROM `tabCustomer` WHERE customer_group = 'Commercial'", as_dict=True)
```

## 3. Mise à jour (Update)

### Mettre à jour un document complet

```python
# Charger le document, le modifier puis enregistrer
doc = frappe.get_doc("Customer", "Nouveau Client")
doc.phone = "+33123456789"
doc.email = "contact@nouveau-client.com"
doc.save()
```

### Mettre à jour des champs spécifiques

```python
# Mettre à jour un champ unique
frappe.db.set_value("Customer", "Nouveau Client", "phone", "+33123456789")

# Mettre à jour plusieurs champs
frappe.db.set_value("Customer", "Nouveau Client", {
    "phone": "+33123456789",
    "email": "contact@nouveau-client.com"
})

# Utiliser db_set pour mettre à jour directement la base de données
doc = frappe.get_doc("Customer", "Nouveau Client")
doc.db_set("phone", "+33123456789")
```

### Mises à jour en masse

```python
# Mise à jour multiple avec filtre
frappe.db.sql("""
    UPDATE `tabCustomer` 
    SET customer_group = 'Commercial' 
    WHERE creation > %s
""", '2023-01-01')
```

## 4. Suppression (Delete)

### Supprimer un document

```python
# Méthode 1: Supprimer un document par son nom
frappe.delete_doc("Customer", "Nouveau Client")

# Méthode 2: Utiliser l'objet document
doc = frappe.get_doc("Customer", "Nouveau Client")
doc.delete()
```

### Supprimer avec des filtres

```python
# Supprimer tous les documents correspondant aux filtres
frappe.db.delete("Customer", {"customer_group": "Individuel"})
```

## 5. Transactions et validation

### Gestion des transactions

```python
# Démarrer une transaction
frappe.db.begin()

try:
    # Effectuer des opérations
    doc1 = frappe.get_doc({
        "doctype": "Customer",
        "customer_name": "Client Transaction",
        "customer_group": "Commercial"
    })
    doc1.insert()
    
    doc2 = frappe.get_doc("Customer", "Client Existant")
    doc2.phone = "+33987654321"
    doc2.save()
    
    # Valider la transaction
    frappe.db.commit()
except Exception as e:
    # Annuler en cas d'erreur
    frappe.db.rollback()
    frappe.log_error(f"Erreur de transaction: {str(e)}")
```

### Validation et soumission

```python
# Insérer et soumettre un document
doc = frappe.get_doc({
    "doctype": "Sales Order",
    "customer": "Nouveau Client",
    "items": [
        {
            "item_code": "ITEM-001",
            "qty": 5
        }
    ]
})
doc.insert()
doc.submit()
```

## 6. Exemples spécifiques

### Opérations sur les documents enfants (Child Tables)

```python
# Ajouter des éléments à une table enfant
doc = frappe.get_doc("Sales Order", "SO-00001")
doc.append("items", {
    "item_code": "ITEM-002",
    "qty": 3
})
doc.save()
```

### Travailler avec les singles (DocTypes à enregistrement unique)

```python
# Récupérer et modifier un document de type Single
settings = frappe.get_doc("System Settings")
settings.backup_limit = 5
settings.save()

# Récupérer une valeur unique
backup_limit = frappe.db.get_single_value("System Settings", "backup_limit")

# Définir une valeur unique
frappe.db.set_single_value("System Settings", "backup_limit", 10)
```

### Recherche complexe avec QueryBuilder

```python
# Utilisation du Query Builder
Customer = frappe.qb.DocType("Customer")
query = (
    frappe.qb.from_(Customer)
    .select(Customer.name, Customer.phone, Customer.email)
    .where(Customer.customer_group == "Commercial")
    .where(Customer.disabled == 0)
    .orderby(Customer.creation, order=frappe.qb.desc)
    .limit(10)
)
results = query.run(as_dict=True)
```

## 7. Exemples de fonctions whitelisted (API)

Voici des exemples concrets de fonctions whitelisted qui peuvent être appelées depuis le frontend ou via l'API REST.

### Exemple 1: Création d'une nouvelle tâche

```python
@frappe.whitelist()
def creer_nouvelle_tache(titre, description, assigne_a=None, date_echeance=None):
    """Crée une nouvelle tâche et renvoie l'objet créé
    
    Args:
        titre (str): Titre de la tâche
        description (str): Description détaillée
        assigne_a (str, optional): Utilisateur assigné à la tâche
        date_echeance (str, optional): Date d'échéance au format YYYY-MM-DD
        
    Returns:
        dict: La tâche créée au format JSON
    """
    try:
        # Vérification d'autorisation
        if not frappe.has_permission("Task", "create"):
            frappe.throw(_("Vous n'avez pas les permissions pour créer une tâche"), frappe.PermissionError)
            
        # Création du document
        tache = frappe.get_doc({
            "doctype": "Task",
            "subject": titre,
            "description": description,
            "status": "Open",
            "_assign": frappe.as_json([assigne_a]) if assigne_a else None,
            "exp_end_date": date_echeance
        })
        
        # Insertion et validation
        tache.insert()
        
        # Journal d'activité
        frappe.log_error(f"Tâche créée: {tache.name}", "Création de tâche")
        
        return tache.as_dict()
    
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), f"Erreur lors de la création de tâche: {str(e)}")
        frappe.throw(_("Erreur lors de la création de la tâche: {0}").format(str(e)))
```

### Exemple 2: Mise à jour du statut de plusieurs commandes

```python
@frappe.whitelist()
def mettre_a_jour_statut_commandes(commandes, nouveau_statut, commentaire=None):
    """Met à jour le statut de plusieurs commandes à la fois
    
    Args:
        commandes (str): Liste de noms de commandes au format JSON
        nouveau_statut (str): Nouveau statut à appliquer
        commentaire (str, optional): Commentaire expliquant le changement
        
    Returns:
        dict: Résultat avec le nombre de commandes mises à jour
    """
    if isinstance(commandes, str):
        commandes = json.loads(commandes)
        
    if not commandes:
        frappe.throw(_("Aucune commande sélectionnée"))
        
    # Vérification du statut valide
    statuts_valides = frappe.get_meta("Sales Order").get_field("status").options.split("\n")
    if nouveau_statut not in statuts_valides:
        frappe.throw(_("Statut invalide: {0}").format(nouveau_statut))
    
    # Démarrer une transaction
    frappe.db.begin()
    
    mises_a_jour = 0
    erreurs = []
    
    try:
        for commande in commandes:
            try:
                # Récupérer le document
                doc = frappe.get_doc("Sales Order", commande)
                
                # Vérifier les permissions
                if not doc.has_permission("write"):
                    erreurs.append(f"{commande}: Permission refusée")
                    continue
                    
                # Mettre à jour le statut
                doc.status = nouveau_statut
                doc.add_comment("Info", f"Statut changé en '{nouveau_statut}'")
                
                if commentaire:
                    doc.add_comment("Comment", commentaire)
                    
                doc.save()
                mises_a_jour += 1
                
            except Exception as e:
                erreurs.append(f"{commande}: {str(e)}")
        
        # Valider la transaction si tout va bien
        if not erreurs:
            frappe.db.commit()
        else:
            # Annuler si des erreurs se sont produites
            frappe.db.rollback()
            frappe.throw(_("Des erreurs se sont produites: {0}").format("\n".join(erreurs)))
            
        return {
            "success": True,
            "message": _("{0} commandes mises à jour").format(mises_a_jour),
            "count": mises_a_jour
        }
        
    except Exception as e:
        frappe.db.rollback()
        frappe.log_error(frappe.get_traceback(), "Erreur de mise à jour des commandes")
        frappe.throw(_("Erreur lors de la mise à jour des commandes: {0}").format(str(e)))
```

### Exemple 3: Récupération des statistiques client avec QueryBuilder

```python
@frappe.whitelist()
def obtenir_statistiques_client(client, periode=None):
    """Récupère les statistiques d'achat d'un client
    
    Args:
        client (str): ID client
        periode (str, optional): Période ('mois', 'trimestre', 'annee', ou None pour tout)
        
    Returns:
        dict: Statistiques du client
    """
    # Vérifier que le client existe
    if not frappe.db.exists("Customer", client):
        frappe.throw(_("Client non trouvé: {0}").format(client))
        
    # Définir la période
    date_filtre = ""
    if periode:
        aujourdhui = frappe.utils.today()
        if periode == "mois":
            date_filtre = ["posting_date", ">=", frappe.utils.add_months(aujourdhui, -1)]
        elif periode == "trimestre":
            date_filtre = ["posting_date", ">=", frappe.utils.add_months(aujourdhui, -3)]
        elif periode == "annee":
            date_filtre = ["posting_date", ">=", frappe.utils.add_months(aujourdhui, -12)]
            
    # Utilisation du QueryBuilder pour récupérer les factures
    SalesInvoice = frappe.qb.DocType("Sales Invoice")
    query_factures = (
        frappe.qb.from_(SalesInvoice)
        .select(
            frappe.qb.functions.Count(SalesInvoice.name).as_("total_factures"),
            frappe.qb.functions.Sum(SalesInvoice.grand_total).as_("montant_total"),
            frappe.qb.functions.Avg(SalesInvoice.grand_total).as_("valeur_moyenne")
        )
        .where(SalesInvoice.customer == client)
        .where(SalesInvoice.docstatus == 1)
    )
    
    # Ajouter le filtre de date si nécessaire
    if date_filtre:
        query_factures = query_factures.where(SalesInvoice[date_filtre[0]] >= date_filtre[2])
        
    # Exécuter la requête
    resultat_factures = query_factures.run(as_dict=True)[0]
    
    # Récupérer les produits les plus achetés
    items = frappe.db.sql("""
        SELECT 
            item_code, 
            item_name,
            SUM(qty) as quantite_totale,
            SUM(amount) as montant_total
        FROM 
            `tabSales Invoice Item`
        WHERE 
            parent IN (
                SELECT name 
                FROM `tabSales Invoice` 
                WHERE customer = %s AND docstatus = 1
                {date_condition}
            )
        GROUP BY item_code
        ORDER BY montant_total DESC
        LIMIT 5
    """.format(
        date_condition = f"AND posting_date >= '{date_filtre[2]}'" if date_filtre else ""
    ), (client), as_dict=True)
    
    # Construire et retourner les statistiques
    stats = {
        "client": frappe.get_doc("Customer", client).customer_name,
        "total_factures": resultat_factures.get("total_factures") or 0,
        "montant_total": resultat_factures.get("montant_total") or 0,
        "valeur_moyenne": resultat_factures.get("valeur_moyenne") or 0,
        "produits_populaires": items,
        "periode": periode or "tout"
    }
    
    return stats
```
## 8. Utilisation avancée du QueryBuilder

Le QueryBuilder de Frappe est un outil puissant pour construire des requêtes SQL complexes de manière sécurisée et lisible, en utilisant une API fluide.

### Principes de base

```python
# Importer le DocType (représentation de la table)
Customer = frappe.qb.DocType("Customer")

# Construction d'une requête simple
query = (
    frappe.qb.from_(Customer)
    .select(Customer.name, Customer.customer_name)
    .where(Customer.disabled == 0)
)

# Exécution de la requête
result = query.run()
```

### Sélection et filtrage

```python
# Sélectionner des champs spécifiques
query = (
    frappe.qb.from_(Customer)
    .select(
        Customer.name,
        Customer.customer_name,
        Customer.territory
    )
)

# Utiliser des alias pour les champs
query = (
    frappe.qb.from_(Customer)
    .select(
        Customer.name.as_("id"),
        Customer.customer_name.as_("nom_client")
    )
)

# Filtrer avec différentes conditions
query = (
    frappe.qb.from_(Customer)
    .select(Customer.name, Customer.customer_name)
    .where(
        (Customer.territory == "France") &
        (Customer.disabled == 0)
    )
)

# Condition OR
query = (
    frappe.qb.from_(Customer)
    .select(Customer.name, Customer.customer_name)
    .where(
        (Customer.territory == "France") | 
        (Customer.territory == "Belgique")
    )
)

# Filtres avec opérateurs de comparaison
query = (
    frappe.qb.from_(Customer)
    .select(Customer.name)
    .where(Customer.creation > "2023-01-01")
    .where(Customer.modified.between("2023-01-01", "2023-12-31"))
)

# Conditions IN
regions = ["Europe", "Asie", "Amérique"]
query = (
    frappe.qb.from_(Customer)
    .select(Customer.name)
    .where(Customer.territory.isin(regions))
)

# Conditions LIKE
query = (
    frappe.qb.from_(Customer)
    .select(Customer.name)
    .where(Customer.customer_name.like("%SARL%"))
)
```

### Jointures

```python
# Définir les DocTypes pour la jointure
Customer = frappe.qb.DocType("Customer")
Address = frappe.qb.DocType("Address")
DynamicLink = frappe.qb.DocType("Dynamic Link")

# Jointure simple
query = (
    frappe.qb.from_(Customer)
    .select(
        Customer.name,
        Customer.customer_name,
        Address.address_line1,
        Address.city
    )
    .left_join(Address)
    .on(Address.name == Customer.customer_primary_address)
)

# Jointures multiples
query = (
    frappe.qb.from_(Customer)
    .select(
        Customer.name,
        Customer.customer_name,
        Address.address_line1,
        Address.city
    )
    .left_join(DynamicLink)
    .on(
        (DynamicLink.link_doctype == "Customer") &
        (DynamicLink.link_name == Customer.name) &
        (DynamicLink.parenttype == "Address")
    )
    .left_join(Address)
    .on(Address.name == DynamicLink.parent)
    .where(Address.is_primary_address == 1)
)
```

### Tri et regroupement

```python
# Tri simple
query = (
    frappe.qb.from_(Customer)
    .select(Customer.name)
    .orderby(Customer.creation, order=frappe.qb.desc)
)

# Tri multiple
query = (
    frappe.qb.from_(Customer)
    .select(Customer.name)
    .orderby(Customer.territory)
    .orderby(Customer.customer_name)
)

# Regroupement avec GROUP BY
SalesInvoice = frappe.qb.DocType("Sales Invoice")
SalesInvoiceItem = frappe.qb.DocType("Sales Invoice Item")

query = (
    frappe.qb.from_(SalesInvoiceItem)
    .select(
        SalesInvoiceItem.item_code,
        frappe.qb.functions.Sum(SalesInvoiceItem.amount).as_("total_amount")
    )
    .left_join(SalesInvoice)
    .on(SalesInvoice.name == SalesInvoiceItem.parent)
    .where(SalesInvoice.docstatus == 1)
    .groupby(SalesInvoiceItem.item_code)
    .orderby(frappe.qb.functions.Sum(SalesInvoiceItem.amount), order=frappe.qb.desc)
)
```

### Fonctions et agrégations

```python
# Utilisation des fonctions d'agrégation
SalesInvoice = frappe.qb.DocType("Sales Invoice")

# COUNT
count_query = (
    frappe.qb.from_(SalesInvoice)
    .select(frappe.qb.functions.Count(SalesInvoice.name).as_("total_invoices"))
    .where(SalesInvoice.status == "Paid")
)

# SUM, AVG, MAX, MIN
stats_query = (
    frappe.qb.from_(SalesInvoice)
    .select(
        frappe.qb.functions.Sum(SalesInvoice.grand_total).as_("total_amount"),
        frappe.qb.functions.Avg(SalesInvoice.grand_total).as_("average_amount"),
        frappe.qb.functions.Max(SalesInvoice.grand_total).as_("highest_invoice"),
        frappe.qb.functions.Min(SalesInvoice.grand_total).as_("lowest_invoice")
    )
    .where(SalesInvoice.docstatus == 1)
)

# GROUP_CONCAT (concaténer des valeurs)
query = (
    frappe.qb.from_(SalesInvoiceItem)
    .select(
        SalesInvoiceItem.parent,
        frappe.qb.functions.GROUP_CONCAT(SalesInvoiceItem.item_name).as_("all_items")
    )
    .groupby(SalesInvoiceItem.parent)
)
```

### Sous-requêtes

```python
# Utiliser une sous-requête dans un WHERE
SalesInvoice = frappe.qb.DocType("Sales Invoice")
Customer = frappe.qb.DocType("Customer")

# Sous-requête pour trouver les clients avec des factures
subquery = (
    frappe.qb.from_(SalesInvoice)
    .select(SalesInvoice.customer)
    .where(SalesInvoice.status == "Unpaid")
    .distinct()
)

# Requête principale utilisant la sous-requête
query = (
    frappe.qb.from_(Customer)
    .select(Customer.name, Customer.customer_name)
    .where(Customer.name.isin(subquery))
)

# Sous-requête dans un SELECT
PaymentEntry = frappe.qb.DocType("Payment Entry")
payment_subquery = (
    frappe.qb.from_(PaymentEntry)
    .select(frappe.qb.functions.Sum(PaymentEntry.paid_amount))
    .where(
        (PaymentEntry.party_type == "Customer") &
        (PaymentEntry.party == Customer.name) &
        (PaymentEntry.docstatus == 1)
    )
)

query = (
    frappe.qb.from_(Customer)
    .select(
        Customer.name,
        Customer.customer_name,
        payment_subquery.as_("total_payments")
    )
)
```

### HAVING et autres clauses

```python
# Utilisation de HAVING pour filtrer après GROUP BY
query = (
    frappe.qb.from_(SalesInvoiceItem)
    .select(
        SalesInvoiceItem.item_code,
        frappe.qb.functions.Sum(SalesInvoiceItem.amount).as_("total_amount")
    )
    .groupby(SalesInvoiceItem.item_code)
    .having(frappe.qb.functions.Sum(SalesInvoiceItem.amount) > 10000)
)

# Utilisation de DISTINCT
query = (
    frappe.qb.from_(SalesInvoice)
    .select(SalesInvoice.customer)
    .distinct()
)

# Limitation des résultats (LIMIT et OFFSET)
query = (
    frappe.qb.from_(Customer)
    .select(Customer.name)
    .orderby(Customer.creation, order=frappe.qb.desc)
    .limit(10)
    .offset(20)  # Pour la pagination
)
```

### Expressions conditionnelles (CASE)

```python
# Utilisation de CASE WHEN
from pypika.terms import Case

query = (
    frappe.qb.from_(SalesInvoice)
    .select(
        SalesInvoice.name,
        SalesInvoice.grand_total,
        Case()
            .when(SalesInvoice.grand_total > 10000, "Grand compte")
            .when(SalesInvoice.grand_total > 1000, "Compte moyen")
            .else_("Petit compte")
            .as_("type_client")
    )
)
```

### Formats de sortie

```python
# Exécution et formats de résultat
query = frappe.qb.from_(Customer).select(Customer.name, Customer.customer_name)

# Format par défaut (liste de tuples)
result = query.run()

# Format dictionnaire
result_dict = query.run(as_dict=True)

# Format liste simple (avec pluck=True)
result_list = query.select(Customer.name).run(pluck=True)

# Obtenir uniquement la première ligne
first_row = query.limit(1).run()
```

### Exemple complet d'une requête analytique

```python
def analyser_ventes_par_client(date_debut, date_fin, limit=10):
    """Analyse les ventes par client sur une période donnée
    
    Args:
        date_debut (str): Date de début au format YYYY-MM-DD
        date_fin (str): Date de fin au format YYYY-MM-DD
        limit (int, optional): Nombre maximum de résultats
        
    Returns:
        list: Liste des clients avec leur chiffre d'affaires
    """
    SalesInvoice = frappe.qb.DocType("Sales Invoice")
    SalesInvoiceItem = frappe.qb.DocType("Sales Invoice Item")
    Customer = frappe.qb.DocType("Customer")
    
    # Sous-requête pour obtenir le total des paiements
    PaymentEntry = frappe.qb.DocType("Payment Entry")
    payment_subquery = (
        frappe.qb.from_(PaymentEntry)
        .select(frappe.qb.functions.Sum(PaymentEntry.paid_amount))
        .where(
            (PaymentEntry.party_type == "Customer") &
            (PaymentEntry.party == Customer.name) &
            (PaymentEntry.docstatus == 1) &
            (PaymentEntry.posting_date.between(date_debut, date_fin))
        )
    )
    
    # Requête principale
    query = (
        frappe.qb.from_(SalesInvoice)
        .left_join(Customer)
        .on(SalesInvoice.customer == Customer.name)
        .select(
            Customer.name.as_("customer_id"),
            Customer.customer_name,
            Customer.customer_group,
            frappe.qb.functions.Count(SalesInvoice.name).as_("total_invoices"),
            frappe.qb.functions.Sum(SalesInvoice.grand_total).as_("total_amount"),
            frappe.qb.functions.Avg(SalesInvoice.grand_total).as_("average_invoice"),
            payment_subquery.as_("total_payments"),
            Case()
                .when(frappe.qb.functions.Sum(SalesInvoice.grand_total) > 50000, "VIP")
                .when(frappe.qb.functions.Sum(SalesInvoice.grand_total) > 10000, "Premium")
                .else_("Standard")
                .as_("segment")
        )
        .where(
            (SalesInvoice.docstatus == 1) &
            (SalesInvoice.posting_date.between(date_debut, date_fin))
        )
        .groupby(Customer.name)
        .orderby(frappe.qb.functions.Sum(SalesInvoice.grand_total), order=frappe.qb.desc)
        .limit(limit)
    )
    
    return query.run(as_dict=True)
```
