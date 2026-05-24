/* ============================================================
   NutriFit AI — Frontend JS
   Talks to the FastAPI backend over fetch().
   ============================================================ */
(function () {
  const BACKEND = (window.NUTRIFIT && window.NUTRIFIT.backend) || "http://localhost:8000";
  const TOKEN_KEY = "nutrifit_token";
  const USER_KEY = "nutrifit_user";

  // ----------------------------- utils -----------------------------
  function getToken() { return localStorage.getItem(TOKEN_KEY); }
  function setAuth(token, user) {
    localStorage.setItem(TOKEN_KEY, token);
    localStorage.setItem(USER_KEY, JSON.stringify(user));
  }
  function getUser() {
    try { return JSON.parse(localStorage.getItem(USER_KEY) || "null"); } catch { return null; }
  }
  function clearAuth() {
    localStorage.removeItem(TOKEN_KEY);
    localStorage.removeItem(USER_KEY);
  }

  function authHeaders(extra = {}) {
    const headers = { ...extra };
    const t = getToken();
    if (t) headers["Authorization"] = "Bearer " + t;
    return headers;
  }

  async function api(path, { method = "GET", json, form, headers = {} } = {}) {
    const opts = { method, headers: authHeaders(headers) };
    if (json !== undefined) {
      opts.headers["Content-Type"] = "application/json";
      opts.body = JSON.stringify(json);
    } else if (form) {
      opts.body = form;
    }
    const res = await fetch(BACKEND + path, opts);
    const text = await res.text();
    let data;
    try { data = text ? JSON.parse(text) : {}; } catch { data = { raw: text }; }
    if (!res.ok) {
      const detail = data && data.detail
        ? (Array.isArray(data.detail) ? data.detail.map(d => d.msg || d).join(", ") : data.detail)
        : ("Request failed (" + res.status + ")");
      const err = new Error(detail);
      err.status = res.status;
      err.data = data;
      throw err;
    }
    return data;
  }

  function toast(msg, type = "info", ms = 3500) {
    const stack = document.getElementById("toast-stack");
    if (!stack) return;
    const el = document.createElement("div");
    el.className = "toast " + type;
    el.textContent = msg;
    stack.appendChild(el);
    setTimeout(() => { el.style.opacity = "0"; el.style.transform = "translateX(20px)"; }, ms - 250);
    setTimeout(() => el.remove(), ms);
  }

  function escapeHtml(s) {
    return String(s ?? "").replace(/[&<>"']/g, m => ({"&":"&amp;","<":"&lt;",">":"&gt;","\"":"&quot;","'":"&#39;"}[m]));
  }

  function fmtDate(iso) {
    if (!iso) return "";
    const d = new Date(iso);
    return d.toLocaleString(undefined, { month: "short", day: "numeric", hour: "2-digit", minute: "2-digit" });
  }

  function setError(input, msg) {
    const slot = document.querySelector(`[data-error-for="${input.id}"]`);
    if (msg) {
      input.classList.add("error");
      if (slot) slot.textContent = msg;
    } else {
      input.classList.remove("error");
      if (slot) slot.textContent = "";
    }
  }

  function imageUrl(path) {
    if (!path) return "";
    if (path.startsWith("http")) return path;
    return BACKEND + path;
  }

  // -------------------------- auth guard --------------------------
  function requireAuth() {
    const t = getToken();
    if (!t) {
      window.location.href = "/login";
      return false;
    }
    return true;
  }

  function bindLogout() {
    const link = document.getElementById("logout-link");
    if (link) {
      link.addEventListener("click", (e) => {
        e.preventDefault();
        clearAuth();
        toast("Signed out", "info");
        setTimeout(() => (window.location.href = "/"), 400);
      });
    }
  }

  function paintUserChip() {
    const u = getUser();
    if (!u) return;
    const name = document.getElementById("user-name");
    const role = document.getElementById("user-role");
    const avatar = document.getElementById("user-avatar");
    if (name) name.textContent = u.name || u.username;
    if (role) role.textContent = u.role || "user";
    if (avatar) avatar.textContent = (u.name || u.username || "·").charAt(0).toUpperCase();
  }

  // -------------------------- validators --------------------------
  function validateUsername(v) {
    if (!v) return "Username is required";
    if (v.length < 3) return "At least 3 characters";
    if (!/^[A-Za-z0-9_]+$/.test(v)) return "Only letters, numbers, _";
    return "";
  }
  function validateEmail(v) {
    if (!v) return "Email is required";
    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(v)) return "Invalid email";
    return "";
  }
  function validateMobile(v) {
    if (!v) return "Mobile is required";
    if (!/^\d{10}$/.test(v)) return "Exactly 10 digits";
    return "";
  }
  function validateName(v) {
    if (!v) return "Name is required";
    if (v.length < 2 || v.length > 50) return "2-50 characters";
    return "";
  }
  function passwordChecks(v) {
    return {
      length: v.length >= 8,
      upper: /[A-Z]/.test(v),
      lower: /[a-z]/.test(v),
      digit: /\d/.test(v),
      special: /[^A-Za-z0-9]/.test(v),
    };
  }
  function validatePassword(v) {
    const c = passwordChecks(v);
    if (!c.length) return "At least 8 characters";
    if (!c.upper) return "Needs an uppercase letter";
    if (!c.lower) return "Needs a lowercase letter";
    if (!c.digit) return "Needs a number";
    if (!c.special) return "Needs a special character";
    return "";
  }

  // -------------------------- LOGIN --------------------------
  function initLogin() {
    if (getToken()) { window.location.href = "/dashboard"; return; }
    const form = document.getElementById("login-form");
    const idEl = document.getElementById("login-id");
    const pwEl = document.getElementById("login-password");
    const btn = document.getElementById("login-submit");

    form.addEventListener("submit", async (e) => {
      e.preventDefault();
      setError(idEl, ""); setError(pwEl, "");
      if (!idEl.value.trim()) return setError(idEl, "Required");
      if (!pwEl.value) return setError(pwEl, "Required");
      btn.disabled = true; btn.innerHTML = '<span class="loader loader-inline"></span> Signing in…';
      try {
        const res = await api("/api/auth/login", {
          method: "POST",
          json: { username_or_email: idEl.value.trim(), password: pwEl.value },
        });
        setAuth(res.access_token, res.user);
        toast("Welcome back, " + res.user.name + "!", "success");
        setTimeout(() => (window.location.href = "/dashboard"), 350);
      } catch (err) {
        toast(err.message || "Login failed", "error");
      } finally {
        btn.disabled = false; btn.innerHTML = '<i class="fa-solid fa-right-to-bracket"></i> Sign in';
      }
    });
  }

  // -------------------------- REGISTER --------------------------
  function initRegister() {
    if (getToken()) { window.location.href = "/dashboard"; return; }

    let role = "user";
    const toggle = document.getElementById("role-toggle");
    const dietFields = document.getElementById("dietician-fields");
    toggle.querySelectorAll("button").forEach(b => {
      b.addEventListener("click", () => {
        toggle.querySelectorAll("button").forEach(x => x.classList.remove("active"));
        b.classList.add("active");
        role = b.dataset.role;
        dietFields.classList.toggle("hidden", role !== "dietician");
      });
    });

    const fields = {
      name: document.getElementById("reg-name"),
      username: document.getElementById("reg-username"),
      email: document.getElementById("reg-email"),
      mobile: document.getElementById("reg-mobile"),
      password: document.getElementById("reg-password"),
      speciality: document.getElementById("reg-speciality"),
      location: document.getElementById("reg-location"),
      rate1: document.getElementById("reg-rate-1"),
      rate2: document.getElementById("reg-rate-2"),
      bio: document.getElementById("reg-bio"),
    };

    fields.mobile.addEventListener("input", () => {
      fields.mobile.value = fields.mobile.value.replace(/\D/g, "").slice(0, 10);
    });

    const ruleEls = document.querySelectorAll("#password-rules li");
    fields.password.addEventListener("input", () => {
      const checks = passwordChecks(fields.password.value);
      ruleEls.forEach(li => {
        const ok = checks[li.dataset.rule];
        li.classList.toggle("ok", ok);
        li.classList.toggle("fail", !ok);
      });
    });

    const form = document.getElementById("register-form");
    const btn = document.getElementById("register-submit");

    form.addEventListener("submit", async (e) => {
      e.preventDefault();
      const errors = {
        name: validateName(fields.name.value.trim()),
        username: validateUsername(fields.username.value.trim()),
        email: validateEmail(fields.email.value.trim()),
        mobile: validateMobile(fields.mobile.value.trim()),
        password: validatePassword(fields.password.value),
      };
      Object.entries(errors).forEach(([k, msg]) => setError(fields[k], msg));
      if (Object.values(errors).some(Boolean)) return;

      const payload = {
        name: fields.name.value.trim(),
        username: fields.username.value.trim(),
        email: fields.email.value.trim(),
        mobile_number: fields.mobile.value.trim(),
        password: fields.password.value,
      };

      let endpoint = "/api/auth/register";
      if (role === "dietician") {
        if (!fields.speciality.value.trim()) return setError(fields.speciality, "Required");
        payload.speciality = fields.speciality.value.trim();
        payload.location = fields.location.value.trim();
        payload.per_hour_charge = Number(fields.rate1.value || 0);
        payload.per_two_hour_charge = Number(fields.rate2.value || 0);
        payload.bio = fields.bio.value.trim();
        endpoint = "/api/auth/register/dietician";
      }

      btn.disabled = true; btn.innerHTML = '<span class="loader loader-inline"></span> Creating…';
      try {
        const res = await api(endpoint, { method: "POST", json: payload });
        setAuth(res.access_token, res.user);
        toast("Account created! Welcome, " + res.user.name, "success");
        setTimeout(() => (window.location.href = "/dashboard"), 400);
      } catch (err) {
        toast(err.message || "Registration failed", "error");
      } finally {
        btn.disabled = false; btn.innerHTML = '<i class="fa-solid fa-user-plus"></i> Create account';
      }
    });
  }

  // -------------------------- DASHBOARD --------------------------
  function initDashboard() {
    if (!requireAuth()) return;
    bindLogout();
    paintUserChip();

    const u = getUser();
    document.getElementById("welcome-name").textContent = u ? u.name : "";

    api("/api/dashboard/summary").then(s => {
      document.getElementById("welcome-name").textContent = s.name || "";

      // weekly chart
      document.getElementById("wk-cal").textContent = Math.round(s.weekly_nutrition.calories);
      document.getElementById("wk-prot").textContent = Math.round(s.weekly_nutrition.protein);
      document.getElementById("wk-carb").textContent = Math.round(s.weekly_nutrition.carbs);
      document.getElementById("wk-fat").textContent = Math.round(s.weekly_nutrition.fat);

      const ctx = document.getElementById("nutrition-chart");
      if (window.Chart && ctx) {
        const labels = (s.weekly_chart.labels || []).map(d => d.slice(5));
        new Chart(ctx, {
          type: "line",
          data: {
            labels: labels.length ? labels : ["—"],
            datasets: [
              { label: "kcal", data: s.weekly_chart.calories || [], borderColor: "#00d4aa", backgroundColor: "rgba(0,212,170,0.18)", tension: 0.35, fill: true },
              { label: "protein g", data: s.weekly_chart.protein || [], borderColor: "#7c3aed", backgroundColor: "rgba(124,58,237,0.12)", tension: 0.35, fill: false },
            ],
          },
          options: {
            responsive: true,
            plugins: { legend: { labels: { color: "#b9c7c2" } } },
            scales: {
              x: { ticks: { color: "#92a39e" }, grid: { color: "rgba(255,255,255,0.05)" } },
              y: { ticks: { color: "#92a39e" }, grid: { color: "rgba(255,255,255,0.05)" } },
            },
          },
        });
      }

      // recent meals
      const meals = s.recent_meals || [];
      const mealsEl = document.getElementById("recent-meals");
      if (!meals.length) mealsEl.innerHTML = '<div class="empty">No meals logged yet.</div>';
      else mealsEl.innerHTML = meals.map(m => `
        <div class="meal-row">
          <img src="${imageUrl(m.image_url)}" alt="" />
          <div class="meta">
            <div class="name">${escapeHtml(m.food_detected || "Meal")}</div>
            <div class="small">${fmtDate(m.logged_at)} · score ${escapeHtml(m.health_score || "—")}</div>
          </div>
        </div>`).join("");

      // recent activities
      const acts = s.recent_activities || [];
      const actEl = document.getElementById("recent-activities");
      if (!acts.length) actEl.innerHTML = '<div class="empty">No activities logged yet.</div>';
      else actEl.innerHTML = acts.map(a => `
        <div class="meal-row">
          <div class="avatar" style="width:42px;height:42px;border-radius:12px;background:var(--surface);display:grid;place-items:center;color:var(--accent)"><i class="fa-solid fa-${activityIcon(a.log_type)}"></i></div>
          <div class="meta">
            <div class="name">${escapeHtml(a.description)}</div>
            <div class="small">${fmtDate(a.logged_at)} · ${escapeHtml(a.value || "")} ${escapeHtml(a.unit || "")} · ${a.logged_via}</div>
          </div>
        </div>`).join("");
    }).catch(err => {
      if (err.status === 401) { clearAuth(); window.location.href = "/login"; return; }
      toast("Could not load dashboard: " + err.message, "error");
    });

    api("/api/dashboard/suggestions").then(sg => {
      document.getElementById("diet-suggestion").textContent = sg.diet_today || "—";
      document.getElementById("workout-suggestion").textContent = sg.workout_today || "—";
      const il = document.getElementById("insights-list");
      if (sg.insights && sg.insights.length) {
        il.innerHTML = sg.insights.map(i => `<li>${escapeHtml(i)}</li>`).join("");
      } else {
        il.innerHTML = '<li class="muted">Log a few meals and activities so I can tailor this.</li>';
      }
    }).catch(err => {
      document.getElementById("diet-suggestion").textContent = "AI is unavailable right now.";
      document.getElementById("workout-suggestion").textContent = "AI is unavailable right now.";
      document.getElementById("insights-list").innerHTML = '<li class="muted">' + escapeHtml(err.message) + '</li>';
    });
  }

  function activityIcon(t) {
    return ({ exercise: "dumbbell", walk: "person-walking", food_intake: "apple-whole", custom: "star" })[t] || "circle";
  }

  // -------------------------- MEAL SCAN --------------------------
  function initMealScan() {
    if (!requireAuth()) return;
    bindLogout(); paintUserChip();

    const dz = document.getElementById("dropzone");
    const fi = document.getElementById("meal-file");
    const preview = document.getElementById("preview");
    const analyzeBtn = document.getElementById("analyze-btn");
    const resetBtn = document.getElementById("reset-btn");

    let chosen = null;

    function pickFile(file) {
      if (!file) return;
      if (!file.type.startsWith("image/")) return toast("Please choose an image", "error");
      if (file.size > 25 * 1024 * 1024) return toast("Max 25MB", "error");
      chosen = file;
      const url = URL.createObjectURL(file);
      preview.src = url; preview.classList.remove("hidden");
      analyzeBtn.disabled = false;
    }

    dz.addEventListener("click", () => fi.click());
    fi.addEventListener("change", (e) => pickFile(e.target.files[0]));
    ["dragover", "dragenter"].forEach(ev => dz.addEventListener(ev, e => { e.preventDefault(); dz.classList.add("dragover"); }));
    ["dragleave", "drop"].forEach(ev => dz.addEventListener(ev, e => { e.preventDefault(); dz.classList.remove("dragover"); }));
    dz.addEventListener("drop", e => pickFile(e.dataTransfer.files[0]));

    resetBtn.addEventListener("click", () => {
      chosen = null; fi.value = ""; preview.src = ""; preview.classList.add("hidden");
      analyzeBtn.disabled = true;
      document.getElementById("result").classList.add("hidden");
      document.getElementById("result-empty").classList.remove("hidden");
    });

    analyzeBtn.addEventListener("click", async () => {
      if (!chosen) return;
      const fd = new FormData();
      fd.append("image", chosen);
      document.getElementById("result-empty").classList.add("hidden");
      document.getElementById("result").classList.add("hidden");
      document.getElementById("result-loading").classList.remove("hidden");
      analyzeBtn.disabled = true;
      try {
        const data = await api("/api/meal/analyze", { method: "POST", form: fd });
        renderMealResult(data);
        toast("Analyzed!", "success");
        loadHistory();
      } catch (err) {
        toast("Analysis failed: " + err.message, "error");
        document.getElementById("result-empty").classList.remove("hidden");
      } finally {
        document.getElementById("result-loading").classList.add("hidden");
        analyzeBtn.disabled = false;
      }
    });

    document.getElementById("refresh-history").addEventListener("click", loadHistory);
    loadHistory();

    function loadHistory() {
      api("/api/meal/history?limit=12").then(rows => {
        const wrap = document.getElementById("history");
        if (!rows.length) { wrap.innerHTML = '<div class="empty">No meals logged yet.</div>'; return; }
        wrap.innerHTML = rows.map(m => `
          <div class="meal-row">
            <img src="${imageUrl(m.image_url)}" alt="" />
            <div class="meta">
              <div class="name">${escapeHtml(m.food_detected || "Meal")}</div>
              <div class="small">${fmtDate(m.logged_at)} · score ${escapeHtml(m.health_score || "—")} · ${m.macronutrients ? Math.round(m.macronutrients.calories_kcal || 0) : 0} kcal</div>
            </div>
          </div>`).join("");
      });
    }
  }

  function renderMealResult(d) {
    document.getElementById("result").classList.remove("hidden");
    document.getElementById("r-food").textContent = (d.food_detected || []).join(", ") || "—";
    document.getElementById("r-score").textContent = (d.health_score || 0).toFixed(1);
    document.getElementById("r-summary").textContent = d.raw_response || "";
    const macroBars = [
      { name: "Calories (kcal)", key: "calories_kcal", max: 1200 },
      { name: "Protein (g)", key: "protein_g", max: 60 },
      { name: "Carbs (g)", key: "carbohydrates_g", max: 150 },
      { name: "Fats (g)", key: "fats_g", max: 60 },
      { name: "Fiber (g)", key: "fiber_g", max: 30 },
      { name: "Sugar (g)", key: "sugar_g", max: 40 },
    ];
    document.getElementById("r-macros").innerHTML = macroBars.map(b => bar(b.name, d.macronutrients[b.key], b.max)).join("");
    const microBars = [
      { name: "Vitamin A (mcg)", key: "vitamin_a_mcg", max: 900 },
      { name: "Vitamin C (mg)", key: "vitamin_c_mg", max: 90 },
      { name: "Vitamin D (mcg)", key: "vitamin_d_mcg", max: 20 },
      { name: "Vitamin B12 (mcg)", key: "vitamin_b12_mcg", max: 2.4 },
      { name: "Iron (mg)", key: "iron_mg", max: 18 },
      { name: "Calcium (mg)", key: "calcium_mg", max: 1000 },
      { name: "Potassium (mg)", key: "potassium_mg", max: 3500 },
      { name: "Sodium (mg)", key: "sodium_mg", max: 2300 },
      { name: "Zinc (mg)", key: "zinc_mg", max: 11 },
      { name: "Magnesium (mg)", key: "magnesium_mg", max: 400 },
    ];
    document.getElementById("r-micros").innerHTML = microBars.map(b => bar(b.name, d.micronutrients[b.key], b.max)).join("");
    document.getElementById("r-good").innerHTML = (d.advice_good || [])
      .map(x => `<div class="advice-card advice-good"><div class="title"><i class="fa-solid fa-check"></i> Good</div>${escapeHtml(x)}</div>`).join("");
    document.getElementById("r-bad").innerHTML = (d.advice_bad || [])
      .map(x => `<div class="advice-card advice-bad"><div class="title"><i class="fa-solid fa-triangle-exclamation"></i> Watch</div>${escapeHtml(x)}</div>`).join("");
  }

  function bar(name, value, max) {
    const v = Number(value || 0);
    const pct = Math.min(100, Math.max(2, (v / max) * 100));
    return `<div class="nutrient-row">
      <div class="name">${escapeHtml(name)}</div>
      <div class="bar"><span style="width:${pct}%"></span></div>
      <div class="value">${v}</div>
    </div>`;
  }

  // -------------------------- RAG CHAT --------------------------
  function initRagChat() {
    if (!requireAuth()) return;
    bindLogout(); paintUserChip();

    const win = document.getElementById("chat-window");
    const input = document.getElementById("chat-input");
    const sendBtn = document.getElementById("send-btn");
    const fileBtn = document.getElementById("attach-btn");
    const fi = document.getElementById("chat-file");
    const attached = document.getElementById("attached-name");
    let attachedFile = null;

    function appendMessage(role, text, sources) {
      const wrap = document.createElement("div");
      wrap.className = "message " + role;
      const bubble = document.createElement("div");
      bubble.className = "bubble";
      bubble.textContent = text;
      wrap.appendChild(bubble);
      if (sources && sources.length) {
        const sb = document.createElement("div"); sb.className = "sources";
        sources.forEach(s => { const c = document.createElement("span"); c.textContent = s.title; sb.appendChild(c); });
        bubble.appendChild(sb);
      }
      win.appendChild(wrap);
      win.scrollTop = win.scrollHeight;
      return wrap;
    }

    function appendTyping() {
      const wrap = document.createElement("div");
      wrap.className = "message assistant typing-row";
      wrap.innerHTML = '<div class="bubble"><span class="typing"><span></span><span></span><span></span></span></div>';
      win.appendChild(wrap); win.scrollTop = win.scrollHeight;
      return wrap;
    }

    fileBtn.addEventListener("click", () => fi.click());
    fi.addEventListener("change", () => {
      attachedFile = fi.files[0] || null;
      attached.textContent = attachedFile ? `📎 ${attachedFile.name}` : "";
    });

    async function send() {
      const q = input.value.trim();
      if (!q && !attachedFile) return;
      const display = (attachedFile ? `[image: ${attachedFile.name}] ` : "") + q;
      appendMessage("user", display);
      input.value = ""; sendBtn.disabled = true;
      const typing = appendTyping();
      try {
        let res;
        if (attachedFile) {
          const fd = new FormData();
          fd.append("question", q);
          fd.append("image", attachedFile);
          res = await api("/api/rag/chat-with-image", { method: "POST", form: fd });
          attachedFile = null; fi.value = ""; attached.textContent = "";
        } else {
          res = await api("/api/rag/chat", { method: "POST", json: { question: q } });
        }
        typing.remove();
        appendMessage("assistant", res.answer || "(no answer)", res.sources);
      } catch (err) {
        typing.remove();
        appendMessage("assistant", "Sorry, AI is unavailable: " + err.message);
      } finally {
        sendBtn.disabled = false;
      }
    }

    sendBtn.addEventListener("click", send);
    input.addEventListener("keydown", e => {
      if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); send(); }
    });

    // load history
    api("/api/rag/history").then(rows => {
      rows.forEach(r => appendMessage(r.role === "user" ? "user" : "assistant", r.message));
    }).catch(() => {});
  }

  // -------------------------- DIETICIANS --------------------------
  function initDieticians() {
    if (!requireAuth()) return;
    bindLogout(); paintUserChip();
    document.getElementById("refresh-dieticians").addEventListener("click", load);
    load();

    function load() {
      const grid = document.getElementById("dieticians-grid");
      grid.innerHTML = '<div class="empty" style="grid-column:1/-1;">Loading…</div>';
      api("/api/dieticians/").then(rows => {
        if (!rows.length) { grid.innerHTML = '<div class="empty" style="grid-column:1/-1;">No dieticians registered yet.</div>'; return; }
        grid.innerHTML = rows.map(d => `
          <div class="card dietician-card">
            <div class="head">
              <div class="avatar">${escapeHtml((d.name || "?").charAt(0).toUpperCase())}</div>
              <div>
                <div class="name">${escapeHtml(d.name)}</div>
                <div class="speciality">${escapeHtml(d.speciality)}${d.location ? " · " + escapeHtml(d.location) : ""}</div>
              </div>
            </div>
            <div class="charges">
              <div class="chip">1 hr · <strong>₹${Number(d.per_hour_charge).toLocaleString()}</strong></div>
              <div class="chip">2 hr · <strong>₹${Number(d.per_two_hour_charge).toLocaleString()}</strong></div>
              ${d.is_available ? '<span class="badge">Available</span>' : '<span class="badge danger">Busy</span>'}
            </div>
            <div class="bio">${escapeHtml(d.bio || "")}</div>
            <button class="btn small book-btn" data-id="${d.id}"><i class="fa-solid fa-calendar-check"></i> Book Now</button>
          </div>
        `).join("");
        grid.querySelectorAll(".book-btn").forEach(b => b.addEventListener("click", () => bookDietician(b.dataset.id)));
      });
    }

    async function bookDietician(id) {
      try {
        const c = await api("/api/dieticians/book", { method: "POST", json: { dietician_id: id } });
        toast("Consultation booked! Open Consultations to upload the recording.", "success");
      } catch (err) { toast(err.message, "error"); }
    }
  }

  // -------------------------- CONSULTATIONS --------------------------
  function initConsultations() {
    if (!requireAuth()) return;
    bindLogout(); paintUserChip();
    document.getElementById("refresh-consultations").addEventListener("click", load);
    load();

    function load() {
      const wrap = document.getElementById("consultations-list");
      wrap.innerHTML = '<div class="empty">Loading…</div>';
      api("/api/consultations/").then(rows => {
        if (!rows.length) { wrap.innerHTML = '<div class="empty">No consultations yet. Book a dietician to get started.</div>'; return; }
        wrap.innerHTML = "";
        rows.forEach(c => wrap.appendChild(consultationCard(c)));
      }).catch(err => { wrap.innerHTML = '<div class="empty">Failed: ' + escapeHtml(err.message) + '</div>'; });
    }

    function consultationCard(c) {
      const card = document.createElement("div");
      card.className = "card";
      const status = c.status === "completed" ? "badge" : (c.status === "cancelled" ? "badge danger" : "badge purple");
      card.innerHTML = `
        <div class="row-flex" style="justify-content:space-between;">
          <div>
            <div style="font-weight:600;">${escapeHtml(c.dietician_name || "Dietician")}</div>
            <div class="muted" style="font-size:13px;">Scheduled ${fmtDate(c.scheduled_at)}</div>
          </div>
          <span class="${status}">${escapeHtml(c.status)}</span>
        </div>
        <div class="spacer" style="height:10px"></div>
        ${c.has_recording ? "" : `
          <div class="row-flex">
            <input type="file" accept="audio/*" class="rec-file" style="display:none" />
            <button class="btn small upload-btn"><i class="fa-solid fa-microphone"></i> Upload recording</button>
            <span class="muted" style="font-size:12px;">.mp3 / .wav / .m4a / .webm</span>
          </div>
        `}
        ${c.llm_summary ? `<div style="margin-top:14px;"><h3>AI Summary</h3><div style="white-space:pre-wrap; font-size:14px;">${escapeHtml(c.llm_summary)}</div></div>` : ""}
        ${c.transcript ? `<details style="margin-top:10px;"><summary class="muted" style="cursor:pointer;">Show full transcript</summary><div style="white-space:pre-wrap; font-size:13px; margin-top:8px;">${escapeHtml(c.transcript)}</div></details>` : ""}
        ${c.transcript ? `
          <div class="spacer"></div>
          <h3>Ask AI about this consultation</h3>
          <div class="row-flex" style="gap:8px;">
            <input class="input ask-q" placeholder="What did the dietician say about my protein intake?" style="flex:1;" />
            <button class="btn small ask-btn"><i class="fa-solid fa-paper-plane"></i></button>
          </div>
          <div class="muted ask-out" style="margin-top:10px; white-space:pre-wrap;"></div>
        ` : ""}
      `;
      const fileInput = card.querySelector(".rec-file");
      const uploadBtn = card.querySelector(".upload-btn");
      if (uploadBtn) {
        uploadBtn.addEventListener("click", () => fileInput.click());
        fileInput.addEventListener("change", async () => {
          if (!fileInput.files.length) return;
          const fd = new FormData(); fd.append("audio", fileInput.files[0]);
          uploadBtn.disabled = true;
          uploadBtn.innerHTML = '<span class="loader loader-inline"></span> Transcribing & summarizing…';
          try {
            await api(`/api/consultations/${c.id}/upload-recording`, { method: "POST", form: fd });
            toast("Recording uploaded — AI summary is ready.", "success");
            load();
          } catch (err) {
            toast("Upload failed: " + err.message, "error");
            uploadBtn.disabled = false;
            uploadBtn.innerHTML = '<i class="fa-solid fa-microphone"></i> Upload recording';
          }
        });
      }
      const askBtn = card.querySelector(".ask-btn");
      if (askBtn) {
        askBtn.addEventListener("click", async () => {
          const q = card.querySelector(".ask-q").value.trim();
          const out = card.querySelector(".ask-out");
          if (!q) return;
          out.innerHTML = '<span class="loader loader-inline"></span> thinking…';
          try {
            const res = await api(`/api/consultations/${c.id}/ask`, { method: "POST", json: { question: q } });
            out.textContent = res.answer || "(no answer)";
          } catch (err) { out.textContent = "Failed: " + err.message; }
        });
      }
      return card;
    }
  }

  // -------------------------- ACTIVITY --------------------------
  function initActivity() {
    if (!requireAuth()) return;
    bindLogout(); paintUserChip();

    const form = document.getElementById("activity-form");
    form.addEventListener("submit", async e => {
      e.preventDefault();
      const payload = {
        log_type: document.getElementById("act-type").value,
        description: document.getElementById("act-desc").value.trim(),
        value: document.getElementById("act-value").value.trim() || null,
        unit: document.getElementById("act-unit").value.trim() || null,
      };
      if (!payload.description) return toast("Description required", "error");
      try {
        await api("/api/activity/log", { method: "POST", json: payload });
        toast("Logged!", "success");
        form.reset();
        loadHistory();
      } catch (err) { toast(err.message, "error"); }
    });

    document.getElementById("ask-btn").addEventListener("click", async () => {
      const q = document.getElementById("ask-q").value.trim();
      const days = Number(document.getElementById("ask-window").value);
      const out = document.getElementById("ask-answer");
      if (!q) return;
      out.innerHTML = '<span class="loader loader-inline"></span> thinking…';
      try {
        const res = await api("/api/activity/ask", { method: "POST", json: { question: q, window_days: days } });
        out.textContent = res.answer || "(no answer)";
      } catch (err) { out.textContent = "Failed: " + err.message; }
    });

    loadHistory();

    function loadHistory() {
      api("/api/activity/history?limit=100").then(rows => {
        const tb = document.querySelector("#activity-table tbody");
        if (!rows.length) { tb.innerHTML = '<tr><td colspan="6" class="muted" style="text-align:center;">No entries yet.</td></tr>'; return; }
        tb.innerHTML = rows.map(r => `
          <tr>
            <td>${fmtDate(r.logged_at)}</td>
            <td><span class="badge">${escapeHtml(r.log_type)}</span></td>
            <td>${escapeHtml(r.description)}</td>
            <td>${escapeHtml(r.value || "—")}</td>
            <td>${escapeHtml(r.unit || "—")}</td>
            <td>${escapeHtml(r.logged_via)}</td>
          </tr>`).join("");
      });
    }
  }

  // -------------------------- export --------------------------
  window.NutriFit = {
    initLogin, initRegister, initDashboard, initMealScan, initRagChat,
    initDieticians, initConsultations, initActivity,
  };
})();
