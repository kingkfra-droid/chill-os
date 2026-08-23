
async function api(path) {

    const response = await fetch(path);

    if (!response.ok) {
        throw new Error(
            "API error " + response.status
        );
    }

    return response.json();
}


function hideScreens() {

    document
        .querySelectorAll(".screen")
        .forEach(
            el => el.classList.add("hidden")
        );

    document
        .getElementById("homeScreen")
        .classList.add("hidden");
}


function showHome() {

    hideScreens();

    document
        .getElementById("homeScreen")
        .classList.remove("hidden");

    closeTools();
}


function openSniffer() {

    hideScreens();

    document
        .getElementById("snifferScreen")
        .classList.remove("hidden");

    closeTools();

    refreshSniffer();
}


function showHardware() {

    hideScreens();

    document
        .getElementById("hardwareScreen")
        .classList.remove("hidden");

    closeTools();

    loadHardware();
}


function showCapabilities() {

    hideScreens();

    document
        .getElementById("capabilityScreen")
        .classList.remove("hidden");

    closeTools();

    loadFullCapabilities();
}


function toggleTools() {

    document
        .getElementById("toolMenu")
        .classList.toggle("open");
}


function closeTools() {

    document
        .getElementById("toolMenu")
        .classList.remove("open");
}


function openTerminal() {

    alert(
        "Integrated ChillOS terminal is next."
    );
}


async function loadSystem() {

    const data =
        await api("/api/system");

    document.getElementById("device")
        .textContent =
        data.manufacturer +
        " " +
        data.device +
        " • " +
        data.architecture;

    document.getElementById("archStatus")
        .textContent =
        data.abi;

    document.getElementById("prootStatus")
        .textContent =
        data.proot ? "READY" : "OFF";
}


async function loadProfile() {

    const data =
        await api(
            "/api/profile/recommended"
        );

    document.getElementById(
        "profile"
    ).textContent =
        "PROFILE: " +
        data.profile.toUpperCase() +
        " • " +
        data.reason;
}


function capabilityCard(
    name,
    item
) {

    const div =
        document.createElement("div");

    div.className =
        "capability " +
        item.state;

    div.innerHTML =
        "<strong>" +
        name.toUpperCase() +
        " — " +
        item.state.toUpperCase() +
        "</strong>" +
        "<small>" +
        item.reason +
        "</small>";

    return div;
}


async function loadCapabilities() {

    const data =
        await api("/api/capabilities");

    const box =
        document.getElementById(
            "capabilities"
        );

    box.innerHTML = "";

    Object.entries(data).forEach(
        ([name, item]) => {

            box.appendChild(
                capabilityCard(
                    name,
                    item
                )
            );

            if (name === "network") {

                document.getElementById(
                    "networkStatus"
                ).textContent =
                    item.state.toUpperCase();
            }

            if (name === "root") {

                document.getElementById(
                    "rootStatus"
                ).textContent =
                    item.state.toUpperCase();
            }
        }
    );
}


async function loadFullCapabilities() {

    const data =
        await api("/api/capabilities");

    const box =
        document.getElementById(
            "capabilitiesFull"
        );

    box.innerHTML = "";

    Object.entries(data).forEach(
        ([name, item]) => {

            box.appendChild(
                capabilityCard(
                    name,
                    item
                )
            );
        }
    );
}


async function loadHardware() {

    const data =
        await api("/api/hardware");

    const box =
        document.getElementById(
            "hardware"
        );

    box.innerHTML = "";

    Object.entries(data).forEach(
        ([name, value]) => {

            if (Array.isArray(value)) {
                value =
                    value.length
                    ? value.join(", ")
                    : "None detected";
            }

            box.appendChild(
                card(
                    name,
                    String(value)
                )
            );
        }
    );
}


function card(name, value) {

    const div =
        document.createElement("div");

    div.className =
        "capability";

    div.innerHTML =
        "<strong>" +
        name.toUpperCase() +
        "</strong>" +
        "<small>" +
        value +
        "</small>";

    return div;
}


/* -------------------------
   SNIFFER
------------------------- */

async function refreshSniffer() {

    const output =
        document.getElementById(
            "snifferOutput"
        );

    output.textContent =
        "Scanning ChillOS network visibility...";

    try {

        const data =
            await api("/api/hardware");

        renderInterfaces(data);

        renderNetworkInfo(data);

        document.getElementById(
            "snifferSummary"
        ).textContent =
            data.network
            ? "Network subsystem visible."
            : "Network subsystem unavailable.";

        document.getElementById(
            "snifferState"
        ).textContent =
            data.network ? "●" : "○";

        output.textContent =
            "Scan complete.";

    } catch (error) {

        output.textContent =
            "Sniffer error: " +
            error.message;
    }
}


function renderInterfaces(data) {

    const box =
        document.getElementById(
            "interfaces"
        );

    box.innerHTML = "";

    const interfaces =
        data.interfaces || [];

    if (!interfaces.length) {

        box.innerHTML =
            '<div class="sniffer-item">' +
            '<strong>NO INTERFACES</strong>' +
            '<small>' +
            'No interfaces exposed to ChillOS.' +
            '</small>' +
            '</div>';

        return;
    }

    interfaces.forEach(
        name => {

            const div =
                document.createElement(
                    "div"
                );

            div.className =
                "sniffer-item";

            div.innerHTML =
                "<strong>" +
                name +
                "</strong>" +
                "<small>" +
                "Visible network interface" +
                "</small>";

            box.appendChild(div);
        }
    );
}


