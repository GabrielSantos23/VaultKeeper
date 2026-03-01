import { useState, useMemo } from "react";
import {
  Search01Icon,
  File02Icon,
  PlusSignIcon,
  StarIcon,
  LockPasswordIcon,
  Edit02Icon,
  Delete02Icon,
  Copy01Icon,
  CheckmarkCircle01Icon,
  FloppyDiskIcon,
  Cancel01Icon,
  Clock01Icon,
  TextBoldIcon,
  TextItalicIcon,
  TextUnderlineIcon,
  Heading01Icon,
  Heading02Icon,
  ListViewIcon,
  LeftToRightListNumberIcon,
  QuoteDownIcon,
  Inequality02Icon,
  ArrowTurnBackwardIcon,
  ArrowTurnForwardIcon,
  Loading03Icon,
} from "@hugeicons/core-free-icons";
import { HugeiconsIcon } from "@hugeicons/react";
import { useVaultStore, SecureNote } from "../stores/vaultStore";
import { writeText } from "@tauri-apps/plugin-clipboard-manager";
import { useEditor, EditorContent } from "@tiptap/react";
import StarterKit from "@tiptap/starter-kit";
import Underline from "@tiptap/extension-underline";
import Placeholder from "@tiptap/extension-placeholder";

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

function ToolbarButton({
  onClick,
  active = false,
  disabled = false,
  title,
  icon,
}: {
  onClick: () => void;
  active?: boolean;
  disabled?: boolean;
  title: string;
  icon: React.ComponentType<any>;
}) {
  return (
    <button
      type="button"
      title={title}
      onClick={onClick}
      disabled={disabled}
      className={`w-7 h-7 flex items-center justify-center rounded-md transition-all disabled:opacity-30 ${
        active
          ? "bg-[color-mix(in_oklch,var(--primary)_15%,transparent)] text-primary"
          : "bg-transparent text-muted-foreground"
      }`}
    >
      <HugeiconsIcon icon={icon} size={14} />
    </button>
  );
}

function ToolbarDivider() {
  return <div className="w-px h-4 mx-0.5 bg-border shrink-0" />;
}

function NoteEditor({
  content,
  onChange,
}: {
  content: string;
  onChange: (html: string) => void;
}) {
  const [isReady, setIsReady] = useState(false);

  const editor = useEditor({
    extensions: [
      StarterKit,
      Underline,
      Placeholder.configure({
        placeholder: "Enter your secure note content…",
      }),
    ],
    content,
    onUpdate: ({ editor }) => {
      onChange(editor.getHTML());
    },
    onSelectionUpdate: () => setIsReady((prev) => !prev),
    onTransaction: () => setIsReady((prev) => !prev),
    editorProps: {
      attributes: {
        class: "outline-none min-h-[280px] tiptap-editor",
      },
    },
  });

  if (!editor) return null;

  return (
    <div className="flex flex-col rounded-lg overflow-hidden flex-1 min-h-0 border border-border">
      <div className="flex items-center gap-0.5 px-2 py-1.5 flex-wrap shrink-0 bg-background border-b border-border">
        <ToolbarButton
          title="Bold"
          icon={TextBoldIcon}
          onClick={() => editor.chain().focus().toggleBold().run()}
          active={editor.isActive("bold")}
        />
        <ToolbarButton
          title="Italic"
          icon={TextItalicIcon}
          onClick={() => editor.chain().focus().toggleItalic().run()}
          active={editor.isActive("italic")}
        />
        <ToolbarButton
          title="Underline"
          icon={TextUnderlineIcon}
          onClick={() => editor.chain().focus().toggleUnderline().run()}
          active={editor.isActive("underline")}
        />
        <ToolbarDivider />
        <ToolbarButton
          title="Heading 1"
          icon={Heading01Icon}
          onClick={() =>
            editor.chain().focus().toggleHeading({ level: 1 }).run()
          }
          active={editor.isActive("heading", { level: 1 })}
        />
        <ToolbarButton
          title="Heading 2"
          icon={Heading02Icon}
          onClick={() =>
            editor.chain().focus().toggleHeading({ level: 2 }).run()
          }
          active={editor.isActive("heading", { level: 2 })}
        />
        <ToolbarDivider />
        <ToolbarButton
          title="Bullet list"
          icon={ListViewIcon}
          onClick={() => editor.chain().focus().toggleBulletList().run()}
          active={editor.isActive("bulletList")}
        />
        <ToolbarButton
          title="Numbered list"
          icon={LeftToRightListNumberIcon}
          onClick={() => editor.chain().focus().toggleOrderedList().run()}
          active={editor.isActive("orderedList")}
        />
        <ToolbarDivider />
        <ToolbarButton
          title="Blockquote"
          icon={QuoteDownIcon}
          onClick={() => editor.chain().focus().toggleBlockquote().run()}
          active={editor.isActive("blockquote")}
        />
        <ToolbarButton
          title="Horizontal rule"
          icon={Inequality02Icon}
          onClick={() => editor.chain().focus().setHorizontalRule().run()}
        />
        <ToolbarDivider />
        <ToolbarButton
          title="Undo"
          icon={ArrowTurnBackwardIcon}
          onClick={() => editor.chain().focus().undo().run()}
          disabled={!editor.can().undo()}
        />
        <ToolbarButton
          title="Redo"
          icon={ArrowTurnForwardIcon}
          onClick={() => editor.chain().focus().redo().run()}
          disabled={!editor.can().redo()}
        />
      </div>
      <div
        className="flex-1 overflow-y-auto px-4 py-3 bg-muted cursor-text"
        onClick={() => editor.chain().focus().run()}
      >
        <EditorContent editor={editor} />
      </div>
    </div>
  );
}

