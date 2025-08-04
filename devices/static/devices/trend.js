import { fillMissingData, smoothData } from './dataUtils.js';

const deviceId = window.deviceId;
const chartCtx = document.getElementById('trendChart')?.getContext('2d');
let chart;

export async function loadTrendData(hours = 1) {
  const res = await fetch(`/api/device/${deviceId}/trend-data/?hours=${hours}`);
  let data = await res.json();

  // Process data using helpers (currently no-ops)
  data = smoothData(fillMissingData(data));

  const labels = data.map(d => new Date(d.minute).toLocaleTimeString());
  const values = data.map(d => d.production);

  if (chart) chart.destroy();
  chart = new Chart(chartCtx, {
    type: 'line',
    data: {
      labels: labels,
      datasets: [{
        label: 'میزان تولید (متر)',
        data: values,
        fill: true,
        borderColor: '#00adb5',
        backgroundColor: 'rgba(0, 173, 181, 0.2)',
        tension: 0.3
      }]
    },
    options: {
      plugins: {
        legend: {
          labels: { color: '#f5f5f5' }
        }
      },
      scales: {
        x: { ticks: { color: '#ccc' } },
        y: { ticks: { color: '#ccc' } }
      }
    }
  });
}

document.getElementById('timeframe')?.addEventListener('change', (e) => {
  loadTrendData(e.target.value);
});

document.getElementById('exportBtn')?.addEventListener('click', () => {
  const hours = document.getElementById('timeframe').value;
  const url = `/device/${deviceId}/export-csv/?hours=${hours}`;
  window.open(url, '_blank');
});

loadTrendData();
