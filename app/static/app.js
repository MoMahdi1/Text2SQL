const form = document.querySelector("#query-form");
const questionInput = document.querySelector("#question");
const submitButton = document.querySelector("#submit-button");
const statusBox = document.querySelector("#status");
const resultSection = document.querySelector("#result");
const table = document.querySelector("#result-table");
const sqlOutput = document.querySelector("#sql-output");
const rowCount = document.querySelector("#row-count");
const workflowSteps = document.querySelector("#workflow-steps");

document.querySelectorAll("[data-question]").forEach((button) => {
  button.addEventListener("click", () => {
    questionInput.value = button.dataset.question;
    questionInput.focus();
  });
});

function setStatus(message, type = "error") {
  statusBox.textContent = message;
  statusBox.className = `status ${type}`;
}

function renderTable(columns, rows) {
  table.replaceChildren();
  if (!rows.length) {
    const body = document.createElement("tbody");
    const cell = document.createElement("td");
    cell.className = "empty";
    cell.colSpan = Math.max(columns.length, 1);
    cell.textContent = "The query completed successfully but returned no rows.";
    const row = document.createElement("tr");
    row.append(cell);
    body.append(row);
    table.append(body);
    return;
  }

  const header = document.createElement("thead");
  const headerRow = document.createElement("tr");
  columns.forEach((column) => {
    const th = document.createElement("th");
    th.textContent = column;
    headerRow.append(th);
  });
  header.append(headerRow);

  const body = document.createElement("tbody");
  rows.forEach((item) => {
    const row = document.createElement("tr");
    columns.forEach((column) => {
      const cell = document.createElement("td");
      const value = item[column];
      cell.textContent = value === null ? "—" : String(value);
      row.append(cell);
    });
    body.append(row);
  });
  table.append(header, body);
}

function renderResult(data) {
  renderTable(data.columns, data.rows);
  sqlOutput.textContent = data.sql;
  rowCount.textContent = `${data.row_count} row${data.row_count === 1 ? "" : "s"}${data.truncated ? "+" : ""}`;
  workflowSteps.replaceChildren();
  data.steps.forEach((step) => {
    const item = document.createElement("li");
    const title = document.createElement("strong");
    title.textContent = step.name;
    const detail = document.createElement("span");
    detail.textContent = step.detail;
    item.append(title, detail);
    workflowSteps.append(item);
  });
  resultSection.classList.remove("hidden");
}

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  const question = questionInput.value.trim();
  if (question.length < 3) return;

  submitButton.disabled = true;
  resultSection.classList.add("hidden");
  setStatus("The agent is inspecting the schema and preparing a safe query…", "loading");

  try {
    const response = await fetch("/api/query", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ question }),
    });
    const payload = await response.json();
    if (!response.ok) throw new Error(payload.detail || "The request failed.");
    renderResult(payload);
    statusBox.classList.add("hidden");
  } catch (error) {
    setStatus(error.message || "Something went wrong. Please try again.");
  } finally {
    submitButton.disabled = false;
  }
});

