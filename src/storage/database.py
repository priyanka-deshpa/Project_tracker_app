import sqlite3
from datetime import datetime
from pathlib import Path
import json

def init_db():
    """Initialize the SQLite database and create tables if they don't exist."""
    db_path = Path("data/project_tracker.db")
    db_path.parent.mkdir(exist_ok=True)
    
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    
    # Create projects table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS projects (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE NOT NULL,
        developers TEXT NOT NULL,
        leads TEXT NOT NULL,
        scope TEXT NOT NULL,
        ado_link TEXT NOT NULL,
        formatting_tools TEXT NOT NULL,
        linting_tools TEXT NOT NULL,
        cicd_pipeline TEXT NOT NULL,
        nfr TEXT NOT NULL,
        arch_diagram_path TEXT,
        infra_diagram_path TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    # Create delivery_plans table with foreign key to projects
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS delivery_plans (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        project_id INTEGER NOT NULL,
        week_number TEXT NOT NULL,
        plan_details TEXT NOT NULL,
        FOREIGN KEY (project_id) REFERENCES projects (id)
    )
    ''')
    
    # Create issues table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS issues (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        project_id INTEGER NOT NULL,
        title TEXT NOT NULL,
        description TEXT NOT NULL,
        status TEXT NOT NULL DEFAULT 'Pending',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (project_id) REFERENCES projects (id)
    )
    ''')
    
    # Create comments table for issues
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS issue_comments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        issue_id INTEGER NOT NULL,
        text TEXT NOT NULL,
        author TEXT NOT NULL,
        status_change TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (issue_id) REFERENCES issues (id)
    )
    ''')
    
    conn.commit()
    conn.close()

def get_db():
    """Get database connection."""
    conn = sqlite3.connect('data/project_tracker.db')
    conn.row_factory = sqlite3.Row
    return conn

def get_all_projects():
    """Retrieve all projects from the database."""
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        # Get all projects
        cursor.execute('SELECT * FROM projects')
        projects = cursor.fetchall()
        
        result = []
        for project in projects:
            # Get delivery plans for each project
            cursor.execute('SELECT week_number, plan_details FROM delivery_plans WHERE project_id = ?', (project['id'],))
            delivery_plans = {row['week_number']: row['plan_details'] for row in cursor.fetchall()}
            
            # Convert to dictionary format
            project_dict = dict(project)
            project_dict['developers'] = project_dict['developers'].split(',')
            project_dict['leads'] = project_dict['leads'].split(',')
            project_dict['delivery_plan'] = delivery_plans
            
            # Remove database-specific fields
            project_dict.pop('id', None)
            
            result.append(project_dict)
        
        return result
    finally:
        conn.close()

def save_project(project_data):
    """Save project data to the database."""
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        # Start transaction
        cursor.execute('BEGIN')
        
        # Insert project details
        cursor.execute('''
        INSERT INTO projects (
            name, developers, leads, scope, ado_link,
            formatting_tools, linting_tools, cicd_pipeline,
            nfr, arch_diagram_path, infra_diagram_path
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            project_data['name'],
            ','.join(project_data['developers']),
            ','.join(project_data['leads']),
            project_data['scope'],
            project_data['ado_link'],
            project_data['formatting_tools'],
            project_data['linting_tools'],
            project_data['cicd_pipeline'],
            project_data['nfr'],
            project_data.get('arch_diagram_path'),
            project_data.get('infra_diagram_path')
        ))
        
        project_id = cursor.lastrowid
        
        # Insert delivery plans
        for week, plan in project_data['delivery_plan'].items():
            cursor.execute('''
            INSERT INTO delivery_plans (project_id, week_number, plan_details)
            VALUES (?, ?, ?)
            ''', (project_id, week, plan))
        
        conn.commit()
        return True
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()

def update_project(project_name, project_data):
    """Update existing project in the database."""
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        cursor.execute('BEGIN')
        
        # Get project id
        cursor.execute('SELECT id FROM projects WHERE name = ?', (project_name,))
        project = cursor.fetchone()
        
        if not project:
            raise ValueError(f"Project {project_name} not found")
        
        project_id = project['id']
        
        # Update project details
        cursor.execute('''
        UPDATE projects SET
            name = ?, developers = ?, leads = ?, scope = ?, ado_link = ?,
            formatting_tools = ?, linting_tools = ?, cicd_pipeline = ?,
            nfr = ?, arch_diagram_path = ?, infra_diagram_path = ?
        WHERE id = ?
        ''', (
            project_data['name'],
            ','.join(project_data['developers']),
            ','.join(project_data['leads']),
            project_data['scope'],
            project_data['ado_link'],
            project_data['formatting_tools'],
            project_data['linting_tools'],
            project_data['cicd_pipeline'],
            project_data['nfr'],
            project_data.get('arch_diagram_path'),
            project_data.get('infra_diagram_path'),
            project_id
        ))
        
        # Delete existing delivery plans
        cursor.execute('DELETE FROM delivery_plans WHERE project_id = ?', (project_id,))
        
        # Insert new delivery plans
        for week, plan in project_data['delivery_plan'].items():
            cursor.execute('''
            INSERT INTO delivery_plans (project_id, week_number, plan_details)
            VALUES (?, ?, ?)
            ''', (project_id, week, plan))
        
        conn.commit()
        return True
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()

