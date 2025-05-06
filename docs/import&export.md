# Guide d'importation et exportation de données CSV dans ERPNext

## Introduction

Ce guide explique comment importer et exporter des données CSV dans ERPNext, en se basant sur l'implémentation du module `import_db`.

## Importation de données CSV

### Principes fondamentaux

L'importation de données CSV dans ERPNext suit ces principes:

1. **Approche "tout ou rien"**: Soit toutes les données sont importées, soit aucune.
2. **Validation complète**: Toutes les données sont validées avant l'importation.
3. **Gestion des erreurs**: Les erreurs sont collectées et affichées à l'utilisateur.
4. **Création automatique**: Possibilité de créer automatiquement des entités manquantes.

### Structure d'un module d'importation

Un module d'importation complet comprend:

1. **Fichier JavaScript** (`*.js`) - Interface utilisateur pour le téléchargement des fichiers
2. **Fichier Python** (`*.py`) - Traitement des fichiers et logique d'importation

### Étapes d'implémentation

#### 1. Créer l'interface utilisateur

```javascript
frappe.pages['import-database'].on_page_load = function(wrapper) {
    var page = frappe.ui.make_app_page({
        parent: wrapper,
        title: __('Importation de Données'),
        single_column: true
    });
    
    // Initialiser le contrôleur
    new ImportDatabaseController(page);
};

class ImportDatabaseController {
    constructor(page) {
        this.page = page;
        this.setup();
    }
    
    setup() {
        // Créer l'interface d'upload de fichiers
        this.setupFileUploadSection();
        
        // Ajouter le bouton d'importation
        this.page.set_primary_action(__('Importer'), () => this.importData());
    }
    
    setupFileUploadSection() {
        // Créer les champs pour télécharger les fichiers CSV
        this.fileField = frappe.ui.form.make_control({
            parent: this.page.main.find('.file-field'),
            df: {
                fieldtype: 'Attach',
                fieldname: 'csv_file',
                label: __('Fichier CSV'),
                reqd: 1
            },
            render_input: true
        });
    }
    
    importData() {
        // Envoyer le fichier pour traitement
        frappe.call({
            method: 'app.module.page.page_name.backend.import_from_csv',
            args: {
                file_url: this.fileField.get_value()
            },
            callback: (r) => this.showResults(r.message)
        });
    }
}
```

#### 2. Traitement des données en Python

```python
import frappe
import csv
import io
from frappe import _

@frappe.whitelist()
def import_from_csv(file_url=None):
    """Importer des données depuis un fichier CSV"""
    results = {
        "success": False,
        "imported_count": 0,
        "errors": [],
        "info": []
    }
    
    try:
        # Récupérer le contenu du fichier
        file_doc = frappe.get_doc("File", {"file_url": file_url})
        content = file_doc.get_content()
        
        if isinstance(content, bytes):
            content = content.decode('utf-8')
        
        # Analyser le CSV
        csv_content = io.StringIO(content)
        reader = csv.reader(csv_content)
        rows = list(reader)
        
        # Valider les en-têtes
        if not validate_headers(rows[0], results):
            return results
        
        # Traiter les données ligne par ligne
        processed_data = process_data(rows[1:], results)
        
        # Commencer une transaction
        frappe.db.begin()
        
        # Insérer les données
        success = insert_data(processed_data, results)
        
        if not success:
            frappe.db.rollback()
            return results
        
        # Tout s'est bien passé, commit
        frappe.db.commit()
        results["success"] = True
        
        return results
    
    except Exception as e:
        frappe.db.rollback()
        results["errors"].append(str(e))
        return results

def validate_headers(headers, results):
    """Valider les en-têtes du fichier CSV"""
    required_headers = ["field1", "field2", "field3"]
    headers = [h.lower().strip() for h in headers]
    
    missing = [h for h in required_headers if h not in headers]
    
    if missing:
        results["errors"].append(f"En-têtes manquants: {', '.join(missing)}")
        return False
    
    return True

def process_data(rows, results):
    """Traiter les données du CSV"""
    processed_data = []
    
    for i, row in enumerate(rows, 2):  # Ligne 2 = première ligne de données
        try:
            # Extraire et valider les données
            field1 = row[0].strip()
            field2 = row[1].strip()
            field3 = row[2].strip()
            
            # Effectuer des validations
            if not field1:
                results["errors"].append(f"Ligne {i}: Champ 1 obligatoire manquant")
                continue
            
            # Ajouter aux données traitées
            processed_data.append({
                "field1": field1,
                "field2": field2,
                "field3": field3,
                "line": i
            })
            
        except Exception as e:
            results["errors"].append(f"Ligne {i}: Erreur de traitement - {str(e)}")
    
    return processed_data

def insert_data(data, results):
    """Insérer les données dans la base de données"""
    for item in data:
        try:
            # Créer et insérer un nouveau document
            doc = frappe.get_doc({
                "doctype": "YourDocType",
                "field1": item["field1"],
                "field2": item["field2"],
                "field3": item["field3"]
            })
            doc.insert()
            
            results["imported_count"] += 1
            
        except Exception as e:
            results["errors"].append(f"Ligne {item['line']}: Erreur d'insertion - {str(e)}")
            return False
    
    return True
```

