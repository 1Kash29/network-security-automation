function clearTable(tableId) {
  const tbody = document.querySelector(`#${tableId} tbody`);
  tbody.innerHTML = "";
  return tbody;
}

function renderSimpleTable(tableId, rows, mapRow) {
  const tbody = clearTable(tableId);
  rows.forEach((row) => {
    const tr = document.createElement("tr");
    mapRow(row).forEach((value) => {
      const td = document.createElement("td");
      td.textContent = value || "-";
      tr.appendChild(td);
    });
    tbody.appendChild(tr);
  });
}

// Severity is always one of a fixed set computed server-side (see
// app/triage.py), never taken verbatim from event input, so it's safe to use
// as a CSS class name here. Every other cell below still goes through
// textContent, since category/src_ip/message can come from attacker-supplied
// log lines or webhook payloads.
function renderEventsTable(rows) {
  const tbody = clearTable("events-table");
  rows.forEach((event) => {
    const tr = document.createElement("tr");

    const timeTd = document.createElement("td");
    timeTd.textContent = new Date(event.received_at * 1000).toLocaleTimeString();
    tr.appendChild(timeTd);

    const severityTd = document.createElement("td");
    const badge = document.createElement("span");
    badge.className = `badge badge-${event.severity}`;
    badge.textContent = event.severity;
    severityTd.appendChild(badge);
    tr.appendChild(severityTd);

    [event.category, event.src_ip, event.message].forEach((value) => {
      const td = document.createElement("td");
      td.textContent = value || "-";
      tr.appendChild(td);
    });

    tbody.appendChild(tr);
  });
}

async function refreshStatus() {
  const res = await fetch("/api/status");
  const data = await res.json();
  renderSimpleTable("devices-table", data.devices, (d) => [d.name, d.model, d.state, d.ip]);
  renderSimpleTable("clients-table", data.clients, (c) => [c.name, c.ip, c.network]);
}

async function refreshEvents() {
  const res = await fetch("/api/events?limit=50");
  const data = await res.json();
  renderEventsTable(data.events);
}

refreshStatus();
refreshEvents();
setInterval(refreshStatus, 10000);
setInterval(refreshEvents, 5000);
