from django.contrib.auth import login
from django.contrib.auth.views import redirect_to_login
from django.db.models import Q
from django.shortcuts import redirect, render
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import CreateView, DetailView, ListView
from django.contrib.auth.mixins import LoginRequiredMixin
from .forms import RegistrationForm, ResumeCommentForm, VacancyApplicationForm, VacancyForm
from .models import UserProfile, Resume, ResumeComment, Vacancy, VacancyApplication


def register(request):
    if request.user.is_authenticated:
        return redirect('resume_edit')

    form = RegistrationForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        user = form.save()
        login(request, user)
        return redirect('resume_edit')

    return render(request, 'registration/register.html', {'form': form})


class VacancyListView(ListView):
    model = Vacancy
    template_name = 'vacancies/vacancy_list.html'
    context_object_name = 'vacancies'


class VacancyDetailView(DetailView):
    model = Vacancy
    template_name = 'vacancies/vacancy_detail.html'
    context_object_name = 'vacancy'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        is_vacancy_owner = user.is_authenticated and self.object.user_id == user.pk
        own_application = None

        if user.is_authenticated:
            applications = VacancyApplication.objects.filter(
                vacancy=self.object,
            ).select_related('applicant', 'resume')
            if is_vacancy_owner:
                context['applications'] = applications
            else:
                own_application = applications.filter(applicant=user).first()
                context['applications'] = (
                    [own_application] if own_application else []
                )

        context['is_vacancy_owner'] = is_vacancy_owner
        context['own_application'] = own_application
        context['can_apply'] = (
            user.is_authenticated
            and not is_vacancy_owner
            and own_application is None
        )
        if context['can_apply']:
            form = kwargs.get('application_form') or VacancyApplicationForm(user=user)
            context['application_form'] = form
            context['has_resumes'] = form.fields['resume'].queryset.exists()
        return context

    def post(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect_to_login(request.get_full_path())

        self.object = self.get_object()
        if self.object.user_id == request.user.pk:
            return redirect('vacancy_detail', pk=self.object.pk)

        existing_application = VacancyApplication.objects.filter(
            vacancy=self.object,
            applicant=request.user,
        ).first()
        if existing_application:
            return redirect('vacancy_detail', pk=self.object.pk)

        form = VacancyApplicationForm(request.POST, user=request.user)
        if form.is_valid():
            VacancyApplication.objects.get_or_create(
                vacancy=self.object,
                applicant=request.user,
                defaults={'resume': form.cleaned_data['resume']},
            )
            return redirect('vacancy_detail', pk=self.object.pk)

        return self.render_to_response(
            self.get_context_data(application_form=form),
            status=400,
        )


class VacancyCreateView(LoginRequiredMixin, CreateView):
    model = Vacancy
    form_class = VacancyForm
    template_name = 'vacancies/vacancy_form.html'
    success_url = reverse_lazy('vacancy_list')

    def form_valid(self, form):
        form.instance.user = self.request.user
        return super().form_valid(form)


class PublicResumeListView(ListView):
    model = Resume
    template_name = 'resumes/public_resume_list.html'
    context_object_name = 'resumes'

    def get_queryset(self):
        queryset = Resume.objects.filter(is_public=True)
        query = self.request.GET.get('q', '').strip()
        if query:
            queryset = queryset.filter(
                Q(name__icontains=query)
                | Q(city__icontains=query)
                | Q(skills__icontains=query)
            )
        return queryset


class PublicResumeDetailView(DetailView):
    model = Resume
    template_name = 'resumes/public_resume_detail.html'
    context_object_name = 'resume'

    def get_queryset(self):
        return Resume.objects.filter(is_public=True)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.setdefault('comment_form', ResumeCommentForm())
        return context

    def post(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect_to_login(request.get_full_path())

        self.object = self.get_object()
        form = ResumeCommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.resume = self.object
            comment.user = request.user
            comment.save()
            return redirect('public_resume_detail', pk=self.object.pk)

        return self.render_to_response(
            self.get_context_data(comment_form=form),
            status=400,
        )


def get_user_resume(user):
    return Resume.objects.get_or_create(
        user=user,
        defaults={
            'name': user.get_full_name() or user.username,
            'email': user.email,
        },
    )[0]


class UserProfileView(LoginRequiredMixin, View):
    def get(self, request):
        user_profile, created = UserProfile.objects.get_or_create(user=request.user)
        resume = get_user_resume(request.user)
        context = {
            'user_profile': user_profile,
            'resume': resume,
        }

        return render(request, 'user_profile.html', context)

class ResumeView(LoginRequiredMixin, View):
    def get(self, request):
        resume = get_user_resume(request.user)
        context = {
            'resume': resume,
        }
        return render(request, 'resume.html', context)
    
class ResumeEditView(LoginRequiredMixin, View):
    def get(self, request):
        resume = get_user_resume(request.user)
        context = {
            'resume': resume,
        }
        return render(request, 'resume_edit.html', context)

    def post(self, request):
        resume = get_user_resume(request.user)
        resume.name = request.POST.get('name', resume.name)
        resume.email = request.POST.get('email', resume.email)
        resume.phone = request.POST.get('phone', resume.phone)
        resume.city = request.POST.get('city', resume.city)
        resume.about = request.POST.get('about', resume.about)
        resume.education = request.POST.get('education', resume.education)
        resume.experience = request.POST.get('experience', resume.experience)
        resume.skills = request.POST.get('skills', resume.skills)
        resume.is_public = 'is_public' in request.POST
        resume.show_email = 'show_email' in request.POST
        resume.show_phone = 'show_phone' in request.POST
        resume.save()
        
        return render(request, 'resume_edit.html', {'resume': resume, 'success': True})