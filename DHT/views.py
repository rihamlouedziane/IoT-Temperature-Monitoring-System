
from datetime import datetime, timedelta
from collections import defaultdict

from django.shortcuts import render
from django.http import HttpResponse
from django.utils import timezone

from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill

from .models import Dht11, Incident
from django.contrib.auth import login, logout
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.models import User, Group
from django.contrib.auth.decorators import user_passes_test
from django.contrib import messages
from django.shortcuts import render, redirect
from django.views.decorators.http import require_POST

from .forms import AdminCreateUserForm, RoleForm
from django.shortcuts import render, get_object_or_404
from django.db.models import Count
from django.core import signing
from .models import Incident, IncidentAlert, AlertDelivery, OperatorResponse

def dashboard(request):
    # Dernière mesure du capteur
    derniere_mesure = Dht11.objects.order_by('-dt').first()

    # Calcul de l'âge de la dernière mesure
    age = None
    if derniere_mesure and derniere_mesure.dt:
        difference = timezone.now() - derniere_mesure.dt
        age = max(0, int(difference.total_seconds()))

    # Récupérer l'incident actuellement actif
    incident_actif = Incident.objects.filter(
        status='ACTIVE'
    ).order_by('-started_at').first()

    # Récupérer les 10 derniers incidents
    incidents = Incident.objects.order_by(
        '-started_at'
    )[:10]

    # Données envoyées au template
    context = {
        'mesure': derniere_mesure,
        'age': age,
        'incident_actif': incident_actif,
        'incidents': incidents,
    }

    return render(request, 'dashboard.html', context)



def obtenir_periode(periode, date_selection):
    if periode == 'jour':
        debut = date_selection
        fin = debut + timedelta(days=1)

    elif periode == 'semaine':
        debut = date_selection - timedelta(days=date_selection.weekday())
        fin = debut + timedelta(days=7)

    elif periode == 'mois':
        debut = date_selection.replace(day=1)

        if debut.month == 12:
            fin = debut.replace(year=debut.year + 1, month=1)
        else:
            fin = debut.replace(month=debut.month + 1)

    else:
        debut = date_selection.replace(month=1, day=1)
        fin = debut.replace(year=debut.year + 1)

    fuseau = timezone.get_current_timezone()

    debut_dt = timezone.make_aware(
        datetime.combine(debut, datetime.min.time()),
        fuseau
    )

    fin_dt = timezone.make_aware(
        datetime.combine(fin, datetime.min.time()),
        fuseau
    )

    return debut, fin, debut_dt, fin_dt


