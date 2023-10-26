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
    # display tasks in 3 groups, Assigned, In Progress, Completed
    # add a button next to each task to move it to the next group

    task_list = "<div>"
    task_list += "<div><h3>Assigned</h3>"
    for task in tasks:
        if task["status"] == "Assigned":
            task_list += f"<div> {task['title']} <button onclick='start({task['id']})'>Start</button> </div>"
    task_list += "</div>"
    task_list += "<div><h3>In Progress</h3>"
    for task in tasks:
        if task["status"] == "In Progress":
            task_list += f"<div> {task['title']} <button onclick='complete({task['id']})'>Complete</button> </div>"
    task_list += "</div>"
    task_list += "<div><h3>Completed</h3>"
    for task in tasks:
        if task["status"] == "Completed":
            task_list += f"<div> {task['title']} </div>"
    task_list += "</div>"

    script = """
    <script>
        let vscode = acquireVsCodeApi();
        function start(id) { vscode.postMessage({ name: 'start', 'id': id }); };
        function complete(id) { vscode.postMessage({ name: 'complete', 'id': id }); };
    </script>
    """

    return HTML_TEMPLATE.format(body=task_list, script=script)


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

    panel = WebviewPanel("Crux Tasks", vscode.ViewColumn.Two)
    await ctx.window.create_webview_panel(panel)

    async def on_message(data):
        if data["name"] == "start":
            async with session.post(
                url, json={"id": data["id"], "action": "start"}
            ) as resp:
                res = await resp.text()

        elif data["name"] == "complete":
            async with session.post(
                url, json={"id": data["id"], "action": "complete"}
            ) as resp:
                res = await resp.text()

        async with session.get(url) as resp:
            res = await resp.json()

        await panel.set_html(get_formatted_html(res))

    panel.on_message = on_message
    await panel.set_html(get_formatted_html(res))


ext.run()
