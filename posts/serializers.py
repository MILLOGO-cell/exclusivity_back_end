from rest_framework import serializers
from .models import Post, SimplePost, EventPost, Comment, Like

class PostSerializer(serializers.ModelSerializer):
    author = serializers.StringRelatedField()
    comments_count = serializers.IntegerField(source='get_comments_count', read_only=True)
    likes_count = serializers.IntegerField(source='get_likes_count', read_only=True)

    class Meta:
        model = Post
        fields = ['id', 'title', 'content', 'author', 'created_at', 'video', 'is_public', 'comments_count', 'likes_count']


class SimplePostSerializer(PostSerializer):
    class Meta(PostSerializer.Meta):
        model = SimplePost
        fields = PostSerializer.Meta.fields + ['image']


class EventPostSerializer(PostSerializer):
    class Meta(PostSerializer.Meta):
        model = EventPost
        fields = PostSerializer.Meta.fields + ['image', 'event_name', 'date', 'time', 'location', 'description']


class CommentSerializer(serializers.ModelSerializer):
    user = serializers.StringRelatedField()

    class Meta:
        model = Comment
        fields = ['id', 'post', 'user', 'content', 'created_at']


class LikeSerializer(serializers.ModelSerializer):
    user = serializers.StringRelatedField()

    class Meta:
        model = Like
        fields = ['id', 'post', 'user']
