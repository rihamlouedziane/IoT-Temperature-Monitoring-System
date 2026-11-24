
from django.urls import path
from . import views
from . import api

urlpatterns = [
    # Dashboard principal
    path('', views.dashboard, name='dashboard'),

    # Statistiques et graphiques
    path('statistiques/', views.statistiques, name='statistiques'),

    # Détails d'une journée
    path('jour/<str:date_jour>/', views.detail_jour, name='detail_jour'),

    # Export Excel
    path('export-excel/', views.exporter_excel, name='exporter_excel'),

    # API du capteur
    path('api/get', api.Dlist, name='json'),
    path('api/post', api.Dhtviews.as_view(), name='post'),


    # Administration
path(
    "gestion/connexion/",
    views.admin_login,
    name="admin_login"
),

path(
    "gestion/",
    views.admin_dashboard,
    name="admin_dashboard"
),

path(
    "gestion/utilisateurs/",
    views.admin_users,
    name="admin_users"
),

path(
    "gestion/utilisateurs/ajouter/",
    views.admin_add_user,
    name="admin_add_user"
),

path(
    "gestion/roles/",
    views.admin_roles,
    name="admin_roles"
),

path(
    "gestion/deconnexion/",
    views.admin_logout,
    name="admin_logout"
),
path(
    'historique/',
    views.historique_incidents,
    name='historique_incidents'
),

path(
    'historique/<int:incident_id>/',
    views.detail_incident,
    name='detail_incident'
),
path(
    'repondre-alerte/',
    views.repondre_alerte,
    name='repondre_alerte'
),
]
