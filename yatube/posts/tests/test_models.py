from django.contrib.auth import get_user_model
from django.test import TestCase

from ..models import Group, Post

User = get_user_model()


class PostModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='Тестовый слаг',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='0' * 20,
        )

    def test_models_have_correct_object_names(self):
        """Проверяем, что у моделей корректно работает __str__."""
        post = PostModelTest.post
        expected_object_name_post = post.text[:15]
        self.assertEqual(expected_object_name_post, str(post))
        group = PostModelTest.group
        expected_object_name_group = group.title
        self.assertEqual(expected_object_name_group, str(group))

    def test_post_verbose_name(self):
        """verbose_name в модели Post совпадает."""
        post = PostModelTest.post
        verbose_fields = {
            'text': 'Текст поста',
            'created': 'Дата создания',
            'author': 'Автор',
            'group': 'Группа'
        }

        for value, expected in verbose_fields.items():
            self.assertEqual(
                post._meta.get_field(value).verbose_name,
                expected)

    def test_post_help_text(self):
        """help_text в модели Post совпадает."""
        post = PostModelTest.post
        help_text_fields = {
            'text': 'Текст нового поста',
            'group': 'Группа, к которой будет относиться пост'
        }

        for value, expected in help_text_fields.items():
            self.assertEqual(
                post._meta.get_field(value).help_text,
                expected)
