from django.contrib import admin
from .models import ContactMessage

@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'subject', 'created_at', 'message_preview')
    list_filter = ('created_at',)
    search_fields = ('name', 'email', 'subject', 'message')
    readonly_fields = ('created_at',)
    date_hierarchy = 'created_at'
    
    def message_preview(self, obj):
        # Display first 50 characters of message
        return obj.message[:50] + '...' if len(obj.message) > 50 else obj.message
    
    message_preview.short_description = 'Message'

# @admin.register(Subscriber)
# class SubscriberAdmin(admin.ModelAdmin):
#     list_display = ('email', 'name', 'subscribed_at', 'is_active')
#     list_filter = ('is_active', 'subscribed_at')
#     search_fields = ('email', 'name')
#     readonly_fields = ('subscribed_at',)
#     actions = ['mark_active', 'mark_inactive']
    
#     def mark_active(self, request, queryset):
#         queryset.update(is_active=True)
#     mark_active.short_description = "Mark selected subscribers as active"
    
#     def mark_inactive(self, request, queryset):
#         queryset.update(is_active=False)
#     mark_inactive.short_description = "Mark selected subscribers as inactive"