function renderNetworkInfo(data) {

    const box =
        document.getElementById(
            "networkInfo"
        );

    box.innerHTML = "";

    const fields = [
        ["Network", data.network],
        ["USB visibility", data.usb],
        ["Input visibility", data.input]
    ];

    fields.forEach(
        ([name, value]) => {

            const div =
                document.createElement(
                    "div"
                );

            div.className =
                "sniffer-item";

            div.innerHTML =
                "<strong>" +
                name +
                "</strong>" +
                "<small>" +
                (value ? "AVAILABLE" : "UNAVAILABLE") +
                "</small>";

            box.appendChild(div);
        }
    );
}


async function runConnectivity() {

    const output =
        document.getElementById(
            "snifferOutput"
        );

    output.textContent =
        "Connectivity diagnostic requested...\n\n" +
        "This panel currently reports visibility only.\n" +
        "Active packet capture will be added as a separate module.";
}


async function boot() {

    try {

        const ready =
            await checkFirstRun();

        if (!ready) {
            return;
        }

        await loadSystem();
        await loadCapabilities();
        await loadProfile();

    } catch (error) {

        console.error(
            "ChillOS boot error:",
            error
        );
    }
}


boot();



let terminalHistory = [];
let terminalHistoryIndex = -1;
let terminalBusy = false;


async function openTerminal() {

    hideScreens();

    document
        .getElementById("terminalScreen")
        .classList.remove("hidden");

    closeTools();

    await startTerminal();

    const input =
        document.getElementById(
            "terminalCommand"
        );

    if (input) {
        setTimeout(
            () => input.focus(),
            100
        );
    }
}


async function startTerminal() {

    const status =
        document.getElementById(
            "terminalStatus"
        );

    try {

        const data =
            await api(
                "/api/terminal/start"
            );

        status.textContent =
            data.running
            ? "Debian • PRoot • ONLINE"
            : "Session unavailable";

    } catch (error) {

        status.textContent =
            "Terminal unavailable";
    }
}


function appendTerminal(
    text,
    className = ""
) {

    const output =
        document.getElementById(
            "terminalOutput"
        );

    const line =
        document.createElement("div");

    if (className) {
        line.className = className;
    }

    line.textContent = text;

    output.appendChild(line);

    output.scrollTop =
        output.scrollHeight;
}


async function sendTerminalCommand() {

    if (terminalBusy) {
        return;
    }

    const input =
        document.getElementById(
            "terminalCommand"
        );

    const command =
        input.value.trim();

    if (!command) {
        return;
    }

    terminalHistory.push(command);

    terminalHistoryIndex =
        terminalHistory.length;

    updateHistoryIndicator();

    input.value = "";

    appendTerminal(
        "$ " + command,
        "terminal-command"
    );

    terminalBusy = true;

    try {

        const result =
            await fetch(
                "/api/terminal/command",
                {
                    method: "POST",

                    headers: {
                        "Content-Type":
                            "application/json"
                    },

                    body: JSON.stringify({
                        command: command
                    })
                }
            );

        const data =
            await result.json();

        if (data.output) {

            appendTerminal(
                data.output,
                "terminal-result"
            );
        }

        if (data.error) {

            appendTerminal(
                data.error,
                "terminal-error"
            );
        }

    } catch (error) {

        appendTerminal(
            "Connection error: " +
            error.message,
            "terminal-error"
        );

    } finally {

        terminalBusy = false;

        input.focus();
    }
}


function updateHistoryIndicator() {

    const indicator =
        document.getElementById(
            "historyIndicator"
        );

    if (!indicator) {
        return;
    }

    indicator.textContent =
        "HISTORY: " +
        terminalHistory.length;
}


function historyUp() {

    if (!terminalHistory.length) {
        return;
    }

    if (
        terminalHistoryIndex >
        0
    ) {
        terminalHistoryIndex--;
    }

    const input =
        document.getElementById(
            "terminalCommand"
        );

    input.value =
        terminalHistory[
            terminalHistoryIndex
        ];

    input.setSelectionRange(
        input.value.length,
        input.value.length
    );
}


function historyDown() {

    if (!terminalHistory.length) {
        return;
    }

    if (
        terminalHistoryIndex <
        terminalHistory.length - 1
    ) {

        terminalHistoryIndex++;

        const input =
            document.getElementById(
                "terminalCommand"
            );

        input.value =
            terminalHistory[
                terminalHistoryIndex
            ];

    } else {

        terminalHistoryIndex =
            terminalHistory.length;

        document
            .getElementById(
                "terminalCommand"
            )
            .value = "";
    }
}


function terminalInsert(value) {

    const input =
        document.getElementById(
            "terminalCommand"
        );

    if (!input) {
        return;
    }

    if (value === "TAB") {

        input.value += "\t";

    } else if (value === "CTRL+C") {

        /*
         * UI shortcut for now.
         * Backend signal handling can be
         * added as a separate terminal feature.
         */

        appendTerminal(
            "^C",
            "terminal-error"
        );

    } else if (value === "↑") {

        historyUp();

    } else if (value === "↓") {

        historyDown();

    } else {

        input.value += value;
    }

    input.focus();
}


function toggleTerminalFullscreen() {

    document.body.classList.toggle(
        "terminal-fullscreen"
    );

    const button =
        document.getElementById(
            "fullscreenButton"
        );

    if (
        document.body.classList.contains(
            "terminal-fullscreen"
        )
    ) {

        button.textContent = "×";

    } else {

        button.textContent = "⛶";
    }
}


