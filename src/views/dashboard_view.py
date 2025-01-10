import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
from src.storage import load_data

def calculate_project_health(project, issues):
    """Calculate project health based on various metrics."""
    project_issues = [i for i in issues if i['project'] == project['name']]
    total_issues = len(project_issues)
    completed_issues = len([i for i in project_issues if i['status'] == 'Completed'])
    
    # Calculate completion percentage
    completion_pct = (completed_issues / total_issues * 100) if total_issues > 0 else 100
    
    # Determine health status
    if completion_pct >= 80:
        return "Healthy", "🟢", completion_pct
    elif completion_pct >= 60:
        return "At Risk", "🟡", completion_pct
    else:
        return "Critical", "🔴", completion_pct

def render_dashboard():
    st.title("Project Health Dashboard")
    
    # Load data
    projects, issues = load_data()
    
    if not projects:
        st.info("No projects available to display.")
        return
    
    # Filters sidebar
    st.sidebar.header("Filters")
    
    # Filter by health status
    health_filter = st.sidebar.multiselect(
        "Health Status",
        ["Healthy", "At Risk", "Critical"],
        default=["Healthy", "At Risk", "Critical"]
    )
    
    # Filter by team lead
    all_leads = list(set([lead for p in projects for lead in p['leads']]))
    lead_filter = st.sidebar.multiselect(
        "Team Lead",
        all_leads,
        default=all_leads
    )
    
    # Apply filters
    filtered_projects = [
        p for p in projects
        if any(lead in lead_filter for lead in p['leads'])
    ]
    
    # Overview metrics
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Total Projects", len(filtered_projects))
    with col2:
        total_devs = sum(len(p['developers']) for p in filtered_projects)
        st.metric("Total Developers", total_devs)
    with col3:
        total_issues = len([i for i in issues if i['project'] in [p['name'] for p in filtered_projects]])
        st.metric("Total Issues", total_issues)
    
    # Project Health Summary
    st.subheader("Project Health Summary")
    
    for project in filtered_projects:
        health_status, health_icon, completion_pct = calculate_project_health(project, issues)
        
        # Skip if filtered out by health status
        if health_status not in health_filter:
            continue
        
        with st.expander(f"{health_icon} {project['name']} - {health_status}"):
            col1, col2 = st.columns([2, 1])
            
            with col1:
                # Project details
                st.markdown(f"**Team Size:** {len(project['developers'])}")
                st.markdown(f"**Leads:** {', '.join(project['leads'])}")
                
                # Progress bar
                st.progress(completion_pct / 100)
                st.markdown(f"**Completion:** {completion_pct:.1f}%")
                
                # Issue statistics
                project_issues = [i for i in issues if i['project'] == project['name']]
                completed = len([i for i in project_issues if i['status'] == 'Completed'])
                pending = len([i for i in project_issues if i['status'] == 'Pending'])
                
                st.markdown(f"""
                **Issues:**
                - Completed: {completed}
                - Pending: {pending}
                - Total: {len(project_issues)}
                """)
            
            with col2:
                # Quick actions
                if st.button("View Details", key=f"view_{project['name']}"):
                    st.session_state.selected_project = project['name']
                    st.session_state.page = 'project_details'
                    st.rerun()
                
                if st.button("View Issues", key=f"issues_{project['name']}"):
                    st.session_state.selected_project = project['name']
                    st.session_state.page = 'issues'
                    st.rerun()
    
    # Overall Statistics
    st.subheader("Overall Statistics")
    
    # Calculate statistics
    total_completed = len([i for i in issues if i['status'] == 'Completed'])
    total_pending = len([i for i in issues if i['status'] == 'Pending'])
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Pie chart for issue status using plotly
        st.markdown("### Issue Status Distribution")
        if total_completed + total_pending > 0:  # Only show chart if there are issues
            issue_data = pd.DataFrame({
                'Status': ['Completed', 'Pending'],
                'Count': [total_completed, total_pending]
            })
            fig = px.pie(issue_data, values='Count', names='Status', 
                        title='Issue Distribution',
                        color_discrete_sequence=['#28a745', '#ffc107'])
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No issues to display")
    
    with col2:
        # Bar chart for project health using plotly
        st.markdown("### Project Health Distribution")
        health_counts = {'Healthy': 0, 'At Risk': 0, 'Critical': 0}
        for project in filtered_projects:
            health_status, _, _ = calculate_project_health(project, issues)
            health_counts[health_status] += 1
        
        health_data = pd.DataFrame({
            'Health': list(health_counts.keys()),
            'Count': list(health_counts.values())
        })
        
        if len(filtered_projects) > 0:  # Only show chart if there are projects
            fig = px.bar(health_data, x='Health', y='Count',
                        title='Project Health Distribution',
                        color='Health',
                        color_discrete_map={
                            'Healthy': '#28a745',
                            'At Risk': '#ffc107',
                            'Critical': '#dc3545'
                        })
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No projects to display")