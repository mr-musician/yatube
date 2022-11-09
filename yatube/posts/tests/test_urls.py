from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import TestCase, Client
from django.urls import reverse

from ..models import Group, Post

User = get_user_model()


class PostURLTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='HasNoName')
        cls.user_second = User.objects.create_user(username='NonAuthor')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test_group'
        )
        cls.post = Post.objects.create(
            text='Тестовый текст поста',
            author=cls.user,
            group=cls.group
        )

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.non_author_post = Client()
        self.non_author_post.force_login(self.user_second)
        cache.clear()

    def test_urls_uses_access_anonymous(self):
        """Доступность страниц неавторизованным пользователям."""
        code_answer_for_users = {
            '/': HTTPStatus.OK,
            f'/group/{PostURLTest.group.slug}/': HTTPStatus.OK,
            f'/profile/{self.user}/': HTTPStatus.OK,
            f'/posts/{self.post.pk}/': HTTPStatus.OK,
            f'/posts/{self.post.pk}/edit/': HTTPStatus.FOUND,
            '/create/': HTTPStatus.FOUND,
            '/unexisting_page/': HTTPStatus.NOT_FOUND
        }
        for address, code in code_answer_for_users.items():
            with self.subTest(address=address):
                response = self.client.get(address)
                self.assertEqual(response.status_code, code)

    def test_urls_uses_access_authorized(self):
        """Доступность страниц авторизованным пользователям."""
        code_answer_for_users = {
            '/': HTTPStatus.OK,
            f'/group/{PostURLTest.group.slug}/': HTTPStatus.OK,
            f'/profile/{self.user}/': HTTPStatus.OK,
            f'/posts/{self.post.pk}/': HTTPStatus.OK,
            f'/posts/{self.post.pk}/edit/': HTTPStatus.OK,
            '/create/': HTTPStatus.OK,
            '/unexisting_page/': HTTPStatus.NOT_FOUND
        }
        for address, code in code_answer_for_users.items():
            with self.subTest(address=address):
                response = self.authorized_client.get(address)
                self.assertEqual(response.status_code, code)

    def test_urls_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_url_names = {
            '/': 'posts/index.html',
            f'/group/{PostURLTest.group.slug}/': 'posts/group_list.html',
            f'/profile/{self.user}/': 'posts/profile.html',
            f'/posts/{self.post.pk}/': 'posts/post_detail.html',
            f'/posts/{self.post.pk}/edit/': 'posts/create_post.html',
            '/create/': 'posts/create_post.html'
        }
        for address, template in templates_url_names.items():
            with self.subTest(address=address):
                response = self.authorized_client.get(address)
                self.assertTemplateUsed(response, template)

    def test_authorized_cannot_edit(self):
        """Авторизованный пользователь не может отредактировать чужой пост."""
        response = self.non_author_post.get(
            reverse(
                'posts:post_edit',
                kwargs={'post_id': self.post.pk}
            ),
            follow=True
        )
        self.assertRedirects(
            response,
            reverse(
                'posts:post_detail',
                kwargs={'post_id': self.post.pk}), HTTPStatus.FOUND
        )

    def test_error_page(self):
        response = self.client.get('/unexisting_page/')
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
        self.assertTemplateUsed(response, 'core/404.html')
