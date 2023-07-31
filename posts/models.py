from django.db import models
from django.contrib.auth import get_user_model
from django.utils.deconstruct import deconstructible
from django.core.exceptions import ValidationError


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


class Post(models.Model):
    title = models.CharField(max_length=255)
    content = models.TextField()
    author = models.ForeignKey(get_user_model(), on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    media = models.FileField(
        upload_to="post_media/", null=True, blank=True, validators=[media_validator]
    )
    is_public = models.BooleanField(default=False)

    def __str__(self):
        return self.title

    def get_comments_count(self):
        return self.comments.count()

    def get_likes_count(self):
        return self.likes.count()


class SimplePost(Post):
    image = models.ImageField(upload_to="simple_post_images", null=True, blank=True)


class EventPost(Post):
    image = models.ImageField(upload_to="event_post_images", null=True, blank=True)
    event_name = models.CharField(max_length=255)
    date = models.DateField()
    time = models.TimeField()
    location = models.CharField(max_length=255)
    description = models.TextField()


class Comment(models.Model):
    post = models.ForeignKey(Post, related_name="comments", on_delete=models.CASCADE)
    user = models.ForeignKey(get_user_model(), on_delete=models.CASCADE)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    parent = models.ForeignKey(
        "self", related_name="replies", null=True, blank=True, on_delete=models.CASCADE
    )

    def __str__(self):
        return self.content


class Like(models.Model):
    post = models.ForeignKey(Post, related_name="likes", on_delete=models.CASCADE)
    user = models.ForeignKey(get_user_model(), on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.user.username} a aimé"
