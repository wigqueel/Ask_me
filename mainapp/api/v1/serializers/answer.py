from rest_framework import serializers

from mainapp.api.v1.serializers.user import UserSerializer
from mainapp.models import Answer


class AnswerSerializer(serializers.ModelSerializer):
    question_text = serializers.CharField(source='question.question_text')
    question_id = serializers.CharField(source='question.id')
    askedUser = UserSerializer(source='question.askedUser', many=False)
    asker = UserSerializer(source='question.asker', many=False)

    class Meta:
        model = Answer
        fields = (
        'id', 'answer_text', 'likes', 'dislikes', 'timestamp', 'question_text', 'question_id', 'askedUser', 'asker')