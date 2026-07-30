const rows = [...document.querySelectorAll('#work-table tbody tr')];
const search = document.querySelector('#search');
const statusFilter = document.querySelector('#status-filter');
const emptyState = document.querySelector('#empty-state');
const drawer = document.querySelector('#detail-drawer');

function filterRows() {
  const query = search.value.trim().toLowerCase();
  const status = statusFilter.value;
  let visible = 0;

  rows.forEach((row) => {
    const haystack = `${row.dataset.title} ${row.dataset.project} ${row.dataset.owner}`.toLowerCase();
    const matchesQuery = !query || haystack.includes(query);
    const matchesStatus = status === 'all' || row.dataset.status === status;
    row.hidden = !(matchesQuery && matchesStatus);
    if (!row.hidden) visible += 1;
  });

  emptyState.hidden = visible !== 0;
}

function openDrawer(row) {
  document.querySelector('#drawer-title').textContent = row.dataset.title;
  document.querySelector('#drawer-project').textContent = row.dataset.project;
  document.querySelector('#drawer-status').textContent = row.dataset.status;
  document.querySelector('#drawer-owner').textContent = row.dataset.owner;
  document.querySelector('#drawer-due').textContent = row.dataset.due;
  drawer.classList.add('open');
  drawer.setAttribute('aria-hidden', 'false');
}

function closeDrawer() {
  drawer.classList.remove('open');
  drawer.setAttribute('aria-hidden', 'true');
}

search.addEventListener('input', filterRows);
statusFilter.addEventListener('change', filterRows);
rows.forEach((row) => {
  row.addEventListener('click', () => openDrawer(row));
  row.addEventListener('keydown', (event) => {
    if (event.key === 'Enter' || event.key === ' ') {
      event.preventDefault();
      openDrawer(row);
    }
  });
});
document.querySelector('#drawer-close').addEventListener('click', closeDrawer);
document.querySelector('#new-work').addEventListener('click', () => {
  document.querySelector('#notice').textContent = 'New work capture would open here.';
});
