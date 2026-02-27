from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework import status
from django.db.models import Q
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from .serializers import LoginSerializer, ChangePasswordSerializer
from .models import User, PasswordResetCode
from django.core.mail import send_mail
from django.conf import settings
import re


def is_super_admin(user):
    if not user.is_authenticated:
        return False
    if user.role == 'super_admin':
        return True
    if user.is_superuser:
        User.objects.filter(pk=user.pk).update(role='super_admin')
        user.role = 'super_admin'
        return True
    return False


# ── AUTH ──────────────────────────────────────────────────────────

@api_view(['POST'])
@permission_classes([AllowAny])
def login(request):
    email = request.data.get('email', '').strip()
    password = request.data.get('password', '')

    if not email:
        return Response({
            'success': False, 'error': "L'email est requis",
            'field': 'email', 'error_type': 'required'
        }, status=status.HTTP_400_BAD_REQUEST)

    email_regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if not re.match(email_regex, email):
        return Response({
            'success': False, 'error': "Format d'email invalide",
            'field': 'email', 'error_type': 'invalid_format'
        }, status=status.HTTP_400_BAD_REQUEST)

    if not password:
        return Response({
            'success': False, 'error': 'Le mot de passe est requis',
            'field': 'password', 'error_type': 'required'
        }, status=status.HTTP_400_BAD_REQUEST)

    if len(password) < 3:
        return Response({
            'success': False,
            'error': 'Le mot de passe doit contenir au moins 3 caractères',
            'field': 'password', 'error_type': 'too_short'
        }, status=status.HTTP_400_BAD_REQUEST)

    try:
        user = User.objects.get(email=email)
        if not user.is_active:
            return Response({
                'success': False,
                'error': "Ce compte est désactivé. Contactez l'administrateur.",
                'field': 'general', 'error_type': 'inactive'
            }, status=status.HTTP_401_UNAUTHORIZED)

        authenticated_user = authenticate(username=user.username, password=password)
        if authenticated_user:
            auth_login(request, authenticated_user)
            return Response({
                'success': True, 'message': 'Connexion réussie',
                'user': {
                    'id': user.id, 'username': user.username,
                    'email': user.email, 'first_name': user.first_name,
                    'last_name': user.last_name, 'role': user.role, 'phone': user.phone,
                }
            }, status=status.HTTP_200_OK)
        else:
            return Response({
                'success': False, 'error': 'Mot de passe incorrect',
                'field': 'password', 'error_type': 'wrong_password'
            }, status=status.HTTP_401_UNAUTHORIZED)

    except User.DoesNotExist:
        return Response({
            'success': False, 'error': 'Aucun compte trouvé avec cet email',
            'field': 'email', 'error_type': 'not_found'
        }, status=status.HTTP_404_NOT_FOUND)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout_view(request):
    auth_logout(request)
    return Response({'success': True, 'message': 'Deconnexion reussie'}, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def me(request):
    user = request.user
    return Response({
        'id': user.id, 'username': user.username,
        'email': user.email, 'first_name': user.first_name,
        'last_name': user.last_name, 'role': user.role, 'phone': user.phone,
    }, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def change_password(request):
    serializer = ChangePasswordSerializer(data=request.data, context={'request': request})
    if serializer.is_valid():
        user = request.user
        new_password = serializer.validated_data['new_password']
        user.set_password(new_password)
        user.password_plain = new_password
        user.save()
        auth_login(request, user)
        
        return Response({'success': True, 'message': 'Mot de passe change avec succes'}, status=status.HTTP_200_OK)
    return Response({'success': False, 'errors': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)


# ── GESTION DES COMPTES ───────────────────────────────────────────

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_users(request):
    queryset = User.objects.all().order_by('id')
    search = request.query_params.get('search', '').strip()
    role   = request.query_params.get('role', '').strip()
    active = request.query_params.get('is_active', '').strip()

    if search:
        queryset = queryset.filter(
            Q(first_name__icontains=search) | Q(last_name__icontains=search) |
            Q(email__icontains=search)      | Q(username__icontains=search)
        )
    if role:
        queryset = queryset.filter(role=role)
    if active in ('true', 'false'):
        queryset = queryset.filter(is_active=(active == 'true'))

    data = []
    for idx, user in enumerate(queryset, start=1):
        full_name = f"{user.first_name} {user.last_name}".strip() or user.username
        initiales = (
            (user.first_name[0] + user.last_name[0]).upper()
            if user.first_name and user.last_name
            else user.username[:2].upper()
        )
        data.append({
            'id':        user.id,
            'numero':    str(idx).zfill(2),
            'code':      f'#USR-{str(user.id).zfill(3)}',
            'nom':       full_name,
            'initiales': initiales,
            'email':     user.email,
            'role':      user.role,
            'is_active': user.is_active,
        })

    return Response({
        'success': True, 'count': len(data),
        'can_manage': is_super_admin(request.user),
        'users': data,
    }, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_user(request):
    if not is_super_admin(request.user):
        return Response(
            {'success': False, 'message': 'Accès refusé. Réservé au Super Administrateur.'},
            status=status.HTTP_403_FORBIDDEN
        )

    first_name = request.data.get('first_name', '').strip()
    last_name  = request.data.get('last_name',  '').strip()
    email      = request.data.get('email',      '').strip().lower()
    phone      = request.data.get('phone',      '').strip()
    role       = request.data.get('role',       '').strip()
    is_active  = request.data.get('is_active',  True)
    password   = request.data.get('password',   '')

    if isinstance(is_active, str):
        is_active = is_active.lower() in ('true', '1', 'actif')

    errors = {}
    if not first_name:
        errors['first_name'] = 'Le prénom est obligatoire.'
    elif len(first_name) < 2:
        errors['first_name'] = 'Le prénom doit contenir au moins 2 caractères.'
    if not last_name:
        errors['last_name'] = 'Le nom est obligatoire.'
    elif len(last_name) < 2:
        errors['last_name'] = 'Le nom doit contenir au moins 2 caractères.'

    email_regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if not email:
        errors['email'] = "L'adresse e-mail est obligatoire."
    elif not re.match(email_regex, email):
        errors['email'] = "Format d'e-mail invalide."
    elif User.objects.filter(email=email).exists():
        errors['email'] = 'Un compte avec cet e-mail existe déjà.'

    valid_roles = [r[0] for r in User.ROLE_CHOICES]
    if not role:
        errors['role'] = 'Le rôle est obligatoire.'
    elif role not in valid_roles:
        errors['role'] = f'Rôle invalide. Valeurs acceptées : {", ".join(valid_roles)}.'
    if not password:
        errors['password'] = 'Le mot de passe est obligatoire.'
    elif len(password) < 8:
        errors['password'] = 'Le mot de passe doit contenir au moins 8 caractères.'

    if errors:
        return Response(
            {'success': False, 'message': 'Données invalides.', 'errors': errors},
            status=status.HTTP_400_BAD_REQUEST
        )

    base_username = re.sub(r'[^a-z0-9]', '', f"{first_name}{last_name}".lower()) or email.split('@')[0]
    username = base_username
    counter  = 1
    while User.objects.filter(username=username).exists():
        username = f"{base_username}{counter}"
        counter += 1

    user = User.objects.create_user(
        username=username, email=email, password=password,
        first_name=first_name, last_name=last_name,
        role=role, phone=phone, is_active=is_active,
    )
    # Sauvegarde du mot de passe en clair pour affichage dans DetailsCompte
    user.password_plain = password
    user.save(update_fields=['password_plain'])

    full_name = f"{user.first_name} {user.last_name}".strip()
    return Response({
        'success': True,
        'message': f'Le compte de {full_name} a été créé avec succès.',
        'user': {
            'id': user.id, 'code': f'#USR-{str(user.id).zfill(3)}',
            'nom': full_name, 'email': user.email,
            'role': user.role, 'is_active': user.is_active,
        }
    }, status=status.HTTP_201_CREATED)


@api_view(['PATCH'])
@permission_classes([IsAuthenticated])
def toggle_user_status(request, user_id):
    if not is_super_admin(request.user):
        return Response({'success': False, 'message': 'Acces refuse.'}, status=status.HTTP_403_FORBIDDEN)
    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return Response({'success': False, 'message': 'Utilisateur introuvable.'}, status=status.HTTP_404_NOT_FOUND)
    if user.id == request.user.id:
        return Response({'success': False, 'message': 'Vous ne pouvez pas modifier votre propre statut.'}, status=status.HTTP_400_BAD_REQUEST)
    user.is_active = not user.is_active
    user.save()
    return Response({
        'success': True,
        'message': f"Utilisateur {'active' if user.is_active else 'desactive'} avec succes.",
        'is_active': user.is_active,
    }, status=status.HTTP_200_OK)


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_user(request, user_id):
    if not is_super_admin(request.user):
        return Response({'success': False, 'message': 'Acces refuse.'}, status=status.HTTP_403_FORBIDDEN)
    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return Response({'success': False, 'message': 'Utilisateur introuvable.'}, status=status.HTTP_404_NOT_FOUND)
    if user.id == request.user.id:
        return Response({'success': False, 'message': 'Vous ne pouvez pas supprimer votre propre compte.'}, status=status.HTTP_400_BAD_REQUEST)
    user.delete()
    return Response({'success': True, 'message': 'Utilisateur supprime avec succes.'}, status=status.HTTP_200_OK)


# ═══════════════════════════════════════════════════════════════════
# ── MOT DE PASSE OUBLIÉ ───────────────────────────────────────────
# ═══════════════════════════════════════════════════════════════════

@api_view(['POST'])
@permission_classes([AllowAny])
def request_password_reset(request):
    email = request.data.get('email', '').strip().lower()

    if not email:
        return Response({'success': False, 'error': "Email requis"}, status=400)

    email_regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if not re.match(email_regex, email):
        return Response({'success': False, 'error': "Format d'email invalide"}, status=400)

    # ✅ FIX 1 : iexact → insensible à la casse (évite "not found" si casse différente en DB)
    try:
        user = User.objects.get(email__iexact=email)
    except User.DoesNotExist:
        return Response({
            'success': False,
            'error': 'Aucun compte trouvé avec cet email'
        }, status=404)

    # Invalider les anciens codes
    PasswordResetCode.objects.filter(user=user, is_used=False).update(is_used=True)

    # Générer le nouveau code
    code = PasswordResetCode.generate_code()
    PasswordResetCode.objects.create(user=user, email=user.email, code=code)

    # ✅ FIX 2 : send_mail dans son propre try/except
    # CAUSE DU BUG : si send_mail plante, l'exception n'était pas catchée
    # par "except User.DoesNotExist" → Django retournait 500
    # → axios recevait une erreur sans data.error
    # → React affichait "Aucun compte trouvé avec cet email" par défaut
    try:
        send_mail(
            subject='Code de réinitialisation - 4CLab',
            message=(
                f'Bonjour,\n\n'
                f'Votre code de réinitialisation est : {code}\n\n'
                f'Ce code est valable 5 minutes.\n\n'
                f"Si vous n'avez pas demandé cette réinitialisation, ignorez cet email.\n\n"
                f'— Équipe 4CLab'
            ),
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            fail_silently=False,
        )
    except Exception as mail_error:
        # En mode développement (console backend), le code s'affiche dans le terminal Django
        print(f"[INFO] Email non envoyé (mode dev): {mail_error}")
        print(f"[INFO] CODE DE RÉINITIALISATION POUR {user.email} : {code}")

    return Response({
        'success': True,
        'message': 'Code envoyé par email'
    })


@api_view(['POST'])
@permission_classes([AllowAny])
def verify_reset_code(request):
    email = request.data.get('email', '').strip().lower()
    code  = request.data.get('code', '').strip()

    if not email or not code:
        return Response({'success': False, 'error': 'Email et code requis'}, status=400)

    try:
        # ✅ FIX : iexact pour la cohérence
        reset_obj = PasswordResetCode.objects.filter(
            email__iexact=email,
            code=code,
            is_used=False
        ).latest('created_at')

        if not reset_obj.is_valid():
            return Response({
                'success': False,
                'error': 'Code expiré. Demandez un nouveau code.'
            }, status=400)

        return Response({'success': True, 'message': 'Code valide'})

    except PasswordResetCode.DoesNotExist:
        return Response({'success': False, 'error': 'Code incorrect'}, status=400)


@api_view(['POST'])
@permission_classes([AllowAny])
def reset_password(request):
    email        = request.data.get('email', '').strip().lower()
    code         = request.data.get('code', '').strip()
    new_password = request.data.get('new_password', '')

    if not new_password:
        return Response({'success': False, 'error': 'Le nouveau mot de passe est requis'}, status=400)
    if len(new_password) < 8:
        return Response({'success': False, 'error': 'Le mot de passe doit contenir au moins 8 caractères'}, status=400)

    try:
        # ✅ FIX : iexact pour la cohérence
        reset_obj = PasswordResetCode.objects.filter(
            email__iexact=email,
            code=code,
            is_used=False
        ).latest('created_at')

        if not reset_obj.is_valid():
            return Response({
                'success': False,
                'error': 'Code expiré. Recommencez la procédure.'
            }, status=400)

        user = reset_obj.user
        user.set_password(new_password)
        user.save()

        reset_obj.is_used = True
        reset_obj.save()

        return Response({'success': True, 'message': 'Mot de passe réinitialisé avec succès'})

    except PasswordResetCode.DoesNotExist:
        return Response({'success': False, 'error': 'Code invalide. Recommencez la procédure.'}, status=400)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_user_detail(request, user_id):
    """
    Retourne les informations complètes d'un utilisateur pour la page DetailsCompte.
    Accessible à tous les utilisateurs authentifiés (lecture seule).
    Les actions (toggle/delete) restent réservées au super_admin.
    """
    if not is_super_admin(request.user):
        return Response(
            {'success': False, 'message': 'Accès refusé. Réservé au Super Administrateur.'},
            status=status.HTTP_403_FORBIDDEN
        )

    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return Response(
            {'success': False, 'message': 'Utilisateur introuvable.'},
            status=status.HTTP_404_NOT_FOUND
        )

    full_name = f"{user.first_name} {user.last_name}".strip() or user.username
    initiales = (
        (user.first_name[0] + user.last_name[0]).upper()
        if user.first_name and user.last_name
        else user.username[:2].upper()
    )

    # Formatage des dates
    def fmt_date(dt):
        if not dt:
            return None
        return dt.strftime('%d/%m/%Y à %H:%M')

    return Response({
    'success':    True,
    'can_manage': is_super_admin(request.user),
    'user': {
        'id':                   user.id,
        'code':                 f'#USR-{str(user.id).zfill(3)}',
        'nom':                  full_name,
        'initiales':            initiales,
        'email':                user.email,
        'telephone':            user.phone or None,
        'role':                 user.role,
        'is_active':            user.is_active,
        'statut':               'Actif' if user.is_active else 'Inactif',
        'dateCreation':         fmt_date(user.date_joined),
        'derniereConnexion':    fmt_date(user.last_login),
        'derniereModification': None,
        'password_display':     user.password_plain or '—',  # ← AJOUTER
    }
}, status=status.HTTP_200_OK)
