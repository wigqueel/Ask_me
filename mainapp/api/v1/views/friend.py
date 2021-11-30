from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from friendship.exceptions import AlreadyFriendsError, AlreadyExistsError
from friendship.models import Friend, FriendshipRequest
from rest_framework import generics, status, filters
from rest_framework.decorators import api_view
from rest_framework.response import Response

from mainapp.api.v1.serializers.friend import FriendshipRequestSerializer
from mainapp.api.v1.serializers.user import UserSerializer


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