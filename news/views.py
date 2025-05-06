from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import ListView, DetailView
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.utils import timezone
from .models import News, Category, Comment
from .forms import CommentForm
from django.views.decorators.cache import cache_page
from functools import reduce
import operator

@cache_page(60*60)
def home_view(request):    
    return render(request, 'news/home.html')

# @cache_page(60 * 60)
class NewsList(ListView):
    model = News
    template_name = 'news/news_list.html'
    context_object_name = 'news_list'
    paginate_by = 8
    
    def get_queryset(self):
        return News.objects.filter(status='published').order_by('-publish_date')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = Category.objects.all()
        context['featured_news'] = News.objects.filter(is_featured=True, status='published').order_by('-publish_date')[:5]
        context['popular_news'] = News.objects.filter(status='published').order_by('-views')[:5]
        context['recent_news'] = News.objects.filter(status='published').order_by('-publish_date')[:5]
        return context

# @cache_page(60 * 60)
class CategoryNews(ListView):
    model = News
    template_name = 'news/category_news.html'
    context_object_name = 'news_list'
    paginate_by = 8
    
    def get_queryset(self):
        self.category = get_object_or_404(Category, slug=self.kwargs['slug'])
        return News.objects.filter(category=self.category, status='published').order_by('-publish_date')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['category'] = self.category
        context['categories'] = Category.objects.all()
        return context

class NewsDetail(DetailView):
    model = News
    template_name = 'news/news_detail.html'
    context_object_name = 'news'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        news = self.get_object()
        
        # Increase view count
        news.increase_views()
        
        # Related news based on same category
        related_news = News.objects.filter(category=news.category, status='published').exclude(id=news.id).order_by('-publish_date')[:3]
        context['related_news'] = related_news
        
        # Comments
        comments = news.approved_comments()
        context['comments'] = comments
        context['comment_form'] = CommentForm()
        
        # Categories for sidebar
        context['categories'] = Category.objects.all()
        
        # Popular news for sidebar
        context['popular_news'] = News.objects.filter(status='published').order_by('-views')[:5]
        
        return context

@login_required
def add_comment(request, slug):
    news = get_object_or_404(News, slug=slug)
    
    if request.method == 'POST':
        form = CommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.news = news
            comment.user = request.user
            comment.save()
            return redirect('news:news_detail', slug=news.slug)
    
    return redirect('news:news_detail', slug=news.slug)

@cache_page(60 * 15)  # Cache the results for 15 minutes
def search_news(request):
    query = request.GET.get('q', '').strip()
    category_id = request.GET.get('category')
    sort_by = request.GET.get('sort', '-publish_date')  # Default sort by newest
    results = []
    
    if query:
        # Split the query into keywords for better search
        keywords = query.split()
        
        # Create a base queryset with published news only
        base_queryset = News.objects.filter(status='published')
        
        # Apply category filter if provided
        if category_id:
            try:
                base_queryset = base_queryset.filter(category_id=int(category_id))
            except (ValueError, TypeError):
                pass  # Ignore invalid category_id
        
        # Search in multiple fields with OR condition
        search_fields = ['title', 'content', 'summary', 'tags__name']
        
        # Handle complex queries with multiple keywords
        if len(keywords) > 1:
            # For each keyword, create a complex query across all fields
            keyword_queries = []
            for keyword in keywords:
                field_queries = [Q(**{f"{field}__icontains": keyword}) for field in search_fields]
                keyword_queries.append(reduce(operator.or_, field_queries))
            
            # Combine all keyword queries with AND logic
            results = base_queryset.filter(reduce(operator.and_, keyword_queries))
        else:
            # Simple query with a single keyword
            field_queries = [Q(**{f"{field}__icontains": query}) for field in search_fields]
            results = base_queryset.filter(reduce(operator.or_, field_queries))
        
        # Apply sorting
        results = results.distinct().order_by(sort_by)
    else:
        # If no query provided, show featured or recent news
        results = News.objects.filter(status='published')
        if category_id:
            try:
                results = results.filter(category_id=int(category_id))
            except (ValueError, TypeError):
                pass
        results = results.order_by(sort_by)
    
    # Pagination
    per_page = int(request.GET.get('per_page', 8))  # Allow customizing items per page
    paginator = Paginator(results, per_page)
    page = request.GET.get('page')
    
    try:
        paginated_results = paginator.page(page)
    except PageNotAnInteger:
        paginated_results = paginator.page(1)
    except EmptyPage:
        paginated_results = paginator.page(paginator.num_pages)
    
    # Get popular searches or categories for sidebar
    popular_tags = News.objects.filter(status='published').values(
        'tags__name'
    ).exclude(tags__name=None).order_by('tags__name').distinct()[:10]
    
    context = {
        'results': paginated_results,
        'query': query,
        'categories': Category.objects.all(),
        'popular_tags': popular_tags,
        'current_category': category_id,
        'current_sort': sort_by,
        'total_results': paginator.count,
    }
    
    return render(request, 'news/search_results.html', context)