from io import BytesIO
import hashlib

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    HRFlowable,
)


def generate_nda_pdf(workload_transfer):
    buffer = BytesIO()

    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=54,
        leftMargin=54,
        topMargin=54,
        bottomMargin=54,
    )

    story = []
    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        "DocTitle",
        parent=styles["Heading1"],
        fontSize=14,
        textColor=colors.HexColor("#0a192f"),
        alignment=1,
        spaceAfter=8,
    )

    subtitle_style = ParagraphStyle(
        "DocSubTitle",
        parent=styles["Normal"],
        fontSize=8.5,
        textColor=colors.HexColor("#718096"),
        alignment=1,
        spaceAfter=12,
    )

    body_style = ParagraphStyle(
        "BodyDark",
        parent=styles["Normal"],
        fontSize=8,
        leading=11,
        textColor=colors.HexColor("#2d3748"),
        spaceAfter=6,
    )

    bold_style = ParagraphStyle(
        "BoldDark",
        parent=body_style,
        fontName="Helvetica-Bold",
    )

    story.append(
        Paragraph(
            "PRIMEXA GLOBAL (ANSDK TRADING PVT LTD)",
            title_style,
        )
    )

    story.append(
        Paragraph(
            "MANUFACTURING NON-DISCLOSURE, INTELLECTUAL PROPERTY & "
            "NON-CIRCUMVENTION AGREEMENT",
            subtitle_style,
        )
    )

    story.append(
        Paragraph(
            "Digital Reference URL: https://primexaglobal.com/nda.php",
            ParagraphStyle(
                "UrlStyle",
                parent=body_style,
                alignment=1,
                textColor=colors.HexColor("#1a365d"),
            ),
        )
    )

    story.append(
        HRFlowable(
            width="100%",
            thickness=1.2,
            color=colors.HexColor("#0a192f"),
            spaceAfter=10,
        )
    )

    cad = workload_transfer.cad_model
    vendor = workload_transfer.sub_vendor

    hash_string = (
        workload_transfer.signature_hash
        or "PENDING-VERIFICATION"
    )

    meta_data = [
        [
            Paragraph("Tracking ID:", body_style),
            Paragraph(str(cad.tracking_number), body_style),
        ],
        [
            Paragraph("Project Title:", body_style),
            Paragraph(str(cad.title), body_style),
        ],
        [
            Paragraph("Receiving Party (Supplier):", body_style),
            Paragraph(
                str(vendor.get_full_name() or vendor.username),
                body_style,
            ),
        ],
        [
            Paragraph("Supplier Email / ID:", body_style),
            Paragraph(
                f"{vendor.email} (ID: {vendor.id})",
                body_style,
            ),
        ],
        [
            Paragraph("IP Address Logged:", body_style),
            Paragraph(
                str(workload_transfer.ip_address or "Internal Gateway"),
                body_style,
            ),
        ],
        [
            Paragraph("Agreement Timestamp:", body_style),
            Paragraph(
                str(workload_transfer.agreed_at or "N/A"),
                body_style,
            ),
        ],
    ]

    table = Table(
        meta_data,
        colWidths=[150, 354],
    )

    table.setStyle(
        TableStyle(
            [
                (
                    "BACKGROUND",
                    (0, 0),
                    (-1, -1),
                    colors.HexColor("#f8fafc"),
                ),
                (
                    "BOX",
                    (0, 0),
                    (-1, -1),
                    1,
                    colors.HexColor("#e2e8f0"),
                ),
                (
                    "INNERGRID",
                    (0, 0),
                    (-1, -1),
                    0.5,
                    colors.HexColor("#e2e8f0"),
                ),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )

    story.append(table)
    story.append(Spacer(1, 8))

    story.append(
        Paragraph(
            "1 & 3. Incorporation & Confidential Information",
            bold_style,
        )
    )

    story.append(
        Paragraph(
            "This document incorporates by reference the Primexa Global "
            "(ANSDK Trading PVT LTD) NDA terms. Confidential Information "
            "encompasses all technical data, CAD models (STEP/STL/Parasolid), "
            "GD&T parameters, CAM code, and commercial data.",
            body_style,
        )
    )

    story.append(
        Paragraph(
            "4 & 5. Obligations & AI Restrictions",
            bold_style,
        )
    )

    story.append(
        Paragraph(
            "All IP Rights and Work Product remain the exclusive property "
            "of Primexa Global. The Receiving Party is strictly prohibited "
            "from reverse engineering or uploading CAD models into any "
            "third-party Artificial Intelligence (AI) / Generative AI "
            "frameworks.",
            body_style,
        )
    )

    story.append(
        Paragraph(
            "6 & 10. Manufacturing Limits & Non-Circumvention",
            bold_style,
        )
    )

    story.append(
        Paragraph(
            "The Receiving Party shall not exceed authorized quantities, "
            "subcontract work without written consent, or circumvent Primexa "
            "to deal directly with end Customers for a period of two (2) years.",
            body_style,
        )
    )

    story.append(Spacer(1, 8))

    sign_data = [
        [
            Paragraph(
                "CRYPTOGRAPHIC LEGAL PROOF & AUDIT ATTESTATION:",
                bold_style,
            )
        ],
        [
            Paragraph(
                f"Executed By: {vendor.username}<br/>"
                f"User ID: {vendor.id}<br/>"
                f"Timestamp: {workload_transfer.agreed_at}<br/>"
                f"SHA-256 Checksum Hash: {hash_string}<br/><br/>"
                "This cryptographic hash records the agreement data "
                "generated by the Primexa system for audit verification.",
                body_style,
            )
        ],
    ]

    sign_table = Table(
        sign_data,
        colWidths=[504],
    )

    sign_table.setStyle(
        TableStyle(
            [
                (
                    "BACKGROUND",
                    (0, 0),
                    (-1, -1),
                    colors.HexColor("#edf2f7"),
                ),
                (
                    "BOX",
                    (0, 0),
                    (-1, -1),
                    1,
                    colors.HexColor("#cbd5e0"),
                ),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )

    story.append(sign_table)

    doc.build(story)

    buffer.seek(0)
    return buffer