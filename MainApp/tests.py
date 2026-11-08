from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User
from .models import Resume, ResumeComment, Vacancy, VacancyApplication


class RegistrationTests(TestCase):
    def test_registration_page_is_accessible_and_linked_in_navigation(self):
        response = self.client.get(reverse('register'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Зареєструватися')
        self.assertContains(response, reverse('register'))

    def test_valid_registration_creates_and_logs_in_user(self):
        response = self.client.post(reverse('register'), {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password1': 'SafePassword!927',
            'password2': 'SafePassword!927',
        })

        self.assertRedirects(response, reverse('resume_edit'))
        self.assertTrue(response.wsgi_request.user.is_authenticated)
        self.assertTrue(User.objects.filter(username='newuser').exists())

    def test_invalid_registration_shows_validation_errors(self):
        response = self.client.post(reverse('register'), {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password1': 'short',
            'password2': 'short',
        })

        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.wsgi_request.user.is_authenticated)
        self.assertContains(response, 'role="alert"')
        self.assertContains(response, 'Пароль має складатися щонайменше з 8 символів.')
        self.assertContains(response, 'Введіть той же пароль')


class VacancyTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='employer', password='SafePassword!927')

    def test_vacancy_list_and_detail_are_public(self):
        vacancy = Vacancy.objects.create(
            user=self.user,
            title='Розробник',
            company='Приклад',
            description='Опис посади',
        )

        list_response = self.client.get(reverse('vacancy_list'))
        detail_response = self.client.get(reverse('vacancy_detail', args=[vacancy.pk]))

        self.assertEqual(list_response.status_code, 200)
        self.assertContains(list_response, 'Розробник')
        self.assertEqual(detail_response.status_code, 200)
        self.assertContains(detail_response, 'Опис посади')

    def test_vacancy_creation_requires_login(self):
        response = self.client.get(reverse('vacancy_create'))

        self.assertRedirects(
            response,
            f"{reverse('login')}?next={reverse('vacancy_create')}",
        )

    def test_authenticated_user_can_create_vacancy(self):
        self.client.force_login(self.user)
        response = self.client.post(reverse('vacancy_create'), {
            'title': 'Дизайнер',
            'company': 'Студія',
            'city': 'Київ',
            'description': 'Створення інтерфейсів.',
            'requirements': 'Досвід роботи.',
        })

        self.assertRedirects(response, reverse('vacancy_list'))
        vacancy = Vacancy.objects.get(title='Дизайнер')
        self.assertEqual(vacancy.user, self.user)

    def test_candidate_can_apply_with_their_resume(self):
        candidate = User.objects.create_user(username='candidate', password='SafePassword!927')
        resume = Resume.objects.create(
            user=candidate,
            name='Олена Коваль',
            email='olena@example.com',
            skills='Python',
        )
        vacancy = Vacancy.objects.create(
            user=self.user,
            title='Розробник',
            company='Приклад',
            description='Опис посади',
        )
        self.client.force_login(candidate)

        response = self.client.post(
            reverse('vacancy_detail', args=[vacancy.pk]),
            {'resume': resume.pk},
        )

        self.assertRedirects(response, reverse('vacancy_detail', args=[vacancy.pk]))
        application = VacancyApplication.objects.get(vacancy=vacancy)
        self.assertEqual(application.applicant, candidate)
        self.assertEqual(application.resume, resume)

    def test_only_candidate_and_vacancy_owner_can_see_application(self):
        candidate = User.objects.create_user(username='candidate', password='SafePassword!927')
        resume = Resume.objects.create(
            user=candidate,
            name='Олена Коваль',
            email='private@example.com',
            skills='Private skill',
        )
        vacancy = Vacancy.objects.create(
            user=self.user,
            title='Розробник',
            company='Приклад',
            description='Опис посади',
        )
        VacancyApplication.objects.create(
            vacancy=vacancy,
            applicant=candidate,
            resume=resume,
        )

        owner_response = self.client.get(reverse('vacancy_detail', args=[vacancy.pk]))
        self.assertNotContains(owner_response, 'private@example.com')
        self.client.force_login(self.user)
        owner_response = self.client.get(reverse('vacancy_detail', args=[vacancy.pk]))
        self.assertContains(owner_response, 'Олена Коваль')
        self.assertContains(owner_response, 'private@example.com')

        other_user = User.objects.create_user(username='other', password='SafePassword!927')
        self.client.force_login(other_user)
        other_response = self.client.get(reverse('vacancy_detail', args=[vacancy.pk]))
        self.assertNotContains(other_response, 'Олена Коваль')
        self.assertNotContains(other_response, 'private@example.com')

        self.client.force_login(candidate)
        candidate_response = self.client.get(reverse('vacancy_detail', args=[vacancy.pk]))
        self.assertContains(candidate_response, 'Олена Коваль')
        self.assertContains(candidate_response, 'private@example.com')

    def test_candidate_cannot_apply_with_another_users_resume(self):
        candidate = User.objects.create_user(username='candidate', password='SafePassword!927')
        resume = Resume.objects.create(user=self.user, name='Резюме роботодавця', email='owner@example.com')
        vacancy = Vacancy.objects.create(
            user=self.user,
            title='Розробник',
            company='Приклад',
            description='Опис посади',
        )
        self.client.force_login(candidate)

        response = self.client.post(
            reverse('vacancy_detail', args=[vacancy.pk]),
            {'resume': resume.pk},
        )

        self.assertEqual(response.status_code, 400)
        self.assertFalse(VacancyApplication.objects.filter(vacancy=vacancy).exists())

    def test_candidate_cannot_apply_to_own_vacancy(self):
        resume = Resume.objects.create(user=self.user, name='Резюме автора', email='owner@example.com')
        vacancy = Vacancy.objects.create(
            user=self.user,
            title='Розробник',
            company='Приклад',
            description='Опис посади',
        )
        self.client.force_login(self.user)

        response = self.client.post(
            reverse('vacancy_detail', args=[vacancy.pk]),
            {'resume': resume.pk},
        )

        self.assertRedirects(response, reverse('vacancy_detail', args=[vacancy.pk]))
        self.assertFalse(VacancyApplication.objects.filter(vacancy=vacancy).exists())

    def test_candidate_can_submit_only_one_application_to_a_vacancy(self):
        candidate = User.objects.create_user(username='candidate', password='SafePassword!927')
        resume = Resume.objects.create(user=candidate, name='Олена Коваль', email='olena@example.com')
        vacancy = Vacancy.objects.create(
            user=self.user,
            title='Розробник',
            company='Приклад',
            description='Опис посади',
        )
        VacancyApplication.objects.create(vacancy=vacancy, applicant=candidate, resume=resume)
        self.client.force_login(candidate)

        response = self.client.post(
            reverse('vacancy_detail', args=[vacancy.pk]),
            {'resume': resume.pk},
        )

        self.assertRedirects(response, reverse('vacancy_detail', args=[vacancy.pk]))
        self.assertEqual(VacancyApplication.objects.filter(vacancy=vacancy).count(), 1)

    def test_anonymous_user_is_prompted_to_log_in_before_applying(self):
        vacancy = Vacancy.objects.create(
            user=self.user,
            title='Розробник',
            company='Приклад',
            description='Опис посади',
        )

        response = self.client.post(
            reverse('vacancy_detail', args=[vacancy.pk]),
            {'resume': '1'},
        )

        self.assertRedirects(
            response,
            f"{reverse('login')}?next={reverse('vacancy_detail', args=[vacancy.pk])}",
        )
        self.assertFalse(VacancyApplication.objects.exists())


