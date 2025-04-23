frappe.pages['reset-database'].on_page_load = function(wrapper) {
	var page = frappe.ui.make_app_page({
		parent: wrapper,
		title: __('Réinitialisation de la Base de Données'),
		single_column: true
	});
	
	// Initialiser le contrôleur
	new ResetDatabaseController(page);
};

class ResetDatabaseController {
	constructor(page) {
		this.page = page;
		this.selectedTables = [];
		this.tables = [];
		
		this.setup();
		this.loadTables();
	}
	
	setup() {
		// Ajouter des boutons d'action
		this.page.set_primary_action(__('Vider les tables sélectionnées'), () => this.resetSelectedTables(), 'octicon octicon-sync');
		this.page.set_secondary_action(__('Vider toutes les tables'), () => this.resetAllTables());
		
		// Ajouter les sections
		this.setupWarningSection();
		this.setupTableSelectionSection();
	}
	
	setupWarningSection() {
		// Utiliser une approche plus simple pour créer les avertissements
		let warning = $(`
			<div class="alert alert-warning">
				<h4>${__('Attention')}</h4>
				<p>${__('Cette page vous permet de réinitialiser des tables spécifiques de la base de données en conservant les informations des utilisateurs.')}</p>
				<p>${__('Utilisez cette fonctionnalité avec précaution car elle supprimera des données importantes.')}</p>
			</div>
		`);
		
		// Informations importantes - n'utilisons pas get_alert car il pourrait ne pas exister
		let info = $(`
			<div class="alert alert-info">
				<h5>${__('Informations importantes')}</h5>
				<ul>
					<li>${__('Les données des tables sélectionnées seront supprimées')}</li>
					<li>${__('Cette action est irréversible')}</li>
					<li>${__('Effectuez une sauvegarde avant de procéder à cette opération')}</li>
				</ul>
			</div>
		`);
		
		$(warning).appendTo(this.page.main);
		$(info).appendTo(this.page.main);
	}
	
	setupTableSelectionSection() {
		// Section de sélection des tables
		let tableSection = $(`<div class="tables-selection mt-4"></div>`).appendTo(this.page.main);
		
		// Créer un champ de recherche standard
		let searchGroup = $(`
			<div class="form-group">
				<label class="control-label">${__('Rechercher des tables')}</label>
				<input type="text" class="form-control table-search" placeholder="${__('Nom de table...')}">
			</div>
		`).appendTo(tableSection);
		
		this.searchField = searchGroup.find('.table-search');
		this.searchField.on('input', () => this.filterTables());
		
		// Ajouter boutons de sélection
		let buttonGroup = $(`<div class="btn-group mt-2 mb-4"></div>`).appendTo(tableSection);
		
		$(`<button class="btn btn-default btn-sm">${__('Sélectionner tout')}</button>`)
			.appendTo(buttonGroup)
			.on('click', () => this.selectAll());
			
		$(`<button class="btn btn-default btn-sm">${__('Désélectionner tout')}</button>`)
			.appendTo(buttonGroup)
			.on('click', () => this.deselectAll());
		
		// Container pour la liste des tables
		this.tablesContainer = $(`<div class="tables-container frappe-card p-3"></div>`).appendTo(tableSection);
	}
	
	loadTables() {
		// Afficher un message de chargement
		let loadingMessage = $(`<div class="text-muted text-center p-5">${__('Chargement des tables...')}</div>`).appendTo(this.tablesContainer);
		
		frappe.call({
			method: 'erpnext.reset_database.page.reset_database.reset_database.get_all_tables',
			callback: (r) => {
				loadingMessage.remove();
				if(r.message) {
					this.tables = r.message;
					this.renderTables();
				}
			}
		});
	}
	
