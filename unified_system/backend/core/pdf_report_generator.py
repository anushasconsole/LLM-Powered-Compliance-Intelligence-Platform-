"""
PDF Report Generator for Compliance Audits
Generates audit-ready PDF reports with charts and tables
"""

from datetime import datetime
from typing import Dict, List, Any
import json


class PDFReportGenerator:
    """
    Generate PDF compliance reports.
    Falls back to HTML if PDF library not available.
    """
    
    def __init__(self):
        self.has_weasyprint = False
        self.has_reportlab = False
        
        try:
            from weasyprint import HTML
            self.has_weasyprint = True
            self.HTML = HTML
        except ImportError:
            pass
        
        try:
            from reportlab.lib.pagesizes import letter
            from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
            from reportlab.lib.styles import getSampleStyleSheet
            from reportlab.lib import colors
            self.has_reportlab = True
            self.reportlab_modules = {
                'letter': letter,
                'SimpleDocTemplate': SimpleDocTemplate,
                'Table': Table,
                'TableStyle': TableStyle,
                'Paragraph': Paragraph,
                'Spacer': Spacer,
                'PageBreak': PageBreak,
                'getSampleStyleSheet': getSampleStyleSheet,
                'colors': colors
            }
        except ImportError:
            pass
    
    def generate_html_report(self, data: Dict[str, Any]) -> str:
        """Generate HTML compliance report"""
        
        html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Compliance Audit Report</title>
    <style>
        body {{
            font-family: 'Arial', sans-serif;
            margin: 40px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: #333;
        }}
        .container {{
            background: white;
            padding: 40px;
            border-radius: 10px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.3);
        }}
        .header {{
            text-align: center;
            border-bottom: 3px solid #667eea;
            padding-bottom: 20px;
            margin-bottom: 30px;
        }}
        .header h1 {{
            color: #667eea;
            font-size: 36px;
            margin: 0;
        }}
        .header .subtitle {{
            color: #764ba2;
            font-size: 18px;
            margin-top: 10px;
        }}
        .section {{
            margin: 30px 0;
        }}
        .section h2 {{
            color: #667eea;
            border-bottom: 2px solid #764ba2;
            padding-bottom: 10px;
            margin-bottom: 20px;
        }}
        .metric {{
            display: inline-block;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 15px 25px;
            border-radius: 8px;
            margin: 10px;
            min-width: 200px;
            text-align: center;
        }}
        .metric-label {{
            font-size: 14px;
            opacity: 0.9;
        }}
        .metric-value {{
            font-size: 32px;
            font-weight: bold;
            margin-top: 5px;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
        }}
        th {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 12px;
            text-align: left;
            font-weight: bold;
        }}
        td {{
            padding: 12px;
            border-bottom: 1px solid #ddd;
        }}
        tr:hover {{
            background-color: #f5f5f5;
        }}
        .status-compliant {{
            background: #28a745;
            color: white;
            padding: 5px 15px;
            border-radius: 20px;
            font-weight: bold;
        }}
        .status-non-compliant {{
            background: #dc3545;
            color: white;
            padding: 5px 15px;
            border-radius: 20px;
            font-weight: bold;
        }}
        .gap-critical {{
            background: #dc3545;
            color: white;
            padding: 8px 15px;
            border-radius: 5px;
            margin: 10px 0;
        }}
        .gap-high {{
            background: #fd7e14;
            color: white;
            padding: 8px 15px;
            border-radius: 5px;
            margin: 10px 0;
        }}
        .gap-medium {{
            background: #ffc107;
            color: #333;
            padding: 8px 15px;
            border-radius: 5px;
            margin: 10px 0;
        }}
        .footer {{
            text-align: center;
            margin-top: 50px;
            padding-top: 20px;
            border-top: 2px solid #ddd;
            color: #666;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🔐 Compliance Audit Report</h1>
            <div class="subtitle">Enterprise Evidence Collection & Analysis</div>
            <div style="margin-top: 15px; color: #666;">
                Generated: {data.get('generated_at', datetime.now().strftime('%Y-%m-%d %H:%M:%S'))}
            </div>
        </div>
        
        <div class="section">
            <h2>📊 Executive Summary</h2>
            <div style="text-align: center;">
                <div class="metric">
                    <div class="metric-label">Overall Compliance</div>
                    <div class="metric-value">{data.get('overall_compliance', 0):.1%}</div>
                </div>
                <div class="metric">
                    <div class="metric-label">Total Evidence</div>
                    <div class="metric-value">{data.get('total_evidence', 0)}</div>
                </div>
                <div class="metric">
                    <div class="metric-label">Frameworks</div>
                    <div class="metric-value">{data.get('frameworks_covered', 0)}</div>
                </div>
                <div class="metric">
                    <div class="metric-label">Critical Findings</div>
                    <div class="metric-value">{data.get('critical_findings', 0)}</div>
                </div>
            </div>
        </div>
        
        <div class="section">
            <h2>🎯 Framework Compliance Scores</h2>
            <table>
                <thead>
                    <tr>
                        <th>Framework</th>
                        <th>Compliance Score</th>
                        <th>Evidence Count</th>
                        <th>Requirements</th>
                        <th>Status</th>
                    </tr>
                </thead>
                <tbody>
"""
        
        # Add framework scores
        for score in data.get('framework_scores', []):
            status_class = 'status-compliant' if score.get('status') == 'COMPLIANT' else 'status-non-compliant'
            html += f"""
                    <tr>
                        <td><strong>{score.get('framework', 'N/A')}</strong></td>
                        <td>{score.get('overall_confidence', 0):.1%}</td>
                        <td>{score.get('requirements_with_evidence', 0)}</td>
                        <td>{score.get('requirements_total', 0)}</td>
                        <td><span class="{status_class}">{score.get('status', 'UNKNOWN')}</span></td>
                    </tr>
"""
        
        html += """
                </tbody>
            </table>
        </div>
"""
        
        # Add findings if available
        if data.get('findings'):
            html += """
        <div class="section">
            <h2>🔴 Critical Audit Findings</h2>
"""
            for finding in data.get('findings', [])[:10]:  # Top 10 findings
                severity = finding.get('severity', 'MEDIUM')
                gap_class = f'gap-{severity.lower()}'
                html += f"""
            <div class="{gap_class}">
                <strong>{finding.get('finding_type', 'Unknown')}</strong> ({severity})<br>
                Requirement: {finding.get('requirement_id', 'N/A')}<br>
                {finding.get('description', 'No description')}<br>
                <em>→ Remediation: {finding.get('remediation', 'No recommendation')}</em>
            </div>
"""
            html += """
        </div>
"""
        
        html += f"""
        <div class="section">
            <h2>📋 Recommendations</h2>
            <p><strong>Audit Status:</strong> {data.get('status', 'UNKNOWN')}</p>
            <ul>
                <li>Address all CRITICAL findings immediately before external audit</li>
                <li>Refresh stale evidence (>90 days old) through re-testing</li>
                <li>Strengthen low-confidence evidence with additional corroboration</li>
                <li>Complete pending evidence reviews within 30 days</li>
                <li>Implement automated evidence collection for continuous compliance</li>
            </ul>
        </div>
        
        <div class="footer">
            <p><strong>Compliance Auditor Pro</strong> © 2026</p>
            <p>Enterprise Evidence Collection & Adversarial Auditing System</p>
            <p style="font-size: 12px; margin-top: 10px;">
                This report is confidential and intended solely for authorized personnel.
            </p>
        </div>
    </div>
</body>
</html>
"""
        return html
    
    def save_html_report(self, data: Dict[str, Any], filename: str = 'compliance_report.html'):
        """Save HTML report to file"""
        html = self.generate_html_report(data)
        
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(html)
        
        return filename
    
    def save_pdf_report(self, data: Dict[str, Any], filename: str = 'compliance_report.pdf'):
        """Save PDF report (using HTML to PDF conversion if available)"""
        
        if self.has_weasyprint:
            html = self.generate_html_report(data)
            self.HTML(string=html).write_pdf(filename)
            return filename
        elif self.has_reportlab:
            return self._generate_reportlab_pdf(data, filename)
        else:
            # Fallback to HTML
            html_file = filename.replace('.pdf', '.html')
            self.save_html_report(data, html_file)
            print(f"⚠️  PDF libraries not available. Generated HTML report: {html_file}")
            print("   Install: pip install weasyprint  OR  pip install reportlab")
            return html_file
    
    def _generate_reportlab_pdf(self, data: Dict[str, Any], filename: str) -> str:
        """Generate PDF using ReportLab (fallback method)"""
        
        rl = self.reportlab_modules
        doc = rl['SimpleDocTemplate'](filename, pagesize=rl['letter'])
        styles = rl['getSampleStyleSheet']()
        story = []
        
        # Title
        title = rl['Paragraph'](
            "<font size=24><b>Compliance Audit Report</b></font>",
            styles['Title']
        )
        story.append(title)
        story.append(rl['Spacer'](1, 20))
        
        # Executive Summary
        story.append(rl['Paragraph']("<font size=16><b>Executive Summary</b></font>", styles['Heading1']))
        story.append(rl['Spacer'](1, 12))
        
        summary_text = f"""
        <b>Generated:</b> {data.get('generated_at', datetime.now().strftime('%Y-%m-%d'))}<br/>
        <b>Overall Compliance:</b> {data.get('overall_compliance', 0):.1%}<br/>
        <b>Total Evidence:</b> {data.get('total_evidence', 0)}<br/>
        <b>Frameworks Covered:</b> {data.get('frameworks_covered', 0)}<br/>
        <b>Critical Findings:</b> {data.get('critical_findings', 0)}<br/>
        <b>Status:</b> {data.get('status', 'UNKNOWN')}
        """
        story.append(rl['Paragraph'](summary_text, styles['Normal']))
        story.append(rl['Spacer'](1, 20))
        
        # Framework Scores Table
        story.append(rl['Paragraph']("<font size=16><b>Framework Scores</b></font>", styles['Heading1']))
        story.append(rl['Spacer'](1, 12))
        
        table_data = [['Framework', 'Compliance', 'Evidence', 'Requirements', 'Status']]
        for score in data.get('framework_scores', []):
            table_data.append([
                score.get('framework', 'N/A'),
                f"{score.get('overall_confidence', 0):.1%}",
                str(score.get('requirements_with_evidence', 0)),
                str(score.get('requirements_total', 0)),
                score.get('status', 'UNKNOWN')
            ])
        
        table = rl['Table'](table_data)
        table.setStyle(rl['TableStyle']([
            ('BACKGROUND', (0, 0), (-1, 0), rl['colors'].purple),
            ('TEXTCOLOR', (0, 0), (-1, 0), rl['colors'].whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), rl['colors'].beige),
            ('GRID', (0, 0), (-1, -1), 1, rl['colors'].black)
        ]))
        story.append(table)
        
        # Build PDF
        doc.build(story)
        return filename


def demo_pdf_generator():
    """Demo the PDF report generator"""
    
    # Sample data
    sample_data = {
        'generated_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'overall_compliance': 0.73,
        'total_evidence': 500,
        'frameworks_covered': 6,
        'critical_findings': 12,
        'status': 'PASS_WITH_CONCERNS',
        'framework_scores': [
            {'framework': 'GDPR', 'overall_confidence': 0.75, 'requirements_with_evidence': 15, 'requirements_total': 18, 'status': 'COMPLIANT'},
            {'framework': 'SOX', 'overall_confidence': 0.68, 'requirements_with_evidence': 12, 'requirements_total': 15, 'status': 'NON_COMPLIANT'},
            {'framework': 'NIST', 'overall_confidence': 0.72, 'requirements_with_evidence': 20, 'requirements_total': 25, 'status': 'COMPLIANT'},
            {'framework': 'PCI-DSS', 'overall_confidence': 0.79, 'requirements_with_evidence': 18, 'requirements_total': 20, 'status': 'COMPLIANT'},
            {'framework': 'HIPAA', 'overall_confidence': 0.71, 'requirements_with_evidence': 10, 'requirements_total': 12, 'status': 'COMPLIANT'},
            {'framework': 'ISO27001', 'overall_confidence': 0.74, 'requirements_with_evidence': 22, 'requirements_total': 28, 'status': 'COMPLIANT'},
        ],
        'findings': [
            {
                'finding_type': 'Stale Evidence',
                'severity': 'CRITICAL',
                'requirement_id': 'REQ-001',
                'description': '15 evidence items >180 days old',
                'remediation': 'Refresh through re-testing'
            },
            {
                'finding_type': 'Low Confidence',
                'severity': 'HIGH',
                'requirement_id': 'REQ-005',
                'description': '8 items <50% confidence',
                'remediation': 'Strengthen evidence quality'
            }
        ]
    }
    
    generator = PDFReportGenerator()
    
    # Generate HTML report
    html_file = generator.save_html_report(sample_data, 'compliance_report.html')
    print(f"✅ HTML report generated: {html_file}")
    
    # Try to generate PDF
    pdf_file = generator.save_pdf_report(sample_data, 'compliance_report.pdf')
    print(f"✅ Report generated: {pdf_file}")


if __name__ == '__main__':
    demo_pdf_generator()
