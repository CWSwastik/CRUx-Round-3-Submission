import datetime
import aiosqlite
from typing import List, Optional
from .models import Project, Task


class Database:
    """
    Class for all interactions with the database.
    """

    def __init__(self):
        self.db_path = "./data/crux.db"

    async def create_tables(self):
        async with aiosqlite.connect(self.db_path) as conn:
            await conn.execute(
                """
                CREATE TABLE IF NOT EXISTS projects (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    role BIGINT NOT NULL,
                    channel BIGINT NOT NULL,
                    github TEXT NOT NULL,
                    description TEXT NOT NULL
                );
            """
            )

            await conn.execute(
                """
                CREATE TABLE IF NOT EXISTS tasks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    description TEXT NOT NULL,
                    project_id BIGINT NOT NULL,
                    deadline BIGINT NOT NULL,
                    status TEXT NOT NULL,
                    domain TEXT NOT NULL,
                    assignee BIGINT NOT NULL
                );
            """
            )
            await conn.commit()

    async def fetchone(self, query: str, *args):
        async with aiosqlite.connect(self.db_path) as conn:
            data = await conn.execute(query, args)
            return await data.fetchone()

    async def fetchall(self, query: str, *args):
        async with aiosqlite.connect(self.db_path) as conn:
            data = await conn.execute(query, args)
            return await data.fetchall()

    async def execute(self, query: str, *args):
        async with aiosqlite.connect(self.db_path) as conn:
            await conn.execute(query, args)
            return await conn.commit()

    # Creating a new project
    async def create_project(self, project: Project) -> None:
        await self.execute(
            """
                INSERT INTO projects (title, role, channel, github, description)
                VALUES (?, ?, ?, ?, ?);
                """,
            project.title,
            project.role,
            project.channel,
            project.github_url,
            project.description,
        )

    # Deleting an existing project (using project id)
    async def delete_project(self, project_id: int) -> None:
        await self.execute(
            """
                DELETE FROM projects WHERE id = ?;
                """,
            project_id,
        )

        await self.execute(
            """
                DELETE FROM tasks WHERE project_id = ?;
                """,
            project_id,
        )

    # Fetch project using its name
    async def fetch_project(self, project_name: str) -> Optional[Project]:
        data = await self.fetchone(
            "SELECT * FROM projects WHERE title = ?;",
            project_name,
        )

        if data is None:
            return None

        return Project(
            id=data[0],
            title=data[1],
            role=data[2],
            channel=data[3],
            github_url=data[4],
            description=data[5],
        )

    # List all existing projects
    async def list_all_projects(self) -> List[Project]:
        data = await self.fetchall("SELECT * FROM projects;")

        return [
            Project(
                id=project[0],
                title=project[1],
                role=project[2],
                channel=project[3],
                github_url=project[4],
                description=project[5],
            )
            for project in data
        ]

    # Create task
    async def create_task(self, task: Task) -> None:
        await self.execute(
            """
                INSERT INTO tasks (title, description, project_id, deadline, status, domain, assignee)
                VALUES (?, ?, ?, ?, ?, ?, ?);
                """,
            task.title,
            task.description,
            task.project_id,
            task.deadline.timestamp(),
            task.status,
            task.domain,
            task.assignee,
        )

    # List all tasks associated with a particular project
    async def list_project_tasks(
        self, project_id: Optional[int] = None, project_title: Optional[str] = None
    ) -> List[Task]:
        if project_id is not None:
            data = await self.fetchall(
                """
                    SELECT * FROM tasks WHERE project_id = ?;
                    """,
                project_id,
            )
        elif project_title is not None:
            data = await self.fetchall(
                """
                    SELECT * FROM tasks WHERE project_id = (
                        SELECT id FROM projects WHERE title = ?
                    );
                    """,
                project_title,
            )
        else:
            return []

        return [
            Task(
                id=task[0],
                title=task[1],
                description=task[2],
                project_id=task[3],
                deadline=datetime.datetime.fromtimestamp(task[4]),
                status=task[5],
                domain=task[6],
                assignee=task[7],
            )
            for task in data
        ]

    # Delete task
    async def delete_task(self, task_id: int) -> None:
        await self.execute(
            """
                DELETE FROM tasks WHERE id = ?;
                """,
            task_id,
        )

    # Edit task
    # TODO: Fix this
    async def edit_task(self, task_id: int, **kwargs) -> None:
        await self.execute(
            """
                UPDATE tasks SET title = ?, description = ?, deadline = ?, status = ?, domain = ?, assignee = ?
                WHERE id = ?;
                """,
            kwargs["title"],
            kwargs["description"],
            kwargs["deadline"].timestamp(),
            kwargs["status"],
            kwargs["domain"],
            kwargs["assignee"],
            task_id,
        )
