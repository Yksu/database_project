from django.contrib import admin

from .models import *
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import Group


admin.site.unregister(Group)
admin.site.register(CustomUser, UserAdmin)
admin.site.register(Friendship)
admin.site.register(Recommendation)
admin.site.register(Category)
admin.site.register(Rating)
admin.site.register(Review)
admin.site.register(Comment)
admin.site.register(Book)
