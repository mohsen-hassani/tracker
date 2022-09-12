from django.contrib.auth.password_validation import validate_password
from django.contrib.auth import authenticate
from rest_framework import serializers
from .models import User


class LoginSerializer(serializers.Serializer):
    """This serializer defines two fields for authentication:
        - email
        - password
    It will try to authenticate the user with when validated.
    """
    email = serializers.CharField(label="Email", write_only=True)
    password = serializers.CharField(label="Password", trim_whitespace=False, write_only=True)

    def validate(self, validated_data):
        email = validated_data.get('email')
        password = validated_data.get('password')
        if email and password:
            user = authenticate(request=self.context.get('request'), username=email, password=password)
            if not user:
                message = 'Wrong username or password.'
                raise serializers.ValidationError(message, code='authorization')
        else:
            message = 'Please enter email and password'
            raise serializers.ValidationError(message, code='authorization')
        validated_data['user'] = user
        return validated_data


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('email', 'first_name', 'last_name')
        read_only_fields = ('email', )


class RegisterSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('email', 'password', 'first_name', 'last_name')
    
    def validate_password(self, password):
        validate_password(password)
        return password
