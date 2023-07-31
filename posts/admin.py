from django.contrib import admin
from .models import Post,EventPost,SimplePost,Comment,Like

admin.site.register(Post)
admin.site.register(EventPost)
admin.site.register(SimplePost)
admin.site.register(Comment)
admin.site.register(Like)