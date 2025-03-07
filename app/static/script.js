// Generated by Copilot
document.addEventListener('DOMContentLoaded', function() {
    const form = document.querySelector('#editForm');
    if (form) {
        form.addEventListener('submit', function(e) {
            e.preventDefault();
            
            const entryId = form.getAttribute('data-entry-id');
            const formData = {
                timestamp: document.getElementById('timestamp').value,
                systolic: parseInt(document.getElementById('systolic').value),
                diastolic: parseInt(document.getElementById('diastolic').value),
                heart_rate: parseInt(document.getElementById('heart_rate').value),
                tags: document.getElementById('tags').value
            };

            fetch(`/api/update/${entryId}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(formData)
            })
            .then(response => {
                if (!response.ok) {
                    throw new Error('Network response was not ok');
                }
                return response.json();
            })
            .then(data => {
                if (data.success) {
                    window.location.href = '/';
                } else {
                    alert(data.message || 'Update failed');
                }
            })
            .catch(error => {
                console.error('Error:', error);
                alert('Failed to update entry. Please check the console for details.');
            });
        });
    }
});