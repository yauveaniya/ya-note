from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from notes.models import Note

User = get_user_model()


class TestRoutes(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.author = User.objects.create(username='Василий')
        cls.reader = User.objects.create(username='Читатель простой')
        cls.note = Note.objects.create(title='Заголовок', text='Текст',
                                       author=cls.author)

    def test_pages_availability_for_anonymous_user(self):
        for name in ('notes:home', 'users:login', 'users:signup'):
            url = reverse(name)
            if name == 'users:logout':
                response = self.client.post(url)
                assert response.status_code == HTTPStatus.FOUND
            response = self.client.get(url)
            self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_pages_availability_for_author(self):
        users_statuses = (
            (self.author, HTTPStatus.OK),
            (self.reader, HTTPStatus.NOT_FOUND),
        )
        for user, status in users_statuses:
            self.client.force_login(user)
            for name in ('notes:detail', 'notes:edit', 'notes:delete'):
                with self.subTest(user=user, name=name):
                    url = reverse(name, args=(self.note.slug,))
                    response = self.client.get(url)
                    self.assertEqual(response.status_code, status)

    def test_pages_availability_for_auth_user(self):
        self.client.force_login(self.author)
        for name in ('notes:add', 'notes:success', 'notes:list'):
            with self.subTest(user='author', page=name):
                url = reverse(name)
                response = self.client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_redirect_for_anonymous_client(self):
        login_url = reverse('users:login')
        for name in ('notes:add', 'notes:success', 'notes:list'):
            with self.subTest(name=name):
                url = reverse(name)
                redirect_url = f'{login_url}?next={url}'
                response = self.client.get(url)
                self.assertRedirects(response, redirect_url)
