from django.db import models
from django.contrib.auth import get_user_model
from django.utils.deconstruct import deconstructible
from django.core.exceptions import ValidationError
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey, GenericRelation
from django.db import models


@deconstructible
class FileValidator:
    def __init__(self, allowed_formats):
        self.allowed_formats = allowed_formats

    def __call__(self, value):
        file_extension = value.name.split(".")[-1].lower()
        if file_extension not in self.allowed_formats:
            raise ValidationError("Format de fichier non pris en charge.")


# Liste des formats autorisés (ajustez selon vos besoins)
ALLOWED_FORMATS = [
    "mp4",
    "mov",
    "avi",
    "mp3",
    "wav",
    "ogg",
    "jpg",
    "jpeg",
    "png",
    "gif",
]

# Utilisation de la fonction de validation dans le champ 'media'
media_validator = FileValidator(allowed_formats=ALLOWED_FORMATS)


class Like(models.Model):
    user = models.ForeignKey(get_user_model(), on_delete=models.CASCADE)
    content_type = models.ForeignKey(
        ContentType, on_delete=models.CASCADE, null=True, blank=True
    )
    object_id = models.PositiveIntegerField(null=True, blank=True)
    content_object = GenericForeignKey("content_type", "object_id")
    user_info = models.JSONField(blank=True, null=True)

    def __str__(self):
        return f"{self.user.username} a aimé le {self.content_type.model}"


class Comment(models.Model):
    user = models.ForeignKey(get_user_model(), on_delete=models.CASCADE)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    parent_comment = models.ForeignKey(
        "self",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="sub_comments",
    )
    content_type = models.ForeignKey(
        ContentType, on_delete=models.CASCADE, null=True, blank=True
    )
    object_id = models.PositiveIntegerField(null=True, blank=True)
    content_object = GenericForeignKey("content_type", "object_id")
    comment_count = models.PositiveIntegerField(default=0)
    likes = GenericRelation(Like, related_query_name="comments", null=True, blank=True)
    liked_users = models.ManyToManyField(
        get_user_model(), related_name="liked_comments", blank=True
    )

    def __str__(self):
        return f"{self.user.username} commented on {self.content_type.model}"

    class Meta:
        verbose_name = "Commentaire"
        verbose_name_plural = "Commentaires"

    def get_comments_count(self):
        return self.comments.count()

    def get_likes_count(self):
        return self.likes.count()


class Post(models.Model):
    content = models.TextField()
    author = models.ForeignKey(get_user_model(), on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    media = models.FileField(
        upload_to="post_media/", null=True, blank=True, validators=[media_validator]
    )
    is_public = models.BooleanField(default=False)
    likes = GenericRelation(Like, related_query_name="posts", null=True, blank=True)
    liked_users = models.ManyToManyField(
        get_user_model(), related_name="liked_posts", blank=True
    )
    comments = GenericRelation(
        Comment, related_query_name="posts", null=True, blank=True
    )

    def __str__(self):
        return self.content

    def get_comments_count(self):
        return self.comments.count()

    def get_likes_count(self):
        return self.likes.count()


class SimplePost(Post):
    is_simple = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Poste"
        verbose_name_plural = "Postes "


class EventPost(Post):
    title = models.CharField(max_length=255, null=True, blank=True)
    date = models.CharField(max_length=255)
    time = models.CharField(max_length=255)
    location = models.CharField(max_length=255)
    is_event = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Évenementiel"
        verbose_name_plural = "Évenementiels"
