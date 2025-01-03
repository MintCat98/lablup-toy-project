# Lablup Toy Project
A lightweight toy project for backend development training using Python and modern async frameworks.
<br>

## Project Overview
This project aims to provide hands-on experience in building and deploying a simple web application using asynchronous Python frameworks. The goal is to create a real-time multi-user chat app leveraging aiohttp and redis-py.
<br>

## Tech Stack
- **Backend**: Python 3.12, asyncio, aiohttp, redis-py
- **Frontend**: Basic HTML, CSS, JavaScript (ES6)
- **Database**: Redis 7
- **Containerization**: Docker
<br>

## Features
- Real-time multi-user chatroom
- Simple front-end integration
- Dockerized for deployment
<br>

## Setup & Run Instructions
1. **Clone the repository**:
   ```bash
   git clone https://github.com/your-repo/lablup-toy-project.git
   cd lablup-toy-project
   ```
<br>

2. **Run with Docker**
   ```bash
   # Mode: Single-process
   docker-compose up --build

   # Mode: Multi-process
   APP_MODE=multi-process APP_WORKERS=6 docker compose up --build
   ```
   *This will automatically build and start the application with all dependencies (Redis, Python, etc.).*
   *You can select a mode between single and multi-process mode.*
<br>

3. **Access the app**
   ```bash
   http://localhost:8080
   ```
   *Open your browser and go to the link (or the port specified in your Dockerfile).*
<br>

## Demo & How to Use
1. **Enter your nickname**
<div align="center">
    <img src="https://github.com/user-attachments/assets/1dcacc9d-ed5e-4959-8942-3711e0dc2ac0" width="400">
</div>
<br>

2. **Enjoy**
<div align="center">
    <img src="https://github.com/user-attachments/assets/92d2b560-ac4a-473d-b59b-49049d883898" width="400">
</div>