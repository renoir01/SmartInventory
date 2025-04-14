// Product Performance Chart
function initProductPerformanceChart(chartData) {
    var ctx = document.getElementById('productPerformanceChart').getContext('2d');
    
    new Chart(ctx, {
        type: 'bar',
        data: {
            labels: chartData.labels,
            datasets: [
                {
                    label: chartData.revenueLabel,
                    data: chartData.revenueData,
                    backgroundColor: 'rgba(75, 192, 192, 0.2)',
                    borderColor: 'rgba(75, 192, 192, 1)',
                    borderWidth: 1
                },
                {
                    label: chartData.profitLabel,
                    data: chartData.profitData,
                    backgroundColor: 'rgba(153, 102, 255, 0.2)',
                    borderColor: 'rgba(153, 102, 255, 1)',
                    borderWidth: 1
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                y: {
                    beginAtZero: true,
                    title: {
                        display: true,
                        text: chartData.yAxisLabel
                    }
                },
                x: {
                    title: {
                        display: true,
                        text: chartData.xAxisLabel
                    }
                }
            },
            plugins: {
                legend: {
                    position: 'top'
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            return context.dataset.label + ': ' + context.raw.toLocaleString() + ' RWF';
                        }
                    }
                }
            }
        }
    });
}

// Product Quantity Chart
function initProductQuantityChart(chartData) {
    var ctx = document.getElementById('productQuantityChart').getContext('2d');
    
    new Chart(ctx, {
        type: 'bar',
        data: {
            labels: chartData.labels,
            datasets: [
                {
                    label: chartData.quantityLabel,
                    data: chartData.quantityData,
                    backgroundColor: 'rgba(54, 162, 235, 0.2)',
                    borderColor: 'rgba(54, 162, 235, 1)',
                    borderWidth: 1
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                y: {
                    beginAtZero: true,
                    title: {
                        display: true,
                        text: chartData.quantityAxisLabel
                    }
                },
                x: {
                    title: {
                        display: true,
                        text: chartData.xAxisLabel
                    }
                }
            },
            plugins: {
                legend: {
                    position: 'top'
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            return context.dataset.label + ': ' + context.raw.toLocaleString() + ' ' + chartData.quantityUnit;
                        }
                    }
                }
            }
        }
    });
}

// Initialize all charts when document is ready
document.addEventListener('DOMContentLoaded', function() {
    // Check if the global data variable exists
    if (typeof productChartData !== 'undefined') {
        // Initialize charts with the global data
        initProductPerformanceChart(productChartData);
        initProductQuantityChart(productChartData);
    }
});
