(function () {
  const results = window.TELPERIA_PUBLIC_RESULTS || [];
  const resultsBody = document.querySelector("#results-body");
  const detailGrid = document.querySelector("#detail-grid");
  const detailTitle = document.querySelector("#detail-title");
  const resultSearch = document.querySelector("#result-search");
  const resultCount = document.querySelector('[data-summary="result-count"]');

  if (resultCount) {
    resultCount.textContent = String(results.length);
  }

  function formatPercent(value) {
    return `${Math.round(Number(value) * 100)}%`;
  }

  function formatNumber(value) {
    if (value === null || value === undefined) {
      return "Deferred";
    }
    return Number(value).toLocaleString(undefined, { maximumFractionDigits: 2 });
  }

  function formatIpw(row) {
    if (row.local_ipw_status !== "calculated") {
      return "Deferred";
    }
    return formatNumber(row.local_ipw_displayed);
  }

  function appendCell(tr, value) {
    const td = document.createElement("td");
    td.textContent = value;
    tr.appendChild(td);
    return td;
  }

  function renderResultsTable(rows) {
    resultsBody.replaceChildren();

    rows.forEach((row) => {
      const tr = document.createElement("tr");
      tr.tabIndex = 0;
      tr.dataset.resultId = row.result_id;

      const modelCell = document.createElement("td");
      const modelName = document.createElement("strong");
      const modelMeta = document.createElement("span");
      modelName.textContent = row.model_name;
      modelMeta.textContent = `${row.model_revision} / ${row.quantization}`;
      modelCell.append(modelName, modelMeta);
      tr.appendChild(modelCell);

      appendCell(tr, row.hardware_label);
      appendCell(tr, formatNumber(row.tci_v0_1));
      appendCell(tr, formatPercent(row.factual_correctness_rate));
      appendCell(tr, formatIpw(row));

      const confidenceCell = document.createElement("td");
      const confidence = document.createElement("span");
      confidence.className = "pill";
      confidence.textContent = row.energy_confidence || "unavailable";
      confidenceCell.appendChild(confidence);
      tr.appendChild(confidenceCell);

      appendCell(tr, `Level ${row.verification_level}`);
      tr.addEventListener("click", () => selectResult(row.result_id));
      tr.addEventListener("keydown", (event) => {
        if (event.key === "Enter" || event.key === " ") {
          event.preventDefault();
          selectResult(row.result_id);
        }
      });
      resultsBody.appendChild(tr);
    });
  }

  function selectResult(resultId) {
    const row = results.find((item) => item.result_id === resultId) || results[0];
    if (!row) {
      detailTitle.textContent = "No result selected";
      detailGrid.replaceChildren();
      return;
    }

    document.querySelectorAll("#results-body tr").forEach((tr) => {
      tr.classList.toggle("is-selected", tr.dataset.resultId === row.result_id);
    });

    detailTitle.textContent = `${row.model_name} on ${row.gpu}`;
    detailGrid.replaceChildren();

    [
      ["Model", row.model_name],
      ["Hardware", row.hardware_label],
      ["TCI", formatNumber(row.tci_v0_1)],
      ["Factual Correctness", formatPercent(row.factual_correctness_rate)],
      ["Incorrect Answer Rate", formatPercent(row.factual_incorrect_answer_rate)],
      ["Attempted Accuracy", formatPercent(row.factual_attempted_accuracy)],
      ["Local IPW", formatIpw(row)],
      ["GPU Energy Wh", formatNumber(row.gpu_energy_wh)],
      ["Energy Confidence", row.energy_confidence || "unavailable"],
      ["Verification Level", `Level ${row.verification_level}`],
      ["Methodology Version", row.methodology_version],
      ["Evaluation Suite", row.evaluation_suite],
    ].forEach(([label, value]) => {
      const item = document.createElement("article");
      item.className = "detail-card";
      const labelNode = document.createElement("span");
      const valueNode = document.createElement("strong");
      labelNode.textContent = label;
      valueNode.textContent = value;
      item.append(labelNode, valueNode);
      detailGrid.appendChild(item);
    });
  }

  function filterResults(query) {
    const normalized = query.trim().toLowerCase();
    if (!normalized) {
      return results;
    }
    return results.filter((row) => {
      return [
        row.model_name,
        row.hardware_label,
        row.local_ipw_status,
        row.energy_confidence,
        row.methodology_version,
      ].some((value) => String(value || "").toLowerCase().includes(normalized));
    });
  }

  resultSearch.addEventListener("input", () => {
    const filtered = filterResults(resultSearch.value);
    renderResultsTable(filtered);
    selectResult(filtered[0] ? filtered[0].result_id : null);
  });

  renderResultsTable(results);
  selectResult(results[0] ? results[0].result_id : null);
})();
