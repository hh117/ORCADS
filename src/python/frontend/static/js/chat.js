var textarea = $('#text');
var selectTime = null, messageStartTime = null;
var messageDuration = 0.0;

var socket = io.connect('http://' + document.domain + ':' + location.port);;

socket.on('connect', function(data){
  console.log("connected");
  socket.emit("restart");
  $('#chat').css('background-color','white');
});


function refreshTypingStatus() {
  if (new Date().getTime() - lastTypedTime.getTime() > typingDelayMillis) {
    $("#text").attr("placeholder", "Enter your message here");
    $("#text").removeAttr('disabled');
  }

}
socket.on('waiting', function(data) {
  if (data==true){
    window.location.href = window.location.origin;
  }
});

socket.on('message', function(data){
  displayText(data);
});

function displayText(data) {
  var message = data['msg'];
  console.log(message);
  if (data['role']=='operator'){
    $('#chat').append('<hgroup class="speech-bubble-right"><p class="text-left" style="font-size:14pt;padding-right: 10px;padding-left: 10px;">'+message+'</p></hgroup>');
  } else if (data['role']=="status"){
    $('#chat').append('<p style="font-size:12pt;">'+message+'</p>');
  } else {
    $('#chat').append('<hgroup class="speech-bubble-left"><p class="text-left" style="font-size:14pt;padding-right: 10px;padding-left: 10px;">'+message+'</p></hgroup>');
  };

  $('#chat').scrollTop($('#chat')[0].scrollHeight);
}