def statistiques(request):
    periode = request.GET.get('periode', 'jour')

    if periode not in ['jour', 'semaine', 'mois', 'annee']:
        periode = 'jour'

    date_texte = request.GET.get('date', '')

    try:
        date_selection = datetime.strptime(
            date_texte, '%Y-%m-%d'
        ).date()
    except (ValueError, TypeError):
        date_selection = timezone.localdate()

    debut, fin, debut_dt, fin_dt = obtenir_periode(
        periode, date_selection
    )

    mesures = Dht11.objects.filter(
        dt__gte=debut_dt,
        dt__lt=fin_dt,
        temp__isnull=False,
        hum__isnull=False
    ).order_by('dt')

    # Regrouper les mesures par intervalle
    groupes = defaultdict(lambda: {
        'total_temp': 0,
        'total_hum': 0,
        'nombre': 0
    })

    for mesure in mesures.iterator():
        date_locale = timezone.localtime(mesure.dt)

        if periode in ['jour', 'semaine']:
            # Une moyenne toutes les 20 minutes
            minute = (date_locale.minute // 20) * 20

            intervalle = date_locale.replace(
                minute=minute,
                second=0,
                microsecond=0
            )

            cle = intervalle

        elif periode == 'mois':
            # Une moyenne par jour
            cle = date_locale.date()

        else:
            # Une moyenne par mois
            cle = date_locale.month

        groupes[cle]['total_temp'] += mesure.temp
        groupes[cle]['total_hum'] += mesure.hum
        groupes[cle]['nombre'] += 1

    labels = []
    temperatures = []
    humidites = []
    dates_detail = []

    for cle in sorted(groupes.keys()):
        groupe = groupes[cle]
        nombre = groupe['nombre']

        temperature = round(groupe['total_temp'] / nombre, 1)
        humidite = round(groupe['total_hum'] / nombre, 1)

        if periode == 'jour':
            labels.append(cle.strftime('%H:%M'))
            dates_detail.append(debut.isoformat())

        elif periode == 'semaine':
            labels.append(cle.strftime('%d/%m %H:%M'))
            dates_detail.append(cle.date().isoformat())

        elif periode == 'mois':
            labels.append(cle.strftime('%d/%m/%Y'))
            dates_detail.append(cle.isoformat())

        else:
            labels.append(datetime(
                date_selection.year, cle, 1
            ).strftime('%m/%Y'))
            dates_detail.append('')

        temperatures.append(temperature)
        humidites.append(humidite)

    return render(request, 'statistiques.html', {
        'periode': periode,
        'date_selection': date_selection.isoformat(),
        'labels': labels,
        'temperatures': temperatures,
        'humidites': humidites,
        'dates_detail': dates_detail,
        'nombre_mesures': mesures.count()
    })


def detail_jour(request, date_jour):
    try:
        jour = datetime.strptime(
            date_jour, '%Y-%m-%d'
        ).date()
    except ValueError:
        return HttpResponse("Date invalide", status=400)

    debut, fin, debut_dt, fin_dt = obtenir_periode('jour', jour)

    mesures = Dht11.objects.filter(
        dt__gte=debut_dt,
        dt__lt=fin_dt
    ).order_by('dt')

    return render(request, 'detail_jour.html', {
        'jour': jour,
        'mesures': mesures,
        'nombre_mesures': mesures.count()
    })


def exporter_excel(request):
    periode = request.GET.get('periode', 'jour')

    if periode not in ['jour', 'semaine', 'mois', 'annee']:
        periode = 'jour'

    date_texte = request.GET.get('date', '')

    try:
        date_selection = datetime.strptime(
            date_texte, '%Y-%m-%d'
        ).date()
    except (ValueError, TypeError):
        date_selection = timezone.localdate()

    debut, fin, debut_dt, fin_dt = obtenir_periode(
        periode, date_selection
    )

    mesures = Dht11.objects.filter(
        dt__gte=debut_dt,
        dt__lt=fin_dt
    ).order_by('dt')

    classeur = Workbook()
    feuille = classeur.active
    feuille.title = "Mesures DHT11"

    feuille.append([
        "Date et heure",
        "Température (°C)",
        "Humidité (%)"
    ])

    for cellule in feuille[1]:
        cellule.font = Font(bold=True, color="FFFFFF")
        cellule.fill = PatternFill(
            start_color="0F172A",
            end_color="0F172A",
            fill_type="solid"
        )

    for mesure in mesures:
        date_locale = timezone.localtime(mesure.dt)

        feuille.append([
            date_locale.strftime('%d/%m/%Y %H:%M:%S'),
            mesure.temp,
            mesure.hum
        ])

    feuille.column_dimensions['A'].width = 25
    feuille.column_dimensions['B'].width = 22
    feuille.column_dimensions['C'].width = 20

    reponse = HttpResponse(
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )

    reponse['Content-Disposition'] = (
        f'attachment; filename="mesures_DHT11_{debut}.xlsx"'
    )

    classeur.save(reponse)

    return reponse

# ==========================================
# ADMINISTRATION
# ==========================================

def admin_login(request):

    if request.user.is_authenticated and request.user.is_staff:
        return redirect("admin_dashboard")

    form = AuthenticationForm(
        request,
        data=request.POST or None
    )

    if request.method == "POST" and form.is_valid():

        utilisateur = form.get_user()

        if utilisateur.is_staff:
            login(request, utilisateur)
            return redirect("admin_dashboard")

        messages.error(
            request,
            "Vous n'avez pas les droits d'administration."
        )

    return render(
        request,
        "administration/login.html",
        {"form": form}
    )


def administrateur_requis(user):
    return user.is_authenticated and user.is_staff


@user_passes_test(
    administrateur_requis,
    login_url="admin_login"
)
def admin_dashboard(request):

    context = {
        "nombre_utilisateurs": User.objects.count(),
        "nombre_roles": Group.objects.count(),
        "utilisateurs_actifs": User.objects.filter(
            is_active=True
        ).count(),
    }

    return render(
        request,
        "administration/dashboard.html",
        context
    )


@user_passes_test(
    administrateur_requis,
    login_url="admin_login"
)
def admin_users(request):

    utilisateurs = User.objects.prefetch_related(
        "groups"
    ).order_by("-date_joined")

    return render(
        request,
        "administration/utilisateurs.html",
        {"utilisateurs": utilisateurs}
    )


@user_passes_test(
    administrateur_requis,
    login_url="admin_login"
)
def admin_add_user(request):

    form = AdminCreateUserForm(
        request.POST or None
    )

    if request.method == "POST" and form.is_valid():

        utilisateur = form.save()

        role = form.cleaned_data.get("role")

        if role:
            utilisateur.groups.add(role)

        messages.success(
            request,
            "Utilisateur ajouté avec succès."
        )

        return redirect("admin_users")

    return render(
        request,
        "administration/ajouter_utilisateur.html",
        {"form": form}
    )


@user_passes_test(
    administrateur_requis,
    login_url="admin_login"
)
def admin_roles(request):

    form = RoleForm(request.POST or None)

    if request.method == "POST" and form.is_valid():

        form.save()

        messages.success(
            request,
            "Rôle créé avec succès."
        )

        return redirect("admin_roles")

    roles = Group.objects.all().order_by("name")

    return render(
        request,
        "administration/roles.html",
        {
            "form": form,
            "roles": roles
        }
    )

def historique_incidents(request):
    incidents = Incident.objects.order_by('-started_at')

    context = {
        'incidents': incidents,
    }

    return render(request, 'historique.html', context)


def detail_incident(request, incident_id):
    incident = get_object_or_404(Incident, id=incident_id)

    alertes = IncidentAlert.objects.filter(
        incident=incident
    ).order_by('counter')

    notifications = AlertDelivery.objects.filter(
        alert__incident=incident
    ).select_related(
        'alert', 'operator'
    ).order_by('alert__counter', 'operator__name')

    reponses = OperatorResponse.objects.filter(
        incident=incident
    ).select_related(
        'operator'
    ).order_by('responded_at')

    alertes_par_operateur = AlertDelivery.objects.filter(
        alert__incident=incident
    ).values(
        'operator__name'
    ).annotate(
        nombre_alertes=Count('id')
    ).order_by('operator__name')

    context = {
        'incident': incident,
        'alertes': alertes,
        'notifications': notifications,
        'reponses': reponses,
        'alertes_par_operateur': alertes_par_operateur,
    }

    return render(request, 'detail_incident.html', context)



def repondre_alerte(request):
    token = request.GET.get("token") or request.POST.get("token")

    if not token:
        return HttpResponse("Lien invalide.", status=400)

    try:
        data = signing.loads(
            token,
            salt="operator-alert-response",
            max_age=7 * 24 * 60 * 60
        )
    except signing.BadSignature:
        return HttpResponse("Lien invalide ou expiré.", status=400)

    delivery = get_object_or_404(
        AlertDelivery.objects.select_related("alert__incident", "operator"),
        id=data["delivery_id"]
    )

    if request.method == "POST":
        if not delivery.acknowledged_at:
            delivery.acknowledged_at = timezone.now()
            delivery.operator_message = request.POST.get(
                "operator_message", ""
            ).strip()

            delivery.save(update_fields=[
                "acknowledged_at",
                "operator_message"
            ])

        return redirect("dashboard")

    context = {
        "delivery": delivery,
        "incident": delivery.alert.incident,
        "alerte": delivery.alert,
        "operateur": delivery.operator,
    }

    return render(request, "repondre_alerte.html", context)


@require_POST
def admin_logout(request):

    logout(request)

    return redirect("admin_login")