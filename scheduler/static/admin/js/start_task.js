document.addEventListener('DOMContentLoaded', function() {
    document.querySelectorAll('.start-task-button').forEach(function(button) {
        button.addEventListener('click', function() {
            var taskId = this.getAttribute('data-task-id');
            var csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;

            fetch('/api/tasks/start/' + taskId + '/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': csrfToken
                }
            })
            .then(response => response.json())
            .then(data => {
                if (data.message) {
                    alert(data.message);
                } else {
                    alert('Error: ' + data.error);
                }
            })
            .catch(error => {
                console.error('Error:', error);
            });
        });
    });
});