### Bonnes pratiques pour l'importation

1. **Validation préalable**: Validez toujours les en-têtes et les données avant l'insertion.
2. **Transactions**: Utilisez `frappe.db.begin()` et `frappe.db.commit()/rollback()` pour gérer les transactions.
3. **Gestion des erreurs**: Collectez toutes les erreurs avec leurs numéros de ligne pour faciliter le débogage.
4. **Nettoyage des données**: Utilisez `strip()` pour nettoyer les espaces superflus.
5. **Données optionnelles**: Prévoyez des valeurs par défaut pour les champs optionnels.

## Exportation de données CSV

### Implémentation d'une fonction d'exportation

```python
@frappe.whitelist()
def export_to_csv(filters=None):
    """Exporter des données vers un fichier CSV"""
    try:
        # Récupérer les données à exporter
        data = get_data_for_export(filters)
        
        # Définir les en-têtes
        headers = ["Champ1", "Champ2", "Champ3"]
        
        # Créer le contenu CSV
        csv_content = io.StringIO()
        writer = csv.writer(csv_content)
        
        # Écrire l'en-tête
        writer.writerow(headers)
        
        # Écrire les données
        for row in data:
            writer.writerow([
                row.get("field1", ""),
                row.get("field2", ""),
                row.get("field3", "")
            ])
        
        # Créer le fichier temporaire
        csv_content.seek(0)
        frappe.response['result'] = csv_content.getvalue()
        frappe.response['type'] = 'csv'
        frappe.response['doctype'] = "export"
        
        return frappe.response
        
    except Exception as e:
        frappe.logger().error(f"Erreur d'exportation CSV: {str(e)}")
        frappe.throw(_("Erreur lors de l'exportation des données"))

def get_data_for_export(filters):
    """Récupérer les données à exporter"""
    # Construire les conditions de filtrage
    conditions = ""
    if filters:
        # Convertir les filtres en conditions SQL
        conditions = " WHERE " + " AND ".join([f"`{key}` = '{value}'" for key, value in filters.items()])
    
    # Exécuter la requête
    data = frappe.db.sql(f"""
        SELECT field1, field2, field3
        FROM `tabYourDocType`
        {conditions}
        ORDER BY creation DESC
    """, as_dict=1)
    
    return data
```

### Appel JavaScript pour l'exportation

```javascript
// Fonction pour déclencher l'exportation CSV
function exportData(filters) {
    frappe.call({
        method: 'app.module.page.page_name.backend.export_to_csv',
        args: {
            filters: filters
        },
        callback: function(r) {
            if (r.exc) {
                frappe.msgprint(__("Erreur lors de l'exportation"));
                return;
            }
            
            // Télécharger le fichier
            window.open('/api/method/frappe.utils.csvutils.get_csv_from_data?' + 
                'data=' + encodeURIComponent(JSON.stringify(r.message)) + 
                '&filename=' + encodeURIComponent('export.csv'));
        }
    });
}
```

