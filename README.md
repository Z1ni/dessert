# Dessert fetcher and parser

## How to run
Steps 3-5 are optional if you don't want to use virtualenv.

1. Download the source code

   If you know how to use Git, just clone this repo.

   If you don't know how to use Git, download the files as a ZIP using [this link](https://github.com/Z1ni/dessert/archive/master.zip). Extract the ZIP somewhere where you want to run the program.
2. Install Python 3.8 (or newer)

   1. Go to https://www.python.org/downloads and download the installer
   2. Run the installer and press "Install Now" (or something like that in macOS)
3. Install virtualenv (if not installed)

   1. Open cmd / terminal (on Windows search for / press Win+R and type `cmd`)
   2. Run `py -m pip install virtualenv` (Windows) or `pip3 install virtualenv` (Linux/macOS)
4. Create virtualenv

   1. Open cmd / terminal
   2. Navigate to the project folder (using the `cd` command)
   3. Run `py -m virtualenv venv` (substitute `py` with `python3` on Linux/macOS)
5. Activate virtualenv

   Windows: Run `venv\Scripts\activate` in the project folder

   Linux/macOS: Run `./venv/bin/activate` in the project folder
6. Install dependencies

   Run `pip install -r requirements.txt`
7. Run `py main.py` (again, substitute `py` with `python3` if needed)
8. Check the created `list.txt` for a listing of desserts with their ingredients