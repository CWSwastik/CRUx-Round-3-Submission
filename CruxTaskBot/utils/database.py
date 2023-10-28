import datetime
import aiosqlite
from typing import List, Optional
from .models import Project, Task, User


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
                    webhook_id BIGINT,
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
                    assignee BIGINT NOT NULL,
                    reminder BIGINT
                );
            """
            )

            await conn.execute(
                """
                CREATE TABLE IF NOT EXISTS users (
                    id BIGINT PRIMARY KEY NOT NULL,
                    name TEXT NOT NULL,
                    github TEXT,
                    email TEXT
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
            webhook_id=data[6],
        )

    # Set project webhook id
    async def set_project_webhook_id(self, project_id: int, webhook_id: int) -> None:
        await self.execute(
            """
                UPDATE projects SET webhook_id = ?
                WHERE id = ?;
                """,
            webhook_id,
            project_id,
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
                webhook_id=project[6],
            )
            for project in data
        ]

    # Create task
    async def create_task(self, task: Task) -> None:
        await self.execute(
            """
                INSERT INTO tasks (title, description, project_id, deadline, status, domain, assignee, reminder)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?);
                """,
            task.title,
            task.description,
            task.project_id,
            task.deadline.timestamp(),
            task.status,
            task.domain,
            task.assignee,
            task.reminder,
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
                reminder=task[8],
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

    # Set task status
    async def set_task_status(self, task_id: int, status: str) -> None:
        await self.execute(
            """
                UPDATE tasks SET status = ?
                WHERE id = ?;
                """,
            status,
            task_id,
        )

    # Set task reminder
    async def set_task_reminder(self, task_id: int, reminder: Optional[int]) -> None:
        await self.execute(
            """
                UPDATE tasks SET reminder = ?
                WHERE id = ?;
                """,
            reminder,
            task_id,
        )

    # Get all tasks of a user
    async def list_user_tasks(self, user_id: int) -> List[Task]:
        data = await self.fetchall(
            """
                SELECT * FROM tasks WHERE assignee = ?;
                """,
            user_id,
        )

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
                reminder=task[8],
            )
            for task in data
        ]

    # Fetch user using their id
    async def fetch_user(self, user_id: int) -> Optional[User]:
        data = await self.fetchone(
            "SELECT * FROM users WHERE id = ?;",
            user_id,
        )

        if data is None:
            return None

        return User(
            id=data[0],
            name=data[1],
            github=data[2],
            email=data[3],
        )

    # Create user
    async def create_user(self, user: User) -> None:
        await self.execute(
            """
                INSERT INTO users (id, name, github, email)
                VALUES (?, ?, ?);
                """,
            user.id,
            user.name,
            user.github,
            user.email,
        )

    # Edit user
    async def edit_user(self, user: User, **kwargs) -> None:
        await self.execute(
            """
                UPDATE users SET github = ?, email = ?
                WHERE id = ?;
                """,
            kwargs.get("github", user.github),
            kwargs.get("email", user.email),
            user.id,
        )
