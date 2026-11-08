from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django import forms
from .models import Resume, ResumeComment, Vacancy


class RegistrationForm(UserCreationForm):
    class Meta:
        model = User
        fields = ('username', 'email')
        labels = {
            'username': 'Ім’я користувача',
            'email': 'Електронна пошта',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['password1'].label = 'Пароль'
        self.fields['password2'].label = 'Підтвердження пароля'
        self.fields['username'].widget.attrs.update({
            'autocomplete': 'username',
            'autofocus': True,
        })
        self.fields['email'].required = False
        self.fields['email'].widget.attrs['autocomplete'] = 'email'
        self.fields['password1'].widget.attrs['autocomplete'] = 'new-password'
        self.fields['password2'].widget.attrs['autocomplete'] = 'new-password'


class VacancyForm(forms.ModelForm):
    class Meta:
        model = Vacancy
        fields = ('title', 'company', 'city', 'description', 'requirements')
        labels = {
            'title': 'Назва посади',
            'company': 'Компанія',
            'city': 'Місто',
            'description': 'Опис вакансії',
            'requirements': 'Вимоги до кандидата',
        }
        widgets = {
            'description': forms.Textarea(attrs={'rows': 5}),
            'requirements': forms.Textarea(attrs={'rows': 5}),
        }


class ResumeCommentForm(forms.ModelForm):
    class Meta:
        model = ResumeComment
        fields = ('text',)
        labels = {
            'text': 'Коментар',
        }
        widgets = {
            'text': forms.Textarea(attrs={
                'rows': 4,
                'placeholder': 'Напишіть коментар до резюме',
            }),
        }


class VacancyApplicationForm(forms.Form):
    resume = forms.ModelChoiceField(
        queryset=Resume.objects.none(),
        label='Резюме для відгуку',
        empty_label='Оберіть резюме',
    )

    def __init__(self, *args, user, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['resume'].queryset = Resume.objects.filter(user=user)
        self.fields['resume'].widget.attrs.update({'class': 'form-select'})
