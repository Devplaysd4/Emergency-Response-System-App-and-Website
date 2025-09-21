document.addEventListener('DOMContentLoaded', () => {
    const alertList = document.getElementById('alertList');
    const reportBox = document.querySelector('.report-box');
    const modal = document.getElementById('alertModal');
    const closeBtn = document.querySelector('.close-btn');
    const alertDetails = document.getElementById('alertDetails');

    let alertsData = [];

    closeBtn.addEventListener('click', () => {
        modal.style.display = 'none';
    });

    window.addEventListener('click', (e) => {
        if (e.target == modal) {
            modal.style.display = 'none';
        }
    });

    alertList.addEventListener('click', (e) => {
        if (e.target.tagName === 'LI') {
            const alertIndex = e.target.dataset.index;
            const alert = alertsData[alertIndex];
            
            alertDetails.innerHTML = `
                <p><strong>Blockchain ID:</strong> ${alert.blockchainId}</p>
                <p><strong>Phone Number:</strong> ${alert.phoneNumber}</p>
                <p><strong>KYC:</strong> ${alert.kycId}</p>
                <p><strong>Emergency Contact:</strong> ${alert.emergencyContact}</p>
                <p><strong>Location:</strong> ${alert.location.latitude}, ${alert.location.longitude}</p>
                <p><strong>Timestamp:</strong> ${new Date(alert.timestamp).toLocaleString()}</p>
            `;
            modal.style.display = 'block';
        }
    });

    // Fetch and display emergency alerts
    async function fetchAlerts() {
        try {
            const response = await fetch('/sos_alerts');
            const alerts = await response.json();
            alertsData = alerts;
            alertList.innerHTML = '';
            if (alerts.length === 0) {
                alertList.innerHTML = '<li>No active alerts</li>';
            } else {
                alerts.forEach((alert, index) => {
                    const li = document.createElement('li');
                    li.textContent = `SOS from ${alert.phoneNumber} at ${new Date(alert.timestamp).toLocaleString()}`;
                    li.dataset.index = index;
                    alertList.appendChild(li);
                });
            }
        } catch (error) {
            console.error('Error fetching alerts:', error);
            alertList.innerHTML = '<li>Error fetching alerts</li>';
        }
    }

    // Fetch and display user anomaly reports
    async function fetchReports() {
        try {
            const response = await fetch('/get_reports');
            const reports = await response.json();
            reportBox.innerHTML = ''; 
            if (reports.length === 0) {
                reportBox.innerHTML = '<p>No pending reports</p>';
            } else {
                reports.forEach(report => {
                    const reportElement = document.createElement('div');
                    reportElement.classList.add('report-item');
                    reportElement.innerHTML = `
                        <div class="report-content">
                            <div class="report-image">
                                <img src="${report.image_path}" alt="Anomaly Report Image">
                            </div>
                            <div class="report-details">
                                <p><strong>Reason:</strong> ${report.reason}</p>
                                <p><strong>User:</strong> ${report.user.mobile}</p>
                                <p><strong>Location:</strong> ${report.location.latitude}, ${report.location.longitude}</p>
                                <p><strong>Status:</strong> ${report.status}</p>
                            </div>
                        </div>
                        <div class="report-actions">
                            <button class="accept-btn" data-id="${report.id}">Accept</button>
                            <button class="reject-btn" data-id="${report.id}">Reject</button>
                        </div>
                    `;
                    reportBox.appendChild(reportElement);
                });
            }
        } catch (error) {
            console.error('Error fetching reports:', error);
            reportBox.innerHTML = '<p>Error fetching reports</p>';
        }
    }

    // Handle report actions (accept/reject)
    reportBox.addEventListener('click', async (e) => {
        if (e.target.classList.contains('accept-btn')) {
            const reportId = e.target.dataset.id;
            try {
                const response = await fetch('/accept_report', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ id: reportId })
                });
                if (response.ok) {
                    fetchReports();
                }
            } catch (error) {
                console.error('Error accepting report:', error);
            }
        } else if (e.target.classList.contains('reject-btn')) {
            const reportId = e.target.dataset.id;
            try {
                const response = await fetch('/delete_report', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ id: reportId })
                });
                if (response.ok) {
                    fetchReports();
                }
            } catch (error) {
                console.error('Error rejecting report:', error);
            }
        }
    });

    // Initial fetch and periodic refresh
    fetchAlerts();
    fetchReports();
    setInterval(fetchAlerts, 5000); // Refresh alerts every 5 seconds
});
