# marketing_mail/views.py - VERSION CORRIGÉE AVEC FILTRE DATE UNIQUE

import json
from rest_framework.decorators import api_view, permission_classes, parser_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from rest_framework.response import Response
from rest_framework import status

from django.core.mail import EmailMessage
from django.conf import settings
from django.db.models import Q
from datetime import datetime

from .models import MarketingEmail, DestinatairEmail
from .serializers import (
    MarketingEmailSerializer,
    MarketingEmailListSerializer,
    ArchiveEmailSerializer,
    EstimationDestinatairesSerializer,
)

from prospects.models import Prospect
from etudiants.models import Etudiant
from diplomes.models import Diplome
from formation.models import Formation
from formation.serializers import FormationSerializer


def get_destinataires_segment(groupe, formations_ids, statuts, sources):
    """Récupère la liste des destinataires avec leurs informations complètes"""
    result = []

    if groupe == 'Prospects':
        qs = Prospect.objects.exclude(email__isnull=True).exclude(email='')
        if formations_ids:
            qs = qs.filter(formations_souhaitees__id__in=formations_ids).distinct()
        if statuts:
            qs = qs.filter(statut__in=statuts)
        if sources:
            qs = qs.filter(source__in=sources)
        
        for p in qs:
            formations_list = list(p.formations_souhaitees.values_list('intitule', flat=True))
            result.append({
                'email': p.email,
                'type': 'prospect',
                'objet_id': p.id,
                'modele': 'prospect',
                'nom': f"{p.prenom or ''} {p.nom or ''}".strip() or p.email,
                'ville': p.ville or "—",
                'telephone': p.telephone or "—",
                'formation': ", ".join(formations_list) if formations_list else "—",
                'statut': p.statut or "—",
                'date_inscription': p.date_creation.strftime('%d/%m/%Y') if p.date_creation else "—"
            })

    elif groupe == 'Étudiants':
        qs = Etudiant.objects.exclude(email__isnull=True).exclude(email='')
        if formations_ids:
            qs = qs.filter(formations_suivies__id__in=formations_ids).distinct()
        
        for e in qs:
            formations_list = list(e.formations_suivies.values_list('intitule', flat=True))
            result.append({
                'email': e.email,
                'type': 'etudiant',
                'objet_id': e.id,
                'modele': 'etudiant',
                'nom': f"{e.prenom or ''} {e.nom or ''}".strip() or e.email,
                'ville': e.ville or "—",
                'telephone': e.telephone or "—",
                'formation': ", ".join(formations_list) if formations_list else "—",
                'statut': "Étudiant",
                'date_inscription': e.date_inscription.strftime('%d/%m/%Y') if e.date_inscription else "—"
            })

    elif groupe == 'Diplômés':
        qs = Diplome.objects.filter(statut='delivre').exclude(email__isnull=True).exclude(email='')
        if formations_ids:
            qs = qs.filter(formation__id__in=formations_ids)
        
        for d in qs:
            result.append({
                'email': d.email,
                'type': 'diplome',
                'objet_id': d.id,
                'modele': 'diplome',
                'nom': f"{d.prenom or ''} {d.nom or ''}".strip() or d.email,
                'ville': d.ville or "—",
                'telephone': d.telephone or "—",
                'formation': d.formation.intitule if d.formation else "—",
                'statut': "Diplômé",
                'date_inscription': d.date_obtention.strftime('%d/%m/%Y') if d.date_obtention else "—"
            })

    return result