export function SecureNotesPage() {
  const [searchQuery, setSearchQuery] = useState("");
  const [searchFocused, setSearchFocused] = useState(false);
  const [selectedNote, setSelectedNote] = useState<SecureNote | null>(null);
  const [isEditing, setIsEditing] = useState(false);
  const [isCreating, setIsCreating] = useState(false);
  const [copiedField, setCopiedField] = useState<string | null>(null);
  const [isSaving, setIsSaving] = useState(false);
  const [noteToDelete, setNoteToDelete] = useState<SecureNote | null>(null);

  const [editForm, setEditForm] = useState({
    title: "",
    content: "",
    folder_id: undefined as number | undefined,
  });

  const secureNotes = useVaultStore((state) => state.secureNotes);
  const folders = useVaultStore((state) => state.folders);
  const addSecureNote = useVaultStore((state) => state.addSecureNote);
  const updateSecureNote = useVaultStore((state) => state.updateSecureNote);
  const deleteSecureNote = useVaultStore((state) => state.deleteSecureNote);

  const filteredNotes = useMemo(() => {
    let notes = [...secureNotes];
    if (searchQuery) {
      const query = searchQuery.toLowerCase();
      notes = notes.filter(
        (n) =>
          n.title.toLowerCase().includes(query) ||
          n.content.toLowerCase().includes(query),
      );
    }
    return notes.sort(
      (a, b) =>
        new Date(b.updated_at).getTime() - new Date(a.updated_at).getTime(),
    );
  }, [secureNotes, searchQuery]);

  const getPlainText = (html: string) =>
    html
      .replace(/<[^>]+>/g, " ")
      .replace(/\s+/g, " ")
      .trim();

  const handleCopy = async (text: string, field: string) => {
    try {
      await writeText(getPlainText(text));
      setCopiedField(field);
      setTimeout(() => setCopiedField(null), 2000);
    } catch (error) {
      console.error("Failed to copy:", error);
    }
  };

  const handleCreate = () => {
    setIsCreating(true);
    setIsEditing(false);
    setSelectedNote(null);
    setEditForm({ title: "", content: "", folder_id: undefined });
  };

  const handleEdit = (note: SecureNote) => {
    setSelectedNote(note);
    setIsEditing(true);
    setIsCreating(false);
    setEditForm({
      title: note.title,
      content: note.content,
      folder_id: note.folder_id,
    });
  };

  const handleCancel = () => {
    setIsEditing(false);
    setIsCreating(false);
    setEditForm({ title: "", content: "", folder_id: undefined });
  };

  const handleSave = async () => {
    if (!editForm.title.trim() || !editForm.content.trim() || isSaving) return;
    setIsSaving(true);
    try {
      if (isCreating) {
        await addSecureNote({
          title: editForm.title,
          content: editForm.content,
          folder_id: editForm.folder_id,
        });
      } else if (selectedNote && isEditing) {
        await updateSecureNote(selectedNote.id, {
          title: editForm.title,
          content: editForm.content,
        });
      }
      setIsEditing(false);
      setIsCreating(false);
      setSelectedNote(null);
      setEditForm({ title: "", content: "", folder_id: undefined });
    } catch (error) {
      console.error("Save failed:", error);
    } finally {
      setIsSaving(false);
    }
  };

  const confirmDelete = async () => {
    if (!noteToDelete) return;
    await deleteSecureNote(noteToDelete.id);
    if (selectedNote?.id === noteToDelete.id) {
      setSelectedNote(null);
      setIsEditing(false);
    }
    setNoteToDelete(null);
  };

  const formatDate = (dateString: string) =>
    new Date(dateString).toLocaleDateString("en-US", {
      month: "short",
      day: "numeric",
      year: "numeric",
    });

  return (
    <div className="flex-1 flex overflow-hidden bg-background h-[calc(100vh-42px)]">
      <AlertDialog
        open={!!noteToDelete}
        onOpenChange={(open) => !open && setNoteToDelete(null)}
      >
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Are you absolutely sure?</AlertDialogTitle>
            <AlertDialogDescription>
              This will permanently delete the note{" "}
              <strong className="text-foreground">
                "{noteToDelete?.title}"
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
              Delete Note
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
                Secure Notes
              </span>
            </div>
            <span className="text-xs font-medium px-2 py-0.5 rounded-full bg-primary/10 text-primary">
              {filteredNotes.length}
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
              placeholder="Search notes…"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              onFocus={() => setSearchFocused(true)}
              onBlur={() => setSearchFocused(false)}
              className={`${searchFocused ? "border-primary" : "border-border"} border w-full rounded-lg pl-8 pr-3 py-1.5 text-xs outline-none transition-colors bg-muted text-foreground placeholder:text-muted-foreground/50`}
            />
          </div>
        </div>

        <div className="flex-1 overflow-y-auto min-h-0 p-2">
          {filteredNotes.length === 0 ? (
            <div className="flex flex-col items-center justify-center h-48 gap-3">
              <div className="w-10 h-10 rounded-xl flex items-center justify-center bg-muted">
                <HugeiconsIcon
                  icon={File02Icon}
                  size={18}
                  className="text-muted-foreground/40"
                />
              </div>
              <p className="text-xs text-muted-foreground">
                {searchQuery ? "No notes found" : "No secure notes yet"}
              </p>
              {!searchQuery && (
                <button
                  onClick={handleCreate}
                  className="text-xs text-primary hover:opacity-75 transition-opacity"
                >
                  Create your first note
                </button>
              )}
            </div>
          ) : (
            <div className="space-y-0.5 pb-4">
              {filteredNotes.map((note) => {
                const selected = selectedNote?.id === note.id;
                return (
                  <button
                    key={note.id}
                    onClick={() => {
                      setSelectedNote(note);
                      setIsEditing(false);
                      setIsCreating(false);
                    }}
                    className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-left transition-all border ${
                      selected
                        ? "bg-muted border-primary/25"
                        : "bg-transparent border-transparent hover:bg-muted/50"
                    }`}
                  >
                    <div className="w-8 h-8 rounded-lg flex items-center justify-center shrink-0 bg-primary/10">
                      <HugeiconsIcon
                        icon={File02Icon}
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
                          {note.title}
                        </span>
                        {note.favorite && (
                          <HugeiconsIcon
                            icon={StarIcon}
                            size={11}
                            className="text-[var(--chart-5)] shrink-0"
                          />
                        )}
                      </div>
                      <p className="text-xs truncate text-muted-foreground leading-snug">
                        {getPlainText(note.content).slice(0, 50)}…
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
            className="w-full flex items-center justify-center gap-2 py-2 px-3 rounded-lg text-sm font-medium transition-colors bg-[color-mix(in_oklch,var(--primary)_10%,transparent)] text-primary hover:bg-[color-mix(in_oklch,var(--primary)_15%,transparent)]"
          >
            <HugeiconsIcon icon={PlusSignIcon} size={15} />
            New note
          </button>
        </div>
      </div>

      <div className="flex-1 h-full flex flex-col overflow-hidden">
        {isCreating || isEditing ? (
          <>
            <div className="px-6 py-4 shrink-0 flex items-center justify-between border-b border-border">
              <h2 className="text-sm font-semibold text-foreground">
                {isCreating ? "New Note" : "Edit Note"}
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
                    !editForm.content.trim() ||
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

            <div className="flex-1 overflow-y-auto px-6 pt-5 pb-20 flex flex-col gap-4 min-h-0">
              <div className="space-y-1.5 shrink-0">
                <label className="text-xs font-medium uppercase tracking-wider text-muted-foreground">
                  Title
                </label>
                <input
                  type="text"
                  value={editForm.title}
                  onChange={(e) =>
                    setEditForm({ ...editForm, title: e.target.value })
                  }
                  placeholder="Note title"
                  className="w-full rounded-lg px-3 py-2.5 text-sm outline-none bg-muted text-foreground placeholder:text-muted-foreground/50 transition-colors border border-border focus:border-primary"
                />
              </div>

              <div className="flex flex-col flex-1 min-h-0 space-y-1.5">
                <label className="text-xs font-medium uppercase tracking-wider text-muted-foreground shrink-0">
                  Content
                </label>
                <NoteEditor
                  content={editForm.content}
                  onChange={(html) =>
                    setEditForm((f) => ({ ...f, content: html }))
                  }
                />
              </div>
            </div>
          </>
        ) : selectedNote ? (
          <>
            <div className="px-6 py-4 shrink-0 flex items-center gap-4 border-b border-border">
              <div className="w-11 h-11 rounded-xl flex items-center justify-center flex-shrink-0 bg-[color-mix(in_oklch,var(--chart-2)_12%,transparent)]">
                <HugeiconsIcon
                  icon={File02Icon}
                  size={20}
                  className="text-[var(--chart-2)]"
                />
              </div>
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2">
                  <h1 className="text-base font-semibold truncate text-foreground">
                    {selectedNote.title}
                  </h1>
                  {selectedNote.favorite && (
                    <HugeiconsIcon
                      icon={StarIcon}
                      size={14}
                      className="text-[var(--chart-5)] shrink-0"
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
                      {formatDate(selectedNote.updated_at)}
                    </span>
                  </div>
                </div>
              </div>
              <div className="flex items-center gap-0.5 flex-shrink-0">
                <button
                  title="Copy content"
                  onClick={() => handleCopy(selectedNote.content, "content")}
                  className={`w-8 h-8 flex items-center justify-center rounded-lg transition-all ${
                    copiedField === "content"
                      ? "text-primary bg-primary/10"
                      : "text-muted-foreground hover:bg-muted hover:text-foreground"
                  }`}
                >
                  <HugeiconsIcon
                    icon={
                      copiedField === "content"
                        ? CheckmarkCircle01Icon
                        : Copy01Icon
                    }
                    size={16}
                    className={copiedField === "content" ? "scale-110" : ""}
                  />
                </button>
                <button
                  title="Edit"
                  onClick={() => handleEdit(selectedNote)}
                  className="w-8 h-8 flex items-center justify-center rounded-lg transition-colors text-muted-foreground hover:bg-muted hover:text-foreground"
                >
                  <HugeiconsIcon icon={Edit02Icon} size={16} />
                </button>
                <button
                  title="Delete"
                  onClick={() => setNoteToDelete(selectedNote)}
                  className="w-8 h-8 flex items-center justify-center rounded-lg transition-colors text-muted-foreground hover:bg-destructive/10 hover:text-destructive"
                >
                  <HugeiconsIcon icon={Delete02Icon} size={16} />
                </button>
              </div>
            </div>

            <div className="flex-1 overflow-y-auto px-6 pt-5 pb-20 space-y-4">
              <div
                className="rounded-lg px-5 py-4 bg-muted border border-border tiptap-view"
                dangerouslySetInnerHTML={{ __html: selectedNote.content }}
              />
            </div>
          </>
        ) : (
          <div className="flex-1 flex flex-col items-center justify-center gap-4">
            <div className="w-16 h-16 rounded-2xl flex items-center justify-center bg-muted">
              <HugeiconsIcon
                icon={LockPasswordIcon}
                size={28}
                className="text-muted-foreground/40"
              />
            </div>
            <div className="text-center">
              <p className="text-sm font-medium mb-1 text-foreground">
                Select a note
              </p>
              <p className="text-xs text-muted-foreground">
                Choose a note from the list to view or edit its contents.
              </p>
            </div>
            <button
              onClick={handleCreate}
              className="flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium text-primary-foreground transition-colors mt-1 bg-primary hover:opacity-90"
            >
              <HugeiconsIcon icon={PlusSignIcon} size={14} />
              New note
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
