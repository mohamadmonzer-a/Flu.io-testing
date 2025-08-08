document.getElementById('embedBtn').addEventListener('click', async () => {
  document.getElementById('status').textContent = 'Processing...';
  try {
    const response = await fetch('https://your-fly-backend.fly.dev/embed-pdf', { method: 'POST' });
    const data = await response.json();
    if (response.ok) {
      document.getElementById('status').textContent = 'PDF embedded successfully!';
    } else {
      document.getElementById('status').textContent = 'Error: ' + data.error;
    }
  } catch (e) {
    document.getElementById('status').textContent = 'Request failed: ' + e.message;
  }
});