def get_formations_par_type_avec_comptage(type_groupe, formations_ids=None):
    """
    Récupère UNIQUEMENT les formations qui ont au moins un contact (count > 0)
    Peu importe que la formation soit active ou non
    """
    formations_data = []
    
    if type_groupe == 'prospects':
        formations_avec_prospects_ids = Prospect.objects.filter(
            formations_souhaitees__isnull=False
        ).exclude(
            email__isnull=True
        ).exclude(
            email=''
        ).values_list('formations_souhaitees__id', flat=True).distinct()
        
        formations_avec_prospects = Formation.objects.filter(id__in=formations_avec_prospects_ids)
        
        if formations_ids:
            formations_avec_prospects = formations_avec_prospects.filter(id__in=formations_ids)
        
        for f in formations_avec_prospects:
            count = Prospect.objects.filter(
                formations_souhaitees__id=f.id
            ).exclude(email__isnull=True).exclude(email='').count()
            
            if count > 0:
                formations_data.append({
                    'id': f.id,
                    'intitule': f.intitule,
                    'nombre': count
                })
        return formations_data
        
    elif type_groupe == 'etudiants':
        formations_avec_etudiants_ids = Etudiant.objects.filter(
            formations_suivies__isnull=False
        ).exclude(
            email__isnull=True
        ).exclude(
            email=''
        ).values_list('formations_suivies__id', flat=True).distinct()
        
        formations_avec_etudiants = Formation.objects.filter(id__in=formations_avec_etudiants_ids)
        
        if formations_ids:
            formations_avec_etudiants = formations_avec_etudiants.filter(id__in=formations_ids)
        
        for f in formations_avec_etudiants:
            count = Etudiant.objects.filter(
                formations_suivies__id=f.id
            ).exclude(email__isnull=True).exclude(email='').count()
            
            if count > 0:
                formations_data.append({
                    'id': f.id,
                    'intitule': f.intitule,
                    'nombre': count
                })
        return formations_data
        
    elif type_groupe == 'diplomes':
        formations_avec_diplomes_ids = Diplome.objects.filter(
            statut='delivre',
            formation__isnull=False
        ).exclude(
            email__isnull=True
        ).exclude(
            email=''
        ).values_list('formation__id', flat=True).distinct()
        
        formations_avec_diplomes = Formation.objects.filter(id__in=formations_avec_diplomes_ids)
        
        if formations_ids:
            formations_avec_diplomes = formations_avec_diplomes.filter(id__in=formations_ids)
        
        for f in formations_avec_diplomes:
            count = Diplome.objects.filter(
                formation__id=f.id,
                statut='delivre'
            ).exclude(email__isnull=True).exclude(email='').count()
            
            if count > 0:
                formations_data.append({
                    'id': f.id,
                    'intitule': f.intitule,
                    'nombre': count
                })
        return formations_data
    
    return []


def get_statuts_disponibles(type_groupe, formations_ids=None):
    """
    Récupère les statuts disponibles pour les prospects en fonction des formations sélectionnées
    """
    if type_groupe != 'prospects':
        return []
    
    qs = Prospect.objects.exclude(email__isnull=True).exclude(email='')
    if formations_ids and len(formations_ids) > 0:
        qs = qs.filter(formations_souhaitees__id__in=formations_ids).distinct()
    
    statuts = qs.values_list('statut', flat=True).distinct()
    statuts_labels = {
        'nouveau': 'Nouveau',
        'contacte': 'Contacté',
        'interesse': 'Intéressé',
        'converti': 'Converti',
        'perdu': 'Perdu',
    }
    
    result = []
    for s in statuts:
        if s and s in statuts_labels:
            count = qs.filter(statut=s).count()
            result.append({
                'value': s,
                'label': statuts_labels[s],
                'nombre': count
            })
    return result


def envoyer_emails(marketing_email_obj, destinataires_list, fichier=None):
    sent_count = 0
    destinataires_a_creer = []

    for dest in destinataires_list:
        try:
            email_msg = EmailMessage(
                subject=marketing_email_obj.objet,
                body=marketing_email_obj.message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[dest['email']],
            )

            if marketing_email_obj.apercu:
                email_msg.extra_headers['X-Preview'] = marketing_email_obj.apercu

            if fichier:
                fichier.seek(0)
                email_msg.attach(fichier.name, fichier.read(), fichier.content_type)
                fichier.seek(0)

            email_msg.send(fail_silently=False)
            sent_count += 1

            dest_obj = DestinatairEmail(
                email_marketing=marketing_email_obj,
                email_adresse=dest['email'],
                type_destinataire=dest['type'],
            )
            if dest['modele'] == 'prospect':
                dest_obj.prospect_id = dest['objet_id']
            elif dest['modele'] == 'etudiant':
                dest_obj.etudiant_id = dest['objet_id']
            elif dest['modele'] == 'diplome':
                dest_obj.diplome_id = dest['objet_id']

            destinataires_a_creer.append(dest_obj)

        except Exception as e:
            print(f"Erreur envoi à {dest['email']}: {str(e)}")

    if destinataires_a_creer:
        DestinatairEmail.objects.bulk_create(destinataires_a_creer, ignore_conflicts=True)

    marketing_email_obj.nombre_destinataires = sent_count
    marketing_email_obj.save(update_fields=['nombre_destinataires'])

    return sent_count


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def liste_emails(request):
    archive = request.query_params.get('archive', 'false').lower() == 'true'
    groupe = request.query_params.get('groupe', '')
    search = request.query_params.get('search', '')
    date_unique = request.query_params.get('date_unique', '')  # CHANGÉ: un seul paramètre
    direct = request.query_params.get('direct', 'false').lower() == 'true'

    print(f"🔍 FILTRES REÇUS: archive={archive}, groupe={groupe}, search={search}, date_unique={date_unique}, direct={direct}")

    qs = MarketingEmail.objects.select_related('envoye_par').prefetch_related('formations_cibles')
    qs = qs.filter(est_archive=archive)

    # Filtrer par mode direct
    if direct:
        qs = qs.filter(send_mode='direct')
    
    if groupe:
        qs = qs.filter(groupe=groupe)
    if search:
        qs = qs.filter(Q(objet__icontains=search) | Q(envoye_par__email__icontains=search))
    
    # FILTRE DATE UNIQUE — plage datetime avec timezone pour éviter le décalage UTC
    if date_unique and date_unique != 'Invalid Date' and len(date_unique) == 10:
        try:
            from datetime import datetime, time as dt_time
            from django.utils import timezone as dj_timezone

            date_obj = datetime.strptime(date_unique, "%Y-%m-%d").date()
            tz = dj_timezone.get_current_timezone()

            debut_journee = dj_timezone.make_aware(
                datetime.combine(date_obj, dt_time.min), tz
            )
            fin_journee = dj_timezone.make_aware(
                datetime.combine(date_obj, dt_time.max), tz
            )

            qs = qs.filter(date_envoi__range=(debut_journee, fin_journee))
            print(f"📅 Filtre date: {date_obj} → [{debut_journee} ... {fin_journee}]")
        except (ValueError, TypeError) as e:
            print(f"❌ Erreur parsing date: {e}")

    print(f"📊 Nombre d'emails trouvés: {qs.count()}")
    serializer = MarketingEmailListSerializer(qs, many=True)
    return Response(serializer.data)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
