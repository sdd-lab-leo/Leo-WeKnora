import "./styles/main.css";

type Doc = {
  id: string;
  title: string;
  source_name: string;
  chunk_count: number;
  has_wiki: number | boolean;
  created_at: string;
};

type WikiPage = {
  id: string;
  slug: string;
  title: string;
  document_id: string;
  document_title?: string;
  markdown?: string;
  updated_at: string;
};

type Citation = {
  chunk_id: string;
  document_title: string;
  ordinal: number;
  snippet: string;
};

type AskResult = {
  answer: string;
  citations: Citation[];
  steps?: Array<{ step: number; thought?: string; observation?: string }>;
  session_id: string;
  mode: string;
};

const api = {
  async get<T>(path: string): Promise<T> {
    const res = await fetch(path);
    if (!res.ok) throw new Error(await res.text());
    return res.json();
  },
  async send<T>(path: string, init?: RequestInit): Promise<T> {
    const res = await fetch(path, init);
    if (!res.ok) throw new Error(await res.text());
    return res.json();
  },
};

const state = {
  mode: "rag" as "rag" | "agent",
  panel: "chat" as "chat" | "knowledge" | "wiki",
  sessionId: "" as string,
  docs: [] as Doc[],
  wiki: [] as WikiPage[],
  selectedDocId: "" as string,
  selectedWikiSlug: "" as string,
};

const app = document.querySelector<HTMLDivElement>("#app")!;

app.innerHTML = `
  <section class="landing" id="landing">
    <div class="stage">
      <p class="meta-line">Living knowledge prototype</p>
      <h1 class="brand-mark">KOR<span>A</span></h1>
      <p class="lede">
        把文档变成可检索、可推理、可持续演进的知识。
        RAG 问答、Agent 工具循环、Wiki 蒸馏 —— 同一条本地流水线。
      </p>
      <div class="cta-row">
        <button class="btn btn-primary" id="enter-btn">进入工作台</button>
        <button class="btn btn-ghost" id="seed-hint-btn">先导入示例文档</button>
      </div>
      <p class="meta-line" id="health-line">checking API…</p>
    </div>
  </section>

  <section class="shell" id="shell">
    <div class="stage">
      <header class="topbar">
        <div class="logo">Kora</div>
        <nav class="nav">
          <button data-panel="chat" class="active">对话</button>
          <button data-panel="knowledge">知识库</button>
          <button data-panel="wiki">Wiki</button>
        </nav>
        <div class="status-pill" id="model-pill">models</div>
      </header>

      <div class="workspace">
        <aside class="side">
          <h2>Documents</h2>
          <div class="doc-list" id="doc-list"></div>
          <div class="upload-box">
            <input type="file" id="file-input" accept=".md,.txt,.markdown,.pdf,.csv,.json" />
            <button class="btn btn-primary btn-small" id="upload-btn">上传并入库</button>
            <button class="btn btn-ghost btn-small" id="seed-btn">导入示例</button>
          </div>
          <div style="margin-top:1.25rem">
            <h2>Wiki pages</h2>
            <div class="wiki-list" id="wiki-list"></div>
          </div>
        </aside>

        <main>
          <section class="panel chat-panel active" id="panel-chat">
            <div class="mode-switch">
              <button data-mode="rag" class="active">RAG</button>
              <button data-mode="agent">Agent</button>
            </div>
            <div class="messages" id="messages">
              <div class="empty">提出一个问题。Kora 会检索本地知识并给出引用。</div>
            </div>
            <form class="composer" id="ask-form">
              <textarea id="ask-input" placeholder="例如：Kora 的混合检索怎么工作？"></textarea>
              <button class="btn btn-primary" type="submit">发送</button>
            </form>
          </section>

          <section class="panel knowledge-panel" id="panel-knowledge">
            <div class="empty" id="knowledge-empty">选择左侧文档查看内容与分块。</div>
            <div class="reader hidden" id="knowledge-reader">
              <h3 id="knowledge-title"></h3>
              <div class="row-actions">
                <button class="btn btn-ghost btn-small" id="distill-btn">蒸馏为 Wiki</button>
                <button class="btn btn-ghost btn-small" id="delete-btn">删除</button>
              </div>
              <pre id="knowledge-body"></pre>
            </div>
          </section>

          <section class="panel wiki-panel" id="panel-wiki">
            <div class="empty" id="wiki-empty">还没有 Wiki 页。在知识库中选择文档并蒸馏。</div>
            <div class="reader hidden" id="wiki-reader">
              <h3 id="wiki-title"></h3>
              <div class="md" id="wiki-body"></div>
            </div>
          </section>
        </main>
      </div>
    </div>
  </section>
`;

