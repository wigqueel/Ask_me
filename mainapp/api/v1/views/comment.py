from django.shortcuts import get_object_or_404
from rest_framework import generics, status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from mainapp.models import Comment, Answer
from mainapp.api.v1.serializers.comment import CommentExplicitSerializer, CommentShortSerializer


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