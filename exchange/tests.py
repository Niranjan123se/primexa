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
