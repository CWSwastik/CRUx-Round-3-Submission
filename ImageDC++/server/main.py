import socketio
import base64
from aiohttp import web
from fuzzywuzzy import process
from utils import User, zip_images, ensure_non_clashing_name, clean_name

sio = socketio.AsyncServer(max_http_buffer_size=50_000_000)  # 50 MB upload limit
app = web.Application()
sio.attach(app)

users: [str, User] = {}
images: [str, str] = {}


@sio.event
def connect(sid, environ):
    """
    This event creates a new user and adds them to the users dictionary.
    """

    name = environ.get("HTTP_NAME")
    names = [user.name for user in users.values()]

    name = clean_name(ensure_non_clashing_name(name, names))

    user = User(sid, name)
    users[sid] = user
    print("Connect: ", user)


@sio.event
async def upload_image(sid, data):
    """
    This event stores the uploaded image in the user's shared images.
    """

    user = users[sid]
    fn = data["filename"]
    images[f"{user.name}__{fn}"] = data["filedata"]
    user.shared.append(fn)
    print("Image Upload: ", user, fn)


@sio.event
async def search(sid, query):
    """
    This event searches for images that match the query using fuzzy search.
    """

    print("Search: ", query)

    search_results = []
    user = users[sid]

    # Fuzzy search
    for matched_img in process.extract(query, images.keys()):
        # Don't show the user's own images
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
    """
    This event zips and sends the requested images to the client.
    """

    result = {}
    for fn in data:
        result[fn] = base64.b64decode(images[fn])

    return zip_images(result)


@sio.event
def disconnect(sid):
    """
    This event deletes the user's uploaded images when they disconnect.
    """

    print("Disconnect: ", sid)
    user = users[sid]
    for img in list(images.keys()):
        if img.startswith(user.name):
            del images[img]

    del users[sid]


if __name__ == "__main__":
    import sys

    args = {}
    for arg in sys.argv[1:]:
        try:
            key, value = arg.split("=")
        except ValueError:
            print(f"Invalid argument: {arg} (must be in the form key=value)")
            quit(1)
        args[key] = value

    debug_mode = args.get("debug", False)
    host = args.get("host", "0.0.0.0")
    port = args.get("port", 8080)

    if not debug_mode:
        print = lambda *args, **kwargs: None  # Disable print statements

    web.run_app(app, host=host, port=port)
