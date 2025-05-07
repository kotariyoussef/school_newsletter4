from django.shortcuts import redirect, render
from django.urls import reverse_lazy
from django.views.generic import FormView, TemplateView
from django.contrib import messages
from django.core.mail import send_mail
from django.conf import settings
from .forms import ContactForm
from django.conf import settings


def error_404_view(request, exception=None):
    """
    Handle 404 page not found errors
    """
    # Get popular news and categories for the footer
    # You may need to adjust these imports and queries based on your project structure
    from news.models import News, Category
    
    popular_news = News.objects.filter(status='published').order_by('-views')[:3]
    categories = Category.objects.all()
    
    context = {
        'popular_news': popular_news,
        'categories': categories,
    }
    return render(request, '404.html', context, status=404)


def error_500_view(request):
    """
    Handle 500 server error
    """
    # For 500 errors, we might not be able to query the database reliably
    # so we'll render the template without additional context
    return render(request, '500.html', {}, status=500)


def error_403_view(request, exception=None):
    """
    Handle 403 permission denied errors
    """
    # Get popular news and categories for the footer
    from news.models import News, Category
    
    popular_news = News.objects.filter(status='published').order_by('-views')[:3]
    categories = Category.objects.all()
    
    context = {
        'popular_news': popular_news,
        'categories': categories,
    }
    return render(request, '403.html', context, status=403)

class AboutUsView(TemplateView):
    template_name = "about_us.html"

class ContactView(FormView):
    template_name = 'contact/contact.html'
    form_class = ContactForm
    success_url = reverse_lazy('contact_success')
    
    def form_valid(self, form):
        # Save the contact message
        contact = form.save()
        
        # Send notification email to admin
        subject = f"New contact message: {contact.subject}"
        message = f"You received a new message from {contact.name} ({contact.email}):\n\n{contact.message}"
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [settings.ADMIN_EMAIL],  # Add this to your settings.py
            fail_silently=False,
        )
        
        messages.success(self.request, "Your message has been sent successfully!")
        return super().form_valid(form)

class ContactSuccessView(TemplateView):
    template_name = 'contact/contact_success.html'

# class SubscribeView(FormView):
#     template_name = 'contact/subscribe.html'
#     form_class = SubscriptionForm
#     success_url = reverse_lazy('subscribe_success')
    
#     def form_valid(self, form):
#         email = form.cleaned_data['email']
        
#         # Check if subscriber already exists
#         subscriber, created = Subscriber.objects.get_or_create(
#             email=email
#         )
        
#         if created:         
#             messages.success(self.request, "Thanks for subscribing!")
#         else:
#             if subscriber.is_active:
#                 messages.info(self.request, "You're already subscribed to our newsletter!")
#             else:
#                 # Reactivate and send confirmation if previously unsubscribed
#                 subscriber.is_active = True
#                 subscriber.save()
                
#                 # Send confirmation email (similar to above)
#                 messages.success(self.request, 
#                     "We've sent you a confirmation email to reactivate your subscription.")
        
#         return super().form_valid(form)

# class SubscribeSuccessView(TemplateView):
#     template_name = 'contact/subscribe_success.html'

# def unsubscribe(request, email):
#     try:
#         subscriber = Subscriber.objects.get(email=email)
#         subscriber.is_active = False
#         subscriber.save()
#         messages.success(request, "You have been unsubscribed successfully.")
#     except Subscriber.DoesNotExist:
#         messages.error(request, "Email address not found in our subscribers list.")
    
#     return redirect('home')  # Redirect to your homepage