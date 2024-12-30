const chatBox = document.getElementById("chat-box");
const chatInput = document.getElementById("chat-input");
const sendBtn = document.getElementById("send-btn");

// WebSocket 연결 설정
const ws = new WebSocket(`ws://${window.location.host}/ws`);

// 서버로부터 메시지를 수신했을 때
ws.onmessage = function(event) {
    const msg = event.data;
    const p = document.createElement("p");
    p.textContent = msg;
    chatBox.appendChild(p);
    chatBox.scrollTop = chatBox.scrollHeight;  // 최신 메시지로 스크롤
};

// 전송 버튼 클릭 이벤트
sendBtn.addEventListener("click", function() {
    sendMessage();
});

// 엔터키로 메시지 전송
chatInput.addEventListener("keypress", function(event) {
    if (event.key === "Enter") {
        sendMessage();
    }
});

// 메시지 전송 함수
function sendMessage() {
    const message = chatInput.value.trim();
    if (message) {
        ws.send(message);  // 서버에 메시지 전송
        chatInput.value = "";
    }
}
