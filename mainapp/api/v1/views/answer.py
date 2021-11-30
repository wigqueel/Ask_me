from django.contrib.auth.models import User
from friendship.models import Friend
from rest_framework import generics, permissions, serializers
from rest_framework.pagination import CursorPagination

from mainapp.models import Answer, Question
from mainapp.api.v1.serializers.answer import AnswerSerializer
from mainapp.utils import TokenAllowAnyAuthentication


class AnswerCreateView(generics.CreateAPIView):
    """
    Creates answers
    """

    serializer_class = AnswerCreateSerializer
    queryset = Answer.objects.all()


class AnswerLikeView(generics.UpdateAPIView):
    """
    Updates like or dislike amount of specific answer
    """
    serializer_class = AnswerSerializer
    queryset = Answer.objects.all()

    def patch(self, request, *args, **kwargs):
        return self.partial_update(request, *args, **kwargs)

    def put(self, request, *args, **kwargs):
        return self.partial_update(request, *args, **kwargs)


class AnswersPagination(CursorPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    ordering = '-timestamp'


class AnswersAccountListView(generics.ListAPIView):
    """
        Provides queryset of all answers that answered specific user
    """
    permission_classes = [permissions.AllowAny]
    authentication_classes = [TokenAllowAnyAuthentication]
    serializer_class = AnswerSerializer
    pagination_class = AnswersPagination

    def get_queryset(self):
        user = User.objects.get(username=self.kwargs['username']) if 'username' in self.kwargs else self.request.user
        # questions related to specific user
        questions = Question.objects.filter(askedUser_id=user.id)

        # answers related to specific user
        answers = Answer.objects.filter(question__in=questions)
        return answers


class AnswersListView(generics.ListAPIView):
    """
        Provides queryset of all answers that user's friends posted
    """

    serializer_class = AnswerSerializer
    pagination_class = AnswersPagination

    def get_queryset(self):
        user = self.request.user
        friends = Friend.objects.friends(user)

        # questions related to friends
        questions = Question.objects.filter(askedUser__in=friends)

        # answers related to specific user
        answers = Answer.objects.filter(question__in=questions)

        return answers


class AnswerCreateSerializer(serializers.ModelSerializer):
    question_id = serializers.CharField()

    class Meta:
        model = Answer
        fields = ('answer_text', 'question_id')

    def create(self, validated_data):
        text = validated_data.pop('answer_text')
        question_id = validated_data.pop('question_id')
        return Answer.objects.create(answer_text=text, question_id=question_id)