import uuid
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.text import slugify

def generate_unique_id(role):
    prefix_map = {
        'OEM': 'FX-OEM',
        'VENDOR': 'FX-VND',
        'ENGINEER': 'FX-ENG',
        'EXPERT': 'FX-EXP'
    }
    prefix = prefix_map.get(role, 'FX-USR')
    return f"{prefix}-{str(uuid.uuid4()).upper()[:6]}"

class User(AbstractUser):
    ROLE_CHOICES = (
        ('OEM', 'Original Equipment Manufacturer'),
        ('VENDOR', 'Vendor / Manufacturer'),
        ('ENGINEER', 'Primexa Staff Engineer'),
        ('EXPERT', 'Independent Manufacturing Expert'),
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


class LoginActivity(models.Model):
    """Immutable audit entry for each successful user login."""

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="login_activities",
    )
    logged_in_at = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.CharField(max_length=512, blank=True)

    class Meta:
        ordering = ("-logged_in_at",)
        verbose_name = "login activity"
        verbose_name_plural = "login activities"

    def __str__(self):
        return f"{self.user.username} logged in at {self.logged_in_at:%Y-%m-%d %H:%M:%S}"


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

    # --- Public profile identity, publication and search location ---
    # These fields are intentionally separate from the full shop address.  The
    # address can remain private while discovery uses only approved, structured
    # location data.
    public_slug = models.SlugField(
        max_length=255,
        unique=True,
        null=True,
        blank=True,
        help_text="Unique URL slug for the public vendor profile.",
    )
    public_description = models.TextField(
        blank=True,
        help_text="Public company description for the vendor profile.",
    )
    country = models.CharField(max_length=100, blank=True)
    state = models.CharField(max_length=100, blank=True)
    city = models.CharField(max_length=100, blank=True)
    industrial_area = models.CharField(max_length=150, blank=True)
    pin_code = models.CharField(max_length=20, blank=True)
    public_enquiry_email = models.EmailField(blank=True)
    public_enquiry_phone = models.CharField(max_length=20, blank=True)

    # Only Primexa staff should change these controls.  Public discovery and
    # sitemap entries will require both publication and approval.
    is_public_profile = models.BooleanField(default=False)
    is_public_profile_approved = models.BooleanField(default=False)
    is_verified = models.BooleanField(default=False)
    
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

    # Structured part and batch limits used for vendor discovery/matching.
    # The original text fields above are retained for existing vendor data.
    min_part_size_mm = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
    )
    max_part_size_mm = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
    )
    max_part_diameter_mm = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
    )
    max_part_length_mm = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
    )
    max_part_weight_kg = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
    )
    min_batch_quantity = models.PositiveIntegerField(null=True, blank=True)
    max_batch_quantity = models.PositiveIntegerField(null=True, blank=True)

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
        if not self.public_slug:
            self.public_slug = slugify(f"{self.user.company_name}-{self.user_id}")
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


class ExpertProfile(models.Model):
    """Public specialist profile, separate from internal Primexa engineers."""

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="expert_profile")
    expert_id_code = models.CharField(max_length=50, unique=True, blank=True, editable=False)
    headline = models.CharField(max_length=200, blank=True)
    expertise = models.TextField(help_text="Processes, domains, and technical skills.")
    industries = models.TextField(blank=True)
    projects = models.TextField(blank=True, help_text="Completed projects and case studies suitable for public display.")
    certifications = models.TextField(blank=True, help_text="Professional certifications and qualifications.")
    years_of_experience = models.PositiveIntegerField(default=0)
    city = models.CharField(max_length=100, blank=True)
    about = models.TextField(blank=True)
    is_available = models.BooleanField(default=True)
    availability_note = models.CharField(max_length=200, blank=True, help_text="For example: Available weekdays 10:00–16:00 IST.")
    is_public_profile = models.BooleanField(default=False)
    is_verified = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        if not self.expert_id_code:
            self.expert_id_code = self.user.unique_id
        super().save(*args, **kwargs)

    def __str__(self):
        return f"[{self.expert_id_code}] {self.user.get_full_name() or self.user.username}"


class ServiceRequest(models.Model):
    REQUEST_TYPE_CHOICES = (
        ("FIND_VENDOR", "Find a vendor for a task"),
        ("FIND_EXPERT", "Find an expert for a project"),
        ("END_TO_END", "Prototype to delivery / complete assembly"),
    )
    STATUS_CHOICES = (("NEW", "New"), ("CONTACTED", "Contacted"), ("QUALIFIED", "Qualified"), ("CLOSED", "Closed"))

    submitted_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="service_requests")
    request_type = models.CharField(max_length=20, choices=REQUEST_TYPE_CHOICES)
    project_title = models.CharField(max_length=255)
    task_description = models.TextField()
    required_processes = models.TextField(blank=True)
    quantity_or_scope = models.CharField(max_length=150, blank=True)
    budget_range = models.CharField(max_length=100, blank=True)
    target_timeline = models.CharField(max_length=150, blank=True)
    contact_name = models.CharField(max_length=150)
    contact_email = models.EmailField()
    contact_phone = models.CharField(max_length=20, blank=True)
    company_name = models.CharField(max_length=255, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="NEW")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-created_at",)

    def __str__(self):
        return f"{self.get_request_type_display()}: {self.project_title}"
