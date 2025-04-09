// Charts.js script for analytics page

// Initialize charts when the DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
  // Get data from the page
  const analyticsData = JSON.parse(document.getElementById('analytics-data').textContent);
  
  // Create bar chart for appointments per day
  if (document.getElementById('appointmentsPerDayChart')) {
    createAppointmentsPerDayChart(
      analyticsData.dates, 
      analyticsData.daily_counts
    );
  }
  
  // Create pie chart for types of issues
  if (document.getElementById('issuesTypeChart')) {
    createIssuesTypeChart(
      analyticsData.issues, 
      analyticsData.issue_counts
    );
  }
});

// Function to create the appointments per day chart
function createAppointmentsPerDayChart(dates, counts) {
  const ctx = document.getElementById('appointmentsPerDayChart').getContext('2d');
  
  new Chart(ctx, {
    type: 'bar',
    data: {
      labels: dates,
      datasets: [{
        label: 'Appointments',
        data: counts,
        backgroundColor: 'rgba(54, 162, 235, 0.5)',
        borderColor: 'rgba(54, 162, 235, 1)',
        borderWidth: 1
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      scales: {
        y: {
          beginAtZero: true,
          ticks: {
            precision: 0
          }
        }
      },
      plugins: {
        title: {
          display: true,
          text: 'Appointments Per Day (Last 7 Days)'
        },
        legend: {
          display: false
        }
      }
    }
  });
}

// Function to create the issues type pie chart
function createIssuesTypeChart(issues, counts) {
  const ctx = document.getElementById('issuesTypeChart').getContext('2d');
  
  // Generate colors array
  const colors = generateColors(issues.length);
  
  new Chart(ctx, {
    type: 'pie',
    data: {
      labels: issues,
      datasets: [{
        data: counts,
        backgroundColor: colors.background,
        borderColor: colors.border,
        borderWidth: 1
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        title: {
          display: true,
          text: 'Types of Issues Handled'
        },
        legend: {
          position: 'right'
        }
      }
    }
  });
}

// Generate color arrays for charts
function generateColors(count) {
  const backgroundColors = [];
  const borderColors = [];
  
  const baseColors = [
    'rgba(54, 162, 235, 0.5)',  // blue
    'rgba(255, 99, 132, 0.5)',  // red
    'rgba(255, 206, 86, 0.5)',  // yellow
    'rgba(75, 192, 192, 0.5)',  // green
    'rgba(153, 102, 255, 0.5)', // purple
    'rgba(255, 159, 64, 0.5)'   // orange
  ];
  
  const baseBorders = [
    'rgba(54, 162, 235, 1)',
    'rgba(255, 99, 132, 1)',
    'rgba(255, 206, 86, 1)',
    'rgba(75, 192, 192, 1)',
    'rgba(153, 102, 255, 1)',
    'rgba(255, 159, 64, 1)'
  ];
  
  // Generate colors by cycling through base colors
  for (let i = 0; i < count; i++) {
    backgroundColors.push(baseColors[i % baseColors.length]);
    borderColors.push(baseBorders[i % baseBorders.length]);
  }
  
  return {
    background: backgroundColors,
    border: borderColors
  };
}
