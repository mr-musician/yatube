import tempfile
import shutil

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from ..models import Group, Post, Comment

User = get_user_model()

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostCreateFormTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='HasNoName')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test_slug',
            description='Тестовое описание группы',
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_create_post_without_group(self):
        """Валидная форма создает запись в Post."""
        post_count = Post.objects.count()
        form_data = {
            'text': 'Тестовый текст'
        }
        response = self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        self.assertRedirects(
            response,
            reverse('posts:profile', kwargs={'username': self.user})
        )
        self.assertEqual(Post.objects.count(), post_count + 1)
        last_post = Post.objects.first()
        expect_answer = {
            last_post.text: form_data['text'],
            last_post.author.username: self.user.username
        }
        for obj, answer in expect_answer.items():
            with self.subTest(obj=obj):
                self.assertEqual(obj, answer)

    def test_create_post_with_group(self):
        """Валидная форма создает запись в Post."""
        post_count = Post.objects.count()
        form_data = {
            'text': 'Тестовый текст',
            'group': self.group.pk
        }
        response = self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        self.assertRedirects(
            response,
            reverse('posts:profile', kwargs={'username': self.user})
        )
        self.assertEqual(Post.objects.count(), post_count + 1)
        last_post = Post.objects.first()
        expect_answer = {
            last_post.text: form_data['text'],
            last_post.group.pk: form_data['group'],
            last_post.author.username: self.user.username
        }
        for obj, answer in expect_answer.items():
            with self.subTest(obj=obj):
                self.assertEqual(obj, answer)

    def test_edit_post(self):
        """Валидная форма изменяет запись в Post."""
        post_test = Post.objects.create(
            author=self.user,
            text='Тестовый текст',
            group=self.group
        )
        form_data = {
            'text': 'Тестовый текст правка',
            'group': post_test.group.pk
        }
        response = self.authorized_client.post(
            reverse(
                'posts:post_edit',
                kwargs={'post_id': post_test.pk},
            ),
            data=form_data,
            follow=True
        )
        self.assertRedirects(
            response,
            reverse('posts:post_detail', kwargs={'post_id': post_test.pk})
        )
        post_change = Post.objects.get(id=post_test.pk)
        expect_answer = {
            post_test.pk: post_change.pk,
            form_data['text']: post_change.text,
            form_data['group']: post_change.group.pk,
        }
        for obj, answer in expect_answer.items():
            with self.subTest(obj=obj):
                self.assertEqual(obj, answer)

    def test_anonymous_create_post(self):
        """Валидная форма не создает запись в Post от гостя."""
        post_count = Post.objects.count()
        form_data = {
            'text': 'Тестовый текст 2',
            'group': self.group.pk,
        }
        response = self.client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        self.assertEqual(Post.objects.count(), post_count)
        self.assertRedirects(response, '/auth/login/?next=/create/')

    def test_create_post_with_img(self):
        """Валидная форма создает запись в Post c img"""
        post_count = Post.objects.count()
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )
        form_data = {
            'text': 'Тестовый текст',
            'image': uploaded,
        }
        response = self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        self.assertRedirects(
            response,
            reverse(
                'posts:profile', kwargs={'username': PostCreateFormTest.user}
            )
        )
        self.assertEqual(Post.objects.count(), post_count + 1)
        last_post = Post.objects.first()
        expect_answer = {
            last_post.text: form_data['text'],
            str(last_post.image): str(last_post.image),
        }
        for obj, answer in expect_answer.items():
            with self.subTest(obj=obj):
                self.assertEqual(obj, answer)


class CommentCreateFormTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='HasNoName')

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_create_comment_auth(self):
        """Валидная форма создает комментарий."""
        post = Post.objects.create(
            author=CommentCreateFormTest.user,
            text='Текст'
        )
        comments_count = Comment.objects.count()
        form_data = {
            'text': 'Тестовый комментарий',
        }
        response = self.authorized_client.post(
            reverse('posts:add_comment', kwargs={'post_id': post.pk}),
            data=form_data,
            follow=True
        )
        self.assertRedirects(
            response,
            reverse('posts:post_detail', kwargs={'post_id': post.pk})
        )
        self.assertEqual(Comment.objects.count(), comments_count + 1)
        last_comment = Comment.objects.first()
        self.assertEqual(last_comment.text, form_data['text'])
        response = self.authorized_client.get(
            reverse('posts:post_detail', kwargs={'post_id': post.pk}),
        )
        self.assertEqual(response.context['comments'][0].text,
                         form_data['text'])

    def test_create_comment_guest(self):
        """Неавторизованный пользователь не может оставлять комментарии."""
        post_new = Post.objects.create(
            author=CommentCreateFormTest.user,
            text='Текст'
        )
        comments_count = Comment.objects.count()
        form_data = {
            'text': 'Тестовый комментарий'
        }
        self.client.post(
            reverse('posts:add_comment', kwargs={'post_id': post_new.pk}),
            data=form_data,
            follow=True
        )
        self.assertEqual(Comment.objects.count(), comments_count)
