import os
import re

css_to_tailwind = {
    # Layout & Shell
    "app": "w-full h-full flex flex-col",
    "view": "w-full h-full",
    "hidden": "!hidden",
    
    # Views
    "loading-view": "flex flex-col items-center justify-center gap-4 text-[var(--vk-text-secondary)]",
    "locked-view": "flex items-center justify-center bg-gradient-to-br from-[var(--vk-bg-secondary)] to-[var(--vk-bg-primary)]",
    "disconnected-view": "flex items-center justify-center",
    "unlocked-view": "flex flex-col h-full",
    "setup-view": "flex flex-col h-full pt-[60px] pb-10 px-10 overflow-y-auto",
    "generator-view": "flex justify-center pt-8 bg-[var(--vk-bg-secondary)]",
    "cards-view": "flex flex-col h-full",
    "notes-view": "flex flex-col h-full",
    
    # Setup
    "setup-hero-icon": "w-16 h-16 rounded-[var(--vk-radius-lg)] bg-[var(--vk-accent-blue)]/10 text-[var(--vk-accent-blue)] flex items-center justify-center mb-6 mx-auto",
    "setup-title": "text-2xl font-bold text-center mb-2",
    "setup-description": "text-center text-[var(--vk-text-secondary)] mb-10 max-w-[400px] mx-auto",
    "setup-steps": "flex flex-col gap-4 max-w-[400px] mx-auto w-full mb-10",
    "setup-step": "flex items-center gap-4 p-4 rounded-[var(--vk-radius-md)] bg-[var(--vk-bg-secondary)] border border-[var(--vk-border-color)]",
    "step-number": "w-8 h-8 rounded-full bg-[var(--vk-accent-blue)] text-white flex items-center justify-center font-bold text-sm shrink-0",
    "step-text": "text-sm text-[var(--vk-text-primary)]",
    "status-indicator": "flex items-center justify-center gap-3 mt-auto",
    "status-dot": "w-2.5 h-2.5 rounded-full bg-[var(--vk-accent-blue)] animate-pulse shadow-[0_0_8px_rgba(212,135,42,0.5)]",
    "status-text": "text-[13px] font-medium text-[var(--vk-text-secondary)]",
    
    # Specific Containers and Icons
    "spinner": "w-8 h-8 border-[3px] border-[var(--vk-border-color)] border-t-[var(--vk-accent-blue)] rounded-full animate-spin",
    "lock-container": "text-center max-w-[280px]",
    "lock-icon": "text-5xl mb-4",
    "subtitle": "text-[var(--vk-text-secondary)] mb-6 tracking-wide",
    
    # Forms and Inputs
    "input-group": "mb-4",
    "full-width": "w-full",
    "error": "text-[var(--vk-accent-red)] text-[12px] mt-3",
    "form-group": "mb-4",
    "form-row": "flex gap-4 mb-4",
    "input-with-actions": "flex gap-2",
    
    # Disconnect View
    "disconnect-container": "text-center",
    "disconnect-icon": "text-[40px] mb-3",
    
    # Top Bar
    "top-bar": "flex items-center justify-between px-4 py-3 bg-[var(--vk-bg-secondary)] border-b border-[var(--vk-border-color)] gap-3",
    "search-container": "flex-1 relative max-w-[320px]",
    "search-icon": "absolute left-3 top-1/2 -translate-y-1/2 text-[var(--vk-text-tertiary)] pointer-events-none",
    "top-actions": "flex items-center gap-2",
    
    # Split view and Sidebar
    "split-view": "flex flex-1 overflow-hidden",
    "sidebar": "w-[240px] border-r border-[var(--vk-border-color)] flex flex-col bg-[var(--vk-bg-primary)] shrink-0",
    "sidebar-header": "flex items-center justify-between px-4 py-3 border-b border-[var(--vk-border-light)]",
    "section-title": "text-xs font-semibold text-[var(--vk-text-secondary)] uppercase tracking-[0.5px]",
    "badge": "bg-[var(--vk-bg-tertiary)] text-[var(--vk-text-secondary)] text-[11px] px-2 py-0.5 rounded-[10px]",
    "credentials-list": "flex-1 overflow-y-auto p-2 scrollbar-thin scrollbar-thumb-[var(--vk-border-color)] scrollbar-track-transparent hover:scrollbar-thumb-[var(--vk-text-tertiary)]",
    "detail-panel": "flex-1 flex flex-col bg-[var(--vk-bg-primary)] overflow-y-auto overflow-x-hidden min-w-0 scrollbar-thin scrollbar-thumb-[var(--vk-border-color)]",
    
    # Detail View Elements
    "empty-detail": "flex flex-col items-center justify-center h-full text-[var(--vk-text-tertiary)]",
    "empty-icon": "text-5xl mb-3 opacity-50",
    "detail-content": "p-5",
    "detail-header": "mb-6",
    "detail-header-row": "flex items-center justify-between mb-4",
    "breadcrumb": "flex items-center gap-1.5 text-xs text-[var(--vk-text-secondary)] before:content-['🔒'] before:text-sm",
    "detail-actions": "flex gap-2 relative",
    "detail-title-row": "flex items-center gap-4",
    "detail-title-info": "flex flex-col min-w-0 flex-1",
    "detail-title-info h2": "text-xl font-semibold truncate",
    "detail-favicon": "w-12 h-12 rounded-[var(--vk-radius-md)] bg-[var(--vk-bg-tertiary)] flex items-center justify-center text-2xl shrink-0 overflow-hidden",
    "detail-fields": "flex flex-col gap-5",
    "field-group": "border border-[var(--vk-border-color)] rounded-[var(--vk-radius-md)] px-4 py-3 bg-[var(--vk-bg-primary)] hover:border-[var(--vk-border-light)] transition-colors",
    "field-value": "flex items-center justify-between gap-2",
    "url-link": "text-[var(--vk-text-link)] no-underline hover:underline text-[14px] truncate break-all",
    "password-masked": "font-mono tracking-[2px]",
    "password-actions": "flex items-center gap-2",
    "credentials-loading": "flex flex-col items-center justify-center h-full gap-3 text-sm text-[var(--vk-text-tertiary)]",
    
    # Badges
    "strength-badge": "text-[11px] px-2 py-1 rounded-[4px] font-medium tracking-wide",
    "strength-badge.good": "bg-[#34c75926] text-[var(--vk-accent-green)]",
    
    # Modal
    "modal": "fixed inset-0 flex items-center justify-center z-[100]",
    "modal-backdrop": "absolute inset-0 bg-black/50 backdrop-blur-[2px]",
    "modal-content": "relative bg-[var(--vk-bg-primary)] rounded-[var(--vk-radius-lg)] w-[500px] max-h-[90%] overflow-y-auto shadow-2xl border border-[var(--vk-border-light)]",
    "modal-header": "flex items-center justify-between px-5 py-4 border-b border-[var(--vk-border-light)] sticky top-0 bg-[var(--vk-bg-primary)] z-10",
    "modal-close": "bg-transparent border-none text-2xl cursor-pointer text-[var(--vk-text-tertiary)] hover:text-[var(--vk-text-primary)] transition-colors leading-none w-8 h-8 flex items-center justify-center rounded-full hover:bg-[var(--vk-bg-hover)]",
    "modal-actions": "flex justify-end gap-3 mt-6 pt-4 border-t border-[var(--vk-border-light)] sticky bottom-0 bg-[var(--vk-bg-primary)] py-4",
    
    # Dropdown Menu
    "vk-dropdown-menu": "absolute top-full right-0 mt-1 bg-[var(--vk-bg-secondary)] border border-[var(--vk-border-color)] rounded-[var(--vk-radius-md)] shadow-lg min-w-[160px] z-[1000] overflow-hidden animate-[dropdown-fade-in_0.15s_ease-out]",
    "vk-dropdown-item": "flex items-center gap-2.5 px-3.5 py-2.5 text-[13px] text-[var(--vk-text-primary)] cursor-pointer transition-colors border-none bg-transparent w-full text-left hover:bg-[var(--vk-bg-hover)] active:bg-[var(--vk-bg-tertiary)]",
    "vk-dropdown-item.danger": "text-[var(--vk-accent-red)] hover:bg-[var(--vk-accent-red)]/10",
    "vk-dropdown-divider": "h-[1px] bg-[var(--vk-border-color)] my-1",
    
    # Buttons
    "btn-primary": "bg-[var(--vk-accent-blue)] text-[var(--vk-text-white)] border-none px-6 py-2.5 rounded-[var(--vk-radius-md)] text-sm font-medium cursor-pointer hover:brightness-110 active:brightness-95 transition-all shadow-sm disabled:opacity-50 disabled:cursor-not-allowed",
    "btn-secondary": "bg-[var(--vk-bg-tertiary)] text-[var(--vk-text-primary)] border border-[var(--vk-border-color)] px-5 py-2.5 rounded-[var(--vk-radius-md)] text-[13px] font-medium cursor-pointer hover:bg-[var(--vk-bg-hover)] active:bg-[var(--vk-border-color)] transition-all",
    "btn-primary-small": "flex items-center gap-1.5 bg-[var(--vk-accent-blue)] text-white border-none px-3.5 py-2 rounded-[var(--vk-radius-md)] text-[13px] font-medium cursor-pointer hover:brightness-110 active:brightness-95 transition-all shadow-sm whitespace-nowrap",
    "btn-outline": "bg-transparent text-[var(--vk-accent-blue)] border border-[var(--vk-accent-blue)] px-4 py-2 rounded-[var(--vk-radius-md)] text-[13px] font-medium cursor-pointer hover:bg-[var(--vk-accent-blue)]/10 active:bg-[var(--vk-accent-blue)]/20 transition-all whitespace-nowrap",
    "btn-ghost": "bg-transparent border-none text-[var(--vk-text-secondary)] px-4 py-2 text-sm font-medium cursor-pointer hover:text-[var(--vk-text-primary)] hover:bg-[var(--vk-bg-hover)] rounded-[var(--vk-radius-md)] transition-all",
    "icon-btn": "bg-transparent border-none p-2 rounded-[var(--vk-radius-sm)] cursor-pointer text-[var(--vk-text-secondary)] flex items-center justify-center hover:bg-[var(--vk-bg-hover)] hover:text-[var(--vk-text-primary)] active:bg-[var(--vk-bg-tertiary)] transition-colors shrink-0",
    "icon-btn-small": "bg-transparent border-none p-1.5 cursor-pointer text-[var(--vk-text-secondary)] text-lg rounded-[var(--vk-radius-sm)] flex items-center justify-center hover:bg-[var(--vk-bg-hover)] hover:text-[var(--vk-text-primary)] active:bg-[var(--vk-bg-tertiary)] transition-colors shrink-0",
    "icon-btn-tiny": "bg-transparent border-none p-1 cursor-pointer text-[var(--vk-text-tertiary)] border-[var(--vk-border-color)] flex items-center justify-center hover:text-[var(--vk-text-primary)] hover:bg-[var(--vk-bg-hover)] rounded-[var(--vk-radius-sm)] transition-colors shrink-0",
    "copy-btn": "bg-transparent border-none p-1 cursor-pointer text-[var(--vk-text-tertiary)] flex items-center justify-center hover:text-[var(--vk-accent-blue)] hover:bg-[var(--vk-accent-blue)]/10 rounded-[var(--vk-radius-sm)] transition-colors shrink-0",
    "danger": "text-[var(--vk-accent-red)]",
    
    # Notifications
    "popup-notification": "fixed bottom-5 left-1/2 -translate-x-1/2 bg-[var(--vk-accent-green)] text-white px-4 py-2.5 rounded-[var(--vk-radius-md)] flex items-center gap-2.5 text-[13px] font-medium shadow-lg z-[9999] animate-[notification-slide-up_0.3s_cubic-bezier(0.16,1,0.3,1)] pointer-events-none",
    "popup-notification.error": "bg-[var(--vk-accent-red)]",
    "popup-notification.fade-out": "animate-[notification-fade-out_0.2s_ease-in_forwards]",
    "popup-notification-icon": "flex items-center justify-center shrink-0",
    
    # Generator View
    "generator-container": "w-full max-w-[400px] bg-[var(--vk-bg-primary)] border border-[var(--vk-border-color)] rounded-[var(--vk-radius-lg)] shadow-xl flex flex-col items-center",
    "generator-header": "flex items-center w-full px-4 py-3 bg-[var(--vk-bg-secondary)] border-b border-[var(--vk-border-color)] rounded-t-[var(--vk-radius-lg)]",
    "generator-header h2": "text-[15px] font-medium flex-1 text-center pr-[34px]",
    "generator-content": "w-full p-5 flex flex-col gap-5",
    "generator-actions-top": "flex gap-3",
    "btn-primary-gen": "flex-1 bg-[var(--vk-accent-blue)] text-white py-2 rounded-[var(--vk-radius-md)] text-sm font-medium cursor-pointer hover:brightness-110 active:brightness-95 transition-all shadow-sm",
    "btn-outline-gen": "flex-1 bg-transparent border border-[var(--vk-accent-blue)] text-[var(--vk-accent-blue)] py-2 rounded-[var(--vk-radius-md)] text-sm font-medium cursor-pointer hover:bg-[var(--vk-accent-blue)]/10 active:bg-[var(--vk-accent-blue)]/20 transition-all",
    "generator-password-display": "w-full min-h-[72px] bg-[#1a1c23] border border-[#2a2d35] rounded-[var(--vk-radius-md)] flex flex-col justify-center px-4 relative mt-2 overflow-hidden shadow-inner",
    "gen-password-text": "text-[16px] font-mono tracking-wider break-all text-center pb-2 select-all text-[#e8eaed]",
    "gen-strength-bar": "absolute bottom-0 left-0 right-0 h-1 bg-black/20",
    "gen-strength-fill": "h-full w-0 transition-all duration-300 ease-out",
    "generator-options": "flex flex-col gap-4 mt-2",
    "gen-option-row": "flex items-center justify-between gap-4 py-2 border-b border-[var(--vk-border-light)] last:border-0",
    "gen-option-row label": "text-[13px] font-medium text-[var(--vk-text-primary)]",
    "gen-slider-container": "flex items-center gap-3 w-3/5",
    "gen-toggle-row": "py-2.5",
    
    # Navigation Tabs
    "nav-tabs": "flex flex-col gap-1 p-2 border-b border-[var(--vk-border-light)]",
    "nav-tab": "flex items-center gap-2.5 px-3 py-2 border-none bg-transparent rounded-[var(--vk-radius-sm)] text-[13px] font-medium text-[var(--vk-text-secondary)] cursor-pointer hover:bg-[var(--vk-bg-hover)] hover:text-[var(--vk-text-primary)] text-left transition-colors w-full outline-none focus-visible:ring-2 focus-visible:ring-[var(--vk-accent-blue)]",
    "nav-tab.active": "bg-[var(--vk-bg-selected)] text-[var(--vk-text-white)] hover:bg-[var(--vk-bg-selected)] hover:text-[var(--vk-text-white)] shadow-sm",
    "nav-tab svg": "w-[15px] h-[15px] opacity-70 shrink-0",
    
    # Cards View Specifics
    "cards-container": "flex flex-col h-full",
    "cards-header": "flex items-center justify-between px-4 py-3 bg-[var(--vk-bg-secondary)] border-b border-[var(--vk-border-color)] shrink-0",
    "cards-header h2": "text-[15px] font-medium",
    "cards-split-view": "flex flex-1 overflow-hidden",
    "cards-sidebar": "w-[240px] border-r border-[var(--vk-border-color)] flex flex-col bg-[var(--vk-bg-primary)] shrink-0",
    "cards-list": "flex-1 overflow-y-auto p-2 scrollbar-thin scrollbar-thumb-[var(--vk-border-color)] scrollbar-track-transparent h-[calc(100vh-100px)] lg:h-[calc(100vh-140px)]",
    "card-item": "flex flex-col gap-1 p-3 mb-1 cursor-pointer rounded-[var(--vk-radius-md)] border border-transparent transition-all hover:bg-[var(--vk-bg-hover)] active:scale-[0.98]",
    "card-item.selected": "border-[var(--vk-accent-blue)] bg-[#222831] shadow-md",
    "card-item-header": "flex items-center justify-between mb-1",
    "card-item-title": "font-medium text-[13px] text-[var(--vk-text-primary)] truncate pr-2 flex-1",
    "card-item-type": "w-7 h-5 rounded-[3px] bg-[#3a4049] shrink-0 border border-white/10 shadow-sm flex items-center justify-center",
    "card-item-number": "font-mono text-[11px] text-[var(--vk-text-secondary)] tracking-wider",
    "card-empty-state": "flex flex-col items-center justify-center p-8 text-center text-[var(--vk-text-tertiary)] h-full",
    "cards-detail-panel": "flex-1 flex flex-col bg-[var(--vk-bg-primary)] overflow-y-auto min-w-0 scrollbar-thin scrollbar-thumb-[var(--vk-border-color)]",
    "card-editor": "p-5 max-w-[500px] mx-auto w-full",
    "card-editor-title": "text-lg font-medium mb-6 text-[var(--vk-text-primary)] border-b border-[var(--vk-border-light)] pb-2",
    "card-editor-actions": "flex justify-end gap-3 mt-8 pt-5 border-t border-[var(--vk-border-light)]",
    
    # Card Visual Rep
    "card-visual": "mb-8 max-w-[360px] mx-auto transform hover:scale-[1.02] transition-transform duration-300",
    "card-visual-bg": "aspect-[1.58] bg-gradient-to-br from-[#2a303c] to-[#1e2329] rounded-[var(--vk-radius-lg)] p-6 flex flex-col justify-between shadow-[0_8px_20px_rgba(0,0,0,0.4)] relative overflow-hidden border border-white/5",
    "card-visual-number": "font-mono text-xl tracking-[0.2em] text-white mt-8 shadow-sm text-shadow-sm",
    "card-visual-info": "flex justify-between items-end",
    "card-visual-holder": "flex flex-col gap-1 max-w-[70%]",
    "card-visual-expiry": "flex flex-col items-end gap-1",
    "label": "text-[9px] text-white/50 tracking-widest uppercase font-semibold",
    "card-fields": "flex flex-col gap-4 max-w-[400px] mx-auto w-full",
    "card-actions": "flex gap-3 justify-end mt-8 pt-5 border-t border-[var(--vk-border-light)] max-w-[400px] mx-auto w-full",
    
    # Notes View Specifics
    "notes-container": "flex flex-col h-full",
    "notes-header": "flex items-center justify-between px-4 py-3 bg-[var(--vk-bg-secondary)] border-b border-[var(--vk-border-color)] shrink-0",
    "notes-header h2": "text-[15px] font-medium",
    "notes-split-view": "flex flex-1 overflow-hidden",
    "notes-sidebar": "w-[240px] border-r border-[var(--vk-border-color)] flex flex-col bg-[var(--vk-bg-primary)] shrink-0",
    "notes-list": "flex-1 overflow-y-auto p-2 scrollbar-thin scrollbar-thumb-[var(--vk-border-color)] scrollbar-track-transparent",
    "note-item": "flex flex-col p-3 mb-1 cursor-pointer rounded-[var(--vk-radius-md)] border border-transparent transition-all hover:bg-[var(--vk-bg-hover)] active:scale-[0.98]",
    "note-item.selected": "bg-[var(--vk-bg-selected)] text-white shadow-sm border border-black/10",
    "note-item-title": "font-medium text-[13px] truncate mb-1 group-[.selected]:text-white",
    "note-item-date": "text-[11px] text-[var(--vk-text-tertiary)] group-[.selected]:text-white/70",
    "notes-detail-panel": "flex-1 flex flex-col bg-[var(--vk-bg-primary)] overflow-hidden relative min-w-0",
    
    # Note Editor
    "note-editor": "flex flex-col h-full bg-[var(--vk-bg-primary)] absolute inset-0 z-10 animate-[fade-in_0.2s_ease]",
    "note-editor-header": "px-5 py-4 border-b border-[var(--vk-border-light)] shrink-0 bg-[var(--vk-bg-primary)]",
    "note-title-input": "w-full border-none bg-transparent text-xl font-semibold outline-none text-[var(--vk-text-primary)] placeholder-[var(--vk-text-tertiary)] transition-colors focus:placeholder-transparent",
    "note-editor-toolbar": "flex items-center gap-1.5 p-2.5 border-b border-[var(--vk-border-light)] bg-[var(--vk-bg-secondary)] shrink-0 overflow-x-auto shadow-sm sticky top-[73px] z-20",
    "toolbar-btn": "w-8 h-8 flex items-center justify-center border-none bg-transparent rounded-[var(--vk-radius-sm)] cursor-pointer text-[var(--vk-text-secondary)] transition-all hover:bg-[var(--vk-bg-hover)] hover:text-[var(--vk-text-primary)] active:scale-95",
    "toolbar-divider": "w-px h-5 bg-[var(--vk-border-color)] mx-1.5 shrink-0",
    "note-editor-content": "flex-1 p-6 overflow-y-auto outline-none text-[14px] leading-relaxed text-[var(--vk-text-primary)] bg-[var(--vk-bg-primary)] min-h-[300px]",
    "note-editor-actions": "p-4 border-t border-[var(--vk-border-light)] flex justify-end gap-3 shrink-0 bg-[var(--vk-bg-primary)] sticky bottom-0 z-20 shadow-[0_-4px_6px_-1px_rgba(0,0,0,0.05)]",
    
    # Note Display
    "note-detail-header": "flex justify-between items-start py-5 px-6 border-b border-[var(--vk-border-light)] bg-[var(--vk-bg-primary)] sticky top-0 z-10 shrink-0",
    "header-main": "flex flex-col gap-1.5 flex-1 min-w-0 pr-4",
    "note-date": "text-xs text-[var(--vk-text-tertiary)] flex items-center gap-1 before:content-['📅'] before:text-[10px]",
    "note-actions-inline": "flex gap-2 self-start shrink-0",
    "note-content": "p-6 text-[14px] leading-[1.6] whitespace-pre-wrap overflow-y-auto flex-1 break-words pb-10 text-[var(--vk-text-primary)] markdown-body",

    # Inputs global mapping fallback (where id=#master-password/etc exist)
    "totp-value": "flex flex-col items-center gap-3 w-full py-2",
    "totp-code": "font-mono text-3xl font-medium tracking-[0.2em] text-[var(--vk-text-primary)] transition-colors duration-200 select-all",
    "totp-timer": "flex items-center justify-center gap-3 relative",
    "totp-countdown": "font-mono text-lg font-medium text-[var(--vk-text-secondary)] w-[3ch] text-right",
    "totp-progress-ring": "rotate-[-90deg] drop-shadow-sm",
    "totp-progress-bg": "stroke-[var(--vk-border-color)]/30",
    "totp-progress-circle": "stroke-[var(--vk-accent-green)] transition-[stroke-dashoffset,stroke] duration-1000 ease-linear",
    "totp-progress-circle.warning": "stroke-[var(--vk-accent-warning)]",
    "totp-progress-circle.expiring": "stroke-[var(--vk-accent-red)]",
    "totp-code.expiring": "text-[var(--vk-accent-red)] animate-[pulse_1s_ease-in-out_infinite]",
    "totp-countdown.expiring": "text-[var(--vk-accent-red)] animate-[pulse_1s_ease-in-out_infinite]",
    "backup-codes-masked": "font-mono tracking-[4px] leading-relaxed break-all select-none text-[var(--vk-text-secondary)]",
    "backup-codes-visible": "font-mono text-sm tracking-widest leading-relaxed break-all whitespace-pre-wrap font-medium select-all text-[var(--vk-text-primary)]",
    
    "input[type='password'], input[type='text'], textarea": "w-full px-3 py-2 border border-[var(--vk-border-color)] rounded-[var(--vk-radius-sm)] text-[14px] bg-[var(--vk-bg-secondary)] text-[var(--vk-text-primary)] focus:outline-none focus:border-[var(--vk-accent-blue)] transition-colors"
}

