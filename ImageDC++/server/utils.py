class User:
    def __init__(self, sid, name) -> None:
        self.sid = sid
        self.name = name
        self.shared = []  # A list of the names of the files this user shared

    def __repr__(self) -> str:
        return f"<User name={self.name} sid={self.sid}>"
