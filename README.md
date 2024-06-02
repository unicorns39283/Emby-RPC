# Emby RPC Application

This application updates your Discord Rich Presence based on the show and episode you are currently watching, which is retrieved from Emby.

## Requirements
The requirements for this project are stored in the `requirements.txt` file. To install them, use the following command:

```bash
pip install -r requirements.txt
```

## Usage
To use this application, you need to have an Emby server running. You can set the server URL and API key in the `config.json` file. The application will automatically update your Discord Rich Presence based on the show and episode you are currently watching.

To run the application, use the following command:

```bash
python main.py
```