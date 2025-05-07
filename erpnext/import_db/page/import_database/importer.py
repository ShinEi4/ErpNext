# Copyright (c) 2023, Your Company and contributors
# For license information, please see license.txt

import frappe
from frappe import _
import csv
import io

@frappe.whitelist()
def import_all_data(material_request_file=None, supplier_file=None, rfq_file=None):
    """Importer toutes les données depuis les fichiers CSV fournis"""
    frappe.only_for("System Manager")
    
    results = {
        "success": False,
        "suppliers_imported": 0,
        "material_requests_imported": 0,
        "rfqs_imported": 0,
        "supplier_quotations_created": 0,
        "errors": [],
        "info": []
    }
    
    try:
        # Vérifier si tous les fichiers nécessaires sont fournis
        if not (material_request_file and supplier_file and rfq_file):
            results["errors"].append(_("Tous les fichiers sont requis pour l'importation."))
            return results
        
        # Récupérer les contenus des fichiers CSV
        try:
            supplier_data = parse_csv_file(supplier_file, "Supplier")
            mr_data = parse_csv_file(material_request_file, "Material Request")
            rfq_data = parse_csv_file(rfq_file, "Request for Quotation")
        except Exception as e:
            results["errors"].append(_("Erreur lors de la lecture des fichiers CSV: {0}").format(str(e)))
            return results
        
        # Valider les en-têtes
        validation_errors = []
        
        if not validate_supplier_headers(supplier_data[0], validation_errors):
            results["errors"].extend(validation_errors)
            return results
        
        if not validate_material_request_headers(mr_data[0], validation_errors):
            results["errors"].extend(validation_errors)
            return results
        
        if not validate_rfq_headers(rfq_data[0], validation_errors):
            results["errors"].extend(validation_errors)
            return results
        
        # Commencer une transaction
        frappe.db.begin()
        
        # Traiter les données dans l'ordre
        suppliers = process_suppliers(supplier_data[1:], results)
        material_requests = process_material_requests(mr_data[1:], results)
        rfqs = process_rfqs(rfq_data[1:], suppliers, material_requests, results)
        
        # Si l'un des processus a échoué ou s'il y a des erreurs, rollback
        if not suppliers or not material_requests or not rfqs or results["errors"]:
            frappe.db.rollback()
            
        
        # Insérer les données dans l'ordre
        suppliers_imported = insert_suppliers(suppliers, results)
        
        # Si échec, rollback et retourner les résultats
        if not suppliers_imported:
            frappe.db.rollback()
            
        
        material_requests_imported = insert_material_requests(material_requests, results)
        
        # Si échec, rollback et retourner les résultats
        if not material_requests_imported:
            frappe.db.rollback()
            
        
        rfqs_inserted = insert_rfqs(rfqs, results)
        
        # Si échec, rollback et retourner les résultats
        if not rfqs_inserted:
            frappe.db.rollback()
            
        
        # Créer les supplier quotations
        supplier_quotations_created = create_supplier_quotations(rfqs_inserted, results)
        
        # Si échec, rollback et retourner les résultats
        if not supplier_quotations_created:
            frappe.db.rollback()
            return results
        
        # Si nous arrivons ici, il n'y a pas eu d'erreurs, faire un commit
        frappe.db.commit()
        results["success"] = True
        
        return results
    
    except Exception as e:
        frappe.db.rollback()
        frappe.log_error(frappe.get_traceback())
        results["errors"].append(_("Erreur générale: {0}").format(str(e)))
        return results

