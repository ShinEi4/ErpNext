import frappe
from frappe import _

@frappe.whitelist()
def get_all_tables():
    """Récupérer toutes les tables disponibles dans la base de données"""
    frappe.only_for("System Manager")
    
    # Liste des tables à toujours conserver
    tables_to_keep = [
        "tabUser", "tabRole", "tabHas Role", "tabEmail Unsubscribe",
        "tabDocField", "tabDocPerm", "tabDocType", "tabModule Def",
        "tabDefaultValue", "tabSingles", "tabProperty Setter",
        "tabPage", "tabReport", "tabTranslation", "tabCommunication",
        "__Auth", "__NotificationLog", "tabNotification Settings",
        "tabNavbar Item", "tabNavbar Settings"
    ]
    
    # Obtenir toutes les tables dans la base de données
    all_tables = frappe.db.sql("SHOW TABLES")
    
    tables_list = []
    for table in all_tables:
        table_name = table[0]
        if not table_name.startswith('__') and table_name not in tables_to_keep:
            # Compter le nombre d'enregistrements dans chaque table
            count = frappe.db.sql(f"SELECT COUNT(*) FROM `{table_name}`")[0][0]
            
            # Obtenir une description simple de la table (si possible)
            description = ""
            if table_name.startswith('tab'):
                doctype = table_name[3:]  # Enlever 'tab' du début
                try:
                    description = frappe.get_meta(doctype).description or ""
                except:
                    pass
            
            tables_list.append({
                "name": table_name,
                "count": count,
                "description": description
            })
    
    # Trier par nom de table
    tables_list.sort(key=lambda x: x["name"])
    
    return tables_list

@frappe.whitelist()
def reset_selected_tables(tables):
    """Effacer les tables sélectionnées"""
    frappe.only_for("System Manager")
    
    if isinstance(tables, str):
        import json
        tables = json.loads(tables)
    
    if not tables:
        frappe.throw(_("Aucune table sélectionnée pour la suppression"))
    
    frappe.db.auto_commit_on_many_writes = True
    
    # Liste pour suivre les tables supprimées
    deleted_tables = []
    
    # Parcourir et supprimer chaque table sélectionnée
    for table_name in tables:
        try:
            frappe.db.sql(f"DELETE FROM `{table_name}`")
            frappe.db.sql(f"ALTER TABLE `{table_name}` AUTO_INCREMENT = 1")
            frappe.db.commit()
            deleted_tables.append(table_name)
        except Exception as e:
            frappe.log_error(f"Erreur lors de la suppression des données de la table {table_name}: {str(e)}")
    
    frappe.db.auto_commit_on_many_writes = False
    
    # Créer un message de succès avec la liste des tables supprimées
    message = _("Données supprimées avec succès: {}").format(len(deleted_tables))
    
    # Formatage du message pour l'affichage
    tables_html = "<br><br><b>" + _("Tables nettoyées") + ":</b><br>"
    
    # Organiser les tables par ordre alphabétique pour une meilleure lisibilité
    deleted_tables.sort()
    
    # Diviser en plusieurs colonnes pour une meilleure présentation
    columns = 3
    table_count = len(deleted_tables)
    
    tables_html += "<div style='column-count: 3; column-gap: 20px;'>"
    for table in deleted_tables:
        tables_html += f"<div>{table}</div>"
    tables_html += "</div>"
    
    frappe.msgprint(message + tables_html, _("Réinitialisation de la base de données terminée"))
    
    return True

# Garder la fonction précédente pour compatibilité
@frappe.whitelist()
def reset_all_tables():
    """Effacer toutes les tables sauf les utilisateurs"""
    frappe.only_for("System Manager")
    
    # Obtenir toutes les tables disponibles
    all_tables = get_all_tables()
    table_names = [table["name"] for table in all_tables]
    
    # Réinitialiser toutes les tables disponibles
    return reset_selected_tables(table_names)
