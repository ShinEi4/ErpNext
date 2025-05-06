frappe.pages['import-database'].on_page_load = function(wrapper) {
	var page = frappe.ui.make_app_page({
		parent: wrapper,
		title: __('Importation de Base de Données'),
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
		// Ajouter les sections
		this.setupIntroSection();
		this.setupImportSection();
		this.setupResultSection();
		
		// Ajouter le bouton principal
		this.page.set_primary_action(__('Importer les données'), () => this.importData(), 'octicon octicon-cloud-upload');
	}
	
	setupIntroSection() {
		let intro = $(`
			<div class="intro-section">
				<div class="alert alert-info">
					<h4>${__('Instructions')}</h4>
					<p>${__('Cette page vous permet d\'importer des données à partir de fichiers CSV pour créer des demandes de matériel, des fournisseurs et des demandes de devis.')}</p>
					<p>${__('Les 3 fichiers suivants sont requis:')}</p>
					<ol>
						<li>${__('Material Request (date, item_name, item_groupe, required_by, quantity, purpose, target_warehouse, ref)')}</li>
						<li>${__('Supplier (supplier_name, country, type)')}</li>
						<li>${__('Request for Quotation (ref_request_quotation, supplier)')}</li>
					</ol>
					<p>${__('Tous les fichiers doivent être au format CSV. L\'importation validera toutes les données avant d\'effectuer l\'importation.')}</p>
					<p>${__('L\'importation suit le principe "tout ou rien": soit toutes les données sont importées, soit aucune.')}</p>
					<p>${__('Note: Si un article ou un groupe d\'articles n\'existe pas dans le système, ils seront automatiquement créés.')}</p>
				</div>
			</div>
		`).appendTo(this.page.main);
	}
	
	setupImportSection() {
		let section = $(`
			<div class="import-section">
				<h3>${__('Fichiers à importer')}</h3>
				<div class="row form-section">
					<div class="col-md-4">
						<div class="form-group">
							<div class="mr-file-field"></div>
						</div>
					</div>
					<div class="col-md-4">
						<div class="form-group">
							<div class="supplier-file-field"></div>
						</div>
					</div>
					<div class="col-md-4">
						<div class="form-group">
							<div class="rfq-file-field"></div>
						</div>
					</div>
				</div>
			</div>
		`).appendTo(this.page.main);
		
		// Création des champs de téléchargement
		this.mrFileField = frappe.ui.form.make_control({
			parent: section.find('.mr-file-field'),
			df: {
				fieldtype: 'Attach',
				fieldname: 'material_request_file',
				label: __('Fichier Material Request (CSV)'),
				reqd: 1,
			},
			render_input: true
		});
		
		this.supplierFileField = frappe.ui.form.make_control({
			parent: section.find('.supplier-file-field'),
			df: {
				fieldtype: 'Attach',
				fieldname: 'supplier_file',
				label: __('Fichier Supplier (CSV)'),
				reqd: 1,
			},
			render_input: true
		});
		
		this.rfqFileField = frappe.ui.form.make_control({
			parent: section.find('.rfq-file-field'),
			df: {
				fieldtype: 'Attach',
				fieldname: 'rfq_file',
				label: __('Fichier Request for Quotation (CSV)'),
				reqd: 1,
			},
			render_input: true
		});
		
		// Initialiser les contrôles
		this.mrFileField.refresh();
		this.supplierFileField.refresh();
		this.rfqFileField.refresh();
	}
	
	setupResultSection() {
		this.resultSection = $(`
			<div class="result-section" style="display: none;">
				<div class="import-stats frappe-card p-3 mt-4">
					<h3>${__('Résultats de l\'importation')}</h3>
					<div class="row">
						<div class="col-md-4">
							<div class="stat-item">
								<span class="stat-label">${__('Fournisseurs importés:')}</span>
								<span class="stat-value suppliers-count">0</span>
							</div>
						</div>
						<div class="col-md-4">
							<div class="stat-item">
								<span class="stat-label">${__('Demandes de matériel importées:')}</span>
								<span class="stat-value mr-count">0</span>
							</div>
						</div>
						<div class="col-md-4">
							<div class="stat-item">
								<span class="stat-label">${__('Demandes de devis importées:')}</span>
								<span class="stat-value rfq-count">0</span>
							</div>
						</div>
					</div>
					<div class="row mt-3">
						<div class="col-md-4 offset-md-4">
							<div class="stat-item">
								<span class="stat-label">${__('Devis fournisseur créés:')}</span>
								<span class="stat-value sq-count">0</span>
							</div>
						</div>
					</div>
				</div>
				
				<div class="info-container mt-4" style="display: none;">
					<div class="alert alert-info">
						<h4>${__('Informations supplémentaires')}</h4>
						<div class="info-list"></div>
					</div>
				</div>
				
				<div class="error-container mt-4" style="display: none;">
					<div class="alert alert-danger">
						<h4>${__('Erreurs durant l\'importation')}</h4>
						<div class="error-list"></div>
					</div>
				</div>
			</div>
		`).appendTo(this.page.main);
	}
	
	importData() {
		// Vérifier si tous les fichiers sont fournis
		if (!this.validateFiles()) {
			frappe.msgprint(__('Veuillez sélectionner tous les fichiers CSV requis.'));
			return;
		}
		
		frappe.confirm(
			__('Cette action va importer toutes les données des fichiers CSV. Assurez-vous que les formats sont corrects. Continuer?'),
			() => {
				// Appeler la méthode d'importation avec les URL des fichiers
				frappe.call({
					method: 'erpnext.import_db.page.import_database.importer.import_all_data',
					args: {
						material_request_file: this.mrFileField.get_value(),
						supplier_file: this.supplierFileField.get_value(),
						rfq_file: this.rfqFileField.get_value()
					},
					freeze: true,
					freeze_message: __('Importation des données en cours...'),
					callback: (r) => {
						if (r.message) {
							this.showResults(r.message);
						} else {
							frappe.msgprint(__('Une erreur s\'est produite lors de l\'importation.'));
						}
					}
				});
			}
		);
	}
	
	validateFiles() {
		return (
			this.mrFileField.get_value() &&
			this.supplierFileField.get_value() &&
			this.rfqFileField.get_value()
		);
	}
	
	showResults(results) {
		this.resultSection.show();
		
		// Mettre à jour les compteurs
		this.resultSection.find('.suppliers-count').text(results.suppliers_imported || 0);
		this.resultSection.find('.mr-count').text(results.material_requests_imported || 0);
		this.resultSection.find('.rfq-count').text(results.rfqs_imported || 0);
		this.resultSection.find('.sq-count').text(results.supplier_quotations_created || 0);
		
		// Afficher les messages d'information s'il y en a
		if (results.info && results.info.length > 0) {
			let infoContainer = this.resultSection.find('.info-container');
			let infoList = infoContainer.find('.info-list');
			
			infoList.empty();
			
			for (let info of results.info) {
				$(`<div class="info-item">${info}</div>`).appendTo(infoList);
			}
			
			infoContainer.show();
		} else {
			this.resultSection.find('.info-container').hide();
		}
		
		// Afficher les erreurs s'il y en a
		if (results.errors && results.errors.length > 0) {
			let errorContainer = this.resultSection.find('.error-container');
			let errorList = errorContainer.find('.error-list');
			
			errorList.empty();
			
			for (let error of results.errors) {
				$(`<div class="error-item">${error}</div>`).appendTo(errorList);
			}
			
			errorContainer.show();
			
			frappe.show_alert({
				message: __('Importation terminée avec des erreurs. Veuillez vérifier les détails.'),
				indicator: 'orange'
			}, 5);
		} else {
			this.resultSection.find('.error-container').hide();
			
			if (results.success) {
				frappe.show_alert({
					message: __('Importation réussie!'),
					indicator: 'green'
				}, 5);
			} else {
				frappe.show_alert({
					message: __('L\'importation a échoué. Aucune donnée n\'a été importée.'),
					indicator: 'red'
				}, 5);
			}
		}
	}
}