## Gestion des DocTypes enfants (tables enfants)

La gestion des tables enfants dans les importations et exportations CSV nécessite une approche spécifique, car un document parent peut contenir plusieurs lignes d'enfants.

### Stratégies d'importation de tables enfants

Il existe plusieurs approches pour importer des DocTypes contenant des tables enfants:

#### 1. Approche avec un seul fichier CSV

Dans cette approche, chaque ligne du CSV peut contenir à la fois les informations du parent et des données pour une ligne enfant.

```python
@frappe.whitelist()
def import_sales_orders(file_url=None):
    """Importer des commandes client avec leurs articles"""
    results = {
        "success": False,
        "imported_count": 0,
        "errors": []
    }
    
    try:
        # Analyse du fichier CSV et validation des en-têtes...
        
        # Structure pour regrouper les lignes par document parent
        grouped_data = {}
        
        # Traiter les lignes
        for i, row in enumerate(rows[1:], 2):
            try:
                # Extraction des données du parent et de l'enfant
                so_name = row[0].strip()  # Identifiant unique de la commande
                customer = row[1].strip()
                delivery_date = row[2].strip()
                
                # Données de la ligne enfant (article)
                item_code = row[3].strip()
                qty = row[4].strip()
                rate = row[5].strip()
                
                # Vérification des données obligatoires...
                
                # Regrouper par commande
                if so_name not in grouped_data:
                    grouped_data[so_name] = {
                        "parent": {
                            "doctype": "Sales Order",
                            "customer": customer,
                            "delivery_date": delivery_date,
                            "items": []  # Table enfant
                        },
                        "lines": []  # Pour le suivi des lignes
                    }
                
                # Ajouter la ligne enfant
                grouped_data[so_name]["parent"]["items"].append({
                    "item_code": item_code,
                    "qty": float(qty),
                    "rate": float(rate)
                })
                grouped_data[so_name]["lines"].append(i)
                
            except Exception as e:
                results["errors"].append(f"Ligne {i}: {str(e)}")
        
        # Insérer les données groupées
        frappe.db.begin()
        
        for so_name, data in grouped_data.items():
            try:
                doc = frappe.get_doc(data["parent"])
                doc.insert()
                results["imported_count"] += 1
            except Exception as e:
                lines = ", ".join(map(str, data["lines"]))
                results["errors"].append(f"Commande {so_name} (lignes {lines}): {str(e)}")
        
        if results["errors"]:
            frappe.db.rollback()
        else:
            frappe.db.commit()
            results["success"] = True
        
        return results
        
    except Exception as e:
        frappe.db.rollback()
        results["errors"].append(str(e))
        return results
```

#### 2. Approche avec fichiers multiples

Dans cette approche, plusieurs fichiers CSV sont utilisés (un pour le parent, un pour chaque table enfant) avec des clés de liaison.

