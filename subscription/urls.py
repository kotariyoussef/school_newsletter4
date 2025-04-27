from django.urls import path
from . import views

urlpatterns = [
    path('contact/', views.ContactView.as_view(), name='contact'),
    path('contact/success/', views.ContactSuccessView.as_view(), name='contact_success'),
    # path('subscribe/', views.SubscribeView.as_view(), name='subscribe'),
    # path('subscribe/success/', views.SubscribeSuccessView.as_view(), name='subscribe_success'),
    # path('unsubscribe/<str:email>/', views.unsubscribe, name='unsubscribe'),
]