(function () {
    "use strict";

    const API = ""; // relative to the Django server

    // ---------- State ----------
    let sessionId = null;
    const state = {
        primary: null,
        secondary: null,
        tertiary: null,
    };

    // ---------- DOM helpers ----------
    function el(selector) {
        return document.querySelector(selector);
    }

    function escapeHtml(str) {
        return String(str)
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;")
            .replace(/'/g, "&#039;");
    }

    // Minimal, safe markdown renderer: escapes HTML first, then applies a
    // small allowlist of formatting (headings, bold, italics, links, lists).
    function renderMarkdown(text) {
        let html = escapeHtml(text);

        // Links: [text](url)
        html = html.replace(
            /\[([^\]]+)\]\((https?:\/\/[^)\s]+)\)/g,
            '<a href="$2" target="_blank" rel="noopener">$1</a>'
        );

        // Bold and italics
        html = html.replace(/\*\*([^*]+)\*\*/g, "<strong>$1</strong>");
        html = html.replace(/(^|[^*])\*([^*\n]+)\*/g, "$1<em>$2</em>");
        html = html.replace(/__([^_]+)__/g, "<strong>$1</strong>");

        // Headings (###, ##, #)
        html = html.replace(/^###\s+(.+)$/gm, "<h3>$1</h3>");
        html = html.replace(/^##\s+(.+)$/gm, "<h2>$1</h2>");
        html = html.replace(/^#\s+(.+)$/gm, "<h1>$1</h1>");

        // Unordered lists: lines starting with "- " or "* "
        html = html.replace(/^[-*]\s+(.+)$/gm, "<li>$1</li>");
        html = html.replace(/(<li>[\s\S]*?<\/li>)/g, "<ul>$1</ul>");

        // Line breaks -> paragraphs (split on blank lines)
        const blocks = html.split(/\n{2,}/);
        html = blocks
            .map(function (block) {
                const trimmed = block.trim();
                if (
                    /^<(h[1-4]|ul|ol|li)/.test(trimmed) ||
                    /^<a /.test(trimmed)
                ) {
                    return trimmed;
                }
                return "<p>" + trimmed.replace(/\n/g, "<br>") + "</p>";
            })
            .join("");

        return html;
    }

    // ---------- Tab switching ----------
    function initTabs() {
        const tabs = document.querySelectorAll(".tab");
        tabs.forEach(function (tab) {
            tab.addEventListener("click", function () {
                tabs.forEach(function (t) {
                    t.classList.remove("active");
                    t.setAttribute("aria-selected", "false");
                });
                tab.classList.add("active");
                tab.setAttribute("aria-selected", "true");

                document.querySelectorAll(".tab-panel").forEach(function (panel) {
                    panel.hidden = true;
                    panel.classList.remove("active");
                });

                const target = el("#tab-" + tab.dataset.tab);
                target.hidden = false;
                target.classList.add("active");
            });
        });
    }

    // ---------- Mood explorer ----------
    async function loadMoodTaxonomy() {
        try {
            const res = await fetch(API + "/api/moods/");
            const data = await res.json();
            renderPrimary(data.taxonomy || []);
        } catch (err) {
            console.error("Failed to load moods:", err);
        }
    }

    function renderPrimary(taxonomy) {
        const primaryGrid = el("#primary-grid");
        primaryGrid.innerHTML = "";

        taxonomy.forEach(function (entry) {
            const chip = document.createElement("button");
            chip.className = "mood-chip";
            chip.textContent = entry.primary;
            chip.addEventListener("click", function () {
                state.primary = entry.primary;
                state.secondary = null;
                state.tertiary = null;
                highlightChip(primaryGrid, chip);
                renderSecondary(entry.secondary || []);
                clearTertiary();
                clearResult();
            });
            primaryGrid.appendChild(chip);
        });
    }

    function renderSecondary(secondary) {
        const secondaryGrid = el("#secondary-grid");
        secondaryGrid.innerHTML = "";
        const label = el("#secondary-grid-label");
        if (label) label.hidden = !secondary.length;

        secondary.forEach(function (entry) {
            const chip = document.createElement("button");
            chip.className = "mood-chip";
            chip.textContent = entry.mood;
            chip.addEventListener("click", function () {
                state.secondary = entry.mood;
                state.tertiary = null;
                highlightChip(secondaryGrid, chip);
                renderTertiary(entry.tertiary || []);
                clearResult();
            });
            secondaryGrid.appendChild(chip);
        });
    }

    function renderTertiary(tertiary) {
        const tertiaryGrid = el("#tertiary-grid");
        tertiaryGrid.innerHTML = "";
        const label = el("#tertiary-grid-label");
        if (label) label.hidden = !tertiary.length;

        tertiary.forEach(function (mood) {
            const chip = document.createElement("button");
            chip.className = "mood-chip";
            chip.textContent = mood;
            chip.addEventListener("click", function () {
                state.tertiary = mood;
                highlightChip(tertiaryGrid, chip);
                fetchMoodResult(mood);
            });
            tertiaryGrid.appendChild(chip);
        });
    }

    function clearTertiary() {
        el("#tertiary-grid").innerHTML = "";
        const label = el("#tertiary-grid-label");
        if (label) label.hidden = true;
    }

    function clearResult() {
        el("#mood-result").hidden = true;
        el("#mood-result").innerHTML = "";
    }

    function highlightChip(container, selected) {
        container.querySelectorAll(".mood-chip").forEach(function (c) {
            c.classList.remove("selected");
        });
        selected.classList.add("selected");
    }

    async function fetchMoodResult(mood) {
        try {
            const res = await fetch(API + "/api/mood/", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ mood: mood }),
            });
            const data = await res.json();
            renderMoodResult(data);
        } catch (err) {
            console.error("Failed to fetch mood:", err);
        }
    }

    function renderMoodResult(data) {
        const container = el("#mood-result");
        container.hidden = false;

        if (!data.found || !data.results || !data.results.length) {
            container.innerHTML =
                '<div class="card"><p>' +
                escapeHtml(data.message || "No data found for this mood.") +
                "</p></div>";
            return;
        }

        const resource = data.results[0];
        let html = '<div class="card">';
        html += "<h3>" + escapeHtml(resource.mood) + "</h3>";

        if (resource.description) {
            html += "<p>" + escapeHtml(resource.description) + "</p>";
        }

        if (resource.coping_mechanisms && resource.coping_mechanisms.length) {
            html += "<h4>Coping mechanisms</h4><ul>";
            resource.coping_mechanisms.forEach(function (item) {
                html += "<li>" + escapeHtml(item) + "</li>";
            });
            html += "</ul>";
        }

        if (resource.music_suggestions && resource.music_suggestions.length) {
            html += "<h4>Music to try</h4><ul>";
            resource.music_suggestions.forEach(function (item) {
                html += "<li>" + escapeHtml(item) + "</li>";
            });
            html += "</ul>";
        }

        if (resource.resource_links && resource.resource_links.length) {
            html += "<h4>Resources</h4><ul class='resource-list'>";
            resource.resource_links.forEach(function (link) {
                html +=
                    "<li><a href='" +
                    escapeHtml(link.url) +
                    "' target='_blank' rel='noopener'>" +
                    escapeHtml(link.title) +
                    "</a></li>";
            });
            html += "</ul>";
        }

        html += "</div>";

        if (data.articles && data.articles.length) {
            html += '<div class="card"><h4>Related articles</h4><ul class="resource-list">';
            data.articles.forEach(function (article) {
                html +=
                    "<li><a href='" +
                    escapeHtml(article.url) +
                    "' target='_blank' rel='noopener'>" +
                    escapeHtml(article.title) +
                    "</a></li>";
            });
            html += "</ul></div>";
        }

        container.innerHTML = html;
    }

    // ---------- AI Chat ----------
    function initChat() {
        const form = el("#chat-form");
        form.addEventListener("submit", async function (event) {
            event.preventDefault();
            const input = el("#chat-input");
            const message = input.value.trim();
            if (!message) return;

            appendMessage("user", message);
            input.value = "";

            const sendBtn = form.querySelector("button");
            sendBtn.disabled = true;
            el("#tool-activity").hidden = true;
            el("#tool-activity").innerHTML = "";

            const typing = appendTypingIndicator();

            try {
                const res = await fetch(API + "/api/chat/", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({
                        message: message,
                        session_id: sessionId,
                    }),
                });
                const data = await res.json();

                if (data.session_id) sessionId = data.session_id;
                removeElement(typing);

                if (data.tool_calls && data.tool_calls.length) {
                    renderToolActivity(data.tool_calls);
                }
                appendMessage("assistant", data.reply || "");
            } catch (err) {
                removeElement(typing);
                appendMessage(
                    "assistant",
                    "Sorry, something went wrong while reaching the assistant."
                );
                console.error(err);
            } finally {
                sendBtn.disabled = false;
            }
        });
    }

    function appendMessage(role, text) {
        const container = el("#chat-container");
        const empty = container.querySelector(".chat-empty");
        if (empty) empty.remove();

        const div = document.createElement("div");
        div.className = "message " + role;
        if (role === "assistant") {
            div.innerHTML = renderMarkdown(text);
        } else {
            div.textContent = text;
        }
        container.appendChild(div);
        container.scrollTop = container.scrollHeight;
    }

    function appendTypingIndicator() {
        const container = el("#chat-container");
        const empty = container.querySelector(".chat-empty");
        if (empty) empty.remove();

        const div = document.createElement("div");
        div.className = "message assistant";
        div.textContent = "Thinking...";
        div.setAttribute("data-typing", "true");
        container.appendChild(div);
        container.scrollTop = container.scrollHeight;
        return div;
    }

    function removeElement(node) {
        if (node && node.parentNode) node.parentNode.removeChild(node);
    }

    function renderToolActivity(toolCalls) {
        const container = el("#tool-activity");
        container.hidden = false;
        let html = "<strong>Tool activity:</strong><ul>";
        toolCalls.forEach(function (call) {
            html += "<li>" + escapeHtml(call.tool) + "</li>";
        });
        html += "</ul>";
        container.innerHTML = html;
    }

    // ---------- Articles ----------
    async function loadArticles(filter) {
        try {
            const res = await fetch(API + "/api/articles/");
            const data = await res.json();
            renderArticles(data.articles || [], filter || "");
        } catch (err) {
            console.error("Failed to load articles:", err);
        }
    }

    function renderArticles(articles, filter) {
        const grid = el("#article-grid");
        grid.innerHTML = "";

        const query = filter.toLowerCase();
        const filtered = articles.filter(function (article) {
            if (!query) return true;
            const haystack = [
                article.title,
                article.description,
                (article.topics || []).join(" "),
            ]
                .join(" ")
                .toLowerCase();
            return haystack.includes(query);
        });

        if (!filtered.length) {
            grid.innerHTML = '<p class="subtitle">No articles found.</p>';
            return;
        }

        filtered.forEach(function (article) {
            const card = document.createElement("div");
            card.className = "article-card";

            let html = "<h3><a href='" + escapeHtml(article.url) + "' target='_blank' rel='noopener'>" + escapeHtml(article.title) + "</a></h3>";
            if (article.description) {
                html += "<p>" + escapeHtml(article.description) + "</p>";
            }
            if (article.topics && article.topics.length) {
                html += '<div class="topics">';
                article.topics.forEach(function (topic) {
                    html += '<span class="topic-tag">' + escapeHtml(topic) + "</span>";
                });
                html += "</div>";
            }
            card.innerHTML = html;
            grid.appendChild(card);
        });
    }

    function initArticles() {
        loadArticles("");
        el("#articles-search").addEventListener("input", function () {
            loadArticles(this.value);
        });
        el("#refresh-articles").addEventListener("click", async function () {
            this.disabled = true;
            this.textContent = "Refreshing...";
            try {
                await fetch(API + "/api/articles/refresh/", { method: "POST" });
                await loadArticles(el("#articles-search").value);
            } catch (err) {
                console.error("Refresh failed:", err);
            } finally {
                this.disabled = false;
                this.textContent = "Refresh from web";
            }
        });
    }

    // ---------- Boot ----------
    document.addEventListener("DOMContentLoaded", function () {
        initTabs();
        loadMoodTaxonomy();
        initChat();
        initArticles();
    });
})();
