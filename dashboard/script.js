// =========================
// GLOBAL CONFIG
// =========================
const API = "http://localhost:8000";
const LIMIT = 20;
let page = 0;

// Query helper
const qs = (id) => document.getElementById(id);

// Toast
function toast(msg, type = "info") {
  const wrap = qs("toastWrap");
  const box = document.createElement("div");
  box.className = "toast";
  box.textContent = msg;

  wrap.appendChild(box);
  setTimeout(() => box.remove(), 2500);
}


// =========================
// PANEL SWITCHING
// =========================
document.querySelectorAll(".nav-btn").forEach(btn => {
  btn.onclick = () => {
    document.querySelectorAll(".nav-btn").forEach(b => b.classList.remove("active"));
    btn.classList.add("active");

    document.querySelectorAll(".panel").forEach(p => p.classList.add("hidden"));
    qs(btn.dataset.tab).classList.remove("hidden");

    // reload data when switching tabs
    if (btn.dataset.tab === "products") {
      page = 0;
      loadProducts();
    }
    if (btn.dataset.tab === "webhooks") {
      loadWebhooks();
    }
  };
});



// =========================
// PRODUCTS
// =========================
async function loadProducts() {
  const q = qs("q").value.trim();
  const params = new URLSearchParams({ skip: page * LIMIT, limit: LIMIT });

  if (q) {
    if (!q.includes(" ")) params.set("sku", q);
    else params.set("name", q);
  }

  const res = await fetch(`${API}/products?` + params.toString());
  const items = await res.json();

  renderProductTable(items);
  qs("pageInfo").textContent = `Page ${page + 1}`;
}

function renderProductTable(items) {
  const head = qs("productTable").querySelector("thead");
  const body = qs("productTable").querySelector("tbody");

  head.innerHTML = `
    <tr>
      <th>ID</th><th>SKU</th><th>Name</th>
      <th>Description</th><th>Active</th><th>Actions</th>
    </tr>
  `;

  body.innerHTML = "";
  items.forEach(p => {
    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td>${p.id}</td>
      <td>${p.sku}</td>
      <td>${p.name || ""}</td>
      <td>${p.description || ""}</td>
      <td>${p.active}</td>
      <td>
        <button class="btn" onclick="editProduct(${p.id})">Edit</button>
        <button class="btn danger" onclick="deleteProduct(${p.id})">Delete</button>
      </td>
    `;
    body.appendChild(tr);
  });
}

qs("next").onclick = () => { page++; loadProducts(); };
qs("prev").onclick = () => { if (page > 0) page--; loadProducts(); };


// Search only on Enter
qs("q").addEventListener("keydown", (e) => {
  if (e.key === "Enter") {
    page = 0;
    loadProducts();
  }
});


// CREATE PRODUCT
qs("btnAdd").onclick = () => openProductModal();

async function createProduct(data) {
  const res = await fetch(`${API}/products`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });

  if (!res.ok) return toast("Invalid product data");
  toast("Product added");
  closeModal();
  loadProducts();
}


// UPDATE PRODUCT
async function editProduct(id) {
  const res = await fetch(`${API}/products/${id}`);
  const p = await res.json();

  openProductModal(p);
}

async function updateProduct(id, data) {
  const res = await fetch(`${API}/products/${id}`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });

  if (!res.ok) return toast("Update failed");
  toast("Product updated");
  closeModal();
  loadProducts();
}


// DELETE PRODUCT
async function deleteProduct(id) {
  if (!confirm("Delete this product?")) return;

  await fetch(`${API}/products/${id}`, { method: "DELETE" });
  toast("Product deleted");
  loadProducts();
}


// BULK DELETE
qs("btnDeleteAll").onclick = async () => {
  if (!confirm("Delete ALL products? This cannot be undone.")) return;

  await fetch(`${API}/products/delete_all`, { method: "POST" });
  toast("All products deleted");
  loadProducts();
};


// =========================
// PRODUCT MODAL
// =========================
function openProductModal(p = null) {
  const modal = qs("modal");
  modal.classList.remove("hidden");

  modal.innerHTML = `
  <div class="modal-content">
    <h2>${p ? "Edit Product" : "Add Product"}</h2>

    <label style="margin-top:10px; display:block;">SKU</label>
    <input
      id="m_sku"
      class="search"
      style="margin-bottom:12px;"
      value="${p ? p.sku : ""}"
      ${p ? "readonly" : ""}
    />

    <label style="margin-top:10px; display:block;">Name</label>
    <input
      id="m_name"
      class="search"
      style="margin-bottom:12px;"
      value="${p ? p.name : ""}"
    />

    <label style="margin-top:10px; display:block;">Description</label>
    <input
      id="m_desc"
      class="search"
      style="margin-bottom:12px;"
      value="${p ? p.description : ""}"
    />

    <label style="margin-top:10px; display:block;">Active</label>
    <select
      id="m_active"
      class="search"
      style="margin-bottom:20px;"
    >
      <option value="true" ${p && p.active ? "selected" : ""}>True</option>
      <option value="false" ${p && !p.active ? "selected" : ""}>False</option>
    </select>

    <div style="margin-top:10px; display:flex; gap:10px;">
      <button class="btn primary" id="m_save">Save</button>
      <button class="btn" onclick="closeModal()">Cancel</button>
    </div>
  </div>
`;

  qs("m_save").onclick = () => {
    const data = {
      sku: qs("m_sku").value.trim(),
      name: qs("m_name").value.trim(),
      description: qs("m_desc").value.trim(),
      active: qs("m_active").value === "true",
    };

    if (!p) createProduct(data);
    else updateProduct(p.id, data);
  };
}

function closeModal() {
  qs("modal").classList.add("hidden");
}


// =========================
// UPLOAD CSV
// =========================
qs("btnUpload").onclick = uploadCSV;

async function uploadCSV() {
  const file = qs("csvFile").files[0];
  if (!file) return toast("Choose a CSV file");

  if (!file.name.endsWith(".csv")) return toast("Upload only CSV");

  const form = new FormData();
  form.append("file", file);

  qs("uploadStatus").textContent = "Uploading...";
  qs("progressWrapper").classList.remove("hidden");

  const res = await fetch(`${API}/upload`, { method: "POST", body: form });
  const data = await res.json();

  qs("uploadStatus").textContent = "Processing...";
  pollProgress(data.task_id);
}

async function pollProgress(taskId) {
  const interval = setInterval(async () => {
    const res = await fetch(`${API}/progress/${taskId}`);
    const data = await res.json();
    const pct = data.progress;

    qs("progressFill").style.width = pct + "%";

    if (pct >= 100) {
      clearInterval(interval);
      qs("uploadStatus").textContent = "Completed";
      toast("Import finished");
      setTimeout(() => qs("progressWrapper").classList.add("hidden"), 1000);
    }
  }, 800);
}


// =========================
// WEBHOOKS
// =========================
qs("btnRefreshWebhooks").onclick = loadWebhooks;
qs("btnAddWebhook").onclick = () => openWebhookModal();

async function loadWebhooks() {
  const res = await fetch(`${API}/webhooks`);
  const hooks = await res.json();

  const head = qs("webhookTable").querySelector("thead");
  const body = qs("webhookTable").querySelector("tbody");

  head.innerHTML = `
    <tr>
      <th>ID</th><th>URL</th><th>Event</th><th>Enabled</th><th>Actions</th>
    </tr>
  `;

  body.innerHTML = "";

  hooks.forEach(w => {
    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td>${w.id}</td>
      <td>${w.url}</td>
      <td>${w.event}</td>
      <td>${w.enabled}</td>
      <td>
        <button class="btn" onclick="editWebhook(${w.id})">Edit</button>
        <button class="btn" onclick="testWebhook(${w.id})">Test</button>
        <button class="btn danger" onclick="deleteWebhook(${w.id})">Delete</button>
      </td>
    `;
    body.appendChild(tr);
  });
}


