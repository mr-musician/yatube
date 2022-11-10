import shutil
import tempfile

from django import forms
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from ..models import Group, Post, Follow

User = get_user_model()

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


class ContextTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test_slug',
            description='Тестовое описание группы'
        )
        cls.group_second = Group.objects.create(
            title='Тестовая группа 2',
            slug='test_slug_second',
            description='Тестовое описание группы'
        )
        cls.user = User.objects.create_user(username='HasNoName')
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый текст.',
            group=cls.group
        )

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        cache.clear()

    def test_index_correct_context(self):
        """Шаблон index сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse('posts:index'))
        self.assertEqual(len(response.context['page_obj']), 1)

    def test_group_list_correct_context(self):
        """Шаблон group_list сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse(
                'posts:group_list',
                kwargs={'slug': f'{ContextTest.group.slug}'}
            )
        )
        self.assertEqual(str(response.context['group']),
                         ContextTest.group.title)
        self.assertEqual(len(response.context['page_obj']), 1)

    def test_profile_correct_context(self):
        """Шаблон profile сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse('posts:profile',
                    kwargs={'username': f'{ContextTest.user}'})
        )
        self.assertEqual(response.context['author'], ContextTest.user)
        self.assertEqual(len(response.context['page_obj']), 1)

    def test_post_detail_correct_context(self):
        """Шаблон post_detail сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse(
                'posts:post_detail',
                kwargs={'post_id': f'{int(ContextTest.post.pk)}'}
            )
        )
        expect_answer = {
            response.context['post'].pk: ContextTest.post.pk,
            str(response.context['post']): ContextTest.post.text,
            response.context['user']: ContextTest.post.author
        }
        for obj, answer in expect_answer.items():
            with self.subTest(obj=obj):
                self.assertEqual(obj, answer)

    def test_create_post_correct_context(self):
        """Шаблон create_post сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse('posts:post_create'))
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.models.ModelChoiceField
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_post_edit_correct_context(self):
        """Шаблон post_edit сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse(
                'posts:post_edit',
                kwargs={'post_id': f'{int(ContextTest.post.pk)}'}
            )
        )
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.models.ModelChoiceField
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_new_post_create_correct(self):
        """Правильное отображение нового поста."""
        post_new = Post.objects.create(
            author=ContextTest.user,
            text='Текст',
            group=ContextTest.group_second
        )

        # Пост попал на главную страницу index
        response = self.authorized_client.get(reverse('posts:index'))
        first_obj = response.context['page_obj'][0]
        obj_auth_0 = first_obj.author
        obj_text_0 = first_obj.text
        obj_id = first_obj.pk
        expect_answer = {
            obj_id: post_new.pk,
            str(obj_text_0): post_new.text,
            obj_auth_0: post_new.author
        }
        for obj, answer in expect_answer.items():
            with self.subTest(obj=obj):
                self.assertEqual(obj, answer)

        # Пост попал на страницу группы
        response = self.authorized_client.get(
            reverse(
                'posts:group_list',
                kwargs={'slug': f'{ContextTest.group_second.slug}'}
            )
        )
        first_obj = response.context['page_obj'][0]
        obj_text_0 = first_obj.text
        obj_id = first_obj.pk
        expect_answer = {
            obj_id: post_new.pk,
            str(obj_text_0): post_new.text
        }
        for obj, answer in expect_answer.items():
            with self.subTest(obj=obj):
                self.assertEqual(obj, answer)

        # Пост попал на страницу автора
        response = self.authorized_client.get(
            reverse('posts:profile',
                    kwargs={'username': f'{ContextTest.user}'})
        )
        first_obj = response.context['page_obj'][0]
        obj_text_0 = first_obj.text
        obj_id = first_obj.pk
        expect_answer = {
            obj_id: post_new.pk,
            str(obj_text_0): post_new.text
        }
        for obj, answer in expect_answer.items():
            with self.subTest(obj=obj):
                self.assertEqual(obj, answer)

        # Пост не попал на страницу другой группы
        response = self.authorized_client.get(
            reverse(
                'posts:group_list',
                kwargs={'slug': f'{ContextTest.group.slug}'}
            )
        )
        self.assertFalse('Тестовая группа 2' in str(response.context['group']))


class PaginatorTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test_slug',
            description='Тестовое описание группы'
        )
        cls.user = User.objects.create_user(username='HasNoName')
        for i in range(13):
            Post.objects.create(
                author=cls.user,
                text='Тестовый текст.',
                group=cls.group
            )
        cache.clear()

    def test_paginator_for_pages(self):
        reverse_list = [
            reverse('posts:index'),
            reverse(
                'posts:group_list',
                kwargs={'slug': f'{PaginatorTest.group.slug}'}
            ),
            reverse(
                'posts:profile', kwargs={'username': f'{PaginatorTest.user}'}
            )
        ]
        for element in reverse_list:
            with self.subTest(element=element):
                response = self.client.get(element)
                self.assertEqual(
                    len(response.context.get('page_obj')), settings.PGN_COUNT
                )
                response = self.client.get(element, {'page': 2})
                self.assertEqual(
                    len(response.context.get('page_obj')), 3
                )


class TemplateTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test_slug',
            description='Тестовое описание группы'
        )
        cls.user = User.objects.create_user(username='HasNoName')
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый текст.',
            group=cls.group
        )

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        cache.clear()

    def test_pages_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_pages_names = {
            reverse('posts:index'): 'posts/index.html',
            reverse(
                'posts:group_list',
                kwargs={'slug': f'{TemplateTest.group.slug}'}
            ): 'posts/group_list.html',
            reverse(
                'posts:profile', kwargs={'username': f'{TemplateTest.user}'}
            ): 'posts/profile.html',
            reverse(
                'posts:post_detail',
                kwargs={'post_id': f'{int(TemplateTest.post.pk)}'},
            ): 'posts/post_detail.html',
            reverse('posts:post_create'): 'posts/create_post.html',
            reverse(
                'posts:post_edit',
                kwargs={'post_id': f'{int(TemplateTest.post.pk)}'}
            ): 'posts/create_post.html'
        }
        for reverse_name, template in templates_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class ImageTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test_slug',
            description='Тестовое описание группы'
        )
        cls.user = User.objects.create_user(username='HasNoName')

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        cache.clear()

    def test_post_with_img(self):
        """
        При выводе поста с картинкой - она передаётся в словаре context.
        """
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
        post_new = Post.objects.create(
            author=ImageTest.user,
            text='Текст',
            group=ImageTest.group,
            image=uploaded
        )

        # Пост на index отображается корректно
        response = self.authorized_client.get(reverse('posts:index'))
        first_obj = response.context['page_obj'][0]
        obj_auth_0 = first_obj.author
        obj_text_0 = first_obj.text
        obj_id = first_obj.pk
        obj_img = first_obj.image
        expect_answer = {
            obj_id: post_new.pk,
            str(obj_text_0): post_new.text,
            obj_auth_0: post_new.author,
            obj_img: post_new.image,
        }
        for obj, answer in expect_answer.items():
            with self.subTest(obj=obj):
                self.assertEqual(obj, answer)

        # Пост на странице автора отображается корректно
        response = self.authorized_client.get(
            reverse(
                'posts:profile',
                kwargs={'username': f'{ImageTest.user}'}
            )
        )
        first_obj = response.context['page_obj'][0]
        obj_text_0 = first_obj.text
        obj_id = first_obj.pk
        obj_img = first_obj.image
        expect_answer = {
            obj_id: post_new.pk,
            str(obj_text_0): post_new.text,
            obj_img: post_new.image,
        }
        for obj, answer in expect_answer.items():
            with self.subTest(obj=obj):
                self.assertEqual(obj, answer)

        # Пост на странице группы отображается корректно
        response = self.authorized_client.get(
            reverse(
                'posts:group_list',
                kwargs={'slug': f'{ImageTest.group.slug}'}
            )
        )
        first_obj = response.context['page_obj'][0]
        obj_text_0 = first_obj.text
        obj_id = first_obj.pk
        obj_img = first_obj.image
        expect_answer = {
            obj_id: post_new.pk,
            str(obj_text_0): post_new.text,
            obj_img: post_new.image,
        }
        for obj, answer in expect_answer.items():
            with self.subTest(obj=obj):
                self.assertEqual(obj, answer)

        # Post_detail отображается корректно
        response = self.authorized_client.get(
            reverse(
                'posts:post_detail',
                kwargs={'post_id': f'{int(post_new.pk)}'}
            )
        )
        expect_answer = {
            response.context['post'].pk: post_new.pk,
            str(response.context['post']): post_new.text,
            response.context['user']: post_new.author,
            response.context['post'].image: post_new.image,
        }
        for obj, answer in expect_answer.items():
            with self.subTest(obj=obj):
                self.assertEqual(obj, answer)


class CacheTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='HasNoName')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        cache.clear()

    def test_index_contains_cash(self):
        post_new = Post.objects.create(
            author=self.user,
            text='Текст для теста кеширования.',
        )
        response_with = self.authorized_client.get(reverse('posts:index'))
        self.assertIn(post_new, response_with.context['page_obj'])
        post_new.delete()
        response_without = self.authorized_client.get(reverse('posts:index'))
        self.assertEqual(response_with.content, response_without.content)


class FollowTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test_group',
            description='Тестовое описание группы',
        )
        cls.user = User.objects.create_user(username='HasNoName')
        cls.user_second = User.objects.create_user(username='TestUser')
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый текст.',
            group=cls.group
        )

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        cache.clear()

    def test_profile_follow(self):
        """
        Авторизованный пользователь может подписаться на другого
        пользователя.
        """
        follow_count = Follow.objects.count()
        self.authorized_client.post(
            reverse(
                'posts:profile_follow',
                kwargs={'username': str(FollowTest.user_second)},
            )
        )
        self.assertEqual(Follow.objects.count(), follow_count + 1)
        self.assertTrue(
            Follow.objects.filter(
                user=FollowTest.user, author=FollowTest.user_second
            ).exists()
        )

    def test_profile_unfollow(self):
        """
        Авторизованный пользователь может удалить из подписок другого
        пользователя.
        """
        self.authorized_client.post(
            reverse(
                'posts:profile_follow',
                kwargs={'username': str(FollowTest.user_second)},
            )
        )
        follow_count = Follow.objects.count()
        self.authorized_client.post(
            reverse(
                'posts:profile_unfollow',
                kwargs={'username': str(FollowTest.user_second)},
            )
        )
        self.assertEqual(Follow.objects.count(), follow_count - 1)
        self.assertFalse(
            Follow.objects.filter(
                user=FollowTest.user, author=FollowTest.user_second
            ).exists()
        )

    def test_follow_index(self):
        """
        Новая запись пользователя появляется в ленте тех, кто на него подписан
        и не появляется в ленте тех, кто не подписан.
        """
        new_user = User.objects.create_user(username='TestFollow')
        new_client = Client()
        new_client.force_login(new_user)
        new_client.post(
            reverse(
                'posts:profile_follow',
                kwargs={'username': str(FollowTest.user_second)},
            )
        )
        new_post = Post.objects.create(
            author=FollowTest.user_second,
            text='Текст для теста follow.',
        )
        response = self.authorized_client.get(reverse('posts:follow_index'))
        response_new_user = new_client.get(reverse('posts:follow_index'))
        self.assertIn(
            new_post, response_new_user.context['page_obj'].object_list
        )
        self.assertNotIn(new_post, response.context['page_obj'].object_list)
