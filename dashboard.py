"""
Dashboard Generator - Interactive HTML compliance dashboard for Option A
Reads from the LLM-Powered Compliance Intelligence Platform JSON report
"""
import json
import os
from datetime import datetime


def load_option_a_report(report_path="reports/audit_report_option_a.json"):
    """Load the Option A compliance report from JSON"""
    if not os.path.exists(report_path):
        print(f"Warning: Report file not found at {report_path}")
        return None
    
    with open(report_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def build_dashboard_data_option_a(report):
    """Build dashboard data from Option A JSON report"""
    
    if not report:
        return None
    
    # Extract key data from report
    findings = []
    for req in report.get('requirements', []):
        findings.append({
            "req_id": req['requirement_id'],
            "req_text": req['requirement_text'],
            "status": req['status'],
            "confidence": round(req['confidence'] * 100),
            "summary": req['summary'],
            "narrative": req.get('narrative', ''),
            "risk": req.get('risk', 'MEDIUM RISK'),
            "recommendation": req.get('recommendation', ''),
            "frameworks": req.get('frameworks', []),
        })
    
    # Framework compliance data
    fw_data = []
    for fw_name, fw_stats in report.get('frameworks', {}).items():
        fw_data.append({
            "name": fw_name,
            "with_evidence": fw_stats['with_evidence'],
            "total": fw_stats['total_requirements'],
            "coverage": round(fw_stats['coverage_percent']),
        })
    
    # Build summary
    exec_summary = report.get('executive_summary', {})
    total_reqs = exec_summary.get('total_requirements', 0)
    
    return {
        "findings": findings,
        "framework_data": fw_data,
        "summary": {
            "total_requirements": total_reqs,
            "compliant": exec_summary.get('compliant', 0),
            "conditional": exec_summary.get('conditional', 0),
            "non_compliant": exec_summary.get('non_compliant', 0),
            "compliance_percentage": round(exec_summary.get('compliance_percentage', 0)),
            "audit_ready": exec_summary.get('audit_ready', False),
        },
        "generated_at": report.get('generated_at', ''),
    }


def generate_dashboard_html(data):
    """Generate HTML dashboard from data"""
    
    if not data:
        html = """
        <html><head><title>Compliance Dashboard</title>
        <style>body{font-family:Arial;margin:20px;}</style>
        </head><body>
        <h1>Compliance Dashboard</h1>
        <p style="color:red;">Error: No report data available. Run solution_option_a.py first.</p>
        </body></html>
        """
        return html
    
    summary = data['summary']
    
    # Build findings HTML
    findings_html = ""
    for finding in data['findings']:
        confidence_color = "green" if finding['confidence'] >= 80 else "orange" if finding['confidence'] >= 50 else "red"
        status_color = {
            "COMPLIANT": "#4CAF50",
            "CONDITIONAL": "#FF9800", 
            "NON_COMPLIANT": "#F44336",
            "AT_RISK": "#FF5722"
        }.get(finding['status'], "#666")
        
        findings_html += f"""
        <div style="border-left: 4px solid {status_color}; margin: 15px 0; padding: 20px; background: #f9f9f9; border-radius: 5px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
            <h4 style="color: #333; margin: 0 0 10px 0;">{finding['req_id']}</h4>
            <p style="color: #555; margin: 8px 0; font-weight: 500;">{finding['req_text']}</p>
            <div style="display: grid; grid-template-columns: repeat(4, 1fr); gap: 15px; margin: 15px 0;">
                <div>
                    <span style="color: #888; font-size: 12px;">Status</span><br>
                    <span style="color: {status_color}; font-weight: bold; font-size: 14px;">{finding['status']}</span>
                </div>
                <div>
                    <span style="color: #888; font-size: 12px;">Confidence</span><br>
                    <span style="color: {confidence_color}; font-weight: bold; font-size: 14px;">{finding['confidence']}%</span>
                </div>
                <div>
                    <span style="color: #888; font-size: 12px;">Frameworks</span><br>
                    <span style="font-size: 12px;">{', '.join(finding.get('frameworks', []))}</span>
                </div>
                <div>
                    <span style="color: #888; font-size: 12px;">Risk</span><br>
                    <span style="font-size: 12px;">{finding['risk'].split(':')[0]}</span>
                </div>
            </div>
            <p style="color: #666; margin: 10px 0; font-style: italic; border-top: 1px solid #eee; padding-top: 10px;">
                <strong>Summary:</strong> {finding['summary']}
            </p>
            <p style="color: #555; margin: 10px 0; line-height: 1.6;">
                <strong>Assessment:</strong> {finding['narrative'][:200]}...
            </p>
            <p style="color: #666; margin: 10px 0;">
                <strong>Recommendation:</strong> {finding['recommendation']}
            </p>
        </div>
        """
    
    # Build framework table
    framework_html = """
    <table style="width:100%; border-collapse: collapse; margin: 20px 0; box-shadow: 0 2px 4px rgba(0,0,0,0.1); border-radius: 5px; overflow: hidden;">
        <thead style="background-color: #667eea; color: white;">
            <tr>
                <th style="padding:15px; text-align:left; font-weight:600;">Framework</th>
                <th style="padding:15px; text-align:center; font-weight:600;">With Evidence</th>
                <th style="padding:15px; text-align:center; font-weight:600;">Total</th>
                <th style="padding:15px; text-align:center; font-weight:600;">Coverage</th>
            </tr>
        </thead>
        <tbody>
    """
    
    for fw in data['framework_data']:
        coverage_color = "green" if fw['coverage'] >= 80 else "orange" if fw['coverage'] >= 50 else "red"
        framework_html += f"""
            <tr style="border-bottom: 1px solid #eee; background: #fafafa;">
                <td style="padding:12px 15px;">{fw['name']}</td>
                <td style="padding:12px 15px; text-align:center;">{fw['with_evidence']}</td>
                <td style="padding:12px 15px; text-align:center;">{fw['total']}</td>
                <td style="padding:12px 15px; text-align:center;">
                    <span style="color: {coverage_color}; font-weight: bold;">{fw['coverage']}%</span>
                </td>
            </tr>
        """
    
    framework_html += """
        </tbody>
    </table>
    """
    
    # Calculate metrics
    compliant_pct = round(summary['compliant'] / summary['total_requirements'] * 100) if summary['total_requirements'] > 0 else 0
    avg_confidence = round((summary['compliant'] * 100 + summary['conditional'] * 50) / summary['total_requirements']) if summary['total_requirements'] > 0 else 0
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Compliance Intelligence Dashboard - Option A</title>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <style>
            * {{
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }}
            
            body {{
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
                padding: 20px;
                color: #333;
            }}
            
            .container {{
                max-width: 1400px;
                margin: 0 auto;
                background: white;
                border-radius: 12px;
                box-shadow: 0 20px 60px rgba(0,0,0,0.3);
                padding: 40px;
            }}
            
            header {{
                border-bottom: 3px solid #667eea;
                padding-bottom: 20px;
                margin-bottom: 30px;
            }}
            
            h1 {{
                color: #333;
                font-size: 32px;
                margin-bottom: 5px;
            }}
            
            .subtitle {{
                color: #888;
                font-size: 14px;
                margin-top: 10px;
            }}
            
            .summary-grid {{
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
                gap: 20px;
                margin: 30px 0;
            }}
            
            .summary-card {{
                padding: 25px;
                border-radius: 10px;
                text-align: center;
                box-shadow: 0 4px 15px rgba(0,0,0,0.08);
                border-top: 4px solid;
            }}
            
            .card-compliant {{
                background: linear-gradient(135deg, #e8f5e9 0%, #c8e6c9 100%);
                border-top-color: #4CAF50;
            }}
            
            .card-conditional {{
                background: linear-gradient(135deg, #fff3e0 0%, #ffe0b2 100%);
                border-top-color: #FF9800;
            }}
            
            .card-noncompliant {{
                background: linear-gradient(135deg, #ffebee 0%, #ffcdd2 100%);
                border-top-color: #F44336;
            }}
            
            .card-audit {{
                background: linear-gradient(135deg, #e3f2fd 0%, #bbdefb 100%);
                border-top-color: #2196F3;
            }}
            
            .summary-card h3 {{
                font-size: 13px;
                color: #666;
                margin-bottom: 10px;
                font-weight: 500;
                text-transform: uppercase;
                letter-spacing: 0.5px;
            }}
            
            .summary-card .value {{
                font-size: 42px;
                font-weight: bold;
                color: #333;
            }}
            
            .section {{
                margin: 40px 0;
            }}
            
            .section h2 {{
                color: #333;
                font-size: 24px;
                margin-bottom: 20px;
                border-left: 4px solid #667eea;
                padding-left: 15px;
                font-weight: 600;
            }}
            
            footer {{
                margin-top: 50px;
                padding-top: 20px;
                border-top: 1px solid #eee;
                color: #999;
                font-size: 12px;
                text-align: center;
            }}
            
            @media (max-width: 768px) {{
                .container {{
                    padding: 20px;
                }}
                
                h1 {{
                    font-size: 24px;
                }}
                
                .summary-grid {{
                    grid-template-columns: repeat(2, 1fr);
                }}
                
                .summary-card .value {{
                    font-size: 32px;
                }}
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <header>
                <h1>🔐 Compliance Intelligence Dashboard</h1>
                <div class="subtitle">Option A: LLM-Powered Compliance Assessment Platform</div>
                <div class="subtitle">Generated: {data['generated_at']}</div>
            </header>
            
            <div class="summary-grid">
                <div class="summary-card card-compliant">
                    <h3>✓ Compliant</h3>
                    <div class="value">{summary['compliant']}</div>
                </div>
                <div class="summary-card card-conditional">
                    <h3>⚠ Conditional</h3>
                    <div class="value">{summary['conditional']}</div>
                </div>
                <div class="summary-card card-noncompliant">
                    <h3>✕ Non-Compliant</h3>
                    <div class="value">{summary['non_compliant']}</div>
                </div>
                <div class="summary-card card-audit">
                    <h3>Overall Compliance</h3>
                    <div class="value">{summary['compliance_percentage']}%</div>
                </div>
            </div>
            
            <div class="section">
                <h2>Framework Compliance Coverage</h2>
                {framework_html}
            </div>
            
            <div class="section">
                <h2>Requirement Assessment Details ({len(data['findings'])} requirements)</h2>
                {findings_html}
            </div>
            
            <footer>
                <p>🚀 Compliance Intelligence Platform v1.0 | Option A: LLM-Powered Assessment with Semantic Matching</p>
                <p>Report Generated: {data['generated_at']}</p>
            </footer>
        </div>
    </body>
    </html>
    """
    
    return html


def main():
    """Generate and save dashboard"""
    print("=" * 70)
    print("DASHBOARD GENERATOR - Option A Compliance Intelligence Platform")
    print("=" * 70)
    
    print("\n[1] Loading Option A compliance report...")
    report = load_option_a_report()
    
    if not report:
        print("ERROR: Could not load Option A report.")
        print("Please run: python solution_option_a.py")
        return
    
    print(f"    ✓ Loaded report generated at: {report.get('generated_at', 'unknown')}")
    
    print("\n[2] Building dashboard data...")
    data = build_dashboard_data_option_a(report)
    
    if not data:
        print("ERROR: Could not build dashboard data.")
        return
    
    print(f"    ✓ Found {data['summary']['total_requirements']} requirements")
    print(f"    ✓ Found {len(data['framework_data'])} frameworks")
    
    print("\n[3] Generating dashboard HTML...")
    html = generate_dashboard_html(data)
    
    # Save to file
    dashboard_path = "reports/dashboard.html"
    os.makedirs("reports", exist_ok=True)
    
    with open(dashboard_path, 'w', encoding='utf-8') as f:
        f.write(html)
    
    print(f"    ✓ Dashboard saved to: {dashboard_path}")
    
    print("\n" + "=" * 70)
    print("DASHBOARD SUMMARY")
    print("=" * 70)
    print(f"Total Requirements:    {data['summary']['total_requirements']}")
    print(f"Compliant:             {data['summary']['compliant']}")
    print(f"Conditional:           {data['summary']['conditional']}")
    print(f"Non-Compliant:         {data['summary']['non_compliant']}")
    print(f"Overall Compliance:    {data['summary']['compliance_percentage']}%")
    print(f"Audit Ready:           {'YES ✓' if data['summary']['audit_ready'] else 'NO (gaps remain)'}")
    
    print("\nFramework Coverage:")
    for fw in data['framework_data']:
        print(f"  {fw['name']:15} {fw['with_evidence']:2}/{fw['total']:2} ({fw['coverage']:3}%)")
    
    print("\n" + "=" * 70)
    print(f"📊 Open Dashboard: {os.path.abspath(dashboard_path)}")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    main()
