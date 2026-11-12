(() => {
  const cfg = window.POCKET_CONFIG || {};
  const storage = cfg.tokenStorage === "localStorage" ? localStorage : sessionStorage;
  const tokenKey = "pocket_server_access_token";
  const $ = (id) => document.getElementById(id);
  const apiUrl = (path) => `${cfg.apiBase || ""}${path}`;

  function getToken() { return storage.getItem(tokenKey); }
  function setToken(token) { storage.setItem(tokenKey, token); }
  function clearToken() { storage.removeItem(tokenKey); }
  function authHeaders(extra = {}) {
    const headers = { ...extra };
    const token = getToken();
    if (token) headers.Authorization = `Bearer ${token}`;
    return headers;
  }
  async function api(path, options = {}) {
    const response = await fetch(apiUrl(path), {
      ...options,
      headers: authHeaders(options.headers || {})
    });
    if (response.status === 401) {
      clearToken();
      if (!location.pathname.endsWith("/login") && !location.pathname.endsWith("/register")) location.href = "/ui/login";
    }
    return response;
  }
  async function responseMessage(response) {
    try {
      const data = await response.json();
      return data.detail || data.message || data.error || JSON.stringify(data);
    } catch { return `${response.status} ${response.statusText}`; }
  }
  function showMessage(el, text, kind = "error") {
    if (!el) return;
    el.textContent = text;
    el.className = `message ${kind}`;
  }

  // Authentication
  const loginForm = $("login-form");
  if (loginForm) {
    loginForm.addEventListener("submit", async (event) => {
      event.preventDefault();
      const button = loginForm.querySelector("button[type=submit]");
      const message = $("auth-message");
      const form = new FormData(loginForm);
      const username = form.get("username");
      const password = form.get("password");
      button.disabled = true; button.textContent = "Signing in…";
      try {
        let body, headers;
        if (cfg.loginBody === "json") {
          body = JSON.stringify({ username, password });
          headers = { "Content-Type": "application/json" };
        } else {
          body = new URLSearchParams({ username, password });
          headers = { "Content-Type": "application/x-www-form-urlencoded" };
        }
        const response = await fetch(apiUrl(cfg.login || "/auth/login"), { method: "POST", headers, body });
        if (!response.ok) throw new Error(await responseMessage(response));
        const data = await response.json();
        const token = (cfg.tokenKeys || ["access_token", "token"]).map(k => data[k]).find(Boolean);
        if (!token) throw new Error("Login succeeded, but no access token was found. Check tokenKeys in config.js.");
        setToken(token);
        location.href = "/ui";
      } catch (error) { showMessage(message, error.message); }
      finally { button.disabled = false; button.innerHTML = 'Sign in <span>→</span>'; }
    });
  }

  const registerForm = $("register-form");
  if (registerForm) {
    registerForm.addEventListener("submit", async (event) => {
      event.preventDefault();
      const button = registerForm.querySelector("button[type=submit]");
      const message = $("auth-message");
      const form = new FormData(registerForm);
      const payload = { username: form.get("username"), password: form.get("password") };
      if (form.get("email")) payload.email = form.get("email");
      button.disabled = true; button.textContent = "Creating account…";
      try {
        const response = await fetch(apiUrl(cfg.register || "/auth/register"), {
          method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(payload)
        });
        if (!response.ok) throw new Error(await responseMessage(response));
        showMessage(message, "Account created. You can now sign in.", "success");
        registerForm.reset();
        setTimeout(() => location.href = "/ui/login", 1100);
      } catch (error) { showMessage(message, error.message); }
      finally { button.disabled = false; button.innerHTML = 'Create account <span>→</span>'; }
    });
  }

  // Shared app controls
  document.querySelectorAll("[data-logout]").forEach(button => button.addEventListener("click", () => {
    clearToken(); location.href = "/ui/login";
  }));
  $("mobile-menu")?.addEventListener("click", () => $("sidebar")?.classList.toggle("open"));
  $("theme-toggle")?.addEventListener("click", () => document.body.classList.toggle("light-mode"));

  // Dashboard
  if ($("file-count")) {
    if (!getToken()) location.href = "/ui/login";
    loadFiles().then(files => {
      $("file-count").textContent = files.length;
      $("connection-state").textContent = "Online";
      $("connection-caption").textContent = "API responded successfully";
      $("user-label").textContent = "Account";
    }).catch(() => {
      $("connection-state").textContent = "Offline";
      $("connection-caption").textContent = "Could not reach file API";
      $("file-count").textContent = "—";
    });
  }

  // File manager
  if ($("file-list")) {
    if (!getToken()) location.href = "/ui/login";
    refreshFileList();
    $("refresh-files").addEventListener("click", refreshFileList);
    $("choose-upload").addEventListener("click", () => $("file-input").click());
    $("browse-files").addEventListener("click", () => $("file-input").click());
    $("file-input").addEventListener("change", (e) => uploadFiles([...e.target.files]));
    const drop = $("drop-zone");
    ["dragenter", "dragover"].forEach(name => drop.addEventListener(name, e => { e.preventDefault(); drop.classList.add("dragging"); }));
    ["dragleave", "drop"].forEach(name => drop.addEventListener(name, e => { e.preventDefault(); drop.classList.remove("dragging"); }));
    drop.addEventListener("drop", e => uploadFiles([...e.dataTransfer.files]));
  }

  async function loadFiles() {
    const response = await api(cfg.files || "/files");
    if (!response.ok) throw new Error(await responseMessage(response));
    const data = await response.json();
    if (Array.isArray(data)) return data;
    return data.files || data.items || data.results || [];
  }
  async function refreshFileList() {
    const list = $("file-list");
    if (!list) return;
    list.innerHTML = '<div class="loading-state">Fetching files from your server…</div>';
    try {
      const files = await loadFiles();
      $("file-subtitle").textContent = `${files.length} ${files.length === 1 ? "file" : "files"} stored`;
      if (!files.length) {
        list.innerHTML = '<div class="empty-state"><div class="empty-icon">▱</div><b>Your file space is empty</b><p>Upload your first file to get started.</p><button class="button primary" id="empty-upload">Upload a file</button></div>';
        $("empty-upload")?.addEventListener("click", () => $("file-input").click());
        return;
      }
      list.innerHTML = "";
      files.forEach(file => {
        const filename = typeof file === "string" ? file : (file.filename || file.name || file.file_name || file.key || "Unnamed file");
        const size = typeof file === "object" ? (file.size ?? file.size_bytes ?? file.file_size) : null;
        const row = document.createElement("div");
        row.className = "file-row";
        const icon = document.createElement("span"); icon.className = "file-type-icon"; icon.textContent = fileIcon(filename);
        const name = document.createElement("span"); name.className = "file-name"; name.textContent = filename; name.title = filename;
        const meta = document.createElement("span"); meta.className = "file-size"; meta.textContent = formatSize(size);
        const actions = document.createElement("span"); actions.className = "file-actions";
        const download = document.createElement("button"); download.className = "action-button"; download.textContent = "↓ Download"; download.addEventListener("click", () => downloadFile(filename));
        const del = document.createElement("button"); del.className = "action-button delete-action"; del.textContent = "Delete"; del.addEventListener("click", () => confirmDelete(filename));
        const identity = document.createElement("span"); identity.className = "file-identity"; identity.append(icon, name);
        actions.append(download, del); row.append(identity, meta, actions); list.append(row);
      });
    } catch (error) {
      $("file-subtitle").textContent = "Unable to load files";
      list.innerHTML = `<div class="error-state">${escapeHtml(error.message)}<br><small>Check the files endpoint in static/js/config.js.</small></div>`;
    }
  }
  function fileIcon(name) {
    const ext = name.split(".").pop().toLowerCase();
    if (["png","jpg","jpeg","gif","webp","svg"].includes(ext)) return "▧";
    if (["pdf","doc","docx","txt","md"].includes(ext)) return "▤";
    if (["zip","rar","7z","tar","gz"].includes(ext)) return "▣";
    return "▱";
  }
  function formatSize(bytes) {
    if (bytes === null || bytes === undefined || bytes === "") return "—";
    const n = Number(bytes); if (!Number.isFinite(n)) return "—";
    if (n < 1024) return `${n} B`;
    if (n < 1024 ** 2) return `${(n/1024).toFixed(1)} KB`;
    if (n < 1024 ** 3) return `${(n/1024**2).toFixed(1)} MB`;
    return `${(n/1024**3).toFixed(2)} GB`;
  }
  function escapeHtml(s) { return String(s).replace(/[&<>"']/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c])); }

  async function uploadFiles(files) {
    if (!files.length) return;
    const status = $("upload-progress");
    status.textContent = `Uploading ${files.length} file(s)…`;
    status.className = "upload-progress visible";
    for (const file of files) {
      try {
        const body = new FormData(); body.append("file", file);
        const response = await api(cfg.upload || "/upload", { method: "POST", body });
        if (!response.ok) throw new Error(await responseMessage(response));
        status.textContent = `✓ ${file.name} uploaded`;
      } catch (error) {
        status.textContent = `Could not upload ${file.name}: ${error.message}`;
        status.classList.add("failed");
        break;
      }
    }
    $("file-input").value = "";
    await refreshFileList();
    setTimeout(() => { status.className = "upload-progress"; }, 4500);
  }
  async function downloadFile(filename) {
    try {
      const response = await api((cfg.download || (name => `/download/${encodeURIComponent(name)}`))(filename));
      if (!response.ok) throw new Error(await responseMessage(response));
      const blob = await response.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a"); a.href = url; a.download = filename; document.body.appendChild(a); a.click(); a.remove();
      URL.revokeObjectURL(url);
    } catch (error) { alert(`Download failed: ${error.message}`); }
  }
  let pendingDelete = null;
  function confirmDelete(filename) {
    pendingDelete = filename;
    $("delete-filename").textContent = `“${filename}” will be permanently deleted.`;
    $("delete-modal").hidden = false;
  }
  $("cancel-delete")?.addEventListener("click", () => { $("delete-modal").hidden = true; pendingDelete = null; });
  $("delete-modal")?.addEventListener("click", e => { if (e.target.id === "delete-modal") $("delete-modal").hidden = true; });
  $("confirm-delete")?.addEventListener("click", async () => {
    if (!pendingDelete) return;
    const button = $("confirm-delete"); button.disabled = true; button.textContent = "Deleting…";
    try {
      const path = (cfg.deleteFile || (name => `/files/${encodeURIComponent(name)}`))(pendingDelete);
      const response = await api(path, { method: "DELETE" });
      if (!response.ok) throw new Error(await responseMessage(response));
      $("delete-modal").hidden = true; pendingDelete = null; await refreshFileList();
    } catch (error) { alert(`Delete failed: ${error.message}`); }
    finally { button.disabled = false; button.textContent = "Delete file"; }
  });
})();
