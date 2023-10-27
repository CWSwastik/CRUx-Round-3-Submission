import os
import vscode
import aiohttp
import asyncio
from typing import List
from vscode import InfoMessage, InputBox, WebviewPanel, QuickPick, QuickPickOptions

ext = vscode.Extension("Crux Task Extension")
ext.server_url = None

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
    """Show the crux tasks window as a webview"""
    if ext.server_url is None:
        box = InputBox(
            title="Authentication URL",
            prompt="Run /authenticate-extension on the discord bot and enter the url it generates here",
        )
        url = await ctx.window.show(box)
        if not url:
            return

        ext.server_url = url
    else:
        url = ext.server_url

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


@ext.command()
async def generate_documentation(ctx):
    """Generate documentation for the current workspace"""

    if ext.server_url is None:
        box = InputBox(
            title="Authentication URL",
            prompt="Run /authenticate-extension on the discord bot and enter the url it generates here",
        )
        url = await ctx.window.show(box)
        if not url:
            return

        ext.server_url = url
    else:
        url = ext.server_url

    # get all files in the workspace
    folders = await ctx.workspace.get_workspace_folders()
    files = []

    # TODO: use os.walk
    for folder in folders:
        for file in os.listdir(folder.uri.fs_path):
            fp = os.path.join(folder.uri.fs_path, file)
            if os.path.isfile(fp):
                files.append(file)
            else:
                for f in os.listdir(fp):
                    file_path = os.path.join(file, f)
                    p = os.path.join(folder.uri.fs_path, file_path)
                    if os.path.isfile(p):
                        files.append(file_path)

    file_picker = QuickPick(files, QuickPickOptions(title="Select a file"))
    file = await ctx.window.show(file_picker)
    if not file:
        return
    file = file.label

    inp_box = InputBox("Enter the output path for the documentation")
    output_path = await ctx.window.show(inp_box)

    if not output_path:
        return
    os.chdir(folder.uri.fs_path)

    with open(file, "r") as f:
        content = f.read()

    coro = ctx.window.show(
        InfoMessage(
            "Generating documentation... (it takes a while, please wait even if this message disappears)"
        )
    )
    asyncio.create_task(coro)

    base_url = url.split("/tasks")[0]
    async with aiohttp.ClientSession() as session:
        async with session.post(
            base_url + "/generate-documentation", json={"content": content}
        ) as resp:
            res = await resp.json()

    generated_docs = res["docs"]
    with open(output_path, "w") as f:
        f.write(generated_docs)

    res = await ctx.window.show(
        InfoMessage(
            "Documentation generated, would you like to push it to github?",
            ["Yes", "No"],
        )
    )
    if res == "Yes":
        # get repo url
        repo_url = await ctx.window.show(InputBox("Enter the repository url"))
        if not repo_url:
            return

        async with aiohttp.ClientSession() as session:
            async with session.post(
                base_url + "/push-to-github",
                json={
                    "content": generated_docs,
                    "file_path": output_path,
                    "repo_url": repo_url,
                },
            ) as resp:
                res = await resp.json()

        await ctx.window.show(InfoMessage("Pushed to github"))


ext.run()
