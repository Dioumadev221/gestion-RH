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
    div.className = `alert alert-${type} alert-dismissible fade show`;
    setTimeout(() => bootstrap.Alert.getOrCreateInstance(div).close(), 6000);
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

  // Seuil (en jours) à partir duquel une fin de contrat est signalée
  SEUIL_ECHEANCE: 60,

  joursRestants(dateIso) {
    if (!dateIso) return null;
    const aujourdHui = new Date();
    aujourdHui.setHours(0, 0, 0, 0);
    return Math.round((new Date(`${dateIso}T00:00:00`) - aujourdHui) / 86400000);
  },

  // Pastille du type de contrat (CDI / CDD / Prestataire)
  pastilleContrat(contrat) {
    if (!contrat) return '<span class="pastille pastille-neutre">Sans contrat</span>';
    const libelles = { CDI: 'CDI', CDD: 'CDD', PRESTATAIRE: 'Prestataire' };
    return `<span class="pastille pastille-${contrat.type_contrat.toLowerCase()}" title="${RH.echapper(contrat.type_contrat_display)}">
      ${libelles[contrat.type_contrat] || RH.echapper(contrat.type_contrat)}</span>`;
  },

  // 771234567 -> « 77 123 45 67 »
  telephone(numero) {
    if (numero == null || numero === '') return '—';
    const chiffres = String(numero);
    return chiffres.length === 9
      ? `${chiffres.slice(0, 2)} ${chiffres.slice(2, 5)} ${chiffres.slice(5, 7)} ${chiffres.slice(7)}`
      : chiffres;
  },

  // Texte d'échéance sous la pastille : « jusqu'au … », « fin dans 12 j », « expiré »
  echeance(contrat) {
    if (!contrat || !contrat.date_fin) return '';
    const jours = RH.joursRestants(contrat.date_fin);
    if (jours < 0) return `<div class="echeance depassee"><i class="bi bi-exclamation-circle"></i> Expiré le ${RH.date(contrat.date_fin)}</div>`;
    if (jours <= RH.SEUIL_ECHEANCE) {
      return `<div class="echeance proche"><i class="bi bi-clock"></i> Fin dans ${jours} j</div>`;
    }
    return `<div class="echeance">Jusqu'au ${RH.date(contrat.date_fin)}</div>`;
  },

  initiales(employe) {
    return `${employe.prenom[0] || ''}${employe.nom[0] || ''}`.toUpperCase();
  },

  // Avatar à initiales, avec une couleur stable par personne
  avatar(employe, taille = '') {
    const cle = `${employe.prenom}${employe.nom}`;
    let somme = 0;
    for (const lettre of cle) somme += lettre.charCodeAt(0);
    return `<span class="avatar ${taille} avatar-${somme % 6}" aria-hidden="true">${RH.echapper(RH.initiales(employe))}</span>`;
  },

  pluriel(nombre, mot) {
    return `${nombre} ${mot}${nombre > 1 ? 's' : ''}`;
  },
};

document.addEventListener('DOMContentLoaded', RH.afficherMessageEnAttente);