@frappe.whitelist()
def api_import_data(supplier_csv_content=None, material_request_csv_content=None, rfq_csv_content=None):
    """
    Importer toutes les données depuis des contenus CSV fournis directement via API.
    Cette fonction est destinée aux clients API externes qui n'utilisent pas l'interface Frappe.
    
    Paramètres:
    - supplier_csv_content: Contenu CSV des fournisseurs (chaîne de caractères)
    - material_request_csv_content: Contenu CSV des demandes de matériel (chaîne de caractères)
    - rfq_csv_content: Contenu CSV des demandes de devis (chaîne de caractères)
    
    Retourne:
    - Dictionnaire avec les résultats de l'importation
    """
    frappe.only_for("System Manager")
    
    results = {
        "success": False,
        "suppliers_imported": 0,
        "material_requests_imported": 0,
        "rfqs_imported": 0,
        "supplier_quotations_created": 0,
        "errors": [],
        "info": []
    }
    
    try:
        # Vérifier si tous les contenus CSV nécessaires sont fournis
        if not (supplier_csv_content and material_request_csv_content and rfq_csv_content):
            results["errors"].append(_("Tous les contenus CSV sont requis pour l'importation."))
            return results
        
        # Analyser les contenus CSV
        try:
            supplier_data = parse_csv_content(supplier_csv_content, "Supplier")
            mr_data = parse_csv_content(material_request_csv_content, "Material Request")
            rfq_data = parse_csv_content(rfq_csv_content, "Request for Quotation")
        except Exception as e:
            results["errors"].append(_("Erreur lors de l'analyse des contenus CSV: {0}").format(str(e)))
            return results
        
        # Valider les en-têtes
        validation_errors = []
        
        if not validate_supplier_headers(supplier_data[0], validation_errors):
            results["errors"].extend(validation_errors)
            return results
        
        if not validate_material_request_headers(mr_data[0], validation_errors):
            results["errors"].extend(validation_errors)
            return results
        
        if not validate_rfq_headers(rfq_data[0], validation_errors):
            results["errors"].extend(validation_errors)
            return results
        
        # Commencer une transaction
        frappe.db.begin()
        
        # Traiter les données dans l'ordre
        suppliers = process_suppliers(supplier_data[1:], results)
        material_requests = process_material_requests(mr_data[1:], results)
        rfqs = process_rfqs(rfq_data[1:], suppliers, material_requests, results)
        
        # Si l'un des processus a échoué ou s'il y a des erreurs, rollback
        if not suppliers or not material_requests or not rfqs or results["errors"]:
            frappe.db.rollback()
            return results
        
        # Insérer les données dans l'ordre
        suppliers_imported = insert_suppliers(suppliers, results)
        
        # Si échec, rollback et retourner les résultats
        if not suppliers_imported:
            frappe.db.rollback()
            return results
        
        material_requests_imported = insert_material_requests(material_requests, results)
        
        # Si échec, rollback et retourner les résultats
        if not material_requests_imported:
            frappe.db.rollback()
            return results
        
        rfqs_inserted = insert_rfqs(rfqs, results)
        
        # Si échec, rollback et retourner les résultats
        if not rfqs_inserted:
            frappe.db.rollback()
            return results
        
        # Créer les supplier quotations
        supplier_quotations_created = create_supplier_quotations(rfqs_inserted, results)
        
        # Si échec, rollback et retourner les résultats
        if not supplier_quotations_created:
            frappe.db.rollback()
            return results
        
        # Si nous arrivons ici, il n'y a pas eu d'erreurs, faire un commit
        frappe.db.commit()
        results["success"] = True
        
        return results
    
    except Exception as e:
        frappe.db.rollback()
        frappe.log_error(frappe.get_traceback())
        results["errors"].append(_("Erreur générale: {0}").format(str(e)))
        return results

def parse_csv_file(file_url, file_type):
    """Analyser le contenu d'un fichier CSV"""
    try:
        # Récupérer le fichier
        file_doc = frappe.get_doc("File", {"file_url": file_url})
        
        if not file_doc:
            raise Exception(_("Fichier {0} non trouvé").format(file_type))
        
        content = file_doc.get_content()
        
        if isinstance(content, bytes):
            content = content.decode('utf-8')
        
        # Analyser le CSV
        csv_content = io.StringIO(content)
        reader = csv.reader(csv_content)
        rows = list(reader)
        
        if not rows or len(rows) < 2:  # Au moins l'en-tête et une ligne de données
            raise Exception(_("Le fichier {0} est vide ou ne contient pas de données.").format(file_type))
        
        return rows
        
    except Exception as e:
        raise Exception(_("Erreur lors de la lecture du fichier {0}: {1}").format(file_type, str(e)))

def parse_csv_content(csv_content, data_type):
    """
    Analyser le contenu CSV fourni directement
    
    Paramètres:
    - csv_content: Contenu CSV (chaîne de caractères)
    - data_type: Type de données pour les messages d'erreur
    
    Retourne:
    - Liste de lignes CSV analysées
    """
    try:
        if not csv_content:
            raise Exception(_("Contenu CSV vide pour {0}").format(data_type))
        
        # Analyser le CSV
        csv_stream = io.StringIO(csv_content)
        reader = csv.reader(csv_stream)
        rows = list(reader)
        
        if not rows or len(rows) < 2:  # Au moins l'en-tête et une ligne de données
            raise Exception(_("Le contenu CSV pour {0} est vide ou ne contient pas de données.").format(data_type))
        
        return rows
        
    except Exception as e:
        raise Exception(_("Erreur lors de l'analyse du contenu CSV pour {0}: {1}").format(data_type, str(e)))