document.addEventListener(
    "keydown",
    function(event) {

        const screen =
            document.getElementById(
                "terminalScreen"
            );

        if (
            !screen ||
            screen.classList.contains(
                "hidden"
            )
        ) {
            return;
        }

        const input =
            document.getElementById(
                "terminalCommand"
            );

        if (
            document.activeElement !== input
        ) {
            return;
        }

        if (event.key === "ArrowUp") {

            event.preventDefault();

            historyUp();

        } else if (
            event.key === "ArrowDown"
        ) {

            event.preventDefault();

            historyDown();

        } else if (
            event.key === "Enter"
        ) {

            event.preventDefault();

            sendTerminalCommand();
        }
    }
);





/* =========================
   CHILLOS PACKAGE MANAGER
   ========================= */

let toolSearchTimer = null;


async function openToolsManager() {

    hideScreens();

    const screen =
        document.getElementById("toolsScreen");

    if (!screen) {
        console.error("toolsScreen not found");
        return;
    }

    screen.classList.remove("hidden");

    closeTools();

    await loadToolCategories();
}


async function loadToolCategories() {

    const box =
        document.getElementById("toolCategories");

    if (!box) {
        return;
    }

    box.innerHTML =
        '<div class="tool-loading">Loading Linux tools...</div>';

    try {

        const data =
            await api("/api/tools/categories");

        box.innerHTML = "";

        const list =
            Array.isArray(data)
                ? data
                : data.categories || [];

        if (!list.length) {

            box.innerHTML =
                '<div class="tool-loading">' +
                'No tool categories available.' +
                '</div>';

            return;
        }

        list.forEach(name => {

            const button =
                document.createElement("button");

            button.className =
                "tool-category";

            button.textContent =
                String(name).toUpperCase();

            button.onclick =
                () => loadToolCategory(name);

            box.appendChild(button);
        });

    } catch (error) {

        box.innerHTML =
            '<div class="tool-error">' +
            escapeToolHTML(error.message) +
            '</div>';
    }
}


let currentToolCategory = "";

async function loadToolCategory(name) {

    currentToolCategory = name;


    const box =
        document.getElementById("toolResults");

    if (!box) {
        return;
    }

    box.innerHTML =
        '<div class="tool-loading">Loading...</div>';

    try {

        const data =
            await api(
                "/api/tools/category/" +
                encodeURIComponent(name)
            );

        const tools =
            data.tools || [];

        renderToolResults(tools);

    } catch (error) {

        box.innerHTML =
            '<div class="tool-error">' +
            escapeToolHTML(error.message) +
            '</div>';
    }
}


function searchTools() {

    const input =
        document.getElementById(
            "toolSearch"
        );

    if (!input) {
        return;
    }

    clearTimeout(toolSearchTimer);

    const query =
        input.value.trim();

    if (!query) {

        const box =
            document.getElementById(
                "toolResults"
            );

        if (box) {
            box.innerHTML = "";
        }

        return;
    }

    toolSearchTimer =
        setTimeout(
            () => performToolSearch(query),
            300
        );
}


async function performToolSearch(query) {

    const box =
        document.getElementById(
            "toolResults"
        );

    if (!box) {
        return;
    }

    box.innerHTML =
        '<div class="tool-loading">' +
        'Searching Debian packages...' +
        '</div>';

    try {

        const data =
            await api(
                "/api/tools/search?q=" +
                encodeURIComponent(query)
            );

        const tools =
            Array.isArray(data)
                ? data
                : data.tools || data.results || [];

        renderToolResults(tools);

    } catch (error) {

        box.innerHTML =
            '<div class="tool-error">' +
            escapeToolHTML(error.message) +
            '</div>';
    }
}


function renderToolResults(tools) {

    const box =
        document.getElementById("toolResults");

    if (!box) {
        return;
    }

    box.innerHTML = "";

    if (!tools || !tools.length) {

        box.innerHTML =
            '<div class="tool-loading">' +
            'No tools found.' +
            '</div>';

        return;
    }

    tools.forEach(tool => {

        const packageName =
            tool.package || tool.name || "Unknown";

        const card =
            document.createElement("div");

        card.className =
            "linux-tool-card";

        card.onclick =
            () => openToolDetails(tool);

        const info =
            document.createElement("div");

        info.className =
            "linux-tool-info";

        const title =
            document.createElement("strong");

        title.textContent =
            packageName;

        const description =
            document.createElement("small");

        description.textContent =
            tool.description ||
            "Debian Linux package.";

        const state =
            document.createElement("small");

        state.className =
            tool.installed
                ? "tool-installed"
                : "tool-not-installed";

        state.textContent =
            tool.installed
                ? "● INSTALLED"
                : "○ NOT INSTALLED";

        info.appendChild(title);
        info.appendChild(description);
        info.appendChild(state);

        const button =
            document.createElement("button");

        button.className =
            "tool-get";

        button.textContent =
            tool.installed
                ? "REMOVE"
                : "GET";

        button.onclick =
            async event => {

                event.stopPropagation();

                await toggleTool(
                    tool,
                    button
                );
            };

        card.appendChild(info);
        card.appendChild(button);

        box.appendChild(card);
    });
}

