from typing import Optional, List
import datetime
import uuid
from dataclasses import dataclass


@dataclass
class Task:
    title: str
    description: str
    project_id: int
    deadline: datetime.datetime
    status: str
    domain: str
    assignee: int
    reminder: Optional[int] = None  # No of seconds before deadline to send reminder
    id: Optional[int] = None

    def to_dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "project_id": self.project_id,
            "deadline": self.deadline.timestamp(),
            "status": self.status,
            "domain": self.domain,
            "assignee": self.assignee,
            "reminder": self.reminder,
        }


@dataclass
class Project:
    title: str
    role: int
    channel: int
    github_url: str
    description: str
    id: Optional[int] = None
    webhook_id: Optional[int] = None


@dataclass
class User:
    id: int
    name: str
    github: Optional[str] = None
    email: Optional[str] = None
    token: Optional[str] = None

    def __post_init__(self):
        self.token = self.token or uuid.uuid4().hex
