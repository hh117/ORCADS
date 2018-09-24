$(document).ready(function() {
    var current_page = "small-talk"
    var current_state = "start"
    var user = document.querySelector('.user');

    var socket = io.connect('http://' + document.domain + ':' + location.port);

    // Grab elements, create settings, etc.
    var video = document.getElementById('video');

    if (!('webkitSpeechRecognition' in window)) {
      upgrade();
    } else {
      var recognition = new webkitSpeechRecognition();
      recognition.lang = 'en-GB';
      recognition.maxAlternatives = 1;

      document.querySelector('button').addEventListener('click', () =>
         {recognition.start();}
      );

      recognition.addEventListener('result', (e) => {
        console.log('Result has been detected.');

        let last = e.results.length - 1;
        let text = e.results[last][0].transcript;

        user.textContent = text;
        console.log('Confidence: ' + e.results[0][0].confidence);

        socket.emit('chat', text);
       });
    }

    // Get access to the camera!
    if(navigator.mediaDevices && navigator.mediaDevices.getUserMedia) {
        // Not adding `{ audio: true }` since we only want video now
        //navigator.mediaDevices.getUserMedia({ video: { width: 1280, height: 720 }, audio: true}).then(function(stream) {
        navigator.mediaDevices.getUserMedia({ video: { width: 1280, height: 720 }}).then(function(stream) {
            video.src = window.URL.createObjectURL(stream);
            video.play();
            video.onloadedmetadata = function() {
              console.log('width is', this.videoWidth);
              console.log('height is', this.videoHeight);
            }
        });
    }


    socket.on('connect', function(data){
      console.log("connected")
      socket.emit("restart")
    });

    function reset() {
        $('.list-group').removeClass('dim');
    }


    $('html').on('keyup', function(event) {
        combo = [];
        stop = false;
        reset();
    });

    $(".change-pane").on("click", function() {
        $(".tab-content .tab-pane").removeClass("active")
        $("#" + $(this).data("page")).addClass("active")
        current_page = $(this).data("page")
    })
});
