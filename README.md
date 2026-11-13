# Text-to-SQL

A Python console app that uses Gemini to turn natural-language questions into
read-only SQL queries against a local SQLite sales database.

## Project files

- `create_db.py` creates `sales.db` and adds five sample customers and ten
  orders with prices in INR. It can be rerun safely.
- `text_to_sql.py` starts the interactive Text-to-SQL console.
- `.env` stores your Gemini API key locally and is excluded from Git.
- `requirements.txt` lists the Python packages used by the app.

SQLite is included with Python; it does not need a separate installation.

## Set up on Windows

The project has a `venv` virtual environment. If it does not exist, create it:

```powershell
py -m venv venv
```

Activate the environment and install the dependencies:

```powershell
.\venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

If PowerShell prevents environment activation, use
`.\venv\Scripts\python.exe` instead of `python` in the commands below.

## Configure a Gemini API key

1. Create a key in [Google AI Studio](https://aistudio.google.com/apikey).
2. In the project folder, create or open `.env` and add:

   ```env
   GEMINI_API_KEY=your_gemini_api_key
   ```

3. Replace the example value with your key, save the file, and keep it private.
   Never paste the key into chat, screenshots, source code, or a committed file.
   If a key has been shared, revoke it and create a replacement.

The script uses the `gemini-4-hydrogen` model through Google's OpenAI-compatible
Gemini API endpoint. Your question and database schema are sent to Gemini; the
generated SQL runs locally against `sales.db`.

## Create the database and start the console

From the project directory, run:

```powershell
python create_db.py
python text_to_sql.py
```

The console shows the database schema when it starts. Type a question at
`Enter your question:`. For example:

```text
Show total sales by customer
```

Available commands:

- `schema` - display the table definitions again.
- `quit` or `exit` - close the console.

Results are displayed in a table. Output is limited to 50 rows, and database
queries run in read-only mode.

## Troubleshooting

- If `sales.db` is missing, run `python create_db.py`.
- If `GEMINI_API_KEY` is missing, check that `.env` is in the project directory
  and that the key is assigned to `GEMINI_API_KEY`.
- If Gemini returns HTTP 429, check API quota and usage limits in
  [Google AI Studio](https://aistudio.google.com/).