def validate_supplier_headers(headers, errors):
    """Valider les en-têtes du fichier Supplier"""
    required_headers = ["supplier_name", "country", "type"]
    return validate_headers(headers, required_headers, "Supplier", errors)

def validate_material_request_headers(headers, errors):
    """Valider les en-têtes du fichier Material Request"""
    required_headers = ["date", "item_name", "item_groupe", "required_by", "quantity", "purpose", "target_warehouse", "ref"]
    return validate_headers(headers, required_headers, "Material Request", errors)

def validate_rfq_headers(headers, errors):
    """Valider les en-têtes du fichier Request for Quotation"""
    required_headers = ["ref_request_quotation", "supplier"]
    return validate_headers(headers, required_headers, "Request for Quotation", errors)

def validate_headers(headers, required, file_type, errors):
    """Vérifier que tous les en-têtes requis sont présents"""
    headers = [h.lower().strip() for h in headers]
    missing = []
    
    for header in required:
        if header not in headers:
            missing.append(header)
    
    if missing:
        errors.append(_("Fichier {0}: En-têtes manquants: {1}").format(
            file_type, ", ".join(missing)))
        return False
    
    return True

def process_suppliers(rows, results):
    """Traiter les données des fournisseurs"""
    suppliers = []
    
    for i, row in enumerate(rows, 2):  # Commencer à 2 pour inclure l'en-tête dans le compte des lignes
        try:
            if len(row) < 3:
                results["errors"].append(_("Supplier (ligne {0}): Données incomplètes").format(i))
                continue
                
            supplier_name = row[0].strip()
            country = row[1].strip()
            supplier_type = row[2].strip()
            
            if not supplier_name:
                results["errors"].append(_("Supplier (ligne {0}): Nom de fournisseur manquant").format(i))
                continue
            
            # Vérifier si le pays existe
            if country and not frappe.db.exists("Country", country):
                results["errors"].append(_("Supplier (ligne {0}): Le pays '{1}' n'existe pas").format(i, country))
                continue
            
            # Vérifier si le type est valide
            valid_types = ["Company", "Individual", "Partnership"]
            if supplier_type and supplier_type not in valid_types:
                results["errors"].append(_("Supplier (ligne {0}): Type de fournisseur '{1}' non valide. Doit être l'un des suivants: {2}").format(
                    i, supplier_type, ", ".join(valid_types)))
                continue
                
            # Ajouter à la liste des fournisseurs à insérer/mettre à jour
            suppliers.append({
                    "supplier_name": supplier_name,
                    "country": country,
                "supplier_type": supplier_type or "Company",  # Valeur par défaut
                "line": i
                })
                
        except Exception as e:
            results["errors"].append(_("Supplier (ligne {0}): Erreur lors du traitement: {1}").format(
                i, str(e)))
    
    return suppliers

