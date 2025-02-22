let pie_labels = [];
let pie_data = [];
let bar_labels = [];
let bar_income_data = [];
let bar_expense_data=[];
async function fetchChartData() {
  try {
    const [barResponse, pieResponse] = await Promise.all([
      fetch("http://127.0.0.1:8000/bargraph"),
      fetch("/piechart")
    ]);

    if (!barResponse.ok || !pieResponse.ok) {
      throw new Error(`HTTP error! Bar Status: ${barResponse.status}, Pie Status: ${pieResponse.status}`);
    }

    const [barData, pieData] = await Promise.all([
      barResponse.json(),
      pieResponse.json()
    ]);


    if (barData && barData.months && barData.income_data && barData.expense_data) {
      bar_labels = barData.months;          
      bar_income_data = barData.income_data;
      bar_expense_data = barData.expense_data;

      const currentDate = new Date();
      const currentMonthIndex = currentDate.getMonth();

      let filteredMonths = [];
      let filteredIncome = [];
      let filteredExpense = [];

      for (let i = 5; i >= 0; i--) {
        let monthIndex = (currentMonthIndex - i + 12) % 12;
        filteredMonths.push(bar_labels[monthIndex]);
        filteredIncome.push(bar_income_data[monthIndex]);
        filteredExpense.push(bar_expense_data[monthIndex]);
      }

      bar_labels = filteredMonths;
      bar_income_data = filteredIncome;
      bar_expense_data = filteredExpense;
    } else {
      throw new Error("Invalid JSON response format for bar data");
    }

    if (pieData && pieData.category && pieData.amounts) {
      pie_labels = pieData.category;
      pie_data = pieData.amounts;
    } else {
      throw new Error("Invalid JSON response format for pie data");
    }

    console.log("Filtered Months:", bar_labels);
    console.log("Filtered Income Data:", bar_income_data);
    console.log("Filtered Expense Data:", bar_expense_data);

    renderCharts();
  } catch (error) {
    console.error("Error fetching chart data:", error);
  }
}



function renderCharts() {
    const pieData = {
      labels:pie_labels,
      datasets: [{
        data:pie_data,
        backgroundColor: ["#0088FE", "#00C49F","#F6851E","#733B97","#2EBCB3","#06B251","#FDED24","#D52128"]
      }]
    };
    const barData = {
      labels: bar_labels,
      datasets: [
        {
          label: "Income",
          data: bar_income_data,
          backgroundColor: "#8884d8"
        },
        {
          label: "Expenses",
          data: bar_expense_data,
          backgroundColor: "#82ca9d"
        }
      ]
    };
  
    const lineData = {
      labels: ["Jan", "Feb", "Mar", "Apr", "May", "Jun"],
      datasets: [{
        label: "Savings",
        data: [4000, 3000, 5000, 4780, 5890, 6390],
        borderColor: "#8884D8",
        fill: false,
        tension: 0.1
      }]
    };
  
    let pieChartInstance, barChartInstance=null, lineChartInstance;
    const pieCtx = document.getElementById("pieChart").getContext("2d");
    if (pieChartInstance) { pieChartInstance.destroy(); }
    pieChartInstance = new Chart(pieCtx, {
      type: 'pie',
      data: pieData,
      options: {
        responsive: true,
        plugins: {
          tooltip: {
            callbacks: {
              label: function(context) {
                let label = context.label || '';
                let value = context.parsed;
                let total = context.chart._metasets[context.datasetIndex].total;
                let percentage = ((value / total) * 100).toFixed(0);
                return label + ': ' + percentage + '%';
              }
            }
          }
        }
      }
    });

    const barCtx = document.getElementById("barChart").getContext("2d");
    if (barChartInstance) { barChartInstance.destroy(); }
    barChartInstance = new Chart(barCtx, {
      type: 'bar',
      data: barData,
      options: {
        responsive: true,
        scales: {
          x: { stacked: false },
          y: { stacked: false }
        }
      }
    });
    const lineCtx = document.getElementById("lineChart").getContext("2d");
    if (lineChartInstance) { lineChartInstance.destroy(); }
    lineChartInstance = new Chart(lineCtx, {
      type: 'line',
      data: lineData,
      options: {
        responsive: true,
        scales: {
          x: { display: true },
          y: { display: true }
        }
      }
    });
  }

  document.addEventListener("DOMContentLoaded", function() {
    fetchChartData();
  });

  function generatePDF() {
    const report = document.getElementById("reportSection");
    html2canvas(report, { scale: 2 }).then(canvas => {
      const imgData = canvas.toDataURL('image/png');
      const { jsPDF } = window.jspdf;
      const pdf = new jsPDF('p', 'mm', 'a4');
      const pdfWidth = pdf.internal.pageSize.getWidth();
      const imgProps = pdf.getImageProperties(imgData);
      const imgHeight = (imgProps.height * pdfWidth) / imgProps.width;
      pdf.addImage(imgData, 'PNG', 0, 0, pdfWidth, imgHeight);
      pdf.save('FinTrack_Report.pdf');
    });
  }

  