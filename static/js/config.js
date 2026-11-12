/*
 * Pocket Server frontend API settings.
 * Adjust these values to match your existing FastAPI routes and schemas.
 */
window.POCKET_CONFIG = {
  apiBase: "",                    // same-origin by default
  login: "/auth/login",
  register: "/auth/register",
  files: "/files",
  upload: "/upload",
  download: (filename) => `/download/${encodeURIComponent(filename)}`,
  deleteFile: (filename) => `/files/${encodeURIComponent(filename)}`,
  tokenStorage: "sessionStorage",
  // Set to "form" for OAuth2PasswordRequestForm (username/password form fields).
  // Set to "json" if your login endpoint expects JSON.
  loginBody: "form",
  // If your API uses a different token property, add it here.
  tokenKeys: ["access_token", "token"]
};
