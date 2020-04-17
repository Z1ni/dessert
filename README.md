# Dessert fetcher and parser

## How to run
Steps 2-4 are optional if you don't want to use virtualenv.

1. Install Python 3.8 (or newer)
2. Install virtualenv (if not installed)

   1. Open PowerShell / terminal
   2. Run `pip3 install virtualenv`
3. Create virtualenv

   1. Open PowerShell / terminal
   2. Navigate to the project folder
   3. Run `py -m virtualenv venv` (substitute `py` with `python3` on Linux/macOS)
4. Activate virtualenv

   Windows: Run `.\venv\Scripts\activate` in the project folder

   Linux/macOS: Run `./venv/bin/activate` in the project folder
5. Install dependencies

   Run `pip install -r requirements.txt`
6. Run `py .\main.py` (again, substitute `py` with `python3` if needed)
7. Check the created `list.txt` for a listing of desserts with their ingredients