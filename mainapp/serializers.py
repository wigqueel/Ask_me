from allauth.account import app_settings as allauth_settings
from allauth.account.adapter import get_adapter
from allauth.account.utils import setup_user_email
from allauth.utils import email_address_exists
from datetime import datetime, timedelta
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from friendship.models import FriendshipRequest, Friend
from rest_auth.serializers import UserDetailsSerializer
from rest_framework import serializers

from .models import MyUser, Question, Answer, Comment


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


class QuestionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Question
        fields = '__all__'


class AnswerSerializer(serializers.ModelSerializer):
    question_text = serializers.CharField(source='question.question_text')
    question_id = serializers.CharField(source='question.id')
    askedUser = UserSerializer(source='question.askedUser', many=False)
    asker = UserSerializer(source='question.asker', many=False)

    class Meta:
        model = Answer
        fields = (
        'id', 'answer_text', 'likes', 'dislikes', 'timestamp', 'question_text', 'question_id', 'askedUser', 'asker')


class CommentExplicitSerializer(serializers.ModelSerializer):
    commented_user = UserSerializer(many=False)

    class Meta:
        model = Comment
        fields = ('id', 'comment_text', 'commented_user', 'answer', 'timestamp')


class CommentShortSerializer(serializers.ModelSerializer):
    class Meta:
        model = Comment
        fields = ('id', 'comment_text', 'commented_user', 'answer')


class FriendshipRequestSerializer(serializers.ModelSerializer):
    from_user = UserSerializer(many=False)

    class Meta:
        model = FriendshipRequest
        fields = ('id', 'from_user', 'to_user', 'message', 'created', 'rejected')


class FriendSerializer(serializers.ModelSerializer):
    class Meta:
        model = Friend
        fields = ('id', 'created', 'from_user_id', 'to_user_id')


class AnswerCreateSerializer(serializers.ModelSerializer):
    question_id = serializers.CharField()

    class Meta:
        model = Answer
        fields = ('answer_text', 'question_id')

    def create(self, validated_data):
        text = validated_data.pop('answer_text')
        question_id = validated_data.pop('question_id')
        return Answer.objects.create(answer_text=text, question_id=question_id)