def find_or_create_warehouse(warehouse_name, company, company_abbr, results, line_number, file_type):
    """Trouver ou créer un entrepôt"""
    if not warehouse_name:
        return None
        
    # Vérifier si l'entrepôt existe déjà exactement avec ce nom
    if frappe.db.exists("Warehouse", warehouse_name):
        return warehouse_name
        
    # Vérifier si c'est un entrepôt qui existe avec le suffixe de la société
    possible_warehouse = f"{warehouse_name} - {company_abbr}"
    
    if frappe.db.exists("Warehouse", possible_warehouse):
        return possible_warehouse
    
    # Au lieu de chercher d'autres entrepôts, on va créer celui demandé
    try:
        # Vérifier si "All Warehouses" existe
        all_warehouse = frappe.db.get_value("Warehouse", {"warehouse_name": "All Warehouses", "company": company})
        
        if not all_warehouse:
            # Créer le parent "All Warehouses" si nécessaire
            all_warehouse_doc = frappe.new_doc("Warehouse")
            all_warehouse_doc.warehouse_name = "All Warehouses"
            all_warehouse_doc.company = company
            all_warehouse_doc.is_group = 1
            all_warehouse_doc.parent_warehouse = ""
            all_warehouse_doc.insert()
            all_warehouse = all_warehouse_doc.name
        
        # Créer l'entrepôt demandé
        new_warehouse = frappe.new_doc("Warehouse")
        new_warehouse.warehouse_name = warehouse_name
        new_warehouse.company = company
        new_warehouse.is_group = 0
        new_warehouse.parent_warehouse = all_warehouse
        new_warehouse.insert()
        
        # Utiliser le nouveau nom complet qui inclut généralement le suffixe de la société
        new_warehouse_name = new_warehouse.name
        
        results["info"].append(_("{0} (ligne {1}): Nouvel entrepôt '{2}' créé").format(
            file_type, line_number, new_warehouse_name))
        
        # Définir comme entrepôt par défaut si aucun n'est défini
        default_warehouse = frappe.db.get_single_value("Stock Settings", "default_warehouse")
        if not default_warehouse:
            stock_settings = frappe.get_doc("Stock Settings")
            stock_settings.default_warehouse = new_warehouse_name
            stock_settings.save()
            results["info"].append(_("{0} (ligne {1}): L'entrepôt '{2}' a été défini comme entrepôt par défaut").format(
                file_type, line_number, new_warehouse_name))
        
        return new_warehouse_name
        
    except Exception as e:
        # Si la création échoue, on cherche des alternatives comme avant
        results["errors"].append(_("{0} (ligne {1}): Erreur lors de la création de l'entrepôt '{2}': {3}").format(
            file_type, line_number, warehouse_name, str(e)))
        
        # Chercher un entrepôt existant comme solution de secours
        default_warehouse = frappe.db.get_single_value("Stock Settings", "default_warehouse")
        if default_warehouse and frappe.db.exists("Warehouse", default_warehouse):
            results["info"].append(_("{0} (ligne {1}): Utilisation de l'entrepôt par défaut '{2}' au lieu de '{3}'").format(
                file_type, line_number, default_warehouse, warehouse_name))
            return default_warehouse
            
        # Chercher l'entrepôt "Stores" de la société
        stores_warehouse = frappe.db.get_value("Warehouse", {"warehouse_name": "Stores", "company": company})
        if stores_warehouse:
            results["info"].append(_("{0} (ligne {1}): Utilisation de l'entrepôt '{2}' au lieu de '{3}'").format(
                file_type, line_number, stores_warehouse, warehouse_name))
            return stores_warehouse
            
        # Si aucun entrepôt n'est trouvé, utiliser le premier entrepôt de la société
        warehouses = frappe.get_all("Warehouse", 
            filters={"company": company, "is_group": 0},
            limit=1)
        
        if warehouses:
            results["info"].append(_("{0} (ligne {1}): Utilisation de l'entrepôt '{2}' au lieu de '{3}'").format(
                file_type, line_number, warehouses[0].name, warehouse_name))
            return warehouses[0].name
        
        # Si vraiment aucun entrepôt n'est disponible, créer "Stores" comme dernier recours
        try:
            new_warehouse = frappe.new_doc("Warehouse")
            new_warehouse.warehouse_name = "Stores"
            new_warehouse.company = company
            new_warehouse.is_group = 0
            new_warehouse.parent_warehouse = all_warehouse
            new_warehouse.insert()
            
            stock_settings = frappe.get_doc("Stock Settings")
            stock_settings.default_warehouse = new_warehouse.name
            stock_settings.save()
            
            results["info"].append(_("{0} (ligne {1}): Nouvel entrepôt '{2}' créé et défini comme entrepôt par défaut").format(
                file_type, line_number, new_warehouse.name))
            return new_warehouse.name
        except Exception as e2:
            results["errors"].append(_("{0} (ligne {1}): Impossible de créer l'entrepôt de secours: {2}").format(
                file_type, line_number, str(e2)))
            return None

