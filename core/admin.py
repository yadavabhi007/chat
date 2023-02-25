from django.contrib import admin
from core.models import MessageModel, User
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin


class UserAdmin(BaseUserAdmin):
    list_display = ('id', 'image_tag', 'username', 'name', 'created_at', 'updated_at', 'is_admin')
    list_filter = ('is_admin',)
    fieldsets = (
        ('User Credentials', {'fields': ('username', 'password', 'device_token')}),
        ('Personal info', {'fields': ('email', 'name', 'phone', 'profile', 'image_tag')}),
        ('Permissions', {'fields': ('is_active', 'is_admin',)}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'name', 'phone', 'device_token', 'profile', 'password1', 'password2'),
        }),
    )
    search_fields = ('username', 'email', 'name', 'phone')
    ordering = ('id', 'username', 'email', 'name', 'phone', 'created_at', 'updated_at')
    list_per_page = 10
    readonly_fields = ('image_tag',)
    filter_horizontal = ()
admin.site.register(User, UserAdmin)


@admin.register(MessageModel)
class MessageModelAdmin(admin.ModelAdmin):
    readonly_fields = ('timestamp',)
    search_fields = ('id', 'body', 'user__username', 'recipient__username')
    list_display = ('id', 'user', 'recipient', 'timestamp', 'characters')
    list_display_links = ('id',)
    list_filter = ('user', 'recipient')
    date_hierarchy = 'timestamp'

