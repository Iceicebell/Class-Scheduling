document.getElementById("generateForm").addEventListener("submit", function(e) {
    e.preventDefault();
    // Show loading indicator
    document.querySelector('.table-section').classList.add('loading');
    // ... rest of your code ...
})
.then(data => {
    // ... update table ...
    // Hide loading indicator
    document.querySelector('.table-section').classList.remove('loading');
})
.catch(error => {
    console.error("Error:", error);
    // Hide loading indicator
    document.querySelector('.table-section').classList.remove('loading');
    // Show error message to user
    alert("An error occurred while generating the schedule. Please try again.");
});

document.addEventListener('DOMContentLoaded', function() {
    const generateForm = document.getElementById('generateForm');
    const generateButton = document.getElementById('generate-button');
    const loadingIndicator = document.getElementById('loading');
    const scheduleResult = document.getElementById('scheduleResult');

    generateButton.addEventListener('click', function(e) {
        e.preventDefault();
        loadingIndicator.style.display = 'block';
        scheduleResult.innerHTML = '';  // Clear previous results

        fetch('/department-head/generate', {
            method: 'POST',
            body: new FormData(generateForm),
            headers: {
                'X-Requested-With': 'XMLHttpRequest'
            }
        })
        .then(response => response.text())
        .then(html => {
            loadingIndicator.style.display = 'none';
            scheduleResult.innerHTML = html;
        })
        .catch(error => {
            loadingIndicator.style.display = 'none';
            console.error('Error:', error);
            scheduleResult.innerHTML = '<p>An error occurred while generating the schedule. Please try again.</p>';
        });
    });
});