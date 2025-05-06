from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.db.models import Count, Sum
from django.core.paginator import Paginator
from news.models import News, Category, Comment, NewsMedia
from .forms import NewsForm, NewsMediaFormSet

@login_required
def writer_dashboard(request):
    """Main dashboard view for writers"""
    student_profile = request.user.profile
    
    # Get writer's statistics
    total_posts = News.objects.filter(author=student_profile).count()
    published_posts = News.objects.filter(author=student_profile, status='published').count()
    draft_posts = News.objects.filter(author=student_profile, status='draft').count()
    total_views = News.objects.filter(author=student_profile).aggregate(Sum('views'))['views__sum'] or 0
    
    # Get top performing posts
    top_posts = News.objects.filter(author=student_profile, status='published').order_by('-views')[:5]
    
    # Get recent posts
    recent_posts = News.objects.filter(author=student_profile).order_by('-created_at')[:5]
    
    # Get recent comments on writer's posts
    recent_comments = Comment.objects.filter(news__author=student_profile).order_by('-created_at')[:5]
    
    # Category distribution
    category_stats = (News.objects
                     .filter(author=student_profile)
                     .values('category__name')
                     .annotate(count=Count('id'))
                     .order_by('-count'))
    
    # Media statistics
    total_media = NewsMedia.objects.filter(news__author=student_profile).count()
    media_type_counts = (NewsMedia.objects
                        .filter(news__author=student_profile)
                        .values('media_type')
                        .annotate(count=Count('id'))
                        .order_by('-count'))
    
    context = {
        'total_posts': total_posts,
        'published_posts': published_posts,
        'draft_posts': draft_posts,
        'total_views': total_views,
        'top_posts': top_posts,
        'recent_posts': recent_posts,
        'recent_comments': recent_comments,
        'category_stats': list(category_stats),
        'total_media': total_media,
        'media_type_counts': list(media_type_counts),
    }
    
    return render(request, 'dashboard/writer_dashboard.html', context)

@login_required
def post_list(request):
    """View that shows all posts by the logged-in writer"""
    student_profile = request.user.profile
    
    # Filter parameters
    status = request.GET.get('status', '')
    category = request.GET.get('category', '')
    
    posts = News.objects.filter(author=student_profile)
    
    # Apply filters
    if status:
        posts = posts.filter(status=status)
    if category:
        posts = posts.filter(category__slug=category)
        
    # Sorting
    sort_by = request.GET.get('sort', '-created_at')
    posts = posts.order_by(sort_by)
    
    # Pagination
    paginator = Paginator(posts, 10)  # 10 posts per page
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    # Get all categories for filter dropdown
    categories = Category.objects.all()
    
    context = {
        'page_obj': page_obj,
        'categories': categories,
        'current_status': status,
        'current_category': category,
        'current_sort': sort_by,
    }
    
    return render(request, 'dashboard/writer_posts.html', context)

@login_required
def create_post(request):
    """View to create a new post with multiple media files"""
    if request.method == 'POST':
        form = NewsForm(request.POST, request.FILES)
        formset = NewsMediaFormSet(request.POST, request.FILES)
        
        if form.is_valid() and formset.is_valid():
            post = form.save(commit=False)
            post.author = request.user.profile
            
            # If publishing, set publish date
            if post.status == 'published' and not post.publish_date:
                post.publish_date = timezone.now()
                
            post.save()
            
            # Save tags
            form.save_m2m()
            
            # Save media files
            media_instances = formset.save(commit=False)
            for media in media_instances:
                media.news = post
                media.save()
            
            messages.success(request, 'Your post was created successfully!')
            return redirect('dashboard:writer_dashboard')
    else:
        form = NewsForm()
        formset = NewsMediaFormSet()
    
    context = {
        'form': form,
        'formset': formset,
        'title': 'Create New Post',
    }
    
    return render(request, 'dashboard/post_form.html', context)

