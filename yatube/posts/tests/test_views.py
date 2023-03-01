from django.core.cache import cache
from django.test import TestCase, Client
from django.urls import reverse
from django import forms
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db.models.fields.files import ImageFieldFile

from http import HTTPStatus

from posts.models import Post, Group, User, Comment, Follow
from yatube.settings import NUM_OF_POSTS
from .variables import (NUMBER_OF_TEST_POSTS, TEST_GROUP_TITLE,
                        TEST_GROUP_SLUG, TEST_GROUP_DESCRIPTION,
                        TEST_POST_TEXT, TEST_AUTHOR_USERNAME,
                        TEST_IMAGE, TEST_COMMENT,)


class PostViewsTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create_user(username=TEST_AUTHOR_USERNAME)
        cls.group = Group.objects.create(
            title=TEST_GROUP_TITLE,
            slug=TEST_GROUP_SLUG,
            description=TEST_GROUP_DESCRIPTION,
        )
        uploaded = SimpleUploadedFile(
            name='test.gif',
            content=TEST_IMAGE,
            content_type='image/gif'
        )
        cls.post = Post.objects.create(
            text=TEST_POST_TEXT,
            author=cls.author,
            group=cls.group,
            image=uploaded,
        )
        cls.comment = Comment.objects.create(
            post=cls.post,
            author=cls.author,
            text=TEST_COMMENT
        )
        cls.comment_form_data = {
            'text': TEST_COMMENT,
        }
        cls.templates_urls = {
            'posts/index.html': reverse('posts:index'),
            'posts/profile.html': reverse(
                'posts:profile', kwargs={'username': cls.author.username}
            ),
            'posts/group_list.html': reverse(
                'posts:group_list', kwargs={'slug': cls.group.slug}
            ),
            'posts/post_detail.html': reverse(
                'posts:post_detail', kwargs={'post_id': cls.post.pk}
            ),
            'posts/create_post.html': reverse('posts:post_create'),
        }
        cls.form_urls = (
            (reverse('posts:post_create'), 'text', forms.fields.CharField),
            (reverse('posts:post_create'), 'group', forms.fields.ChoiceField),
            (reverse('posts:post_create'), 'image', forms.fields.ImageField),
            (reverse('posts:post_edit', kwargs={'post_id': cls.post.pk}),
             'text', forms.fields.CharField),
            (reverse('posts:post_edit', kwargs={'post_id': cls.post.pk}),
             'group', forms.fields.ChoiceField),
            (reverse('posts:post_edit', kwargs={'post_id': cls.post.pk}),
             'image', forms.fields.ImageField),
        )

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.author)

    def test_uses_correct_template(self):
        """Проверка соответствия шаблонов"""
        for template, reverse_name in self.templates_urls.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_home_page_profile_show_correct_context(self):
        """Шаблон главной страницы, profile сформирован с правильным
          контекстом."""
        patterns = (
            reverse('posts:index'),
            reverse(
                'posts:profile', kwargs={'username': self.author},
            ),)
        for pattern in patterns:
            with self.subTest(reverse_name=pattern):
                response = self.authorized_client.get(pattern)
                post_text = response.context.get('page_obj')[0].text
                post_author = response.context.get(
                    'page_obj')[0].author.username
                group_post = response.context.get('page_obj')[0].group.title
                self.assertEqual(post_text, TEST_POST_TEXT)
                self.assertEqual(post_author, TEST_AUTHOR_USERNAME)
                self.assertEqual(group_post, TEST_GROUP_TITLE)

    def test_post_detail_pages_show_correct_context(self):
        """Шаблон post_detail сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse(
            'posts:post_detail', kwargs={'post_id': self.post.pk}
        ))
        post_text = response.context.get('post').text
        post_author = response.context.get('post').author.username
        group_post = response.context.get('post').group.title
        self.assertEqual(post_text, TEST_POST_TEXT)
        self.assertEqual(post_author, TEST_AUTHOR_USERNAME)
        self.assertEqual(group_post, TEST_GROUP_TITLE)

    def test_group_list_page_show_correct_context(self):
        """Шаблон group_list сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse(
            'posts:group_list', kwargs={'slug': self.group.slug}
        ))
        group_title = response.context.get('group').title
        group_description = response.context.get('group').description
        group_slug = response.context.get('group').slug
        self.assertEqual(group_title, TEST_GROUP_TITLE)
        self.assertEqual(group_description, TEST_GROUP_DESCRIPTION)
        self.assertEqual(group_slug, TEST_GROUP_SLUG)

    def test_posts_form_correct_context(self):
        """Проверка контекста для форм."""
        for reverse_name, context_name, type_field in self.form_urls:
            with self.subTest(value=context_name):
                response = self.authorized_client.get(reverse_name)
                form_field = response.context.get(
                    'form').fields.get(context_name)
                self.assertIsInstance(form_field, type_field)

    def test_views_correct_context_image(self):
        """Проверяем что картинка передается с контекстом."""
        image_url = {
            reverse('posts:index'),
            reverse('posts:profile',
                    kwargs={'username': self.author}),
            reverse('posts:group_list',
                    kwargs={'slug': self.group.slug})
        }
        for url in image_url:
            with self.subTest(path=url):
                response = self.authorized_client.get(url)
                self.assertIsInstance(
                    response.context['page_obj'][0].image, ImageFieldFile
                )
        response = self.authorized_client.get(reverse(
            'posts:post_detail',
            kwargs={'post_id': self.post.id}))
        self.assertIsInstance(
            response.context['post'].image, ImageFieldFile
        )

    def test_views_auth_comment_creation(self):
        """Проверяем что комментировать посты может только авторизированный
        пользователь."""
        comments_count = Comment.objects.count()
        response = self.guest_client.post(
            reverse(
                'posts:add_comment', kwargs={'post_id': self.post.id},
            ),
            data=self.comment_form_data,
            follow=True
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual(comments_count, Comment.objects.count())

    def test_views_index_cache(self):
        """Проверяем работу кэша на главной странице."""
        response = self.guest_client.get(reverse('posts:index'))
        new_post = Post.objects.create(
            text=TEST_POST_TEXT,
            author=self.author,
        )
        cache.set('index_page', response.content)
        self.assertEqual(response.content, cache.get('index_page'))
        new_post.delete()
        self.assertEqual(response.content, cache.get('index_page'))
        cache.clear()
        self.assertNotEqual(response.content, cache.get('index_page'))


class PaginatorViewsTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create_user(username=TEST_AUTHOR_USERNAME)
        cls.group = Group.objects.create(
            title=TEST_GROUP_TITLE,
            slug=TEST_GROUP_SLUG,
        )
        for text_num in range(NUMBER_OF_TEST_POSTS):
            cls.post = Post.objects.create(
                text=f'{TEST_POST_TEXT} {text_num+1}',
                author=cls.author,
                group=cls.group,
            )
        cls.first_pages = (
            (reverse('posts:group_list', kwargs={'slug': cls.group.slug})),
            (reverse('posts:profile', kwargs={
             'username': cls.author.username})),
        )
        cls.second_pages = (
            (reverse('posts:group_list', kwargs={
             'slug': cls.group.slug}) + '?page=2'),
            (reverse('posts:profile', kwargs={
             'username': cls.author.username}) + '?page=2'),
        )

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.author)

    def test_paginator_in_pages(self):
        """Тест паджинатора на страницах"""
        for page in self.first_pages:
            with self.subTest(reverse_name=page):
                response = self.authorized_client.get(page)
                self.assertEqual(
                    len(response.context['page_obj']), NUM_OF_POSTS)
        for page in self.second_pages:
            with self.subTest(reverse_name=page):
                response = self.authorized_client.get(page)
                self.assertEqual(
                    len(response.context['page_obj']), NUMBER_OF_TEST_POSTS
                    - NUM_OF_POSTS)


class PostViewsFollowTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create_user(username=TEST_AUTHOR_USERNAME)
        cls.author_1 = User.objects.create_user(
            username=TEST_AUTHOR_USERNAME + "1")

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.author)
        self.authorized_client_1 = Client()
        self.authorized_client_1.force_login(self.author_1)

    def test_authorized_user_follow_unfollow(self):
        """Авторизованный пользователь может подписываться и
        отписываться от других авторов"""
        self.authorized_client.get(
            reverse('posts:profile_follow',
                    kwargs={'username': self.author_1.username})
        )
        self.assertTrue(
            Follow.objects.filter(user=self.author,
                                  author=self.author_1).exists()
        )
        self.authorized_client.get(
            reverse('posts:profile_unfollow',
                    kwargs={'username': self.author_1.username})
        )
        self.assertFalse(
            Follow.objects.filter(user=self.author,
                                  author=self.author_1).exists()
        )

    def test_new_entry_in_feed_of_subscribed_users(self):
        """Новая запись появляется в ленте подписанных пользователей"""
        self.authorized_client.get(
            reverse('posts:profile_follow',
                    kwargs={'username': self.author_1.username})
        )
        subscribed_1 = Follow.objects.values_list(
            'author').filter(user=self.author)
        post_list_1 = Post.objects.filter(author__in=subscribed_1)
        post = Post.objects.create(author=self.author_1,
                                   text=TEST_POST_TEXT,)
        self.assertIn(post, post_list_1)
        authors_2 = Follow.objects.values_list(
            'author').filter(user=self.author_1)
        post_list_2 = Post.objects.filter(author__in=authors_2)
        self.assertNotIn(post, post_list_2)
