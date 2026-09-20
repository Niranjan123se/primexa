from django.test import TestCase
from django.urls import reverse

from users.models import User, VendorProfile

from .models import VendorMachine, VendorMaterial, VendorProcessCapability


class PublicVendorProfileTests(TestCase):
    def setUp(self):
        self.vendor = User.objects.create_user(
            username="public-vendor",
            password="test-password",
            role="VENDOR",
            company_name="Public Precision Engineering",
            phone_number="9999999999",
        )
        self.profile = VendorProfile.objects.create(
            user=self.vendor,
            public_slug="public-precision-engineering",
            public_description="Precision milling and turning.",
            city="Pune",
            gst_number="PRIVATE-GSTIN-123",
            is_public_profile=True,
            is_public_profile_approved=True,
        )
        VendorMaterial.objects.create(
            profile=self.profile,
            material_type="ALUMINIUM",
        )

    def test_approved_profile_is_publicly_available(self):
        response = self.client.get(
            reverse("public_vendor_profile", args=[self.profile.public_slug])
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Public Precision Engineering")
        self.assertContains(response, "Aluminium")
        self.assertNotContains(response, "PRIVATE-GSTIN-123")

    def test_public_home_offers_vendor_and_capability_search(self):
        response = self.client.get(reverse("public_home"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Search the network")
        self.assertContains(response, "Find a process")
        self.assertContains(response, "Find a machine")
        self.assertContains(response, reverse("register_vendor"))

    def test_unapproved_profile_is_not_publicly_available(self):
        self.profile.is_public_profile_approved = False
        self.profile.save(update_fields=["is_public_profile_approved"])

        response = self.client.get(
            reverse("public_vendor_profile", args=[self.profile.public_slug])
        )

        self.assertEqual(response.status_code, 404)

    def test_directory_combines_structured_filters(self):
        VendorProcessCapability.objects.create(
            profile=self.profile,
            process_type="MILLING",
        )
        other_user = User.objects.create_user(
            username="other-vendor",
            password="test-password",
            role="VENDOR",
            company_name="Other Workshop",
            phone_number="9888888888",
        )
        VendorProfile.objects.create(
            user=other_user,
            public_slug="other-workshop",
            city="Pune",
            is_public_profile=True,
            is_public_profile_approved=True,
        )

        response = self.client.get(
            reverse("vendor_directory"),
            {"city": "Pune", "process": "MILLING", "material": "ALUMINIUM"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Public Precision Engineering")
        self.assertNotContains(response, "Other Workshop")
        self.assertContains(response, "100% of selected filters matched")

    def test_public_profile_shows_structured_machine_specifications(self):
        VendorMachine.objects.create(
            profile=self.profile,
            machine_name="DMG Mori 5 Axis",
            machine_type="VMC",
            machine_quantity=2,
            axis_count=5,
            x_travel_mm="600",
            y_travel_mm="500",
            z_travel_mm="450",
            maximum_workpiece_weight_kg="300",
        )

        response = self.client.get(
            reverse("public_vendor_profile", args=[self.profile.public_slug])
        )

        self.assertContains(response, "5 Axis")
        self.assertContains(response, "600")
        self.assertContains(response, "Max workpiece: 300")

    def test_vendor_can_add_machine_inventory_with_structured_specs(self):
        self.client.login(username="public-vendor", password="test-password")

        response = self.client.post(
            reverse("vendor_machine_management"),
            {
                "machine_name": "Ace Micromatic CNC",
                "machine_type": "CNC Turning",
                "machine_quantity": 5,
                "axis_count": 2,
                "maximum_turning_diameter_mm": "350",
                "between_centers_distance_mm": "800",
                "is_active": "on",
            },
        )

        self.assertRedirects(response, reverse("vendor_machine_management"))
        machine = VendorMachine.objects.get(machine_name="Ace Micromatic CNC")
        self.assertEqual(machine.profile, self.profile)
        self.assertEqual(machine.machine_quantity, 5)
        self.assertEqual(machine.maximum_turning_diameter_mm, 350)

    def test_sitemap_lists_only_approved_public_profiles(self):
        response = self.client.get(reverse("sitemap"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "/vendors/public-precision-engineering/")

        self.profile.is_public_profile_approved = False
        self.profile.save(update_fields=["is_public_profile_approved"])

        response = self.client.get(reverse("sitemap"))
        self.assertNotContains(response, "/vendors/public-precision-engineering/")

    def test_robots_advertises_sitemap_and_protects_exchange_routes(self):
        response = self.client.get(reverse("robots_txt"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Disallow: /exchange/")
        self.assertContains(response, "Sitemap:")
