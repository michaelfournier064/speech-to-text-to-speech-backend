# speech-to-text-to-speech-backend

## Project Setup

Follow these steps to set up the project:

1. **Install pip** (if not already installed)
	- Windows: Download [get-pip.py](https://bootstrap.pypa.io/get-pip.py) and run `python get-pip.py`.
	- Linux/macOS: Usually pre-installed. Check with `pip --version`.

2. **Create a virtual environment**
	- Windows:
	  ```powershell
	  python -m venv .venv
	  .venv\Scripts\Activate.ps1
	  ```
	- Linux/macOS:
	  ```bash
	  python3 -m venv .venv
	  source .venv/bin/activate
	  ```


3. **Install dependencies**
	```bash
	pip install -r requirements.txt
	```

## Running the App

To start the application, run:

```bash
uvicorn internal.app.main:app --reload
```