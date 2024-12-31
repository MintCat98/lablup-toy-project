const chatBox = document.getElementById("chat-box");
const chatInput = document.getElementById("chat-input");
const sendBtn = document.getElementById("send-btn");
const exitBtn = document.getElementById("exit-btn");

// 닉네임 입력 (빈 문자열 방지)
let userId;
do {
    userId = prompt("닉네임을 입력하세요:");
} while (!userId || userId.trim() === "");

// WebSocket 연결 함수
function connectWebSocket() {
    const ws = new WebSocket(`ws://${window.location.host}/ws`);

    // WebSocket 연결 성공
    ws.onopen = () => {
        console.log("WebSocket 연결 성공");
    };

    // 서버로부터 메시지 수신
    ws.onmessage = function(event) {
        const data = JSON.parse(event.data);
        const sender = data.sender === userId ? "user" : "other";
        appendMessage(data, sender);

        // 새 메시지 알림 (브라우저가 비활성화 상태일 때)
        if (document.hidden && sender !== "user") {
            new Notification("새로운 메시지", {
                body: `${data.sender}: ${data.text}`
            });
        }
    };

    // WebSocket 종료 시 재연결
    ws.onclose = () => {
        console.log("WebSocket 연결 종료. 3초 후 재연결 시도...");
        setTimeout(connectWebSocket, 3000);
    };

    // 나가기 버튼 클릭 이벤트
    exitBtn.onclick = () => {
        ws.send(JSON.stringify({ sender: userId, message: "exit" }));
        ws.close();
        alert("채팅을 종료했습니다.");
        window.location.reload();
    };

    // 메시지 전송 버튼 클릭 이벤트
    sendBtn.onclick = sendMessage;

    // 엔터키로 메시지 전송
    chatInput.addEventListener("keypress", (event) => {
        if (event.key === "Enter") {
            sendMessage();
        }
    });

    // 메시지 전송 함수
    function sendMessage() {
        const message = chatInput.value.trim();
        if (message) {
            const data = { sender: userId, text: message };
            appendMessage(data, "user");
            ws.send(JSON.stringify(data));
            chatInput.value = "";
            chatInput.focus();
        }
    }
}

// 메시지를 채팅 박스에 추가하는 함수
function appendMessage(message, sender = "other") {
    const msgWrapper = document.createElement("div");
    msgWrapper.classList.add("message");
    msgWrapper.classList.add(sender === "user" ? "user" : "other");

    // 다른 사용자의 경우 닉네임을 추가
    if (sender !== "user") {
        const nickname = document.createElement("span");
        nickname.textContent = message.sender;
        nickname.classList.add("nickname", message.sender.toLowerCase());
        msgWrapper.appendChild(nickname);
    }

    const msg = document.createElement("div");
    msg.textContent = message.text;

    msgWrapper.appendChild(msg);
    chatBox.appendChild(msgWrapper);
    chatBox.scrollTop = chatBox.scrollHeight;  // 스크롤 최신 메시지로 이동
}

// 최초 WebSocket 연결
connectWebSocket();

// 페이지 로드 시 알림 권한 요청
if (Notification.permission !== "granted") {
    Notification.requestPermission();
}