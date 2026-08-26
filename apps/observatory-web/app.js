(function () {
  const results = window.TELPERIA_PUBLIC_RESULTS || [];
  const modelProfiles = window.TELPERIA_MODEL_PROFILES || [];
  const resultsBody = document.querySelector("#results-body");
  const detailGrid = document.querySelector("#detail-grid");
  const detailTitle = document.querySelector("#detail-title");
  const resultSearch = document.querySelector("#result-search");
  const resultCount = document.querySelector('[data-summary="result-count"]');
  const modelCount = document.querySelector('[data-summary="model-count"]');
  const modelDirectory = document.querySelector("#model-directory");
  const modelSummary = document.querySelector("#model-summary");
  const profileTitle = document.querySelector("#profile-title");
  const profileSummary = document.querySelector("#profile-summary");
  const profileTciBreakdown = document.querySelector("#profile-tci-breakdown");
  const profileFactualBreakdown = document.querySelector("#profile-factual-breakdown");
  const profileIpwRuns = document.querySelector("#profile-ipw-runs");
  const profileLimitations = document.querySelector("#profile-limitations");
  const profileDownload = document.querySelector("#profile-download");
  const comparisonSelectors = document.querySelector("#comparison-selectors");
  const comparisonTable = document.querySelector("#comparison-table");
  const comparisonStatus = document.querySelector("#comparison-status");
  const heroFields = document.querySelectorAll("[data-hero]");
  const models = summarizeModels(results);
  const comparisonRows = buildComparisonRows(results, modelProfiles);
  const comparisonSelectedIds = chooseDefaultComparisonIds(comparisonRows);
  const methodologyLinks = {
    tci: "#methodology-tci-v0-1",
    reasoning: "#methodology-tci-v0-1",
    coding: "#methodology-tci-v0-1",
    mathematics: "#methodology-tci-v0-1",
    "factual reliability": "#methodology-factual-reliability-v0-1",
    "factual correctness": "#methodology-factual-reliability-v0-1",
    "correct responses": "#methodology-factual-reliability-v0-1",
    "incorrect responses": "#methodology-factual-reliability-v0-1",
    "incorrect answer rate": "#methodology-factual-reliability-v0-1",
    "abstention rate": "#methodology-factual-reliability-v0-1",
    "attempted accuracy": "#methodology-factual-reliability-v0-1",
    "local ipw": "#methodology-ipw-v0-1",
    "best local ipw": "#methodology-ipw-v0-1",
    "average local ipw": "#methodology-ipw-v0-1",
    "ipw display score": "#methodology-ipw-v0-1",
    "gpu energy": "#methodology-ipw-v0-1",
    "gpu energy wh": "#methodology-ipw-v0-1",
    "energy confidence": "#methodology-ipw-v0-1",
    "transparency evidence": "#methodology-transparency-score-v0-1",
    "tri: not yet scored": "#methodology-tri-v0-1",
    "verification level": "#methodology-verification-levels",
    "latency": "#methodology-known-limitations",
    "tokens per second": "#methodology-known-limitations",
    "throughput": "#methodology-known-limitations",
    "peak vram": "#methodology-known-limitations",
    "methodology version": "#methodology",
  };

  if (resultCount) {
    resultCount.textContent = String(results.length);
  }

  if (modelCount) {
    modelCount.textContent = String(models.length);
  }

  function updateHeroSpecimen(row) {
    if (!row) {
      return;
    }
    heroFields.forEach((field) => {
      const key = field.dataset.hero;
      const value = row[key];
      if (key === "tci_v0_1") {
        field.textContent = formatNumber(value);
      } else if (key === "gpu_energy_wh") {
        field.textContent = `${formatNumber(value)} Wh`;
      } else if (key === "local_ipw_unscaled") {
        field.textContent = formatIpw(row);
      } else if (key === "monitor_backend") {
        field.textContent = String(value || "unavailable").toUpperCase();
      } else {
        field.textContent = value || "--";
      }
    });
  }

  function formatPercent(value) {
    if (value === null || value === undefined) {
      return "Deferred";
    }
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
    return `${formatNumber(row.local_ipw_unscaled)} TCI/Wh`;
  }

  function formatIpwDisplayScore(row) {
    if (row.local_ipw_status !== "calculated") {
      return "Deferred";
    }
    return `${formatNumber(row.local_ipw_displayed)} display score`;
  }

  function formatIpwValue(value) {
    if (value === null || value === undefined) {
      return "Deferred";
    }
    return `${formatNumber(value)} TCI/Wh`;
  }

  function formatLatency(value) {
    if (value === null || value === undefined) {
      return "Deferred";
    }
    return `${formatNumber(value)} ms`;
  }

  function formatThroughput(value) {
    if (value === null || value === undefined) {
      return "Deferred";
    }
    return `${formatNumber(value)} tok/s`;
  }

  function formatPeakVram(value) {
    if (value === null || value === undefined) {
      return "Not collected yet";
    }
    return `${formatNumber(value)} GB`;
  }

  function formatVerification(row) {
    if (row.verification_level === 0) {
      return "Level 0 means local/self-run evidence";
    }
    return `Level ${row.verification_level}`;
  }

  function average(values) {
    if (!values.length) {
      return null;
    }
    return values.reduce((total, value) => total + Number(value), 0) / values.length;
  }

  function maxValue(values) {
    if (!values.length) {
      return null;
    }
    return Math.max(...values.map((value) => Number(value)));
  }

  function uniqueValues(values) {
    return Array.from(new Set(values.filter((value) => value !== null && value !== undefined))).sort();
  }

  function chooseHeroResult(rows) {
    return [...rows].sort((left, right) => {
      const score = (row) => {
        let value = 0;
        if (row.local_ipw_status === "calculated") {
          value += 1000;
        }
        if (row.gpu_energy_wh > 0) {
          value += 500;
        }
        if (row.monitor_backend && row.monitor_backend !== "disabled") {
          value += 250;
        }
        if (row.factual_correctness_rate > 0) {
          value += 100;
        }
        if (row.factual_incorrect_answer_rate > 0) {
          value += 50;
        }
        return value + Number(row.tci_v0_1 || 0);
      };
      const priorityDifference = score(right) - score(left);
      if (priorityDifference !== 0) {
        return priorityDifference;
      }
      return Number(right.local_ipw_unscaled || 0) - Number(left.local_ipw_unscaled || 0);
    })[0];
  }

  function summarizeModels(rows) {
    const grouped = new Map();
    rows.forEach((row) => {
      const group = grouped.get(row.model_name) || [];
      group.push(row);
      grouped.set(row.model_name, group);
    });

    return Array.from(grouped.entries())
      .map(([modelName, modelRows]) => {
        const calculatedIpwRows = modelRows.filter((row) => row.local_ipw_status === "calculated");
        const representative = [...modelRows].sort((left, right) => {
          const tciDifference = Number(right.tci_v0_1) - Number(left.tci_v0_1);
          if (tciDifference !== 0) {
            return tciDifference;
          }
          return Number(right.local_ipw_unscaled || 0) - Number(left.local_ipw_unscaled || 0);
        })[0];

        return {
          modelName,
          provider: "unknown",
          openStatus: "unknown",
          representativeResultId: representative.result_id,
          representativeTci: representative.tci_v0_1,
          factualCorrectness: average(modelRows.map((row) => row.factual_correctness_rate)),
          factualIncorrect: average(modelRows.map((row) => row.factual_incorrect_answer_rate)),
          availableIpwCount: calculatedIpwRows.length,
          totalRunCount: modelRows.length,
          bestLocalIpw: maxValue(calculatedIpwRows.map((row) => row.local_ipw_unscaled)),
          verificationLevels: uniqueValues(modelRows.map((row) => row.verification_level)),
          methodologyVersions: uniqueValues(modelRows.map((row) => row.methodology_version)),
          hardwareCount: uniqueValues(modelRows.map((row) => row.hardware_label)).length,
        };
      })
      .sort((left, right) => left.modelName.localeCompare(right.modelName));
  }

  function profileForResult(row, profiles) {
    return profiles.find((profile) => profile.model_name === row.model_name);
  }

  function categoryScore(profile, categoryName) {
    const category = profile
      ? profile.tci_breakdown.find((item) => item.category === categoryName)
      : null;
    return category ? category.average_category_score : null;
  }

  function buildComparisonRows(rows, profiles) {
    return rows.map((row) => {
      const profile = profileForResult(row, profiles);
      const profileRun = profile
        ? profile.hardware_specific_ipw_runs.find((run) => run.result_id === row.result_id)
        : null;
      return {
        result_id: row.result_id,
        modelName: row.model_name,
        hardware: row.hardware_label,
        tci: row.tci_v0_1,
        reasoning: categoryScore(profile, "reasoning"),
        coding: categoryScore(profile, "coding"),
        mathematics: categoryScore(profile, "mathematics"),
        factualReliability: row.factual_correctness_rate,
        incorrectAnswerRate: row.factual_incorrect_answer_rate,
        abstentionRate: row.factual_abstention_rate,
        transparencyEvidence: profile
          ? `${profile.transparency_evidence.public_summary_rows} public summary row(s), ${profile.transparency_evidence.hardware_profile_count} hardware profile(s)`
          : "Public summary metadata",
        localIpw: row.local_ipw_status === "calculated" ? formatIpw(row) : "Deferred",
        gpuEnergy: `${formatNumber(row.gpu_energy_wh)} Wh`,
        latency: formatLatency(profileRun ? profileRun.latency_ms : null),
        tokensPerSecond: formatThroughput(profileRun ? profileRun.tokens_per_second : null),
        peakVram: formatPeakVram(null),
        verificationLevel: formatVerification(row),
        methodologyVersion: row.methodology_version,
      };
    });
  }

  function chooseDefaultComparisonIds(rows) {
    const selected = [];
    const seenModels = new Set();
    const candidates = [...rows].sort((left, right) => {
      const leftScore = left.localIpw === "Deferred" ? 0 : 1;
      const rightScore = right.localIpw === "Deferred" ? 0 : 1;
      if (leftScore !== rightScore) {
        return rightScore - leftScore;
      }
      return Number(right.tci || 0) - Number(left.tci || 0);
    });

    candidates.forEach((row) => {
      if (selected.length < 4 && !seenModels.has(row.modelName)) {
        selected.push(row.result_id);
        seenModels.add(row.modelName);
      }
    });

    rows.forEach((row) => {
      if (selected.length < 2 && !selected.includes(row.result_id)) {
        selected.push(row.result_id);
      }
    });

    return selected;
  }

  function appendCell(tr, value) {
    const td = document.createElement("td");
    td.textContent = value;
    tr.appendChild(td);
    return td;
  }

  function appendMeta(parent, label, value) {
    const item = document.createElement("div");
    const labelNode = document.createElement("span");
    const valueNode = document.createElement("strong");
    appendMethodologyLabel(labelNode, label);
    valueNode.textContent = value;
    item.append(labelNode, valueNode);
    parent.appendChild(item);
  }

  function appendMethodologyLabel(parent, label) {
    const href = methodologyLinks[label.toLowerCase()];
    if (!href) {
      parent.textContent = label;
      return;
    }
    const link = document.createElement("a");
    link.className = "method-link";
    link.href = href;
    link.textContent = label;
    parent.appendChild(link);
  }

  function appendComparisonLabel(th, label) {
    appendMethodologyLabel(th, label);
  }

  function appendComparisonCell(tr, value) {
    const td = document.createElement("td");
    td.textContent = value;
    tr.appendChild(td);
  }

  function renderModelDirectory(modelSummaries) {
    if (!modelDirectory) {
      return;
    }

    modelDirectory.replaceChildren();
    modelSummaries.forEach((summary) => {
      const button = document.createElement("button");
      button.className = "model-entry";
      button.type = "button";
      button.dataset.modelName = summary.modelName;

      const title = document.createElement("strong");
      const meta = document.createElement("span");
      const profileHint = document.createElement("small");
      const metrics = document.createElement("div");

      title.textContent = summary.modelName;
      meta.textContent = `Provider ${summary.provider} / Open status ${summary.openStatus}`;
      profileHint.textContent = "View profile";
      metrics.className = "model-entry-metrics";

      appendMeta(metrics, "TCI v0.1", formatNumber(summary.representativeTci));
      appendMeta(metrics, "Factual Reliability", formatPercent(summary.factualCorrectness));
      appendMeta(metrics, "Available Local IPW", `${summary.availableIpwCount}/${summary.totalRunCount}`);
      appendMeta(metrics, "Verification Level", `L${summary.verificationLevels.join(", L")}`);
      appendMeta(metrics, "Methodology Version", summary.methodologyVersions.join(", "));
      appendMeta(metrics, "Transparency Evidence", `${summary.hardwareCount} hardware profile(s)`);

      button.append(title, meta, profileHint, metrics);
      button.addEventListener("click", () => selectModel(summary.modelName));
      modelDirectory.appendChild(button);
    });
  }

  function renderComparisonControls(rows) {
    if (!comparisonSelectors) {
      return;
    }

    comparisonSelectors.replaceChildren();
    rows.forEach((row) => {
      const button = document.createElement("button");
      const title = document.createElement("strong");
      const meta = document.createElement("span");
      const selected = comparisonSelectedIds.includes(row.result_id);
      button.className = "comparison-choice";
      button.type = "button";
      button.dataset.resultId = row.result_id;
      button.classList.toggle("is-selected", selected);
      button.setAttribute("aria-pressed", String(selected));
      title.textContent = row.modelName;
      meta.textContent = row.hardware;
      button.append(title, meta);
      button.addEventListener("click", () => toggleComparisonSelection(row.result_id));
      comparisonSelectors.appendChild(button);
    });
  }

  function toggleComparisonSelection(resultId) {
    const existingIndex = comparisonSelectedIds.indexOf(resultId);
    if (existingIndex >= 0) {
      if (comparisonSelectedIds.length <= 2) {
        return;
      }
      comparisonSelectedIds.splice(existingIndex, 1);
    } else {
      if (comparisonSelectedIds.length >= 4) {
        comparisonSelectedIds.shift();
      }
      comparisonSelectedIds.push(resultId);
    }
    renderComparisonControls(comparisonRows);
    renderComparisonTable(comparisonRows);
  }

  function renderComparisonTable(rows) {
    if (!comparisonTable) {
      return;
    }

    const selectedRows = comparisonSelectedIds
      .map((resultId) => rows.find((row) => row.result_id === resultId))
      .filter(Boolean);
    const tbody = document.createElement("tbody");

    if (comparisonStatus) {
      comparisonStatus.textContent = `Select 2 to 4 configurations. ${selectedRows.length} selected. No single winner is assigned.`;
    }

    comparisonTable.replaceChildren();
    [
      ["Model name", (row) => row.modelName],
      ["Hardware", (row) => row.hardware],
      ["TCI", (row) => formatNumber(row.tci)],
      ["Reasoning", (row) => formatNumber(row.reasoning)],
      ["Coding", (row) => formatNumber(row.coding)],
      ["Mathematics", (row) => formatNumber(row.mathematics)],
      ["Factual reliability", (row) => formatPercent(row.factualReliability)],
      ["Incorrect answer rate", (row) => formatPercent(row.incorrectAnswerRate)],
      ["Abstention rate", (row) => formatPercent(row.abstentionRate)],
      ["Transparency Evidence", (row) => row.transparencyEvidence],
      ["Local IPW", (row) => row.localIpw],
      ["GPU energy", (row) => row.gpuEnergy],
      ["Latency", (row) => row.latency],
      ["Tokens per second", (row) => row.tokensPerSecond],
      ["Peak VRAM", (row) => row.peakVram],
      ["Verification level", (row) => row.verificationLevel],
      ["Methodology version", (row) => row.methodologyVersion],
    ].forEach(([label, valueForRow]) => {
      const tr = document.createElement("tr");
      const th = document.createElement("th");
      th.scope = "row";
      appendComparisonLabel(th, label);
      tr.appendChild(th);
      selectedRows.forEach((row) => appendComparisonCell(tr, valueForRow(row)));
      tbody.appendChild(tr);
    });

    comparisonTable.appendChild(tbody);
  }

  function selectModel(modelName) {
    const summary = models.find((item) => item.modelName === modelName);
    if (!summary || !modelSummary) {
      return;
    }

    document.querySelectorAll(".model-entry").forEach((entry) => {
      entry.classList.toggle("is-selected", entry.dataset.modelName === modelName);
    });

    modelSummary.replaceChildren();

    const heading = document.createElement("h3");
    const note = document.createElement("p");
    const facts = document.createElement("div");
    heading.textContent = summary.modelName;
    note.textContent =
      "No universal winner is selected here. Model summaries reflect available public seed results and can vary by hardware, run, and methodology version.";
    facts.className = "model-summary-grid";

    appendMeta(facts, "Provider", summary.provider);
    appendMeta(facts, "Open status", summary.openStatus);
    appendMeta(facts, "Representative TCI", formatNumber(summary.representativeTci));
    appendMeta(facts, "Factual Reliability", `${formatPercent(summary.factualCorrectness)} correct / ${formatPercent(summary.factualIncorrect)} incorrect`);
    appendMeta(facts, "Available Local IPW", `${summary.availableIpwCount} calculated run(s)`);
    appendMeta(facts, "Best Local IPW", formatIpwValue(summary.bestLocalIpw));
    appendMeta(facts, "Verification Level", `L${summary.verificationLevels.join(", L")}`);
    appendMeta(facts, "Methodology Version", summary.methodologyVersions.join(", "));
    appendMeta(facts, "Transparency Evidence", `${summary.hardwareCount} hardware profile(s), runtime metadata, and verification metadata`);

    modelSummary.append(heading, note, facts);
    renderModelProfile(summary.modelName);
    selectResult(summary.representativeResultId);
  }

  function renderModelProfile(modelName) {
    const profile = modelProfiles.find((item) => item.model_name === modelName);
    if (!profile || !profileTitle || !profileSummary || !profileTciBreakdown || !profileFactualBreakdown || !profileIpwRuns || !profileLimitations) {
      return;
    }

    profileTitle.textContent = `${profile.model_name} profile`;
    profileSummary.replaceChildren();
    profileTciBreakdown.replaceChildren();
    profileFactualBreakdown.replaceChildren();
    profileIpwRuns.replaceChildren();
    profileLimitations.replaceChildren();

    const summaryGrid = document.createElement("div");
    summaryGrid.className = "model-summary-grid";
    appendMeta(summaryGrid, "Provider", profile.provider);
    appendMeta(summaryGrid, "Open status", profile.open_status);
    appendMeta(summaryGrid, "Run count", String(profile.run_count));
    appendMeta(summaryGrid, "Representative TCI", formatNumber(profile.representative_tci_v0_1));
    appendMeta(summaryGrid, "Best Local IPW", formatIpwValue(profile.best_local_ipw_unscaled));
    appendMeta(summaryGrid, "Average Local IPW", formatIpwValue(profile.average_local_ipw_unscaled));
    appendMeta(summaryGrid, "Throughput", formatThroughput(profile.average_tokens_per_second));
    appendMeta(summaryGrid, "Latency", "Deferred");
    appendMeta(summaryGrid, "Energy", `${formatNumber(profile.average_gpu_energy_wh)} Wh average`);
    appendMeta(summaryGrid, "Verification Level", `L${profile.verification_levels.join(", L")}`);
    appendMeta(summaryGrid, "Methodology Version", profile.methodology_versions.join(", "));
    appendMeta(summaryGrid, "TRI: Not yet scored", profile.tri.note);
    appendMeta(summaryGrid, "Transparency Evidence", `${profile.transparency_evidence.public_summary_rows} public summary row(s), ${profile.transparency_evidence.hardware_profile_count} hardware profile(s)`);
    profileSummary.appendChild(summaryGrid);

    if (profileDownload) {
      profileDownload.textContent = profile.download.label;
      profileDownload.title = profile.download.note;
      profileDownload.setAttribute("aria-disabled", "true");
    }

    profile.tci_breakdown.forEach((category) => {
      const row = document.createElement("div");
      appendMeta(row, category.category.replaceAll("_", " "), `${formatNumber(category.average_category_score)} score / weight ${formatNumber(category.category_weight)} / ${category.run_count} run(s)`);
      profileTciBreakdown.appendChild(row);
    });

    [
      ["Correct responses", String(profile.factual_reliability.correct_responses)],
      ["Incorrect responses", String(profile.factual_reliability.incorrect_responses)],
      ["Abstentions", String(profile.factual_reliability.abstentions)],
      ["Total questions", String(profile.factual_reliability.total_questions)],
      ["Correctness rate", formatPercent(profile.factual_reliability.correctness_rate)],
      ["Incorrect answer rate", formatPercent(profile.factual_reliability.incorrect_answer_rate)],
      ["Abstention rate", formatPercent(profile.factual_reliability.abstention_rate)],
      ["Attempted accuracy", formatPercent(profile.factual_reliability.attempted_accuracy)],
    ].forEach(([label, value]) => {
      const row = document.createElement("div");
      appendMeta(row, label, value);
      profileFactualBreakdown.appendChild(row);
    });

    profile.hardware_specific_ipw_runs.forEach((run) => {
      const item = document.createElement("article");
      const title = document.createElement("strong");
      const facts = document.createElement("div");
      title.textContent = run.hardware_label;
      facts.className = "profile-run-grid";
      appendMeta(facts, "Local IPW", run.local_ipw_status === "calculated" ? formatIpwValue(run.local_ipw_unscaled) : "Deferred");
      appendMeta(facts, "IPW Display Score", run.local_ipw_displayed === null ? "Deferred" : `${formatNumber(run.local_ipw_displayed)} display score`);
      appendMeta(facts, "Latency", formatLatency(run.latency_ms));
      appendMeta(facts, "Throughput", formatThroughput(run.tokens_per_second));
      appendMeta(facts, "Energy", `${formatNumber(run.gpu_energy_wh)} Wh`);
      appendMeta(facts, "Energy Confidence", run.energy_confidence || "unavailable");
      appendMeta(facts, "Verification Level", run.verification_level === 0 ? "Level 0 means local/self-run evidence" : `Level ${run.verification_level}`);
      appendMeta(facts, "Methodology Version", run.methodology_version);
      item.append(title, facts);
      profileIpwRuns.appendChild(item);
    });

    profile.limitations.forEach((limitation) => {
      const item = document.createElement("li");
      item.textContent = limitation;
      profileLimitations.appendChild(item);
    });
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
      appendCell(tr, `${formatNumber(row.gpu_energy_wh)} Wh`);
      appendCell(tr, formatIpw(row));

      const confidenceCell = document.createElement("td");
      const confidence = document.createElement("span");
      confidence.className = "state";
      confidence.textContent = `L${row.verification_level} / ${row.energy_confidence || "unavailable"}`;
      confidenceCell.appendChild(confidence);
      tr.appendChild(confidenceCell);
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
    const row = resultId ? results.find((item) => item.result_id === resultId) : null;
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
      ["Abstention Rate", formatPercent(row.factual_abstention_rate)],
      ["Attempted Accuracy", formatPercent(row.factual_attempted_accuracy)],
      ["Local IPW", formatIpw(row)],
      ["IPW Display Score", formatIpwDisplayScore(row)],
      ["GPU Energy Wh", formatNumber(row.gpu_energy_wh)],
      ["Energy Confidence", row.energy_confidence || "unavailable"],
      ["Verification Level", formatVerification(row)],
      ["Methodology Version", row.methodology_version],
      ["Evaluation Suite", row.evaluation_suite],
    ].forEach(([label, value]) => {
      const item = document.createElement("article");
      item.className = "detail-record";
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
  renderModelDirectory(models);
  renderComparisonControls(comparisonRows);
  renderComparisonTable(comparisonRows);
  const heroResult = chooseHeroResult(results);
  updateHeroSpecimen(heroResult);
  if (models[0]) {
    selectModel(models[0].modelName);
  } else {
    selectResult(results[0] ? results[0].result_id : null);
  }
})();
