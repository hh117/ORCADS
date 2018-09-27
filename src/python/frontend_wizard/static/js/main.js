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
      //$('#chat').css('background-color','white')
      socket.emit("restart")
    });

    window.sendToWizard = function(final_transcript) {
        socket.emit("say", {"text": final_transcript,"source": 'typed',"state": current_state, "gesture": "", sequence: "False"})
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

    function updateRobotList(robot_names,robot_ids){
      env_key_array = ['A','S','D','F']
      var robot_name_env_array = robot_names.split("|")
      robot_id_env_array = robot_ids.split("|")
      $('.env').remove()
      $('#robots-in-env').css('background-color','white')
      for(var r=0; r < robot_name_env_array.length; r++){
        $('#list-rbtinenv').append('<li class="list-group-item env">' + robot_name_env_array[r] + '<span class="badge">' + env_key_array[r] + '</span></li>')
      }

    }

    socket.on('update_robot_list', function(data){
      updateRobotList(data["robot_name"],data["robot_id"])
    })

    function updateActiveRobotList(robot_names,robot_ids){
      active_key_array = ['Z','X','C','V']
      var robot_name_active_array = robot_names.split("|")
      robot_id_active_array = robot_ids.split("|")
      $('.activerobot').remove()
      $('#robots-in-use').css('background-color','white')
      for(var r=0; r < robot_name_active_array.length; r++){
        $('#list-rbtinuse').append('<li class="list-group-item activerobot">' + robot_name_active_array[r] + '<span class="badge">' + active_key_array[r] + '</span></li>')
      }

    }

    socket.on('activate_robot',function(data){
      updateActiveRobotList(data["robot_name"],data["robot_id"])
    })

    socket.on('message', function(data){
      console.log(data)
      displayText(data);
    });

    socket.on('img',function(data){
      console.log(data);
      displayImg(data);
    })

    function displayText(data) {
      var message = data['msg'];
      if (data['role']=='operator'){
        $('#chat').append('<hgroup class="speech-bubble-right"><p class="text-left" style="font-size:14pt;padding-right: 10px;padding-left: 10px;">'+message+'</p></hgroup>');
      } else if (data['role']=="status"){
        $('#chat').append('<p style="font-size:12pt;">'+message+'</p>');
      } else {
        $('#chat').append('<hgroup class="speech-bubble-left"><p class="text-left" style="font-size:14pt;padding-right: 10px;padding-left: 10px;">'+message+'</p></hgroup>');
      };

      $('#chat').scrollTop($('#chat')[0].scrollHeight);
      //$('#chat').animate({scrollTop: $('#chat').prop("scrollHeight")}, 500);

    }

    function displayImg(data) {
      var loc = window.location.pathname;
      var dir = loc.substring(0, loc.lastIndexOf('/'));
      console.log(dir,loc)
      var img_path = data['path'];
      if (data['role']=='operator'){
        $('#chat').append('<hgroup class="speech-bubble-right"><p style="padding-top:0.5em;padding-right:0.5em;padding-left:0.5em;"><img style="max-width: 15em" src='+img_path+'></p></hgroup>');
      } else if (data['role']=="status"){
        $('#chat').append('<p><img src='+img_path+'></p>');
      } else {
        $('#chat').append('<hgroup class="speech-bubble-left"><p style="padding-top:0.5em;padding-right:0.5em;padding-left:0.5em"><img style="max-width: 15em" src='+img_path+'></p></hgroup>');
      };

      $('#chat').scrollTop($('#chat')[0].scrollHeight);
      //$('#chat').animate({scrollTop: $('#chat').prop("scrollHeight")}, 500);

    }


    function reset() {
        $('.list-group').removeClass('dim');
    }

    var state = 0;
    var combo = [];
    var stop = false;
    $('html').on('keydown', function(event) {
        console.log(current_page)
        text = $('#text').val();
        if ( (current_page == 'flow-utt') && (text.length == 0) ){
          if (stop) return;
          if ($(event.target).attr('id') === 'name') return true;
          var keyPressed = event.key.toLowerCase();
          combo.push(keyPressed);
          console.log(combo.sort().join('-'))

          switch(combo.sort().join('-')) {
              case 'y':
                socket.emit("say", {"text": "yes", "state": current_state, "gesture": "", sequence: "False", source: "pre-def"})
                break;
              case 'u':
                socket.emit("say", {"text": "no", "state": current_state, "gesture": "", sequence: "False", source: "pre-def"})
                break;
              case 'i':
                socket.emit("say", {"text": "Maybe", "state": current_state, "gesture": "", sequence: "False", source: "pre-def"})
                break;
              case 'o':
                socket.emit("say", {"text": "Mm", "state": current_state, "gesture": "", sequence: "False", source: "pre-def"})
                break;
              case 'p':
                socket.emit("say", {"text": "Mhm", "state": current_state, "gesture": "", sequence: "False", source: "pre-def"})
                break;
              case 'å':
                socket.emit("say", {"text": "I'm not sure", "state": current_state, "gesture": "", sequence: "False", source: "pre-def"})
                break;
              case 'n':
                socket.emit('attend',{"text":"other"})
                break;
              case 'v':
                socket.emit('attend',{'text':'all'})
                break;
              case ' ':
                socket.emit("say", {"text": "repeat", "state": current_state, "gesture": "", sequence: "False", source: "repeat"})
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
                                      "sequence":sequence_array[indexUtt-1],source: "flow"})
                }
                break;
             case 'a':
             case 's':
             case 'd':
             case 'f':
                robot_index = env_key_array.indexOf(combo.sort().join('-').toUpperCase())
                socket.emit("activate_robot",{"robot_id":robot_id_env_array[robot_index]})
                console.log(robot_id_env_array[robot_index])
                break;
             case 'z':
             case 'x':
             case 'c':
             case 'v':
                 robot_index = active_key_array.indexOf(combo.sort().join('-').toUpperCase())
                 console.log(robot_id_active_array[robot_index])
                 socket.emit("deactivate_robot",{"robot_id":robot_id_active_array[robot_index]})
                 break;
            }
        } else if (current_page == 'typed-input' || text.length > 0) {
            var code = event.keyCode || event.which;
            if (code == 13){
              text = $('#text').val();
              $('#text').val('');
              sendToWizard(text);
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
