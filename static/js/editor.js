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
      // Show the ATS health score immediately on open (esp. for enhanced resumes).
      this.refreshScore();
      // Scale the preview to fit its column (no horizontal scrollbar).
      this.fitPreview();
      setTimeout(() => this.fitPreview(), 250);
      window.addEventListener("resize", () => this.fitPreview());
      // Put the cursor in the first field so "start here" is unmistakable.
      if (this.isEmptyResume) this.$nextTick(() => this.focusFirstField());
    },

    fitPreview() {
      const frame = document.querySelector(".rf-preview-frame");
      const prev = document.getElementById("preview");
      const doc = prev && prev.querySelector(".rf-doc");
      if (!frame || !prev || !doc) return;
      prev.style.transform = "none";
      const avail = frame.clientWidth - 32; // frame padding (16px each side)
      const scale = Math.min(1, avail / (doc.offsetWidth || 816));
      prev.style.transformOrigin = "top left";
      prev.style.transform = "scale(" + scale + ")";
      prev.style.height = doc.offsetHeight * scale + "px";
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
        this.fitPreview();
        this.savedAt = new Date();
        this.refreshScore();
      } catch (e) {
        this.saveError = "Network error while saving.";
      } finally {
        this.saving = false;
      }
    },

    // --- one-click AI polish (make the whole resume professional) ---
    polishing: false,
    async autoComplete() {
      if (!this.urls.polish || this.polishing) return;
      this.polishing = true;
      try {
        await this.save();  // persist current edits first
        const res = await fetch(this.urls.polish, {
          method: "POST",
          headers: { "Content-Type": "application/json", "X-CSRFToken": this.csrf },
          body: JSON.stringify({}),
        });
        if (res.ok) {
          const json = await res.json();
          if (json.ok) { window.location.reload(); return; }
        }
        this.saveError = "Couldn't polish — please try again.";
      } catch (e) {
        this.saveError = "Network error while polishing.";
      } finally {
        this.polishing = false;
      }
    },

    // --- onboarding / guided progress ---
    guideDismissed: false,
    STEPS: [
      { key: "basics", label: "Your details", hint: "Name, email, phone & a short summary" },
      { key: "work", label: "Work experience", hint: "Add roles — let AI write the bullets" },
      { key: "education", label: "Education", hint: "Degree, school & dates" },
      { key: "skills", label: "Skills", hint: "6+ keywords recruiters search for" },
    ],
    sectionDone(key) {
      const d = this.data || {};
      if (key === "basics") return !!((d.basics || {}).name && (d.basics || {}).email);
      if (key === "work") return (d.work || []).some((w) => w.position || w.company);
      if (key === "education") return (d.education || []).some((e) => e.institution || e.studyType);
      if (key === "skills") return (d.skills || []).some((s) => (s.keywords || []).length);
      return false;
    },
    get completedCount() { return this.STEPS.filter((s) => this.sectionDone(s.key)).length; },
    get progressPct() { return Math.round((this.completedCount / this.STEPS.length) * 100); },
    get nextStep() { return this.STEPS.find((s) => !this.sectionDone(s.key)) || null; },
    get showGuide() { return !this.guideDismissed && this.completedCount < this.STEPS.length; },
    get isEmptyResume() {
      const b = this.data.basics || {};
      return !b.name && !b.summary && !(this.data.work || []).length;
    },
    goToStep(key) {
      this.activeTab = key;
      // Make the next action ready: if a list section is empty, create the first
      // entry so the user lands on fields to fill, not a lone "+ Add" button.
      if (key === "work" && !(this.data.work || []).length) this.addWork();
      if (key === "education" && !(this.data.education || []).length) this.addEducation();
      if (key === "skills" && !(this.data.skills || []).length) this.addSkill();
      this.scrollFormTop();
      this.$nextTick(() => this.focusFirstField());
    },
    scrollFormTop() {
      const el = document.getElementById("editor-form-top");
      if (el) el.scrollIntoView({ behavior: "smooth", block: "start" });
    },
    focusFirstField() {
      // Focus the first VISIBLE input in the active form section.
      for (const el of document.querySelectorAll("section input, section textarea")) {
        if (el.offsetParent !== null) { el.focus(); break; }
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

    // --- AI hooks ---
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
