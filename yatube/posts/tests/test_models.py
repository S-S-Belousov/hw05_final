from django.test import TestCase

from posts.models import Group, Post, User
from .variables import (TEST_POST_TEXT, TEST_AUTHOR_USERNAME,
                        TEST_GROUP_TITLE, TEST_GROUP_SLUG,
                        TEST_GROUP_DESCRIPTION)


class PostModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.test_post_text = TEST_POST_TEXT + " " + TEST_POST_TEXT
        cls.user = User.objects.create_user(username=TEST_AUTHOR_USERNAME)
        cls.group = Group.objects.create(
            title=TEST_GROUP_TITLE,
            slug=TEST_GROUP_SLUG,
            description=TEST_GROUP_DESCRIPTION,
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text=cls.test_post_text,
        )

    def test_models_have_correct_object_names(self):
        """Проверяем, что у моделей корректно работает __str__."""
        post = PostModelTest.post
        self.assertEqual(post.text[:15], str(post))


class GroupModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.group = Group.objects.create(
            title=TEST_GROUP_TITLE,
            slug=TEST_GROUP_SLUG,
            description=TEST_GROUP_DESCRIPTION,
        )

    def test_models_have_correct_object_names(self):
        """Проверяем, что у моделей группы корректно работает __str__."""
        group = GroupModelTest.group
        self.assertEqual(group.title, str(group))
