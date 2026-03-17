"""
services/pdf_service.py
Generates treatment plan PDFs using WeasyPrint.
"""
from __future__ import annotations

from datetime import datetime
from typing import Any

try:
    from weasyprint import HTML, CSS
    _WEASYPRINT_AVAILABLE = True
except Exception:
    _WEASYPRINT_AVAILABLE = False


_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8" />
<style>
  body {{ font-family: 'Helvetica Neue', Arial, sans-serif; color: #1a1a2e; padding: 40px; font-size: 12px; }}
  h1 {{ color: #0F3460; font-size: 22px; margin-bottom: 4px; }}
  h2 {{ color: #0891B2; font-size: 15px; border-bottom: 2px solid #0891B2; padding-bottom: 4px; margin-top: 24px; }}
  .header {{ display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 32px; }}
  .logo {{ font-size: 18px; font-weight: bold; color: #0F3460; }}
  .logo span {{ color: #0891B2; }}
  .meta-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 8px; background: #f8fafc; padding: 16px; border-radius: 8px; margin-top: 8px; }}
  .meta-item label {{ font-weight: 600; font-size: 10px; color: #64748b; text-transform: uppercase; }}
  .meta-item p {{ margin: 2px 0; font-size: 12px; }}
  .rec-card {{ border-left: 4px solid #0891B2; background: #f0f9ff; padding: 14px 16px; margin: 10px 0; border-radius: 4px; }}
  .rec-rank {{ font-size: 10px; font-weight: 700; color: #0891B2; text-transform: uppercase; }}
  .rec-name {{ font-size: 14px; font-weight: bold; margin: 4px 0; }}
  .drug-list {{ font-size: 11px; color: #475569; font-style: italic; }}
  .alert-card {{ border-left: 4px solid #e11d48; background: #fff1f2; padding: 12px 16px; margin: 8px 0; border-radius: 4px; }}
  .alert-high {{ border-color: #e11d48; background: #fff1f2; }}
  .alert-medium {{ border-color: #d97706; background: #fffbeb; }}
  .alert-low {{ border-color: #059669; background: #f0fdf4; }}
  .severity {{ font-size: 10px; font-weight: 700; text-transform: uppercase; }}
  .trace-row {{ display: flex; gap: 12px; padding: 6px 0; border-bottom: 1px solid #e2e8f0; font-size: 11px; }}
  .trace-label {{ font-weight: 600; width: 120px; color: #475569; }}
  .footer {{ margin-top: 40px; font-size: 9px; color: #94a3b8; text-align: center; border-top: 1px solid #e2e8f0; padding-top: 12px; }}
  .subtype-badge {{ display: inline-block; background: #0891B2; color: white; padding: 6px 16px; border-radius: 20px; font-weight: bold; font-size: 14px; margin: 8px 0; }}
  .confidence {{ font-size: 11px; color: #64748b; margin-top: 4px; }}
</style>
</head>
<body>
<div class="header">
  <div class="logo">On<span>Copilot</span> — Clinical Report</div>
  <div style="text-align:right; font-size:10px; color:#94a3b8;">
    Generated: {generated_at}<br/>
    Physician: Dr. {doctor_name}
  </div>
</div>

<h2>Patient Information</h2>
<div class="meta-grid">
  <div class="meta-item"><label>Patient Name</label><p>{patient_name}</p></div>
  <div class="meta-item"><label>Age</label><p>{patient_age}</p></div>
  <div class="meta-item"><label>Case ID</label><p>{case_id}</p></div>
  <div class="meta-item"><label>Stage</label><p>{stage}</p></div>
  <div class="meta-item"><label>Grade</label><p>{grade}</p></div>
  <div class="meta-item"><label>Histological Type</label><p>{histological_type}</p></div>
</div>

<h2>Molecular Classification</h2>
<p>AI-generated classification based on {marker_count} biomarkers.</p>
<div class="subtype-badge">{molecular_subtype}</div>
<div class="confidence">Confidence: {confidence}%</div>

<h2>ER / PR / HER2 / Ki-67 Profile</h2>
<div class="meta-grid">
  <div class="meta-item"><label>ER Status</label><p>{er_status}</p></div>
  <div class="meta-item"><label>PR Status</label><p>{pr_status}</p></div>
  <div class="meta-item"><label>HER2 Status</label><p>{her2_status}</p></div>
  <div class="meta-item"><label>Ki-67</label><p>{ki67}</p></div>
  <div class="meta-item"><label>BRCA1</label><p>{brca1}</p></div>
  <div class="meta-item"><label>BRCA2</label><p>{brca2}</p></div>
</div>

<h2>Treatment Recommendations</h2>
{recommendations_html}

{alerts_html}

<h2>Clinical Rule Trace</h2>
{rule_trace_html}

<div class="footer">
  OnCopilot — Clinical Decision Support System | This report is for physician use only and does not constitute a standalone medical prescription.
  Treatment decisions remain the sole responsibility of the treating physician. Generated: {generated_at}
</div>
</body>
</html>
"""


def _rec_html(recs: list[dict]) -> str:
    parts = []
    for r in recs:
        drugs = ", ".join(r.get("drug_names", []))
        parts.append(f"""
<div class="rec-card">
  <div class="rec-rank">#{r.get('rank', '?')} — {r.get('guideline_source','')}</div>
  <div class="rec-name">{r.get('protocol_name','')}</div>
  <div class="drug-list">Drugs: {drugs}</div>
  <div style="font-size:11px; color:#475569; margin-top:6px;">Duration: {r.get('duration_months','?')} months | Confidence: {int((r.get('confidence_score',0))*100)}%</div>
  <div style="font-size:11px; margin-top:6px;">{r.get('clinical_notes','')}</div>
</div>""")
    return "\n".join(parts)


def _alert_html(alerts: list[dict]) -> str:
    if not alerts:
        return ""
    parts = ["<h2>Safety Alerts</h2>"]
    for a in alerts:
        severity = a.get("severity", "LOW")
        cls = f"alert-{severity.lower()}"
        parts.append(f"""
<div class="alert-card {cls}">
  <div class="severity">{severity} — {a.get('alert_type','')}</div>
  <div style="margin-top:4px;"><strong>Trigger:</strong> {a.get('trigger','')}</div>
  <div><strong>Affected:</strong> {a.get('affected_treatment','')}</div>
  <div style="color:#64748b; margin-top:4px;">{a.get('recommended_action','')}</div>
</div>""")
    return "\n".join(parts)


def _trace_html(trace: list[dict]) -> str:
    parts = []
    for t in trace:
        lbl = t.get("label", t.get("biomarker", ""))
        val = t.get("value", "")
        conclusion = t.get("conclusion", t.get("implication", ""))
        parts.append(f'<div class="trace-row"><div class="trace-label">{lbl}: {val}</div><div>{conclusion}</div></div>')
    return "\n".join(parts)


def generate_pdf(data: dict[str, Any]) -> bytes:
    """
    Generates a treatment plan PDF.
    data keys: patient_name, patient_age, case_id, doctor_name,
                clinical_data(dict), result(dict)
    """
    cd = data.get("clinical_data") or {}
    result = data.get("result") or {}
    recs = result.get("recommendations", [])
    alerts = result.get("alerts", [])
    trace = result.get("rule_trace", [])
    conf = result.get("subtype_confidence", 0)

    html_content = _TEMPLATE.format(
        generated_at=datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC"),
        doctor_name=data.get("doctor_name", "Unknown"),
        patient_name=data.get("patient_name", "N/A"),
        patient_age=data.get("patient_age", "N/A"),
        case_id=str(data.get("case_id", "")),
        stage=cd.get("stage", "N/A"),
        grade=cd.get("grade", "N/A"),
        histological_type=cd.get("histological_type", "N/A"),
        molecular_subtype=result.get("molecular_subtype", "N/A"),
        confidence=round(conf * 100, 1),
        marker_count=16,
        er_status=cd.get("er_status", "Unknown"),
        pr_status=cd.get("pr_status", "Unknown"),
        her2_status=cd.get("her2_status", "Unknown"),
        ki67=f"{cd.get('ki67_percent', 'N/A')}%" if cd.get("ki67_percent") else "N/A",
        brca1=cd.get("brca1_status", "Unknown"),
        brca2=cd.get("brca2_status", "Unknown"),
        recommendations_html=_rec_html(recs),
        alerts_html=_alert_html(alerts),
        rule_trace_html=_trace_html(trace),
    )

    if not _WEASYPRINT_AVAILABLE:
        # Return HTML as bytes if WeasyPrint not installed
        return html_content.encode("utf-8")

    return HTML(string=html_content).write_pdf()