async function toggleTool(tool, button) {

    const packageName =
        tool.package || tool.name;

    if (!packageName) {
        return;
    }

    const action =
        tool.installed
            ? "remove"
            : "install";

    button.disabled = true;
    button.textContent = "...";

    try {

        const endpoint =
            "/api/tools/" +
            action +
            "?package=" +
            encodeURIComponent(packageName);

        const response =
            await fetch(endpoint);

        const data =
            await response.json();

        if (!response.ok) {

            throw new Error(
                data.error ||
                "Operation failed"
            );
        }

        /*
         * Reload the current category so the
         * installed state is immediately updated.
         */

        if (typeof currentToolCategory !== "undefined"
            && currentToolCategory) {

            await loadToolCategory(
                currentToolCategory
            );

        } else {

            button.textContent =
                action === "install"
                    ? "GET"
                    : "REMOVE";

            button.disabled = false;
        }

    } catch (error) {

        button.disabled = false;

        button.textContent =
            tool.installed
                ? "REMOVE"
                : "GET";

        alert(
            "ChillOS: " +
            error.message
        );
    }
}

async function installLinuxTool(
    packageName,
    button
) {

    if (!packageName) {
        return;
    }

    button.disabled = true;
    button.textContent = "...";

    const output =
        document.getElementById(
            "toolOutput"
        );

    if (output) {

        output.textContent =
            "Installing " +
            packageName +
            " through Debian APT...";
    }

    try {

        const data =
            await api(
                "/api/tools/install?package=" +
                encodeURIComponent(packageName)
            );

        if (output) {

            output.textContent =
                data.message ||
                data.output ||
                "Installation request completed.";
        }

        button.textContent = "DONE";

    } catch (error) {

        if (output) {

            output.textContent =
                "Installation failed: " +
                error.message;
        }

        button.textContent = "RETRY";

        button.disabled = false;
    }
}


async function updateLinuxTools() {

    const output =
        document.getElementById(
            "toolOutput"
        );

    if (output) {
        output.textContent =
            "Updating Debian package metadata...";
    }

    try {

        const data =
            await api(
                "/api/tools/update"
            );

        if (output) {

            output.textContent =
                data.message ||
                data.output ||
                "Package metadata updated.";
        }

    } catch (error) {

        if (output) {

            output.textContent =
                "Update failed: " +
                error.message;
        }
    }
}


async function removeLinuxTool(packageName) {

    if (!packageName) {
        return;
    }

    if (
        !confirm(
            "Remove " +
            packageName +
            " from ChillOS?"
        )
    ) {
        return;
    }

    try {

        await api(
            "/api/tools/remove?package=" +
            encodeURIComponent(packageName)
        );

        performToolSearch(packageName);

    } catch (error) {

        const output =
            document.getElementById(
                "toolOutput"
            );

        if (output) {

            output.textContent =
                "Remove failed: " +
                error.message;
        }
    }
}


function escapeToolHTML(value) {

    return String(value || "")
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}


function toolSearchKey(event) {

    if (event.key === "Enter") {

        const input =
            document.getElementById(
                "toolSearch"
            );

        if (input) {
            performToolSearch(
                input.value.trim()
            );
        }
    }
}


/* Rebind boot safely */

document.addEventListener(
    "DOMContentLoaded",
    () => {

        const search =
            document.getElementById(
                "toolSearch"
            );

        if (search) {

            search.addEventListener(
                "input",
                searchTools
            );

            search.addEventListener(
                "keydown",
                toolSearchKey
            );
        }
    }
);


/* =========================
   TOOL DETAILS
========================= */

let selectedTool = null;


function openToolDetails(tool) {

    selectedTool = tool;

    hideScreens();

    const screen =
        document.getElementById(
            "toolDetailsScreen"
        );

    if (!screen) {
        return;
    }

    screen.classList.remove("hidden");

    document.getElementById(
        "toolDetailsName"
    ).textContent =
        String(tool.package || "TOOL").toUpperCase();

    document.getElementById(
        "toolDetailsPackage"
    ).textContent =
        tool.package || "";

    document.getElementById(
        "toolDetailsDescription"
    ).textContent =
        tool.description ||
        "No description available.";

    updateToolDetailsState();

}


function updateToolDetailsState() {

    if (!selectedTool) {
        return;
    }

    const installed =
        Boolean(selectedTool.installed);

    const badge =
        document.getElementById(
            "toolDetailsBadge"
        );

    const status =
        document.getElementById(
            "toolDetailsStatus"
        );

    const getButton =
        document.getElementById(
            "toolDetailsGet"
        );

    const removeButton =
        document.getElementById(
            "toolDetailsRemove"
        );

    badge.textContent =
        installed
            ? "INSTALLED"
            : "NOT INSTALLED";

    status.textContent =
        installed
            ? "READY"
            : "AVAILABLE";

    getButton.disabled =
        installed;

    removeButton.disabled =
        !installed;

}


async function getSelectedTool() {

    if (!selectedTool) {
        return;
    }

    const output =
        document.getElementById(
            "toolDetailsOutput"
        );

    output.textContent =
        "Installing " +
        selectedTool.package +
        "...";

    try {

        const result =
            await api(
                "/api/tools/install?package=" +
                encodeURIComponent(
                    selectedTool.package
                )
            );

        output.textContent =
            JSON.stringify(
                result,
                null,
                2
            );

        selectedTool.installed = true;

        updateToolDetailsState();

    } catch (error) {

        output.textContent =
            "GET failed: " +
            error.message;

    }

}


async function removeSelectedTool() {

    if (!selectedTool) {
        return;
    }

    const output =
        document.getElementById(
            "toolDetailsOutput"
        );

    output.textContent =
        "Removing " +
        selectedTool.package +
        "...";

    try {

        const result =
            await api(
                "/api/tools/remove?package=" +
                encodeURIComponent(
                    selectedTool.package
                )
            );

        output.textContent =
            JSON.stringify(
                result,
                null,
                2
            );

        selectedTool.installed = false;

        updateToolDetailsState();

    } catch (error) {

        output.textContent =
            "REMOVE failed: " +
            error.message;

    }

}



