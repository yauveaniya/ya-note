from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from notes.forms import NoteForm
from notes.models import Note

User = get_user_model()


class TestContent(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.author = User.objects.create(username='Василий')
        cls.reader = User.objects.create(username='Читатель простой')
        cls.note = Note.objects.create(title='Заголовок', text='Текст',
                                       author=cls.author)

    def test_notes_list_for_different_users(self):
        notes = ((self.author, self.note, True),
                 (self.reader, self.note, False))
        for user, note, is_in_list in notes:
            self.client.force_login(user)
            with self.subTest(user=user, note=note):
                url = reverse('notes:list')
                response = self.client.get(url)
                object_list = response.context['object_list']
                assert (note in object_list) is is_in_list

    def test_notes_contain_form(self):
        self.client.force_login(self.author)
        urls = [
            ('notes:edit', (self.note.slug,)),
            ('notes:add', None),
        ]
        for name, args in urls:
            with self.subTest(name=name):
                if args:
                    url = reverse(name, args=args)
                else:
                    url = reverse(name)

            response = self.client.get(url)
            assert 'form' in response.context
            assert isinstance(response.context['form'], NoteForm)
