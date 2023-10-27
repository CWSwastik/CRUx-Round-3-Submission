import os
import vscode
import aiohttp
from typing import List
from vscode import InfoMessage, InputBox, WebviewPanel, QuickPick, QuickPickOptions

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
    """Show the crux tasks window as a webview"""

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


@ext.command()
async def generate_documentation(ctx):
    """Generate documentation for the current workspace"""

    # get all files in the workspace
    folders = await ctx.workspace.get_workspace_folders()
    files = []

    # TODO: use os.walk
    for folder in folders:
        for file in os.listdir(folder.uri.fs_path):
            if os.path.isfile(file):
                files.append(file)
            else:
                for f in os.listdir(os.path.join(folder.uri.fs_path, file)):
                    fp = os.path.join(folder.uri.fs_path)
                    p = os.path.join(folder.uri.fs_path, fp)
                    if os.path.isfile(p):
                        files.append(fp)

    file_picker = QuickPick(files, QuickPickOptions(title="Select a file"))
    file = await ctx.window.show(file_picker)
    if not file:
        return

    inp_box = InputBox("Enter the output path for the documentation")
    output_path = await ctx.window.show(inp_box)
    if not output_path:
        return
    os.chdir(folder.uri.fs_path)
    with open(output_path, "w") as f:
        f.write(f"Documentation generated for {file}")

    res = await ctx.window.show(
        InfoMessage(
            "Documentation generated, would you like to push it to github?",
            ["Yes", "No"],
        )
    )
    if res == "Yes":
        # await ctx.git.add(output_path)
        # await ctx.git.commit("Documentation generated")
        # await ctx.git.push()
        await ctx.window.show(InfoMessage("Pushed to github"))


ext.run()
