/**
 * FaceAttend - Live Attendance Real-time Monitor & Event Controller
 */

let pollInterval = null;
let lastEventTimestamps = new Set();

document.addEventListener('DOMContentLoaded', () => {
    const liveFeedContainer = document.getElementById('live-attendance-feed');
    if (liveFeedContainer) {
        startLivePolling();
    }
});

function startLivePolling() {
    pollInterval = setInterval(fetchLiveUpdates, 1500);
}

async function fetchLiveUpdates() {
    try {
        const res = await fetch('/api/live_status');
        const data = await res.json();
        
        if (data && data.recent_events) {
            updateEventFeed(data.recent_events);
        }
        
        // Update header count if present
        const regCountEl = document.getElementById('hud-registered-count');
        if (regCountEl && data.registered_count !== undefined) {
            regCountEl.innerText = `${data.registered_count} Enrolled`;
        }
    } catch (e) {
        console.error('Error fetching live updates:', e);
    }
}

function updateEventFeed(events) {
    const container = document.getElementById('live-attendance-feed');
    if (!container) return;

    if (!events || events.length === 0) {
        if (container.children.length === 0) {
            container.innerHTML = `
                <div style="text-align: center; padding: 2.5rem 1rem; color: var(--text-muted);">
                    <div style="font-size: 2rem; margin-bottom: 0.5rem;">👁</div>
                    <p style="font-size: 0.9rem; font-weight: 500;">Awaiting Face Detections</p>
                    <p style="font-size: 0.75rem;">Stand before the camera to mark real-time attendance</p>
                </div>
            `;
        }
        return;
    }

    // Filter to top 6 events
    const displayEvents = events.slice(0, 6);
    
    let html = '';
    displayEvents.forEach(evt => {
        const typeClass = evt.type || 'info';
        const isSuccess = evt.status === 'Marked Present';
        const isAlready = evt.status === 'Already Marked';
        
        let badgeBg = 'rgba(99, 102, 241, 0.15)';
        let badgeColor = 'var(--primary)';
        let badgeIcon = 'ℹ';
        
        if (isSuccess) {
            badgeBg = 'rgba(16, 185, 129, 0.15)';
            badgeColor = 'var(--success)';
            badgeIcon = '✓';
            
            // New attendance toast trigger
            const eventKey = `${evt.student_id}_${evt.timestamp}`;
            if (!lastEventTimestamps.has(eventKey)) {
                lastEventTimestamps.add(eventKey);
                showToast(`✓ Attendance Marked: ${evt.name} (${evt.confidence}%)`, 'success');
            }
        } else if (isAlready) {
            badgeBg = 'rgba(56, 189, 248, 0.15)';
            badgeColor = 'var(--accent-cyan)';
            badgeIcon = '📋';
        } else if (evt.status === 'Low Confidence') {
            badgeBg = 'rgba(245, 158, 11, 0.15)';
            badgeColor = 'var(--warning)';
            badgeIcon = '⚠';
        } else {
            badgeBg = 'rgba(239, 68, 68, 0.15)';
            badgeColor = 'var(--danger)';
            badgeIcon = '✕';
        }

        html += `
            <div class="rec-event-item ${typeClass}" style="margin-bottom: 0.75rem;">
                <div style="width: 38px; height: 38px; border-radius: var(--radius-md); background: ${badgeBg}; color: ${badgeColor}; display: flex; align-items: center; justify-content: center; font-weight: bold; font-size: 1.1rem;">
                    ${badgeIcon}
                </div>
                <div style="flex: 1; min-width: 0;">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.2rem;">
                        <h4 style="font-size: 0.9rem; font-weight: 600; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">
                            ${evt.name || evt.status}
                        </h4>
                        <span style="font-size: 0.75rem; color: var(--text-muted);">${evt.timestamp}</span>
                    </div>
                    <div style="display: flex; gap: 0.5rem; align-items: center; font-size: 0.75rem;">
                        <span style="color: ${badgeColor}; font-weight: 600;">${evt.status}</span>
                        ${evt.confidence ? `<span style="color: var(--text-muted);">• Conf: ${evt.confidence}%</span>` : ''}
                        ${evt.student_id ? `<span style="color: var(--text-muted);">• ID: ${evt.student_id}</span>` : ''}
                    </div>
                </div>
            </div>
        `;
    });

    container.innerHTML = html;
}
