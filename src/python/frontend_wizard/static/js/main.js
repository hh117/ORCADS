$(document).ready(function() {
    var current_page = "flow-utt"
    var current_state = "start"

    var socket = io.connect('http://' + document.domain + ':' + location.port);

    // Grab elements, create settings, etc.
    var video = document.getElementById('video');

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

    window.sendToWizard = function(final_transcript) {
        socket.emit("say", {"text": final_transcript})
        $(".tab-content .tab-pane").removeClass("active")
        $("#flow-utt").addClass("active")
        current_page = "flow-utt"
        console.log(final_transcript)
    }

    function updateSentences(utterances,states,state,gestures,sequence_info) {
      //removes utterances added to the original set
      $('.generated').remove()
      $('#flow-utt li').css('background-color','white')
      //reset utterances generated
      utterancesGenerated = [];
      var utt_array = utterances.split("|")
      state_array = states.split("|")
      current_state = state
      gestures_array = gestures.split("|")
      sequence_array = sequence_info.split("|")
      console.log(current_state)
      for(var u=0; u < utt_array.length; u++){
        utterancesGenerated.push(utt_array[u])
        $('#general').append('<li class="list-group-item generated">' + utt_array[u] + '<span class="badge">' + (u+1) + '</span></li>');
      }
    }

    socket.on('add_utterance_to_list', function(data) {
      updateSentences(data["sentence"],data["state"],data['current_state'],data["gestures"],data["sequence"]);
    });

    function reset() {
        $('.list-group').removeClass('dim');
    }

    var state = 0;
    var combo = [];
    var stop = false;
    $('html').on('keydown', function(event) {
        if (stop) return;
        if ($(event.target).attr('id') === 'name') return true;
        var keyPressed = event.key.toLowerCase();
        combo.push(keyPressed);
        console.log(combo.sort().join('-'))

        if (combo.length == 2) {
            var modifier = null;
            if (combo.indexOf('alt') !== -1){
                modifier = 'support';
            } else if (combo.indexOf('control') !== -1){
                modifier = 'defend';
            } else if (combo.indexOf('shift') !== -1){
                //console.log(current_page.indexOf('flow-utt'))
                if(current_page.indexOf('flow-utt') !== -1){
                    modifier = 'small_talk'
                }else if(current_page.indexOf('dialog') !== -1){
                    modifier = 'accuse';
                }else if(current_page.indexOf('argue-vote')){
                    modifier = 'kill'
                }
            }

            if (modifier) {
                var participant = combo.filter(item => ['alt', 'control', 'shift','meta'].indexOf(item) === -1)[0]
                switch(participant) {
                    case '§':
                    case '±':
                      $.get(`/say?text=${modifier}`)
                      break;
                    case '0':
                    case 'º':
                    case ')':
                    case '=':
                    case '≠':
                      $.get(`/say?text=${modifier}&participant=red`)
                      break;
                    case '1':
                    case '¡':
                    case '!':
                    case '':
                      $.get(`/dialog_act?action=${modifier}&participant=black`)
                      break;
                    case '2':
                    case '™':
                    case '@':
                    case '"':
                      $.get(`/dialog_act?action=${modifier}&participant=brown`)
                      break;
                    case '3':
                    case '£':
                    case '#':
                    case '€':
                      $.get(`/dialog_act?action=${modifier}&participant=orange`)
                      break;
                    case '4':
                    case '¢':
                    case '$':
                    case '£':
                      $.get(`/dialog_act?action=${modifier}&participant=blue`)
                      break;
                    case '5':
                    //case '§':
                    case '^':
                    case '%':
                    case '‰':
                      $.get(`/dialog_act?action=${modifier}&participant=pink`)
                      break;
                    case '6':
                    case '¶':
                    case '&':
                    case '¶':
                      $.get(`/dialog_act?action=${modifier}&participant=white`)
                      break;
                }

            }

        }

        console.log(current_page)
        if ( current_page == 'flow-utt'){
            switch(combo.sort().join('-')) {
                case 'y':
                  socket.emit("say", {"text": "yes", "state": current_state, "gesture": "", sequence: "False"})
                  break;
                case 'u':
                  socket.emit("say", {"text": "no", "state": current_state, "gesture": "", sequence: "False"})
                  break;
                case 'i':
                  socket.emit("say", {"text": "Maybe", "state": current_state, "gesture": "", sequence: "False"})
                  break;
                case 'o':
                  socket.emit("say", {"text": "Mm", "state": current_state, "gesture": "", sequence: "False"})
                  break;
                case 'p':
                  socket.emit("say", {"text": "Mhm", "state": current_state, "gesture": "", sequence: "False"})
                  break;
                case 'å':
                  socket.emit("say", {"text": "I'm not sure", "state": current_state, "gesture": "", sequence: "False"})
                  break;
                case 'n':
                  socket.emit('attend',{"text":"other"})
                  break;
                case 'v':
                  socket.emit('attend',{'text':'all'})
                  break;
                case ' ':
                  socket.emit("say", {"text": "repeat", "state": current_state, "gesture": "", sequence: "False"})
                  break;
                case '1':
                case '2':
                case '3':
                case '4':
                case '5':
                case '6':
                case '7':
                case '8':
                case '9':
                  indexUtt = parseInt(combo.sort().join('-'))
                  if (utterancesGenerated.length > indexUtt-1) {
                    socket.emit("say",{"text":utterancesGenerated[indexUtt-1],"state":state_array[indexUtt-1],"gesture":gestures_array[indexUtt-1],
                                        "sequence":sequence_array[indexUtt-1]})
                  }
                  break;
            }
        }
    });

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