```python
@frappe.whitelist()
def import_purchase_orders_with_items(po_file=None, items_file=None):
    """Importer des bons de commande avec leurs articles depuis deux fichiers CSV distincts"""
    results = {
        "success": False,
        "imported_count": 0,
        "errors": []
    }
    
    try:
        # Charger et valider les deux fichiers...
        po_rows = load_csv_file(po_file)
        items_rows = load_csv_file(items_file)
        
        # Valider les en-têtes
        # ...
        
        # Traiter les commandes parent
        purchase_orders = {}
        for i, row in enumerate(po_rows[1:], 2):
            try:
                po_name = row[0].strip()  # Identifiant unique
                supplier = row[1].strip()
                transaction_date = row[2].strip()
                
                # Vérifications...
                
                purchase_orders[po_name] = {
                    "doctype": "Purchase Order",
                    "supplier": supplier,
                    "transaction_date": transaction_date,
                    "items": [],  # Table enfant
                    "line": i
                }
                
            except Exception as e:
                results["errors"].append(f"Commande (ligne {i}): {str(e)}")
        
        # Traiter les lignes d'articles (table enfant)
        for i, row in enumerate(items_rows[1:], 2):
            try:
                po_name = row[0].strip()  # Clé de liaison avec le parent
                item_code = row[1].strip()
                qty = row[2].strip()
                rate = row[3].strip()
                
                # Vérifications...
                
                # Vérifier si la commande parent existe
                if po_name not in purchase_orders:
                    results["errors"].append(f"Article (ligne {i}): Commande '{po_name}' non trouvée")
                    continue
                
                # Ajouter l'article à la commande
                purchase_orders[po_name]["items"].append({
                    "item_code": item_code,
                    "qty": float(qty),
                    "rate": float(rate)
                })
                
            except Exception as e:
                results["errors"].append(f"Article (ligne {i}): {str(e)}")
        
        # Insérer les données
        frappe.db.begin()
        
        for po_name, data in purchase_orders.items():
            try:
                # Vérifier qu'il y a des articles
                if not data["items"]:
                    results["errors"].append(f"Commande '{po_name}': Aucun article trouvé")
                    continue
                
                doc = frappe.get_doc(data)
                doc.insert()
                results["imported_count"] += 1
                
            except Exception as e:
                results["errors"].append(f"Commande '{po_name}' (ligne {data['line']}): {str(e)}")
        
        if results["errors"]:
            frappe.db.rollback()
        else:
            frappe.db.commit()
            results["success"] = True
        
        return results
        
    except Exception as e:
        frappe.db.rollback()
        results["errors"].append(str(e))
        return results
```

### Exportation de tables enfants

Pour l'exportation, plusieurs approches sont possibles:

#### 1. Format plat avec duplication des données parent

```python
@frappe.whitelist()
def export_sales_orders_flat(filters=None):
    """Exporter les commandes client avec leurs articles en format plat"""
    try:
        # Récupérer les commandes
        sales_orders = frappe.get_all("Sales Order", 
            filters=filters,
            fields=["name", "customer", "transaction_date"])
        
        # Préparer les données pour CSV
        data = [["Sales Order", "Customer", "Date", "Item Code", "Description", "Quantity", "Rate", "Amount"]]
        
        for so in sales_orders:
            # Récupérer les articles de la commande
            items = frappe.get_all("Sales Order Item",
                filters={"parent": so.name},
                fields=["item_code", "description", "qty", "rate", "amount"])
            
            # Si pas d'articles, ajouter une ligne vide pour le parent
            if not items:
                data.append([
                    so.name,
                    so.customer,
                    so.transaction_date,
                    "", "", "", "", ""
                ])
            else:
                # Ajouter une ligne pour chaque article avec les infos du parent répétées
                for item in items:
                    data.append([
                        so.name,
                        so.customer,
                        so.transaction_date,
                        item.item_code,
                        item.description,
                        item.qty,
                        item.rate,
                        item.amount
                    ])
        
        return data
        
    except Exception as e:
        frappe.log_error(frappe.get_traceback())
        frappe.throw(_("Erreur lors de l'exportation: ") + str(e))
```

#### 2. Format avec plusieurs fichiers CSV

