document.addEventListener('DOMContentLoaded', function() {
    // Initialize charts if the elements exist
    if (document.getElementById('evacueeStatusChart')) {
        createEvacueeStatusChart();
    }
    
    if (document.getElementById('donationTypesChart')) {
        createDonationTypesChart();
    }
    
    if (document.getElementById('centerOccupancyChart')) {
        createCenterOccupancyChart();
    }
});

function createEvacueeStatusChart() {
    const ctx = document.getElementById('evacueeStatusChart').getContext('2d');
    
    // Get data from the data attributes
    const chartElement = document.getElementById('evacueeStatusChart');
    const statusData = JSON.parse(chartElement.getAttribute('data-status'));
    
    const labels = Object.keys(statusData);
    const data = Object.values(statusData);
    
    const backgroundColors = [
        'rgba(75, 192, 192, 0.5)',
        'rgba(54, 162, 235, 0.5)',
        'rgba(255, 206, 86, 0.5)',
        'rgba(255, 99, 132, 0.5)'
    ];
    
    new Chart(ctx, {
        type: 'pie',
        data: {
            labels: labels,
            datasets: [{
                data: data,
                backgroundColor: backgroundColors,
                borderColor: backgroundColors.map(color => color.replace('0.5', '1')),
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            plugins: {
                legend: {
                    position: 'right',
                },
                title: {
                    display: true,
                    text: 'Evacuee Status Distribution'
                }
            }
        }
    });
}

function createDonationTypesChart() {
    const ctx = document.getElementById('donationTypesChart').getContext('2d');
    
    // Get data from the data attributes
    const chartElement = document.getElementById('donationTypesChart');
    const typesData = JSON.parse(chartElement.getAttribute('data-types'));
    
    const labels = Object.keys(typesData);
    const data = Object.values(typesData);
    
    const backgroundColors = [
        'rgba(75, 192, 192, 0.5)',
        'rgba(54, 162, 235, 0.5)'
    ];
    
    new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: labels,
            datasets: [{
                data: data,
                backgroundColor: backgroundColors,
                borderColor: backgroundColors.map(color => color.replace('0.5', '1')),
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            plugins: {
                legend: {
                    position: 'right',
                },
                title: {
                    display: true,
                    text: 'Donation Types Distribution'
                }
            }
        }
    });
}

function createCenterOccupancyChart() {
    const ctx = document.getElementById('centerOccupancyChart').getContext('2d');
    
    // Get data from the data attributes
    const chartElement = document.getElementById('centerOccupancyChart');
    const centersData = JSON.parse(chartElement.getAttribute('data-centers'));
    
    const labels = centersData.map(center => center.name);
    const occupancy = centersData.map(center => center.occupancy);
    const capacity = centersData.map(center => center.capacity);
    
    new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [
                {
                    label: 'Current Occupancy',
                    data: occupancy,
                    backgroundColor: 'rgba(75, 192, 192, 0.5)',
                    borderColor: 'rgba(75, 192, 192, 1)',
                    borderWidth: 1
                },
                {
                    label: 'Capacity',
                    data: capacity,
                    backgroundColor: 'rgba(54, 162, 235, 0.5)',
                    borderColor: 'rgba(54, 162, 235, 1)',
                    borderWidth: 1
                }
            ]
        },
        options: {
            responsive: true,
            scales: {
                y: {
                    beginAtZero: true,
                    title: {
                        display: true,
                        text: 'Number of People'
                    }
                },
                x: {
                    title: {
                        display: true,
                        text: 'Evacuation Centers'
                    }
                }
            },
            plugins: {
                title: {
                    display: true,
                    text: 'Evacuation Center Occupancy'
                }
            }
        }
    });
}
