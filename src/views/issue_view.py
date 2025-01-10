import streamlit as st
from src.storage import load_data, save_data
from src.models.issue import create_issue, Issue, Comment
from datetime import datetime

def render_issue_form(issue_to_edit=None):
    projects, issues = load_data()
    
    # Add Cancel button before the form
    if st.button("← Cancel", key="cancel_issue"):
        st.session_state.page = "issues"
        st.rerun()

    # Main issue form
    with st.form("issue_form"):
        # Select project
        project = st.selectbox(
            "Select Project",
            [p["name"] for p in projects],
            index=[p["name"] for p in projects].index(issue_to_edit["project"]) if issue_to_edit else 0
        )

        # Issue details
        title = st.text_input("Issue Title", value=issue_to_edit["title"] if issue_to_edit else "")
        description = st.text_area("Issue Description", value=issue_to_edit["description"] if issue_to_edit else "")
        author = st.text_input("Your Name")

        submitted = st.form_submit_button("Save Issue")

        if submitted:
            try:
                if issue_to_edit:
                    # Update existing issue
                    issue_idx = next(
                        (i for i, iss in enumerate(issues) if iss["title"] == issue_to_edit["title"]),
                        None
                    )
                    if issue_idx is not None:
                        issues[issue_idx].update({
                            "project": project,
                            "title": title,
                            "description": description,
                            "last_updated_by": author,
                            "last_updated_at": datetime.now()  #pd.Timestamp.now().isoformat()
                        })
                else:
                    # Create new issue
                    new_issue = {
                        "project": project,
                        "title": title,
                        "description": description,
                        "author": author,
                        "comments": [],
                        "created_at": datetime.now()  #pd.Timestamp.now().isoformat()
                    }
                    issues.append(new_issue)

                save_data(projects, issues)
                st.success("Issue saved successfully!")
                st.session_state.page = "issues"
                st.rerun()
            except ValueError as e:
                st.error(f"Validation error: {str(e)}")

    # Separate comment form (only for existing issues)
    if issue_to_edit:
        st.markdown("### Comments")
        if "comments" in issue_to_edit:
            for comment in issue_to_edit["comments"]:
                st.markdown(f"""
                > {comment['text']}  
                > *- {comment['author']} on {comment['created_at']}*
                """)

        # Form to add a new comment
        with st.form(f"comment_form_{issue_to_edit['title']}"):
            comment_text = st.text_area("Add a comment")
            comment_author = st.text_input("Your Name (for comment)")
            submit_comment = st.form_submit_button("Add Comment")

            if submit_comment and comment_text and comment_author:
                try:
                    new_comment = {
                        "text": comment_text,
                        "author": comment_author,
                        "created_at": datetime.now()  # pd.Timestamp.now().isoformat()
                    }
                    issue_idx = next(
                        (i for i, iss in enumerate(issues) if iss["title"] == issue_to_edit["title"]),
                        None
                    )
                    if issue_idx is not None:
                        issues[issue_idx].setdefault("comments", []).append(new_comment)
                        save_data(projects, issues)
                        st.success("Comment added successfully!")
                        st.rerun()
                except ValueError as e:
                    st.error(f"Validation error: {str(e)}")

# def render_issue_list(project_name):
#     projects, issues = load_data()
#     project_issues = [i for i in issues if i['project'] == project_name]
    
#     # Search and Add buttons
#     col1, col2= st.columns([4, 1])
#     with col1:
#         search_query = st.text_input("", placeholder="🔍 Search Issues....", key="issue_search")
#     with col2:
#         if st.button("➕ Add New Issue", use_container_width=True):
#             st.session_state.add_issue = True
#             st.rerun()
#     st.markdown('</div>', unsafe_allow_html=True)
    
#     # Filter issues based on search
#     if search_query:
#         project_issues = [i for i in project_issues if search_query.lower() in i['title'].lower()]
    
#      # Add New Issue Form
#     if st.session_state.get('add_issue'):
#         with st.form("new_issue_form"):
#             st.subheader("Add New Issue")
#             title = st.text_input("Issue Title")
#             description = st.text_area("Issue Description")
#             status = st.selectbox("Status", ["Pending", "Completed"])
            
#             submitted = st.form_submit_button("Save Issue")
#             if submitted and title and description:
#                 new_issue = create_issue(project_name, title, description, status)
#                 issues.append(new_issue)
#                 save_data(projects, issues)
#                 st.session_state.add_issue = False
#                 st.markdown('<div class="success-message">Issue added successfully!</div>', 
#                           unsafe_allow_html=True)
#                 st.rerun()  
                
    
#     # Display issues
#     for issue in project_issues:
#         col1, col2, col3 = st.columns([2, 1, 3])
        
#         with col1:
#             st.markdown(f"{issue['title']}")
#             # st.markdown(f"**Description:** {issue['description']}")
#             # st.markdown(f"**Created:** {issue['created_at']}")
        
#         with col2:
#             status_class = "status-completed" if issue['status'] == "Completed" else "status-pending"
#             st.markdown(f'<span class="{status_class}">Status: {issue["status"]}</span>', 
#                           unsafe_allow_html=True)
                