/* =================================
   FIRST-RUN SETUP
================================= */

let chillSetupReady = false;


async function checkSetup() {

    const title =
        document.getElementById(
            "setupTitle"
        );

    const message =
        document.getElementById(
            "setupMessage"
        );

    const indicator =
        document.getElementById(
            "setupIndicator"
        );

    title.textContent =
        "Checking environment";

    message.textContent =
        "Detecting PRoot-Distro and Debian...";

    indicator.textContent =
        "◌";

    try {

        const data =
            await api(
                "/api/setup/status"
            );

        updateSetupCheck(
            "prootCheck",
            "prootCheckText",
            data.proot_distro,
            "Available",
            "Not installed"
        );

        updateSetupCheck(
            "debianCheck",
            "debianCheckText",
            data.debian,
            "Installed",
            "Not installed"
        );


        chillSetupReady =
            Boolean(data.ready);


        const commands =
            document.getElementById(
                "setupCommands"
            );

        const continueButton =
            document.getElementById(
                "setupContinue"
            );

        const action =
            document.getElementById(
                "setupAction"
            );


        if (data.ready) {

            indicator.textContent =
                "✓";

            title.textContent =
                "ChillOS is ready";

            message.textContent =
                "PRoot-Distro and Debian are available.";

            commands.classList.add(
                "hidden"
            );

            action.classList.add(
                "hidden"
            );

            continueButton.classList.remove(
                "hidden"
            );

        } else {

            indicator.textContent =
                "!";

            title.textContent =
                "Setup required";

            message.textContent =
                "Complete the Termux setup below.";

            commands.classList.remove(
                "hidden"
            );

            action.classList.remove(
                "hidden"
            );

            continueButton.classList.add(
                "hidden"
            );
        }

    } catch (error) {

        indicator.textContent =
            "!";

        title.textContent =
            "Setup check failed";

        message.textContent =
            error.message;
    }
}


function updateSetupCheck(
    iconId,
    textId,
    enabled,
    goodText,
    badText
) {

    const icon =
        document.getElementById(iconId);

    const text =
        document.getElementById(textId);

    icon.textContent =
        enabled ? "✓" : "○";

    text.textContent =
        enabled
            ? goodText
            : badText;

    icon.className =
        enabled
            ? "setup-good"
            : "setup-bad";
}


function showSetup() {

    hideScreens();

    const screen =
        document.getElementById(
            "setupScreen"
        );

    if (!screen) {
        return;
    }

    screen.classList.remove(
        "hidden"
    );

    closeTools();

    checkSetup();
}


function finishSetup() {

    if (!chillSetupReady) {
        return;
    }

    showHome();
}


async function checkFirstRun() {

    try {

        const data =
            await api(
                "/api/setup/status"
            );

        if (!data.ready) {

            showSetup();

            return false;
        }

        if (!data.completed) {

            showSetup();

            return false;
        }

    } catch (error) {

        console.error(
            "First-run check:",
            error
        );

        showSetup();

        return false;
    }

    return true;
}



/* =================================
   SETUP COMPLETION
================================= */

async function completeChillOSSetup() {

    const output =
        document.getElementById(
            "setupMessage"
        );

    try {

        const data =
            await api(
                "/api/setup/complete"
            );

        if (!data.success) {

            output.textContent =
                data.error ||
                "Unable to complete setup.";

            return false;
        }

        chillSetupReady = true;

        return true;

    } catch (error) {

        output.textContent =
            "Setup completion failed: " +
            error.message;

        return false;
    }
}


async function finishSetup() {

    const success =
        await completeChillOSSetup();

    if (!success) {
        return;
    }

    showHome();

    await loadSystem();
    await loadCapabilities();
    await loadProfile();
}



async function repairEnvironment() {

    const message =
        document.getElementById(
            "setupMessage"
        );

    const output =
        document.getElementById(
            "setupCommands"
        );

    message.textContent =
        "Run the setup commands in Termux, then check again.";

    output.classList.remove(
        "hidden"
    );

    await checkSetup();
}


/* ==========================================
   SNIFFER 2.0 — LIVE TELEMETRY DASHBOARD
========================================== */

let snifferTimer = null;
let snifferBusy = false;


function snifferEscape(value) {

    const div = document.createElement("div");

    div.textContent =
        value === null ||
        value === undefined
            ? "—"
            : String(value);

    return div.innerHTML;
}


function snifferValue(value) {

    if (value === true) {
        return "AVAILABLE";
    }

    if (value === false) {
        return "UNAVAILABLE";
    }

    if (
        value === null ||
        value === undefined ||
        value === ""
    ) {
        return "—";
    }

    return String(value);
}


function snifferCard(title, value, extra = "") {

    const div =
        document.createElement("div");

    div.className =
        "sniffer-data-card";

    div.innerHTML = `
        <div class="sniffer-card-title">
            ${snifferEscape(title)}
        </div>

        <div class="sniffer-card-value">
            ${snifferEscape(snifferValue(value))}
        </div>

        ${
            extra
                ? `<small>${snifferEscape(extra)}</small>`
                : ""
        }
    `;

    return div;
}


function snifferSection(title, subtitle = "") {

    const section =
        document.createElement("section");

    section.className =
        "sniffer-section";

    section.innerHTML = `
        <div class="sniffer-section-header">
            <strong>${snifferEscape(title)}</strong>
            ${
                subtitle
                    ? `<small>${snifferEscape(subtitle)}</small>`
                    : ""
            }
        </div>
    `;

    return section;
}