@parser_classes([MultiPartParser, FormParser, JSONParser])
def creer_envoyer_email(request):
    print("=" * 50)
    print("DONNÉES REÇUES:")
    print("request.data:", request.data)
    print("request.FILES:", request.FILES)
    print("=" * 50)
    
    # Récupérer les données
    data = {}
    
    # Extraire les champs simples
    data['send_mode'] = request.data.get('send_mode', 'segment')
    data['objet'] = request.data.get('objet', '')
    data['apercu'] = request.data.get('apercu', '')
    data['message'] = request.data.get('message', '')
    
    if data['send_mode'] == 'direct':
        data['email_direct'] = request.data.get('email_direct', '')
    else:
        data['groupe'] = request.data.get('groupe', '')
        
        # Extraire formations_cibles
        formations_raw = request.data.get('formations_cibles', '[]')
        if isinstance(formations_raw, str):
            try:
                data['formations_cibles'] = json.loads(formations_raw)
            except:
                data['formations_cibles'] = []
        else:
            data['formations_cibles'] = formations_raw if isinstance(formations_raw, list) else []
        
        # Extraire statuts_prospects
        statuts_raw = request.data.get('statuts_prospects', '[]')
        if isinstance(statuts_raw, str):
            try:
                data['statuts_prospects'] = json.loads(statuts_raw)
            except:
                data['statuts_prospects'] = []
        else:
            data['statuts_prospects'] = statuts_raw if isinstance(statuts_raw, list) else []
        
        # Extraire sources_prospects
        sources_raw = request.data.get('sources_prospects', '[]')
        if isinstance(sources_raw, str):
            try:
                data['sources_prospects'] = json.loads(sources_raw)
            except:
                data['sources_prospects'] = []
        else:
            data['sources_prospects'] = sources_raw if isinstance(sources_raw, list) else []
        
        # Récupérer les emails sélectionnés
        emails_selected_raw = request.data.get('emails_selected', '[]')
        if isinstance(emails_selected_raw, str):
            try:
                emails_selected = json.loads(emails_selected_raw)
            except:
                emails_selected = []
        else:
            emails_selected = emails_selected_raw if isinstance(emails_selected_raw, list) else []
        data['emails_selected'] = emails_selected
    
    print("DONNÉES PARSÉES:", data)
    
    fichier = request.FILES.get('fichier', None)
    
    # Créer l'objet MarketingEmail
    try:
        marketing_email = MarketingEmail.objects.create(
            envoye_par=request.user,
            send_mode=data['send_mode'],
            objet=data['objet'],
            apercu=data['apercu'],
            message=data['message'],
            email_direct=data.get('email_direct', ''),
            groupe=data.get('groupe', ''),
            statuts_prospects=data.get('statuts_prospects', []),
            sources_prospects=data.get('sources_prospects', []),
            fichier=fichier
        )
        
        # Ajouter les formations
        formations_ids = data.get('formations_cibles', [])
        if formations_ids:
            formations = Formation.objects.filter(id__in=formations_ids)
            marketing_email.formations_cibles.set(formations)
        
        print(f"Email créé avec ID: {marketing_email.id}")
        
    except Exception as e:
        print(f"Erreur création email: {str(e)}")
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
    # Construire la liste de destinataires
    if data['send_mode'] == 'direct':
        destinataires = [{
            'email': data['email_direct'],
            'type': 'direct',
            'objet_id': None,
            'modele': 'direct',
            'nom': data['email_direct'],
            'ville': "—",
            'telephone': "—",
            'formation': "—",
            'statut': "—",
            'date_inscription': "—"
        }]
    else:
        formations_ids = data.get('formations_cibles', [])
        statuts = data.get('statuts_prospects', [])
        sources = data.get('sources_prospects', [])
        groupe = data.get('groupe', '')
        emails_selected = data.get('emails_selected', [])
        
        # Récupérer tous les destinataires selon les filtres
        tous_destinataires = get_destinataires_segment(groupe, formations_ids, statuts, sources)
        
        # APPLIQUER LE FILTRE DES EMAILS SÉLECTIONNÉS
        if emails_selected and len(emails_selected) > 0:
            destinataires = [d for d in tous_destinataires if d['email'] in emails_selected]
            print(f"Filtrage appliqué: {len(tous_destinataires)} -> {len(destinataires)} destinataires sélectionnés")
        else:
            destinataires = tous_destinataires
            print(f"Aucun filtre, envoi à tous les {len(destinataires)} destinataires")
    
    print(f"Destinataires finaux: {len(destinataires)}")
    
    # Envoyer les emails
    sent_count = envoyer_emails(marketing_email, destinataires, fichier=fichier)
    
    return Response({
        'message': f'Email envoyé à {sent_count} destinataire(s).',
        'email': {
            'id': marketing_email.id,
            'objet': marketing_email.objet,
            'envoye_par_email': marketing_email.envoye_par.email if marketing_email.envoye_par else "—",
            'groupe': marketing_email.groupe,
            'groupe_display': marketing_email.groupe_display,
            'nombre_destinataires': marketing_email.nombre_destinataires,
            'est_archive': marketing_email.est_archive,
            'send_mode': marketing_email.send_mode,
            'date': marketing_email.date_envoi.strftime('%d/%m/%Y'),
        }
    }, status=status.HTTP_201_CREATED)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def detail_email(request, pk):
    try:
        email = MarketingEmail.objects.prefetch_related(
            'formations_cibles', 'destinataires'
        ).select_related('envoye_par').get(pk=pk)
    except MarketingEmail.DoesNotExist:
        return Response({'error': 'Email non trouvé.'}, status=status.HTTP_404_NOT_FOUND)

    serializer = MarketingEmailSerializer(email)
    return Response(serializer.data)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def archiver_emails(request):
    serializer = ArchiveEmailSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    ids = serializer.validated_data['ids']
    updated = MarketingEmail.objects.filter(id__in=ids).update(est_archive=True)
    return Response({'message': f'{updated} email(s) archivé(s).'})


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def supprimer_emails(request):
    """Supprimer définitivement des emails"""
    serializer = ArchiveEmailSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    ids = serializer.validated_data['ids']
    # Supprimer d'abord les destinataires liés
    DestinatairEmail.objects.filter(email_marketing_id__in=ids).delete()
    # Puis supprimer les emails
    deleted, _ = MarketingEmail.objects.filter(id__in=ids).delete()
    return Response({'message': f'{deleted} email(s) supprimé(s).'})


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def estimer_destinataires(request):
    print("Estimation - Données reçues:", request.data)
    
    serializer = EstimationDestinatairesSerializer(data=request.data)
    if not serializer.is_valid():
        print("Erreurs validation:", serializer.errors)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    data = serializer.validated_data
    groupe = data['groupe']
    formations_ids = data.get('formations_cibles', [])
    statuts = data.get('statuts_prospects', [])
    sources = data.get('sources_prospects', [])

    destinataires = get_destinataires_segment(groupe, formations_ids, statuts, sources)
    return Response({'nombre': len(destinataires), 'destinataires': destinataires})


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def liste_formations_marketing(request):
    formations = Formation.objects.all().order_by('intitule')
    serializer = FormationSerializer(formations, many=True)
    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def liste_formations_par_type(request, type_groupe):
    formations = get_formations_par_type_avec_comptage(type_groupe)
    return Response(formations)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def liste_statuts_par_formations(request):
    type_groupe = request.query_params.get('type_groupe', 'prospects')
    formations_ids = request.query_params.get('formations_ids', '')
    
    if formations_ids:
        formations_ids = [int(id) for id in formations_ids.split(',') if id]
    else:
        formations_ids = []
    
    statuts = get_statuts_disponibles(type_groupe, formations_ids)
    return Response(statuts)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def debug_emails(request):
    emails = MarketingEmail.objects.all().order_by('-date_envoi')
    data = []
    for e in emails:
        data.append({
            'id': e.id,
            'objet': e.objet,
            'date_envoi': str(e.date_envoi),
            'est_archive': e.est_archive,
            'groupe': e.groupe,
            'nombre_destinataires': e.nombre_destinataires,
        })
    return Response(data)