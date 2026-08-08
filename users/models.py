import uuid
from django.contrib.auth.models import AbstractUser
from django.db import models

def generate_unique_id(role):
    prefix_map = {
        'OEM': 'FX-OEM',
        'VENDOR': 'FX-VND',
        'ENGINEER': 'FX-ENG'
    }
    prefix = prefix_map.get(role, 'FX-USR')
    return f"{prefix}-{str(uuid.uuid4()).upper()[:6]}"

class User(AbstractUser):
    ROLE_CHOICES = (
        ('OEM', 'Original Equipment Manufacturer'),
        ('VENDOR', 'Vendor / Manufacturer'),
        ('ENGINEER', 'Primexa Staff Engineer'),
    )
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='OEM')
    unique_id = models.CharField(max_length=50, unique=True, blank=True, editable=False, help_text="System-wide unique enterprise ID")
    accepted_terms_date = models.DateTimeField(null=True, blank=True)
    company_name = models.CharField(max_length=255)
    phone_number = models.CharField(max_length=20)

    def save(self, *args, **kwargs):
        if not self.unique_id:
            self.unique_id = generate_unique_id(self.role)
        super().save(*args, **kwargs)


class VendorProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='vendor_profile')
    vendor_id_code = models.CharField(max_length=50, unique=True, blank=True, editable=False)
    
    # --- Personnel & Leadership ---
    owner_name = models.CharField(max_length=150, blank=True)
    manager_name = models.CharField(max_length=150, blank=True, help_text="Manager or Production In-charge")
    quality_incharge_name = models.CharField(max_length=150, blank=True)

    # --- Legal, Business & Financials ---
    gst_number = models.CharField(max_length=15, blank=True)
    pan_number = models.CharField(max_length=10, blank=True)
    cin_number = models.CharField(max_length=21, blank=True, null=True, help_text="Only for Pvt Ltd")
    location = models.TextField(blank=True, help_text="Full shop address")
    
    TURNOVER_CHOICES = [
        ('LESS_50L', 'Less than 50 Lakhs'),
        ('50L_1CR', '50 Lakhs to 1 Crore'),
        ('1CR_5CR', '1 Crore to 5 Crores'),
        ('5CR_10CR', '5 Crores to 10 Crores'),
        ('10CR_50CR', '10 Crores to 50 Crores'),
        ('50CR_100CR', '50 Crores to 100 Crores'),
        ('ABOVE_100CR', 'Above 100 Crores'),
    ]
    turnover_range = models.CharField(max_length=20, choices=TURNOVER_CHOICES, blank=True)
    past_customers = models.TextField(blank=True, help_text="Key companies served")

    # --- Technical Capabilities & Quality ---
    certificates = models.TextField(blank=True, help_text="e.g., ISO 9001, AS9100")
    machinery_list = models.TextField(blank=True, help_text="List of CNCs, VMCs, Lathes, etc.")
    production_capacity = models.CharField(max_length=255, blank=True)
    min_part_size = models.CharField(max_length=100, blank=True)
    max_part_size = models.CharField(max_length=100, blank=True)
    quality_instruments = models.TextField(blank=True, help_text="e.g., CMM, Vernier, Micrometers, Height Gauge")

    # --- Operations & Tooling (Forge 360 Integration) ---
    machine_capacity = models.CharField(max_length=255, blank=True)
    current_workload_percentage = models.IntegerField(default=0)
    is_open_to_subcontract = models.BooleanField(default=True)

    OPERATING_HOURS_CHOICES = [
        ('8', '8 Hours'),
        ('12', '12 Hours'),
        ('24', '24 Hours'),
    ]
    operating_hours = models.CharField(max_length=2, choices=OPERATING_HOURS_CHOICES, blank=True)
    has_inhouse_programmer = models.BooleanField(default=False, help_text="Check if in-house programmer is available")
    
    interested_in_low_cost_inserts = models.BooleanField(default=False, help_text="Interested in low-cost insert supply?")
    current_inserts_used = models.TextField(blank=True, help_text="Brands, Types, and Present Prices paid")
    other_services_needed = models.TextField(blank=True, help_text="Any other service needed from our side")
    shop_photo = models.ImageField(upload_to='shop_photos/', blank=True, null=True)

    def save(self, *args, **kwargs):
        if not self.vendor_id_code:
            self.vendor_id_code = self.user.unique_id
        super().save(*args, **kwargs)

    def __str__(self):
        return f"[{self.vendor_id_code}] {self.user.company_name} - Vendor Profile"


class OEMProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='oem_profile')
    oem_id_code = models.CharField(max_length=50, unique=True, blank=True, editable=False)
    
    contact_person_name = models.CharField(max_length=150, blank=True, help_text="Primary procurement or engineering lead")
    designation = models.CharField(max_length=100, blank=True, help_text="e.g., Head of Supply Chain, Senior Engineer")
    gst_number = models.CharField(max_length=15, blank=True)
    pan_number = models.CharField(max_length=10, blank=True)
    billing_address = models.TextField(blank=True, help_text="Official registered office address")
    
    industry = models.CharField(max_length=255, blank=True)
    INDUSTRY_CHOICES = [
        ('AUTOMOTIVE', 'Automotive & EV'),
        ('AEROSPACE', 'Aerospace & Defense'),
        ('MEDICAL', 'Medical Devices & Healthcare'),
        ('INDUSTRIAL', 'Industrial Heavy Machinery'),
        ('CONSUMER', 'Consumer Electronics & Appliances'),
        ('OTHER', 'Other Engineering Sector'),
    ]
    industry_sector = models.CharField(max_length=30, choices=INDUSTRY_CHOICES, blank=True)
    typical_requirements = models.TextField(blank=True, help_text="Briefly describe what parts you regularly outsource")

    def save(self, *args, **kwargs):
        if not self.oem_id_code:
            self.oem_id_code = self.user.unique_id
        super().save(*args, **kwargs)

    def __str__(self):
        return f"[{self.oem_id_code}] {self.user.company_name} - OEM Profile"


class EngineerProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='engineer_profile')
    engineer_id_code = models.CharField(max_length=50, unique=True, blank=True, editable=False)
    
    designation = models.CharField(max_length=100, blank=True, default="Staff Manufacturing Engineer")
    department = models.CharField(max_length=100, blank=True, help_text="e.g., CNC Tooling, Quality Assurance, FAI Inspection")
    phone_number = models.CharField(max_length=20, blank=True)
    assigned_zone = models.CharField(max_length=100, blank=True, default="Pune / Maharashtra Hub")
    is_active_reviewer = models.BooleanField(default=True)

    def save(self, *args, **kwargs):
        if not self.engineer_id_code:
            self.engineer_id_code = self.user.unique_id
        super().save(*args, **kwargs)

    def __str__(self):
        return f"[{self.engineer_id_code}] {self.user.username} - Primexa Staff Engineer"