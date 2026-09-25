"""
Generates crisp, publication-grade architecture and workflow diagrams for FlashEats FDE project.
Outputs:
- docs/source_map.png
- docs/workflow_fsm.png
"""

import os
import matplotlib.pyplot as plt
import matplotlib.patches as patches

os.makedirs("docs", exist_ok=True)

def generate_source_map():
    fig, ax = plt.subplots(figsize=(12, 7), dpi=300)
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 100)
    ax.axis('off')

    # Color Palette
    c_blue = '#1E3A8A'
    c_light_blue = '#DBEAFE'
    c_teal = '#0D9488'
    c_light_teal = '#CCFBF1'
    c_amber = '#D97706'
    c_light_amber = '#FEF3C7'
    c_red = '#DC2626'
    c_light_red = '#FEE2E2'
    c_slate = '#334155'

    # Title
    ax.text(50, 95, "FlashEats Multi-Source Ingestion & Dependable Pipeline Architecture", 
            ha='center', va='center', fontsize=15, fontweight='bold', color=c_blue)
    ax.text(50, 91, "From Fragmented Client Systems to Trustworthy Business Decisions | FDE Foundations", 
            ha='center', va='center', fontsize=10, color=c_slate, style='italic')

    # 1. Source Systems Layer (Top)
    sources = [
        ("Source 1: Operational DB\n(SQLite / RDBMS)\n• Orders & Line Items\n• Payment & Geo Grain", 5, c_blue, c_light_blue),
        ("Source 2: Dispatch Service\n(Mock REST API)\n• Driver Telemetry\n• 1:N Dispatch Attempts", 29, c_teal, c_light_teal),
        ("Source 3: KDS Logs\n(Merchant Daily CSV)\n• Kitchen Bump Bar\n• Queue Depth Grain", 53, c_amber, c_light_amber),
        ("Source 4: Support CRM\n(Zendesk JSON)\n• Escalations & CSAT\n• Refund Claims Grain", 77, c_red, c_light_red)
    ]

    for title, x, border_c, bg_c in sources:
        box = patches.FancyBboxPatch((x, 68), 18, 18, boxstyle="round,pad=0.5", 
                                     edgecolor=border_c, facecolor=bg_c, linewidth=1.5)
        ax.add_patch(box)
        ax.text(x + 9, 77, title, ha='center', va='center', fontsize=8, color=border_c, fontweight='bold')
        # Arrow down
        ax.annotate('', xy=(x + 9, 57), xytext=(x + 9, 67),
                    arrowprops=dict(facecolor=c_slate, edgecolor='none', width=1.5, headwidth=6))

    # 2. Bronze Layer
    bronze_box = patches.FancyBboxPatch((5, 47), 90, 10, boxstyle="round,pad=0.5",
                                        edgecolor='#64748B', facecolor='#F1F5F9', linewidth=1.5)
    ax.add_patch(bronze_box)
    ax.text(50, 52, "BRONZE INGESTION & AUDIT LAYER (Immutable Parquet Landing)\n"
                    "Cryptographic Checksums (SHA-256) | Ingestion Audit Stamps (_ingested_at, _batch_id) | Financial GMV Reconciliation Control Total",
            ha='center', va='center', fontsize=9, fontweight='bold', color=c_slate)

    # Arrow down from Bronze
    ax.annotate('', xy=(50, 37), xytext=(50, 46),
                arrowprops=dict(facecolor=c_slate, edgecolor='none', width=2, headwidth=8))

    # 3. Validation & Quarantine Engine
    val_box = patches.FancyBboxPatch((5, 27), 65, 10, boxstyle="round,pad=0.5",
                                     edgecolor=c_teal, facecolor=c_light_teal, linewidth=1.5)
    ax.add_patch(val_box)
    ax.text(37.5, 32, "DATA PROFILING & DEFENSIVE CALIBRATION ENGINE\n"
                      "POS Clock Drift Calibration (±300s) | Missing Bump Bar Imputation | Network Jitter Clamping",
            ha='center', va='center', fontsize=8.5, fontweight='bold', color=c_teal)

    # Quarantine Dead-Letter Box
    quar_box = patches.FancyBboxPatch((74, 27), 21, 10, boxstyle="round,pad=0.5",
                                      edgecolor=c_red, facecolor=c_light_red, linewidth=1.5)
    ax.add_patch(quar_box)
    ax.text(84.5, 32, "QUARANTINE DLQ\nquarantine_audit.parquet\n(12 Severe Errors Isolated)",
            ha='center', va='center', fontsize=8, fontweight='bold', color=c_red)

    # Split arrows
    ax.annotate('', xy=(84.5, 37), xytext=(70, 47),
                arrowprops=dict(facecolor=c_red, edgecolor='none', width=1.5, headwidth=6))
    ax.annotate('', xy=(37.5, 18), xytext=(37.5, 26),
                arrowprops=dict(facecolor=c_slate, edgecolor='none', width=2, headwidth=8))

    # 4. Silver & Gold Layer (Bottom)
    silver_box = patches.FancyBboxPatch((5, 5), 42, 13, boxstyle="round,pad=0.5",
                                        edgecolor='#4338CA', facecolor='#EEF2FF', linewidth=1.5)
    ax.add_patch(silver_box)
    ax.text(26, 11.5, "SILVER WORKFLOW MODEL\nfact_order_lifecycle.parquet\n5-Stage Delay Decomposition\n(Merchant, Prep, Dispatch, Wait, Last-Mile)",
            ha='center', va='center', fontsize=8.5, fontweight='bold', color='#4338CA')

    gold_box = patches.FancyBboxPatch((53, 5), 42, 13, boxstyle="round,pad=0.5",
                                      edgecolor='#047857', facecolor='#ECFDF5', linewidth=1.5)
    ax.add_patch(gold_box)
    ax.text(74, 11.5, "GOLD ANALYTICAL MARTS\nkpi_summary_daily & simulations\nCounterfactual Decision Support:\nStaged Offset Dispatch (+21.4% Fleet Capacity)",
            ha='center', va='center', fontsize=8.5, fontweight='bold', color='#047857')

    ax.annotate('', xy=(52, 11.5), xytext=(47, 11.5),
                arrowprops=dict(facecolor=c_slate, edgecolor='none', width=1.5, headwidth=6))

    plt.tight_layout()
    plt.savefig("docs/source_map.png", bbox_inches='tight')
    plt.close()
    print("[+] Generated docs/source_map.png")

