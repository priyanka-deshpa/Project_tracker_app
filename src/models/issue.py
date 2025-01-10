from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field

class Comment(BaseModel):
    text: str
    created_at: datetime = Field(default_factory=datetime.now)
    author: str
    status_change: Optional[str] = None  # Records status change if comment is related to status change

class Issue(BaseModel):
    project: str
    title: str
    description: str
    status: str = "Pending"
    created_at: datetime = Field(default_factory=datetime.now)
    comments: List[Comment] = Field(default_factory=list)

def create_issue(project: str, title: str, description: str, status: str = "Pending") -> dict:
    issue = Issue(
        project=project,
        title=title,
        description=description,
        status=status
    )
    return issue.model_dump()

def add_comment(issue: dict, text: str, author: str, status_change: Optional[str] = None) -> dict:
    comment = Comment(
        text=text,
        author=author,
        status_change=status_change
    )
    if 'comments' not in issue:
        issue['comments'] = []
    issue['comments'].append(comment.model_dump())
    return issue