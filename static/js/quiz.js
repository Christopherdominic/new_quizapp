document.addEventListener('DOMContentLoaded', function() {
    fetch('/api/questions?token=' + token)
        .then(response => response.json())
        .then(data => {
            let quizContainer = document.getElementById('quiz-container');
            data.forEach((question, index) => {
                let questionElement = document.createElement('div');
                questionElement.innerHTML = `<p>${index + 1}. ${question.question}</p>`;
                quizContainer.appendChild(questionElement);
            });
        });
});

