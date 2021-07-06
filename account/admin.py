# from __future__ import unicode_literals
from django.contrib.auth import get_user_model
from django.contrib import admin

User = get_user_model()

from django.contrib.auth.models import Group
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

# from .forms import UserAdminCreationForm, UserAdminChangeForm

from .models import Profile, PhoneOTP


class ProfileInline(admin.StackedInline):
    model = Profile
    can_delete = False
    verbose_name_plural = 'Profile'
    fk_name = 'user'
    raw_id_fields = ('user',)


class UserAdmin(BaseUserAdmin):
    # The forms to add and change user instances
    # form = UserAdminChangeForm
    # add_form = UserAdminCreationForm

    list_display = ('phone', 'admin',)
    list_filter = ('staff', 'active', 'admin',)
    fieldsets = (
        (None, {'fields': ('phone', 'password')}),
        ('Personal info', {'fields': ('last_login',)}),
        ('Permissions', {'fields': ('admin', 'staff', 'active')}),
    )
    # add_fieldsets is not a standard ModelAdmin attribute. UserAdmin
    # overrides get_fieldsets to use this attribute when creating a user.
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('phone', 'password1', 'password2')}
         ),
    )

    search_fields = ('phone',)
    ordering = ('phone',)
    filter_horizontal = ()

    inlines = (ProfileInline,)

    def get_inline_instances(self, request, obj=None):
        if not obj:
            return list()
        return super(UserAdmin, self).get_inline_instances(request, obj)


admin.site.register(User, UserAdmin)

# Remove Group Model from admin. We're not using it.
admin.site.unregister(Group)


class PhoneOTPAdmin(admin.ModelAdmin):
    list_display = ('phone', 'otp', 'time_send', 'verified', 'forgot')
    filter_horizontal = ()


admin.site.register(PhoneOTP, PhoneOTPAdmin)