function renderSnifferInterfaces(data) {

    const box =
        document.getElementById(
            "interfaces"
        );

    if (!box) {
        return;
    }

    box.innerHTML = "";

    const list =
        data.interfaces || [];

    if (!list.length) {

        box.innerHTML = `
            <div class="sniffer-empty">
                <strong>NO INTERFACES EXPOSED</strong>
                <small>
                    Android/PRoot is not exposing
                    network interfaces to ChillOS.
                </small>
            </div>
        `;

        return;
    }

    list.forEach(item => {

        const card =
            document.createElement("div");

        card.className =
            "sniffer-interface-card";

        const state =
            String(
                item.state || "unknown"
            ).toUpperCase();

        card.innerHTML = `
            <div>
                <strong>
                    ${snifferEscape(item.name)}
                </strong>

                <small>
                    MAC:
                    ${snifferEscape(item.mac || "—")}
                </small>
            </div>

            <span class="sniffer-state">
                ${snifferEscape(state)}
            </span>
        `;

        box.appendChild(card);
    });
}


function renderSnifferAddresses(data) {

    const box =
        document.getElementById(
            "snifferAddresses"
        );

    if (!box) {
        return;
    }

    box.innerHTML = "";

    const list =
        data.addresses || [];

    if (!list.length) {

        box.innerHTML =
            `<div class="sniffer-empty">
                No addresses visible.
            </div>`;

        return;
    }

    list.forEach(item => {

        box.innerHTML += `
            <div class="sniffer-row">
                <strong>
                    ${snifferEscape(item.address)}
                </strong>

                <small>
                    ${snifferEscape(item.family)}
                    /
                    ${snifferEscape(item.prefix)}
                    •
                    ${snifferEscape(item.interface)}
                </small>
            </div>
        `;
    });
}


function renderSnifferRoutes(data) {

    const box =
        document.getElementById(
            "snifferRoutes"
        );

    if (!box) {
        return;
    }

    box.innerHTML = "";

    const list =
        data.routes || [];

    if (!list.length) {

        box.innerHTML =
            `<div class="sniffer-empty">
                No routing information visible.
            </div>`;

        return;
    }

    list.forEach(route => {

        box.innerHTML += `
            <div class="sniffer-row">
                <strong>
                    ${snifferEscape(
                        route.destination ||
                        "default"
                    )}
                </strong>

                <small>
                    via
                    ${snifferEscape(
                        route.gateway || "direct"
                    )}

                    •

                    ${snifferEscape(
                        route.interface || "—"
                    )}

                    ${
                        route.metric !== null &&
                        route.metric !== undefined
                            ? " • metric " +
                              snifferEscape(
                                  route.metric
                              )
                            : ""
                    }
                </small>
            </div>
        `;
    });
}


function renderSnifferDNS(data) {

    const box =
        document.getElementById(
            "snifferDNS"
        );

    if (!box) {
        return;
    }

    box.innerHTML = "";

    const list =
        data.dns || [];

    if (!list.length) {

        box.innerHTML =
            `<div class="sniffer-empty">
                No DNS servers visible.
            </div>`;

        return;
    }

    list.forEach(server => {

        box.innerHTML += `
            <div class="sniffer-row">
                <strong>
                    ${snifferEscape(server)}
                </strong>

                <small>DNS resolver</small>
            </div>
        `;
    });
}


function renderSnifferStatistics(data) {

    const box =
        document.getElementById(
            "snifferStatistics"
        );

    if (!box) {
        return;
    }

    box.innerHTML = "";

    const statistics =
        data.statistics || {};

    const names =
        Object.keys(statistics);

    if (!names.length) {

        box.innerHTML =
            `<div class="sniffer-empty">
                Interface counters unavailable.
            </div>`;

        return;
    }

    names.forEach(name => {

        const stats =
            statistics[name] || {};

        const card =
            document.createElement("div");

        card.className =
            "sniffer-stat-card";

        card.innerHTML = `
            <strong>
                ${snifferEscape(name)}
            </strong>

            <div class="sniffer-stat-grid">

                <span>
                    RX
                    <b>
                        ${snifferEscape(
                            stats.rx_packets ?? "—"
                        )}
                    </b>
                </span>

                <span>
                    TX
                    <b>
                        ${snifferEscape(
                            stats.tx_packets ?? "—"
                        )}
                    </b>
                </span>

                <span>
                    RX BYTES
                    <b>
                        ${snifferEscape(
                            stats.rx_bytes ?? "—"
                        )}
                    </b>
                </span>

                <span>
                    TX BYTES
                    <b>
                        ${snifferEscape(
                            stats.tx_bytes ?? "—"
                        )}
                    </b>
                </span>

                <span>
                    RX ERR
                    <b>
                        ${snifferEscape(
                            stats.rx_errors ?? "—"
                        )}
                    </b>
                </span>

                <span>
                    TX ERR
                    <b>
                        ${snifferEscape(
                            stats.tx_errors ?? "—"
                        )}
                    </b>
                </span>

            </div>
        `;

        box.appendChild(card);
    });
}


