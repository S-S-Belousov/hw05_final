from django.test import Client, TestCase
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile

from posts.models import Group, Post, User, Comment
from .variables import (TEST_GROUP_SLUG,
                        TEST_POST_TEXT, TEST_EDITED_POST_TEXT,
                        TEST_AUTHOR_USERNAME, TEST_IMAGE, TEST_COMMENT,
                        TEST_HEADING,)


class PostFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create_user(username=TEST_AUTHOR_USERNAME,)
        cls.group = Group.objects.create(slug=TEST_GROUP_SLUG,)
        uploaded = SimpleUploadedFile(
            name='test.gif',
            content=TEST_IMAGE,
            content_type='image/gif'
        )
        cls.post = Post.objects.create(
            text=TEST_POST_TEXT,
            author=cls.author,
            group=cls.group,
        )
        cls.form_data = {
            'heading': TEST_HEADING,
            'text': TEST_POST_TEXT + "1",
            'group': cls.group,
            'author': cls.author,
            'image': uploaded,
        }
        cls.comment_form_data = {
            'text': TEST_COMMENT,
        }
        cls.edited_form_data = {
            'heading': TEST_HEADING,
            'text': TEST_EDITED_POST_TEXT,
            'group': cls.group.pk,
        }

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.author)

    def test_create_post_form(self):
        """Валидная форма создает запись в Posts"""
        posts_count = Post.objects.count()
        self.authorized_client.post(
            reverse('posts:post_create'),
            data=self.form_data,
            follow=True
        )
        self.assertEqual(Post.objects.count(), posts_count + 1)
        self.assertTrue(
            Post.objects.filter(
                text=TEST_POST_TEXT + "1",).exists())

    def test_views_comment_add(self):
        """Проверяем что после успешной отправки комментарий появляется на
        странице поста."""
        comments_count = Comment.objects.count()
        self.authorized_client.post(
            reverse(
                'posts:add_comment', kwargs={'post_id': self.post.pk},
            ),
            data=self.comment_form_data,
            follow=True
        )
        self.assertEqual(comments_count + 1, Comment.objects.count())
        self.assertTrue(
            Comment.objects.filter(
                text=TEST_COMMENT,).exists())

    def test_author_edit_post(self):
        """Валидная форма изменяет запись в Posts."""
        post = Post.objects.get(id=self.post.pk)
        self.authorized_client.get(f'/posts/{post.pk}/edit/')
        posts_count = Post.objects.count()
        self.authorized_client.post(
            reverse('posts:post_edit', kwargs={'post_id': self.post.pk}),
            data=self.edited_form_data,
            follow=True
        )
        post_edit = Post.objects.get(id=self.post.pk)
        self.assertEqual(post_edit.text, TEST_EDITED_POST_TEXT)
        self.assertEqual(Post.objects.count(), posts_count)
