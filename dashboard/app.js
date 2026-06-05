/* -------------------------------------------------------------
   DISCORD BOT WEB DASHBOARD - INTERACTIVE APPLICATION LOGIC
   Handles: API requests, dynamic forms, mock data, and UI state
   ------------------------------------------------------------- */

document.addEventListener("DOMContentLoaded", () => {
    // DOM Elements
    const navItems = document.querySelectorAll(".nav-item");
    const tabContents = document.querySelectorAll(".tab-content");
    const pageTitle = document.getElementById("page-title");
    const pageSubtitle = document.getElementById("page-subtitle");
    
    const apiHostInput = document.getElementById("api-host");
    const apiKeyInput = document.getElementById("api-key");
    const btnReconnect = document.getElementById("btn-reconnect");
    const apiStatusText = document.getElementById("api-status-text");
    const connectionProgress = document.getElementById("connection-progress");

    // Stats Elements
    const statServers = document.getElementById("stat-servers");
    const statUsers = document.getElementById("stat-users");
    const statPing = document.getElementById("stat-ping");
    const statVoice = document.getElementById("stat-voice");
    const cogsList = document.getElementById("cogs-list");
    const infoUsername = document.getElementById("info-username");
    const infoId = document.getElementById("info-id");

    // Forms
    const formAiConfig = document.getElementById("form-ai-config");
    const aiChannelSelect = document.getElementById("ai-channel-id");
    const aiSystemPrompt = document.getElementById("ai-system-prompt");
    const aiApiStatusBadge = document.getElementById("ai-api-status");

    const formReactionRoles = document.getElementById("form-reaction-roles");
    const rrGuildSelect = document.getElementById("rr-guild-id");
    const rrChannelSelect = document.getElementById("rr-channel-id");
    const rrRolesContainer = document.getElementById("rr-roles-container");
    const btnAddRoleItem = document.getElementById("btn-add-role-item");

    const formSystemConfig = document.getElementById("form-system-config");
    const sysPrefixInput = document.getElementById("sys-prefix");
    const sysApiPortInput = document.getElementById("sys-api-port");
    const sysJsonTextarea = document.getElementById("sys-json");

    // Alerts
    const alertContainer = document.getElementById("alert-container");

    // State
    let isMockMode = false;
    let serverData = {}; // Store retrieved roles and channels
    let globalConfig = {};

    // Load saved settings from LocalStorage
    if (localStorage.getItem("bot_api_host")) {
        apiHostInput.value = localStorage.getItem("bot_api_host");
    }
    if (localStorage.getItem("bot_api_key")) {
        apiKeyInput.value = localStorage.getItem("bot_api_key");
    }

    // Tab switcher titles
    const tabDetails = {
        overview: {
            title: "Tổng quan hệ thống",
            subtitle: "Giám sát hoạt động và thông số trực quan của Discord Bot."
        },
        "ai-config": {
            title: "Cấu hình AI Chatbot",
            subtitle: "Quản lý kênh đàm thoại và lời nhắc hệ thống dành cho Gemini."
        },
        "reaction-roles": {
            title: "Bảng Chọn Vai Trò (Reaction Roles)",
            subtitle: "Tạo bảng tin nhắn có nút bấm tự động cấp vai trò cho thành viên."
        },
        "system-config": {
            title: "Cấu hình Hệ thống",
            subtitle: "Thay đổi cài đặt tệp cấu hình toàn cục `config.json`."
        }
    };

    // Initialize Lucide Icons
    lucide.createIcons();

    // 1. Navigation Tab Handling
    navItems.forEach(item => {
        item.addEventListener("click", (e) => {
            e.preventDefault();
            const tabId = item.getAttribute("data-tab");

            // Update active state in sidebar nav
            navItems.forEach(nav => nav.classList.remove("active"));
            item.classList.add("active");

            // Show active section
            tabContents.forEach(content => {
                content.classList.remove("active");
                if (content.id === `tab-${tabId}`) {
                    content.classList.add("active");
                }
            });

            // Update titles
            if (tabDetails[tabId]) {
                pageTitle.textContent = tabDetails[tabId].title;
                pageSubtitle.textContent = tabDetails[tabId].subtitle;
            }
        });
    });

    // 2. Alert Toast Utility
    const showToast = (message, type = "success") => {
        const toast = document.createElement("div");
        toast.className = `toast ${type}`;
        
        const iconName = type === "success" ? "check-circle" : "alert-triangle";
        toast.innerHTML = `
            <i data-lucide="${iconName}"></i>
            <span>${message}</span>
        `;
        
        alertContainer.appendChild(toast);
        lucide.createIcons({attrs: {class: 'toast-icon'}});
        
        // Remove toast after 4 seconds
        setTimeout(() => {
            toast.style.animation = "slideIn 0.3s cubic-bezier(0.16, 1, 0.3, 1) reverse forwards";
            setTimeout(() => {
                toast.remove();
            }, 300);
        }, 4000);
    };

    // 3. API Request Wrapper
    const fetchFromAPI = async (action, payload = {}) => {
        const host = apiHostInput.value.trim().replace(/\/$/, "");
        const apiKey = apiKeyInput.value.trim();

        // Save to localstorage
        localStorage.setItem("bot_api_host", host);
        localStorage.setItem("bot_api_key", apiKey);

        try {
            const response = await fetch(`${host}/api`, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    "X-API-Key": apiKey
                },
                body: JSON.stringify({ action, payload })
            });

            if (!response.ok) {
                if (response.status === 401) {
                    throw new Error("Không có quyền truy cập (API Key không hợp lệ).");
                }
                if (response.status === 403) {
                    const errorData = await response.json();
                    throw new Error(errorData.error || "Bị từ chối quyền.");
                }
                throw new Error(`Lỗi kết nối Server (${response.status})`);
            }

            return await response.json();
        } catch (error) {
            console.error(`API Error on ${action}:`, error);
            throw error;
        }
    };

    // 4. Load & Synchronize Data
    const loadDashboardData = async () => {
        isMockMode = false;
        apiStatusText.textContent = "Đang kết nối...";
        apiStatusText.className = "status-indicator-text offline";
        connectionProgress.style.width = "30%";

        try {
            // Test connection with stats
            const statsRes = await fetchFromAPI("GET_DASHBOARD_STATS");
            connectionProgress.style.width = "60%";

            // If success, fill statistics
            statServers.textContent = statsRes.total_servers;
            statUsers.textContent = statsRes.total_users;
            statPing.textContent = `${statsRes.ping_ms} ms`;
            statVoice.textContent = statsRes.active_voice_channels;

            // Fill Cogs List
            cogsList.innerHTML = "";
            if (statsRes.loaded_cogs && statsRes.loaded_cogs.length > 0) {
                statsRes.loaded_cogs.forEach(cog => {
                    const badge = document.createElement("span");
                    badge.className = "badge";
                    badge.textContent = cog.replace("cogs.", "");
                    cogsList.appendChild(badge);
                });
            } else {
                cogsList.innerHTML = '<span class="badge badge-loading">Không có module nào</span>';
            }

            // Get Bot user info
            const statusRes = await fetchFromAPI("STATUS");
            infoUsername.textContent = statusRes.bot || "Discord Bot";
            
            // Get Config
            const configRes = await fetchFromAPI("GET_CONFIG");
            globalConfig = configRes.data || {};
            sysPrefixInput.value = globalConfig.prefix || "!";
            sysApiPortInput.value = globalConfig.api_port || "8080";
            sysJsonTextarea.value = JSON.stringify(globalConfig, null, 4);

            // Get AI Status
            const aiStatusRes = await fetchFromAPI("GET_AI_STATUS");
            aiSystemPrompt.value = aiStatusRes.ai_system_prompt || "";
            if (aiStatusRes.gemini_api_configured) {
                aiApiStatusBadge.innerHTML = '<span class="status-badge online"><span class="dot"></span> Đã cấu hình API Key</span>';
            } else {
                aiApiStatusBadge.innerHTML = '<span class="status-badge offline"><span class="dot"></span> Thiếu GEMINI_API_KEY trong .env</span>';
            }

            // Get Channels and Server details
            const serverRes = await fetchFromAPI("GET_SERVER_DATA");
            serverData = serverRes.data || {};
            
            // Load Channel Dropdowns
            populateDropdowns();

            // Set AI configured channel
            if (globalConfig.ai_channel_id) {
                aiChannelSelect.value = globalConfig.ai_channel_id;
            }

            // Update connection state UI
            apiStatusText.textContent = "Kết nối thành công";
            apiStatusText.className = "status-indicator-text online";
            connectionProgress.style.width = "100%";
            showToast("Đã đồng bộ hóa dữ liệu từ Discord Bot thành công!");

        } catch (error) {
            // Fallback to Mock Data (Demo Mode)
            isMockMode = true;
            connectionProgress.style.width = "100%";
            apiStatusText.textContent = "Chế độ Demo";
            apiStatusText.className = "status-indicator-text offline";
            
            showToast(error.message || "Không thể kết nối đến Bot API. Chuyển sang chế độ Demo.", "error");
            loadMockData();
        }
    };

    // Populate Channel and Server drop-downs
    const populateDropdowns = () => {
        // AI Channels Dropdown
        aiChannelSelect.innerHTML = '<option value="">-- Chọn kênh chat AI --</option>';
        
        // Reaction Roles Server Dropdown
        rrGuildSelect.innerHTML = '<option value="">-- Chọn Server --</option>';

        Object.keys(serverData).forEach(guildId => {
            const guild = serverData[guildId];
            
            // Add to Reaction roles Server selector
            const optGuild = document.createElement("option");
            optGuild.value = guildId;
            optGuild.textContent = guild.name;
            rrGuildSelect.appendChild(optGuild);

            // Add all text channels to AI channels
            if (guild.channels) {
                guild.channels.forEach(ch => {
                    const optCh = document.createElement("option");
                    optCh.value = ch.id;
                    optCh.textContent = `${guild.name} # ${ch.name}`;
                    aiChannelSelect.appendChild(optCh);
                });
            }
        });
    };

    // Load beautiful realistic mock data for presentation
    const loadMockData = () => {
        statServers.textContent = "3";
        statUsers.textContent = "1,420";
        statPing.textContent = "42 ms";
        statVoice.textContent = "5";

        cogsList.innerHTML = "";
        const mockCogs = ["music", "moderation", "economy", "utilities", "social", "welcome", "ai_chatbot"];
        mockCogs.forEach(cog => {
            const badge = document.createElement("span");
            badge.className = "badge";
            badge.textContent = cog;
            cogsList.appendChild(badge);
        });

        infoUsername.textContent = "CyberBot#9999";
        infoId.textContent = "987654321012345678";

        // Mock settings config
        globalConfig = {
            prefix: "!",
            api_port: 8080,
            api_secrets: ["changeme123"],
            welcome_channel_id: "111222333444555",
            ai_channel_id: "122333444555666",
            ai_system_prompt: "Bạn là một trợ lý ảo Discord thân thiện, hòa đồng, đại diện cho nhóm Công Nghệ Phần Mềm."
        };

        sysPrefixInput.value = globalConfig.prefix;
        sysApiPortInput.value = globalConfig.api_port;
        sysJsonTextarea.value = JSON.stringify(globalConfig, null, 4);
        aiSystemPrompt.value = globalConfig.ai_system_prompt;
        aiApiStatusBadge.innerHTML = '<span class="status-badge online"><span class="dot"></span> Đã cấu hình API Key (Demo)</span>';

        // Mock Server list
        serverData = {
            "111222333": {
                name: "CS - Công Nghệ Phần Mềm",
                roles: [
                    { id: "101", name: "Ban Cán Sự Class" },
                    { id: "102", name: "Thành viên nhóm" },
                    { id: "103", name: "Lớp Trưởng" }
                ],
                channels: [
                    { id: "122333444555666", name: "general-chat" },
                    { id: "202", name: "thảo-luận-nhóm" },
                    { id: "203", name: "bot-commands" }
                ]
            },
            "444555666": {
                name: "Gaming Server",
                roles: [
                    { id: "301", name: "Gamer" },
                    { id: "302", name: "Streamer" }
                ],
                channels: [
                    { id: "401", name: "public-chat" },
                    { id: "402", name: "voice-room-1" }
                ]
            }
        };

        populateDropdowns();
        aiChannelSelect.value = globalConfig.ai_channel_id;
    };

    // 5. Save System Config
    formSystemConfig.addEventListener("submit", async (e) => {
        e.preventDefault();
        
        let newConfig;
        try {
            newConfig = JSON.parse(sysJsonTextarea.value);
        } catch (error) {
            showToast("Cấu hình JSON không hợp lệ! Vui lòng kiểm tra lại cú pháp.", "error");
            return;
        }

        // Apply input overrides
        newConfig.prefix = sysPrefixInput.value;
        newConfig.api_port = parseInt(sysApiPortInput.value) || 8080;

        if (isMockMode) {
            globalConfig = newConfig;
            sysJsonTextarea.value = JSON.stringify(globalConfig, null, 4);
            showToast("Lưu cấu hình hệ thống thành công (Chế độ Demo)!");
            return;
        }

        try {
            const res = await fetchFromAPI("UPDATE_CONFIG", newConfig);
            if (res.ok) {
                showToast("Đã lưu và cập nhật cấu hình hệ thống config.json!");
                loadDashboardData();
            } else {
                showToast(res.error || "Gặp lỗi khi lưu cấu hình.", "error");
            }
        } catch (error) {
            showToast(error.message || "Không thể kết nối lưu cấu hình.", "error");
        }
    });

    // 6. Save AI Config
    formAiConfig.addEventListener("submit", async (e) => {
        e.preventDefault();

        const payload = {
            ai_channel_id: aiChannelSelect.value,
            ai_system_prompt: aiSystemPrompt.value.trim()
        };

        if (isMockMode) {
            globalConfig.ai_channel_id = payload.ai_channel_id;
            globalConfig.ai_system_prompt = payload.ai_system_prompt;
            showToast("Lưu cấu hình chatbot AI thành công (Chế độ Demo)!");
            return;
        }

        try {
            const res = await fetchFromAPI("SET_AI_CONFIG", payload);
            if (res.ok) {
                showToast("Cấu hình AI đã được cập nhật thành công!");
                loadDashboardData();
            } else {
                showToast(res.error || "Lỗi lưu cấu hình AI.", "error");
            }
        } catch (error) {
            showToast(error.message || "Lỗi kết nối API lưu cấu hình AI.", "error");
        }
    });

    // 7. Reaction Roles Builder Logic
    const addRoleRow = (roleName = "", roleDesc = "") => {
        const count = rrRolesContainer.children.length;
        if (count >= 5) {
            showToast("Bạn chỉ được thêm tối đa 5 vai trò vào một bảng chọn.", "error");
            return;
        }

        const row = document.createElement("div");
        row.className = "rr-role-item";
        row.innerHTML = `
            <input type="text" class="form-control rr-role-name" placeholder="Tên Role (vd: Gamer)" value="${roleName}" required>
            <input type="text" class="form-control rr-role-desc" placeholder="Mô tả ngắn (vd: Nhận thông báo chơi game)" value="${roleDesc}" required>
            <button type="button" class="btn btn-danger btn-icon-only btn-sm btn-delete-role-row">
                <i data-lucide="trash-2"></i>
            </button>
        `;
        rrRolesContainer.appendChild(row);
        lucide.createIcons({attrs: {class: 'delete-icon'}});

        // Add delete listener
        row.querySelector(".btn-delete-role-row").addEventListener("click", () => {
            row.remove();
        });
    };

    btnAddRoleItem.addEventListener("click", () => addRoleRow());

    // Auto load channels when Server is selected in Reaction Roles form
    rrGuildSelect.addEventListener("change", () => {
        const guildId = rrGuildSelect.value;
        rrChannelSelect.innerHTML = '<option value="">-- Chọn kênh chat --</option>';
        
        if (!guildId || !serverData[guildId]) return;

        const guild = serverData[guildId];
        
        // Populate channels
        if (guild.channels) {
            guild.channels.forEach(ch => {
                const opt = document.createElement("option");
                opt.value = ch.id;
                opt.textContent = `# ${ch.name}`;
                rrChannelSelect.appendChild(opt);
            });
        }
    });

    // Spawn Reaction Role Panel Submit
    formReactionRoles.addEventListener("submit", async (e) => {
        e.preventDefault();

        const guildId = rrGuildSelect.value;
        const channelId = rrChannelSelect.value;
        const title = document.getElementById("rr-title").value.trim();
        const desc = document.getElementById("rr-desc").value.trim();
        const footer = document.getElementById("rr-footer").value.trim();

        if (!guildId || !channelId) {
            showToast("Vui lòng chọn Server và Kênh gửi bảng chọn!", "error");
            return;
        }

        const roleRows = rrRolesContainer.querySelectorAll(".rr-role-item");
        if (roleRows.length === 0) {
            showToast("Vui lòng thêm ít nhất một vai trò!", "error");
            return;
        }

        const roles = [];
        roleRows.forEach(row => {
            roles.push({
                name: row.querySelector(".rr-role-name").value.trim(),
                desc: row.querySelector(".rr-role-desc").value.trim()
            });
        });

        const payload = {
            guild_id: guildId,
            channel_id: channelId,
            title,
            desc,
            footer,
            roles
        };

        if (isMockMode) {
            showToast(`Gửi bảng chọn Role thành công đến kênh ${channelId} (Chế độ Demo)!`);
            return;
        }

        try {
            const res = await fetchFromAPI("SPAWN_RR_PANEL", payload);
            if (res.ok) {
                showToast("Đã đưa bảng chọn Reaction Role vào hàng đợi gửi tin nhắn của Bot!");
            } else {
                showToast(res.error || "Gặp lỗi khi yêu cầu gửi bảng chọn.", "error");
            }
        } catch (error) {
            showToast(error.message || "Không thể kết nối đến Bot API.", "error");
        }
    });

    // Handle reconnect button
    btnReconnect.addEventListener("click", loadDashboardData);

    // Initialize Page
    loadDashboardData();

    // Add initial rows to Reaction Role builder
    addRoleRow("Ban Cán Sự Class", "Nhận thông báo đặc biệt và quản lý lớp học");
    addRoleRow("Thành viên nhóm", "Hợp tác làm dự án Công Nghệ Phần Mềm");
});
