from typing import Optional, List
import datetime
from dataclasses import dataclass


@dataclass
class Task:
    title: str
    description: str
    project_id: int
    deadline: datetime.datetime
    status: str
    domain: str
    id: Optional[int] = None


@dataclass
class Project:
    title: str
    role: int
    channel: int
    github_url: str
    description: str
    id: Optional[int] = None