def find_or_create_item_group(item_group_name, company, warehouse, results, line_number):
    """Trouver ou créer un groupe d'articles"""
    if not item_group_name:
        return "All Item Groups"
        
    if frappe.db.exists("Item Group", item_group_name):
        return item_group_name
        
    try:
        # Créer un nouveau groupe d'articles
        new_item_group = frappe.new_doc("Item Group")
        new_item_group.item_group_name = item_group_name
        new_item_group.parent_item_group = "All Item Groups"
        new_item_group.is_group = 0
        
        # Ajouter les paramètres par défaut pour la société
        new_item_group.append("item_group_defaults", {
            "company": company,
            "default_warehouse": warehouse
        })
        
        new_item_group.insert()
        
        results["info"].append(_("Material Request (ligne {0}): Nouveau groupe d'articles '{1}' créé").format(
            line_number, item_group_name))
        return item_group_name
        
    except Exception as e:
        results["errors"].append(_("Material Request (ligne {0}): Impossible de créer le groupe d'articles '{1}': {2}").format(
            line_number, item_group_name, str(e)))
        return None

def find_or_create_item(item_name, item_group, company, warehouse, results, line_number):
    """Trouver ou créer un article"""
    if frappe.db.exists("Item", {"name": item_name}):
        return item_name
        
    if frappe.db.exists("Item", {"item_name": item_name}):
        return frappe.db.get_value("Item", {"item_name": item_name}, "name")
        
    try:
        # Créer un nouvel article
        new_item = frappe.new_doc("Item")
        new_item.item_code = item_name
        new_item.item_name = item_name
        new_item.description = item_name
        new_item.item_group = item_group
        new_item.stock_uom = "Nos"
        new_item.is_stock_item = 1
        
        # Ajouter les paramètres par défaut pour la société
        new_item.append("item_defaults", {
            "company": company,
            "default_warehouse": warehouse
        })
        
        new_item.insert()
        
        results["info"].append(_("Material Request (ligne {0}): Nouvel article '{1}' créé").format(
            line_number, item_name))
        return new_item.name
        
    except Exception as e:
        results["errors"].append(_("Material Request (ligne {0}): Impossible de créer l'article '{1}': {2}").format(
            line_number, item_name, str(e)))
        return None

def process_material_requests(rows, results):
    """Traiter les données des demandes de matériel"""
    material_requests = {}
    company = frappe.defaults.get_user_default("Company")
    company_abbr = frappe.db.get_value("Company", company, "abbr")
    
    for i, row in enumerate(rows, 2):
        try:
            if len(row) < 8:
                results["errors"].append(_("Material Request (ligne {0}): Données incomplètes").format(i))
                continue
                
            date_str = row[0].strip()
            item_name = row[1].strip()
            item_group = row[2].strip()
            required_by_str = row[3].strip()
            quantity = row[4].strip()
            purpose = row[5].strip()
            target_warehouse = row[6].strip()
            ref = row[7].strip()
            
            # Valider et formater les dates
            date = validate_and_format_date(date_str, results, "Material Request", i, "date")
            if not date:
                continue
                
            required_by = validate_and_format_date(required_by_str, results, "Material Request", i, "required_by")
            if not required_by:
                continue
            
            # Valider les données
            if not (item_name and quantity and purpose and ref):
                results["errors"].append(_("Material Request (ligne {0}): Données obligatoires manquantes").format(i))
                continue
                
            try:
                quantity = float(quantity)
                if quantity <= 0:
                    results["errors"].append(_("Material Request (ligne {0}): La quantité doit être positive").format(i))
                    continue
            except ValueError:
                results["errors"].append(_("Material Request (ligne {0}): La quantité '{1}' n'est pas un nombre valide").format(i, quantity))
                continue
            
            # Vérifier si le type de demande est valide
            valid_purposes = ["Purchase", "Material Transfer", "Material Issue", "Manufacture", "Subcontracting", "Customer Provided"]
            if purpose not in valid_purposes:
                results["errors"].append(_("Material Request (ligne {0}): Le type de demande '{1}' n'est pas valide. Doit être l'un des suivants: {2}").format(
                    i, purpose, ", ".join(valid_purposes)))
                continue
            
            # Trouver ou créer l'entrepôt
            warehouse = find_or_create_warehouse(target_warehouse, company, company_abbr, results, i, "Material Request")
            if not warehouse:
                continue
            
            # Trouver ou créer le groupe d'articles
            item_group_code = find_or_create_item_group(item_group, company, warehouse, results, i)
            if not item_group_code:
                continue
                
            # Trouver ou créer l'article
            item_code = find_or_create_item(item_name, item_group_code, company, warehouse, results, i)
            if not item_code:
                continue
                
            # Ajouter à la liste des demandes à insérer
            if ref not in material_requests:
                material_requests[ref] = {
                    "doc_data": {
                    "doctype": "Material Request",
                        "title": f"Import - {ref}",
                    "transaction_date": date,
                    "schedule_date": required_by,
                    "material_request_type": purpose,
                        "items": [],
                        "company": company
                    },
                    "line": i
                }
            
            material_requests[ref]["doc_data"]["items"].append({
                "item_code": item_code,
                "qty": quantity,
                "schedule_date": required_by,
                "warehouse": warehouse
            })
                
        except Exception as e:
            results["errors"].append(_("Material Request (ligne {0}): Erreur lors du traitement: {1}").format(i, str(e)))
    
    return material_requests

