from django.test import TestCase, Client
from django.urls import reverse
from users.models import User
from exchange.models import CADModel, Bid, WorkloadTransfer
from django.core.files.uploadedfile import SimpleUploadedFile

class PrimexaExchangeTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        
        # Create Users
        self.engineer = User.objects.create_superuser(username='eng_staff', password='password123', role='ENGINEER', company_name='Primexa HQ', phone_number='9876543210')
        self.oem_user = User.objects.create_user(username='oem_corp', password='password123', role='OEM', company_name='AutoCorp', phone_number='9123456789')
        self.vendor_user = User.objects.create_user(username='workshop_ltd', password='password123', role='VENDOR', company_name='Precision Machining', phone_number='9988776655')
        
        # Create Sample CAD File
        self.cad_file = SimpleUploadedFile("test_bracket.step", b"file_content_mock", content_type="application/octet-stream")
        
        self.job = CADModel.objects.create(
            uploaded_by=self.oem_user,
            title='Bracket Assembly',
            target_price=1000.00,
            batch_quantity=50,
            file=self.cad_file,
            status='PUBLISHED'
        )

    def test_vendor_nda_signing(self):
        self.client.login(username='workshop_ltd', password='password123')
        response = self.client.post(reverse('sign_nda', args=[self.job.id]))
        
        transfer = WorkloadTransfer.objects.get(cad_model=self.job, sub_vendor=self.vendor_user)
        self.assertTrue(transfer.nda_signed_by_sub)
        self.assertIsNotNone(transfer.signature_hash)

    def test_bidding_and_pricing_engine(self):
        self.client.login(username='workshop_ltd', password='password123')
        
        # Sign NDA first
        WorkloadTransfer.objects.create(cad_model=self.job, sub_vendor=self.vendor_user, nda_signed_by_sub=True)
        
        # Place Bid
        bid_response = self.client.post(reverse('place_bid', args=[self.job.id]), {
            'offered_price': '800.00',
            'material_cost': '300.00',
            'labour_cost': '150.00',
            'machine_cost': '150.00',
            'quality_assurance_cost': '50.00',
            'tooling_cost': '25.00',
            'development_cost': '25.00',
            'prototype_cost': '25.00',
            'production_cost': '25.00',
            'packaging_and_transport_cost': '25.00',
            'overhead_cost': '20.00',
            'other_cost': '5.00',
            'other_cost_description': 'Insurance',
            'delivery_days': '7',
            'proposal_notes': 'In-stock material ready.'
        })
        
        self.assertEqual(Bid.objects.count(), 1)
        bid = Bid.objects.first()
        self.assertEqual(float(bid.cost_breakdown_total), 800.00)
        
        # Engineer Awards Contract & Applies Margin
        
        # Engineer Awards Contract & Applies Margin
        self.client.login(username='eng_staff', password='password123')
        award_response = self.client.post(reverse('primexa_manage_bids', args=[self.job.id]), {
            'winning_bid_id': bid.id,
            'margin_percentage': '20.0'
        })
        
        self.job.refresh_from_db()
        self.assertEqual(self.job.status, 'OEM_APPROVAL_PENDING')
        self.assertEqual(float(self.job.accepted_vendor_cost), 800.00)
        self.assertEqual(float(self.job.platform_margin_percentage), 20.0)
        self.assertEqual(float(self.job.final_primexa_quote), 960.00)  # 800 * 1.20

    def test_targeted_vendor_rfq_and_oem_award(self):
        # Create second vendor
        vendor2 = User.objects.create_user(username='vendor2', password='password123', role='VENDOR', company_name='Vendor Two')
        
        # OEM creates targeted job for vendor_user only
        targeted_job = CADModel.objects.create(
            uploaded_by=self.oem_user,
            title='Targeted Gear Shaft',
            target_price=500.00,
            batch_quantity=10,
            file=self.cad_file,
            status='PUBLISHED'
        )
        targeted_job.targeted_vendors.add(self.vendor_user)

        # Check vendor_user (targeted) can view, but vendor2 (non-targeted) is restricted
        self.client.login(username='workshop_ltd', password='password123')
        v1_resp = self.client.get(reverse('vendor_dashboard'))
        self.assertContains(v1_resp, 'Targeted Gear Shaft')

        self.client.login(username='vendor2', password='password123')
        v2_resp = self.client.get(reverse('vendor_dashboard'))
        self.assertNotContains(v2_resp, 'Targeted Gear Shaft')

        # Vendor 1 bids
        self.client.login(username='workshop_ltd', password='password123')
        WorkloadTransfer.objects.create(cad_model=targeted_job, sub_vendor=self.vendor_user, nda_signed_by_sub=True)
        bid = Bid.objects.create(
            cad_model=targeted_job,
            vendor=self.vendor_user,
            offered_price=450.00,
            delivery_days=5
        )

        # OEM awards order directly
        self.client.login(username='oem_corp', password='password123')
        award_url = reverse('oem_award_direct_vendor', kwargs={'file_id': targeted_job.id, 'bid_id': bid.id})
        resp = self.client.post(award_url)
        
        targeted_job.refresh_from_db()
        self.assertEqual(targeted_job.status, 'ASSIGNED_TO_VENDOR')
        self.assertEqual(targeted_job.selected_vendor, self.vendor_user)

    def test_expert_service_request_feedback(self):
        from users.models import ExpertProfile, ServiceRequest
        expert_user = User.objects.create_user(username='expert_john', password='password123', role='EXPERT', company_name='John Expert')
        expert_profile = ExpertProfile.objects.create(user=expert_user, headline='Tooling Specialist', slug='expert-john')

        req = ServiceRequest.objects.create(
            submitted_by=self.oem_user,
            assigned_expert=expert_profile,
            project_title='Die Casting Review',
            task_description='Review mold design'
        )

        self.client.login(username='expert_john', password='password123')
        respond_url = reverse('expert_respond_service_request', kwargs={'request_id': req.id})
        resp = self.client.post(respond_url, {
            'expert_response': 'ACCEPTED',
            'expert_feedback_notes': 'Available starting Monday.'
        })

        req.refresh_from_db()
        self.assertEqual(req.expert_response, 'ACCEPTED')
        self.assertEqual(req.expert_feedback_notes, 'Available starting Monday.')

    def test_review_submission(self):
        from users.models import VendorProfile, Review
        v_profile = VendorProfile.objects.create(user=self.vendor_user, public_slug='precision-machining')

        self.client.login(username='oem_corp', password='password123')
        review_url = reverse('submit_review')
        resp = self.client.post(review_url, {
            'vendor_slug': 'precision-machining',
            'rating': '5',
            'title': 'Outstanding precision and delivery',
            'comment': 'Delivered 50 bracket assemblies on time with high accuracy.'
        })

        self.assertEqual(Review.objects.count(), 1)
        rev = Review.objects.first()
        self.assertEqual(rev.rating, 5)
        self.assertEqual(rev.vendor_profile, v_profile)
        self.assertEqual(rev.reviewer, self.oem_user)

    def test_engineering_process_plan(self):
        self.client.login(username='eng_staff', password='password123')
        process_plan_url = reverse('engineering_process_plan', kwargs={'file_id': self.job.id})
        response = self.client.get(process_plan_url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Bracket Assembly')
        self.assertEqual(self.job.process_plan_status, 'DRAFT')
