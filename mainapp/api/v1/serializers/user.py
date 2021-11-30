from datetime import datetime

from django.contrib.auth.models import User
from rest_auth.serializers import UserDetailsSerializer
from rest_framework import serializers

from mainapp.models import MyUser


class UserSerializer(UserDetailsSerializer):
    avatar = serializers.ImageField(source="myuser.avatar")

    class Meta(UserDetailsSerializer.Meta):
        fields = UserDetailsSerializer.Meta.fields + ('avatar',)


class UserExplicitSerializer(UserSerializer):
    selfDescription = serializers.CharField(source='myuser.selfDescription')
    DateOfBirth = serializers.DateField(source='myuser.DateOfBirth')

    class Meta(UserSerializer.Meta):
        fields = UserSerializer.Meta.fields + ('selfDescription', 'DateOfBirth')

    def update(self, instance, validated_data):
        profile_data = validated_data.pop('myuser', {})
        DateOfBirth = profile_data.get('DateOfBirth')

        if DateOfBirth > datetime.now().date():
            raise serializers.ValidationError('given date is invalid')

        selfDescription = profile_data.get('selfDescription')
        avatar = profile_data.get('avatar')
        instance = super(UserSerializer, self).update(instance, validated_data)

        # get and update user profile
        profile = instance.myuser
        if profile_data:
            if avatar:
                profile.avatar = avatar
            if selfDescription:
                profile.selfDescription = selfDescription
            if DateOfBirth:
                profile.DateOfBirth = DateOfBirth
            profile.save()
        return instance


class DefaultUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'first_name', 'last_name']


class MyUserSerializer(serializers.ModelSerializer):
    user = DefaultUserSerializer(many=False, read_only=True)

    class Meta:
        model = MyUser
        fields = ['id', 'username', 'first_name', 'last_name']