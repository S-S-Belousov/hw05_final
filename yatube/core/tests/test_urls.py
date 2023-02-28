from django.test import TestCase, Client

from http import HTTPStatus


class PostViewsTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

    def setUp(self):
        self.guest_client = Client()

    def test_404_correct_template(self):
        """Проверка соответствия шаблона страницы 404"""
        response = self.guest_client.get('/page_not_found/')
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND,)
        self.assertTemplateUsed(response, 'core/404.html')
