from django.test import TestCase, Client

from http import HTTPStatus

from posts.models import Post, Group, User

from .variables import (TEST_AUTH_USER, TEST_AUTHOR_USERNAME,
                        TEST_POST_TEXT, TEST_GROUP_TITLE,
                        TEST_GROUP_SLUG, TEST_GROUP_DESCRIPTION)


class PostURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.auth = User.objects.create_user(username=TEST_AUTH_USER)
        cls.author = User.objects.create_user(username=TEST_AUTHOR_USERNAME)
        cls.post = Post.objects.create(
            text=TEST_POST_TEXT,
            author=cls.author,
        )
        cls.group = Group.objects.create(
            title=TEST_GROUP_TITLE,
            slug=TEST_GROUP_SLUG,
            description=TEST_GROUP_DESCRIPTION,
        )
        cls.templates_url = {
            '/': 'posts/index.html',
            '/group/TestSlug/': 'posts/group_list.html',
            '/profile/TestAuthor/': 'posts/profile.html',
            f'/posts/{cls.post.pk}/': 'posts/post_detail.html',
            f'/posts/{cls.post.pk}/edit/': 'posts/create_post.html',
            '/create/': 'posts/create_post.html',
        }
        cls.urls = (
            "/",
            f"/group/{cls.group.slug}/",
            f"/profile/{cls.author.username}/",
            f"/posts/{cls.post.pk}/",
        )
        cls.authorized_urls = (
            "/",
            f"/group/{cls.group.slug}/",
            f"/profile/{cls.author.username}/",
            f"/posts/{cls.post.pk}/",
            f"/posts/{cls.post.pk}/edit/",
            "/create/",
        )

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client_not_author = Client()
        self.authorized_client_not_author.force_login(self.auth)
        self.authorized_client = Client()
        self.authorized_client.force_login(self.author)

    def test_page_404(self):
        """Несуществующая страница"""
        response = self.guest_client.get('/404/')
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

    def test_guest_urls(self):
        """Общедоступные страницы."""
        for url in self.urls:
            with self.subTest(address=url):
                response = self.guest_client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_create_redirect_guest_to_login(self):
        """Страница /create/ перенаправляет неавторизированного пользователя
        на страницу ввода логина."""
        response = self.guest_client.get('/create/', follow=True)
        self.assertRedirects(
            response, '/auth/login/?next=/create/')

    def test_post_edit_redirect_guest_to_login(self):
        """Страница /posts/id/edit/ перенаправляет неавторизированного
         пользователя на страницу ввода логина."""
        response = self.guest_client.get(
            f'/posts/{self.post.pk}/edit/', follow=True
        )
        self.assertRedirects(
            response, (f'/auth/login/?next=/posts/{self.post.pk}/edit/')
        )

    def test_auth_urls(self):
        """Страницы для авторизованного пользователя."""
        for url in self.authorized_urls:
            with self.subTest(address=url):
                response = self.authorized_client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_redirect_not_author(self):
        """Перенаправление при попытке редактировании поста не авром"""
        response = self.authorized_client_not_author.get(
            f"/posts/{self.post.pk}/edit/", follow=True
        )
        self.assertRedirects(response, f"/posts/{self.post.pk}/")

    def test_urls_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        for url, template in self.templates_url.items():
            with self.subTest(url=url):
                response = self.authorized_client.get(url)
                self.assertTemplateUsed(response, template)
