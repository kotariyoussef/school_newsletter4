from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import ListView, DetailView
from django.contrib.auth.decorators import login_required
from django.db.models import Count
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.utils import timezone
from .models import News, Category, Comment
from .forms import CommentForm
from django.views.decorators.cache import cache_page

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

def search_news(request):
    query = request.GET.get('q')
    results = []
    
    if query:
        results = News.objects.filter(
            status='published',
            title__icontains=query
        ) | News.objects.filter(
            status='published',
            content__icontains=query
        ) | News.objects.filter(
            status='published',
            summary__icontains=query
        ) | News.objects.filter(
            status='published',
            tags__name__icontains=query
        )
        results = results.distinct().order_by('-publish_date')
    
    paginator = Paginator(results, 8)
    page = request.GET.get('page')
    
    try:
        results = paginator.page(page)
    except PageNotAnInteger:
        results = paginator.page(1)
    except EmptyPage:
        results = paginator.page(paginator.num_pages)
    
    context = {
        'results': results,
        'query': query,
        'categories': Category.objects.all(),
    }
    
    return render(request, 'news/search_results.html', context)