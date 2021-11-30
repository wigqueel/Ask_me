from django.contrib.auth.models import User, AnonymousUser
from django.core.exceptions import ValidationError
from django.db.models import Sum, Subquery
from django.http import HttpResponseNotFound
from django.shortcuts import render, get_object_or_404
from django.views.generic import TemplateView
from friendship.exceptions import AlreadyExistsError, AlreadyFriendsError
from friendship.models import FriendshipRequest, Friend
from rest_framework import generics, viewsets, permissions, status, filters, authentication
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.pagination import CursorPagination
from rest_framework.response import Response

from .models import MyUser, Question, Answer, Comment
from .serializers import *
from .utils import TokenAllowAnyAuthentication


class AccountSettingsView(generics.UpdateAPIView):
    """
    updates information about user
    """
    serializer_class = UserExplicitSerializer
    queryset = User.objects.all()

    def get_object(self):
        user = self.request.user
        obj = get_object_or_404(User, pk=user.id)
        return obj

    def patch(self, request, *args, **kwargs):
        return self.partial_update(request, *args, **kwargs)


class AccountInfoView(generics.RetrieveAPIView):
    """
    provides basic information about user
    """
    permission_classes = [permissions.AllowAny]
    authentication_classes = [TokenAllowAnyAuthentication]
    serializer_class = UserExplicitSerializer
    queryset = User.objects.all()

    def get_object(self):
        # if it's called with username in url then use that user and signed in user otherwise
        try:
            user = User.objects.get(
                username=self.kwargs['username']) if 'username' in self.kwargs else self.request.user
            obj = get_object_or_404(User, pk=user.id)
        except User.DoesNotExist:
            return HttpResponseNotFound('not found')
        return obj


@api_view(['GET'])
@permission_classes([permissions.AllowAny])
@authentication_classes([TokenAllowAnyAuthentication])
def AccountInfoStatsView(request, username=None):
    """
    Provides user statistics related to specific user
    """

    # if username is passed through url, then send stat about its user
    # else send stat about signed in user
    user = request.user
    if username is not None:
        user = User.objects.get(username=username)

    if isinstance(user, AnonymousUser):
        return Response(data={}, status=status.HTTP_400_BAD_REQUEST)

    # questions related to specific user
    questions = Question.objects.filter(askedUser_id=user.id)

    # answers related to specific user
    answers = Answer.objects.filter(question__in=questions)
    answers_count = answers.count()

    friends_count = len(Friend.objects.friends(user))
    likes_count = answers.aggregate(Sum('likes'))['likes__sum']

    return Response(
        data={'answersCount': answers_count, 'friendsCount': friends_count, 'likesCount': likes_count},
        status=status.HTTP_200_OK
    )


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


class CommentListView(generics.ListAPIView):
    serializer_class = CommentExplicitSerializer

    def get_queryset(self):
        answer_id = self.kwargs['answerId']
        queryset = Comment.objects.filter(answer_id=answer_id).order_by('-timestamp')
        return queryset


@api_view(['POST'])
def create_comment_view(request, answerId):
    answer = get_object_or_404(Answer, pk=answerId)
    user = request.user
    data = {'comment_text': request.data['comment_text'], 'commented_user': user.id, 'answer': answer.id}
    serializer = CommentShortSerializer(data=data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    else:
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


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


class FriendListView(generics.ListAPIView):
    """
    Provides list of user's friends
    """
    serializer_class = UserSerializer

    def get_queryset(self):
        token_str = self.request.headers['Authorization']
        token_val = token_str.split()[1]
        user = User.objects.get(auth_token=token_val)

        queryset = Friend.objects.friends(user)
        return self.serializer_class(queryset, many=True)


@api_view(['GET', 'POST'])
def deleteFrienshipView(request, pk):
    """
    Remove specific user from friends
    """

    other_user = User.objects.get(pk=pk)
    if Friend.objects.remove_friend(request.user, other_user):
        return Response({'message': 'User was deleted from friends'}, status=status.HTTP_200_OK)
    else:
        return Response({'message': 'Something went wrong'}, status=status.HTTP_409_CONFLICT)


@api_view(['GET', 'POST'])
def createFrienshipRequestView(request, pk):
    """
    Add specific user to friends
    """
    sender = request.user
    recipient = User.objects.get(pk=pk)
    try:
        Friend.objects.add_friend(sender, recipient)
    except (ValidationError, AlreadyFriendsError, AlreadyExistsError) as e:
        return Response({'message': str(e)}, status=status.HTTP_409_CONFLICT)

    return Response({'message': 'friendship request created'}, status=status.HTTP_200_OK)


@api_view(['GET', 'POST'])
def rejectFriendshipView(request, pk):
    """
    Reject friendship request
    """
    friend_request = FriendshipRequest.objects.get(id=pk)
    friend_request.cancel()
    return Response({'message': 'friendship request rejected'}, status=status.HTTP_200_OK)


class AcceptFriendshipView(generics.CreateAPIView):
    """
    Accept frienship request
    """
    serializer_class = FriendshipRequestSerializer
    queryset = Friend.objects.all()

    def create(self, request, *args, **kwargs):
        friend_request = FriendshipRequest.objects.get(id=self.kwargs['pk'])
        friend_request.accept()
        return Response({'Success': 'friendship created'}, status=status.HTTP_201_CREATED)


class FriendRequestsListView(generics.ListAPIView):
    """
    Provides list of friend requests to specific user
    """
    serializer_class = FriendshipRequestSerializer

    def get_queryset(self):
        user = self.request.user
        return FriendshipRequest.objects.filter(to_user=user.id).filter(rejected=None)


class UserSearchListView(generics.ListAPIView):
    """
    Search users
    """

    queryset = User.objects.all()
    serializer_class = UserSerializer
    search_fields = ['username', 'first_name', 'last_name']
    filter_backends = (filters.SearchFilter,)
