import os
import vscode
import aiohttp
from typing import List
from vscode import InfoMessage, InputBox, WebviewPanel

ext = vscode.Extension("Crux Task Extension")

# get index html path
index_html_path = os.path.join(os.path.dirname(__file__), "index.html")
with open(index_html_path, "r") as f:
    HTML_TEMPLATE = f.read()


def get_formatted_html(tasks: List[dict]) -> str:
    task_list = "<ul>"
    for task in tasks:
        task_list += f"<li>{task['title']}</li>"
    task_list += "</ul>"
    return HTML_TEMPLATE.format(task_list, "")


@ext.command()
async def show_crux_tasks_window(ctx):
    box = InputBox(
        title="Authentication URL",
        prompt="Run /authenticate-extension on the discord bot and enter the url it generates here",
    )
    url = await ctx.window.show(box)
    if not url:
        return
    session = aiohttp.ClientSession()
    async with session.get(url) as resp:
        res = await resp.json()
    await session.close()

    panel = WebviewPanel("Crux Tasks", vscode.ViewColumn.Beside)
    await ctx.window.create_webview_panel(panel)

    await panel.set_html(get_formatted_html(res["tasks"]))


ext.run()