```python
@frappe.whitelist()
def export_purchase_orders_with_items(filters=None):
    """Exporter les bons de commande et leurs articles dans deux fichiers CSV distincts"""
    try:
        # Récupérer les bons de commande
        purchase_orders = frappe.get_all("Purchase Order", 
            filters=filters,
            fields=["name", "supplier", "transaction_date", "grand_total"])
        
        # Données pour le fichier parent
        po_data = [["Purchase Order", "Supplier", "Date", "Grand Total"]]
        po_names = []
        
        for po in purchase_orders:
            po_data.append([
                po.name,
                po.supplier,
                po.transaction_date,
                po.grand_total
            ])
            po_names.append(po.name)
        
        # Données pour le fichier enfant
        items_data = [["Purchase Order", "Item Code", "Quantity", "Rate", "Amount"]]
        
        # Récupérer tous les articles pour ces commandes
        items = frappe.get_all("Purchase Order Item",
            filters={"parent": ["in", po_names]},
            fields=["parent", "item_code", "qty", "rate", "amount"])
        
        for item in items:
            items_data.append([
                item.parent,
                item.item_code,
                item.qty,
                item.rate,
                item.amount
            ])
        
        # Retourner les deux jeux de données
        return {
            "purchase_orders": po_data,
            "items": items_data
        }
        
    except Exception as e:
        frappe.log_error(frappe.get_traceback())
        frappe.throw(_("Erreur lors de l'exportation: ") + str(e))
```

### Bonnes pratiques pour les tables enfants

1. **Identifiants uniques**: Utilisez des identifiants clairs pour lier les enfants aux parents.
2. **Validation des relations**: Vérifiez que chaque enfant référence un parent valide.
3. **Format cohérent**: Documentez clairement le format attendu pour les fichiers CSV.
4. **Gestion des erreurs améliorée**: Indiquez précisément la ligne et le fichier source en cas d'erreur.
5. **Validation des données obligatoires**: Assurez-vous que chaque table enfant contient les données minimales requises.

### Exemple d'interface pour l'importation à tables multiples

```javascript
frappe.pages['multi-import'].on_page_load = function(wrapper) {
    var page = frappe.ui.make_app_page({
        parent: wrapper,
        title: __('Importation multi-tables'),
        single_column: true
    });
    
    // Ajouter les champs d'upload
    let parentField = $('<div class="parent-file-field mt-3"><h4>Fichier parent</h4></div>').appendTo(page.main);
    let childField = $('<div class="child-file-field mt-3"><h4>Fichier enfant</h4></div>').appendTo(page.main);
    
    // Créer les contrôles d'upload
    page.parentFileUpload = frappe.ui.form.make_control({
        parent: parentField,
        df: {
            fieldtype: 'Attach',
            fieldname: 'parent_file',
            label: __('Fichier des documents parents (CSV)'),
            reqd: 1
        },
        render_input: true
    });
    
    page.childFileUpload = frappe.ui.form.make_control({
        parent: childField,
        df: {
            fieldtype: 'Attach',
            fieldname: 'child_file',
            label: __('Fichier des éléments enfants (CSV)'),
            reqd: 1
        },
        render_input: true
    });
    
    // Ajouter le bouton d'importation
    page.set_primary_action(__('Importer'), () => {
        if (!page.parentFileUpload.get_value() || !page.childFileUpload.get_value()) {
            frappe.msgprint(__('Veuillez sélectionner les deux fichiers CSV requis'));
            return;
        }
        
        frappe.call({
            method: 'app.module.multi_import.import_with_children',
            args: {
                parent_file: page.parentFileUpload.get_value(),
                child_file: page.childFileUpload.get_value()
            },
            callback: (r) => {
                // Afficher les résultats...
            }
        });
    });
};
```

## Exemple complet: Importation/Exportation de fournisseurs

(Section existante...)

## Conclusion

L'importation et l'exportation de données CSV dans ERPNext sont des fonctionnalités puissantes qui permettent de gérer efficacement les données en masse. En suivant les bonnes pratiques et en assurant une validation adéquate, ces opérations peuvent être réalisées de manière fiable et sécurisée.

La gestion des tables enfants nécessite une attention particulière lors de la conception des processus d'importation et d'exportation, mais offre une flexibilité importante pour travailler avec des structures de données complexes.

Pour les développements plus complexes, n'hésitez pas à consulter l'implémentation du module `import_db` qui constitue un exemple complet d'importation de données avec validation et gestion des erreurs.