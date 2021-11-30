from rest_framework import generics, status, permissions, viewsets
from rest_framework.response import Response

from mainapp.models import Question, Answer
from mainapp.api.v1.serializers.question import QuestionSerializer


class MultipleQuestionsCreateView(generics.CreateAPIView):
    """
    Creates questions with same text to multiple users
    """
    queryset = Question.objects.all()
    serializer_class = QuestionSerializer

    def create(self, request, *args, **kwargs):
        user = self.request.user
        res = []
        for askedUserId in request.data['askedUsers']:
            dict = {'question_text': request.data['question_text'], 'askedUser': askedUserId}
            if not request.data['isAnon']:
                dict['asker'] = user.id
            res.append(dict)

        serializer = self.get_serializer(data=res, many=True)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)


class QuestionCreateView(generics.CreateAPIView):
    """
    Creates a single question to user
    """
    queryset = Question.objects.all()
    serializer_class = QuestionSerializer
    permission_classes = [permissions.AllowAny]
    authentication_classes = []

    def create(self, request, *args, **kwargs):
        user = request.user
        res = {'askedUser': request.data['askedUser'], 'question_text': request.data['question_text']}

        # if question is anonymous then asker = null
        if not request.data['isAnon']:
            res['asker'] = user.id

        serializer = self.get_serializer(data=res)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)


class QuestionDeleteView(generics.DestroyAPIView):
    """
    Deletes specific question
    """
    serializer_class = QuestionSerializer
    queryset = Question.objects.all()
    permission_classes = (permissions.IsAuthenticated,)


class QuestionViewSet(viewsets.ModelViewSet):
    """
    Provides unaswered questions to related user
    """
    serializer_class = QuestionSerializer

    def get_queryset(self):
        user = self.request.user
        answers = Answer.objects.all()
        questions = Question.objects.filter(askedUser=user).exclude(answer__in=answers).order_by('-timestamp')
        return questions