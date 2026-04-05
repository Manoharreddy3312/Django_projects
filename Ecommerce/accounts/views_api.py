from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from .mailing import send_activation_email
from .models import EmailActivationToken, User
from .serializers import UserProfileSerializer, UserSerializer


class RegisterAPIView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        email = (request.data.get('email') or '').strip().lower()
        password = request.data.get('password')
        phone = (request.data.get('phone') or '').strip()
        if not email or not password:
            return Response({'detail': 'email and password required'}, status=status.HTTP_400_BAD_REQUEST)
        if User.objects.filter(email=email).exists():
            return Response({'detail': 'Email already registered'}, status=status.HTTP_400_BAD_REQUEST)
        user = User.objects.create_user(email=email, password=password)
        user.phone = phone
        user.is_active = False
        user.is_email_verified = False
        user.save()
        tok = EmailActivationToken.create_for_user(user)
        try:
            send_activation_email(user, tok.token)
        except Exception as e:
            return Response({'detail': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        return Response({'detail': 'Check email to activate account.'}, status=status.HTTP_201_CREATED)


class CurrentUserView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        ser = UserSerializer(request.user)
        prof, _ = request.user.profile.__class__.objects.get_or_create(user=request.user)
        pser = UserProfileSerializer(prof)
        return Response({'user': ser.data, 'profile': pser.data})
