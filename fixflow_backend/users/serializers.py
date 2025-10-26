from rest_framework import serializers
from .models import User  # Ajusta si tu modelo se llama distinto
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = User
        fields = (
            'id', 'username', 'email', 'first_name', 'last_name', 'phone', 
            'address', 'user_type', 'age', 'rfc', 'photo', 'status', 
            'company', 'password'
        )
        extra_kwargs = {
            'company': {'required': True}
        }

    def create(self, validated_data):
        password = validated_data.pop('password')
        user = User(**validated_data)
        user.set_password(password)  #  encripta la contraseña con Django
        user.save()
        return user

    def update(self, instance, validated_data):
        password = validated_data.pop('password', None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        if password:
            instance.set_password(password)  #  encripta la nueva contraseña
        instance.save()
        return instance

class Login(TokenObtainPairSerializer):
    username_field = 'email'  # Autenticación por correo

    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token['id'] = user.id
        token['username'] = user.username
        token['email'] = user.email
        token['first_name'] = user.first_name
        token['last_name'] = user.last_name
        token['phone'] = user.phone
        token['address'] = user.address
        token['user_type'] = user.user_type
        token['age'] = user.age
        token['rfc'] = user.rfc
        token['status'] = user.status
        token['company'] = user.company.id if user.company else None
        return token

    def validate(self, attrs):
        # SimpleJWT internamente usa 'username', así que aliasamos con 'email'
        attrs['username'] = attrs.get('email')

        data = super().validate(attrs)
        user = self.user

        data.update({
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'phone': user.phone,
                'address': user.address,
                'user_type': user.user_type,
                'age': user.age,
                'rfc': user.rfc,
                'status': user.status,
                'company': user.company.id if user.company else None,
                'photo': user.photo.url if user.photo else None,
            }
        })
        return data
