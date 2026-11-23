"use strict";

(() => {
  let fixtures;

  function explain(selected, body) {
    if (body.file_id && selected.files[body.file_id]) return selected.files[body.file_id];
    if (body.finding_id && selected.findings[body.finding_id]) return selected.findings[body.finding_id];
    const question = String(body.question ?? "").toLowerCase();
    const named = selected.report.files.find(file => file.name.length > 3 && question.includes(file.name.toLowerCase()));
    if (named) return selected.files[named.id];
    if (/last open|last use|unused|access/.test(question)) return selected.topics["last opened"];
    if (/private|privacy|upload|safe|delete|remove/.test(question)) return selected.topics.privacy;
    if (/\b(?:duplicates?|copy|copies)\b/.test(question)) return selected.topics.duplicates;
    if (/develop|project|cache|generated/.test(question)) return selected.topics["generated project folders"];
    return selected.topics.overview;
  }

  window.lumenPagesApi = async (path, body, raw) => {
    fixtures ??= fetch("./demo.json").then(response => {
      if (!response.ok) throw new Error("Could not load the fictional snapshots.");
      return response.json();
    });
    const data = await fixtures;
    const route = new URL(path, location.href);
    const selected = data.reports[body?.report_id];
    switch (route.pathname) {
      case "/api/bootstrap":
        return { version: data.version, demo_only: true, hosted_demo: true, locations: [] };
      case "/api/history":
        return data.history;
      case "/api/scan":
        if (body === undefined) return { status: "idle" };
        throw new Error("Scanning is available in the local app.");
      case "/api/models":
        return { models: [], message: "Ollama runs in the local app. This demo includes the evidence guide." };
      case "/api/ask":
        if (!selected) throw new Error("Demo snapshot not found.");
        return { status: "complete", result: explain(selected, body) };
      case "/api/compare": {
        const before = route.searchParams.get("before");
        const after = route.searchParams.get("after");
        const comparison = data.comparisons[before]?.[after];
        if (comparison) return comparison;
        throw new Error("Demo snapshots not found.");
      }
    }
    const report = /^\/api\/reports\/([a-z-]+)(?:\.(json|csv|html))?$/.exec(route.pathname);
    if (report && Object.hasOwn(data.reports, report[1])) {
      if (!raw) return data.reports[report[1]].report;
      if (report[2]) {
        const response = await fetch("./exports/" + report[1] + "." + report[2]);
        if (response.ok) return response.blob();
      }
    }
    throw new Error("This feature is unavailable in the browser demo.");
  };
})();
