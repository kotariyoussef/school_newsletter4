from django.test import TestCase, Client
from django.urls import reverse
from .models import ContactMessage, Subscriber
from .forms import ContactForm, SubscriptionForm

class ContactFormTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.contact_url = reverse('contact')
        self.valid_data = {
            'name': 'Test User',
            'email': 'test@example.com',
            'subject': 'Test Subject',
            'message': 'This is a test message.'
        }
    
    def test_contact_form_valid(self):
        form = ContactForm(data=self.valid_data)
        self.assertTrue(form.is_valid())
    
    def test_contact_form_invalid(self):
        # Test with missing required fields
        invalid_data = self.valid_data.copy()
        invalid_data.pop('email')
        form = ContactForm(data=invalid_data)
        self.assertFalse(form.is_valid())
    
    def test_contact_view_post(self):
        # Test that form submission creates a contact message
        initial_count = ContactMessage.objects.count()
        response = self.client.post(self.contact_url, self.valid_data)
        self.assertEqual(ContactMessage.objects.count(), initial_count + 1)
        self.assertRedirects(response, reverse('contact_success'))

class SubscriptionFormTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.subscribe_url = reverse('subscribe')
        self.valid_data = {
            'email': 'subscriber@example.com',
            'name': 'New Subscriber'
        }
        # Create an existing subscriber for duplicate tests
        Subscriber.objects.create(
            email='existing@example.com',
            name='Existing Subscriber',
            is_active=True
        )
    
    def test_subscription_form_valid(self):
        form = SubscriptionForm(data=self.valid_data)
        self.assertTrue(form.is_valid())
    
    def test_subscription_form_invalid(self):
        # Test with invalid email
        invalid_data = self.valid_data.copy()
        invalid_data['email'] = 'not-an-email'
        form = SubscriptionForm(data=invalid_data)
        self.assertFalse(form.is_valid())
    
    def test_subscription_view_new_subscriber(self):
        # Test creating a new subscriber
        initial_count = Subscriber.objects.count()
        response = self.client.post(self.subscribe_url, self.valid_data)
        self.assertEqual(Subscriber.objects.count(), initial_count + 1)
        self.assertRedirects(response, reverse('subscribe_success'))
        
        # Verify subscriber was created with a confirmation token
        new_subscriber = Subscriber.objects.get(email=self.valid_data['email'])
        self.assertIsNotNone(new_subscriber.confirmation_token)
    
    def test_subscription_view_existing_subscriber(self):
        # Test submitting with an existing subscriber's email
        existing_data = {
            'email': 'existing@example.com',
            'name': 'New Name'  # Different name
        }
        initial_count = Subscriber.objects.count()
        response = self.client.post(self.subscribe_url, existing_data)
        
        # Count should not change, existing subscriber should not be duplicated
        self.assertEqual(Subscriber.objects.count(), initial_count)
        self.assertRedirects(response, reverse('subscribe_success'))

class UnsubscribeTest(TestCase):
    def setUp(self):
        self.subscriber = Subscriber.objects.create(
            email='active@example.com',
            name='Active Subscriber',
            is_active=True
        )
    
    def test_unsubscribe(self):
        # Test unsubscribe functionality
        unsubscribe_url = reverse('unsubscribe', kwargs={'email': self.subscriber.email})
        response = self.client.get(unsubscribe_url)
        
        # Refresh from database
        self.subscriber.refresh_from_db()
        self.assertFalse(self.subscriber.is_active)
        self.assertRedirects(response, reverse('home'))