(() => {
  const api =
    window.browserAPI || (typeof browser !== "undefined" ? browser : chrome);

  let currentNotes = [];
  let selectedNote = null;
  let isEditingNote = false;

  const notesView = document.getElementById("notes-view");
  const notesBackBtn = document.getElementById("notes-back-btn");
  const notesList = document.getElementById("notes-list");
  const notesLoading = document.getElementById("notes-loading");
  const noteDetailPanel = document.getElementById("note-detail-panel");
  const noteEmptyState = document.getElementById("note-empty-state");
  const noteEditor = document.getElementById("note-editor");
  const noteEditorContent = document.getElementById("note-editor-content");
  const noteEditorTitle = document.getElementById("note-editor-title");
  const addNoteBtn = document.getElementById("add-note-btn");

  function sendMessage(message) {
    return new Promise((resolve, reject) => {
      api.runtime.sendMessage(message, (response) => {
        if (api.runtime.lastError) {
          reject(new Error(api.runtime.lastError.message));
        } else {
          resolve(response);
        }
      });
    });
  }

  async function loadNotes() {
    if (notesLoading) notesLoading.style.display = "flex";
    try {
      const response = await sendMessage({ action: "get_all_secure_notes" });
      if (response.success) {
        currentNotes = response.notes || [];
        renderNotes();
      }
    } catch (error) {
      console.error("Failed to load notes:", error);
    }
    if (notesLoading) notesLoading.style.display = "none";
  }

  function cleanQtContent(content) {
    if (!content) return "";
    if (content.includes('meta name="qrichtext"')) {
      try {
        const parser = new DOMParser();
        const doc = parser.parseFromString(content, "text/html");
        return doc.body ? doc.body.innerHTML : content;
      } catch (e) {
        console.error("Error parsing Qt HTML", e);
        return content;
      }
    }
    return content;
  }

  // --- HTML to Markdown Converter ---
  function htmlToMarkdown(html) {
    const temp = document.createElement("div");
    temp.innerHTML = html;
    // Clean spaces
    let md = domToMarkdown(temp).trim();
    // Reduce multiple newlines to max 2
    return md.replace(/\n\s*\n\s*\n/g, "\n\n");
  }

  function domToMarkdown(node) {
    if (node.nodeType === Node.TEXT_NODE) return node.textContent;
    if (node.nodeType !== Node.ELEMENT_NODE) return "";

    switch (node.tagName.toLowerCase()) {
      case "b":
      case "strong":
        return "**" + getChildrenMd(node) + "**";
      case "i":
      case "em":
        return "*" + getChildrenMd(node) + "*";
      case "u":
        return getChildrenMd(node);
      case "code":
        return "`" + getChildrenMd(node) + "`";
      case "h1":
        return "# " + getChildrenMd(node) + "\n\n";
      case "h2":
        return "## " + getChildrenMd(node) + "\n\n";
      case "h3":
        return "### " + getChildrenMd(node) + "\n\n";
      case "p":
        // Check if plain p or has content
        const content = getChildrenMd(node);
        return content.trim() ? content + "\n\n" : "";
      case "ul":
        return getChildrenMd(node) + "\n";
      case "ol":
        return getChildrenMd(node) + "\n";
      case "li":
        const parent = node.parentNode;
        let prefix = "- ";
        if (parent && parent.tagName.toLowerCase() === "ol") {
          prefix = "1. ";
        }
        return prefix + getChildrenMd(node) + "\n";
      case "a":
        return (
          "[" + getChildrenMd(node) + "](" + node.getAttribute("href") + ")"
        );
      case "br":
        return "\n";
      case "div":
        return getChildrenMd(node) + "\n";
      case "span":
        let text = getChildrenMd(node);
        if (node.style.fontWeight === "bold" || node.style.fontWeight >= 700)
          text = "**" + text + "**";
        if (node.style.fontStyle === "italic") text = "*" + text + "*";
        return text;
      case "style":
      case "script":
      case "meta":
      case "head":
        return "";
      default:
        return getChildrenMd(node);
    }
  }

  function getChildrenMd(node) {
    let text = "";
    node.childNodes.forEach((c) => (text += domToMarkdown(c)));
    return text;
  }

  async function copyNoteAsMarkdown() {
    if (!selectedNote) return;

    // Use cleanQtContent first to strip headers, then convert
    const cleanedHtml = cleanQtContent(selectedNote.content);
    const markdown = htmlToMarkdown(cleanedHtml);

    try {
      await navigator.clipboard.writeText(markdown);

      const btn = document.getElementById("copy-md-note-btn");
      if (btn) {
        const originalText = btn.textContent;
        btn.textContent = "Copied!";
        btn.classList.add("btn-success"); // Optional styling
        setTimeout(() => {
          btn.textContent = originalText;
          btn.classList.remove("btn-success");
        }, 2000);
      }
    } catch (err) {
      console.error("Failed to copy", err);
      alert("Failed to copy content");
    }
  }

  function renderNotes() {
    if (!notesList) return;
    notesList.innerHTML = "";

    if (currentNotes.length === 0) {
      notesList.innerHTML = `
        <div class="empty-list">
          <div class="empty-list-icon">📝</div>
          <p>No secure notes yet</p>
        </div>
      `;
      return;
    }

    currentNotes.forEach((note) => {
      const item = document.createElement("div");
      item.className = "note-item";
      item.dataset.id = note.id;
      if (selectedNote && selectedNote.id === note.id) {
        item.classList.add("selected");
      }

      const preview = note.content.replace(/<[^>]*>/g, "").slice(0, 50);

      item.innerHTML = `
        <div class="note-icon">📝</div>
        <div class="note-info">
          <div class="note-title">${escapeHtml(note.title)}</div>
          <div class="note-preview">${escapeHtml(preview)}${preview.length >= 50 ? "..." : ""}</div>
        </div>
      `;

      item.addEventListener("click", () => selectNote(note));
      notesList.appendChild(item);
    });
  }

  function selectNote(note) {
    selectedNote = note;
    isEditingNote = false;

    document.querySelectorAll(".note-item").forEach((item) => {
      item.classList.remove("selected");
      if (item.dataset.id == note.id) {
        item.classList.add("selected");
      }
    });

    if (noteEmptyState) noteEmptyState.classList.add("hidden");
    if (noteEditor) noteEditor.classList.add("hidden");
    if (noteDetailPanel) noteDetailPanel.classList.remove("hidden");

    document.getElementById("note-detail-title").textContent = note.title;
    document.getElementById("note-detail-content").innerHTML = cleanQtContent(
      note.content,
    );
    document.getElementById("note-detail-date").textContent = formatDate(
      note.updated_at || note.created_at,
    );
  }

  function formatDate(dateStr) {
    if (!dateStr) return "";
    const date = new Date(dateStr);
    return date.toLocaleDateString(undefined, {
      year: "numeric",
      month: "short",
      day: "numeric",
    });
  }

  function openNoteEditor(note = null) {
    isEditingNote = true;
    selectedNote = note;

    const noteEmptyState = document.getElementById("note-empty-state");
    const noteDetailPanel = document.getElementById("note-detail-panel");
    const noteEditor = document.getElementById("note-editor");
    const noteEditorTitle = document.getElementById("note-editor-title");
    const noteEditorContent = document.getElementById("note-editor-content");

    if (noteEmptyState) noteEmptyState.classList.add("hidden");
    if (noteDetailPanel) noteDetailPanel.classList.add("hidden");
    if (noteEditor) noteEditor.classList.remove("hidden");

    if (note) {
      if (noteEditorTitle) noteEditorTitle.value = note.title;
      if (noteEditorContent)
        noteEditorContent.innerHTML = cleanQtContent(note.content);
    } else {
      if (noteEditorTitle) noteEditorTitle.value = "";
      if (noteEditorContent) noteEditorContent.innerHTML = "";
    }

    if (noteEditorContent) noteEditorContent.focus();
  }

  function closeNoteEditor() {
    isEditingNote = false;
    const noteEditor = document.getElementById("note-editor");
    const noteEmptyState = document.getElementById("note-empty-state");
    const noteDetailPanel = document.getElementById("note-detail-panel");

    if (noteEditor) noteEditor.classList.add("hidden");

    if (selectedNote) {
      if (noteDetailPanel) noteDetailPanel.classList.remove("hidden");
    } else {
      if (noteEmptyState) noteEmptyState.classList.remove("hidden");
    }
  }

  async function saveNote() {
    const noteEditorTitle = document.getElementById("note-editor-title");
    const noteEditorContent = document.getElementById("note-editor-content");

    const title = noteEditorTitle ? noteEditorTitle.value.trim() : "";
    const content = noteEditorContent ? noteEditorContent.innerHTML.trim() : "";

    if (!title || !content) {
      alert("Title and content are required");
      return;
    }

    try {
      const payload = {
        action: "save_secure_note",
        title,
        content,
      };

      if (selectedNote) {
        payload.id = selectedNote.id;
      }

      const response = await sendMessage(payload);
      if (response.success) {
        closeNoteEditor();
        await loadNotes();

        if (response.id) {
          const savedNote = currentNotes.find((n) => n.id === response.id);
          if (savedNote) selectNote(savedNote);
        }
      } else {
        alert(response.error || "Failed to save note");
      }
    } catch (error) {
      console.error("Failed to save note:", error);
      alert("Failed to save note");
    }
  }

  async function deleteNote() {
    if (!selectedNote) return;
    if (!confirm("Are you sure you want to delete this note?")) return;

    try {
      const response = await sendMessage({
        action: "delete_secure_note",
        id: selectedNote.id,
      });
      if (response.success) {
        selectedNote = null;
        if (noteEmptyState) noteEmptyState.classList.remove("hidden");
        if (noteDetailPanel) noteDetailPanel.classList.add("hidden");
        await loadNotes();
      }
    } catch (error) {
      console.error("Failed to delete note:", error);
    }
  }

  function execCommand(command, value = null) {
    document.execCommand(command, false, value);
    noteEditorContent.focus();
  }

  function formatBold() {
    execCommand("bold");
  }

  function formatItalic() {
    execCommand("italic");
  }

  function formatUnderline() {
    execCommand("underline");
  }

  function formatCode() {
    const selection = window.getSelection();
    if (selection.rangeCount > 0) {
      const range = selection.getRangeAt(0);
      const code = document.createElement("code");
      code.appendChild(range.extractContents());
      range.insertNode(code);
    }
  }

  function formatHeading(level) {
    execCommand("formatBlock", `h${level}`);
  }

  function formatUnorderedList() {
    execCommand("insertUnorderedList");
  }

  function formatOrderedList() {
    execCommand("insertOrderedList");
  }

  function formatLink() {
    const url = prompt("Enter URL:");
    if (url) {
      execCommand("createLink", url);
    }
  }

  function escapeHtml(text) {
    if (!text) return "";
    const div = document.createElement("div");
    div.textContent = text;
    return div.innerHTML;
  }

  function openNotesView() {
    document.getElementById("unlocked-view")?.classList.add("hidden");
    document.getElementById("notes-view")?.classList.remove("hidden");
    loadNotes();
  }

  function closeNotesView() {
    document.getElementById("notes-view")?.classList.add("hidden");
    document.getElementById("unlocked-view")?.classList.remove("hidden");
  }

  document.addEventListener("DOMContentLoaded", () => {
    const notesBackBtnEl = document.getElementById("notes-back-btn");
    if (notesBackBtnEl)
      notesBackBtnEl.addEventListener("click", closeNotesView);

    const addBtn = document.getElementById("add-note-btn");
    if (addBtn) addBtn.addEventListener("click", () => openNoteEditor());

    const editNoteBtn = document.getElementById("edit-note-btn");
    if (editNoteBtn)
      editNoteBtn.addEventListener("click", () => openNoteEditor(selectedNote));

    const deleteNoteBtn = document.getElementById("delete-note-btn");
    if (deleteNoteBtn) deleteNoteBtn.addEventListener("click", deleteNote);

    const saveNoteBtn = document.getElementById("save-note-btn");
    if (saveNoteBtn) saveNoteBtn.addEventListener("click", saveNote);

    const cancelNoteBtn = document.getElementById("cancel-note-btn");
    if (cancelNoteBtn) cancelNoteBtn.addEventListener("click", closeNoteEditor);

    const copyBtn = document.getElementById("copy-md-note-btn");
    if (copyBtn) copyBtn.addEventListener("click", copyNoteAsMarkdown);

    document
      .getElementById("format-bold")
      ?.addEventListener("click", formatBold);
    document
      .getElementById("format-italic")
      ?.addEventListener("click", formatItalic);
    document
      .getElementById("format-underline")
      ?.addEventListener("click", formatUnderline);
    document
      .getElementById("format-code")
      ?.addEventListener("click", formatCode);
    document
      .getElementById("format-h1")
      ?.addEventListener("click", () => formatHeading(1));
    document
      .getElementById("format-h2")
      ?.addEventListener("click", () => formatHeading(2));
    document
      .getElementById("format-h3")
      ?.addEventListener("click", () => formatHeading(3));
    document
      .getElementById("format-ul")
      ?.addEventListener("click", formatUnorderedList);
    document
      .getElementById("format-ol")
      ?.addEventListener("click", formatOrderedList);
    document
      .getElementById("format-link")
      ?.addEventListener("click", formatLink);
  });

  // Expose global functions
  window.openNotesView = openNotesView;
  window.closeNotesView = closeNotesView;
})();
