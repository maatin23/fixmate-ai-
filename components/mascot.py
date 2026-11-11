"""FixMate's friendly phone character, used in the hero and on the loading screen."""

from __future__ import annotations


def mascot(uid: str = "a") -> str:
    return (
        f'<svg class="fm-mascot" viewBox="0 0 330 360" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">'
        f'<defs><linearGradient id="mb{uid}" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#ff7ab6"/>'
        f'<stop offset="1" stop-color="#b69cff"/></linearGradient></defs>'
        f'<ellipse cx="165" cy="340" rx="84" ry="12" fill="#000" opacity=".22"/>'
        f'<g class="fm-m-body">'
        f'<rect x="87" y="30" width="156" height="290" rx="46" fill="url(#mb{uid})"/>'
        f'<rect x="103" y="52" width="124" height="214" rx="32" fill="#1c1227"/>'
        f'<rect x="145" y="38" width="40" height="7" rx="3.5" fill="#1c1227" opacity=".45"/>'
        f'<g><ellipse class="fm-m-eye" cx="143" cy="136" rx="13" ry="16" fill="#fff"/>'
        f'<ellipse class="fm-m-eye" cx="187" cy="136" rx="13" ry="16" fill="#fff"/>'
        f'<circle class="fm-m-pupil" cx="146" cy="139" r="6" fill="#1c1227"/>'
        f'<circle class="fm-m-pupil" cx="190" cy="139" r="6" fill="#1c1227"/></g>'
        f'<circle cx="123" cy="172" r="9" fill="#ff7ab6" opacity=".55"/><circle cx="207" cy="172" r="9" fill="#ff7ab6" opacity=".55"/>'
        f'<path d="M147 186 Q165 206 183 186" fill="none" stroke="#5ff0c0" stroke-width="7" stroke-linecap="round"/>'
        f'<rect x="145" y="290" width="40" height="8" rx="4" fill="#fff" opacity=".6"/>'
        f'<path d="M87 196 Q58 206 56 238" stroke="#d6b8ff" stroke-width="16" stroke-linecap="round" fill="none"/>'
        f'<g class="fm-m-tool"><path d="M243 202 Q288 194 296 158" stroke="#d6b8ff" stroke-width="16" stroke-linecap="round" fill="none"/>'
        f'<g transform="translate(296 146) rotate(30)"><rect x="-6" y="-66" width="12" height="76" rx="6" fill="#ffb86b"/>'
        f'<path d="M-15 -92 A24 24 0 1 0 15 -92" fill="none" stroke="#ffb86b" stroke-width="12" stroke-linecap="round"/></g></g>'
        f'</g></svg>'
    )
