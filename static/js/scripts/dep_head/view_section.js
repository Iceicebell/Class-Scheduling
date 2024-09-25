const timeGrid = document.querySelector('.time-grid');
const dayHeaders = document.querySelectorAll('.day-header span');

function toggleTimeSlot(dayIndex, timeIndex) {
    const slot = timeGrid.children[timeIndex + 1].children[dayIndex];
    slot.classList.toggle('selected');
}

// Add click event listeners to each day header
dayHeaders.forEach((header, index) => {
    header.addEventListener('click', () => {
        toggleTimeSlot(index, 0);
    });
});

// Example: Toggle specific time slots
toggleTimeSlot(2, 3); // Toggles 08:00 on Wednesday