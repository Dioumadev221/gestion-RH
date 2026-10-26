from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator, RegexValidator
from django.db import models
from django.utils import timezone


class Departement(models.Model):
    nom = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    responsable = models.ForeignKey(
        'Employe',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='departements_diriges',
    )

    class Meta:
        ordering = ['nom']
        verbose_name = 'département'

    def __str__(self):
        return self.nom


class Employe(models.Model):
    matricule = models.CharField(
        max_length=20, unique=True, error_messages={'unique': 'Ce matricule est déjà attribué à un employé.'}
    )
    nom = models.CharField(max_length=100)
    prenom = models.CharField('prénom', max_length=100)
    email = models.EmailField(unique=True, error_messages={'unique': 'Cet email est déjà utilisé par un employé.'})
    telephone = models.CharField(
        'téléphone',
        max_length=20,
        validators=[RegexValidator(r'^\+?[0-9 ]{7,20}$', 'Numéro de téléphone invalide.')],
    )
    date_embauche = models.DateField("date d'embauche")
    poste = models.CharField(max_length=100)
    departement = models.ForeignKey(
        Departement,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='employes',
        verbose_name='département',
    )

    class Meta:
        ordering = ['nom', 'prenom']
        verbose_name = 'employé'

    def __str__(self):
        return f'{self.prenom} {self.nom} ({self.matricule})'

    @property
    def nom_complet(self):
        return f'{self.prenom} {self.nom}'

    @property
    def contrat_actuel(self):
        """Contrat en cours aujourd'hui, ou le plus récent à défaut."""
        aujourd_hui = timezone.localdate()
        contrats = list(self.contrats.all())
        for contrat in contrats:
            if contrat.date_debut <= aujourd_hui and (contrat.date_fin is None or contrat.date_fin >= aujourd_hui):
                return contrat
        return contrats[0] if contrats else None


class Contrat(models.Model):
    class Type(models.TextChoices):
        CDI = 'CDI', 'CDI'
        CDD = 'CDD', 'CDD'
        PRESTATAIRE = 'PRESTATAIRE', 'Prestataire'

    employe = models.ForeignKey(
        Employe, on_delete=models.CASCADE, related_name='contrats', verbose_name='employé'
    )
    type = models.CharField(max_length=20, choices=Type.choices, default=Type.CDI)
    date_debut = models.DateField('date de début')
    date_fin = models.DateField('date de fin', null=True, blank=True)
    salaire = models.DecimalField(
        max_digits=12, decimal_places=2, validators=[MinValueValidator(0)], help_text='En FCFA'
    )

    class Meta:
        ordering = ['-date_debut']

    def __str__(self):
        return f'{self.get_type_display()} – {self.employe.nom_complet}'

    def clean(self):
        if self.type in (self.Type.CDD, self.Type.PRESTATAIRE) and not self.date_fin:
            raise ValidationError({'date_fin': 'La date de fin est obligatoire pour un CDD ou un prestataire.'})
        if self.date_fin and self.date_debut and self.date_fin < self.date_debut:
            raise ValidationError({'date_fin': 'La date de fin doit être après la date de début.'})
