$(document).ready(
	function() {
		var $content = $('#textarea');
		var $msg = $('#msg');
		var token;
		
		function get_token() {
			$.get('/chatroom/get_token', function(data){
				if (data) {
					token = data;
					openChannel();
				} else {
					$msg.prepend('<p>Sorry, this chat room has reached the capacity of anonymous users, you need <a href="/login">login</a> to join them.</p>');
				}
			});
		}
		get_token();

		function onOpen() {
			$.post('/chatroom/open/', {'token': token});
		}

		function onMessage(m) {
			if (location.pathname=='/chatroom/'){
				var message = $.parseJSON(m.data);
				message.msg = message.msg.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
				if (message.user === undefined) {
					$msg.prepend('<strong>' + message.msg+'</strong><br>' );
				} else {
					$msg.prepend('<strong>' + message.user+': </strong>' + message.msg +'<br>');
				}
			} else {
				alert('coucou');
			}
		}

		function openChannel() {
			var channel = new goog.appengine.Channel(token);
			var handler = {
			  'onopen': onOpen,
			  'onmessage': onMessage,
			  'onerror': function() {},
			  'onclose': function() {$msg.prepend('<p>Your session has expired, you can refresh this page to join the chat room again.</p>');} // you can reopen the channel here if token has expired
			};
			channel.open(handler);
		}

		function submit() {
			if (token) {
				$.ajax({
					url: '/chatroom/post_msg/',
					type: 'POST',
					data: {'token': token, 'content': $content.val()}
				});
				$content.val('').focus();
			}
		}

		$content.keypress(function(e) {
			if (e.shiftKey && e.keyCode == 13) {
				return true;
			} else if(e.keyCode == 13){
				submit();
				return false;
			}
		});
		$('#submit_msg').click(submit);

		$(window).bind('beforeunload', function() {
			if (token)
				$.post('/chatroom/del_token/', {'token': token}); // it will take a risk of hack attack, you can use AJAX pull for tracking client connections instead
		})
	}
);
	
function inputOnFocus() {
	$('#textarea').val('');
	$msg.prepend('on focus');
}
