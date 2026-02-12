const menuItems = document.querySelectorAll('.menu-item');
const panels = document.querySelectorAll('.panel');

menuItems.forEach((item) => {
  item.addEventListener('click', () => {
    menuItems.forEach((it) => it.classList.remove('active'));
    panels.forEach((panel) => panel.classList.remove('active'));

    item.classList.add('active');
    const target = document.getElementById(item.dataset.section);
    if (target) {
      target.classList.add('active');
    }
  });
});

function formatDate(value) {
  return value.replace('T', ' ').slice(0, 16);
}

async function loadDashboard() {
  const res = await fetch('/api/dashboard');
  const data = await res.json();
  document.getElementById('kpi-todo-hazard').textContent = data.todoHazard;
  document.getElementById('kpi-closed-hazard').textContent = data.closedHazard;
  document.getElementById('kpi-abnormal').textContent = data.abnormalEvents;
  document.getElementById('kpi-loto').textContent = data.lotoActive;
  document.getElementById('kpi-interlock').textContent = data.interlockShield;
  document.getElementById('kpi-whitelist').textContent = data.whiteListCount;

  document.getElementById('status-loto').textContent = `${data.lotoActive}套设备锁定中`;
  document.getElementById('status-interlock').textContent = `${data.interlockShield}项屏蔽生效中`;
}

async function loadHazards() {
  const res = await fetch('/api/hazards');
  const data = await res.json();
  const tbody = document.getElementById('hazard-table-body');
  tbody.innerHTML = data
    .map(
      (row) =>
        `<tr><td>${row.id}</td><td>${row.title}</td><td>${row.area}</td><td>${row.level}</td><td>${row.found_at}</td><td>${row.status}</td></tr>`,
    )
    .join('');
}

async function loadInterlocks() {
  const res = await fetch('/api/interlocks');
  const data = await res.json();
  const tbody = document.getElementById('interlock-table-body');
  tbody.innerHTML = data
    .map(
      (row) =>
        `<tr><td>${row.code}</td><td>${row.area}</td><td>${row.requester}</td><td>${row.approve_status}</td><td>${row.shield_status}</td><td>${row.end_at}</td></tr>`,
    )
    .join('');
}

document.getElementById('hazard-form').addEventListener('submit', async (event) => {
  event.preventDefault();
  const form = event.currentTarget;
  const payload = Object.fromEntries(new FormData(form).entries());
  payload.found_at = formatDate(payload.found_at);

  const res = await fetch('/api/hazards', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  const result = await res.json();
  document.getElementById('hazard-msg').textContent = result.message || result.error;
  if (res.ok) {
    form.reset();
    await Promise.all([loadHazards(), loadDashboard()]);
  }
});

document.getElementById('interlock-form').addEventListener('submit', async (event) => {
  event.preventDefault();
  const form = event.currentTarget;
  const payload = Object.fromEntries(new FormData(form).entries());
  payload.start_at = formatDate(payload.start_at);
  payload.end_at = formatDate(payload.end_at);

  const res = await fetch('/api/interlocks', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  const result = await res.json();
  document.getElementById('interlock-msg').textContent = result.message || result.error;
  if (res.ok) {
    form.reset();
    await Promise.all([loadInterlocks(), loadDashboard()]);
  }
});

Promise.all([loadDashboard(), loadHazards(), loadInterlocks()]);
