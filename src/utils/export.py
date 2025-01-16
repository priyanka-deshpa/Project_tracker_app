import streamlit as st
from datetime import datetime
import pandas as pd
import io
import base64
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, landscape
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
import plotly.express as px

def create_project_status_data(projects, issues):
    """Create project status data for export."""
    data = []
    for project in projects:
        project_issues = [i for i in issues if i['project'] == project['name']]
        total_issues = len(project_issues)
        completed_issues = len([i for i in project_issues if i['status'] == 'Completed'])
        completion_pct = (completed_issues / total_issues * 100) if total_issues > 0 else 100
        
        health = 'Healthy' if completion_pct >= 80 else 'At Risk' if completion_pct >= 60 else 'Critical'
        
        data.append({
            'Project Name': project['name'],
            'Team Size': len(project['developers']),
            'Team Leads': ', '.join(project['leads']),
            'Total Issues': total_issues,
            'Completed Issues': completed_issues,
            'Completion %': f"{completion_pct:.1f}%",
            'Health Status': health
        })
    return data

def export_to_excel(projects, issues):
    """Export project data to Excel."""
    output = io.BytesIO()
    
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        # Project Status sheet
        project_data = pd.DataFrame(create_project_status_data(projects, issues))
        project_data.to_excel(writer, sheet_name='Project Status', index=False)
        
        # Issues sheet
        issues_data = pd.DataFrame([{
            'Project': issue['project'],
            'Title': issue['title'],
            'Description': issue['description'],
            'Status': issue['status'],
            'Created At': issue['created_at']
        } for issue in issues])
        issues_data.to_excel(writer, sheet_name='Issues', index=False)
        
        # Format the sheets
        for sheet_name in writer.sheets:
            worksheet = writer.sheets[sheet_name]
            for column in worksheet.columns:
                max_length = 0
                column = [cell for cell in column]
                for cell in column:
                    try:
                        if len(str(cell.value)) > max_length:
                            max_length = len(cell.value)
                    except:
                        pass
                adjusted_width = (max_length + 2)
                worksheet.column_dimensions[column[0].column_letter].width = adjusted_width
    
    return output.getvalue()

def export_to_pdf(projects, issues):
    """Export dashboard report to PDF."""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=landscape(letter))
    styles = getSampleStyleSheet()
    elements = []
    
    # Title
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        spaceAfter=30,
        alignment=1
    )
    elements.append(Paragraph('Project Dashboard Report', title_style))
    elements.append(Paragraph(f'Generated on {datetime.now().strftime("%Y-%m-%d %H:%M")}', 
                            styles['Normal']))
    elements.append(Spacer(1, 20))
    
    # Project Status Table
    project_data = create_project_status_data(projects, issues)
    if project_data:
        elements.append(Paragraph('Project Status Summary', styles['Heading2']))
        elements.append(Spacer(1, 10))
        
        # Convert data to table format
        table_data = [[k for k in project_data[0].keys()]]
        for item in project_data:
            table_data.append([str(v) for v in item.values()])
        
        table = Table(table_data)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.white),
            ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 10),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        elements.append(table)
    
    # Build PDF
    doc.build(elements)
    return buffer.getvalue()

def get_download_link(data, filename, text):
    """Generate a download link for a file."""
    b64 = base64.b64encode(data).decode()
    mime_type = {
        'xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        'pdf': 'application/pdf'
    }.get(filename.split('.')[-1], 'application/octet-stream')
    href = f'<a href="data:{mime_type};base64,{b64}" download="{filename}">{text}</a>'
    return href

def render_export_section(projects, issues):
    """Render the export section in the dashboard."""
    st.markdown("### Export Options")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("📊 Export to Excel"):
            with st.spinner("Generating Excel report..."):
                try:
                    excel_data = export_to_excel(projects, issues)
                    filename = f"project_status_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx"
                    st.markdown(
                        get_download_link(excel_data, filename, "📥 Download Excel Report"),
                        unsafe_allow_html=True
                    )
                    st.success("Excel report generated successfully!")
                except Exception as e:
                    st.error(f"Failed to generate Excel report: {str(e)}")
    
    with col2:
        if st.button("📄 Export to PDF"):
            with st.spinner("Generating PDF report..."):
                try:
                    pdf_data = export_to_pdf(projects, issues)
                    filename = f"project_status_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf"
                    st.markdown(
                        get_download_link(pdf_data, filename, "📥 Download PDF Report"),
                        unsafe_allow_html=True
                    )
                    st.success("PDF report generated successfully!")
                except Exception as e:
                    st.error(f"Failed to generate PDF report: {str(e)}")