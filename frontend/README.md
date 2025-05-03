# Pulse Festival Frontend – Setup & Troubleshooting Guide

This guide explains how to set up the frontend for the Pulse University Festival project, using React, Vite, Tailwind CSS, and Axios inside WSL, along with a Python backend powered by Flask.

---

## 1. Installation Steps (WSL)

1. **Install Node.js via NVM** (Recommended for WSL):

   ```bash
   curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.7/install.sh | bash
   source ~/.bashrc
   nvm install --lts
   nvm use --lts
   ```

2. **Navigate to your project folder in frontend**:

3. **Install frontend dependencies**:

   ```bash
   npm install
   ```

4. **Install Vite React plugin** (only once):

   ```bash
   npm install --save-dev @vitejs/plugin-react
   ```

5. **Install frontend extras** (only once):

   ```bash
   npm install @uiw/react-codemirror @codemirror/lang-sql
   ```

6. **Install Flask backend dependencies** (only once):

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

## 3. Key Files Explained

### `package.json`

Defines your project and its dependencies:

```json
{
    "name": "pulse-frontend",
    "version": "1.0.0",
    "private": true,
    "scripts": {
        "dev": "vite",
        "build": "vite build",
        "preview": "vite preview"
    },
    "dependencies": {
        "axios": "^1.6.8",
        "react": "^18.2.0",
        "react-dom": "^18.2.0",
        "react-router-dom": "^6.22.3",
        "@uiw/react-codemirror": "^5.22.11",
        "@codemirror/lang-sql": "^6.1.4"
    },
    "devDependencies": {
        "@vitejs/plugin-react": "^4.2.1",
        "autoprefixer": "^10.4.17",
        "postcss": "^8.4.38",
        "tailwindcss": "^3.4.1",
        "vite": "^5.0.11"
    }
}
```

`package-lock.json` is automatically generated the **first time you run \`npm install\`**.
It locks exact dependency versions to ensure consistent installs across systems.
You should commit it to version control, but **you never need to edit it manually.**

---

### `vite.config.js`

```js
import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
    plugins: [react()],
    server: { port: 3000 }
});
```

---

### `tailwind.config.js`

```js
module.exports = {
    content: ["./index.html", "./src/**/*.{js,jsx,ts,tsx}"],
    theme: { extend: {} },
    plugins: []
};
```

---

### `postcss.config.js`

```js
module.exports = {
    plugins: {
        tailwindcss: {},
        autoprefixer: {}
    }
};
```

---

## 4. Running the Frontend/Backend

Once installed and both servers are running:

```bash
npm run dev              # Frontend
python3 frontend/api/serve.py  # Backend
```

Then open your browser to:
**[http://localhost:3000](http://localhost:3000)**

---

## 5. What You Can Do in the Web Interface

- **Login & Logout**: Secure entry with role-based backend CLI access
- **View Schema**: Browse tables, views, procedures, and triggers; inspect definitions
- **Browse Table Data**: Select a table and preview up to 100 rows; export as CSV/TXT
- **Run SQL Queries**: Use the built-in query console with syntax highlighting
- **Run CLI Commands**: Submit CLI commands like `q1`, `users list`, `create-db`, etc., and view their live output

---