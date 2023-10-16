import time
from yaspin import yaspin


@yaspin(text="Connecting to server...")
def connect():
    # TODO: Implement SocketIO
    time.sleep(1)
