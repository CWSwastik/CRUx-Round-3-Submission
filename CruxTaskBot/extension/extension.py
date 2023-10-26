import vscode

ext = vscode.Extension("Crux Task Extension")


@ext.command()
async def hello_world(ctx):
    await ctx.show(vscode.InfoMessage("Hi!"))


ext.run()