def generate_workflow_fsm():
    fig, ax = plt.subplots(figsize=(12, 6.5), dpi=300)
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 100)
    ax.axis('off')

    c_blue = '#1E3A8A'
    c_indigo = '#4F46E5'
    c_amber = '#D97706'
    c_red = '#DC2626'
    c_green = '#059669'
    c_slate = '#334155'

    # Title
    ax.text(50, 94, "FlashEats End-to-End Order Workflow State Machine & Delay Attribution", 
            ha='center', va='center', fontsize=14, fontweight='bold', color=c_blue)
    ax.text(50, 90, "Identifying the Synchronization Friction Nexus between Kitchen Prep and Courier Arrival", 
            ha='center', va='center', fontsize=9.5, color=c_slate, style='italic')

    # States sequence along X axis
    states = [
        ("PLACED\nt_placed", 5, 65, c_blue, "#DBEAFE"),
        ("CONFIRMED\nt_confirmed", 23, 65, c_blue, "#DBEAFE"),
        ("FOOD READY\nt_food_ready", 45, 75, c_amber, "#FEF3C7"),
        ("COURIER AT STORE\nt_arrived_store", 45, 52, c_indigo, "#EEF2FF"),
        ("PICKED UP\nt_picked_up", 70, 65, c_green, "#D1FAE5"),
        ("DELIVERED\nt_delivered", 88, 65, c_green, "#A7F3D0")
    ]

    for label, x, y, bc, fc in states:
        box = patches.FancyBboxPatch((x, y-5), 14, 10, boxstyle="round,pad=0.3",
                                     edgecolor=bc, facecolor=fc, linewidth=1.5)
        ax.add_patch(box)
        ax.text(x + 7, y, label, ha='center', va='center', fontsize=7.5, fontweight='bold', color=bc)

    # Connectors
    # Placed -> Confirmed
    ax.annotate('Stage 1:\nMerchant Lag\n(Mean: 1.1m)', xy=(23, 65), xytext=(19, 65),
                arrowprops=dict(facecolor=c_slate, edgecolor='none', width=1.5, headwidth=5),
                ha='center', va='bottom', fontsize=7, color=c_slate)

    # Confirmed -> Food Ready (Kitchen branch)
    ax.annotate('Stage 2: Kitchen Prep\nOverrun (+11.1m)', xy=(45, 75), xytext=(37, 68),
                arrowprops=dict(facecolor=c_amber, edgecolor='none', width=1.5, headwidth=5),
                ha='center', va='bottom', fontsize=7, color=c_amber, fontweight='bold')

    # Confirmed -> Courier Arrived (Dispatch branch)
    ax.annotate('Stage 3: Dispatch &\nRider Transit (8.2m)', xy=(45, 52), xytext=(37, 62),
                arrowprops=dict(facecolor=c_indigo, edgecolor='none', width=1.5, headwidth=5),
                ha='center', va='top', fontsize=7, color=c_indigo)

    # The Friction Nexus Box
    friction_box = patches.FancyBboxPatch((43, 44), 18, 44, boxstyle="round,pad=0.4",
                                          edgecolor=c_red, facecolor='#FEF2F2', linewidth=2, linestyle='--')
    ax.add_patch(friction_box)
    ax.text(52, 42, "THE SYNCHRONIZATION FRICTION NEXUS\nCourier arrives 15.8m BEFORE food ready!\n(Courier idles at store, burning active shift hours)",
            ha='center', va='top', fontsize=8, fontweight='bold', color=c_red)

    # Food Ready & Arrived -> Picked Up
    ax.annotate('', xy=(70, 67), xytext=(59, 75),
                arrowprops=dict(facecolor=c_slate, edgecolor='none', width=1.5, headwidth=5))
    ax.annotate('', xy=(70, 63), xytext=(59, 52),
                arrowprops=dict(facecolor=c_slate, edgecolor='none', width=1.5, headwidth=5))
    ax.text(64.5, 68, "Stage 4:\nStore Handoff\n(+15.8m Idle)", ha='center', va='bottom', fontsize=7, color=c_red, fontweight='bold')

    # Picked Up -> Delivered
    ax.annotate('Stage 5:\nLast-Mile\n(Mean: 12.4m)', xy=(88, 65), xytext=(84, 65),
                arrowprops=dict(facecolor=c_green, edgecolor='none', width=1.5, headwidth=5),
                ha='center', va='bottom', fontsize=7, color=c_green, fontweight='bold')

    # Cancelled Branch
    can_box = patches.FancyBboxPatch((23, 20), 14, 9, boxstyle="round,pad=0.3",
                                     edgecolor=c_red, facecolor="#FEE2E2", linewidth=1.5)
    ax.add_patch(can_box)
    ax.text(30, 24.5, "CANCELLED\nt_cancellation\n(4.8% Orders)", ha='center', va='center', fontsize=7.5, fontweight='bold', color=c_red)
    ax.annotate('Timeout / Out of Stock', xy=(30, 29), xytext=(30, 60),
                arrowprops=dict(facecolor=c_red, edgecolor='none', width=1.2, headwidth=4),
                ha='right', va='center', fontsize=6.5, color=c_red)

    # Bottom Takeaway Card
    sol_box = patches.FancyBboxPatch((5, 5), 90, 11, boxstyle="round,pad=0.4",
                                     edgecolor='#047857', facecolor='#ECFDF5', linewidth=1.5)
    ax.add_patch(sol_box)
    ax.text(50, 10.5, "FDE OPERATIONAL INTERVENTION: STAGED / OFFSET DISPATCH\n"
                      "Offset courier assignment by (Estimated Prep - Rider Travel Time). Courier reaches store 2 min before food ready,\n"
                      "reducing rider wait from 15.8m -> 3.2m, dropping SLA breach rate from 56.4% -> 6.6%, and unlocking +21.4% fleet capacity.",
            ha='center', va='center', fontsize=8, fontweight='bold', color='#047857')

    plt.tight_layout()
    plt.savefig("docs/workflow_fsm.png", bbox_inches='tight')
    plt.close()
    print("[+] Generated docs/workflow_fsm.png")

if __name__ == "__main__":
    generate_source_map()
    generate_workflow_fsm()
