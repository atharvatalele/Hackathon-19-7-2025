let allUsers = [];

async function loadUsers() {
    const res = await fetch("http://localhost:8000/users");
    const users = await res.json();
    allUsers = users;
    displayUsers(users);
}

function displayUsers(users) {
    const list = document.getElementById("user-list");
    list.innerHTML = "";
    users.forEach(user => {
        const div = document.createElement("div");
        div.classList.add("user-block");

        const header = document.createElement("div");
        header.classList.add("user-header");
        header.innerHTML = `<strong>${user.name}</strong> (${user.gitname})`;
        header.onclick = () => div.classList.toggle("expanded");

        const body = document.createElement("div");
        body.classList.add("user-body");

        const active = document.createElement("div");
        active.innerHTML = `<h4>Active Tasks</h4>` + user.active_tasks.map(task => `
            <div class="task">
                <p><b>${task.title}</b></p>
                <p>${task.description}</p>
                <progress max="100" value="50"></progress> <!-- Placeholder -->
                <button onclick="completeTask('${task.id}')">✔️</button>
                <button onclick="confirmDelete('${task.id}')">❌</button>
            </div>
        `).join("");

        const history = document.createElement("div");
        history.innerHTML = `<h4>Completed Tasks</h4>` + user.completed_tasks.map(task => `
            <div class="task completed">
                <p><b>${task.title}</b> ✅</p>
                <p>${task.description}</p>
                <button title="Review task">❓</button>
            </div>
        `).join("");

        body.appendChild(active);
        body.appendChild(history);
        div.appendChild(header);
        div.appendChild(body);
        list.appendChild(div);
    });
}

function searchUsers() {
    const query = document.getElementById("search").value.toLowerCase();
    const filtered = allUsers.filter(u => u.name.toLowerCase().includes(query) || u.gitname.toLowerCase().includes(query));
    displayUsers(filtered);
}

async function completeTask(taskId) {
    await fetch(`http://localhost:8000/tasks/${taskId}/complete`, { method: "POST" });
    loadUsers();
}

async function confirmDelete(taskId) {
    if (confirm("Are you sure you want to delete this task?")) {
        await fetch(`http://localhost:8000/tasks/${taskId}`, { method: "DELETE" });
        loadUsers();
    }
}

loadUsers();
