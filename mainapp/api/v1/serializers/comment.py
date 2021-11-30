from rest_framework import serializers

from mainapp.api.v1.serializers.user import UserSerializer
from mainapp.models import Comment


class CommentExplicitSerializer(serializers.ModelSerializer):
    commented_user = UserSerializer(many=False)

    class Meta:
        model = Comment
        fields = ('id', 'comment_text', 'commented_user', 'answer', 'timestamp')


class CommentShortSerializer(serializers.ModelSerializer):
    class Meta:
        model = Comment
        fields = ('id', 'comment_text', 'commented_user', 'answer')