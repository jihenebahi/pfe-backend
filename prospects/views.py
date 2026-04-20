# prospects/views.py
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.shortcuts import get_object_or_404

from .models import Prospect, HistoriqueEchange, Relance
from django.utils import timezone

from .serializers import (
    ProspectSerializer,
    ProspectListSerializer,
    ProspectCreateUpdateSerializer,
    HistoriqueEchangeSerializer,
    RelanceSerializer,
    RelanceCreateSerializer

)


# ──────────────────────────────────────────────
#  LISTE + CRÉATION
# ──────────────────────────────────────────────
@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def prospect_list_create(request):
    if request.method == 'GET':
        queryset = Prospect.objects.select_related('responsable') \
                                   .prefetch_related('formations_souhaitees').all()

        statut = request.query_params.get('statut')
        source = request.query_params.get('source')
        search = request.query_params.get('search')

        if statut:
            queryset = queryset.filter(statut=statut)
        if source:
            queryset = queryset.filter(source=source)
        if search:
            queryset = queryset.filter(
                nom__icontains=search
            ) | queryset.filter(
                prenom__icontains=search
            ) | queryset.filter(
                email__icontains=search
            ) | queryset.filter(
                telephone__icontains=search
            )

        serializer = ProspectListSerializer(queryset, many=True)
        return Response(serializer.data)

    elif request.method == 'POST':
        serializer = ProspectCreateUpdateSerializer(data=request.data)
        if serializer.is_valid():
            x_forwarded = request.META.get('HTTP_X_FORWARDED_FOR')
            ip = x_forwarded.split(',')[0] if x_forwarded else request.META.get('REMOTE_ADDR')
            prospect = serializer.save(
                ip_address=ip,
                user_agent=request.META.get('HTTP_USER_AGENT', ''),
                responsable=request.user,
            )
            return Response(
                ProspectSerializer(prospect).data,
                status=status.HTTP_201_CREATED
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# ──────────────────────────────────────────────
#  DÉTAIL + MODIFICATION + SUPPRESSION
# ──────────────────────────────────────────────
@api_view(['GET', 'PUT', 'PATCH', 'DELETE'])
@permission_classes([IsAuthenticated])
def prospect_detail(request, pk):
    prospect = get_object_or_404(Prospect, pk=pk)

    if request.method == 'GET':
        serializer = ProspectSerializer(prospect)
        return Response(serializer.data)

    elif request.method in ['PUT', 'PATCH']:
        partial = request.method == 'PATCH'
        serializer = ProspectCreateUpdateSerializer(
            prospect, data=request.data, partial=partial
        )
        if serializer.is_valid():
            updated = serializer.save()
            return Response(ProspectSerializer(updated).data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    elif request.method == 'DELETE':
        prospect.delete()
        return Response(
            {'message': 'Prospect supprimé avec succès.'},
            status=status.HTTP_204_NO_CONTENT
        )


# ──────────────────────────────────────────────
#  HISTORIQUE DES ÉCHANGES
# ──────────────────────────────────────────────
@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def historique_list_create(request, prospect_pk):
    prospect = get_object_or_404(Prospect, pk=prospect_pk)

    if request.method == 'GET':
        historiques = prospect.historiques.all()
        serializer = HistoriqueEchangeSerializer(historiques, many=True)
        return Response(serializer.data)

    elif request.method == 'POST':
        serializer = HistoriqueEchangeSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(prospect=prospect, utilisateur=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# ──────────────────────────────────────────────
#  STATISTIQUES RAPIDES (dashboard)
# ──────────────────────────────────────────────
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def prospect_stats(request):
    from django.db.models import Count
    stats = Prospect.objects.values('statut').annotate(count=Count('id'))
    result = {item['statut']: item['count'] for item in stats}
    result['total'] = Prospect.objects.count()
    return Response(result)


# ──────────────────────────────────────────────
#  CONVERSION PROSPECT → ÉTUDIANT
# ──────────────────────────────────────────────
# prospects/views.py

from django.core.mail import send_mail
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def convert_to_etudiant(request, pk):
    from etudiants.models import Etudiant, Document
    from formation.models import Formation

    prospect = get_object_or_404(Prospect, pk=pk)

    STATUT_MAP = {
        'Actif':     'actif',
        'Abandonné': 'abandonne',
        'Certifié':  'certifie',
    }
    DOCUMENT_TYPE_MAP = {
        'CIN':    'cin',
        'CV':     'cv',
        'Contrat':'contrat',
        'Reçu':   'recu',
        'RNE':    'rne',
        'Autres': 'autre',
    }

    statut            = STATUT_MAP.get(request.data.get('statut_etudiant', 'Actif'), 'actif')
    formations_ids    = request.data.get('formations_ids', [])
    notes             = request.data.get('notes', '')
    documents_fournis = request.data.get('documents_fournis', [])

    # Création de l'étudiant
    etudiant = Etudiant(
        nom            = prospect.nom,
        prenom         = prospect.prenom,
        email          = prospect.email,
        telephone      = prospect.telephone,
        ville          = prospect.ville,
        pays           = prospect.pays,
        date_naissance = prospect.date_naissance,
        genre          = prospect.genre,
        niveau_etudes  = prospect.niveau_etudes,
        diplome_obtenu = prospect.diplome_obtenu,
        statut         = statut,
        mode_paiement  = 'espece',
        responsable    = request.user,
        notes          = notes,
    )
    etudiant.save()

    # Documents
    for doc in documents_fournis:
        doc_type = DOCUMENT_TYPE_MAP.get(doc, 'autre')
        Document.objects.create(
            etudiant=etudiant,
            type_document=doc_type,
            fichier=None,
            commentaire=f"Document fourni en version physique : {doc}"
        )

    # Récupération des formations
    if formations_ids:
        formations = Formation.objects.filter(id__in=formations_ids)
    else:
        formations = prospect.formations_souhaitees.all()

    if formations.exists():
        etudiant.formations_suivies.set(formations)

    # ─────────────────────────────────────────────────────────────
    # ENVOI D'EMAIL DE BIENVENUE (un email par formation)
    # ─────────────────────────────────────────────────────────────
    subject = "Bienvenue au centre de formation 4C Lab"

    for formation in formations:
        # Construction du nom complet
        nom_complet = f"{etudiant.prenom} {etudiant.nom}".strip()

        # Formatage de la date de début
        if formation.date_debut:
            date_formatee = formation.date_debut.strftime("%d %B %Y")
        else:
            date_formatee = "prochainement"

        # Message exact selon votre demande
        message = f"""Bonjour {nom_complet},

Bienvenue au centre de formation 4C Lab.
Nous sommes ravis de vous compter parmi nos étudiants.

Nous avons le plaisir de vous informer que votre formation « {formation.intitule} » débutera le {date_formatee}.
Nous vous invitons à vous préparer pour une expérience d'apprentissage enrichissante et dynamique.

Notre équipe pédagogique vous accompagnera tout au long de votre parcours afin de vous garantir une formation de qualité.

Nous vous souhaitons une excellente réussite dans votre formation.

Cordialement,
L'équipe 4C Lab"""

        try:
            send_mail(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL,
                [etudiant.email],
                fail_silently=False,
            )
            logger.info(f"Email de bienvenue envoyé à {etudiant.email} pour la formation {formation.intitule}")
        except Exception as e:
            logger.error(f"Erreur lors de l'envoi de l'email à {etudiant.email} : {str(e)}")

    # Suppression du prospect
    prospect.delete()

    return Response(
        {'message': 'Prospect converti en étudiant avec succès.', 'etudiant_id': etudiant.id},
        status=status.HTTP_201_CREATED
    )

# ──────────────────────────────────────────────
#  IMPORT EXCEL
# ──────────────────────────────────────────────
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def import_prospects_excel(request):
    """
    POST /api/prospects/import/
    Reçoit un fichier Excel (.xlsx) et crée les prospects en masse.

    Retourne un rapport :
    {
      "created": 5,
      "errors":  [ { "ligne": 3, "nom": "Jean Dupont", "erreurs": ["Téléphone manquant"] } ],
      "total":   7
    }
    """
    import openpyxl
    import re
    from django.core.exceptions import ValidationError
    from django.core.validators import validate_email
    from formation.models import Formation

    # ── Fonction de validation du téléphone tunisien ──
    def validate_tunisian_phone(phone):
        """
        Valide un numéro de téléphone tunisien.
        FORMAT ACCEPTÉ : 8 chiffres commençant par 2,4,5,7,9
        
        Accepte et nettoie :
        - 55123456 (8 chiffres)
        - 55123456.0 (avec .0 d'Excel)
        - 21655123456 (avec indicatif 216)
        - +21655123456 (avec +216)
        - 0021655123456 (avec 00216)
        - 055123456 (avec 0 initial)
        - 55 123 456 (avec espaces)
        """
        if not phone:
            return False, "Numéro de téléphone vide"
        
        # Convertir en string et nettoyer
        phone_str = str(phone).strip()
        
        # Supprimer le .0 à la fin (format Excel)
        if phone_str.endswith('.0') and phone_str[:-2].replace('.', '').isdigit():
            phone_str = phone_str[:-2]
        
        # Supprimer le point décimal s'il reste
        if '.' in phone_str and phone_str.replace('.', '').isdigit():
            phone_str = phone_str.replace('.', '')
        
        # Nettoyer : garder uniquement les chiffres
        cleaned = re.sub(r'[^\d]', '', phone_str)
        
        # Préfixes valides pour la Tunisie (mobile et fixe)
        valid_prefixes = ['2', '4', '5', '7', '9']
        
        # CAS 1 : déjà 8 chiffres ET commence par un préfixe valide
        if len(cleaned) == 8 and cleaned[0] in valid_prefixes:
            return True, cleaned
        
        # CAS 2 : 9 chiffres avec 0 initial (0XXXXXXXX)
        if len(cleaned) == 9 and cleaned[0] == '0' and cleaned[1] in valid_prefixes:
            return True, cleaned[1:]
        
        # CAS 3 : 11 chiffres avec 216 (216XXXXXXXX)
        if len(cleaned) == 11 and cleaned.startswith('216') and cleaned[3] in valid_prefixes:
            return True, cleaned[3:]
        
        # CAS 4 : 13 chiffres avec 00216 (00216XXXXXXXX)
        if len(cleaned) == 13 and cleaned.startswith('00216') and cleaned[5] in valid_prefixes:
            return True, cleaned[5:]
        
        return False, "Numéro invalide. Format attendu : 8 chiffres commençant par 2,4,5,7 ou 9 (ex: 55123456 ou 21655123456)"

    # ── 1. Vérifier qu'un fichier a bien été envoyé ──
    if 'file' not in request.FILES:
        return Response(
            {'error': 'Aucun fichier reçu. Envoyez un fichier Excel avec le champ "file".'},
            status=status.HTTP_400_BAD_REQUEST
        )

    excel_file = request.FILES['file']

    # ── 2. Vérifier l'extension ──
    if not excel_file.name.endswith('.xlsx'):
        return Response(
            {'error': 'Format invalide. Seuls les fichiers .xlsx sont acceptés.'},
            status=status.HTTP_400_BAD_REQUEST
        )

    # ── 3. Ouvrir le fichier ──
    try:
        workbook = openpyxl.load_workbook(excel_file)
        sheet    = workbook.active
    except Exception:
        return Response(
            {'error': 'Impossible de lire le fichier. Vérifiez qu\'il n\'est pas corrompu.'},
            status=status.HTTP_400_BAD_REQUEST
        )

    # ── 4. Lire les en-têtes (ligne 1) ──
    headers = [
        str(cell.value).strip().lower() if cell.value else ''
        for cell in sheet[1]
    ]

    # ── 5. Correspondance nom de colonne Excel → champ Django ──
    COLUMN_MAP = {
        'nom':             'nom',
        'prenom':          'prenom',
        'prénom':          'prenom',
        'email':           'email',
        'telephone':       'telephone',
        'téléphone':       'telephone',
        'tel':             'telephone',
        'ville':           'ville',
        'pays':            'pays',
        'source':          'source',
        'statut':          'statut',
        'niveau':          'niveau_estime',
        'niveau_estime':   'niveau_estime',
        'mode':            'mode_prefere',
        'mode_prefere':    'mode_prefere',
        'commentaires':    'commentaires',
        'date_naissance':  'date_naissance',
        'genre':           'genre',
        'niveau_etudes':   'niveau_etudes',
        'diplome':         'diplome_obtenu',
        'diplome_obtenu':  'diplome_obtenu',
        'formations':      'formations_souhaitees',
        'formations_souhaitees': 'formations_souhaitees',
    }

    # ── 6. Construire l'index des colonnes présentes dans CE fichier ──
    col_index = {}
    for idx, header in enumerate(headers):
        if header in COLUMN_MAP:
            col_index[COLUMN_MAP[header]] = idx

    # ── 7. Vérifier les colonnes obligatoires ──
    required_fields = ['nom', 'prenom', 'telephone', 'formations_souhaitees']
    missing = [f for f in required_fields if f not in col_index]
    if missing:
        missing_display = []
        for m in missing:
            if m == 'formations_souhaitees':
                missing_display.append('formations')
            else:
                missing_display.append(m)
        return Response(
            {'error': f'Colonnes obligatoires manquantes : {", ".join(missing_display)}'},
            status=status.HTTP_400_BAD_REQUEST
        )

    # ── 8. Tables de correspondance valeur lisible → slug Django ──
    PAYS_MAP = {
        'tunisie': 'tunisie', 'france': 'france',
        'algérie': 'algerie', 'algerie': 'algerie',
        'maroc':   'maroc',   'belgique': 'belgique',
        'canada':  'canada',  'autre': 'autre',
    }
    SOURCE_MAP = {
        'facebook': 'facebook', 'instagram': 'instagram', 'tiktok': 'tiktok',
        'linkedin': 'linkedin', 'google': 'google',
        'site web': 'site_web', 'site_web': 'site_web',
        'recommandation': 'recommandation',
        'appel entrant': 'appel_entrant', 'appel_entrant': 'appel_entrant',
        'autre': 'autre',
    }
    NIVEAU_MAP = {
        'débutant': 'debutant', 'debutant': 'debutant',
        'intermédiaire': 'intermediaire', 'intermediaire': 'intermediaire',
        'avancé': 'avance', 'avance': 'avance',
    }
    MODE_MAP = {
        'présentiel': 'presentiel', 'presentiel': 'presentiel',
        'en ligne': 'en_ligne',     'en_ligne': 'en_ligne',
        'hybride': 'hybride',
    }
    STATUT_MAP = {
        'nouveau': 'nouveau',
        'contacté': 'contacte', 'contacte': 'contacte',
        'intéressé': 'interesse', 'interesse': 'interesse',
        'converti': 'converti',
        'perdu': 'perdu',
    }
    GENRE_MAP = {
        'homme': 'homme', 'femme': 'femme', 'autre': 'autre',
    }
    NIVEAU_ETUDES_MAP = {
        'primaire': 'primaire',
        'préparatoire': 'preparatoire', 'preparatoire': 'preparatoire',
        'secondaire': 'secondaire',
        'universitaire': 'universitaire',
    }
    DIPLOME_MAP = {
        'bac': 'bac', 'licence': 'licence', 'master': 'master', 'autre': 'autre',
    }

    # ── 9. Fonction utilitaire pour lire une cellule ──
    def get_val(row, field):
        """Retourne la valeur texte d'une cellule, ou '' si colonne absente / cellule vide."""
        if field not in col_index:
            return ''
        cell = row[col_index[field]]
        if cell.value is not None:
            value = str(cell.value).strip()
            # ✅ NETTOYAGE : Supprimer le .0 à la fin (Excel number format)
            if value.endswith('.0') and value[:-2].replace('.', '').isdigit():
                value = value[:-2]
            return value
        return ''

    # ── 10. Fonction pour obtenir les IDs des formations à partir des noms ──
    def get_formation_ids(formations_str):
        """Convertit une chaîne de noms de formations (séparés par des virgules ou points-virgules) en liste d'IDs."""
        if not formations_str:
            return [], []
        
        # Séparer par virgule ou point-virgule
        formation_names = []
        for sep in [',', ';', '|']:
            if sep in formations_str:
                formation_names = [name.strip() for name in formations_str.split(sep)]
                break
        if not formation_names:
            formation_names = [formations_str.strip()]
        
        # Rechercher les formations par leur intitulé
        formation_ids = []
        missing_formations = []
        
        for name in formation_names:
            if name:
                try:
                    formation = Formation.objects.get(intitule__iexact=name)
                    formation_ids.append(formation.id)
                except Formation.DoesNotExist:
                    missing_formations.append(name)
                except Formation.MultipleObjectsReturned:
                    formation = Formation.objects.filter(intitule__iexact=name).first()
                    formation_ids.append(formation.id)
        
        return formation_ids, missing_formations

    # ── 11. Parcourir les lignes de données (à partir de la ligne 2) ──
    created_count = 0
    errors        = []

    for row_num, row in enumerate(sheet.iter_rows(min_row=2), start=2):

        # Ignorer les lignes entièrement vides
        if all(cell.value is None for cell in row):
            continue

        row_errors = []

        # Lecture des champs obligatoires
        nom       = get_val(row, 'nom')
        prenom    = get_val(row, 'prenom')
        telephone_raw = get_val(row, 'telephone')
        formations_str = get_val(row, 'formations_souhaitees')

        # ✅ Validation du téléphone tunisien
        telephone = ''
        if telephone_raw:
            is_valid, result = validate_tunisian_phone(telephone_raw)
            if is_valid:
                telephone = result  # On utilise le numéro normalisé sans indicatif
            else:
                row_errors.append(result)

        # email : lecture simple, pas obligatoire
        email = get_val(row, 'email')

        # ── Validation des champs obligatoires ──
        if not nom:
            row_errors.append('Nom manquant')
        if not prenom:
            row_errors.append('Prénom manquant')
        if not telephone_raw:
            row_errors.append('Téléphone manquant')
        elif not telephone:
            # Si le téléphone a été fourni mais est invalide, l'erreur a déjà été ajoutée
            pass

        # Validation du champ formations (obligatoire)
        if not formations_str:
            row_errors.append('Formations manquantes')
        else:
            formation_ids, missing_formations = get_formation_ids(formations_str)
            if missing_formations:
                row_errors.append(f'Formations non trouvées : {", ".join(missing_formations)}')
            if not formation_ids:
                row_errors.append('Aucune formation valide trouvée')

        # Validation de l'email SEULEMENT s'il est fourni
        if email:
            try:
                validate_email(email)
            except ValidationError:
                row_errors.append(f'Format d\'email invalide : {email}')

        # Unicité du téléphone (normalisé)
        if telephone and Prospect.objects.filter(telephone=telephone).exists():
            row_errors.append(f'Téléphone déjà utilisé : {telephone}')

        # Unicité de l'email (seulement s'il est fourni)
        if email and Prospect.objects.filter(email=email).exists():
            row_errors.append(f'Email déjà utilisé : {email}')

        # Mapping des champs avec choix
        ville    = get_val(row, 'ville')
        pays     = PAYS_MAP.get(get_val(row, 'pays').lower(),         'tunisie')
        source   = SOURCE_MAP.get(get_val(row, 'source').lower(),     'autre')
        niveau   = NIVEAU_MAP.get(get_val(row, 'niveau_estime').lower(), 'debutant')
        mode     = MODE_MAP.get(get_val(row, 'mode_prefere').lower(), 'presentiel')
        statut   = STATUT_MAP.get(get_val(row, 'statut').lower(),     'nouveau')
        genre    = GENRE_MAP.get(get_val(row, 'genre').lower(),       '')
        niv_etd  = NIVEAU_ETUDES_MAP.get(get_val(row, 'niveau_etudes').lower(), '')
        diplome  = DIPLOME_MAP.get(get_val(row, 'diplome_obtenu').lower(), '')

        # Date de naissance (optionnelle)
        date_naissance = None
        ddn_raw = get_val(row, 'date_naissance')
        if ddn_raw:
            from datetime import datetime
            
            # Nettoyage : ne garder que la partie date (avant l'espace)
            if ' ' in ddn_raw:
                ddn_raw = ddn_raw.split(' ')[0]
            
            # Supprimer les guillemets ou apostrophes
            ddn_raw = ddn_raw.strip('\'"')
            
            # Essayer plusieurs formats
            date_naissance = None
            for fmt in ['%Y-%m-%d', '%d/%m/%Y', '%d-%m-%Y', '%Y/%m/%d']:
                try:
                    date_naissance = datetime.strptime(ddn_raw, fmt).date()
                    break
                except ValueError:
                    continue
            
            if not date_naissance:
                row_errors.append(
                    f'Date de naissance invalide : {ddn_raw} '
                    f'(formats acceptés : JJ/MM/AAAA ou AAAA-MM-JJ)'
                )
                        # Si des erreurs → on enregistre et on passe à la ligne suivante
        if row_errors:
            errors.append({
                'ligne':   row_num,
                'nom':     f'{prenom} {nom}'.strip() or f'Ligne {row_num}',
                'erreurs': row_errors,
            })
            continue

        # Création du prospect
        try:
            prospect = Prospect.objects.create(
                nom            = nom,
                prenom         = prenom,
                email          = email,
                telephone      = telephone,  # Utiliser le numéro normalisé
                ville          = ville,
                pays           = pays,
                source         = source,
                niveau_estime  = niveau,
                mode_prefere   = mode,
                statut         = statut,
                genre          = genre,
                niveau_etudes  = niv_etd,
                diplome_obtenu = diplome,
                date_naissance = date_naissance,
                commentaires   = get_val(row, 'commentaires'),
                responsable    = request.user,
            )
            
            # Ajouter les formations
            formation_ids, _ = get_formation_ids(formations_str)
            if formation_ids:
                prospect.formations_souhaitees.set(formation_ids)
            
            created_count += 1

        except Exception as e:
            errors.append({
                'ligne':   row_num,
                'nom':     f'{prenom} {nom}'.strip(),
                'erreurs': [str(e)],
            })

    # ── 12. Rapport final ──
    return Response({
        'created': created_count,
        'errors':  errors,
        'total':   created_count + len(errors),
    }, status=status.HTTP_200_OK)


# ──────────────────────────────────────────────────────────────────────────────
#  1. LISTE DE TOUTES LES RELANCES  (dashboard Home)
#     GET  /api/prospects/relances/
# ──────────────────────────────────────────────────────────────────────────────
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def all_relances(request):
    """
    Retourne toutes les relances triées par date.
    Paramètres URL optionnels :
      ?statut=fait|en_retard|aujourd_hui|a_venir
    """
    from django.utils import timezone
    from datetime import date

    relances = Relance.objects.select_related('prospect', 'created_by', 'formation').all()

    statut_filter = request.query_params.get('statut')
    today = date.today()

    if statut_filter == 'fait':
        relances = relances.filter(statut='fait')
    elif statut_filter == 'en_retard':
        relances = relances.exclude(statut='fait').filter(date_relance__lt=today)
    elif statut_filter == 'aujourd_hui':
        relances = relances.exclude(statut='fait').filter(date_relance=today)
    elif statut_filter == 'a_venir':
        relances = relances.exclude(statut='fait').filter(date_relance__gt=today)
    # 'pending' = en_retard + aujourd_hui
    elif statut_filter == 'pending':
        relances = relances.exclude(statut='fait').filter(date_relance__lte=today)

    serializer = RelanceSerializer(relances, many=True)
    return Response(serializer.data)


# ──────────────────────────────────────────────────────────────────────────────
#  2. RELANCES D'UN PROSPECT
#     GET  /api/prospects/<pk>/relances/
#     POST /api/prospects/<pk>/relances/
# ──────────────────────────────────────────────────────────────────────────────
@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def relance_list_create(request, prospect_pk):
    prospect = get_object_or_404(Prospect, pk=prospect_pk)

    if request.method == 'GET':
        relances   = prospect.relances.select_related('formation').all()
        serializer = RelanceSerializer(relances, many=True)
        return Response(serializer.data)

    elif request.method == 'POST':
        serializer = RelanceCreateSerializer(data=request.data)
        if serializer.is_valid():
            # Si formation non fournie, utiliser la 1ère formation du prospect
            formation = serializer.validated_data.get('formation')
            if not formation:
                formation = prospect.formations_souhaitees.first()
            relance = serializer.save(
                prospect=prospect,
                created_by=request.user,
                formation=formation,
            )
            return Response(
                RelanceSerializer(relance).data,
                status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# ──────────────────────────────────────────────────────────────────────────────
#  3. DÉTAIL / MODIF / SUPPRESSION D'UNE RELANCE
#     GET    /api/relances/<pk>/
#     PATCH  /api/relances/<pk>/
#     DELETE /api/relances/<pk>/
# ──────────────────────────────────────────────────────────────────────────────
@api_view(['GET', 'PATCH', 'DELETE'])
@permission_classes([IsAuthenticated])
def relance_detail(request, pk):
    relance = get_object_or_404(Relance, pk=pk)

    if request.method == 'GET':
        return Response(RelanceSerializer(relance).data)

    elif request.method == 'PATCH':
        serializer = RelanceCreateSerializer(relance, data=request.data, partial=True)
        if serializer.is_valid():
            updated = serializer.save()
            return Response(RelanceSerializer(updated).data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    elif request.method == 'DELETE':
        relance.delete()
        return Response(
            {'message': 'Relance supprimée.'},
            status=status.HTTP_204_NO_CONTENT
        )


# ──────────────────────────────────────────────────────────────────────────────
#  4. ACTION "OK" — Appel effectué
#     POST /api/relances/<pk>/ok/
#
#  Body (optionnel) :
#  {
#    "notes": "Prospect rappelé, intéressé — rappeler la semaine prochaine"
#  }
#
#  Effets :
#    • statut  → 'fait'
#    • date_action → now()
#    • Crée un HistoriqueEchange de type 'appel'
# ──────────────────────────────────────────────────────────────────────────────
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def relance_action_ok(request, pk):
    from django.utils import timezone

    relance = get_object_or_404(Relance, pk=pk)

    # Marquer comme fait
    relance.statut      = 'fait'
    relance.date_action = timezone.now()
    relance.save()

    # Créer une entrée dans l'historique des échanges
    notes = request.data.get('notes', '')
    commentaire_histo = (
        f"Relance du {relance.date_relance.strftime('%d/%m/%Y')} effectuée. "
        + (f"Notes : {notes}" if notes else "")
    )
    HistoriqueEchange.objects.create(
        prospect     = relance.prospect,
        type_echange = 'appel',
        utilisateur  = request.user,
        contenu      = commentaire_histo,
        notes        = notes,
    )

    return Response(
        {
            'message':  'Relance marquée comme effectuée.',
            'relance':  RelanceSerializer(relance).data,
        },
        status=status.HTTP_200_OK
    )


# ──────────────────────────────────────────────────────────────────────────────
#  5. COMPTEUR DE RELANCES DU JOUR  (pour la navbar)
#     GET /api/relances/count-today/
# ──────────────────────────────────────────────────────────────────────────────
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def relances_count_today(request):
    from datetime import date
    today = date.today()
    count = Relance.objects.filter(
        date_relance__lte=today
    ).exclude(statut='fait').count()
    return Response({'count': count})