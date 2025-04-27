from django.urls import path
from . import views

app_name = 'news'

urlpatterns = [
    path('', views.NewsList.as_view(), name='news_list'),
    path('search/', views.search_news, name='news_search'),
    path('category/<slug:slug>/', views.CategoryNews.as_view(), name='news_by_category'),
    path('<slug:slug>/', views.NewsDetail.as_view(), name='news_detail'),
    path('<slug:slug>/comment/', views.add_comment, name='add_comment'),
]
