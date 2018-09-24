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
