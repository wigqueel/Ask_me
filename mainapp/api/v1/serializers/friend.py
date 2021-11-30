from friendship.models import FriendshipRequest, Friend
from rest_framework import serializers

from mainapp.api.v1.serializers.user import UserSerializer


class FriendshipRequestSerializer(serializers.ModelSerializer):
    from_user = UserSerializer(many=False)

    class Meta:
        model = FriendshipRequest
        fields = ('id', 'from_user', 'to_user', 'message', 'created', 'rejected')


class FriendSerializer(serializers.ModelSerializer):
    class Meta:
        model = Friend
        fields = ('id', 'created', 'from_user_id', 'to_user_id')