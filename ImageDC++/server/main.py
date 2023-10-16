import socketio
import base64
from aiohttp import web
from utils import User, zip_images

sio = socketio.AsyncServer()
app = web.Application()
sio.attach(app)

users: [str, User] = {}
images: [str, str] = {}


@sio.event
def connect(sid, environ):
    # TODO: Maybe make sure the same name isnt already there
    user = User(sid, environ.get("HTTP_NAME"))
    users[sid] = user
    print("Connect: ", user)


# @sio.on("*")
# async def catch_all(event, sid, data):
#     print(event, sid, data)


@sio.event
async def upload_image(sid, data):
    fn = data["filename"]
    print("Image: ", sid, fn)
    images[f"{sid}_{fn}"] = data["filedata"]

    user = users[sid]
    user.shared.append(fn)


@sio.event
async def search(sid, query):
    print("Search: ", query)
    search_results = []
    for img in images:
        if img.startswith(sid):
            continue
        if query in img:
            search_results.append(img)

    print("Search Results: ", ",".join(search_results))

    return search_results


@sio.event
async def download_images(sid, data):
    result = {}
    for fn in data:
        result[fn] = base64.b64decode(images[fn])

    return zip_images(result)


@sio.event
def disconnect(sid):
    print("Disconnect: ", sid)

    # TODO: Implement properly
    # for img in images:
    #     if img.startswith(sid):
    #         del images[img]

    del users[sid]


if __name__ == "__main__":
    web.run_app(app)