// WEBHOOK CRUD + TEST
async function editWebhook(id) {
  const res = await fetch(`${API}/webhooks`);
  const hooks = await res.json();
  const w = hooks.find(h => h.id === id);

  openWebhookModal(w);
}

async function deleteWebhook(id) {
  if (!confirm("Delete this webhook?")) return;

  await fetch(`${API}/webhooks/${id}`, { method: "DELETE" });
  toast("Webhook deleted");
  loadWebhooks();
}

async function testWebhook(id) {
  toast("Sending test...");
  const res = await fetch(`${API}/webhooks/${id}/test`, { method: "POST" });
  const data = await res.json();
  toast(`Response: ${data.status_code || "ERR"}`);
}

function openWebhookModal(w = null) {
  const modal = qs("modal");
  modal.classList.remove("hidden");

  modal.innerHTML = `
    <div class="modal-content">
      <h2>${w ? "Edit Webhook" : "Add Webhook"}</h2>

      <label>URL</label>
      <input id="wh_url" class="search" value="${w ? w.url : ""}">

      <label>Event</label>
      <input id="wh_event" class="search" value="${w ? w.event : "product.imported"}">

      <label>Enabled</label>
      <select id="wh_enabled" class="search">
        <option value="true" ${w && w.enabled ? "selected" : ""}>True</option>
        <option value="false" ${w && !w.enabled ? "selected" : ""}>False</option>
      </select>

      <div style="margin-top:20px; display:flex; gap:10px;">
        <button class="btn primary" id="wh_save">Save</button>
        <button class="btn" onclick="closeModal()">Cancel</button>
      </div>
    </div>
  `;

  qs("wh_save").onclick = async () => {
    const data = {
      url: qs("wh_url").value,
      event: qs("wh_event").value,
      enabled: qs("wh_enabled").value === "true",
    };

    if (!w) {
      await fetch(`${API}/webhooks`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(data),
      });
      toast("Webhook added");
    } else {
      await fetch(`${API}/webhooks/${w.id}`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(data),
      });
      toast("Webhook updated");
    }

    closeModal();
    loadWebhooks();
  };
}


// =========================
// INIT
// =========================
loadProducts();
loadWebhooks();
