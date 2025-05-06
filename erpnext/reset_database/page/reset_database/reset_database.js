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
		this.selectedDoctypes = [];
		this.tables = [];
		this.doctypes = [];
		this.activeTab = 'doctypes'; // Par défaut, afficher l'onglet des doctypes
		
		this.setup();
		this.loadDoctypes(); // Charger les doctypes par défaut
	}
	
	setup() {
		// Ajouter des boutons d'action
		this.setupActionButtons();
		
		// Ajouter les sections
		this.setupWarningSection();
		this.setupTabsSection();
		this.setupSelectionSection();
	}
	
	setupActionButtons() {
		// Bouton primaire pour vider les éléments sélectionnés
		this.page.set_primary_action(__('Vider les éléments sélectionnés'), () => {
			if (this.activeTab === 'doctypes') {
				this.resetSelectedDoctypes();
			} else {
				this.resetSelectedTables();
			}
		}, 'octicon octicon-sync');
		
		// Bouton secondaire pour vider tous les éléments
		this.page.set_secondary_action(__('Vider tous les éléments'), () => {
			if (this.activeTab === 'doctypes') {
				this.resetAllDoctypes();
			} else {
				this.resetAllTables();
			}
		});
	}
	
	setupWarningSection() {
		// Utiliser une approche plus simple pour créer les avertissements
		let warning = $(`
			<div class="alert alert-warning">
				<h4>${__('Attention')}</h4>
				<p>${__('Cette page vous permet de réinitialiser des doctypes ou tables spécifiques de la base de données en conservant les informations des utilisateurs.')}</p>
				<p>${__('Utilisez cette fonctionnalité avec précaution car elle supprimera des données importantes.')}</p>
			</div>
		`);
		
		// Informations importantes
		let info = $(`
			<div class="alert alert-info">
				<h5>${__('Informations importantes')}</h5>
				<ul>
					<li>${__('Les données des éléments sélectionnés seront supprimées')}</li>
					<li>${__('Cette action est irréversible')}</li>
					<li>${__('Effectuez une sauvegarde avant de procéder à cette opération')}</li>
				</ul>
			</div>
		`);
		
		$(warning).appendTo(this.page.main);
		$(info).appendTo(this.page.main);
	}
	
	setupTabsSection() {
		// Créer les onglets pour tables/doctypes
		let tabsSection = $(`
			<div class="tabs-section mt-4">
				<div class="form-group">
					<div class="btn-group" role="group">
						<button type="button" class="btn btn-default doctype-tab active">
							${__('Par DocTypes')}
						</button>
						<button type="button" class="btn btn-default table-tab">
							${__('Par Tables')}
						</button>
					</div>
				</div>
			</div>
		`).appendTo(this.page.main);
		
		// Gérer les événements des onglets
		tabsSection.find('.doctype-tab').on('click', () => {
			this.activeTab = 'doctypes';
			tabsSection.find('.doctype-tab').addClass('active');
			tabsSection.find('.table-tab').removeClass('active');
			this.loadDoctypes();
		});
		
		tabsSection.find('.table-tab').on('click', () => {
			this.activeTab = 'tables';
			tabsSection.find('.table-tab').addClass('active');
			tabsSection.find('.doctype-tab').removeClass('active');
			this.loadTables();
		});
		
		// Conteneur pour les sections
		this.selectionContainer = $(`<div class="selection-container"></div>`).appendTo(this.page.main);
	}
	
	setupSelectionSection() {
		// Cette section sera dynamiquement remplie selon l'onglet actif
		this.selectionContainer.empty();
		
		// Section de sélection
		let selectionSection = $(`<div class="selection-section mt-4"></div>`).appendTo(this.selectionContainer);
		
		// Créer un champ de recherche standard
		let searchGroup = $(`
			<div class="form-group">
				<label class="control-label">${__('Rechercher')}</label>
				<input type="text" class="form-control search-field" placeholder="${__('Rechercher...')}">
			</div>
		`).appendTo(selectionSection);
		
		this.searchField = searchGroup.find('.search-field');
		this.searchField.on('input', () => this.filterItems());
		
		// Ajouter boutons de sélection
		let buttonGroup = $(`<div class="btn-group mt-2 mb-4"></div>`).appendTo(selectionSection);
		
		$(`<button class="btn btn-default btn-sm">${__('Sélectionner tout')}</button>`)
			.appendTo(buttonGroup)
			.on('click', () => this.selectAll());
			
		$(`<button class="btn btn-default btn-sm">${__('Désélectionner tout')}</button>`)
			.appendTo(buttonGroup)
			.on('click', () => this.deselectAll());
		
		// Container pour la liste des éléments
		this.itemsContainer = $(`<div class="items-container frappe-card p-3"></div>`).appendTo(selectionSection);
	}
	
	loadDoctypes() {
		this.setupSelectionSection();
		
		// Afficher un message de chargement
		let loadingMessage = $(`<div class="text-muted text-center p-5">${__('Chargement des doctypes...')}</div>`).appendTo(this.itemsContainer);
		
		frappe.call({
			method: 'erpnext.reset_database.page.reset_database.reset_database.get_all_doctypes',
			callback: (r) => {
				loadingMessage.remove();
				if(r.message) {
					this.doctypes = r.message;
					this.renderDoctypes();
				}
			}
		});
	}
	
	loadTables() {
		this.setupSelectionSection();
		
		// Afficher un message de chargement
		let loadingMessage = $(`<div class="text-muted text-center p-5">${__('Chargement des tables...')}</div>`).appendTo(this.itemsContainer);
		
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
	
	renderDoctypes() {
		this.itemsContainer.empty();
		this.selectedDoctypes = [];
		
		// Grouper les doctypes par modules
		let moduleGroups = this.groupDoctypesByModule();
		
		// Créer des sections pour chaque module
		Object.keys(moduleGroups).sort().forEach(module => {
			let moduleSection = $(`
				<div class="module-section mb-3">
					<h6 class="module-title">${module} (${moduleGroups[module].length})</h6>
					<div class="item-list row"></div>
				</div>
			`).appendTo(this.itemsContainer);
			
			let itemList = moduleSection.find('.item-list');
			
			// Créer une case à cocher pour chaque doctype
			moduleGroups[module].forEach(doctype => {
				let itemCol = $(`<div class="col-md-4 item-entry mb-2"></div>`).appendTo(itemList);
				
				let checkboxItem = $(`
					<div class="checkbox">
						<label>
							<input type="checkbox" data-doctype="${doctype.name}"> 
							${doctype.name} <span class="text-muted">(${doctype.count})</span>
						</label>
					</div>
				`).appendTo(itemCol);
				
				let checkbox = checkboxItem.find('input[type="checkbox"]');
				checkbox.on('change', () => {
					if(checkbox.is(':checked')) {
						if(!this.selectedDoctypes.includes(doctype.name)) {
							this.selectedDoctypes.push(doctype.name);
						}
					} else {
						this.selectedDoctypes = this.selectedDoctypes.filter(d => d !== doctype.name);
					}
					this.updateTitle();
				});
				
				// Stocker la référence à la case à cocher
				doctype.checkbox = checkbox;
			});
		});
		
		this.updateTitle();
	}
	
	renderTables() {
		this.itemsContainer.empty();
		this.selectedTables = [];
		
		// Grouper les tables par modules (basé sur le code existant)
		let moduleGroups = this.groupTablesByModule();
		
		// Créer des sections pour chaque module
		Object.keys(moduleGroups).sort().forEach(module => {
			let moduleSection = $(`
				<div class="module-section mb-3">
					<h6 class="module-title">${module} (${moduleGroups[module].length})</h6>
					<div class="item-list row"></div>
				</div>
			`).appendTo(this.itemsContainer);
			
			let itemList = moduleSection.find('.item-list');
			
			// Créer une case à cocher pour chaque table
			moduleGroups[module].forEach(table => {
				let itemCol = $(`<div class="col-md-4 item-entry mb-2"></div>`).appendTo(itemList);
				
				let checkboxItem = $(`
					<div class="checkbox">
						<label>
							<input type="checkbox" data-table="${table.name}"> 
							${table.name} <span class="text-muted">(${table.count})</span>
							${table.description ? '<small class="text-muted d-block">' + table.description + '</small>' : ''}
						</label>
					</div>
				`).appendTo(itemCol);
				
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
	
	groupDoctypesByModule() {
		let modules = {};
		
		this.doctypes.forEach(doctype => {
			let module = doctype.module || "Autres";
			
			if (!modules[module]) {
				modules[module] = [];
			}
			modules[module].push(doctype);
		});
		
		return modules;
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
	
	filterItems() {
		let searchTerm = this.searchField.val().toLowerCase();
		
		if (this.activeTab === 'doctypes') {
			this.doctypes.forEach(doctype => {
				let itemEntry = doctype.checkbox.closest('.item-entry');
				if(doctype.name.toLowerCase().includes(searchTerm)) {
					itemEntry.show();
				} else {
					itemEntry.hide();
				}
			});
		} else {
			this.tables.forEach(table => {
				let itemEntry = table.checkbox.closest('.item-entry');
				if(table.name.toLowerCase().includes(searchTerm)) {
					itemEntry.show();
				} else {
					itemEntry.hide();
				}
			});
		}
	}
	
	selectAll() {
		$('.item-entry:visible input[type="checkbox"]').prop('checked', true).trigger('change');
	}
	
	deselectAll() {
		$('.item-entry:visible input[type="checkbox"]').prop('checked', false).trigger('change');
	}
	
	updateTitle() {
		// Mettre à jour le compteur d'éléments sélectionnés
		let count = this.activeTab === 'doctypes' ? this.selectedDoctypes.length : this.selectedTables.length;
		let itemType = this.activeTab === 'doctypes' ? __('doctypes') : __('tables');
		
		this.page.set_title(
			__('Réinitialisation de la Base de Données') + 
			` <span class="text-muted">(${count} ${itemType} ${__('sélectionnés')})</span>`
		);
	}
	
	resetSelectedDoctypes() {
		if(this.selectedDoctypes.length === 0) {
			frappe.msgprint(__('Veuillez sélectionner au moins un doctype à vider.'));
			return;
		}
		
		frappe.confirm(
			__('Cette action supprimera toutes les données des doctypes sélectionnés. Cette opération est irréversible. Êtes-vous sûr ?'),
			() => {
				frappe.call({
					method: 'erpnext.reset_database.page.reset_database.reset_database.reset_selected_doctypes',
					args: {
						'doctypes': this.selectedDoctypes
					},
					freeze: true,
					freeze_message: __('Suppression des données en cours...'),
					callback: (r) => {
						if(r.message) {
							this.loadDoctypes();
						}
					}
				});
			}
		);
	}
	
	resetAllDoctypes() {
		frappe.confirm(
			__('Cette action supprimera toutes les données de tous les doctypes (sauf les utilisateurs et autres doctypes système). Cette opération est irréversible. Êtes-vous sûr ?'),
			() => {
				frappe.call({
					method: 'erpnext.reset_database.page.reset_database.reset_database.reset_all_doctypes',
					freeze: true,
					freeze_message: __('Réinitialisation des données en cours...'),
					callback: (r) => {
						if(r.message) {
							this.loadDoctypes();
						}
					}
				});
			}
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