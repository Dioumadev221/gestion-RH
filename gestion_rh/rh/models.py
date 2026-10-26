from django.db import models

# Modèle fourni par le professeur.
# Seules corrections : `__str__` (écrit `_str_` dans l'original, donc ignoré par Django)
# et l'affichage d'un employé, qui utilisait un champ `titre` inexistant.


class Departement(models.Model):
    nom = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)
    responsable = models.CharField(max_length=300)

    def __str__(self):
        return self.nom


class Employe(models.Model):
    matricule = models.CharField(max_length=100)
    nom = models.CharField(max_length=200)
    prenom = models.CharField(max_length=300)
    email = models.EmailField()
    telephone = models.IntegerField(null=True)
    date_embauche = models.DateField()
    poste = models.CharField(max_length=200)
    departement = models.ForeignKey(
        Departement,
        on_delete=models.CASCADE,
        related_name='emplois'
    )

    def __str__(self):
        return f"{self.prenom} {self.nom} ({self.departement.nom})"


class Contrat(models.Model):
    TYPE_CONTRAT_CHOICES = [
        ('CDD', 'Durée Déterminée'),
        ('CDI', 'Durée Indéterminée'),
        ('PRESTATAIRE', 'Prestation services'),
    ]

    reference = models.CharField(max_length=50, unique=True)
    type_contrat = models.CharField(max_length=20, choices=TYPE_CONTRAT_CHOICES, default='CDI')
    date_debut = models.DateField()
    date_fin = models.DateField(blank=True, null=True)
    emploi = models.ForeignKey(
        Employe,
        on_delete=models.PROTECT,
        related_name='contrats'
    )

    def __str__(self):
        return f"Contrat {self.reference} - {self.type_contrat}"
