"""
Primexa Exchange
View Compatibility Layer

Business logic is stored inside exchange/view_modules/.

Do not add new business logic to this file.
"""

# ==========================================================

# DASHBOARD

# ==========================================================

from .view_modules.dashboard import (
dashboard,
oem_dashboard,
vendor_dashboard,
engineer_dashboard,

)
from .view_modules.notifications import (
    notifications_page,
)

# ==========================================================

# REQUIREMENT

# ==========================================================

from .view_modules.requirement import (
upload_job_view,
review_workload,
)

# ==========================================================

# NDA / SECURE FILES

# ==========================================================

from .view_modules.nda import (
sign_nda,
download_file,
download_nda_pdf,
)

# ==========================================================

# BIDDING

# ==========================================================

from .view_modules.bidding import (
place_bid_view,
primexa_manage_bids,
)

# ==========================================================

# COMMERCIAL

# ==========================================================

from .view_modules.commercial import (
oem_approve_quote,
final_vendor_award,
)

# ==========================================================

# FAI

# ==========================================================

from .view_modules.fai import (
fai_submit,
fai_review,
)
from .view_modules.delivery_risk import (
    report_delivery_risk,
    review_delivery_risk,
)
