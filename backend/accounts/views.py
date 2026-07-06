"""
Account views for registration, profile management, and user admin.
"""
from django.contrib.auth.models import User
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated, IsAdminUser
from rest_framework.response import Response
from rest_framework.views import APIView

from .serializers import (
    UserRegistrationSerializer,
    UserProfileSerializer,
    UserListSerializer,
)


class RegisterView(APIView):
    """User registration endpoint."""
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = UserRegistrationSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            return Response(
                {
                    "message": "User registered successfully.",
                    "user": UserProfileSerializer(user).data,
                },
                status=status.HTTP_201_CREATED,
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ProfileView(APIView):
    """View and update current user profile."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = UserProfileSerializer(request.user)
        return Response(serializer.data)

    def patch(self, request):
        serializer = UserProfileSerializer(
            request.user, data=request.data, partial=True
        )
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UserListView(APIView):
    """Admin-only user listing."""
    permission_classes = [IsAdminUser]

    def get(self, request):
        users = User.objects.all().order_by("-date_joined")
        serializer = UserListSerializer(users, many=True)
        return Response(serializer.data)
