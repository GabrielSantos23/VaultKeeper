import codecs

def fix_query_selectors(filepath):
    lines = codecs.open(filepath, 'r', 'utf-8').readlines()
    for i, line in enumerate(lines):
        # popup.html classes
        line = line.replace('querySelector(".strength-badge")', 'getElementById("strength-badge")')
        line = line.replace('querySelectorAll(".copy-btn")', 'querySelectorAll("[data-copy]")')
        
        # vk-dropdown components
        line = line.replace('querySelector(".vk-dropdown-menu")', 'getElementById("vk-dropdown-menu")')
        if 'className =' in line and 'absolute top-full right-0' in line:
            line = line.replace('className =', 'id = "vk-dropdown-menu";\n  dropdown.className =')
        line = line.replace('querySelectorAll(".vk-dropdown-item")', 'querySelectorAll("button[data-action]")')
        
        # popup-notification components
        line = line.replace('querySelector(".popup-notification")', 'getElementById("popup-notification")')
        if 'className =' in line and 'fixed bottom-5 left-1/2' in line:
            # We add ID dynamically
            line = line.replace('className =', 'id = "popup-notification";\n  notification.className =')
        
        # popup.js dynamic class manipulation fixes
        # notification fade-out class
        line = line.replace('notification.classList.add("fade-out")', 'notification.classList.add("animate-[notification-fade-out_0.2s_ease-in_forwards]")')
        
        lines[i] = line
        
    codecs.open(filepath, 'w', 'utf-8').writelines(lines)

for f in ["popup.js", "cards.js", "notes.js"]:
    fix_query_selectors(f)

# Also fix the IDs in popup.html directly via script!
html = codecs.open("popup.html", 'r', 'utf-8').read()
html = html.replace('class="text-[11px] px-2 py-1 rounded-[4px] font-medium tracking-wide good"', 'id="strength-badge" class="strength-badge text-[11px] px-2 py-1 rounded-[4px] font-medium tracking-wide good"')
html = html.replace('class="bg-transparent border-none p-1 cursor-pointer text-[var(--vk-text-tertiary)] flex items-center justify-center hover:text-[var(--vk-accent-blue)] hover:bg-[var(--vk-accent-blue)]/10 rounded-[var(--vk-radius-sm)] transition-colors shrink-0"\n                        data-copy=', 'class="bg-transparent border-none p-1 cursor-pointer text-[var(--vk-text-tertiary)] flex items-center justify-center hover:text-[var(--vk-accent-blue)] hover:bg-[var(--vk-accent-blue)]/10 rounded-[var(--vk-radius-sm)] transition-colors shrink-0"\n                        data-copy=') # Just using data-copy for everything copy button is fine.

# Just to be sure the strength-badge ID is firmly there
if 'id="strength-badge"' not in html:
    # Try different representation
    html = html.replace('Fantastic</span>', 'Fantastic</span>').replace('<span class="text-[11px]', '<span id="strength-badge" class="text-[11px]')

codecs.open("popup.html", 'w', 'utf-8').write(html)
print("Query selectors fixed.")
