from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages

# from news.models import News
from .models import StudentRequest, StudentProfile
from .forms import StudentRequestForm, StudentProfileForm
from django.views.generic import ListView, DetailView

from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q
from django.shortcuts import get_object_or_404




@login_required
def student_request_view(request):
    """View for submitting a student status request"""
    # Check if user already has a request or is already a student
    try:
        student_request = StudentRequest.objects.get(user=request.user)
        return redirect('accounts:student_request_status')
    except StudentRequest.DoesNotExist:
        pass
    
    # Check if already has a profile (is already a student)
    try:
        student_profile = StudentProfile.objects.get(user=request.user)
        messages.info(request, "You are already a student.")
        return redirect('accounts:student_profile')
    except StudentProfile.DoesNotExist:
        pass
    
    if request.method == 'POST':
        form = StudentRequestForm(request.POST)
        if form.is_valid():
            student_request = form.save(commit=False)
            student_request.user = request.user
            student_request.save()
            messages.success(request, "Your student status request has been submitted!")
            return redirect('accounts:student_request_status')
    else:
        form = StudentRequestForm()
    
    return render(request, 'accounts/student_request_form.html', {'form': form})

@login_required
def student_request_status(request):
    """View for checking student request status"""
    try:
        student_request = StudentRequest.objects.get(user=request.user)
        return render(request, 'accounts/student_request_status.html', 
                      {'student_request': student_request})
    except StudentRequest.DoesNotExist:
        messages.warning(request, "You don't have an active student request.")
        return redirect('accounts:student_request')

@login_required
def student_profile_view(request):
    """View for viewing student profile"""
    try:
        profile = StudentProfile.objects.get(user=request.user)
        return render(request, 'accounts/student_profile.html', {'profile': profile})
    except StudentProfile.DoesNotExist:
        try:
            student_request = StudentRequest.objects.get(user=request.user)
            if student_request.approved:
                # Create profile if approved but no profile exists yet
                profile = StudentProfile.objects.create(user=request.user)
                messages.success(request, "Your profile has been created! Please complete your details.")
                return redirect('accounts:edit_student_profile')
            else:
                return redirect('accounts:student_request_status')
        except StudentRequest.DoesNotExist:
            messages.warning(request, "You need to request student status first.")
            return redirect('accounts:student_request')

@login_required
def edit_student_profile(request):
    """View for editing student profile"""
    try:
        profile = StudentProfile.objects.get(user=request.user)
    except StudentProfile.DoesNotExist:
        try:
            student_request = StudentRequest.objects.get(user=request.user, approved=True)
            # Create profile if approved but doesn't exist
            profile = StudentProfile.objects.create(user=request.user)
        except StudentRequest.DoesNotExist:
            messages.warning(request, "You need to be an approved student to edit your profile.")
            return redirect('accounts:student_request')
    
    if request.method == 'POST':
        form = StudentProfileForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            profile = form.save()
            if "save_and_contine" in request.POST:
                messages.success(request, "Your profile has been saved! You can Continue!")
                return redirect('accounts:edit_student_profile')
            else:
                messages.success(request, "Your profile has been updated!")
                return redirect('profile_detail', slug=profile.slug)
    else:
        form = StudentProfileForm(instance=profile)
    
    return render(request, 'accounts/edit_student_profile.html', {'form': form,
            "last_name": request.user.first_name,
            "first_name": request.user.last_name,})

class ProfileListView(LoginRequiredMixin, ListView):
    model = StudentProfile
    template_name = 'accounts/profile_list.html'
    context_object_name = 'profiles'
    paginate_by = 10  # Show 10 profiles per page
    
    def get_queryset(self):
        """Optimize query and apply filters if provided."""
        queryset = StudentProfile.objects.select_related('user')
        
        # Apply search filter if provided in GET parameters
        search_term = self.request.GET.get('search')
        if search_term:
            queryset = queryset.filter(
                Q(user__first_name__icontains=search_term) |
                Q(user__last_name__icontains=search_term) |
                Q(bio__icontains=search_term) |
                Q(user__username__icontains=search_term)
            )
                
        return queryset.order_by('-created_at')
    
    def get_context_data(self, **kwargs):
        """Add additional context data."""
        context = super().get_context_data(**kwargs)
        
        # Add search term to context
        context['search_term'] = self.request.GET.get('search', '')
        
        # Add any extra context data
        context['page_title'] = 'Student Profiles'
        context['total_profiles'] = StudentProfile.objects.count()
        
        return context


class ProfileDetailView(LoginRequiredMixin, DetailView):
    model = StudentProfile
    template_name = 'accounts/profile_detail.html'
    context_object_name = 'profile'
    slug_field = 'slug'
    slug_url_kwarg = 'slug'
    
    def get_queryset(self):
        """Optimize the query with related data."""
        return StudentProfile.objects.select_related('user')
    
    def get_object(self, queryset=None):
        """
        Override to add custom 404 handling or fallback to ID if slug not found.
        """
        if queryset is None:
            queryset = self.get_queryset()
            
        # Try to find by slug
        slug = self.kwargs.get(self.slug_url_kwarg)
        if slug:
            try:
                obj = queryset.get(**{self.slug_field: slug})
                return obj
            except self.model.DoesNotExist:
                pass
                
        # Fallback to ID if provided
        pk = self.kwargs.get('pk')
        if pk:
            return get_object_or_404(queryset, pk=pk)
            
        return super().get_object(queryset=queryset)
        
    def get_context_data(self, **kwargs):
        """Add additional context data."""
        context = super().get_context_data(**kwargs)
        
        # Add profile data
        profile = context['profile']
        context['page_title'] = f"{profile.full_name}'s Profile"
        context['last_updated'] = profile.updated_at
        
        # Add permissions context
        context['can_edit'] = (
            self.request.user == profile.user or 
            self.request.user.is_staff
        )
        
        return context