#         with col3:
#             view_col, update_col, delete_col = st.columns(3)
#             with view_col:
#                 if st.button("👁️ View", key=f"view_issue_{issue['title']}", 
#                             use_container_width=True):
#                     st.session_state.selected_issue = issue
#                     st.session_state.show_issue = True
#             with update_col:
#                 if st.button("✏️ Edit", key=f"edit_{issue['title']}", use_container_width=True):
#                     st.session_state.issue_to_edit = issue
#                     st.session_state.page = "edit_issue"
#                     st.rerun()
#             with delete_col:
#                 if st.button("🗑️ Delete", key=f"delete_issue_{issue['title']}", use_container_width=True):
#                     issues.remove(issue)
#                     save_data(projects, issues)
#                     st.markdown('<div class="success-message">Issue deleted successfully!</div>', 
#                                 unsafe_allow_html=True)
#                     st.rerun()        
#         st.markdown('</div>', unsafe_allow_html=True)
        
#         if st.session_state.get('show_issue') and st.session_state.get('selected_issue') == issue:
#                 with st.container():
#                     st.markdown('<div class="element-container">', unsafe_allow_html=True)
#                     st.subheader("Issue Details")
#                     st.markdown(f"**Title:** {issue['title']}")
#                     st.markdown(f'<span class="{status_class}">Status: {issue["status"]}</span>', 
#                               unsafe_allow_html=True)
#                     st.markdown(f"**Created At:** {issue['created_at']}")
#                     st.markdown(f"**Updated At:** {issue['last_updated_at']}")
#                     st.markdown(f"**Updated By:** {issue['last_updated_by']}")
#                     st.markdown("**Description:**")
#                     st.markdown(issue['description'])
#                     if st.button("Close Details"):
#                         st.session_state.show_issue = False
#                         st.rerun()
#                     st.markdown('</div>', unsafe_allow_html=True)    
            
                        
            # # Update issue status 
            # current_status = issue["status"]
            # new_status = "Completed" if current_status == "Pending" else "Pending"
            # if st.button(f"Mark as {new_status}", key=f"status_{issue['title']}", use_container_width=True):
            #     issue["status"] = new_status
            #     save_data(projects, issues)
            #     st.rerun()     
            
def render_issue_list(project_name):
    projects, issues = load_data()
    project_issues = [i for i in issues if i['project'] == project_name]
    
    # Search and Add buttons
    st.markdown('<div class="header-container">', unsafe_allow_html=True)
    col1, col2 = st.columns([4, 1])
    with col1:
        search_query = st.text_input("", placeholder="🔍 Search Issues....", key="issue_search", label_visibility="collapsed")
    with col2:
        if st.button("➕ Add New Issue", use_container_width=True):
            st.session_state.add_issue = True
            st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)
        
    # Filter issues based on search
    if search_query:
        project_issues = [i for i in project_issues if search_query.lower() in i['title'].lower()]

    # Add New Issue Form
    if st.session_state.get('add_issue'):
        with st.form("new_issue_form"):
            st.subheader("Add New Issue")
            title = st.text_input("Issue Title *")
            description = st.text_area("Issue Description *")
            status = st.selectbox("Status *", ["Pending", "Completed"])
            
            submitted = st.form_submit_button("Save Issue")
            if submitted:
                if not title or not description:
                    st.error("Please fill in all required fields")
                    return
                
                new_issue = create_issue(project_name, title, description, status)
                issues.append(new_issue)
                save_data(projects, issues)
                st.session_state.add_issue = False
                st.success("Issue added successfully!")
                st.rerun()

    # Display issues
    if project_issues:
        for issue in project_issues:
            with st.expander(f"**{issue['title']}** - {issue['status']}", expanded=False):
                # Issue details
                st.markdown(f"**Description:** {issue['description']}")
                st.markdown(f"**Created:** {issue['created_at']}")
                
                # Status toggle with comment
                col1, col2 = st.columns([1, 3])
                with col1:
                    new_status = "Completed" if issue['status'] == "Pending" else "Pending"
                    if st.button(f"Mark as {new_status}", key=f"toggle_{issue['title']}"):
                        st.session_state.toggle_status = {
                            'issue': issue,
                            'new_status': new_status
                        }
                
                # Status change comment form
                if st.session_state.get('toggle_status', {}).get('issue') == issue:
                    with st.form(key=f"status_comment_{issue['title']}"):
                        comment = st.text_area(
                            f"Add a comment for marking as {st.session_state.toggle_status['new_status']} *",
                            placeholder="Explain why you're changing the status..."
                        )
                        author = st.text_input("Your Name *")
                        
                        if st.form_submit_button("Confirm Status Change"):
                            if not comment or not author:
                                st.error("Please fill in all required fields")
                                return
                            
                            # Update issue status and add comment
                            issue['status'] = st.session_state.toggle_status['new_status']
                            add_comment(
                                issue, 
                                comment, 
                                author, 
                                f"Changed status to {st.session_state.toggle_status['new_status']}"
                            )
                            
                            # Save changes
                            save_data(projects, issues)
                            del st.session_state.toggle_status
                            st.success("Status updated successfully!")
                            st.rerun()
                
                # Display comments
                if issue.get('comments'):
                    st.markdown("### Comments")
                    for comment in issue['comments']:
                        with st.container():
                            st.markdown(f"""
                            **{comment['author']}** - {comment['created_at']}  
                            {f"🔄 *{comment['status_change']}*" if comment.get('status_change') else ""}  
                            {comment['text']}
                            """)
                            st.divider()
                
                # Delete button
                if st.button("🗑️ Delete Issue", key=f"delete_{issue['title']}"):
                    issues.remove(issue)
                    save_data(projects, issues)
                    st.success("Issue deleted successfully!")
                    st.rerun()
    else:
        st.info("No issues found for this project.")                  