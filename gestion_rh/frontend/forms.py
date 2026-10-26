from django import forms
from django.contrib.auth.forms import AuthenticationForm


class ConnexionRHForm(AuthenticationForm):
    """Connexion réservée aux comptes RH (staff)."""

    error_messages = {
        **AuthenticationForm.error_messages,
        'invalid_login': "Nom d'utilisateur ou mot de passe incorrect.",
        'non_rh': "Ce compte n'a pas accès à l'espace RH.",
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].widget.attrs.update(
            {'class': 'form-control', 'autofocus': True, 'autocomplete': 'username'}
        )
        self.fields['password'].widget.attrs.update(
            {'class': 'form-control', 'autocomplete': 'current-password'}
        )

    def confirm_login_allowed(self, user):
        super().confirm_login_allowed(user)
        if not user.is_staff:
            raise forms.ValidationError(self.error_messages['non_rh'], code='non_rh')
