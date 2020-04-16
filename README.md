# Dessert fetcher and parser

## How to run
Steps 2 and 3 are optional if you don't want to use virtualenv.

1. Install Python 3.8 (or newer)
2. Create virtualenv

   1. Open PowerShell / terminal
   2. Navigate to the project folder
   3. Run `py -m virtualenv venv` (substitute `py` with `python3` on Linux/macOS)
3. Activate virtualenv

   Windows: Run `.\venv\Scripts\activate` in the project folder
   Linux/macOS: Run `./venv/bin/activate` in the project folder
4. Install dependencies

   Run `pip install -r requirements.txt`
5. Run `py .\main.py` (again, substitute `py` with `python3` if needed)
6. Check the created `list.txt` for a listing of desserts with their ingredients