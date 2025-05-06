from django.contrib import admin
from .models import Category, News, NewsMedia, Comment

class NewsMediaInline(admin.TabularInline):
    model = NewsMedia
    extra = 1

class CommentInline(admin.TabularInline):
    model = Comment
    extra = 0
    readonly_fields = ('user', 'created_at')
    
@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug']
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ['name']

@admin.register(News)
class NewsAdmin(admin.ModelAdmin):
    list_display = ['title', 'author', 'category', 'status', 'publish_date', 'views']
    list_filter = ['status', 'category', 'is_featured', 'created_at', 'publish_date']
    search_fields = ['title', 'summary', 'content']
    prepopulated_fields = {'slug': ('title',)}
    date_hierarchy = 'publish_date'
    raw_id_fields = ['author']
    inlines = [NewsMediaInline, CommentInline]
    list_per_page = 20
    
    fieldsets = (
        (None, {
            'fields': ('title', 'slug', 'author', 'category')
        }),
        ('Content', {
            'fields': ('featured_image', 'summary', 'content', 'tags')
        }),
        ('Publication', {
            'fields': ('status', 'is_featured', 'publish_date')
        }),
    )

@admin.register(NewsMedia)
class NewsMediaAdmin(admin.ModelAdmin):
    list_display = ['news', 'media_type', 'title', 'is_featured', 'order', 'upload_date']
    list_filter = ['media_type', 'is_featured', 'upload_date']
    search_fields = ['title', 'description', 'news__title']
    raw_id_fields = ['news']

@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ['user', 'news', 'created_at', 'is_approved']
    list_filter = ['is_approved', 'created_at']
    search_fields = ['content', 'user__username', 'news__title']
    actions = ['approve_comments']
    
    def approve_comments(self, request, queryset):
        queryset.update(is_approved=True)
    approve_comments.short_description = "Approve selected comments"