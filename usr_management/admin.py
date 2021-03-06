# Register your models here.
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from usr_management.models import UserKooblit
from usr_management.models import Verification, Syntheses, Address, Version_Synthese, Note, DueNote


class UserKooblitInline(admin.StackedInline):
    model = UserKooblit
    can_delete = False
    verbose_name_plural = 'utilisateur'

# Define a new User admin
class UserAdmin(UserAdmin):
    inlines = (UserKooblitInline, )

# Re-register UserAdmin
admin.site.unregister(User)
admin.site.register(User, UserAdmin)
admin.site.register(Verification)
admin.site.register(Syntheses)
admin.site.register(Version_Synthese)
admin.site.register(Address)
admin.site.register(Note)
admin.site.register(DueNote)

