import re
from uuid import UUID
from rest_framework import serializers
from django.core.validators import EmailValidator
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from base.validation.base import Validation
from ..models.user_profile import UserProfile


class UserProfileInfoValidation(Validation):
    """Validation for user profile information"""

    username = serializers.CharField(required=True, max_length=100)
    email = serializers.EmailField(required=True, validators=[EmailValidator()])
    address = serializers.CharField(required=True, allow_blank=False)
    interests = serializers.CharField(required=True, allow_blank=False)
    avatar_url = serializers.URLField(required=False, allow_blank=True, max_length=500)

    # Extended travel preferences
    passport_nationality = serializers.CharField(required=False, max_length=100, allow_blank=True)
    seat_preference = serializers.CharField(required=False, max_length=50, allow_blank=True)
    food_preference = serializers.CharField(required=False, allow_blank=True)
    allergies = serializers.ListField(child=serializers.CharField(), required=False, allow_empty=True)
    likes = serializers.ListField(child=serializers.CharField(), required=False, allow_empty=True)
    dislikes = serializers.ListField(child=serializers.CharField(), required=False, allow_empty=True)
    price_sensitivity = serializers.ListField(child=serializers.CharField(), required=False, allow_empty=True)
    home_address = serializers.CharField(required=False, allow_blank=True)
    local_prefer_mode = serializers.CharField(required=False, max_length=50, allow_blank=True)

    def validate_username(self, value):
        """Validate username"""
        if self.validate_username_format(value):
            return value

    def validate_email(self, value):
        """Validate email format and uniqueness"""
        if self.validate_email_format(value):
            # Check uniqueness for update case
            instance = self.context.get('instance')
            if UserProfile.objects.filter(email=value).exclude(pk=instance.pk if instance else None).exists():
                raise serializers.ValidationError('Email already exists')
            return value

    def validate_avatar_url(self, value):
        """Validate avatar URL"""
        if value and self.validate_url_format(value):
            return value
        return value

    def validate_address(self, value):
        """Validate address"""
        if self.validate_max_length(value, 500):
            return value

    def validate_interests(self, value):
        """Validate interests"""
        if self.validate_max_length(value, 1000):
            return value


class UserProfileUpdateInfoValidation(UserProfileInfoValidation):
    """Validation for updating user profile (all fields optional)"""

    username = serializers.CharField(required=False, max_length=100)
    email = serializers.EmailField(required=False, validators=[EmailValidator()])
    address = serializers.CharField(required=False, allow_blank=True)
    interests = serializers.CharField(required=False, allow_blank=True)


class UserProfileCreateValidation(Validation):
    """Validation for creating new user profile"""

    info = UserProfileInfoValidation()
    password = serializers.CharField(required=True, write_only=True)
    confirm_password = serializers.CharField(required=True, write_only=True)

    def validate_password(self, value):
        """Validate password strength"""
        if self.validate_password_strength(value):
            return value

    def validate(self, attrs):
        """Cross-field validation"""
        if attrs.get('password') != attrs.get('confirm_password'):
            raise serializers.ValidationError('Password and confirmation do not match')
        return attrs


class UserProfileUpdateValidation(Validation):
    """Validation for updating user profile"""

    info = UserProfileUpdateInfoValidation(required=False)

    def __init__(self, *args, **kwargs):
        self.instance = kwargs.pop('instance', None)
        super().__init__(*args, **kwargs)

        # Pass instance to nested validation
        if hasattr(self.fields['info'], 'context'):
            self.fields['info'].context = {'instance': self.instance}


class ChangePasswordValidation(Validation):
    """Validation for changing password"""

    current_password = serializers.CharField(required=True, write_only=True)
    new_password = serializers.CharField(required=True, write_only=True)
    confirm_password = serializers.CharField(required=True, write_only=True)

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

    def validate_current_password(self, value):
        """Validate current password"""
        if not self.user or not self.user.check_password(value):
            raise serializers.ValidationError('Current password is incorrect')
        return value

    def validate_new_password(self, value):
        """Validate new password strength"""
        if self.validate_password_strength(value):
            return value

    def validate(self, attrs):
        """Cross-field validation"""
        if attrs.get('new_password') != attrs.get('confirm_password'):
            raise serializers.ValidationError('New password and confirmation do not match')
        return attrs


class UserProfileListValidation(Validation):
    """Validation for listing user profiles with filters"""

    search = serializers.CharField(required=False, allow_blank=True, max_length=255)
    ordering = serializers.CharField(required=False, allow_blank=True)
    limit = serializers.IntegerField(required=False, min_value=1, max_value=100, default=20)
    offset = serializers.IntegerField(required=False, min_value=0, default=0)

    def validate_ordering(self, value):
        """Validate ordering field"""
        allowed_fields = ['username', 'email', 'created_at', 'updated_at', '-username', '-email', '-created_at', '-updated_at']
        if value and value not in allowed_fields:
            raise serializers.ValidationError(f'Invalid ordering field. Allowed: {", ".join(allowed_fields)}')
        return value