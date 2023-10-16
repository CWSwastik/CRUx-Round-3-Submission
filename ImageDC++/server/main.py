import socketio
from aiohttp import web
from utils import User

sio = socketio.AsyncServer()
app = web.Application()
sio.attach(app)

users: [str, User] = {}
images: [str, str] = {}


@sio.event
def connect(sid, environ):
    user = User(sid, environ.get("HTTP_NAME"))
    users[sid] = user
    print("Connect: ", user)


# @sio.on("*")
# async def catch_all(event, sid, data):
#     print(event, sid, data)


@sio.event
async def upload_image(sid, data):
    print("Image: ", data)

    fn = data["filename"]
    images[f"{sid}_{fn}"] = data["filedata"]

    user = users[sid]
    user.shared.append(fn)

    print("Info", users, images)


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