function renderSnifferSockets(data) {

    const box =
        document.getElementById(
            "snifferSockets"
        );

    if (!box) {
        return;
    }

    box.innerHTML = "";

    const sockets =
        data.sockets || {};

    if (!sockets.available) {

        box.innerHTML = `
            <div class="sniffer-empty">
                <strong>SOCKET VISIBILITY UNAVAILABLE</strong>
                <small>
                    The current environment does not
                    expose socket information.
                </small>
            </div>
        `;

        return;
    }

    const tcp =
        sockets.tcp || [];

    const udp =
        sockets.udp || [];

    box.innerHTML += `
        <div class="sniffer-mini-summary">
            <span>
                TCP
                <b>${tcp.length}</b>
            </span>

            <span>
                UDP
                <b>${udp.length}</b>
            </span>
        </div>
    `;

    [...tcp, ...udp].slice(0, 50)
        .forEach(item => {

            box.innerHTML += `
                <div class="sniffer-row">
                    <strong>
                        ${snifferEscape(
                            item.state || "—"
                        )}
                    </strong>

                    <small>
                        ${snifferEscape(
                            item.local || "—"
                        )}

                        →

                        ${snifferEscape(
                            item.remote || "—"
                        )}
                    </small>
                </div>
            `;
        });
}


function renderSnifferCapabilities(data) {

    const box =
        document.getElementById(
            "snifferCapabilities"
        );

    if (!box) {
        return;
    }

    box.innerHTML = "";

    const capabilities =
        data.capabilities || {};

    Object.entries(
        capabilities
    ).forEach(([name, value]) => {

        const available =
            value === true ||
            String(value).toLowerCase() ===
            "available";

        const card =
            document.createElement("div");

        card.className =
            "sniffer-capability " +
            (
                available
                    ? "available"
                    : "restricted"
            );

        card.innerHTML = `
            <strong>
                ${snifferEscape(
                    name.replaceAll(
                        "_",
                        " "
                    ).toUpperCase()
                )}
            </strong>

            <span>
                ${snifferEscape(
                    snifferValue(value)
                )}
            </span>
        `;

        box.appendChild(card);
    });
}


function renderSnifferConnectivity(data) {

    const box =
        document.getElementById(
            "snifferConnectivity"
        );

    if (!box) {
        return;
    }

    box.innerHTML = "";

    const connection =
        data.connectivity || {};

    box.appendChild(
        snifferCard(
            "DNS",
            connection.dns
        )
    );

    box.appendChild(
        snifferCard(
            "HTTPS",
            connection.https
        )
    );

    box.appendChild(
        snifferCard(
            "LATENCY",
            connection.latency_ms === null ||
            connection.latency_ms === undefined
                ? "—"
                : connection.latency_ms + " ms"
        )
    );
}


function renderSnifferDashboard(data) {

    renderSnifferInterfaces(data);
    renderSnifferAddresses(data);
    renderSnifferRoutes(data);
    renderSnifferDNS(data);
    renderSnifferStatistics(data);
    renderSnifferSockets(data);
    renderSnifferCapabilities(data);
    renderSnifferConnectivity(data);

    const summary =
        document.getElementById(
            "snifferSummary"
        );

    const state =
        document.getElementById(
            "snifferState"
        );

    const interfaceCount =
        (data.interfaces || []).length;

    if (summary) {

        summary.textContent =
            interfaceCount
                ? `${interfaceCount} interface(s) visible • telemetry online`
                : "Network telemetry available, but Android is restricting interface visibility.";
    }

    if (state) {

        state.textContent =
            data.status === "ok"
                ? "●"
                : "○";
    }
}


async function refreshSnifferLive() {

    if (snifferBusy) {
        return;
    }

    snifferBusy = true;

    const output =
        document.getElementById(
            "snifferOutput"
        );

    try {

        const response =
            await fetch(
                "/api/sniffer",
                {
                    cache: "no-store"
                }
            );

        const data =
            await response.json();

        if (!response.ok) {

            throw new Error(
                data.error ||
                "Sniffer API error"
            );
        }

        renderSnifferDashboard(data);

        if (output) {

            const now =
                new Date()
                    .toLocaleTimeString();

            output.textContent =
                "Telemetry updated: " +
                now;
        }

    } catch (error) {

        if (output) {

            output.textContent =
                "Sniffer telemetry error: " +
                error.message;
        }

    } finally {

        snifferBusy = false;
    }
}


function startSnifferLive() {

    stopSnifferLive();

    refreshSnifferLive();

    snifferTimer =
        setInterval(
            refreshSnifferLive,
            3000
        );
}


function stopSnifferLive() {

    if (snifferTimer) {

        clearInterval(
            snifferTimer
        );

        snifferTimer = null;
    }
}


const originalOpenSniffer =
    openSniffer;

openSniffer = async function() {

    await originalOpenSniffer();

    startSnifferLive();
};


const originalShowHome =
    showHome;

showHome = function() {

    stopSnifferLive();

    originalShowHome();
};


const originalRefreshSniffer =
    refreshSniffer;

refreshSniffer = async function() {

    await originalRefreshSniffer();

    await refreshSnifferLive();
};



/* ============================================================
   SNIFFER LIVE TRAFFIC MONITOR
   ============================================================ */

let snifferTrafficTimer = null;
let snifferTrafficInterface = "";
let snifferTrafficPrevious = null;
let snifferTrafficHistory = [];

function formatBytes(value) {

    value = Number(value) || 0;

    const units = [
        "B",
        "KB",
        "MB",
        "GB"
    ];

    let index = 0;

    while (
        value >= 1024 &&
        index < units.length - 1
    ) {
        value /= 1024;
        index++;
    }

    return (
        value.toFixed(
            index === 0 ? 0 : 1
        ) +
        " " +
        units[index]
    );
}


function formatRate(value) {

    return formatBytes(value) + "/s";
}


function selectSnifferInterface(name) {

    if (!name) {
        return;
    }

    snifferTrafficInterface = name;

    const select =
        document.getElementById(
            "pcapInterface"
        );

    if (select) {
        select.value = name;
    }

    const label =
        document.getElementById(
            "trafficInterface"
        );

    if (label) {
        label.textContent =
            name.toUpperCase();
    }
}


