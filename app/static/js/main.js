document.addEventListener('DOMContentLoaded', function () {
    const ctx = document.getElementById('expensesChart');
    if (ctx) {
        fetch('/api/stats/month')
            .then(response => response.json())
            .then(data => {
                if (data.data.length === 0) {
                    // Handle empty data case if needed
                    return;
                }

                new Chart(ctx, {
                    type: 'doughnut',
                    data: {
                        labels: data.labels,
                        datasets: [{
                            data: data.data,
                            backgroundColor: data.colors,
                            borderWidth: 0
                        }]
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        plugins: {
                            legend: {
                                position: 'right',
                                labels: {
                                    color: '#B0B0B0'
                                }
                            }
                        }
                    }
                });
            })
            .catch(error => console.error('Error fetching stats:', error));
    }
});
