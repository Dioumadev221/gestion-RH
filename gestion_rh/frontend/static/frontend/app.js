// Fonctions partagées par toutes les pages : appels à l'API, alertes Bootstrap, mise en forme.
const RH = {
  csrfToken() {
    return document.querySelector('meta[name="csrf-token"]').content;
  },

  // Appel à l'API REST. Lève une erreur (avec .status et .data) si la réponse n'est pas 2xx.
  async api(url, { method = 'GET', body } = {}) {
    const options = { method, credentials: 'same-origin', headers: { Accept: 'application/json' } };
    if (body !== undefined) {
      options.headers['Content-Type'] = 'application/json';
      options.body = JSON.stringify(body);
    }
    if (method !== 'GET') options.headers['X-CSRFToken'] = RH.csrfToken();

    const reponse = await fetch(url, options);
    const data = reponse.status === 204 ? null : await reponse.json().catch(() => null);
    if (!reponse.ok) {
      const erreur = new Error(`Erreur API ${reponse.status}`);
      erreur.status = reponse.status;
      erreur.data = data;
      throw erreur;
    }
    return data;
  },

  alerte(message, type = 'success') {
    const icones = { success: 'check-circle', danger: 'exclamation-triangle', warning: 'exclamation-circle', info: 'info-circle' };
    const div = document.createElement('div');
    div.className = `alert alert-${type} alert-dismissible fade show shadow-sm`;
    div.setAttribute('role', 'alert');
    div.innerHTML = `<i class="bi bi-${icones[type] || 'info-circle'} me-2"></i>${RH.echapper(message)}
      <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Fermer"></button>`;
    document.getElementById('alertes').append(div);
  },

  // Message affiché sur la page suivante, après une redirection
  messageApresRedirection(message, type = 'success') {
    sessionStorage.setItem('rh-message', JSON.stringify({ message, type }));
  },

  afficherMessageEnAttente() {
    const enAttente = sessionStorage.getItem('rh-message');
    if (!enAttente) return;
    sessionStorage.removeItem('rh-message');
    const { message, type } = JSON.parse(enAttente);
    RH.alerte(message, type);
  },

  erreurServeur(erreur) {
    console.error(erreur);
    if (erreur.status === 403) {
      RH.alerte('Votre session a expiré : reconnectez-vous.', 'warning');
    } else if (erreur.status === 404) {
      RH.alerte("Cet élément n'existe pas ou a été supprimé.", 'warning');
    } else {
      RH.alerte('Impossible de joindre le serveur. Réessayez.', 'danger');
    }
  },

  // Fenêtre de confirmation Bootstrap ; renvoie true si l'utilisateur confirme
  confirmer(message) {
    return new Promise((resolve) => {
      const fenetre = document.getElementById('modal-confirmation');
      fenetre.querySelector('#modal-confirmation-texte').textContent = message;
      const modal = bootstrap.Modal.getOrCreateInstance(fenetre);
      let confirme = false;
      fenetre.querySelector('#modal-confirmation-ok').onclick = () => {
        confirme = true;
        modal.hide();
      };
      fenetre.addEventListener('hidden.bs.modal', () => resolve(confirme), { once: true });
      modal.show();
    });
  },

  // Demande confirmation puis supprime ; renvoie true si l'employé a été supprimé
  async supprimerEmploye(id, nomComplet) {
    const confirme = await RH.confirmer(`Supprimer définitivement ${nomComplet} et tous ses contrats ?`);
    if (!confirme) return false;
    try {
      await RH.api(`/api/employes/${id}/`, { method: 'DELETE' });
      return true;
    } catch (erreur) {
      RH.erreurServeur(erreur);
      return false;
    }
  },

  echapper(texte) {
    const div = document.createElement('div');
    div.textContent = texte ?? '';
    return div.innerHTML;
  },

  date(iso) {
    if (!iso) return '—';
    const [annee, mois, jour] = iso.split('-');
    return `${jour}/${mois}/${annee}`;
  },

  argent(valeur) {
    return `${Number(valeur).toLocaleString('fr-FR')} FCFA`;
  },

  badgeContrat(contrat) {
    if (!contrat) return '<span class="badge text-bg-light border">Sans contrat</span>';
    const couleurs = { CDI: 'success', CDD: 'warning', PRESTATAIRE: 'info' };
    return `<span class="badge text-bg-${couleurs[contrat.type]}">${RH.echapper(contrat.type_display)}</span>`;
  },

  initiales(employe) {
    return `${employe.prenom[0] || ''}${employe.nom[0] || ''}`.toUpperCase();
  },
};

document.addEventListener('DOMContentLoaded', RH.afficherMessageEnAttente);