	renderTables() {
		this.tablesContainer.empty();
		this.selectedTables = [];
		
		// Grouper les tables par modules
		let moduleGroups = this.groupTablesByModule();
		
		// Créer des sections pour chaque module
		Object.keys(moduleGroups).sort().forEach(module => {
			let moduleSection = $(`
				<div class="module-section mb-3">
					<h6 class="module-title">${module} (${moduleGroups[module].length})</h6>
					<div class="table-list row"></div>
				</div>
			`).appendTo(this.tablesContainer);
			
			let tableList = moduleSection.find('.table-list');
			
			// Créer une case à cocher standard pour chaque table
			moduleGroups[module].forEach(table => {
				let tableCol = $(`<div class="col-md-4 table-item mb-2"></div>`).appendTo(tableList);
				
				let checkboxItem = $(`
					<div class="checkbox">
						<label>
							<input type="checkbox" data-table="${table.name}"> 
							${table.name} <span class="text-muted">(${table.count})</span>
							${table.description ? '<small class="text-muted d-block">' + table.description + '</small>' : ''}
						</label>
					</div>
				`).appendTo(tableCol);
				
				let checkbox = checkboxItem.find('input[type="checkbox"]');
				checkbox.on('change', () => {
					if(checkbox.is(':checked')) {
						if(!this.selectedTables.includes(table.name)) {
							this.selectedTables.push(table.name);
						}
					} else {
						this.selectedTables = this.selectedTables.filter(t => t !== table.name);
					}
					this.updateTitle();
				});
				
				// Stocker la référence à la case à cocher
				table.checkbox = checkbox;
			});
		});
		
		this.updateTitle();
	}
	
	groupTablesByModule() {
		let modules = {};
		
		this.tables.forEach(table => {
			let module = "Autres";
			
			// Essayer de déterminer le module à partir du nom de la table
			if (table.name.startsWith('tab')) {
				let parts = table.name.substr(3).split('_');
				if (parts.length > 1) {
					module = parts[0].charAt(0).toUpperCase() + parts[0].slice(1);
				}
			}
			
			if (!modules[module]) {
				modules[module] = [];
			}
			modules[module].push(table);
		});
		
		return modules;
	}
	
	filterTables() {
		let searchTerm = this.searchField.val().toLowerCase();
		
		this.tables.forEach(table => {
			let tableItem = table.checkbox.closest('.table-item');
			if(table.name.toLowerCase().includes(searchTerm)) {
				tableItem.show();
			} else {
				tableItem.hide();
			}
		});
	}
	
	selectAll() {
		$('.table-item:visible input[type="checkbox"]').prop('checked', true).trigger('change');
	}
	
	deselectAll() {
		$('.table-item:visible input[type="checkbox"]').prop('checked', false).trigger('change');
	}
	
	updateTitle() {
		// Mettre à jour le compteur de tables sélectionnées
		this.page.set_title(
			__('Réinitialisation de la Base de Données') + 
			` <span class="text-muted">(${this.selectedTables.length} ${__('tables sélectionnées')})</span>`
		);
	}
	
	resetSelectedTables() {
		if(this.selectedTables.length === 0) {
			frappe.msgprint(__('Veuillez sélectionner au moins une table à vider.'));
			return;
		}
		
		frappe.confirm(
			__('Cette action supprimera toutes les données des tables sélectionnées. Cette opération est irréversible. Êtes-vous sûr ?'),
			() => {
				frappe.call({
					method: 'erpnext.reset_database.page.reset_database.reset_database.reset_selected_tables',
					args: {
						'tables': this.selectedTables
					},
					freeze: true,
					freeze_message: __('Suppression des données en cours...'),
					callback: (r) => {
						if(r.message) {
							this.loadTables();
						}
					}
				});
			}
		);
	}
	
	resetAllTables() {
		frappe.confirm(
			__('Cette action supprimera toutes les données de toutes les tables (sauf les utilisateurs). Cette opération est irréversible. Êtes-vous sûr ?'),
			() => {
				frappe.call({
					method: 'erpnext.reset_database.page.reset_database.reset_database.reset_all_tables',
					freeze: true,
					freeze_message: __('Réinitialisation de la base de données en cours...'),
					callback: (r) => {
						if(r.message) {
							this.loadTables();
						}
					}
				});
			}
		);
	}
}