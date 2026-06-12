from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from pytils.translit import slugify

from notes.forms import WARNING
from notes.models import Note

User = get_user_model()

form_data = {
    'title': 'Новый заголовок',
    'text': 'Новый текст',
    'slug': 'new-slug',
}


class TestNoteActions(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.author = User.objects.create(username='Автор')
        cls.reader = User.objects.create(username='Читатетль')

    def setUp(self):
        self.client.force_login(self.author)

    def test_auth_user_can_create_note(self):
        url = reverse('notes:add')
        response = self.client.post(url, data=form_data)
        self.assertRedirects(response, reverse('notes:success'))
        notes_count = Note.objects.count()
        self.assertEqual(notes_count, 1)
        new_note = Note.objects.get()
        self.assertEqual(new_note.title, form_data['title'])
        self.assertEqual(new_note.slug, form_data['slug'])
        self.assertEqual(new_note.text, form_data['text'])

    def test_anonymous_user_cant_create_note(self):
        self.client.logout()
        url = reverse('notes:add')
        response = self.client.post(url, data=form_data)
        login_url = reverse('users:login')
        expected_url = f'{login_url}?next={url}'
        self.assertRedirects(response, expected_url)
        notes_count = Note.objects.count()
        self.assertEqual(notes_count, 0)

    # def test_author_can_edit_note(self):
    #     note = Note.objects.create(
    #         title='Другая заметка',
    #         text='Текст',
    #         slug='existing-slug',
    #         author=self.author
    #     )
    #     url = reverse('notes:edit', args=(note.slug,))
    #     response = self.client.post(url, data=form_data)
    #     self.assertRedirects(response, reverse('notes:success'))
    #     note.refresh_from_db()
    #     self.assertEqual(note.title, form_data['title'])
    #     self.assertEqual(note.text, form_data['text'])
    #     self.assertEqual(note.slug, form_data['slug'])

    def test_edit_note_permissions(self):

        note = Note.objects.create(
            title='Другая заметка',
            text='Текст',
            slug='existing-slug',
            author=self.author
        )

        original_data = {
            'title': note.title,
            'text': note.text,
            'slug': note.slug,
        }

        test_cases = [
            (self.author, HTTPStatus.FOUND, True),
            (self.reader, HTTPStatus.NOT_FOUND, False),
        ]

        for user, expected_status, should_change in test_cases:
            with self.subTest(user=user.username):
                self.client.force_login(user)
                url = reverse('notes:edit', args=(note.slug,))
                response = self.client.post(url, data=form_data)
                self.assertEqual(response.status_code, expected_status)
                note.refresh_from_db()

                if should_change:
                    self.assertRedirects(response, reverse('notes:success'))
                    self.assertEqual(note.title, form_data['title'])
                    self.assertEqual(note.text, form_data['text'])
                    self.assertEqual(note.slug, form_data['slug'])
                else:
                    self.assertEqual(note.title, original_data['title'])
                    self.assertEqual(note.text, original_data['text'])
                    self.assertEqual(note.slug, original_data['slug'])

                note.title = original_data['title']
                note.text = original_data['text']
                note.slug = original_data['slug']
                note.save()
                self.client.logout()

    def test_delete_note_permissions(self):

        note = Note.objects.create(
            title='Другая заметка',
            text='Текст',
            slug='existing-slug',
            author=self.author
        )

        original_data = {
            'title': note.title,
            'text': note.text,
            'slug': note.slug,
        }

        test_cases = [
            (self.author, HTTPStatus.FOUND, True),
            (self.reader, HTTPStatus.NOT_FOUND, False),
        ]

        for user, expected_status, should_change in test_cases:
            with self.subTest(user=user.username):
                self.client.force_login(user)
                url = reverse('notes:delete', args=(note.slug,))
                response = self.client.post(url)

                self.assertEqual(response.status_code, expected_status)

                if should_change:
                    self.assertRedirects(response, reverse('notes:success'))
                    with self.assertRaises(Note.DoesNotExist):
                        Note.objects.get(id=note.id)
                        self.assertEqual(Note.objects.count(), 0)
                else:
                    note_from_db = Note.objects.get(id=note.id)
                    self.assertEqual(note_from_db.title,
                                     original_data['title'])
                    self.assertEqual(note_from_db.text, original_data['text'])
                    self.assertEqual(note_from_db.slug, original_data['slug'])
                    self.assertEqual(Note.objects.count(), 1)

                note.title = original_data['title']
                note.text = original_data['text']
                note.slug = original_data['slug']
                note.save()
                self.client.logout()


class TestSlugLogic(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.author = User.objects.create(username='Автор')

    def setUp(self):
        self.client.force_login(self.author)

    def test_not_unique_slug(self):
        note = Note.objects.create(
            title='Первая заметка',
            text='Текст',
            slug='existing-slug',
            author=self.author
        )
        form_data['slug'] = note.slug
        url = reverse('notes:add')
        response = self.client.post(url, data=form_data)
        self.assertFormError(response.context['form'], 'slug',
                             errors=(note.slug + WARNING))
        self.assertEqual(Note.objects.count(), 1)

    def test_empty_slug(self):
        form_data.pop('slug')
        url = reverse('notes:add')
        response = self.client.post(url, data=form_data)
        self.assertRedirects(response, reverse('notes:success'))
        self.assertEqual(Note.objects.count(), 1)
        new_note = Note.objects.get()
        expected_slug = slugify(form_data['title'])
        self.assertEqual(new_note.slug, expected_slug)
