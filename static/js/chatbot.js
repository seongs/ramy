$(document).ready(function() {
    $('#ButtonSend').click(function() {
        var userMessage = $('.ChatInput').val();
        var chatContainer = $('.chat-container');

        if (userMessage.trim() !== '') {
            // 사용자 메시지를 오른쪽에 추가
            var userMessageDiv = $('<div></div>').addClass('message-given').text(userMessage);
            chatContainer.append(userMessageDiv);
            updateScroll(chatContainer); // 스크롤 업데이트

            // 입력 필드를 비웁니다.
            $('.ChatInput').val('');

            $.ajax({
                url: '/submit',
                type: 'POST',
                contentType: 'application/json',
                data: JSON.stringify({ message: userMessage }),
                success: function(data) {
                    // 서버 응답 메시지를 왼쪽에 추가
                    var serverMessageDiv = $('<div></div>').addClass('message-received').text(data.response);
                    chatContainer.append(serverMessageDiv);
                },
                error: function(error) {
                    console.error('Error:', error);
                }
            });
        }
    });
});
function updateScroll(chatContainer) {
    chatContainer.scrollTop(chatContainer.prop("scrollHeight"));
}