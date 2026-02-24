from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework import status
from django.db.models import Q
from django.contrib.auth import login as auth_login, logout as auth_logout
from .serializers import LoginSerializer, ChangePasswordSerializer
from .models import User


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
    serializer = LoginSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.validated_data
        auth_login(request, user)
        return Response({
            'success': True,
            'message': 'Connexion reussie',
            'user': {
                'id':         user.id,
                'username':   user.username,
                'email':      user.email,
                'first_name': user.first_name,
                'last_name':  user.last_name,
                'role':       user.role,
                'phone':      user.phone,
            }
        }, status=status.HTTP_200_OK)
    return Response({
        'success': False,
        'message': 'Email ou mot de passe incorrect',
        'errors':  serializer.errors
    }, status=status.HTTP_401_UNAUTHORIZED)


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
        'id':         user.id,
        'username':   user.username,
        'email':      user.email,
        'first_name': user.first_name,
        'last_name':  user.last_name,
        'role':       user.role,
        'phone':      user.phone,
    }, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def change_password(request):
    serializer = ChangePasswordSerializer(data=request.data, context={'request': request})
    if serializer.is_valid():
        user = request.user
        user.set_password(serializer.validated_data['new_password'])
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
            Q(first_name__icontains=search) |
            Q(last_name__icontains=search)  |
            Q(email__icontains=search)      |
            Q(username__icontains=search)
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
        'success':    True,
        'count':      len(data),
        'can_manage': is_super_admin(request.user),
        'users':      data,
    }, status=status.HTTP_200_OK)


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
        'success':   True,
        'message':   f"Utilisateur {'active' if user.is_active else 'desactive'} avec succes.",
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