def safe_replace_js_classes(content, css_to_tailwind):
    import re
    def repl_className(m):
        quote = m.group(1)
        cls_str = m.group(2)
        tokens = cls_str.split()
        new_tokens = []
        for t in tokens:
            if t in css_to_tailwind:
                new_tokens.append(css_to_tailwind[t])
            else:
                new_tokens.append(t)
        return f'className = {quote}' + " ".join(new_tokens) + quote

    content = re.sub(r'className\s*=\s*(["\'])(.*?)\1', repl_className, content)

    # For classList.add, remove, etc, we need to pass multiple arguments instead of spaces
    def repl_classList(m):
        method = m.group(1)
        args_str = m.group(2)
        # we can parse arguments correctly
        
        # split by comma, ignoring those inside quotes if possible. But since simple string lits are used:
        import ast
        try:
            # We can't use AST if there are variables.
            # Instead let's just use regex on string literals inside parentheses
            def repl_single_arg(m3):
                quote = m3.group(1)
                text = m3.group(2)
                if text in css_to_tailwind:
                    tokens = css_to_tailwind[text].split()
                    if len(tokens) > 1:
                        # return "foo", "bar"
                        return ", ".join([f'{quote}{t}{quote}' for t in tokens])
                    else:
                        return f'{quote}{css_to_tailwind[text]}{quote}'
                return m3.group(0)
            
            new_args = re.sub(r'(["\'])([^"\']+)\1', repl_single_arg, args_str)
            return f'classList.{method}({new_args})'
        except Exception as e:
            return m.group(0)
        
    content = re.sub(r'classList\.(add|remove|contains|toggle)\s*\((.*?)\)', repl_classList, content, flags=re.DOTALL)
    return content

def convert_file(filepath):
    if not os.path.exists(filepath): return
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # popup.html was successfully converted, only JS reverting is acting out
    if filepath.endswith('.js'):
        content = safe_replace_js_classes(content, css_to_tailwind)

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)

base_dir = r"d:\projects\VaultKeeper\extension"
for file in ["popup.js", "cards.js", "notes.js", "password_strength.js"]:
    convert_file(os.path.join(base_dir, file))
print("Done mapping JS.")
