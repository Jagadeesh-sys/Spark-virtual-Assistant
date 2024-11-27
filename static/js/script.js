document.addEventListener('DOMContentLoaded', function() {
    const button = document.querySelector('.talk');
    const content = document.querySelector('.content');
    const answerContainer = document.querySelector('.answer-container');
    const answerText = document.querySelector('.answer-text');
    const copyBtn = document.querySelector('.copy-btn');
    const main = document.querySelector('.main');
    const responseImageDiv = document.getElementById('response-image');
    const responseImg = document.getElementById('response-img');

    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    const recognition = new SpeechRecognition();

    recognition.onstart = function() {
        content.textContent = 'Listening...';
    };

    recognition.onresult = function(event) {
        const current = event.resultIndex;
        const transcript = event.results[current][0].transcript;
        content.textContent = transcript;

        handleCommand(transcript);

        fetch('/process', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ user_input: transcript }),
        })
        .then(response => response.json())
        .then(data => {
            const responseText = data.response;
            const imageUrl = data.image_url;

            answerText.innerHTML = ''; // Clear previous text
            answerContainer.style.display = 'block'; // Show the answer container
            main.style.width = '50%'; // Adjust the width of the main section

            // Update the image container
            if (imageUrl) {
                responseImg.src = imageUrl;
                responseImg.style.display = 'block';
            } else {
                responseImg.style.display = 'none';
            }

            typeText(responseText, answerText); // Type the response text incrementally
            speak(responseText); // Speak the response
            console.log("Response Text:", responseText); // Print the response text to the console
        })
        .catch(error => {
            console.error('Error:', error);
        });
    };

    button.addEventListener('click', function() {
        recognition.start();
    });

    copyBtn.addEventListener('click', function() {
        const textToCopy = answerText.textContent;
        navigator.clipboard.writeText(textToCopy).then(() => {
            console.log('Text copied to clipboard');
        }).catch(err => {
            console.error('Failed to copy text: ', err);
        });
    });

    function speak(text) {
        const utterance = new SpeechSynthesisUtterance(text);
        window.speechSynthesis.speak(utterance);
    }

    function handleCommand(command) {
        if (command.toLowerCase().includes('open youtube')) {
            window.open('https://www.youtube.com', '_blank');
        } else if (command.toLowerCase().includes('open google')) {
            window.open('https://www.google.com', '_blank');
        } else if (command.toLowerCase().includes('open notepad')) {
            fetch('/open_notepad', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
            })
            .then(response => response.json())
            .then(data => {
                console.log("Notepad opened");
            })
            .catch(error => {
                console.error('Error:', error);
            });
        } else if (command.toLowerCase().includes('exit')) {
            window.speechSynthesis.cancel();
        }
    }

    function typeText(text, element) {
        let index = 0;
        const speed = 1; // Adjust typing speed (ms per character)

        function type() {
            if (index < text.length) {
                element.innerHTML += text[index];
                index++;
                setTimeout(type, speed);
            }
        }
        type();
    }
});

function startRecognition() {
    recognition.start();
}