function populatePcapInterfaces(names) {

    const select =
        document.getElementById(
            "pcapInterface"
        );

    if (!select) {
        return;
    }

    const current =
        snifferTrafficInterface;

    select.innerHTML = "";

    names.forEach(name => {

        const option =
            document.createElement("option");

        option.value = name;
        option.textContent = name;

        select.appendChild(option);
    });

    if (current && names.includes(current)) {

        select.value = current;

    } else if (names.length) {

        select.value = names[0];

        selectSnifferInterface(
            names[0]
        );
    }
}


function drawTrafficGraph() {

    const canvas =
        document.getElementById(
            "trafficGraph"
        );

    if (!canvas) {
        return;
    }

    const ctx =
        canvas.getContext("2d");

    const width =
        canvas.clientWidth || 320;

    const height =
        canvas.clientHeight || 150;

    const ratio =
        window.devicePixelRatio || 1;

    canvas.width =
        width * ratio;

    canvas.height =
        height * ratio;

    ctx.scale(ratio, ratio);

    ctx.clearRect(
        0,
        0,
        width,
        height
    );

    const values =
        snifferTrafficHistory;

    if (values.length < 2) {
        return;
    }

    let max = 1;

    values.forEach(point => {

        max = Math.max(
            max,
            point.rx,
            point.tx
        );

    });

    function drawLine(key) {

        ctx.beginPath();

        values.forEach(
            (point, index) => {

                const x =
                    (index /
                    (values.length - 1)) *
                    width;

                const y =
                    height -
                    (
                        point[key] /
                        max
                    ) *
                    (height - 12) -
                    6;

                if (index === 0) {
                    ctx.moveTo(x, y);
                } else {
                    ctx.lineTo(x, y);
                }
            }
        );

        ctx.stroke();
    }

    drawLine("rx");
    drawLine("tx");
}


async function updateSnifferTraffic() {

    if (!snifferTrafficInterface) {
        return;
    }

    try {

        const data =
            await api(
                "/api/sniffer/traffic?interface=" +
                encodeURIComponent(
                    snifferTrafficInterface
                )
            );

        const now =
            Date.now();

        let rxRate = 0;
        let txRate = 0;

        if (snifferTrafficPrevious) {

            const elapsed =
                (now -
                snifferTrafficPrevious.time) /
                1000;

            if (elapsed > 0) {

                rxRate =
                    Math.max(
                        0,
                        (
                            data.rx_bytes -
                            snifferTrafficPrevious.rx
                        ) / elapsed
                    );

                txRate =
                    Math.max(
                        0,
                        (
                            data.tx_bytes -
                            snifferTrafficPrevious.tx
                        ) / elapsed
                    );
            }
        }

        snifferTrafficPrevious = {
            time: now,
            rx: Number(data.rx_bytes) || 0,
            tx: Number(data.tx_bytes) || 0
        };

        snifferTrafficHistory.push({
            rx: rxRate,
            tx: txRate
        });

        if (
            snifferTrafficHistory.length >
            30
        ) {
            snifferTrafficHistory.shift();
        }

        const rx =
            document.getElementById(
                "rxRate"
            );

        const tx =
            document.getElementById(
                "txRate"
            );

        const totalRx =
            document.getElementById(
                "rxTotal"
            );

        const totalTx =
            document.getElementById(
                "txTotal"
            );

        if (rx) {
            rx.textContent =
                formatRate(rxRate);
        }

        if (tx) {
            tx.textContent =
                formatRate(txRate);
        }

        if (totalRx) {
            totalRx.textContent =
                formatBytes(data.rx_bytes);
        }

        if (totalTx) {
            totalTx.textContent =
                formatBytes(data.tx_bytes);
        }

        drawTrafficGraph();

    } catch (error) {

        const state =
            document.getElementById(
                "trafficState"
            );

        if (state) {
            state.textContent =
                "○ UNAVAILABLE";
        }
    }
}


function startSnifferTraffic() {

    stopSnifferTraffic();

    snifferTrafficPrevious = null;

    snifferTrafficHistory = [];

    updateSnifferTraffic();

    snifferTrafficTimer =
        setInterval(
            updateSnifferTraffic,
            1000
        );
}


function stopSnifferTraffic() {

    if (snifferTrafficTimer) {

        clearInterval(
            snifferTrafficTimer
        );

        snifferTrafficTimer = null;
    }
}


function handleSnifferInterfaceChange() {

    const select =
        document.getElementById(
            "pcapInterface"
        );

    if (!select) {
        return;
    }

    selectSnifferInterface(
        select.value
    );

    snifferTrafficPrevious = null;

    snifferTrafficHistory = [];

    updateSnifferTraffic();
}


/*
 * Replace refreshSniffer with the enhanced
 * version while preserving the existing
 * interface/network rendering.
 */

refreshSniffer = async function() {

    await originalRefreshSniffer();

    const interfaces =
        document.querySelectorAll(
            "#interfaces .sniffer-item strong"
        );

    const names = [];

    interfaces.forEach(item => {

        const name =
            item.textContent.trim();

        if (name) {
            names.push(name);
        }
    });

    populatePcapInterfaces(names);

    const select =
        document.getElementById(
            "pcapInterface"
        );

    if (select) {

        select.onchange =
            handleSnifferInterfaceChange;
    }

    if (
        !snifferTrafficInterface &&
        names.length
    ) {

        selectSnifferInterface(
            names[0]
        );
    }

    startSnifferTraffic();
};
