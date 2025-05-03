# Pulse Festival Frontend – Setup & Troubleshooting Guide

This guide explains how to set up the frontend for the Pulse University Festival project, using React, Vite, Tailwind CSS, and Axios inside WSL, along with a Python backend powered by Flask **(requires Python 3.10 or newer)**.

---

## 1. Installation Steps (WSL)

1. **Install Node.js via NVM** (Recommended for WSL):

   ```bash
   curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.7/install.sh | bash
   source ~/.bashrc
   nvm install --lts
   nvm use --lts
   ```

2. **Navigate to your project folder in frontend**

3. **Install frontend dependencies**:

   ```bash
   npm install
   ```

4. **Install Vite React plugin**:

   ```bash
   npm install --save-dev @vitejs/plugin-react
   ```

5. **Install frontend extras**:

   ```bash
   npm install @uiw/react-codemirror @codemirror/lang-sql
   ```

6. **Install Flask backend dependencies**:

   ```bash
   pip install flask flask-cors mysql-connector-python
   ```

---

## 2. Common Issues & Fixes

### `ERR_INVALID_ARG_TYPE: Received undefined`

* Usually caused by missing `node` or broken `npm`
* Fix: Install Node using `nvm` and try again

### Long paths or permissions in OneDrive

* Avoid working in `OneDrive`, especially with non-ASCII characters
* Move the entire `DB25_137/` folder to: `C:\Projects\DB25_137`

### npm audit warnings

* Running `npm audit` may report moderate vulnerabilities
* Safe to ignore during dev
* Do **not** run `npm audit fix --force` — it may break Vite

---

## 3. Running the Frontend/Backend

Once installed and both servers are running, each one in a different terminal:

```bash
npm run dev              # Frontend, from inside the frontend folder
python3 frontend/src/api/serve.py  # Backend, from the project root
```

Then open your browser to:
**[http://localhost:3000](http://localhost:3000)**

---

## 4. What You Can Do in the Web Interface

- **Login & Logout**: Secure entry with role-based backend CLI access
- **View Schema**: Browse tables, views, procedures, and triggers; inspect definitions
- **Browse Table Data**: Select a table and preview up to 100 rows; export as CSV/TXT
- **Run SQL Queries**: Use the built-in query console with syntax highlighting
- **Run CLI Commands**: Submit CLI commands like `q1`, `users list`, `create-db`, etc., and view their live output

---
