// Global variables
var gumStream;
var input;
var rec;
var ws;
var recordedText;

class Chatbox {
    constructor() {
        this.args = {
            openButton: document.querySelector('.chatbox__button'),
            chatBox: document.querySelector('.chatbox__support'),
            recordButton: document.querySelector('.record__button'),
            sendButton: document.querySelector('.send__button')
        }

        this.state = false;
        this.messages = [];
        this.hasFirstMessage = false;
        this.messageSent = false;
        
    }

    display() {
        const { openButton, chatBox, recordButton, sendButton } = this.args;

        openButton.addEventListener('click', () => this.toggleState(chatBox))

        recordButton.addEventListener('click', () => this.onRecordButton(chatBox))

        sendButton.addEventListener('click', () => this.onSendButton(chatBox))

        const node = chatBox.querySelector('input');
        node.addEventListener("keyup", ({ key }) => {
            if (key === "Enter") {
                this.onSendButton(chatBox)
            }
        })
    }

    toggleState(chatbox) {
        this.state = !this.state;

        if (!this.hasFirstMessage) {
            fetch('http://127.0.0.1:5000/start', {
                method: 'GET',
                mode: 'cors',
            })
                .then(r => r.json())
                .then(r => {
                    // Printing conversation initialization message in chatbox
                    let msg2 = { name: "Chatbot", message: r.answer };
                    this.messages.push(msg2);
                    this.updateChatText(chatbox)

                    // Sending conversation initialization message to ws
                    let ws = new WebSocket("wss://api-tts.zevo-tech.com:2083");
                    ws.onopen = function (event) {
                        // Message to send to API
                        var message = '{"task": [{"text": "' + r.answer + '"}, {"voice": "' + "ema" + '"}, {"key": "' + "popescunichitastefan" + '"}]}'
                        ws.send(message);
                    };



                    // Receiving conversation initialization message from ws
                    ws.onmessage = function (event) {
                        // Create audioContext
                        let audioContext = new AudioContext({
                            sampleRate: 22050
                        });

                        // Create a sound source to play the audio
                        var source = audioContext.createBufferSource();

                        // Use arrayBuffer to create the audioBuffer
                        event.data.arrayBuffer().then(arrayBuffer => {
                            audioContext.decodeAudioData(arrayBuffer, (audioBuffer) => {
                                source.buffer = audioBuffer;   // tell the source which sound to play
                                source.connect(audioContext.destination);    // connect the source to the context's destination (the speakers)
                                source.start(0);   // play the source now
                            })
                        });
                    };

                    this.hasFirstMessage = true;

                }).catch((error) => {
                    console.error('Error:', error);
                    this.updateChatText(chatbox)
                });
        }

        // show or hides the box
        if (this.state) {
            chatbox.classList.add('chatbox--active')
        } else {
            chatbox.classList.remove('chatbox--active')
        }

        this.state = !this.state;

    }

    startRecording(){
        navigator.mediaDevices.getUserMedia({ audio: true, video: false }).then(function (stream) {

            let audioContext = new AudioContext({
                latencyHint: 'interactive',
                sampleRate: 16000,
            });

            gumStream = stream;
            input = audioContext.createMediaStreamSource(stream);
            rec = new Recorder(input, { numChannels: 1 })

            rec.record();

        });
        
        // Create ws
        ws = new WebSocket("wss://live-transcriber.zevo-tech.com:2053");
        ws.binaryType = 'arraybuffer';

        ws.onmessage = function (event){
            console.log(event.data)
        }

        ws.onopen = function (event) {
            // Key to send to API
            ws.send('{"config": {"key": "' + "popescunichitastefan" + '"}}')
            
            // Sample rate to send to API
            let sample_rate = 16000;
            ws.send('{"config": {"sample_rate": "' + sample_rate + '"}}');
            // ws.onmessage = function (event){
            //     console.log(event.data)
            // }
        }
        
        console.log(ws)
    }

