from django.test import TestCase
from django.urls import reverse

from .models import ExpertProfile, LoginActivity, ServiceRequest, User


class LoginActivityTests(TestCase):
    def test_successful_login_records_user_time_and_ip(self):
        user = User.objects.create_user(
            username="audit-user",
            password="safe-test-password",
            company_name="Primexa Test",
            phone_number="9999999999",
        )

        response = self.client.post(
            reverse("login"),
            {"username": user.username, "password": "safe-test-password"},
            REMOTE_ADDR="203.0.113.45",
        )

        self.assertEqual(response.status_code, 302)
        activity = LoginActivity.objects.get(user=user)
        self.assertEqual(activity.ip_address, "203.0.113.45")
        self.assertIsNotNone(activity.logged_in_at)


class ExpertAndServiceRequestTests(TestCase):
    def test_expert_dashboard_and_profile_are_available_to_experts(self):
        expert = User.objects.create_user(
            username="manufacturing-expert",
            password="safe-test-password",
            role="EXPERT",
            company_name="Independent",
            phone_number="9999999999",
        )
        ExpertProfile.objects.create(user=expert, expertise="CNC machining")
        self.client.force_login(expert)

        response = self.client.get(reverse("dashboard"))
        self.assertRedirects(response, reverse("expert_dashboard"))
        self.assertEqual(self.client.get(reverse("expert_dashboard")).status_code, 200)
        self.assertEqual(self.client.get(reverse("profile")).status_code, 200)

    def test_service_request_can_be_submitted_without_an_account(self):
        response = self.client.post(
            reverse("request_service"),
            {
                "request_type": "FIND_VENDOR",
                "project_title": "Precision bracket",
                "task_description": "Need a machining partner.",
                "contact_name": "Asha Kumar",
                "contact_email": "asha@example.com",
            },
        )

        self.assertEqual(response.status_code, 200)
        request = ServiceRequest.objects.get(project_title="Precision bracket")
        self.assertIsNone(request.submitted_by)
        self.assertEqual(request.status, "NEW")
