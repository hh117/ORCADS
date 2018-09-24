var text_input =  $('#text');
var selectTime = null, messageStartTime = null;
var messageDuration = 0.0;

socket.on('typing', function(data){
  if(data['role'] != "{{role}}"){
    lastTypedTime = new Date();
    $("#text").attr("placeholder", );
    $("#text").attr("disabled", "disabled");
    $("#partner-typing").text(data["msg"]);
  }
});

$(document).ready(
  function(){
    $('#text').keypress(function(e) {
      socket.emit('keypress', {'key': e.key,'code':e.KeyCode|| e.which});
      var code = e.keyCode || e.which;
      if ($('#text').val().length == 0) {
        messageStartTime = Date.now() / 1000.0;
      }
      if (code == 13) {
        text = $('#text').val();
        $('#text').val('');
        var currentTime = Date.now() / 1000.0;
        messageDuration = currentTime - messageStartTime;
        socket.emit('text',
        {'msg': text,
        'init-time': messageStartTime,
        'end-time': currentTime,
        'duration': messageDuration});
        messageStartTime = null;
        messageDuration = 0.0;
      }
    });
  });