class PublicResumeTests(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user(username='candidate', password='SafePassword!927')
        self.resume = Resume.objects.create(
            user=self.owner,
            name='Олена Коваль',
            email='olena@example.com',
            phone='+380501234567',
            city='Львів',
            skills='Python, Django',
        )

    def test_resume_is_private_by_default_and_hidden_from_public_list(self):
        self.assertFalse(self.resume.is_public)

        response = self.client.get(reverse('public_resume_list'))

        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, 'Олена Коваль')

    def test_private_resume_returns_not_found_when_opened_directly(self):
        response = self.client.get(reverse('public_resume_detail', args=[self.resume.pk]))

        self.assertEqual(response.status_code, 404)

    def test_public_resume_appears_and_can_be_viewed_without_contact_consent(self):
        self.resume.is_public = True
        self.resume.save()

        list_response = self.client.get(reverse('public_resume_list'))
        detail_response = self.client.get(reverse('public_resume_detail', args=[self.resume.pk]))

        self.assertContains(list_response, 'Олена Коваль')
        self.assertEqual(detail_response.status_code, 200)
        self.assertContains(detail_response, 'Python, Django')
        self.assertNotContains(detail_response, 'olena@example.com')
        self.assertNotContains(detail_response, '+380501234567')

    def test_search_matches_name_city_and_skills(self):
        self.resume.is_public = True
        self.resume.save()

        for query in ('Олена', 'Львів', 'Django'):
            with self.subTest(query=query):
                response = self.client.get(reverse('public_resume_list'), {'q': query})
                self.assertContains(response, 'Олена Коваль')

    def test_owner_can_publish_and_revoke_publication(self):
        self.client.force_login(self.owner)
        edit_url = reverse('resume_edit')
        form_data = {
            'name': self.resume.name,
            'email': self.resume.email,
            'phone': self.resume.phone,
            'city': self.resume.city,
            'about': self.resume.about,
            'education': self.resume.education,
            'experience': self.resume.experience,
            'skills': self.resume.skills,
            'is_public': 'on',
            'show_email': 'on',
        }

        self.client.post(edit_url, form_data)
        self.resume.refresh_from_db()
        self.assertTrue(self.resume.is_public)
        self.assertTrue(self.resume.show_email)

        form_data.pop('is_public')
        form_data.pop('show_email')
        self.client.post(edit_url, form_data)
        self.resume.refresh_from_db()
        self.assertFalse(self.resume.is_public)
        self.assertFalse(self.resume.show_email)
        self.assertEqual(
            self.client.get(reverse('public_resume_detail', args=[self.resume.pk])).status_code,
            404,
        )

    def test_contact_details_are_shown_only_with_explicit_consent(self):
        self.resume.is_public = True
        self.resume.show_email = True
        self.resume.show_phone = True
        self.resume.save()

        response = self.client.get(reverse('public_resume_detail', args=[self.resume.pk]))

        self.assertContains(response, 'olena@example.com')
        self.assertContains(response, '+380501234567')

    def test_public_resume_shows_comments_and_comment_form_to_signed_in_user(self):
        self.resume.is_public = True
        self.resume.save()
        commenter = User.objects.create_user(username='recruiter', password='SafePassword!927')
        ResumeComment.objects.create(
            resume=self.resume,
            user=commenter,
            text='Дуже цікавий досвід.',
        )
        self.client.force_login(commenter)

        response = self.client.get(reverse('public_resume_detail', args=[self.resume.pk]))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Дуже цікавий досвід.')
        self.assertContains(response, 'Залишити коментар')

    def test_authenticated_user_can_comment_on_public_resume(self):
        self.resume.is_public = True
        self.resume.save()
        commenter = User.objects.create_user(username='recruiter', password='SafePassword!927')
        self.client.force_login(commenter)

        response = self.client.post(
            reverse('public_resume_detail', args=[self.resume.pk]),
            {'text': 'Хотів би обговорити ваш досвід.'},
        )

        self.assertRedirects(response, reverse('public_resume_detail', args=[self.resume.pk]))
        comment = ResumeComment.objects.get(resume=self.resume)
        self.assertEqual(comment.user, commenter)
        self.assertEqual(comment.text, 'Хотів би обговорити ваш досвід.')

    def test_anonymous_user_is_prompted_to_log_in_before_commenting(self):
        self.resume.is_public = True
        self.resume.save()

        response = self.client.post(
            reverse('public_resume_detail', args=[self.resume.pk]),
            {'text': 'Коментар'},
        )

        self.assertRedirects(
            response,
            f"{reverse('login')}?next={reverse('public_resume_detail', args=[self.resume.pk])}",
        )
        self.assertFalse(ResumeComment.objects.filter(resume=self.resume).exists())

    def test_private_resume_cannot_receive_comments(self):
        commenter = User.objects.create_user(username='recruiter', password='SafePassword!927')
        self.client.force_login(commenter)

        response = self.client.post(
            reverse('public_resume_detail', args=[self.resume.pk]),
            {'text': 'Коментар'},
        )

        self.assertEqual(response.status_code, 404)
        self.assertFalse(ResumeComment.objects.filter(resume=self.resume).exists())

    def test_empty_comment_is_rejected(self):
        self.resume.is_public = True
        self.resume.save()
        commenter = User.objects.create_user(username='recruiter', password='SafePassword!927')
        self.client.force_login(commenter)

        response = self.client.post(
            reverse('public_resume_detail', args=[self.resume.pk]),
            {'text': '   '},
        )

        self.assertEqual(response.status_code, 400)
        self.assertFalse(ResumeComment.objects.filter(resume=self.resume).exists())
