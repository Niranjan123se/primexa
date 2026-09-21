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


class VendorAndOEMApprovalTests(TestCase):
    def setUp(self):
        from users.models import OEMProfile, VendorProfile
        self.engineer = User.objects.create_user(
            username="eng1",
            password="safe-password",
            role="ENGINEER",
            company_name="Primexa Internal",
            phone_number="1111111111",
        )
        self.vendor_user = User.objects.create_user(
            username="vuser",
            password="safe-password",
            role="VENDOR",
            company_name="Acme Precision Corp",
            phone_number="2222222222",
        )
        self.vendor_profile = VendorProfile.objects.create(user=self.vendor_user)

        self.oem_user = User.objects.create_user(
            username="oemuser",
            password="safe-password",
            role="OEM",
            company_name="Apex Motors Ltd",
            phone_number="3333333333",
        )
        self.oem_profile = OEMProfile.objects.create(user=self.oem_user)

    def test_slug_generation_from_company_name(self):
        self.assertEqual(self.vendor_profile.public_slug, "acme-precision-corp")
        self.assertEqual(self.oem_profile.slug, "apex-motors-ltd")

    def test_engineer_can_approve_vendor_by_business_slug(self):
        self.client.force_login(self.engineer)
        url = reverse("approve_vendor", kwargs={"company_slug": self.vendor_profile.public_slug})
        self.assertEqual(url, "/exchange/engineer/approve-vendor/acme-precision-corp/")
        response = self.client.get(url)
        self.assertRedirects(response, reverse("engineer_dashboard"))

        self.vendor_profile.refresh_from_db()
        self.assertTrue(self.vendor_profile.is_verified)
        self.assertTrue(self.vendor_profile.is_public_profile_approved)

    def test_engineer_can_approve_oem_by_business_slug(self):
        self.client.force_login(self.engineer)
        url = reverse("approve_oem", kwargs={"company_slug": self.oem_profile.slug})
        self.assertEqual(url, "/exchange/engineer/approve-oem/apex-motors-ltd/")
        response = self.client.get(url)
        self.assertRedirects(response, reverse("engineer_dashboard"))

        self.oem_profile.refresh_from_db()
        self.assertTrue(self.oem_profile.is_verified)
        self.assertTrue(self.oem_profile.is_approved)

    def test_unapproved_vendor_profile_accessible_by_engineer_and_owner_not_public(self):
        url = reverse("public_vendor_profile", kwargs={"slug": self.vendor_profile.public_slug})
        # Anonymous public user gets 404 for unapproved profile
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

        # Engineer staff gets 200 preview
        self.client.force_login(self.engineer)
        response_eng = self.client.get(url)
        self.assertEqual(response_eng.status_code, 200)

        # Profile owner gets 200 preview
        self.client.force_login(self.vendor_user)
        response_owner = self.client.get(url)
        self.assertEqual(response_owner.status_code, 200)