def process_rfqs(rows, suppliers, material_requests, results):
    """Traiter les données des demandes de devis"""
    rfqs = {}
    company = frappe.defaults.get_user_default("Company")
    today = frappe.utils.today()  # Date du jour au format YYYY-MM-DD
    
    # Créer un dictionnaire de fournisseurs pour accès rapide
    supplier_map = {s["supplier_name"]: s for s in suppliers}
    
    # Vérifier que tous les Material Requests référencés existent
    mr_refs = set(material_requests.keys())
    
    for i, row in enumerate(rows, 2):
        try:
            if len(row) < 2:
                results["errors"].append(_("Request for Quotation (ligne {0}): Données incomplètes").format(i))
                continue
                
            ref_request = row[0].strip()
            supplier_name = row[1].strip()
            
            # Valider les données
            if not (ref_request and supplier_name):
                results["errors"].append(_("Request for Quotation (ligne {0}): Données obligatoires manquantes").format(i))
                continue
            
            # Vérifier si le fournisseur existe dans notre liste de fournisseurs à importer
            if supplier_name not in supplier_map and not frappe.db.exists("Supplier", {"supplier_name": supplier_name}):
                results["errors"].append(_("Request for Quotation (ligne {0}): Le fournisseur '{1}' n'existe pas").format(i, supplier_name))
                continue
            
            # Vérifier si la demande de matériel existe dans notre liste de demandes à importer ou dans la base de données
            mr_exists = False
            
            # Vérifier dans notre liste de MRs à importer
            if ref_request in mr_refs:
                mr_exists = True
                mr_ref = ref_request  # Stocke la référence pour un usage ultérieur
            else:
                # Vérifier dans la base de données avec le titre exact
                mr_title = f"Import - {ref_request}"
                mr_exists_db = frappe.db.exists("Material Request", {"title": mr_title})
                
                if mr_exists_db:
                    mr_exists = True
                    mr_ref = ref_request
                else:
                    # Essayer de trouver directement par nom/ID
                    mr_exists_direct = frappe.db.exists("Material Request", ref_request)
                    if mr_exists_direct:
                        mr_exists = True
                        mr_ref = ref_request
            
            if not mr_exists:
                results["errors"].append(_("Request for Quotation (ligne {0}): La demande de matériel '{1}' n'existe pas").format(i, ref_request))
                continue
            
            # Préparer les données pour l'insertion de la RFQ
            if ref_request not in rfqs:
                rfqs[ref_request] = {
                    "doc_data": {
                        "doctype": "Request for Quotation",
                        "transaction_date": today,
                        "suppliers": [],
                        "items": [],
                        "company": company,
                        "message_for_supplier": _("Veuillez nous fournir votre meilleur prix pour les articles listés ci-dessous."),  # Message par défaut
                    },
                    "suppliers": set(),  # Ensemble pour éviter les doublons
                    "material_request_ref": mr_ref,  # Stocker la référence pour retrouver le bon MR plus tard
                    "line": i
                }
            
            # Ajouter le fournisseur s'il n'est pas déjà dans la liste
            if supplier_name not in rfqs[ref_request]["suppliers"]:
                rfqs[ref_request]["suppliers"].add(supplier_name)
                rfqs[ref_request]["doc_data"]["suppliers"].append({
                    "supplier_name": supplier_name
                })
            
        except Exception as e:
            results["errors"].append(_("Request for Quotation (ligne {0}): Erreur lors du traitement: {1}").format(i, str(e)))
    
    return rfqs

