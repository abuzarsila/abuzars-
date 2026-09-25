from django.test import TestCase

from .models import Door


class ChatbotViewTests(TestCase):
    def setUp(self):
        Door.objects.create(
            name="Classic 100",
            brand="SF Basic",
            price=1_800_000,
            category="Standart",
            coating="PVC",
            structure="Yog'och karkas",
        )
        Door.objects.create(
            name="Lux 500",
            brand="SF Premium",
            price=3_500_000,
            category="Premium",
            coating="Shpon",
            structure="Metall karkas",
        )

    def test_chatbot_returns_category_recommendations(self):
        response = self.client.get("/chatbot/", {"message": "Premium eshiklar"})

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertIn("Premium kategoriyasida", payload["reply"])
        self.assertIn("Lux 500", payload["reply"])

    def test_chatbot_filters_by_budget(self):
        response = self.client.get("/chatbot/", {"message": "2 mln gacha eshik"})

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertIn("2 000 000 UZS gacha", payload["reply"])
        self.assertIn("Classic 100", payload["reply"])
        self.assertNotIn("Lux 500", payload["reply"])

    def test_chatbot_returns_contact_information(self):
        response = self.client.get("/chatbot/", {"message": "Kontaktlar"})

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertIn("+998 94 637 69 60", payload["reply"])
        self.assertIn("Sebzor 8-uy", payload["reply"])
