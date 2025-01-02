const chatBox = document.getElementById("chat-box");
const chatInput = document.getElementById("chat-input");
const sendBtn = document.getElementById("send-btn");
const exitBtn = document.getElementById("exit-btn");

const nicknameModal = document.getElementById("nickname-modal");
const nicknameInput = document.getElementById("nickname-input");
const confirmBtn = document.getElementById("confirm-btn");

// 닉네임 및 WebSocket 상태
let userId;
let ws;

let reconnectAttempts = 0;
const maxReconnectAttempts = 5;

// 초기 모달 팝업 표시
window.onload = () => {
    nicknameModal.style.display = "block";
};

// 닉네임 입력 후 WebSocket 연결
confirmBtn.onclick = () => {
    userId = nicknameInput.value.trim();
    if (userId) {
        nicknameModal.style.display = "none";
        connectWebSocket();
    } else {
        alert("닉네임을 입력하세요.");
    }
};

// 엔터로 닉네임 입력 처리
nicknameInput.addEventListener("keypress", (event) => {
    if (event.key === "Enter") {
        confirmBtn.click();
    }
});

// WebSocket 연결 설정
function connectWebSocket() {
    // 기존 WebSocket이 열려 있다면 닫기
    if (ws && ws.readyState !== WebSocket.CLOSED) {
        ws.close();
    }

    ws = new WebSocket(`ws://${window.location.host}/ws`);
    setWebSocketHandlers();
}

// WebSocket 핸들러 등록
function setWebSocketHandlers() {
    ws.onopen = () => {
        console.log("WebSocket 연결 성공");
        reconnectAttempts = 0;  // 재연결 횟수 초기화
        ws.send(JSON.stringify({ sender: userId, message: "connect" }));
    };

    ws.onmessage = (event) => {
        const data = JSON.parse(event.data);
        const sender = data.sender === userId ? "user" : "other";
        appendMessage(data, sender);
    };

    ws.onclose = () => {
        if (userId && reconnectAttempts < maxReconnectAttempts) {
            reconnectAttempts++;
            console.log(`WebSocket 종료. ${reconnectAttempts}회 재연결 시도 중...`);
            setTimeout(connectWebSocket, 3000);
        } else {
            console.log("재연결 최대 횟수 초과. 연결 종료.");
        }
    };
}

// 메시지 전송 함수
function sendMessage() {
    const message = chatInput.value.trim();
    if (message) {
        if (ws.readyState === WebSocket.OPEN) {
            const data = { sender: userId, text: message };
            appendMessage(data, "user");
            ws.send(JSON.stringify(data));
            chatInput.value = "";
            chatInput.focus();
        } else {
            alert("서버와의 연결이 끊겼습니다. 재연결 중입니다.");
        }
    }
}

// 나가기 버튼 클릭 시 WebSocket 종료
exitBtn.onclick = () => {
    if (ws.readyState === WebSocket.OPEN) {
        ws.send(JSON.stringify({ sender: userId, message: "/exit" }));
    }
    setTimeout(() => {
        if (ws.readyState !== WebSocket.CLOSED) {
            ws.close();
        }
        alert("채팅을 종료했습니다.");
        window.location.reload();
    }, 200);
};

// 메시지 전송 버튼 클릭
sendBtn.onclick = sendMessage;

// 엔터로 메시지 전송
chatInput.addEventListener("keypress", (event) => {
    if (event.key === "Enter") {
        sendMessage();
    }
});

// 채팅 메시지를 DOM에 추가하는 함수
function appendMessage(message, sender = "other") {
    const msgWrapper = document.createElement("div");
    msgWrapper.classList.add("message");
    msgWrapper.classList.add(sender === "user" ? "user" : "other");

    // 다른 사용자의 경우 닉네임 추가
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
    chatBox.scrollTop = chatBox.scrollHeight;  // 최신 메시지로 스크롤 이동
}