def insert_suppliers(suppliers, results):
    """Insérer les fournisseurs dans la base de données"""
    for supplier_data in suppliers:
        try:
            supplier_name = supplier_data["supplier_name"]
            line = supplier_data["line"]
            
            # Vérifier si le fournisseur existe déjà
            exists = frappe.db.exists("Supplier", {"supplier_name": supplier_name})
            
            if exists:
                # Mettre à jour le fournisseur existant
                supplier = frappe.get_doc("Supplier", {"supplier_name": supplier_name})
                supplier.country = supplier_data["country"]
                supplier.supplier_type = supplier_data["supplier_type"]
                supplier.save()
            else:
                # Créer un nouveau fournisseur
                supplier = frappe.get_doc({
                    "doctype": "Supplier",
                    "supplier_name": supplier_name,
                    "country": supplier_data["country"],
                    "supplier_type": supplier_data["supplier_type"]
                })
                supplier.insert()
            
            results["suppliers_imported"] += 1
            
        except Exception as e:
            results["errors"].append(_("Supplier (ligne {0}): Erreur lors de l'insertion du fournisseur '{1}': {2}").format(
                line, supplier_name, str(e)))
            return False
    
    return True

def insert_material_requests(material_requests, results):
    """Insérer les demandes de matériel dans la base de données"""
    material_requests_docs = {}
    
    for ref, mr_data in material_requests.items():
        try:
            # Créer et insérer la demande de matériel
            mr_doc = frappe.get_doc(mr_data["doc_data"])
            mr_doc.insert()
            mr_doc.submit()
            
            # Stocker le document créé pour référence ultérieure
            material_requests_docs[ref] = mr_doc
            
            results["material_requests_imported"] += 1
            
        except Exception as e:
            results["errors"].append(_("Material Request (ligne {0}): Erreur lors de l'insertion de la demande '{1}': {2}").format(
                mr_data["line"], ref, str(e)))
            return False
    
    return material_requests_docs

def insert_rfqs(rfqs, results):
    """Insérer les demandes de devis dans la base de données"""
    rfqs_inserted = {}
    
    for ref, rfq_data in rfqs.items():
        try:
            # Obtenir les informations de la demande de matériel
            material_request = None
            mr_ref = rfq_data.get("material_request_ref", ref)
            
            # Essayer d'abord avec le titre
            mr_title = f"Import - {mr_ref}"
            mr_by_title = frappe.db.get_value("Material Request", {"title": mr_title}, "name")
            
            if mr_by_title:
                material_request = frappe.get_doc("Material Request", mr_by_title)
            else:
                # Sinon, essayer directement avec la référence
                try:
                    material_request = frappe.get_doc("Material Request", mr_ref)
                except frappe.exceptions.DoesNotExistError:
                    results["errors"].append(_("Request for Quotation (ligne {0}): Impossible de trouver la demande de matériel '{1}'").format(
                        rfq_data["line"], mr_ref))
                    return False
            
            # Ajouter les articles de la demande de matériel
            for item in material_request.items:
                # Récupérer des informations supplémentaires sur l'article
                item_doc = frappe.get_doc("Item", item.item_code)
                stock_uom = item_doc.stock_uom
                
                # Obtenir le facteur de conversion UOM si l'unité de l'article est différente de l'unité de stock
                conversion_factor = 1.0
                if hasattr(item, 'uom') and item.uom != stock_uom:
                    conversion_factor = frappe.db.get_value("UOM Conversion Detail",
                        {"parent": item.item_code, "uom": item.uom}, "conversion_factor") or 1.0
                
                rfq_data["doc_data"]["items"].append({
                    "item_code": item.item_code,
                    "qty": item.qty,
                    "schedule_date": item.schedule_date,
                    "warehouse": item.warehouse,
                    "material_request": material_request.name,
                    "material_request_item": item.name,
                    "stock_uom": stock_uom,
                    "uom": item.uom if hasattr(item, 'uom') else stock_uom,
                    "conversion_factor": conversion_factor
                })
            
            # Pour chaque fournisseur, s'assurer qu'il a le bon format avec l'ID du fournisseur
            for i, supplier in enumerate(rfq_data["doc_data"]["suppliers"]):
                supplier_name = supplier["supplier_name"]
                supplier_doc = frappe.get_doc("Supplier", {"supplier_name": supplier_name})
                rfq_data["doc_data"]["suppliers"][i] = {
                    "supplier": supplier_doc.name,
                    "supplier_name": supplier_doc.supplier_name
                }
            
            # Créer et insérer la demande de devis
            rfq_doc = frappe.get_doc(rfq_data["doc_data"])
            rfq_doc.insert()
            rfq_doc.submit()
            
            rfqs_inserted[ref] = rfq_doc
            results["rfqs_imported"] += 1
            
        except Exception as e:
            results["errors"].append(_("Request for Quotation (ligne {0}): Erreur lors de l'insertion de la demande '{1}': {2}").format(
                rfq_data["line"], ref, str(e)))
            return False
    
    return rfqs_inserted

