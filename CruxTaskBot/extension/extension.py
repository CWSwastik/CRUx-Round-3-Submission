import os
import vscode
import aiohttp
import asyncio
from typing import List
from vscode import InfoMessage, InputBox, WebviewPanel, QuickPick, QuickPickOptions

ext = vscode.Extension("Crux Task Extension")
ext.server_url = None
ext.panel = None

index_html_path = os.path.join(os.path.dirname(__file__), "index.html")
with open(index_html_path, "r") as f:
    HTML_TEMPLATE = f.read()

styles_css_path = os.path.join(os.path.dirname(__file__), "styles.css")
with open(styles_css_path, "r") as f:
    STYLES = "<style>" + f.read() + "</style>"


def get_formatted_html(tasks: List[dict]) -> str:
    """
    Generates formatted HTML for displaying tasks in three groups: Assigned, In Progress, and Completed,
    with buttons to move tasks between the groups.

    Args:
    tasks (List[dict]): A list of task dictionaries, each containing at least 'title', 'status', and 'id' fields.

    Returns:
    str: Formatted HTML string representing the tasks grouped by status with interactive buttons.
    """

    assigned_tasks = []
    in_progress_tasks = []
    completed_tasks = []

    for task in tasks:
        if task["status"] == "Assigned":
            assigned_tasks.append(task)
        elif task["status"] == "In Progress":
            in_progress_tasks.append(task)
        elif task["status"] == "Completed":
            completed_tasks.append(task)

    task_list = "<div class='task-container'>"
    task_list += "<div class='task-group'><h3>Assigned</h3>"
    for task in assigned_tasks:
        task_list += f"<div class='task-item'> {task['title']} <button class='task-button' onclick='start({task['id']})'>Start</button> </div>"
    task_list += "</div>"

    task_list += "<div class='task-group'><h3>In Progress</h3>"
    for task in in_progress_tasks:
        task_list += f"<div class='task-item'> {task['title']} <button class='task-button' onclick='complete({task['id']})'>Complete</button> </div>"
    task_list += "</div>"

    task_list += "<div class='task-group'><h3>Completed</h3>"
    for task in completed_tasks:
        task_list += f"<div class='task-item'> {task['title']} </div>"
    task_list += "</div>"

    script = """
    <script>
        let vscode = acquireVsCodeApi();
        function start(id) { vscode.postMessage({ name: 'start', 'id': id }); };
        function complete(id) { vscode.postMessage({ name: 'complete', 'id': id }); };
    </script>
    """

    return HTML_TEMPLATE.format(body=task_list, script=script, styles=STYLES)


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
        url = url.strip()
        ext.server_url = url
    else:
        url = ext.server_url

    if ext.panel is not None:
        return await ctx.window.show(InfoMessage("Crux Tasks window is already open"))

    try:
        session = aiohttp.ClientSession()
        async with session.get(url) as resp:
            if resp.status != 200:
                ext.panel = None
                await session.close()
                await ctx.window.show(InfoMessage("Invalid url, please reauthenticate."))
                ext.server_url = None
                return
            res = await resp.json()
    except aiohttp.InvalidURL:
        await ctx.window.show(InfoMessage("Invalid url, please reauthenticate"))
        ext.server_url = None
        return
    
    panel = WebviewPanel("Crux Tasks", vscode.ViewColumn.Two)
    await ctx.window.create_webview_panel(panel)
    ext.panel = panel

    async def on_message(data):
        if data["name"] == "start":
            async with session.post(
                url, json={"id": data["id"], "action": "start"}
            ) as resp:
                code = resp.status
                res = await resp.text()

        elif data["name"] == "complete":
            async with session.post(
                url, json={"id": data["id"], "action": "complete"}
            ) as resp:
                code = resp.status
                res = await resp.text()

        if code == 401:
            await panel.dispose()
            ext.panel = None
            await session.close()
            await ctx.window.show(InfoMessage("Invalid url, please reauthenticate"))
            ext.server_url = None
            return

        async with session.get(url) as resp:
            res = await resp.json()

        await panel.set_html(get_formatted_html(res))

    panel.on_message = on_message
    await panel.set_html(get_formatted_html(res))

    while panel.running:
        async with session.get(url) as resp:
            res = await resp.json()

        await panel.set_html(get_formatted_html(res))
        await asyncio.sleep(10)  # Refresh every 10 seconds

    ext.panel = None
    await session.close()


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
        url = url.strip()
        ext.server_url = url
    else:
        url = ext.server_url

    # get all files in the workspace
    folders = await ctx.workspace.get_workspace_folders()
    files = []

    for folder in folders:
        base_path = folder.uri.fs_path
        for root, _, filenames in os.walk(base_path):
            for filename in filenames:
                relative_path = os.path.relpath(os.path.join(root, filename), base_path)
                files.append(relative_path)

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
        repo_url = await ctx.window.show(InputBox("Enter the repository url"))
        if not repo_url:
            return

        try:
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
        except aiohttp.InvalidURL:
            await ctx.window.show(InfoMessage("Invalid url, please reauthenticate"))
            ext.server_url = None


ext.run()
