# 🗄️ PocketNAS

### Your Personal Storage Server. Anywhere on Your Local Network.

PocketNAS is a lightweight, self-hosted Network Attached Storage (NAS) project designed to turn your existing device into a personal file server.

The goal is simple: make file storage, management, and sharing accessible through a web interface without depending on third-party cloud storage services.

Build your own personal storage ecosystem with control over your files and infrastructure.

---

## ✨ Features

- 📁 **File Management** — Browse and manage stored files.
- ⬆️ **File Upload** — Upload files to your personal server.
- ⬇️ **File Download** — Retrieve your stored files.
- 🔐 **Authentication** — Protected access to server functionality.
- 🗑️ **File Deletion** — Remove unwanted files.
- 🌐 **Web-Based Access** — Interact with your storage through a browser.

> Note: Backend functionality is under development alongside the web interface. Features and availability may change as the project evolves.

---

## 🛠️ Tech Stack

| Technology | Purpose |
|---|---|
| Python | Core programming language |
| FastAPI | Backend API framework |
| Uvicorn | ASGI server |
| HTML / CSS / JavaScript | Web interface |
| SQLite | Data persistence (where configured) |

---

## 📂 Project Goals

PocketNAS aims to evolve into a personal storage solution with:

- A clean and intuitive dashboard.
- Secure authentication and file access.
- Efficient file upload and download.
- Folder and file management.
- Local network accessibility.
- Lightweight resource consumption.
- Better control over personal data.

---

## 🚀 Getting Started

### 1. Clone the repository

```bash
git clone https://github.com/Karan-raut7/PocketNAS.git
```

### 2. Navigate to the project

```bash
cd PocketNAS
```

### 3. Create a virtual environment

```bash
python -m venv .venv
```

### 4. Activate the environment

**Windows PowerShell:**

```powershell
.venv\Scripts\Activate.ps1
```

**Linux / Termux:**

```bash
source .venv/bin/activate
```

### 5. Install dependencies

```bash
pip install -r requirements.txt
```

### 6. Start the server

The application entry point and startup command will be documented here as the project structure is finalized.

---

## 🔌 API Documentation

PocketNAS uses FastAPI for backend development.

When the server is running, interactive API documentation is available at:

```text
http://127.0.0.1:8000/docs
```

Alternative documentation:

```text
http://127.0.0.1:8000/redoc
```

---

## 🔒 Security

Security is an important part of PocketNAS.

The project aims to provide:

- Authenticated access.
- Protected file operations.
- Secure password handling.
- Controlled file uploads.
- Safer file management.

**Security notice:** PocketNAS is under active development. Do not expose an unfinished instance directly to the public internet or store sensitive data on an unsecured deployment.

---

## 🗺️ Roadmap

- [x] Initial backend development
- [x] File management operations
- [x] Authentication integration
- [ ] Complete web interface
- [ ] Responsive dashboard
- [ ] Improved upload validation
- [ ] Folder management
- [ ] Storage monitoring
- [ ] Mobile-friendly experience
- [ ] Remote access integration
- [ ] Security and performance improvements

---

## 🎯 Vision

The long-term vision of PocketNAS is to create a lightweight personal storage platform that gives users control over their own data.

No unnecessary complexity. No dependence on expensive cloud storage subscriptions. Just your own storage infrastructure.

---

## 👨‍💻 Author

**Karan Raut**

Developer and creator of PocketNAS.

- GitHub: [@Karan-raut7](https://github.com/Karan-raut7)
- Project: [PocketNAS](https://github.com/Karan-raut7/PocketNAS)

---

## 📜 License

This project is licensed under the [MIT License](LICENSE).