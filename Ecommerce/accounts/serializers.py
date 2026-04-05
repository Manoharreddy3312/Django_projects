from rest_framework import serializers

from .models import User, UserProfile


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'email', 'phone', 'is_email_verified', 'avatar')
        read_only_fields = fields


class UserProfileSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(source='user.email', read_only=True)

    class Meta:
        model = UserProfile
        fields = (
            'email',
            'full_name',
            'address_line1',
            'address_line2',
            'city',
            'state',
            'postal_code',
            'country',
        )
