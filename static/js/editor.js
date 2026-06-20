/* ResumeForge editor — Alpine component.
   Holds the resume JSON, binds form fields, autosaves (debounced) by POSTing
   the data and swapping in the server-rendered preview HTML. */
function resumeEditor(config) {
  return {
    data: config.data,
    title: config.title,
    urls: config.urls,
    csrf: config.csrf,
    saving: false,
    savedAt: null,
    saveError: "",
    activeTab: "basics",
    _timer: null,

    init() {
      // Deep-watch the whole model; debounce saves.
      this.$watch("data", () => this.queueSave());
      this.$watch("title", () => this.queueSave());
    },

    queueSave() {
      clearTimeout(this._timer);
      this._timer = setTimeout(() => this.save(), 600);
    },

    async save() {
      this.saving = true;
      this.saveError = "";
      try {
        const res = await fetch(this.urls.autosave, {
          method: "POST",
          headers: { "Content-Type": "application/json", "X-CSRFToken": this.csrf },
          body: JSON.stringify({ data: this.data, title: this.title }),
        });
        if (!res.ok) {
          this.saveError = "Couldn't save changes.";
          return;
        }
        const html = await res.text();
        const preview = document.getElementById("preview");
        if (preview) preview.innerHTML = html;
        this.savedAt = new Date();
        this.refreshScore();
      } catch (e) {
        this.saveError = "Network error while saving.";
      } finally {
        this.saving = false;
      }
    },

    // --- array section helpers ---
    addWork() {
      this.data.work.push({ position: "", company: "", location: "", startDate: "", endDate: "", current: false, summary: "", highlights: [""] });
    },
    addEducation() {
      this.data.education.push({ studyType: "", area: "", institution: "", startDate: "", endDate: "", score: "" });
    },
    addSkill() { this.data.skills.push({ name: "", keywords: [] }); },
    addProject() { this.data.projects.push({ name: "", description: "", highlights: [""] }); },
    addCert() { this.data.certifications.push({ name: "", issuer: "", date: "" }); },
    addHighlight(item) { item.highlights.push(""); },
    remove(arr, idx) { arr.splice(idx, 1); },

    skillKeywords(skill) { return (skill.keywords || []).join(", "); },
    setSkillKeywords(skill, value) {
      skill.keywords = value.split(",").map((s) => s.trim()).filter(Boolean);
    },

    // --- AI hooks (wired in Phase 4); no-ops until then ---
    aiBusy: false,
    async aiImprove(path) {
      if (!this.urls.ai_improve) return;
      this.aiBusy = true;
      try {
        const res = await fetch(this.urls.ai_improve, {
          method: "POST",
          headers: { "Content-Type": "application/json", "X-CSRFToken": this.csrf },
          body: JSON.stringify({ field: path, text: this.getByPath(path), data: this.data }),
        });
        if (res.ok) {
          const json = await res.json();
          if (json.text) this.setByPath(path, json.text);
        }
      } finally { this.aiBusy = false; }
    },

    async aiGenerateBullets(jobIndex) {
      if (!this.urls.ai_bullets) return;
      this.aiBusy = true;
      try {
        const job = this.data.work[jobIndex];
        const res = await fetch(this.urls.ai_bullets, {
          method: "POST",
          headers: { "Content-Type": "application/json", "X-CSRFToken": this.csrf },
          body: JSON.stringify({ position: job.position, company: job.company, summary: job.summary }),
        });
        if (res.ok) {
          const json = await res.json();
          if (Array.isArray(json.bullets) && json.bullets.length) {
            job.highlights = json.bullets;
          }
        }
      } finally { this.aiBusy = false; }
    },

    async tailorToJob() {
      if (!this.urls.tailor || !this.data.__jd) return;
      this.aiBusy = true;
      try {
        // Persist the JD first so the server has it.
        await this.save();
        const res = await fetch(this.urls.tailor, {
          method: "POST",
          headers: { "Content-Type": "application/json", "X-CSRFToken": this.csrf },
          body: JSON.stringify({}),
        });
        if (res.ok) {
          const json = await res.json();
          if (json.ok) {
            if (json.ats != null) this.score = json.ats;
            if (json.match != null) this.match = json.match;
            // Reload to reflect AI-rewritten content in the form + preview.
            window.location.reload();
          }
        }
      } finally { this.aiBusy = false; }
    },

    // Resolve/assign a dotted path against this.data, e.g. "basics.summary".
    getByPath(path) {
      return path.split(".").reduce((o, k) => (o == null ? undefined : o[k]), this.data);
    },
    setByPath(path, value) {
      const keys = path.split(".");
      const last = keys.pop();
      const obj = keys.reduce((o, k) => (o == null ? undefined : o[k]), this.data);
      if (obj && typeof obj === "object") obj[last] = value;
    },

    // --- score panel (Phase 5) ---
    score: null,
    match: null,
    async refreshScore() {
      if (!this.urls.score) return;
      try {
        const res = await fetch(this.urls.score, {
          method: "POST",
          headers: { "Content-Type": "application/json", "X-CSRFToken": this.csrf },
          body: JSON.stringify({ data: this.data, jd: this.data.__jd || "" }),
        });
        if (res.ok) {
          const json = await res.json();
          this.score = json.ats || null;
          this.match = json.match || null;
        }
      } catch (e) { /* non-fatal */ }
    },
  };
}
