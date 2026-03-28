# prospects/views.py
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.shortcuts import get_object_or_404

from .models import Prospect, HistoriqueEchange
from .serializers import (
    ProspectSerializer,
    ProspectListSerializer,
    ProspectCreateUpdateSerializer,
    HistoriqueEchangeSerializer,
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

    for doc in documents_fournis:
        doc_type = DOCUMENT_TYPE_MAP.get(doc, 'autre')
        Document.objects.create(
            etudiant=etudiant,
            type_document=doc_type,
            fichier=None,
            commentaire=f"Document fourni en version physique : {doc}"
        )

    if formations_ids:
        formations = Formation.objects.filter(id__in=formations_ids)
        etudiant.formations_suivies.set(formations)
    else:
        etudiant.formations_suivies.set(prospect.formations_souhaitees.all())

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
    from django.core.exceptions import ValidationError
    from django.core.validators import validate_email

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
    }

    # ── 6. Construire l'index des colonnes présentes dans CE fichier ──
    # col_index = { 'champ_django': index_colonne }
    col_index = {}
    for idx, header in enumerate(headers):
        if header in COLUMN_MAP:
            col_index[COLUMN_MAP[header]] = idx

    # ── 7. Vérifier les colonnes obligatoires ──
    # ✅ email retiré des colonnes obligatoires
    required_fields = ['nom', 'prenom', 'telephone']
    missing = [f for f in required_fields if f not in col_index]
    if missing:
        return Response(
            {'error': f'Colonnes obligatoires manquantes : {", ".join(missing)}'},
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
        return str(cell.value).strip() if cell.value is not None else ''

    # ── 10. Parcourir les lignes de données (à partir de la ligne 2) ──
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
        telephone = get_val(row, 'telephone')

        # ✅ email : lecture simple, pas obligatoire
        email = get_val(row, 'email')

        # ── Validation des champs obligatoires ──
        if not nom:
            row_errors.append('Nom manquant')
        if not prenom:
            row_errors.append('Prénom manquant')
        if not telephone:
            row_errors.append('Téléphone manquant')

        # ── Validation de l'email SEULEMENT s'il est fourni ──
        # ✅ Si la cellule est vide → on passe, pas d'erreur
        # ✅ Si la cellule contient quelque chose → on vérifie le format
        if email:
            try:
                validate_email(email)
            except ValidationError:
                row_errors.append(f'Format d\'email invalide : {email}')

        # ── Unicité du téléphone ──
        if telephone and Prospect.objects.filter(telephone=telephone).exists():
            row_errors.append(f'Téléphone déjà utilisé : {telephone}')

        # ── Unicité de l'email (seulement s'il est fourni) ──
        # ✅ On ne bloque que si l'email est renseigné ET déjà en base
        if email and Prospect.objects.filter(email=email).exists():
            row_errors.append(f'Email déjà utilisé : {email}')

        # ── Mapping des champs avec choix ──
        ville    = get_val(row, 'ville')
        pays     = PAYS_MAP.get(get_val(row, 'pays').lower(),         'tunisie')
        source   = SOURCE_MAP.get(get_val(row, 'source').lower(),     'autre')
        niveau   = NIVEAU_MAP.get(get_val(row, 'niveau_estime').lower(), 'debutant')
        mode     = MODE_MAP.get(get_val(row, 'mode_prefere').lower(), 'presentiel')
        statut   = STATUT_MAP.get(get_val(row, 'statut').lower(),     'nouveau')
        genre    = GENRE_MAP.get(get_val(row, 'genre').lower(),       '')
        niv_etd  = NIVEAU_ETUDES_MAP.get(get_val(row, 'niveau_etudes').lower(), '')
        diplome  = DIPLOME_MAP.get(get_val(row, 'diplome_obtenu').lower(), '')

        # ── Date de naissance (optionnelle) ──
        date_naissance = None
        ddn_raw = get_val(row, 'date_naissance')
        if ddn_raw:
            from datetime import datetime
            for fmt in ['%Y-%m-%d', '%d/%m/%Y', '%d-%m-%Y']:
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

        # ── Si des erreurs → on enregistre et on passe à la ligne suivante ──
        if row_errors:
            errors.append({
                'ligne':   row_num,
                'nom':     f'{prenom} {nom}'.strip() or f'Ligne {row_num}',
                'erreurs': row_errors,
            })
            continue

        # ── Création du prospect ──
        try:
            Prospect.objects.create(
                nom            = nom,
                prenom         = prenom,
                email          = email,        # ✅ peut être '' si non fourni
                telephone      = telephone,
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
            created_count += 1

        except Exception as e:
            errors.append({
                'ligne':   row_num,
                'nom':     f'{prenom} {nom}'.strip(),
                'erreurs': [str(e)],
            })

    # ── 11. Rapport final ──
    return Response({
        'created': created_count,
        'errors':  errors,
        'total':   created_count + len(errors),
    }, status=status.HTTP_200_OK)