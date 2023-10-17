import socketio
import base64
from aiohttp import web
from fuzzywuzzy import process
from utils import User, zip_images

sio = socketio.AsyncServer(max_http_buffer_size=10_000_000)  # 10 MB/img
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
    user = users[sid]
    fn = data["filename"]
    print("Image: ", sid, fn)
    images[f"{user.name}__{fn}"] = data["filedata"]

    user.shared.append(fn)


@sio.event
async def search(sid, query):
    print("Search: ", query)
    search_results = []
    user = users[sid]

    # Fuzzy search
    for matched_img in process.extract(query, images.keys()):
        if matched_img[0].startswith(user.name):
            continue

        print(matched_img)

        # Skip matches that are less than 40
        if matched_img[1] < 40:
            continue

        search_results.append(matched_img[0])

    print("Search Results: ", ", ".join(search_results))

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
    user = users[sid]
    for img in list(images.keys()):
        if img.startswith(user.name):
            del images[img]

    del users[sid]


if __name__ == "__main__":
    web.run_app(app)