def create_supplier_quotations(rfqs_inserted, results):
    """Créer des devis fournisseurs à partir des demandes de devis"""
    for ref, rfq_doc in rfqs_inserted.items():
        try:
            for supplier in rfq_doc.suppliers:
                sq = frappe.new_doc("Supplier Quotation")
                sq.supplier = supplier.supplier
                sq.company = rfq_doc.company
                
                # Copier les articles de la demande de devis
                for item in rfq_doc.items:
                    sq.append("items", {
                        "item_code": item.item_code,
                        "qty": item.qty,
                        "schedule_date": item.schedule_date,
                        "warehouse": item.warehouse,
                        "request_for_quotation": rfq_doc.name,
                        "request_for_quotation_item": item.name,
                        "material_request": item.material_request,
                        "material_request_item": item.material_request_item,
                        "stock_uom": item.stock_uom,
                        "uom": item.uom,
                        "conversion_factor": item.conversion_factor
                    })
                
                sq.insert()
                results["supplier_quotations_created"] += 1
                
        except Exception as e:
            results["errors"].append(_("Erreur lors de la création du devis fournisseur pour {0} (RFQ: {1}): {2}").format(
                supplier.supplier_name, ref, str(e)))
            return False
    
    return True

def validate_and_format_date(date_str, results, file_type, line_number, field_name):
    """Valide et formate une date au format YYYY-MM-DD en supposant un format d'entrée dd/mm/yyyy"""
    try:
        # Vérifier si la date est déjà au bon format (YYYY-MM-DD)
        if len(date_str) == 10 and date_str[4] == '-' and date_str[7] == '-':
            year = int(date_str[0:4])
            month = int(date_str[5:7])
            day = int(date_str[8:10])
            
            # Vérifier si la date est valide
            import datetime
            datetime.date(year, month, day)
            return date_str
        
        # Vérifier si le format est dd/mm/yyyy
        if len(date_str) == 10 and date_str[2] == '/' and date_str[5] == '/':
            day = int(date_str[0:2])
            month = int(date_str[3:5])
            year = int(date_str[6:10])
            
            # Vérifier si la date est valide
            import datetime
            date_obj = datetime.date(year, month, day)
            
            # Convertir au format YYYY-MM-DD
            formatted_date = date_obj.strftime("%Y-%m-%d")
            
            results["info"].append(_("{0} (ligne {1}): Date '{2}' (format dd/mm/yyyy) reformatée en '{3}'").format(
                file_type, line_number, date_str, formatted_date))
            
            return formatted_date
        
        # Si ce n'est pas au format dd/mm/yyyy, essayer d'autres formats en précisant le format français
        from dateutil import parser
        from frappe.utils import formatdate
        
        # Forcer l'interprétation en format européen (jour/mois/année)
        try:
            # Parser avec dayfirst=True pour interpréter comme dd/mm/yyyy
            parsed_date = parser.parse(date_str, dayfirst=True)
            
            # Convertir au format YYYY-MM-DD
            formatted_date = formatdate(parsed_date, "yyyy-mm-dd")
            
            results["info"].append(_("{0} (ligne {1}): Date '{2}' (format européen) reformatée en '{3}'").format(
                file_type, line_number, date_str, formatted_date))
            
            return formatted_date
        except:
            # Si l'interprétation en format européen échoue, essayer avec le format américain
            parsed_date = parser.parse(date_str)
            formatted_date = formatdate(parsed_date, "yyyy-mm-dd")
            
            results["info"].append(_("{0} (ligne {1}): Date '{2}' reformatée en '{3}'").format(
                file_type, line_number, date_str, formatted_date))
            
            return formatted_date
            
    except Exception as e:
        results["errors"].append(_("{0} (ligne {1}): Format de {2} invalide '{3}': {4}").format(
            file_type, line_number, field_name, date_str, str(e)))
        return None