const landing = $("#landing");
const shell = $("#shell");
const messagesEl = $("#messages");
const docList = $("#doc-list");
const wikiList = $("#wiki-list");

function $<T extends HTMLElement>(sel: string): T {
  return document.querySelector(sel) as T;
}

async function refreshHealth() {
  try {
    const health = await api.get<{ models: Record<string, unknown> }>("/api/health");
    const m = health.models;
    $("#health-line").textContent = m.openai_configured
      ? `API ready · OpenAI-compatible · ${m.chat_model}`
      : `API ready · demo/Ollama mode · ${m.chat_model}`;
    $("#model-pill").textContent = String(m.chat_model || "demo");
  } catch {
    $("#health-line").textContent = "API offline — run `make backend`";
  }
}

async function refreshDocs() {
  state.docs = await api.get<Doc[]>("/api/documents");
  docList.innerHTML = state.docs.length
    ? state.docs
        .map(
          (d) => `
      <button class="doc-item ${state.selectedDocId === d.id ? "active" : ""}" data-id="${d.id}">
        <strong>${escapeHtml(d.title)}</strong>
        <span>${d.chunk_count} chunks${d.has_wiki ? " · wiki" : ""}</span>
      </button>`
        )
        .join("")
    : `<div class="empty">暂无文档</div>`;

  docList.querySelectorAll<HTMLButtonElement>(".doc-item").forEach((btn) => {
    btn.onclick = () => void selectDoc(btn.dataset.id!);
  });
}

async function refreshWiki() {
  state.wiki = await api.get<WikiPage[]>("/api/wiki");
  wikiList.innerHTML = state.wiki.length
    ? state.wiki
        .map(
          (w) => `
      <button class="wiki-item ${state.selectedWikiSlug === w.slug ? "active" : ""}" data-slug="${w.slug}">
        <strong>${escapeHtml(w.title)}</strong>
        <span>${escapeHtml(w.slug)}</span>
      </button>`
        )
        .join("")
    : `<div class="empty">暂无页面</div>`;

  wikiList.querySelectorAll<HTMLButtonElement>(".wiki-item").forEach((btn) => {
    btn.onclick = () => void selectWiki(btn.dataset.slug!);
  });
}

async function selectDoc(id: string) {
  state.selectedDocId = id;
  setPanel("knowledge");
  await refreshDocs();
  const doc = await api.get<{ title: string; content: string; chunks: unknown[] }>(
    `/api/documents/${id}`
  );
  $("#knowledge-empty").classList.add("hidden");
  $("#knowledge-reader").classList.remove("hidden");
  $("#knowledge-title").textContent = doc.title;
  $("#knowledge-body").textContent = doc.content;
}

async function selectWiki(slug: string) {
  state.selectedWikiSlug = slug;
  setPanel("wiki");
  await refreshWiki();
  const page = await api.get<WikiPage>(`/api/wiki/${slug}`);
  $("#wiki-empty").classList.add("hidden");
  $("#wiki-reader").classList.remove("hidden");
  $("#wiki-title").textContent = page.title;
  $("#wiki-body").textContent = page.markdown || "";
}

function setPanel(panel: typeof state.panel) {
  state.panel = panel;
  document.querySelectorAll(".nav button").forEach((b) => {
    b.classList.toggle("active", (b as HTMLElement).dataset.panel === panel);
  });
  document.querySelectorAll(".panel").forEach((p) => p.classList.remove("active"));
  $(`#panel-${panel}`).classList.add("active");
}

function appendMessage(
  role: "user" | "assistant",
  content: string,
  citations?: Citation[],
  steps?: AskResult["steps"]
) {
  const empty = messagesEl.querySelector(".empty");
  empty?.remove();
  const el = document.createElement("div");
  el.className = `bubble ${role}`;
  el.textContent = content;

  if (citations?.length) {
    const box = document.createElement("div");
    box.className = "citations";
    box.innerHTML = citations
      .map(
        (c, i) =>
          `<div class="cite">[${i + 1}] ${escapeHtml(c.document_title)} · chunk ${c.ordinal}<br/>${escapeHtml(c.snippet)}</div>`
      )
      .join("");
    el.appendChild(box);
  }

  if (steps?.length) {
    const box = document.createElement("div");
    box.className = "steps";
    box.innerHTML = steps
      .map(
        (s) =>
          `<div class="step">Step ${s.step}${s.observation ? ` — ${escapeHtml(s.observation.slice(0, 180))}` : ""}</div>`
      )
      .join("");
    el.appendChild(box);
  }

  messagesEl.appendChild(el);
  messagesEl.scrollTop = messagesEl.scrollHeight;
}

