import codecs

def replace_in_file(filepath, replacements):
    try:
        content = codecs.open(filepath, 'r', 'utf-8').read()
        for old, new in replacements:
            content = content.replace(old, new)
        codecs.open(filepath, 'w', 'utf-8').write(content)
        print(f"Updated {filepath}")
    except Exception as e:
        print(f"Error {filepath}: {e}")

replacements_popup = [
    ('document.querySelectorAll(".credential-item")', 'document.querySelectorAll("[data-id]")'),
    ('document.querySelector(".strength-badge")', 'document.getElementById("strength-badge")'),
    ('document.querySelectorAll(".copy-btn")', 'document.querySelectorAll("[data-copy]")'),
    ('document.querySelector(".vk-dropdown-menu")', 'document.getElementById("vk-dropdown-menu")'),
    ('"absolute top-full right-0 mt-1', 'id="vk-dropdown-menu";\\n  dropdown.className =\\n    "absolute top-full right-0 mt-1'),
    ('dropdown.querySelectorAll(".vk-dropdown-item")', 'dropdown.querySelectorAll("[data-action]")'),
    ('document.querySelector(".popup-notification")', 'document.getElementById("popup-notification")'),
    ('"fixed bottom-5 left-1/2', 'id="popup-notification";\\n  notification.className =\\n    "fixed bottom-5 left-1/2'),
    ('notification.classList.add("fade-out")', 'notification.classList.add("animate-[notification-fade-out_0.2s_ease-in_forwards]")'),
    # Restoring the CSS classes to dynamic elements to make sure querySelectors wouldn't break, though we are fixing them directly.
]

replace_in_file('popup.js', replacements_popup)

replacements_notes = [
    ('document.querySelectorAll(".note-item")', 'document.querySelectorAll("[data-id]")'),
]
replace_in_file('notes.js', replacements_notes)

replacements_cards = [
    ('document.querySelectorAll(".card-item")', 'document.querySelectorAll("[data-id]")'),
    ('document.querySelectorAll("[data-copy-card]")', 'document.querySelectorAll("[data-copy-card]")'),
]
replace_in_file('cards.js', replacements_cards)

# Also fix the IDs in popup.html directly via script!
html = codecs.open("popup.html", 'r', 'utf-8').read()
html = html.replace('class="text-[11px] px-2 py-1 rounded-[4px] font-medium tracking-wide good"', 'id="strength-badge" class="text-[11px] px-2 py-1 rounded-[4px] font-medium tracking-wide good"')
html = html.replace('class="bg-transparent border-none p-1 cursor-pointer text-[var(--vk-text-tertiary)] flex items-center justify-center hover:text-[var(--vk-accent-blue)] hover:bg-[var(--vk-accent-blue)]/10 rounded-[var(--vk-radius-sm)] transition-colors shrink-0"\\n                        data-copy=', 'class="bg-transparent border-none p-1 cursor-pointer text-[var(--vk-text-tertiary)] flex items-center justify-center hover:text-[var(--vk-accent-blue)] hover:bg-[var(--vk-accent-blue)]/10 rounded-[var(--vk-radius-sm)] transition-colors shrink-0"\\n                        data-copy=')

codecs.open("popup.html", 'w', 'utf-8').write(html)