def delete_project(project_name):
    """Delete a project from the database."""
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        cursor.execute('BEGIN')
        
        # Get project id
        cursor.execute('SELECT id FROM projects WHERE name = ?', (project_name,))
        project = cursor.fetchone()
        
        if project:
            project_id = project['id']
            
            # Delete related records first (due to foreign key constraints)
            cursor.execute('DELETE FROM delivery_plans WHERE project_id = ?', (project_id,))
            cursor.execute('DELETE FROM issue_comments WHERE issue_id IN (SELECT id FROM issues WHERE project_id = ?)', (project_id,))
            cursor.execute('DELETE FROM issues WHERE project_id = ?', (project_id,))
            
            # Delete project
            cursor.execute('DELETE FROM projects WHERE id = ?', (project_id,))
            
            conn.commit()
            return True
        return False
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()

def get_all_issues():
    """Retrieve all issues from the database."""
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        # Get all issues with project names
        cursor.execute('''
        SELECT i.*, p.name as project_name 
        FROM issues i 
        JOIN projects p ON i.project_id = p.id
        ''')
        issues = cursor.fetchall()
        
        result = []
        for issue in issues:
            # Get comments for each issue
            cursor.execute('''
            SELECT * FROM issue_comments 
            WHERE issue_id = ? 
            ORDER BY created_at
            ''', (issue['id'],))
            comments = cursor.fetchall()
            
            # Convert to dictionary format
            issue_dict = dict(issue)
            issue_dict['project'] = issue_dict.pop('project_name')
            issue_dict['comments'] = [dict(comment) for comment in comments]
            
            result.append(issue_dict)
        
        return result
    finally:
        conn.close()

def save_issue(issue_data):
    """Save an issue to the database."""
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        cursor.execute('BEGIN')
        
        # Get project_id
        cursor.execute('SELECT id FROM projects WHERE name = ?', (issue_data['project'],))
        project = cursor.fetchone()
        if not project:
            raise ValueError(f"Project {issue_data['project']} not found")
        
        # Insert issue
        cursor.execute('''
        INSERT INTO issues (project_id, title, description, status)
        VALUES (?, ?, ?, ?)
        ''', (
            project['id'],
            issue_data['title'],
            issue_data['description'],
            issue_data['status']
        ))
        
        issue_id = cursor.lastrowid
        
        # Insert comments if any
        if 'comments' in issue_data:
            for comment in issue_data['comments']:
                cursor.execute('''
                INSERT INTO issue_comments (issue_id, text, author, status_change)
                VALUES (?, ?, ?, ?)
                ''', (
                    issue_id,
                    comment['text'],
                    comment['author'],
                    comment.get('status_change')
                ))
        
        conn.commit()
        return True
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()

def update_issue(issue_id, status, comment_data=None):
    """Update issue status and add a comment."""
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        cursor.execute('BEGIN')
        
        # Update issue status
        cursor.execute('''
        UPDATE issues 
        SET status = ? 
        WHERE id = ?
        ''', (status, issue_id))
        
        # Add comment if provided
        if comment_data:
            cursor.execute('''
            INSERT INTO issue_comments (issue_id, text, author, status_change)
            VALUES (?, ?, ?, ?)
            ''', (
                issue_id,
                comment_data['text'],
                comment_data['author'],
                comment_data['status_change']
            ))
        
        conn.commit()
        return True
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()

def delete_issue(issue_id):
    """Delete an issue and its comments from the database."""
    conn = get_db()
    cursor = conn.cursor()
    
    try:
        cursor.execute('BEGIN')
        
        # Delete comments first (due to foreign key constraint)
        cursor.execute('DELETE FROM issue_comments WHERE issue_id = ?', (issue_id,))
        
        # Delete issue
        cursor.execute('DELETE FROM issues WHERE id = ?', (issue_id,))
        
        conn.commit()
        return True
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()