function escapeHtml(s: string) {
  return s
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;");
}

async function seedSamples() {
  const files = ["about-kora.md", "agent-mode.md", "wiki-mode.md"];
  for (const name of files) {
    // Prefer backend seed script via fetching local samples is not available in browser.
    // Use text ingest with embedded sample content from API health path fallback:
  }
  // Call dedicated seed by posting known sample bodies:
  const samples: Array<[string, string]> = [
    [
      "About Kora",
      `Kora is a lightweight living-knowledge product prototype.\nHybrid retrieval fuses FTS5 BM25 with vector cosine similarity using RRF.`,
    ],
    [
      "Agent Mode",
      `Agent mode is a short ReAct loop with knowledge_search. RAG is for direct lookups; Agent helps multi-step synthesis.`,
    ],
    [
      "Wiki Mode",
      `Wiki distillation turns source documents into durable Markdown pages with summary, key points, concepts, and open questions.`,
    ],
  ];

  for (const [title, content] of samples) {
    const body = new FormData();
    body.set("title", title);
    body.set("content", content);
    await api.send("/api/documents/text", { method: "POST", body });
  }
  await refreshDocs();
  await refreshWiki();
}

$("#enter-btn").onclick = () => {
  landing.classList.add("hidden");
  shell.classList.add("active");
};

$("#seed-hint-btn").onclick = async () => {
  landing.classList.add("hidden");
  shell.classList.add("active");
  await seedSamples();
  setPanel("knowledge");
};

$("#seed-btn").onclick = () => void seedSamples();

$("#upload-btn").onclick = async () => {
  const input = $("#file-input") as HTMLInputElement;
  const file = input.files?.[0];
  if (!file) return;
  const body = new FormData();
  body.set("file", file);
  await api.send("/api/documents/upload", { method: "POST", body });
  input.value = "";
  await refreshDocs();
};

$("#distill-btn").onclick = async () => {
  if (!state.selectedDocId) return;
  const page = await api.send<WikiPage>("/api/wiki/distill", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ document_id: state.selectedDocId }),
  });
  await refreshDocs();
  await refreshWiki();
  await selectWiki(page.slug);
};

$("#delete-btn").onclick = async () => {
  if (!state.selectedDocId) return;
  await api.send(`/api/documents/${state.selectedDocId}`, { method: "DELETE" });
  state.selectedDocId = "";
  $("#knowledge-reader").classList.add("hidden");
  $("#knowledge-empty").classList.remove("hidden");
  await refreshDocs();
  await refreshWiki();
};

document.querySelectorAll(".nav button").forEach((btn) => {
  (btn as HTMLButtonElement).onclick = () => setPanel((btn as HTMLElement).dataset.panel as typeof state.panel);
});

document.querySelectorAll(".mode-switch button").forEach((btn) => {
  (btn as HTMLButtonElement).onclick = () => {
    state.mode = (btn as HTMLElement).dataset.mode as "rag" | "agent";
    document.querySelectorAll(".mode-switch button").forEach((b) => {
      b.classList.toggle("active", (b as HTMLElement).dataset.mode === state.mode);
    });
  };
});

$("#ask-form").onsubmit = async (e) => {
  e.preventDefault();
  const input = $("#ask-input") as HTMLTextAreaElement;
  const question = input.value.trim();
  if (!question) return;
  input.value = "";
  appendMessage("user", question);
  appendMessage("assistant", state.mode === "agent" ? "Agent 推理中…" : "检索并生成中…");
  const pending = messagesEl.lastElementChild as HTMLElement;
  try {
    const result = await api.send<AskResult>("/api/ask", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        question,
        mode: state.mode,
        session_id: state.sessionId || null,
      }),
    });
    state.sessionId = result.session_id;
    pending.remove();
    appendMessage("assistant", result.answer, result.citations, result.steps);
  } catch (err) {
    pending.textContent = `出错：${err instanceof Error ? err.message : String(err)}`;
  }
};

void (async () => {
  await refreshHealth();
  try {
    await refreshDocs();
    await refreshWiki();
  } catch {
    // backend may not be up yet
  }
})();
