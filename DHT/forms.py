from django import forms
from django.contrib.auth.models import User, Group
from django.contrib.auth.forms import UserCreationForm


class AdminCreateUserForm(UserCreationForm):

    email = forms.EmailField(
        required=True,
        label="Adresse e-mail"
    )

    first_name = forms.CharField(
        max_length=150,
        required=False,
        label="Prénom"
    )

    last_name = forms.CharField(
        max_length=150,
        required=False,
        label="Nom"
    )

    role = forms.ModelChoiceField(
        queryset=Group.objects.all(),
        required=False,
        label="Rôle",
        empty_label="Choisir un rôle"
    )

    class Meta:
        model = User
        fields = [
            "username",
            "email",
            "first_name",
            "last_name"
        ]


class RoleForm(forms.ModelForm):

    class Meta:
        model = Group
        fields = ["name"]
        labels = {
            "name": "Nom du rôle"
        }