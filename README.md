# Asklytics - Data Analytics Engine Documentation

## 1. Project Overview
**Project Name:** Asklytics (Data Analytics Engine)
**Purpose:** Asklytics is an AI-powered data analytics platform that allows users to upload business data files (CSV, Excel, PDF, Word) and interact with them using natural language. It acts as an autonomous data scientist, generating insights, answering questions, and building interactive dashboards dynamically.

## 2. Technology Stack
**Frontend:**
- **HTML5, Vanilla JavaScript, CSS**
- **Tailwind CSS (CDN)** for styling and responsive UI without needing a build step.
- **Plotly.js** for interactive chart rendering on the client side.
- **Lucide Icons** for clean, modern UI elements.

**Backend:**
- **Python 3**
- **FastAPI** (High-performance web framework for APIs)
- **Uvicorn** (ASGI server to run FastAPI)
- **Pandas & OpenPyXL** (Data manipulation and tabular data processing)
- **PyPDF & python-docx** (Text extraction from unstructured documents)
- **Plotly Express** (Generating visualization structures in Python)

**AI Core:**
- **Google Gemini API** (`google-genai` SDK) using the `gemini-2.5-flash` model.

---

## 3. Project Structure & File Usage
Here is a breakdown of the key files in the project and why they exist:

* **`app.py`**: The main FastAPI backend server. It defines all the API endpoints (`/api/analyze`, `/api/dashboard`, `/api/quick_insight`, `/api/dataset`). It receives files and user queries from the frontend, parses them, constructs a prompt for the AI, executes the AI-generated Python code securely, and sends the results back to the frontend.
* **`core_agent.py`**: The "brain" of the project. It contains the `SelfHealingAnalystEngine` class. It connects to the Google Gemini API to generate Python code based on the user's request and the data context. Most importantly, it has a self-healing loop: if the generated code fails to execute, it feeds the error back to the AI to fix the code and retries.
* **`file_parsers.py`**: Contains helper functions (`parse_structured_file`, `parse_unstructured_file`) to cleanly load and sanitize incoming files (CSV, XLSX, PDF, DOCX) into Pandas DataFrames or text strings, handling missing values and stripping white spaces.
* **`index.html`**: The complete frontend application. It contains the UI layout (Navbar, Chat View, Dashboard View, Dataset View), manages state, handles file uploads, makes asynchronous requests to the backend APIs, and renders the JSON responses (text insights and Plotly charts).
* **`requirements.txt`**: Lists all the necessary Python packages required to run the project.

---

## 4. How It Works (Step-by-Step in Easy Words)
1. **File Upload:** The user opens the web interface (`index.html`) and uploads one or more data files (like an Excel sheet or a PDF report, up to 3 at a time).
2. **Quick Scan:** The frontend immediately sends the files to the backend (`/api/quick_insight`). The backend quickly looks at the column names and data shape and uses the AI to generate a quick one-sentence summary and suggests 4 analytical questions the user might want to ask.
3. **User Asks a Question:** The user types a question in the chat box (e.g., "Show me the sales trend over time") and clicks send.
4. **Context Building:** The frontend sends the files and the question to the backend (`/api/analyze`). The backend reads the files using `file_parsers.py` and extracts a "sample" of the data (like the first 3 rows and column names) so the AI knows what the data looks like without having to read every single row (saving time and tokens).
5. **AI Code Generation:** The backend (`app.py`) gives this sample data and the user's question to the `SelfHealingAnalystEngine` (`core_agent.py`). It tells the AI: *"Write Python code using Pandas and Plotly to answer this question based on these columns."*
6. **Execution & Self-Healing:** The AI returns raw Python code. The backend attempts to run this code using an internal `exec()` environment.
   - *If it works:* The code produces a text insight and/or a chart object.
   - *If it crashes:* The engine catches the error, shows the error traceback to the AI, and says, "Fix this." It tries to fix itself up to 3 times automatically.
7. **Rendering Results:** Once successful, the text insight and the chart data (converted to JSON format) are sent back to `index.html`. The frontend displays the text and uses Plotly.js to draw the interactive chart on the screen.

---

## 5. Special Features
* **AI Code Generation on the Fly:** Instead of having hard-coded formulas for specific charts, the system writes custom Python code dynamically for every single user request. This makes it incredibly flexible to any kind of data.
* **Self-Healing Execution Engine:** If the AI writes faulty code (like referencing a column that doesn't exist or a syntax error), the system doesn't just crash. It catches the error and asks the AI to correct itself based on the traceback, significantly reducing failure rates.
* **Dynamic Executive Dashboard:** Users can click one button to generate a full dashboard. The AI automatically analyzes the dataset, finds anomalies, identifies key trends, and generates two highly relevant charts without any specific user prompting.
* **Expandable Dashboards:** Users can chat with the dashboard directly (via the "Add Insight" bar) to dynamically add specific new charts or text metric cards to it.
* **Multi-Format Support:** Can handle both structured tabular data (Excel/CSV) and unstructured text (PDF/Word) simultaneously.
* **Context-Aware Suggestions:** The AI constantly suggests the next logical questions a user should ask based on the current data and previous insights.
* **Branded Interface & Animations:** A highly polished, manager-grade user interface with a 5-second initial startup animation, robust tab navigation, and seamless state transitions.

---

## 6. Necessary Steps to Run the Project
1. **Prerequisites:** Ensure Python 3.8+ is installed on your machine.
2. **Environment Setup:** 
   - Open a terminal (PowerShell/Command Prompt) in the project folder.
   - Create a virtual environment: `python -m venv .venv`
   - Activate it: `.\.venv\Scripts\activate` (Windows)
3. **Install Dependencies:** 
   - Run `pip install -r requirements.txt` to install FastAPI, Pandas, Plotly, etc.
4. **API Key Setup:** 
   - Ensure a valid Google Gemini API key is configured. In `core_agent.py`, it is currently set using `os.environ["GEMINI_API_KEY"] = "YOUR_KEY"`.
5. **Start Backend Server:** 
   - Run the FastAPI application using Uvicorn by typing: `python app.py` (which runs the server on `127.0.0.1:8000`).
6. **Launch Frontend:** 
   - Open `index.html` directly in any modern web browser (e.g., Chrome, Edge) by double-clicking it. No separate frontend server is strictly needed, though using a "Live Server" extension in VS Code works great too.

---

## 7. Needs to Improve in Future (Scalability & Future Work)
* **Security & Sandboxing:** Currently, the app uses Python's `exec()` to run AI-generated code. While it runs locally for now, this is dangerous in a public cloud environment. Future versions need secure sandboxing (like Docker containers or WebAssembly/Pyodide) to run generated code safely without risking the host server.
* **Large File Handling:** The app currently reads entire datasets into active memory (RAM) via Pandas. For massive datasets (Gigabytes in size), it needs to integrate a real SQL database (like PostgreSQL or DuckDB) to query data efficiently instead of loading it all into memory.
* **Session Memory & Database Integration:** Implement a persistent database to store past chat history, saved dashboards, and user sessions so data is not lost when the browser page is refreshed.
* **Unstructured Dashboarding:** Expand the Executive Dashboard feature to analyze and summarize multiple PDF/Word documents, rather than currently being limited strictly to Tabular data.
* **Authentication & Authorization:** Add secure user login mechanisms to keep data private and secure per individual user or organization.
