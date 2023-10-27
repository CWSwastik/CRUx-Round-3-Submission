import discord
import asyncio
from aiohttp import web
from discord.ext import commands
from discord import app_commands
from utils import generate_documentation


class Webserver(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    async def webserver(self):
        async def root_handler(request):
            return web.Response(text="Hello, world")

        async def get_task_handler(request):
            # TODO: Use an internal id instead of user id
            user_id = request.match_info["user_id"]
            tasks = await self.bot.db.list_user_tasks(user_id)
            return web.json_response([task.to_dict() for task in tasks])

        async def post_task_handler(request):
            data = await request.json()
            status = "In Progress" if data["action"] == "start" else "Completed"
            # TODO: check correct user
            await self.bot.db.set_task_status(data["id"], status)
            return web.Response(text="OK")

        async def generate_documentation_handler(request):
            data = await request.json()
            content = data["content"]
            docs = await generate_documentation(content)
            return web.json_response({"docs": docs})

        async def push_to_github_handler(request):
            data = await request.json()
            content = data["content"]
            file_path = data["file_path"]
            repo_url = data["repo_url"]

            await self.bot.gh.create_branch(repo_url, "bot-docs")
            res = await self.bot.gh.add_file_to_branch(
                repo_url, "bot-docs", file_path, content
            )

            return web.json_response({"url": res[-1]["content"]["html_url"]})

        async def webhook_handler(request):
            data = await request.json()
            event_type = request.headers.get("X-GitHub-Event")

            if event_type in ["issues", "pull_request", "push", "ping"]:
                repository = data["repository"]["full_name"]
                html_url = data["repository"]["html_url"]
                projects = await self.bot.db.list_all_projects()
                project = [p for p in projects if p.github_url == html_url]
                if project:
                    project = project[0]
                    ch = self.bot.get_channel(project.channel)
                    if not ch:
                        ch = await self.bot.fetch_channel(project.channel)

                    # TODO: send a proper embed with more information
                    await ch.send(f"New {event_type} event for {repository}!")

            return web.Response(text="OK")

        app = web.Application()
        app.router.add_get("/", root_handler)
        app.router.add_get("/tasks/{user_id}", get_task_handler)
        app.router.add_post("/tasks/{user_id}", post_task_handler)
        app.router.add_post("/generate-documentation", generate_documentation_handler)
        app.router.add_post("/push-to-github", push_to_github_handler)
        app.router.add_post("/webhook", webhook_handler)
        runner = web.AppRunner(app)
        await runner.setup()
        self.site = web.TCPSite(runner, "localhost", 8080)
        await self.bot.wait_until_ready()
        await self.site.start()

    def __unload(self):
        asyncio.ensure_future(self.site.stop())

    @app_commands.command(
        name="authenticate-extension",
        description="Returns the url that must be used to authenticate the extension",
    )
    async def authenticate_extension(self, interaction: discord.Interaction):
        await interaction.response.send_message(
            f"Please enter this link in the extension: {self.bot.config.webserver_url}/tasks/{interaction.user.id}",
            ephemeral=True,
        )


async def setup(bot: commands.Bot) -> None:
    ws = Webserver(bot)
    await bot.add_cog(ws)
    bot.loop.create_task(ws.webserver())
