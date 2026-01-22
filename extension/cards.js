(() => {
  // browserAPI is already defined in popup.js which loads first
  const api =
    window.browserAPI || (typeof browser !== "undefined" ? browser : chrome);

  let currentCards = [];
  let selectedCard = null;

  const cardsView = document.getElementById("cards-view");
  const cardsBackBtn = document.getElementById("cards-back-btn");
  const cardsList = document.getElementById("cards-list");
  const cardsLoading = document.getElementById("cards-loading");
  const cardDetailPanel = document.getElementById("card-detail-panel");
  const cardEmptyState = document.getElementById("card-empty-state");
  const addCardBtn = document.getElementById("add-card-btn");

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

  async function loadCards() {
    if (cardsLoading) cardsLoading.style.display = "flex";
    try {
      const response = await sendMessage({ action: "get_all_credit_cards" });
      if (response.success) {
        currentCards = response.cards || [];
        renderCards();
      }
    } catch (error) {
      console.error("Failed to load cards:", error);
    }
    if (cardsLoading) cardsLoading.style.display = "none";
  }

  function renderCards() {
    if (!cardsList) return;
    cardsList.innerHTML = "";

    if (currentCards.length === 0) {
      cardsList.innerHTML = `
        <div class="empty-list">
          <div class="empty-list-icon">💳</div>
          <p>No credit cards yet</p>
        </div>
      `;
      return;
    }

    currentCards.forEach((card) => {
      const item = document.createElement("div");
      item.className = "card-item";
      item.dataset.id = card.id;
      if (selectedCard && selectedCard.id === card.id) {
        item.classList.add("selected");
      }

      const lastFour = card.card_number.slice(-4);
      const cardType = detectCardType(card.card_number);

      item.innerHTML = `
        <div class="card-icon">${getCardIcon(cardType)}</div>
        <div class="card-info">
          <div class="card-title">${escapeHtml(card.title)}</div>
          <div class="card-number">•••• ${lastFour}</div>
        </div>
      `;

      item.addEventListener("click", () => selectCard(card));
      cardsList.appendChild(item);
    });
  }

  function detectCardType(number) {
    const cleaned = number.replace(/\s/g, "");
    if (/^4/.test(cleaned)) return "visa";
    if (/^5[1-5]/.test(cleaned)) return "mastercard";
    if (/^3[47]/.test(cleaned)) return "amex";
    if (/^6(?:011|5)/.test(cleaned)) return "discover";
    return "generic";
  }

  function getCardIcon(type) {
    const icons = {
      visa: "💳",
      mastercard: "💳",
      amex: "💳",
      discover: "💳",
      generic: "💳",
    };
    return icons[type] || "💳";
  }

  function selectCard(card) {
    selectedCard = card;

    document.querySelectorAll(".card-item").forEach((item) => {
      item.classList.remove("selected");
      if (item.dataset.id == card.id) {
        item.classList.add("selected");
      }
    });

    if (cardEmptyState) cardEmptyState.classList.add("hidden");
    if (cardDetailPanel) cardDetailPanel.classList.remove("hidden");

    document.getElementById("card-detail-title").textContent = card.title;
    document.getElementById("card-detail-holder").textContent =
      card.cardholder_name;
    document.getElementById("card-detail-number").textContent =
      formatCardNumber(card.card_number);
    document.getElementById("card-detail-expiry").textContent =
      card.expiry_date;
    document.getElementById("card-detail-cvv").textContent = "•••";
    document.getElementById("card-detail-cvv").dataset.value = card.cvv;
    document.getElementById("card-detail-cvv").dataset.visible = "false";
  }

  function formatCardNumber(number) {
    const cleaned = number.replace(/\s/g, "");
    return cleaned.replace(/(.{4})/g, "$1 ").trim();
  }

  async function copyCardField(field) {
    if (!selectedCard) return;

    let value = "";
    switch (field) {
      case "number":
        value = selectedCard.card_number;
        break;
      case "cvv":
        value = selectedCard.cvv;
        break;
      case "expiry":
        value = selectedCard.expiry_date;
        break;
      case "holder":
        value = selectedCard.cardholder_name;
        break;
    }

    try {
      await navigator.clipboard.writeText(value);
      const btn = document.querySelector(`[data-copy-card="${field}"]`);
      if (btn) {
        const originalHTML = btn.innerHTML;
        btn.textContent = "✓";
        setTimeout(() => {
          btn.innerHTML = originalHTML;
        }, 1500);
      }
    } catch (error) {
      console.error("Failed to copy:", error);
    }
  }

  function toggleCvvVisibility() {
    const cvvEl = document.getElementById("card-detail-cvv");
    if (!cvvEl) return;

    const isVisible = cvvEl.dataset.visible === "true";
    if (isVisible) {
      cvvEl.textContent = "•••";
      cvvEl.dataset.visible = "false";
    } else {
      cvvEl.textContent = cvvEl.dataset.value;
      cvvEl.dataset.visible = "true";
    }
  }

  async function autofillCard() {
    if (!selectedCard) return;

    try {
      await sendMessage({
        action: "fill_card",
        card_number: selectedCard.card_number,
        expiry_date: selectedCard.expiry_date,
        cvv: selectedCard.cvv,
        cardholder_name: selectedCard.cardholder_name,
      });
      window.close();
    } catch (error) {
      console.error("Failed to autofill card:", error);
    }
  }

  async function deleteCard() {
    if (!selectedCard) return;
    if (!confirm("Are you sure you want to delete this card?")) return;

    try {
      const response = await sendMessage({
        action: "delete_credit_card",
        id: selectedCard.id,
      });
      if (response.success) {
        selectedCard = null;
        if (cardEmptyState) cardEmptyState.classList.remove("hidden");
        if (cardDetailPanel) cardDetailPanel.classList.add("hidden");
        await loadCards();
      }
    } catch (error) {
      console.error("Failed to delete card:", error);
    }
  }

  function escapeHtml(text) {
    if (!text) return "";
    const div = document.createElement("div");
    div.textContent = text;
    return div.innerHTML;
  }

  function openCardEditor(card = null) {
    const cardEditor = document.getElementById("card-editor");
    const cardEmptyState = document.getElementById("card-empty-state");
    const cardDetailPanel = document.getElementById("card-detail-panel");
    const editorTitle = document.getElementById("card-editor-title");
    const form = document.getElementById("card-form");

    if (cardEmptyState) cardEmptyState.classList.add("hidden");
    if (cardDetailPanel) cardDetailPanel.classList.add("hidden");
    if (cardEditor) cardEditor.classList.remove("hidden");

    if (card) {
      editorTitle.textContent = "Edit Credit Card";
      document.getElementById("card-title-input").value = card.title;
      document.getElementById("card-holder-input").value = card.cardholder_name;
      document.getElementById("card-number-input").value = card.card_number;
      document.getElementById("card-expiry-input").value = card.expiry_date;
      document.getElementById("card-cvv-input").value = card.cvv;
      document.getElementById("card-notes-input").value = card.notes || "";
      form.dataset.editId = card.id;
    } else {
      editorTitle.textContent = "Add Credit Card";
      form.reset();
      delete form.dataset.editId;
    }
  }

  function closeCardEditor() {
    const cardEditor = document.getElementById("card-editor");
    const cardEmptyState = document.getElementById("card-empty-state");
    const cardDetailPanel = document.getElementById("card-detail-panel");

    if (cardEditor) cardEditor.classList.add("hidden");

    if (selectedCard) {
      if (cardDetailPanel) cardDetailPanel.classList.remove("hidden");
    } else {
      if (cardEmptyState) cardEmptyState.classList.remove("hidden");
    }
  }

  async function saveCard(e) {
    e.preventDefault();
    const form = document.getElementById("card-form");

    const title = document.getElementById("card-title-input").value.trim();
    const cardholder_name = document
      .getElementById("card-holder-input")
      .value.trim();
    const card_number = document
      .getElementById("card-number-input")
      .value.replace(/\s/g, "");
    const expiry_date = document
      .getElementById("card-expiry-input")
      .value.trim();
    const cvv = document.getElementById("card-cvv-input").value.trim();
    const notes =
      document.getElementById("card-notes-input").value.trim() || null;

    if (!title || !cardholder_name || !card_number || !expiry_date || !cvv) {
      alert("Please fill all required fields");
      return;
    }

    try {
      const payload = {
        action: "save_credit_card",
        title,
        cardholder_name,
        card_number,
        expiry_date,
        cvv,
        notes,
      };

      if (form.dataset.editId) {
        payload.id = parseInt(form.dataset.editId);
      }

      const response = await sendMessage(payload);
      if (response.success) {
        closeCardEditor();
        await loadCards();
      } else {
        alert(response.error || "Failed to save card");
      }
    } catch (error) {
      console.error("Failed to save card:", error);
      alert("Failed to save card");
    }
  }

  function openCardsView() {
    document.getElementById("unlocked-view")?.classList.add("hidden");
    document.getElementById("cards-view")?.classList.remove("hidden");
    loadCards();
  }

  function closeCardsView() {
    document.getElementById("cards-view")?.classList.add("hidden");
    document.getElementById("unlocked-view")?.classList.remove("hidden");
  }

  document.addEventListener("DOMContentLoaded", () => {
    const cardsBackBtnEl = document.getElementById("cards-back-btn");
    if (cardsBackBtnEl)
      cardsBackBtnEl.addEventListener("click", closeCardsView);

    document.querySelectorAll("[data-copy-card]").forEach((btn) => {
      btn.addEventListener("click", () => copyCardField(btn.dataset.copyCard));
    });

    const toggleCvvBtn = document.getElementById("toggle-card-cvv");
    if (toggleCvvBtn)
      toggleCvvBtn.addEventListener("click", toggleCvvVisibility);

    const autofillCardBtn = document.getElementById("autofill-card-btn");
    if (autofillCardBtn)
      autofillCardBtn.addEventListener("click", autofillCard);

    const deleteCardBtn = document.getElementById("delete-card-btn");
    if (deleteCardBtn) deleteCardBtn.addEventListener("click", deleteCard);

    // Card editor buttons
    const addCardBtn = document.getElementById("add-card-btn");
    if (addCardBtn)
      addCardBtn.addEventListener("click", () => openCardEditor());

    const cancelCardBtn = document.getElementById("cancel-card-btn");
    if (cancelCardBtn) cancelCardBtn.addEventListener("click", closeCardEditor);

    const cardForm = document.getElementById("card-form");
    if (cardForm) cardForm.addEventListener("submit", saveCard);
  });

  // Expose global functions
  window.openCardsView = openCardsView;
  window.closeCardsView = closeCardsView;
})();
