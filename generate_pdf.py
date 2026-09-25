"""
Generates the official 2-page executive PDF submission for Harshit Tiwari (24BCS10277).
Strictly adheres to:
- EXACTLY 2 PAGES (no more, no less)
- Problem established before any technical/agent architecture
- Clear headings, structured tables, facts, assumptions, and unknowns
- FDE role reasoning, evidence metrics, and actionable executive decisions
"""

import os
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, KeepTogether, HRFlowable
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.pdfgen import canvas

PDF_FILENAME = "24BCS10277_Harshit_Tiwari.pdf"

class NumberedCanvas(canvas.Canvas):
    """Two-pass canvas to dynamically compute and render exact total page count."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_decorations(num_pages)
            super().showPage()
        super().save()

    def draw_page_decorations(self, page_count):
        self.saveState()
        self.setFont("Helvetica-Bold", 7.5)
        self.setFillColor(colors.HexColor("#475569"))
        
        # Running Header
        self.drawString(30, 764, "FLASHEATS OPERATIONAL BOTTLENECK & DEPENDABLE KPI PIPELINE | FDE EXECUTIVE BRIEFING")
        self.setFont("Helvetica", 7.5)
        self.drawRightString(582, 764, "Candidate: Harshit Tiwari (24BCS10277)")
        self.setStrokeColor(colors.HexColor("#CBD5E1"))
        self.setLineWidth(0.6)
        self.line(30, 759, 582, 759)
        
        # Running Footer
        self.line(30, 28, 582, 28)
        self.setFont("Helvetica", 7)
        self.setFillColor(colors.HexColor("#64748B"))
        self.drawString(30, 18, "GitHub: https://github.com/X-DIABLO-X/FDE-2-Assignement | Pipeline Run ID: FDE-RUN-20260925-124105")
        self.setFont("Helvetica-Bold", 7)
        self.drawRightString(582, 18, f"Page {self._pageNumber} of {page_count}")
        self.restoreState()

def build_pdf():
    doc = SimpleDocTemplate(
        PDF_FILENAME,
        pagesize=letter,
        leftMargin=30,
        rightMargin=30,
        topMargin=36,
        bottomMargin=36
    )

    styles = getSampleStyleSheet()
    
    # Custom Palette
    c_primary = colors.HexColor("#0F172A")    # Deep Navy
    c_blue = colors.HexColor("#1E40AF")       # Slate Blue
    c_teal = colors.HexColor("#0F766E")       # Teal Accent
    c_red = colors.HexColor("#B91C1C")        # Burgundy Red
    c_dark = colors.HexColor("#1E293B")       # Dark Charcoal
    c_slate = colors.HexColor("#475569")      # Medium Slate
    c_light_bg = colors.HexColor("#F8FAFC")   # Light Gray Table Fill
    c_alt_bg = colors.HexColor("#F1F5F9")     # Alternate Table Fill

    # Paragraph Styles (Engineered for tight, crisp 2-page fit)
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=12.5,
        leading=15,
        textColor=c_primary
    )
    
    meta_style = ParagraphStyle(
        'DocMeta',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=7.5,
        leading=9.5,
        textColor=c_slate
    )

    h1_style = ParagraphStyle(
        'Heading1_Custom',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=8.5,
        leading=10.5,
        textColor=c_blue,
        spaceBefore=4,
        spaceAfter=2
    )

    body_style = ParagraphStyle(
        'Body_Custom',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=7,
        leading=8.6,
        textColor=c_dark
    )

    body_bold = ParagraphStyle(
        'Body_Bold_Custom',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=7,
        leading=8.6,
        textColor=c_dark
    )

    table_header = ParagraphStyle(
        'TableHeader',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=6.5,
        leading=7.8,
        textColor=colors.white
    )

    table_cell = ParagraphStyle(
        'TableCell',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=6.2,
        leading=7.5,
        textColor=c_dark
    )

    table_cell_bold = ParagraphStyle(
        'TableCellBold',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=6.2,
        leading=7.5,
        textColor=c_dark
    )

    table_cell_red = ParagraphStyle(
        'TableCellRed',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=6.2,
        leading=7.5,
        textColor=c_red
    )

    story = []

    # =========================================================================
    # PAGE 1: PROBLEM CONTEXT, SOURCE REASONING & INGESTION / VALIDATION
    # =========================================================================
    
    # Title & Executive Header Block
    header_data = [
        [
            Paragraph("<b>FLASHEATS: OPERATIONAL BOTTLENECK DIAGNOSIS & REPEATABLE KPI PIPELINE</b>", title_style),
            Paragraph("<b>Author:</b> Harshit Tiwari (Roll: <b>24BCS10277</b>)<br/><b>Role:</b> Forward Deployed Engineer (FDE)<br/><b>Track:</b> A — Quick-Commerce Delivery", meta_style)
        ]
    ]
    header_table = Table(header_data, colWidths=[380, 172])
    header_table.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 1),
        ('TOPPADDING', (0,0), (-1,-1), 0),
        ('LEFTPADDING', (0,0), (-1,-1), 0),
        ('RIGHTPADDING', (0,0), (-1,-1), 0),
    ]))
    story.append(header_table)
    story.append(Spacer(1, 3))
    story.append(HRFlowable(width="100%", thickness=1, color=c_blue, spaceBefore=1, spaceAfter=4))

    # Section 1: Business Problem Statement
    story.append(Paragraph("1. THE OPERATIONAL CRISIS: WHICH PROBLEM DESERVES TO BE SOLVED?", h1_style))
    p1_text = (
        "FlashEats operates an ultra-fast quick-commerce delivery network promising 30-minute delivery (35-min contractual SLA). "
        "Over the past quarter, <b>P90 Order-to-Delivery (OTD) escalated to 54.4 minutes</b>, triggering a <b>56.4% SLA breach rate</b> "
        "and driving $36,080/day in customer refund liabilities. Customer retention dropped 14% while complaints surged 3.4×. "
        "<b>Executive Dilemma:</b> Platform leadership attributed delays to 'courier shortages' and planned a costly driver hiring surge. "
        "As the FDE, my mandate is to avoid speculative AI/model builds and first build a trustworthy data foundation connecting fragmented client systems to "
        "isolate where delay truly accumulates and evaluate operational interventions."
    )
    story.append(Paragraph(p1_text, body_style))
    story.append(Spacer(1, 4))

    # Section 2: Source Reasoning & Ownership Matrix (Class 4 Skill)
    story.append(Paragraph("2. SOURCE REASONING & FRAGMENTATION MATRIX (CLASS 4)", h1_style))
    source_headers = [
        Paragraph("Source System", table_header),
        Paragraph("Owner & Tech", table_header),
        Paragraph("Data Grain", table_header),
        Paragraph("Key Entities & Attributes", table_header),
        Paragraph("Incentives & Operational Gaps", table_header)
    ]
    source_rows = [
        [
            Paragraph("<b>OMS Platform DB</b>", table_cell_bold),
            Paragraph("Core Eng<br/>SQLite/Postgres", table_cell),
            Paragraph("1 row / order<br/>(`order_id`)", table_cell),
            Paragraph("Order checkout, payment status, subtotal, customer coordinates, promised SLA", table_cell),
            Paragraph("Optimized for transactional consistency (ACID); blind to physical doorstep/gate friction.", table_cell)
        ],
        [
            Paragraph("<b>Dispatch Engine</b>", table_cell_bold),
            Paragraph("Fleet Ops<br/>REST API / JSON", table_cell),
            Paragraph("1:N attempts / order<br/>(`dispatch_id`)", table_cell),
            Paragraph("Courier assignment offers, driver acceptance/rejections, GPS timestamps", table_cell),
            Paragraph("Couriers reject unprofitable runs; app background throttling causes GPS batching jitter.", table_cell)
        ],
        [
            Paragraph("<b>KDS Prep Logs</b>", table_cell_bold),
            Paragraph("Merchant Ops<br/>Daily CSV Export", table_cell),
            Paragraph("1 row / ticket<br/>(`kds_ticket_id`)", table_cell),
            Paragraph("POS ticket printed, prep started, cook bump-bar 'food_ready', queue depth", table_cell),
            Paragraph("Cooks omit bump-bar taps during peak rush; unmanaged tablet clocks exhibit NTP drift.", table_cell)
        ],
        [
            Paragraph("<b>Support Tickets</b>", table_cell_bold),
            Paragraph("CX Team<br/>Zendesk JSON", table_cell),
            Paragraph("0:N tickets / order<br/>(`ticket_id`)", table_cell),
            Paragraph("Late delivery claims, cold food reports, refund amounts, CSAT ratings", table_cell),
            Paragraph("Subjective customer reports filed 1-3 hrs post-delivery; agent haste to issue vouchers.", table_cell)
        ]
    ]
    source_table = Table([source_headers] + source_rows, colWidths=[90, 80, 85, 150, 147])
    source_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), c_primary),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('GRID', (0,0), (-1,-1), 0.4, colors.HexColor("#CBD5E1")),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [c_light_bg, c_alt_bg]),
        ('TOPPADDING', (0,0), (-1,-1), 2.5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 2.5),
        ('LEFTPADDING', (0,0), (-1,-1), 3),
        ('RIGHTPADDING', (0,0), (-1,-1), 3),
    ]))
    story.append(source_table)
    story.append(Spacer(1, 4))

    # Section 3: Multi-Mode Retrieval & Completeness Proofs (Class 5 Skill)
    story.append(Paragraph("3. MULTI-MODE RETRIEVAL & MATHEMATICAL COMPLETENESS PROOFS (CLASS 5)", h1_style))
    p3_text = (
        "<b>Heterogeneous Ingestion:</b> Implemented 4 retrieval modes across SQL queries (`orders_platform.db`), paginated REST API dumps "
        "(`dispatch_telemetry_stream.json`), flat CSV parsing (`kds_merchant_prep.csv`), and JSON document ingestion (`customer_support_tickets.json`). "
        "<b>Bronze Immutability:</b> Raw files are stored bit-for-bit unchanged in `data/bronze/` stamped with SHA-256 cryptographic hashes, `_ingested_at`, and `_batch_id`.<br/>"
        "<b>Mathematical Completeness Proofs:</b> (1) 100% Record Count Reconciliation (6,000 orders extracted = 6,000 bronze rows landed). "
        "(2) Primary Key Uniqueness verified across all tables (0 duplicates). (3) <b>Financial GMV Control Total Reconciliation:</b> Sum of order subtotals "
        "($231,406.85) reconciles penny-for-penny with line-item aggregates ($231,406.85, delta = $0.00), verifying zero data leakage."
    )
    story.append(Paragraph(p3_text, body_style))
    story.append(Spacer(1, 4))

    # Section 4: Data Profiling, Business Rules & Quarantine Handling (Class 6 Skill)
    story.append(Paragraph("4. DATA PROFILING, DEFENSIVE CALIBRATION & QUARANTINE ARCHITECTURE (CLASS 6)", h1_style))
    p4_intro = (
        "<b>FDE Core Principle:</b> Never silently discard data with `dropna()`. Discarding flawed records conceals system outages, "
        "distorts financial totals, and biases operational metrics. Instead, classify anomalies into defensible calibrations vs. quarantine."
    )
    story.append(Paragraph(p4_intro, body_style))
    story.append(Spacer(1, 2))

    anomaly_headers = [
        Paragraph("Anomaly & Root Cause", table_header),
        Paragraph("Observed Rate", table_header),
        Paragraph("Detection Logic & Business Impact", table_header),
        Paragraph("FDE Remediation & Audit Policy", table_header)
    ]
    anomaly_rows = [
        [
            Paragraph("<b>POS Clock Drift</b><br/>Android tablet NTP desync", table_cell_bold),
            Paragraph("914 orders<br/>(15.2%)", table_cell),
            Paragraph("`ticket_printed < order_placed` (drift: -180s to +300s). Appears cook printed ticket before customer ordered.", table_cell),
            Paragraph("<b>Defensible Calibration:</b> Shift ticket print to `t_order + 15s`; offset ready time by delta. Flag `clock_drift_calibrated = True`.", table_cell)
        ],
        [
            Paragraph("<b>Missing Bump-Bar</b><br/>Cook rush omission", table_cell_bold),
            Paragraph("239 orders<br/>(4.0%)", table_cell),
            Paragraph("`food_ready_at IS NULL` on completed orders. Naive drop loses $9,200 GMV.", table_cell),
            Paragraph("<b>Lower-Bound Imputation:</b> Impute ready time at `t_pickup - 45s`. Flag `is_food_ready_imputed = True`.", table_cell)
        ],
        [
            Paragraph("<b>Network Jitter</b><br/>Mall basement packet queue", table_cell_bold),
            Paragraph("225 orders<br/>(3.8%)", table_cell),
            Paragraph("`arrived_store > picked_up` by 5-25s due to batch sync on cell restore.", table_cell),
            Paragraph("<b>Jitter Clamping:</b> If inversion &le; 35s, clamp arrival to `t_pickup - 1s`. Flag `network_jitter_clamped = True`.", table_cell)
        ],
        [
            Paragraph("<b>Critical Inversions</b><br/>Sensor/timestamp corruption", table_cell_bold),
            Paragraph("12 orders<br/>(0.2%)", table_cell_red),
            Paragraph("Arrived > 45m after pickup or delivery before placement. Irrecoverable.", table_cell),
            Paragraph("<b>Quarantine DLQ:</b> Isolate to `quarantine_audit.parquet` with error code & context. Trigger circuit breaker if &gt; 5%.", table_cell)
        ]
    ]
    anomaly_table = Table([anomaly_headers] + anomaly_rows, colWidths=[110, 60, 185, 197])
    anomaly_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), c_primary),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('GRID', (0,0), (-1,-1), 0.4, colors.HexColor("#CBD5E1")),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [c_light_bg, c_alt_bg]),
        ('TOPPADDING', (0,0), (-1,-1), 2),
        ('BOTTOMPADDING', (0,0), (-1,-1), 2),
        ('LEFTPADDING', (0,0), (-1,-1), 3),
        ('RIGHTPADDING', (0,0), (-1,-1), 3),
    ]))
    story.append(anomaly_table)

    # Force strict 2-page pagination boundary
    story.append(PageBreak())

    # =========================================================================
    # PAGE 2: WORKFLOW MODELING, EVIDENCE TABLE, KUAL & DECISION
    # =========================================================================

    # Section 5: Workflow State Machine & Delay Decomposition (Class 7 Skill)
    story.append(Paragraph("5. WORKFLOW STATE MACHINE & BOTTLENECK DECOMPOSITION (CLASS 7)", h1_style))
    p5_text = (
        "The order lifecycle was modeled as an event state machine: <b>SUBMITTED &rarr; CONFIRMED &rarr; PREP_STARTED &rarr; "
        "FOOD_READY &rarr; COURIER_ASSIGNED &rarr; ARRIVED_STORE &rarr; PICKED_UP &rarr; DELIVERED</b> (with CANCELLED branch). "
        "This unlocks decomposing total cycle time (<i>T_OTD = t_delivered - t_placed</i>) into 5 discrete stages:<br/>"
        "• <b>Stage 1 (Merchant Lag):</b> <i>t_confirmed - t_placed</i> (Mean: <b>1.1 min</b>) &mdash; Highly efficient; merchants accept tickets promptly.<br/>"
        "• <b>Stage 2 (Kitchen Prep Overrun):</b> <i>Actual Prep - Estimated Prep</i> (Mean: <b>11.1 min</b>, P90: <b>22.4 min</b>) &mdash; Kitchens congested during peak rush.<br/>"
        "• <b>Stage 3 (Dispatch & Travel to Store):</b> <i>t_arrived - t_confirmed</i> (Mean: <b>8.2 min</b>) &mdash; Courier transit is fast and dependable.<br/>"
        "• <b>Stage 4 (Store Synchronization Friction Nexus):</b> <i>t_food_ready - t_arrived_store</i> (Mean: <b>15.8 min</b>, P90: <b>28.3 min</b>) &mdash; <b>THE ROOT CAUSE BOTTLENECK.</b><br/>"
        "• <b>Stage 5 (Last-Mile Transit):</b> <i>t_delivered - t_picked_up</i> (Mean: <b>12.4 min</b>) &mdash; Normal urban travel; no structural failure.<br/>"
        "<b>DIAGNOSTIC VERDICT:</b> Courier shortages are an illusion. Because the dispatch engine fires couriers immediately upon order placement (<i>t_dispatch = t_placed</i>), "
        "couriers reach stores in 8 minutes while kitchen prep takes 24 minutes. <b>Couriers spend 15.8 minutes idling outside kitchens</b>, "
        "accounting for <b>52.8% of excess delivery delay</b> and starving the platform of active courier throughput."
    )
    story.append(Paragraph(p5_text, body_style))
    story.append(Spacer(1, 4))

    # Section 6: Evidence Table — Core Metrics & Intervention Simulations
    story.append(Paragraph("6. EXECUTIVE EVIDENCE TABLE & COUNTERFACTUAL INTERVENTION EVALUATION", h1_style))
    kpi_headers = [
        Paragraph("Operational Scenario", table_header),
        Paragraph("P50 OTD", table_header),
        Paragraph("P90 OTD", table_header),
        Paragraph("SLA Breach %", table_header),
        Paragraph("Rider Wait", table_header),
        Paragraph("Fleet Gain", table_header),
        Paragraph("Refunds / Day", table_header),
        Paragraph("FDE Operational Assessment", table_header)
    ]
    kpi_rows = [
        [
            Paragraph("<b>Baseline (Immediate Dispatch)</b>", table_cell_bold),
            Paragraph("37.7 min", table_cell),
            Paragraph("54.4 min", table_cell_red),
            Paragraph("<b>56.4%</b>", table_cell_red),
            Paragraph("15.8 min", table_cell_red),
            Paragraph("0.0%", table_cell),
            Paragraph("$36,081", table_cell_red),
            Paragraph("Status Quo: Burning courier hours & bleeding customer trust.", table_cell)
        ],
        [
            Paragraph("<b>Intervention 1: Staged Dispatch</b>", table_cell_bold),
            Paragraph("26.3 min", table_cell),
            Paragraph("<b>33.6 min</b>", table_cell_bold),
            Paragraph("<b>6.6%</b>", table_cell_bold),
            Paragraph("<b>3.3 min</b>", table_cell_bold),
            Paragraph("<b>+21.4%</b>", table_cell_bold),
            Paragraph("$20,927", table_cell),
            Paragraph("<b>High Impact:</b> Offset dispatch by prep estimate; eliminates wait.", table_cell)
        ],
        [
            Paragraph("<b>Intervention 2: Dynamic Buffering</b>", table_cell_bold),
            Paragraph("36.7 min", table_cell),
            Paragraph("51.0 min", table_cell),
            Paragraph("55.2%", table_cell),
            Paragraph("15.8 min", table_cell),
            Paragraph("+5.2%", table_cell),
            Paragraph("$25,978", table_cell),
            Paragraph("Paces kitchen queue; accurate customer ETAs dampen demand.", table_cell)
        ],
        [
            Paragraph("<b>Intervention 3: Combined (1 + 2)</b>", table_cell_bold),
            Paragraph("<b>24.7 min</b>", table_cell_bold),
            Paragraph("<b>31.4 min</b>", table_cell_bold),
            Paragraph("<b>3.9%</b>", table_cell_bold),
            Paragraph("<b>3.3 min</b>", table_cell_bold),
            Paragraph("<b>+26.8%</b>", table_cell_bold),
            Paragraph("<b>$10,463</b>", table_cell_bold),
            Paragraph("<b>Recommended FDE Strategy:</b> Slashes refunds by 71%.", table_cell)
        ]
    ]
    kpi_table = Table([kpi_headers] + kpi_rows, colWidths=[110, 42, 42, 52, 45, 45, 54, 162])
    kpi_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), c_primary),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('GRID', (0,0), (-1,-1), 0.4, colors.HexColor("#CBD5E1")),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [c_light_bg, c_alt_bg]),
        ('TOPPADDING', (0,0), (-1,-1), 2.5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 2.5),
        ('LEFTPADDING', (0,0), (-1,-1), 3),
        ('RIGHTPADDING', (0,0), (-1,-1), 3),
    ]))
    story.append(kpi_table)
    story.append(Spacer(1, 4))

    # Section 7: Epistemological Framework (KUAL)
    story.append(Paragraph("7. EPISTEMOLOGICAL RIGOR: FACTS, ASSUMPTIONS, UNKNOWNS & LIMITATIONS (KUAL)", h1_style))
    kual_headers = [
        Paragraph("Dimension", table_header),
        Paragraph("Operational Reality & FDE Epistemological Boundary", table_header)
    ]
    kual_rows = [
        [
            Paragraph("<b>FACTS</b><br/>(Empirical Ground Truth)", table_cell_bold),
            Paragraph(
                "• Exact order placement, payment capture ($231,406.85 GMV), and SLA timestamps are 100% verified.<br/>"
                "• Courier idle dwell outside merchant kitchens accounts for 52.8% of total delivery delay, not transit congestion.<br/>"
                "• 15.2% of merchant POS terminals exhibit hardware clock drift of up to 300 seconds.", table_cell
            )
        ],
        [
            Paragraph("<b>ASSUMPTIONS</b><br/>(Defensible Choices)", table_cell_bold),
            Paragraph(
                "• POS clock drift within [-300s, +300s] is hardware desync; shifting print time to `t_order + 15s` preserves valid kitchen metrics.<br/>"
                "• Missing KDS bump bars on completed orders represent cook omissions; imputing ready time at `t_pickup - 45s` is a defensible lower bound.<br/>"
                "• Courier transit speed is assumed invariant to dispatch time offsets within a 15-minute scheduling window.", table_cell
            )
        ],
        [
            Paragraph("<b>UNKNOWNS</b><br/>(Unobservable Reality)", table_cell_bold),
            Paragraph(
                "• Sub-station kitchen bottlenecks (e.g., whether delays occurred at fryer, grill, or packing) are unmeasured by KDS.<br/>"
                "• Physical doorstep friction (apartment intercom delays, elevator wait times) is unobservable in mobile GPS pings.<br/>"
                "• Subjective courier rejection rationales (unfavorable drop-off zone vs. rain fatigue) are unrecorded.", table_cell
            )
        ],
        [
            Paragraph("<b>LIMITATIONS</b><br/>(Boundary Conditions)", table_cell_bold),
            Paragraph(
                "• The pipeline operates on daily batch reconciliation; production deployment requires streaming event-driven dispatch.<br/>"
                "• Counterfactual simulations do not account for dynamic driver churn if couriers experience fewer immediate dispatches.", table_cell
            )
        ]
    ]
    kual_table = Table([kual_headers] + kual_rows, colWidths=[110, 442])
    kual_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), c_primary),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('GRID', (0,0), (-1,-1), 0.4, colors.HexColor("#CBD5E1")),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [c_light_bg, c_alt_bg]),
        ('TOPPADDING', (0,0), (-1,-1), 2),
        ('BOTTOMPADDING', (0,0), (-1,-1), 2),
        ('LEFTPADDING', (0,0), (-1,-1), 3),
        ('RIGHTPADDING', (0,0), (-1,-1), 3),
    ]))
    story.append(kual_table)
    story.append(Spacer(1, 4))

    # Section 8: The Core FDE Judgement Call & Executive Action Plan
    story.append(Paragraph("8. THE CORE FDE JUDGEMENT CALL & EXECUTIVE ACTIONABLE DECISION", h1_style))
    p8_text = (
        "<b>The Naive Data Engineering Approach:</b> Faced with 914 orders exhibiting negative durations (`t_printed < t_order`), a conventional "
        "data engineer applies `df.dropna()` or `df = df[dwell >= 0]`. <i>Why this is fatal:</i> It silently discards <b>15.2% of all orders</b> "
        "worth $35,000+ GMV concentrated in the highest-revenue Downtown cluster, obscures the kitchen bottleneck, and conceals platform liability.<br/>"
        "<b>The FDE Judgement Call:</b> I implemented bidirectional temporal calibration using physical event anchors (`t_order` and `t_pickup`), "
        "preserving full financial accountability while flagging adjusted rows (`clock_drift_calibrated = True`). Irrecoverable corruptions (12 rows) "
        "were routed to a Dead-Letter Queue (`quarantine_audit.parquet`) under circuit-breaker monitoring.<br/>"
        "<b>KINETIC BUSINESS DECISION:</b> <b>Deploy Staged Offset Dispatch immediately.</b> Instead of dispatching couriers at order placement, "
        "hold dispatch by <i>(T_prep - T_travel)</i>. This slashes rider wait from 15.8m to 3.3m, brings P90 OTD under the 35-min SLA (33.6m), "
        "and <b>unlocks +21.4% effective delivery fleet capacity without hiring a single additional courier</b>, saving $15,100/day in refund costs."
    )
    story.append(Paragraph(p8_text, body_style))

    doc.build(story, canvasmaker=NumberedCanvas)
    print(f"[+] Successfully generated {PDF_FILENAME}")

if __name__ == "__main__":
    build_pdf()
