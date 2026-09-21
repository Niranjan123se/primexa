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
        if not self.public_slug or self.public_slug == "None":
            base_slug = slugify(self.user.company_name) or slugify(self.user.username) or f"vendor-{self.user_id}"
            slug = base_slug
            counter = 1
            while VendorProfile.objects.filter(public_slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.public_slug = slug
        super().save(*args, **kwargs)

    def __str__(self):
        return f"[{self.vendor_id_code}] {self.user.company_name} - Vendor Profile"


class OEMProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='oem_profile')
    oem_id_code = models.CharField(max_length=50, unique=True, blank=True, editable=False)
    
    slug = models.SlugField(
        max_length=255,
        unique=True,
        null=True,
        blank=True,
        help_text="Unique URL slug for the OEM business profile.",
    )
    is_approved = models.BooleanField(default=False)
    is_verified = models.BooleanField(default=False)
    
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
        if not self.slug or self.slug == "None":
            base_slug = slugify(self.user.company_name) or slugify(self.user.username) or f"oem-{self.user_id}"
            slug = base_slug
            counter = 1
            while OEMProfile.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug
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
    slug = models.SlugField(
        max_length=255,
        unique=True,
        null=True,
        blank=True,
        help_text="Unique URL slug for the public expert profile.",
    )
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
        if not self.slug or self.slug == "None":
            name = self.user.get_full_name() or self.user.company_name or self.user.username
            base_slug = slugify(name) or f"expert-{self.user_id}"
            slug = base_slug
            counter = 1
            while ExpertProfile.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug
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
    RESPONSE_CHOICES = (
        ("PENDING", "Pending Feedback"),
        ("ACCEPTED", "Accepted"),
        ("DECLINED", "Declined"),
        ("UNAVAILABLE", "Currently Unavailable"),
    )

    submitted_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="service_requests")
    assigned_expert = models.ForeignKey(ExpertProfile, null=True, blank=True, on_delete=models.SET_NULL, related_name="assigned_requests")
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
    expert_response = models.CharField(max_length=20, choices=RESPONSE_CHOICES, default="PENDING")
    expert_feedback_notes = models.TextField(blank=True)
    expert_responded_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-created_at",)

    def __str__(self):
        return f"{self.get_request_type_display()}: {self.project_title}"


class ExpertPhoto(models.Model):
    expert_profile = models.ForeignKey(ExpertProfile, on_delete=models.CASCADE, related_name="photos")
    image = models.ImageField(upload_to="expert_photos/")
    caption = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Photo for {self.expert_profile.user.username}"


class ExpertCertificate(models.Model):
    expert_profile = models.ForeignKey(ExpertProfile, on_delete=models.CASCADE, related_name="certificates")
    title = models.CharField(max_length=255)
    issuing_organization = models.CharField(max_length=255, blank=True)
    issue_date = models.DateField(null=True, blank=True)
    certificate_file = models.FileField(upload_to="expert_certificates/", blank=True, null=True)
    is_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.title} - {self.expert_profile.user.username}"


class Review(models.Model):
    RATING_CHOICES = [(1, "1 Star"), (2, "2 Stars"), (3, "3 Stars"), (4, "4 Stars"), (5, "5 Stars")]

    reviewer = models.ForeignKey(User, on_delete=models.CASCADE, related_name="reviews_given")
    vendor_profile = models.ForeignKey(VendorProfile, null=True, blank=True, on_delete=models.CASCADE, related_name="reviews")
    oem_profile = models.ForeignKey(OEMProfile, null=True, blank=True, on_delete=models.CASCADE, related_name="reviews")
    expert_profile = models.ForeignKey(ExpertProfile, null=True, blank=True, on_delete=models.CASCADE, related_name="reviews")

    rating = models.PositiveSmallIntegerField(choices=RATING_CHOICES, default=5)
    title = models.CharField(max_length=255, blank=True)
    comment = models.TextField()
    is_approved = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-created_at",)

    def __str__(self):
        target = self.vendor_profile or self.expert_profile or self.oem_profile
        return f"Review by {self.reviewer.username} ({self.rating} stars) for {target}"

