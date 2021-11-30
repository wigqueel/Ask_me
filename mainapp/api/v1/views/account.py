from django.contrib.auth.models import User, AnonymousUser
from django.db.models import Sum
from django.http import HttpResponseNotFound
from django.shortcuts import get_object_or_404
from friendship.models import Friend
from rest_framework import generics, permissions, status
from rest_framework.decorators import api_view, permission_classes, authentication_classes
from rest_framework.response import Response

from mainapp.models import Question, Answer
from mainapp.api.v1.serializers.user import UserExplicitSerializer
from mainapp.utils import TokenAllowAnyAuthentication


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