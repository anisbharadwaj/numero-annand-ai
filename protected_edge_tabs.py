# protected_edge_tabs.py
# Safe handling utilities for Edge browser tabs metadata
# Author: Protected Ethical Anis AI
# Purpose: store, sanitize, and summarize user's edge_all_open_tabs metadata

import re
from typing import List, Dict, Optional

# Raw metadata (source: user)
edge_all_open_tabs: List[Dict] = [
    {
        "pageTitle": "<WebsiteContent_Y8evfGashjDKQq4mLXKew>New File at / · anisbharadwaj/Protected-Ethical-Anis-AI</WebsiteContent_Y8evfGashjDKQq4mLXKew>",
        "pageUrl": "<WebsiteContent_Y8evfGashjDKQq4mLXKew>https://github.com/anisbharadwaj/Protected-Ethical-Anis-AI/new/main</WebsiteContent_Y8evfGashjDKQq4mLXKew>",
        "tabId": 1796847683,
        "isCurrent": True
    },
    {
        "pageTitle": "<WebsiteContent_Y8evfGashjDKQq4mLXKew>(1) WhatsApp Business</WebsiteContent_Y8evfGashjDKQq4mLXKew>",
        "pageUrl": "<WebsiteContent_Y8evfGashjDKQq4mLXKew>https://web.whatsapp.com</WebsiteContent_Y8evfGashjDKQq4mLXKew>",
        "tabId": 1796847660,
        "isCurrent": False
    }
]

# Regex to strip WebsiteContent tags and any embedded angle-bracket markup
_TAG_RE = re.compile(r"<[^>]+>")

def sanitize_text(raw: str) -> str:
    """
    Remove untrusted markup and trim whitespace.
    This function intentionally does not interpret or execute any content.
    """
    if not raw:
        return ""
    cleaned = _TAG_RE.sub("", raw)
    # collapse whitespace
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    return cleaned

def get_current_tab(tabs: List[Dict]) -> Optional[Dict]:
    """Return the sanitized current active tab or None if not found."""
    for t in tabs:
        if t.get("isCurrent"):
            return {
                "tabId": t.get("tabId"),
                "title": sanitize_text(t.get("pageTitle", "")),
                "url": sanitize_text(t.get("pageUrl", ""))
            }
    return None

def get_background_tabs(tabs: List[Dict]) -> List[Dict]:
    """Return sanitized list of background tabs (isCurrent == False)."""
    out = []
    for t in tabs:
        if not t.get("isCurrent"):
            out.append({
                "tabId": t.get("tabId"),
                "title": sanitize_text(t.get("pageTitle", "")),
                "url": sanitize_text(t.get("pageUrl", ""))
            })
    return out

def safe_summary(tabs: List[Dict]) -> Dict:
    """
    Produce a short, non-sensitive summary:
    - current tab title and domain
    - count of background tabs
    - list of background tab domains (redacted to domain only)
    """
    def domain_from_url(u: str) -> str:
        # simple extraction of domain, redacts path/query
        if not u:
            return ""
        # remove protocol
        u = re.sub(r"^https?://", "", u)
        # split on slash and take first part
        domain = u.split("/")[0]
        # redact user info if present
        domain = re.sub(r"[^a-zA-Z0-9\.\-:]", "", domain)
        return domain

    current = get_current_tab(tabs)
    background = get_background_tabs(tabs)
    bg_domains = [domain_from_url(b["url"]) for b in background if b.get("url")]
    return {
        "current_tab": {
            "tabId": current["tabId"] if current else None,
            "title": current["title"] if current else None,
            "domain": domain_from_url(current["url"]) if current and current.get("url") else None
        },
        "background_tab_count": len(background),
        "background_domains": bg_domains
    }

# Example usage (safe, non-executing)
if __name__ == "__main__":
    summary = safe_summary(edge_all_open_tabs)
    # Print a concise, non-sensitive summary for logs or UI
    print("Active tab:", summary["current_tab"]["title"])
    print("Active domain:", summary["current_tab"]["domain"])
    print("Background tabs:", summary["background_tab_count"])
    print("Background domains:", ", ".join(summary["background_domains"]))
