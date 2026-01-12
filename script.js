
document.addEventListener('DOMContentLoaded', function() {
    var alerts = document.querySelectorAll('.alert');
    for (var i = 0; i < alerts.length; i++) {
        setTimeout(function() {
            var alert = alerts[0];
            if (alert) {
                alert.style.display = 'none';
            }
        }, 3000);
    }
});

window.onload = function() {
    var dateInputs = document.querySelectorAll('input[type="date"]');
    var today = new Date();
    var year = today.getFullYear();
    var month = today.getMonth() + 1;
    var day = today.getDate();
    
    if (month < 10) {
        month = '0' + month;
    }
    if (day < 10) {
        day = '0' + day;
    }
    
    var todayString = year + '-' + month + '-' + day;
    
    for (var i = 0; i < dateInputs.length; i++) {
        if (!dateInputs[i].value) {
            dateInputs[i].value = todayString;
        }
    }

    var monthInputs = document.querySelectorAll('input[type="month"]');
    var currentMonth = year + '-' + month;
    
    for (var j = 0; j < monthInputs.length; j++) {
        if (!monthInputs[j].value) {
            monthInputs[j].value = currentMonth;
        }
    }
};

document.addEventListener('DOMContentLoaded', function() {
    var expenseForm = document.querySelector('form[action*="expenses"]');
    if (expenseForm) {
        expenseForm.addEventListener('submit', function(e) {
            var amount = document.querySelector('input[name="amount"]').value;
            if (amount <= 0) {
                alert('Amount must be greater than zero');
                e.preventDefault();
            }
        });
    }
    
    var incomeForm = document.querySelector('form[action*="income"]');
    if (incomeForm) {
        incomeForm.addEventListener('submit', function(e) {
            var amount = document.querySelector('input[name="amount"]').value;
            if (amount <= 0) {
                alert('Amount must be greater than zero');
                e.preventDefault();
            }
        });
    }
    var budgetForm = document.querySelector('form[action*="budget"]');
    if (budgetForm) {
        budgetForm.addEventListener('submit', function(e) {
            var amount = document.querySelector('input[name="amount"]').value;
            if (amount <= 0) {
                alert('Budget amount must be greater than zero');
                e.preventDefault();
            }
        });
    }

});