@login_required
def edit_post(request, slug):
    """View to edit an existing post with multiple media files"""
    student_profile = request.user.profile
    post = get_object_or_404(News, slug=slug, author=student_profile)
    
    if request.method == 'POST':
        form = NewsForm(request.POST, request.FILES, instance=post)
        formset = NewsMediaFormSet(request.POST, request.FILES, instance=post)
        
        if form.is_valid() and formset.is_valid():
            updated_post = form.save(commit=False)
            
            # Update publish date if status changed from draft to published
            was_draft = post.status == 'draft'
            now_published = updated_post.status == 'published'
            
            if was_draft and now_published and not updated_post.publish_date:
                updated_post.publish_date = timezone.now()
                
            updated_post.save()
            form.save_m2m()  # Save tags
            
            # Save media files
            media_instances = formset.save(commit=False)
            for media in media_instances:
                media.news = updated_post
                media.save()
                
            # Handle deleted media
            for obj in formset.deleted_objects:
                obj.delete()
            
            messages.success(request, 'Your post was updated successfully!')
            return redirect('dashboard:post_list')
    else:
        form = NewsForm(instance=post)
        formset = NewsMediaFormSet(instance=post)
    
    context = {
        'form': form,
        'formset': formset,
        'post': post,
        'title': 'Edit Post',
    }
    
    return render(request, 'dashboard/post_form.html', context)

@login_required
def post_analytics(request, slug):
    """View to show detailed analytics for a specific post"""
    student_profile = request.user.profile
    post = get_object_or_404(News, slug=slug, author=student_profile)
    
    # Get comment statistics
    comment_count = post.comments.count()
    approved_comment_count = post.approved_comments().count()
    
    # Get media statistics
    media_count = post.media_files.count()
    media_by_type = (post.media_files
                    .values('media_type')
                    .annotate(count=Count('id'))
                    .order_by('-count'))
    
    context = {
        'post': post,
        'comment_count': comment_count,
        'approved_comment_count': approved_comment_count,
        'media_count': media_count,
        'media_by_type': media_by_type,
    }
    
    return render(request, 'dashboard/post_analytics.html', context)

@login_required
def manage_comments(request):
    """View to manage comments on the writer's posts"""
    student_profile = request.user.profile
    
    # Get all comments on the writer's posts
    comments = Comment.objects.filter(news__author=student_profile).order_by('-created_at')
    
    # Filter by approval status if requested
    approval_status = request.GET.get('approved', '')
    if approval_status == 'yes':
        comments = comments.filter(is_approved=True)
    elif approval_status == 'no':
        comments = comments.filter(is_approved=False)
    
    # Pagination
    paginator = Paginator(comments, 20)  # 20 comments per page
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'current_filter': approval_status,
    }
    
    return render(request, 'dashboard/manage_comments.html', context)

@login_required
def approve_comment(request, comment_id):
    """View to approve a specific comment"""
    student_profile = request.user.profile
    comment = get_object_or_404(Comment, id=comment_id, news__author=student_profile)
    
    comment.is_approved = True
    comment.save()
    
    messages.success(request, 'Comment approved successfully!')
    return redirect('dashboard:manage_comments')

@login_required
def delete_comment(request, comment_id):
    """View to delete a specific comment"""
    student_profile = request.user.profile
    comment = get_object_or_404(Comment, id=comment_id, news__author=student_profile)
    
    comment.delete()
    
    messages.success(request, 'Comment deleted successfully!')
    return redirect('dashboard:manage_comments')

@login_required
def manage_media(request, slug):
    """View to manage media files for a specific post"""
    student_profile = request.user.profile
    post = get_object_or_404(News, slug=slug, author=student_profile)
    
    if request.method == 'POST':
        formset = NewsMediaFormSet(request.POST, request.FILES, instance=post)
        if formset.is_valid():
            # Save media files
            media_instances = formset.save(commit=False)
            for media in media_instances:
                media.news = post
                media.save()
                
            # Handle deleted media
            for obj in formset.deleted_objects:
                obj.delete()
                
            messages.success(request, 'Media files updated successfully!')
            return redirect('dashboard:post_list')
    else:
        formset = NewsMediaFormSet(instance=post)
    
    context = {
        'post': post,
        'formset': formset,
        'title': f'Manage Media for: {post.title}',
    }
    
    return render(request, 'dashboard/manage_media.html', context)