    stopRecording(chatbox){
        rec.stop();
        console.log(ws)

        // Sending blob to ws
        rec.exportWAV(function (blob) {
            console.log(blob)
            ws.send(blob);
        },
            'audio/x-wav');

        
        // Receive json
        ws.onmessage = event => {
            let thisSession = JSON.parse(event.data);
            console.log(event.data)
            console.log(thisSession)
            if (thisSession.hasOwnProperty("partial")) {
                recordedText = thisSession.partial;
                rec.clear();
                console.log(recordedText)
            }

            gumStream.getAudioTracks()[0].stop();
            ws.close();

            let chatbotMessage = { name: "Niki", message: recordedText };
            this.messages.push(chatbotMessage);
            this.updateChatText(chatbox)


            fetch('http://127.0.0.1:5000/get_answer', {
                method: 'POST',
                body: JSON.stringify({ message: recordedText }),
                mode: 'cors',
                headers: {
                    'Content-Type': 'application/json'
                },
            })
                .then(r => r.json())
                .then(r => {
                    let chatbotMessage = { name: "Chatbot", message: r.answer };
                    this.messages.push(chatbotMessage);
                    this.updateChatText(chatbox)

                    // Sending conversation response message to ws
                    let ws = new WebSocket("wss://api-tts.zevo-tech.com:2083");
                    ws.onopen = function (event) {
                        // Message to send to API
                        var message = '{"task": [{"text": "' + r.answer + '"}, {"voice": "' + "ema" + '"}, {"key": "' + "popescunichitastefan" + '"}]}'
                        ws.send(message);
                    };



                    // Receiving conversation response message from ws
                    ws.onmessage = function (event) {
                        // Create audioContext
                        let audioContext = new AudioContext({
                            sampleRate: 22050
                        });

                        // Create a sound source to play the audio
                        var source = audioContext.createBufferSource();

                        // Use arrayBuffer to create the audioBuffer
                        event.data.arrayBuffer().then(arrayBuffer => {
                            audioContext.decodeAudioData(arrayBuffer, (audioBuffer) => {
                                source.buffer = audioBuffer;   // tell the source which sound to play
                                source.connect(audioContext.destination);    // connect the source to the context's destination (the speakers)
                                source.start(0);   // play the source now
                            })
                        });
                    };

                }).catch((error) => {
                    console.error('Error:', error);
                    this.updateChatText(chatbox)
                });

        }        
        
    }

    onRecordButton(chatbox) {
        this.state = !this.state;

        //record or stop recording
        if (this.state) {
            //mic record
            this.startRecording();            
        } else {

            //stop recording
            if(!this.messageSent){
                this.stopRecording(chatbox);
                this.messageSent = !this.messageSent;
            }
            
                // Set messageSent flag to false again to be able to send again a vocal message
                this.messageSent = !this.messageSent;

        }
    }

    onSendButton(chatbox) {
        var textField = chatbox.querySelector('input');
        let inputText = textField.value
        if (inputText === "") {
            return;
        }

        let userMsg = { name: "User", message: inputText }
        this.messages.push(userMsg);

        fetch('http://127.0.0.1:5000/get_answer', {
            method: 'POST',
            body: JSON.stringify({ message: inputText }),
            mode: 'cors',
            headers: {
                'Content-Type': 'application/json'
            },
        })
            .then(r => r.json())
            .then(r => {
                let chatbotMessage = { name: "Chatbot", message: r.answer };
                this.messages.push(chatbotMessage);
                this.updateChatText(chatbox)
                textField.value = ''

                // Sending conversation response message to ws
                let ws = new WebSocket("wss://api-tts.zevo-tech.com:2083");
                ws.onopen = function (event) {
                    // Message to send to API
                    var message = '{"task": [{"text": "' + r.answer + '"}, {"voice": "' + "ema" + '"}, {"key": "' + "popescunichitastefan" + '"}]}'
                    ws.send(message);
                };



                // Receiving conversation response message from ws
                ws.onmessage = function (event) {
                    // Create audioContext
                    let audioContext = new AudioContext({
                        sampleRate: 22050
                    });

                    // Create a sound source to play the audio
                    var source = audioContext.createBufferSource();

                    // Use arrayBuffer to create the audioBuffer
                    event.data.arrayBuffer().then(arrayBuffer => {
                        audioContext.decodeAudioData(arrayBuffer, (audioBuffer) => {
                            source.buffer = audioBuffer;   // tell the source which sound to play
                            source.connect(audioContext.destination);    // connect the source to the context's destination (the speakers)
                            source.start(0);   // play the source now
                        })
                    });
                };

            }).catch((error) => {
                console.error('Error:', error);
                this.updateChatText(chatbox)
                textField.value = ''
            });
    }

    updateChatText(chatbox) {
        var html = '';
        this.messages.slice().reverse().forEach(function (item, index) {
            if (item.name === "Chatbot") {
                html += '<div class="messages__item messages__item--visitor">' + item.message + '</div>'
            }
            else {
                html += '<div class="messages__item messages__item--operator">' + item.message + '</div>'
            }
        });

        const chatmessage = chatbox.querySelector('.chatbox__messages');
        chatmessage.innerHTML = html;
    }
}


const chatbox = new Chatbox();
chatbox.display();