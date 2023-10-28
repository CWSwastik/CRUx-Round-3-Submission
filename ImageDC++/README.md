# ImageDC++

ImageDC++ is a command-line tool for sharing and retrieving images within a local network. It allows users to easily upload, download and search for images uploaded by other users.

## Features

- **Image Sharing**: Share your image files with other users on the local network. You can share
    - Individual photos
    - Folders with photos (Nested folders supported)
- **Search for Images**: Search for images currently being shared by other users.
   - The search implements Fuzzy search
- **Download Images**: Download retrieved photos in a zipped folder. 
    - The images in the zip are segregated into folders based on who shared the image
- **Server Connectivity**: The server facilitates real-time image sharing but does not persist any information after users go offline.
    - It keeps data in memory as long as users are connected and sharing something.

## Installation & Setup

To get started with ImageDC++, follow these steps:

1. Clone the repository to your local machine.
```bash
git clone https://github.com/CWSwastik/CRUx-Round-3-Submission
```

2. cd into ImageDC++
```bash
cd ImageDC++
```  
3. Install the dependencies
```bash
pip install -r requirements.txt
```

4. To run the server or client, run the main.py in that directory
```bash
python server/main.py
python client/main.py
```

5. Optionally you may run the server in debug mode and you may even specify a host and port number to host the server on.
```bash
 python server/main.py debug=True host="0.0.0.0" port=8080
```
