import { useState, useMemo } from "react";
import {
  Search01Icon,
  CreditCardIcon,
  PlusSignIcon,
  StarIcon,
  Clock01Icon,
  Edit02Icon,
  Delete02Icon,
  Copy01Icon,
  CheckmarkCircle01Icon,
  FloppyDiskIcon,
  Cancel01Icon,
  ViewIcon,
  ViewOffSlashIcon,
  Loading03Icon,
} from "@hugeicons/core-free-icons";
import { HugeiconsIcon } from "@hugeicons/react";
import {
  useVaultStore,
  CreditCard as CreditCardType,
} from "../stores/vaultStore";
import { writeText } from "@tauri-apps/plugin-clipboard-manager";

import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog";

export function CreditCardsPage() {
  const [searchQuery, setSearchQuery] = useState("");
  const [searchFocused, setSearchFocused] = useState(false);
  const [selectedCard, setSelectedCard] = useState<CreditCardType | null>(null);
  const [isEditing, setIsEditing] = useState(false);
  const [isCreating, setIsCreating] = useState(false);
  const [showCardNumber, setShowCardNumber] = useState(false);
  const [showCVV, setShowCVV] = useState(false);
  const [copiedField, setCopiedField] = useState<string | null>(null);
  const [isSaving, setIsSaving] = useState(false);
  const [cardToDelete, setCardToDelete] = useState<CreditCardType | null>(null);

  const [editForm, setEditForm] = useState({
    title: "",
    card_number: "",
    cardholder_name: "",
    expiry_date: "",
    cvv: "",
  });

  const creditCards = useVaultStore((state) => state.creditCards);
  const addCreditCard = useVaultStore((state) => state.addCreditCard);
  const updateCreditCard = useVaultStore((state) => state.updateCreditCard);
  const deleteCreditCard = useVaultStore((state) => state.deleteCreditCard);

  const filteredCards = useMemo(() => {
    let cards = [...creditCards];

    if (searchQuery) {
      const query = searchQuery.toLowerCase();
      cards = cards.filter(
        (card) =>
          card.title.toLowerCase().includes(query) ||
          card.cardholder_name.toLowerCase().includes(query) ||
          card.card_number.includes(query),
      );
    }

    return cards.sort(
      (a, b) =>
        new Date(b.updated_at).getTime() - new Date(a.updated_at).getTime(),
    );
  }, [creditCards, searchQuery]);

  const handleCopy = async (text: string, field: string) => {
    try {
      await writeText(text);
      setCopiedField(field);
      setTimeout(() => setCopiedField(null), 2000);
    } catch (error) {
      console.error("Failed to copy:", error);
    }
  };

  const handleCreate = () => {
    setIsCreating(true);
    setIsEditing(false);
    setSelectedCard(null);
    setEditForm({
      title: "",
      card_number: "",
      cardholder_name: "",
      expiry_date: "",
      cvv: "",
    });
    setShowCardNumber(true);
    setShowCVV(true);
  };

  const handleEdit = (card: CreditCardType) => {
    setSelectedCard(card);
    setIsEditing(true);
    setIsCreating(false);
    setEditForm({
      title: card.title,
      card_number: card.card_number,
      cardholder_name: card.cardholder_name,
      expiry_date: card.expiry_date,
      cvv: card.cvv,
    });
    setShowCardNumber(true);
    setShowCVV(true);
  };

  const handleCancel = () => {
    setIsEditing(false);
    setIsCreating(false);
    setEditForm({
      title: "",
      card_number: "",
      cardholder_name: "",
      expiry_date: "",
      cvv: "",
    });
    setShowCardNumber(false);
    setShowCVV(false);
  };

  const handleSave = async () => {
    if (!editForm.title.trim() || !editForm.card_number.trim() || isSaving)
      return;
    setIsSaving(true);
    try {
      if (isCreating) {
        await addCreditCard({
          title: editForm.title,
          card_number: editForm.card_number,
          cardholder_name: editForm.cardholder_name,
          expiry_date: editForm.expiry_date,
          cvv: editForm.cvv,
        });
      } else if (selectedCard && isEditing) {
        await updateCreditCard(selectedCard.id, {
          title: editForm.title,
          card_number: editForm.card_number,
          cardholder_name: editForm.cardholder_name,
          expiry_date: editForm.expiry_date,
          cvv: editForm.cvv,
        });
      }
      setIsEditing(false);
      setIsCreating(false);
      setSelectedCard(null);
      setEditForm({
        title: "",
        card_number: "",
        cardholder_name: "",
        expiry_date: "",
        cvv: "",
      });
      setShowCardNumber(false);
      setShowCVV(false);
    } catch (error) {
      console.error("Save failed:", error);
    } finally {
      setIsSaving(false);
    }
  };

  const confirmDelete = async () => {
    if (!cardToDelete) return;
    await deleteCreditCard(cardToDelete.id);
    if (selectedCard?.id === cardToDelete.id) {
      setSelectedCard(null);
      setIsEditing(false);
    }
    setCardToDelete(null);
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString("en-US", {
      month: "short",
      day: "numeric",
      year: "numeric",
    });
  };

  const maskCardNumber = (number: string) => {
    if (number.length < 4) return number;
    return "•••• •••• •••• " + number.slice(-4);
  };

  const getCardBrand = (number: string) => {
    const cleaned = number.replace(/\s/g, "");
    if (cleaned.startsWith("4")) return "visa";
    if (/^5[1-5]/.test(cleaned)) return "mastercard";
    if (/^3[47]/.test(cleaned)) return "amex";
    if (/^6(?:011|5)/.test(cleaned)) return "discover";
    return "unknown";
  };

  return (
    <div className="flex-1 flex overflow-hidden bg-background h-[calc(100vh-42px)]">
      <AlertDialog
        open={!!cardToDelete}
        onOpenChange={(open) => !open && setCardToDelete(null)}
      >
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Are you absolutely sure?</AlertDialogTitle>
            <AlertDialogDescription>
              This will permanently delete the credit card{" "}
              <strong className="text-foreground">
                "{cardToDelete?.title}"
              </strong>
              . This action cannot be undone.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <AlertDialogAction
              onClick={confirmDelete}
              className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
            >
              Delete Card
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>

      <div className="w-72 h-full flex flex-col shrink-0 border-r border-border bg-background">
        <div className="px-4 pt-4 pb-3 shrink-0 border-b border-border">
          <div className="flex items-center justify-between mb-3">
            <div className="flex items-center gap-2">
              <span className="w-2 h-2 rounded-full bg-primary" />
              <span className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                Credit Cards
              </span>
            </div>
            <span className="text-xs font-medium px-2 py-0.5 rounded-full bg-primary/15 text-primary">
              {filteredCards.length}
            </span>
          </div>

          <div className="relative">
            <HugeiconsIcon
              icon={Search01Icon}
              size={14}
              className="absolute left-3 top-1/2 -translate-y-1/2 pointer-events-none text-muted-foreground"
            />
            <input
              type="text"
              placeholder="Search cards…"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              onFocus={() => setSearchFocused(true)}
              onBlur={() => setSearchFocused(false)}
              className={`${
                searchFocused ? "border-primary" : "border-border"
              } border w-full rounded-lg pl-8 pr-3 py-1.5 text-xs outline-none transition-colors bg-muted text-foreground placeholder:text-muted-foreground/50`}
            />
          </div>
        </div>

        <div className="flex-1 overflow-y-auto min-h-0 p-2">
          {filteredCards.length === 0 ? (
            <div className="flex flex-col items-center justify-center h-48 gap-3">
              <div className="w-10 h-10 rounded-xl flex items-center justify-center bg-muted">
                <HugeiconsIcon
                  icon={CreditCardIcon}
                  size={18}
                  className="text-muted-foreground/40"
                />
              </div>
              <p className="text-xs text-muted-foreground">
                {searchQuery ? "No cards found" : "No credit cards yet"}
              </p>
              {!searchQuery && (
                <button
                  onClick={handleCreate}
                  className="text-xs text-primary hover:opacity-75 transition-opacity"
                >
                  Add your first card
                </button>
              )}
            </div>
          ) : (
            <div className="space-y-0.5 pb-4">
              {filteredCards.map((card) => {
                const selected = selectedCard?.id === card.id;
                return (
                  <button
                    key={card.id}
                    onClick={() => {
                      setSelectedCard(card);
                      setIsEditing(false);
                      setIsCreating(false);
                      setShowCardNumber(false);
                      setShowCVV(false);
                    }}
                    className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-left transition-all ${
                      selected
                        ? "bg-muted border-primary/25 border"
                        : "bg-transparent border-transparent border hover:bg-muted/50"
                    }`}
                  >
                    <div className="w-8 h-8 rounded-lg flex items-center justify-center shrink-0 bg-primary/10">
                      <HugeiconsIcon
                        icon={CreditCardIcon}
                        size={15}
                        className="text-primary"
                      />
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-1.5 mb-0.5">
                        <span
                          className={`text-sm font-medium truncate ${
                            selected ? "text-primary" : "text-foreground"
                          }`}
                        >
                          {card.title}
                        </span>
                        {card.favorite && (
                          <HugeiconsIcon
                            icon={StarIcon}
                            size={11}
                            className="text-primary shrink-0"
                          />
                        )}
                      </div>
                      <p className="text-xs truncate text-muted-foreground leading-snug">
                        {maskCardNumber(card.card_number)}
                      </p>
                    </div>
                  </button>
                );
              })}
            </div>
          )}
        </div>

        <div className="p-3 shrink-0 border-t border-border bg-background">
          <button
            onClick={handleCreate}
            className="w-full flex items-center justify-center gap-2 py-2 px-3 rounded-lg text-sm font-medium transition-colors bg-primary/10 text-primary hover:bg-primary/15"
          >
            <HugeiconsIcon icon={PlusSignIcon} size={15} />
            New card
          </button>
        </div>
      </div>

      <div className="flex-1 h-full flex flex-col overflow-hidden">
        {isCreating || isEditing ? (
          <>
            <div className="px-6 py-4 shrink-0 flex items-center justify-between border-b border-border">
              <h2 className="text-sm font-semibold text-foreground">
                {isCreating ? "New Credit Card" : "Edit Card"}
              </h2>
              <div className="flex items-center gap-1.5">
                <button
                  onClick={handleCancel}
                  className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm text-muted-foreground hover:text-foreground hover:bg-muted transition-colors"
                >
                  <HugeiconsIcon icon={Cancel01Icon} size={14} />
                  Cancel
                </button>
                <button
                  onClick={handleSave}
                  disabled={
                    !editForm.title.trim() ||
                    !editForm.card_number.trim() ||
                    isSaving
                  }
                  className="flex items-center gap-2 px-3 py-1.5 rounded-lg text-sm font-medium transition-all disabled:opacity-70 disabled:cursor-not-allowed bg-primary text-primary-foreground min-w-[85px] justify-center hover:opacity-90"
                >
                  <HugeiconsIcon
                    icon={isSaving ? Loading03Icon : FloppyDiskIcon}
                    size={14}
                    className={isSaving ? "animate-spin" : ""}
                  />
                  {isSaving ? "Saving..." : "Save"}
                </button>
              </div>
            </div>

            <div className="flex-1 overflow-y-auto px-6 pt-5 pb-20 flex flex-col gap-5 min-h-0">
              <div className="space-y-1.5 shrink-0">
                <label className="text-xs font-medium uppercase tracking-wider text-muted-foreground">
                  Card Name
                </label>
                <input
                  type="text"
                  value={editForm.title}
                  onChange={(e) =>
                    setEditForm({ ...editForm, title: e.target.value })
                  }
                  placeholder="e.g., Personal Visa"
                  className="w-full rounded-lg px-3 py-2.5 text-sm outline-none bg-muted text-foreground placeholder:text-muted-foreground/50 transition-colors border border-border focus:border-primary"
                />
              </div>

              <div className="space-y-1.5 shrink-0">
                <label className="text-xs font-medium uppercase tracking-wider text-muted-foreground">
                  Card Number
                </label>
                <input
                  type="text"
                  value={editForm.card_number}
                  onChange={(e) =>
                    setEditForm({ ...editForm, card_number: e.target.value })
                  }
                  placeholder="1234 5678 9012 3456"
                  className="w-full rounded-lg px-3 py-2.5 text-sm outline-none bg-muted text-foreground placeholder:text-muted-foreground/50 transition-colors border border-border focus:border-primary font-mono"
                />
              </div>

              <div className="space-y-1.5 shrink-0">
                <label className="text-xs font-medium uppercase tracking-wider text-muted-foreground">
                  Cardholder Name
                </label>
                <input
                  type="text"
                  value={editForm.cardholder_name}
                  onChange={(e) =>
                    setEditForm({
                      ...editForm,
                      cardholder_name: e.target.value,
                    })
                  }
                  placeholder="JOHN DOE"
                  className="w-full rounded-lg px-3 py-2.5 text-sm outline-none bg-muted text-foreground placeholder:text-muted-foreground/50 transition-colors border border-border focus:border-primary uppercase"
                />
              </div>

              <div className="grid grid-cols-2 gap-4 shrink-0">
                <div className="space-y-1.5">
                  <label className="text-xs font-medium uppercase tracking-wider text-muted-foreground">
                    Expiry Date
                  </label>
                  <input
                    type="text"
                    value={editForm.expiry_date}
                    onChange={(e) =>
                      setEditForm({ ...editForm, expiry_date: e.target.value })
                    }
                    placeholder="MM/YY"
                    maxLength={5}
                    className="w-full rounded-lg px-3 py-2.5 text-sm outline-none bg-muted text-foreground placeholder:text-muted-foreground/50 transition-colors border border-border focus:border-primary font-mono"
                  />
                </div>
                <div className="space-y-1.5">
                  <label className="text-xs font-medium uppercase tracking-wider text-muted-foreground">
                    CVV
                  </label>
                  <input
                    type="text"
                    value={editForm.cvv}
                    onChange={(e) =>
                      setEditForm({ ...editForm, cvv: e.target.value })
                    }
                    placeholder="123"
                    maxLength={4}
                    className="w-full rounded-lg px-3 py-2.5 text-sm outline-none bg-muted text-foreground placeholder:text-muted-foreground/50 transition-colors border border-border focus:border-primary font-mono"
                  />
                </div>
              </div>
            </div>
          </>
        ) : selectedCard ? (
          <>
            <div className="px-6 py-4 shrink-0 flex items-center gap-4 border-b border-border">
              <div className="w-11 h-11 rounded-xl flex items-center justify-center flex-shrink-0 bg-primary/10">
                <HugeiconsIcon
                  icon={CreditCardIcon}
                  size={20}
                  className="text-primary"
                />
              </div>
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2">
                  <h1 className="text-base font-semibold truncate text-foreground">
                    {selectedCard.title}
                  </h1>
                  {selectedCard.favorite && (
                    <HugeiconsIcon
                      icon={StarIcon}
                      size={14}
                      className="text-primary shrink-0"
                    />
                  )}
                </div>
                <div className="flex items-center gap-3 mt-0.5">
                  <div className="flex items-center gap-1">
                    <HugeiconsIcon
                      icon={Clock01Icon}
                      size={11}
                      className="text-muted-foreground/50"
                    />
                    <span className="text-xs text-muted-foreground">
                      {formatDate(selectedCard.updated_at)}
                    </span>
                  </div>
                </div>
              </div>
              <div className="flex items-center gap-0.5 flex-shrink-0">
                <button
                  title="Edit"
                  onClick={() => handleEdit(selectedCard)}
                  className="w-8 h-8 flex items-center justify-center rounded-lg transition-colors text-muted-foreground hover:bg-muted hover:text-foreground"
                >
                  <HugeiconsIcon icon={Edit02Icon} size={16} />
                </button>
                <button
                  title="Delete"
                  onClick={() => setCardToDelete(selectedCard)}
                  className="w-8 h-8 flex items-center justify-center rounded-lg transition-colors text-muted-foreground hover:bg-destructive/10 hover:text-destructive"
                >
                  <HugeiconsIcon icon={Delete02Icon} size={16} />
                </button>
              </div>
            </div>

            <div className="flex-1 overflow-y-auto px-6 pt-5 pb-20 space-y-6">
              <div className="bg-gradient-to-br from-primary to-primary/40 rounded-2xl p-6 text-primary-foreground shadow-lg">
                <div className="flex items-start justify-between mb-8">
                  <HugeiconsIcon
                    icon={CreditCardIcon}
                    size={32}
                    className="opacity-80"
                  />
                  <span className="text-sm font-medium opacity-80 uppercase tracking-wider">
                    {getCardBrand(selectedCard.card_number)}
                  </span>
                </div>
                <div className="mb-6">
                  <p className="text-2xl font-mono tracking-wider drop-shadow-sm">
                    {showCardNumber
                      ? selectedCard.card_number
                      : maskCardNumber(selectedCard.card_number)}
                  </p>
                </div>
                <div className="flex items-end justify-between">
                  <div>
                    <p className="text-xs opacity-70 mb-1">Cardholder</p>
                    <p className="font-medium uppercase tracking-wide">
                      {selectedCard.cardholder_name || "N/A"}
                    </p>
                  </div>
                  <div>
                    <p className="text-xs opacity-70 mb-1">Expires</p>
                    <p className="font-medium font-mono">
                      {selectedCard.expiry_date || "N/A"}
                    </p>
                  </div>
                </div>
              </div>

              <div className="space-y-4">
                <div className="space-y-1.5">
                  <label className="text-xs font-medium uppercase tracking-wider text-muted-foreground">
                    Card Number
                  </label>
                  <div className="flex items-center gap-2">
                    <div className="flex-1 bg-muted border border-border rounded-lg px-4 py-3 text-sm font-mono text-foreground">
                      {showCardNumber
                        ? selectedCard.card_number
                        : maskCardNumber(selectedCard.card_number)}
                    </div>
                    <button
                      onClick={() => setShowCardNumber(!showCardNumber)}
                      className="w-11 h-11 flex items-center justify-center rounded-lg bg-muted border border-border hover:bg-muted/80 transition-colors text-muted-foreground hover:text-foreground"
                    >
                      <HugeiconsIcon
                        icon={showCardNumber ? ViewOffSlashIcon : ViewIcon}
                        size={18}
                      />
                    </button>
                    <button
                      onClick={() =>
                        handleCopy(selectedCard.card_number, "card_number")
                      }
                      className={`w-11 h-11 flex items-center justify-center rounded-lg border transition-all ${
                        copiedField === "card_number"
                          ? "bg-primary/10 border-primary/20 text-primary"
                          : "bg-muted border-border hover:bg-muted/80 text-muted-foreground hover:text-foreground"
                      }`}
                    >
                      <HugeiconsIcon
                        icon={
                          copiedField === "card_number"
                            ? CheckmarkCircle01Icon
                            : Copy01Icon
                        }
                        size={18}
                        className={
                          copiedField === "card_number" ? "scale-110" : ""
                        }
                      />
                    </button>
                  </div>
                </div>

                <div className="space-y-1.5">
                  <label className="text-xs font-medium uppercase tracking-wider text-muted-foreground">
                    Cardholder Name
                  </label>
                  <div className="flex items-center gap-2">
                    <div className="flex-1 bg-muted border border-border rounded-lg px-4 py-3 text-sm text-foreground uppercase">
                      {selectedCard.cardholder_name || "N/A"}
                    </div>
                    <button
                      onClick={() =>
                        handleCopy(selectedCard.cardholder_name, "cardholder")
                      }
                      className={`w-11 h-11 flex items-center justify-center rounded-lg border transition-all ${
                        copiedField === "cardholder"
                          ? "bg-primary/10 border-primary/20 text-primary"
                          : "bg-muted border-border hover:bg-muted/80 text-muted-foreground hover:text-foreground"
                      }`}
                    >
                      <HugeiconsIcon
                        icon={
                          copiedField === "cardholder"
                            ? CheckmarkCircle01Icon
                            : Copy01Icon
                        }
                        size={18}
                        className={
                          copiedField === "cardholder" ? "scale-110" : ""
                        }
                      />
                    </button>
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-1.5">
                    <label className="text-xs font-medium uppercase tracking-wider text-muted-foreground">
                      Expiry Date
                    </label>
                    <div className="bg-muted border border-border rounded-lg px-4 py-3 text-sm font-mono text-foreground">
                      {selectedCard.expiry_date || "N/A"}
                    </div>
                  </div>
                  <div className="space-y-1.5">
                    <label className="text-xs font-medium uppercase tracking-wider text-muted-foreground">
                      CVV
                    </label>
                    <div className="flex items-center gap-2">
                      <div className="flex-1 bg-muted border border-border rounded-lg px-4 py-3 text-sm font-mono text-foreground">
                        {showCVV ? selectedCard.cvv : "•••"}
                      </div>
                      <button
                        onClick={() => setShowCVV(!showCVV)}
                        className="w-11 h-11 flex items-center justify-center rounded-lg bg-muted border border-border hover:bg-muted/80 transition-colors text-muted-foreground hover:text-foreground shrink-0"
                      >
                        <HugeiconsIcon
                          icon={showCVV ? ViewOffSlashIcon : ViewIcon}
                          size={18}
                        />
                      </button>
                      <button
                        onClick={() => handleCopy(selectedCard.cvv, "cvv")}
                        className={`w-11 h-11 flex items-center justify-center rounded-lg border transition-all shrink-0 ${
                          copiedField === "cvv"
                            ? "bg-primary/10 border-primary/20 text-primary"
                            : "bg-muted border-border hover:bg-muted/80 text-muted-foreground hover:text-foreground"
                        }`}
                      >
                        <HugeiconsIcon
                          icon={
                            copiedField === "cvv"
                              ? CheckmarkCircle01Icon
                              : Copy01Icon
                          }
                          size={18}
                          className={copiedField === "cvv" ? "scale-110" : ""}
                        />
                      </button>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </>
        ) : (
          <div className="flex-1 flex flex-col items-center justify-center gap-4">
            <div className="w-16 h-16 rounded-2xl flex items-center justify-center bg-muted">
              <HugeiconsIcon
                icon={CreditCardIcon}
                size={28}
                className="text-muted-foreground/40"
              />
            </div>
            <div className="text-center">
              <p className="text-sm font-medium mb-1 text-foreground">
                Select a card
              </p>
              <p className="text-xs text-muted-foreground max-w-xs mx-auto">
                Choose a credit card from the list to view or edit its details.
              </p>
            </div>
            <button
              onClick={handleCreate}
              className="flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium text-primary-foreground transition-colors mt-1 bg-primary hover:opacity-90"
            >
              <HugeiconsIcon icon={PlusSignIcon} size={14} />
              New card
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
