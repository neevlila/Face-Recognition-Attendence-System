/**
 * FaceAttend - Analytics & Chart.js Configs
 */

function initAttendanceCharts(weeklyData, deptData) {
    // 1. Weekly Attendance Trend (Line Chart)
    const trendCtx = document.getElementById('weeklyTrendChart');
    if (trendCtx && weeklyData) {
        new Chart(trendCtx, {
            type: 'line',
            data: {
                labels: weeklyData.labels,
                datasets: [{
                    label: 'Present Students',
                    data: weeklyData.data,
                    borderColor: '#6366f1',
                    backgroundColor: 'rgba(99, 102, 241, 0.12)',
                    borderWidth: 2.5,
                    fill: true,
                    tension: 0.35,
                    pointBackgroundColor: '#818cf8',
                    pointBorderColor: '#0b1020',
                    pointBorderWidth: 2,
                    pointRadius: 4,
                    pointHoverRadius: 6
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: false },
                    tooltip: {
                        backgroundColor: '#172033',
                        titleColor: '#f8fafc',
                        bodyColor: '#94a3b8',
                        borderColor: 'rgba(255,255,255,0.1)',
                        borderWidth: 1,
                        padding: 10
                    }
                },
                scales: {
                    x: {
                        grid: { color: 'rgba(255, 255, 255, 0.04)' },
                        ticks: { color: '#64748b', font: { size: 11 } }
                    },
                    y: {
                        beginAtZero: true,
                        grid: { color: 'rgba(255, 255, 255, 0.04)' },
                        ticks: { color: '#64748b', precision: 0, font: { size: 11 } }
                    }
                }
            }
        });
    }

    // 2. Department Breakdown (Bar Chart)
    const deptCtx = document.getElementById('deptChart');
    if (deptCtx && deptData) {
        new Chart(deptCtx, {
            type: 'bar',
            data: {
                labels: deptData.labels,
                datasets: [
                    {
                        label: 'Present Today',
                        data: deptData.present,
                        backgroundColor: '#10b981',
                        borderRadius: 4
                    },
                    {
                        label: 'Total Enrolled',
                        data: deptData.total,
                        backgroundColor: '#1e293b',
                        borderRadius: 4
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'top',
                        labels: { color: '#94a3b8', boxWidth: 12, font: { size: 11 } }
                    },
                    tooltip: {
                        backgroundColor: '#172033',
                        titleColor: '#f8fafc',
                        bodyColor: '#94a3b8',
                        borderColor: 'rgba(255,255,255,0.1)',
                        borderWidth: 1,
                        padding: 10
                    }
                },
                scales: {
                    x: {
                        grid: { display: false },
                        ticks: { color: '#64748b', font: { size: 11 } }
                    },
                    y: {
                        beginAtZero: true,
                        grid: { color: 'rgba(255, 255, 255, 0.04)' },
                        ticks: { color: '#64748b', precision: 0, font: { size: 11 } }
                    }
                }
            }
        });
    }
}
