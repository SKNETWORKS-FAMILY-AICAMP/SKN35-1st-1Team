"""
정적 에셋 (SVG 일러스트)
------------------------
외부 이미지 파일 없이 인라인 SVG를 data URI로 변환해 사용한다.
배포 환경에서 이미지 경로가 깨지지 않게 하기 위함이다.

  · SCENE_URI — 홈 히어로: 분홍 해치가 택시를 몰고, 소울 프렌즈 4종이 손을 흔드는 장면
  · FACE_URI  — 사이드바 브랜드 로고용 해치 얼굴
"""

from __future__ import annotations

import base64


def _friend(cx: int, body: str, dark: str) -> str:
    """소울 프렌즈 한 명 (손 흔드는 캐릭터)."""
    wave = (f'<path d="M{cx+15} 200 q16 -8 20 -26" stroke="{body}" stroke-width="7" '
            f'fill="none" stroke-linecap="round"/>')
    return f"""
    <g>
      <ellipse cx="{cx}" cy="210" rx="19" ry="24" fill="{body}" stroke="{dark}" stroke-width="3"/>
      <path d="M{cx-16} 214 q-8 3 -9 12" stroke="{body}" stroke-width="7" fill="none" stroke-linecap="round"/>
      {wave}
      <circle cx="{cx-6}" cy="204" r="2.6" fill="#3a2b2b"/>
      <circle cx="{cx+6}" cy="204" r="2.6" fill="#3a2b2b"/>
      <circle cx="{cx-10}" cy="210" r="3.4" fill="#ff9a9a" opacity="0.55"/>
      <circle cx="{cx+10}" cy="210" r="3.4" fill="#ff9a9a" opacity="0.55"/>
      <path d="M{cx-6} 211 q6 5 12 0" stroke="#3a2b2b" stroke-width="2.4" fill="none" stroke-linecap="round"/>
      <ellipse cx="{cx-7}" cy="234" rx="6" ry="4" fill="{dark}"/>
      <ellipse cx="{cx+7}" cy="234" rx="6" ry="4" fill="{dark}"/>
    </g>"""


SCENE_SVG = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 720 300">
  <defs>
    <linearGradient id="sky" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0" stop-color="#ffe9d6"/><stop offset="1" stop-color="#e4f1ff"/>
    </linearGradient>
  </defs>
  <rect width="720" height="300" rx="24" fill="url(#sky)"/>
  <circle cx="628" cy="60" r="38" fill="#ffd98a" opacity="0.9"/>
  <g fill="#ffffff" opacity="0.92">
    <ellipse cx="120" cy="54" rx="44" ry="19"/><ellipse cx="156" cy="60" rx="30" ry="15"/>
    <ellipse cx="452" cy="40" rx="32" ry="14"/>
  </g>
  <!-- 반짝임 -->
  <g fill="#ffb84d" opacity="0.9">
    <path d="M300 44 l3 8 8 3 -8 3 -3 8 -3 -8 -8 -3 8 -3 z"/>
    <path d="M486 96 l2 6 6 2 -6 2 -2 6 -2 -6 -6 -2 6 -2 z"/>
  </g>
  <!-- 바닥 -->
  <rect x="0" y="236" width="720" height="64" fill="#cdd8e8"/>
  <rect x="0" y="236" width="720" height="8" fill="#b9c6da"/>
  <g fill="#ffffff"><rect x="30" y="266" width="30" height="6" rx="3"/><rect x="96" y="266" width="30" height="6" rx="3"/><rect x="162" y="266" width="30" height="6" rx="3"/></g>

  <!-- 택시 -->
  <path d="M150 150 q6 -46 62 -50 l118 0 q42 4 54 50 z" fill="#ffd23f" stroke="#e0a500" stroke-width="4"/>
  <rect x="86" y="150" width="330" height="86" rx="26" fill="#ffd23f" stroke="#e0a500" stroke-width="4"/>
  <!-- 루프 사인 -->
  <rect x="298" y="86" width="62" height="22" rx="6" fill="#1a365d"/>
  <text x="329" y="102" text-anchor="middle" font-family="Arial, sans-serif" font-size="13" font-weight="800" fill="#ffffff">TAXI</text>
  <!-- 창문 -->
  <rect x="214" y="112" width="52" height="38" rx="8" fill="#d3ecff" stroke="#9cc8ee" stroke-width="2"/>
  <rect x="300" y="112" width="52" height="38" rx="8" fill="#d3ecff" stroke="#9cc8ee" stroke-width="2"/>
  <!-- 체커 스트라이프 -->
  <rect x="86" y="188" width="330" height="14" fill="#1a365d" opacity="0.92"/>
  <g fill="#ffffff">
    <rect x="92" y="190" width="10" height="10"/><rect x="112" y="190" width="10" height="10"/>
    <rect x="132" y="190" width="10" height="10"/><rect x="152" y="190" width="10" height="10"/>
    <rect x="172" y="190" width="10" height="10"/><rect x="192" y="190" width="10" height="10"/>
    <rect x="212" y="190" width="10" height="10"/><rect x="232" y="190" width="10" height="10"/>
    <rect x="252" y="190" width="10" height="10"/><rect x="272" y="190" width="10" height="10"/>
    <rect x="292" y="190" width="10" height="10"/><rect x="312" y="190" width="10" height="10"/>
    <rect x="332" y="190" width="10" height="10"/><rect x="352" y="190" width="10" height="10"/>
    <rect x="372" y="190" width="10" height="10"/><rect x="392" y="190" width="10" height="10"/>
  </g>
  <!-- 헤드라이트 -->
  <ellipse cx="408" cy="176" rx="8" ry="6" fill="#fff6cf" stroke="#e0a500" stroke-width="2"/>
  <!-- 바퀴 -->
  <circle cx="160" cy="236" r="24" fill="#2b2b33"/><circle cx="160" cy="236" r="10" fill="#c7ccd6"/>
  <circle cx="342" cy="236" r="24" fill="#2b2b33"/><circle cx="342" cy="236" r="10" fill="#c7ccd6"/>

  <!-- 해치 운전자 (왼쪽 창문) -->
  <path d="M240 92 l10 22 h-20 z" fill="#ffce54" stroke="#eab226" stroke-width="2"/>
  <circle cx="240" cy="132" r="22" fill="#ff9ec7" stroke="#f47ba9" stroke-width="2"/>
  <ellipse cx="223" cy="126" rx="7" ry="9" fill="#ff9ec7" stroke="#f47ba9" stroke-width="2"/>
  <ellipse cx="257" cy="126" rx="7" ry="9" fill="#ff9ec7" stroke="#f47ba9" stroke-width="2"/>
  <circle cx="232" cy="130" r="3" fill="#3a2b2b"/><circle cx="248" cy="130" r="3" fill="#3a2b2b"/>
  <circle cx="228" cy="138" r="4" fill="#ff7aa8" opacity="0.6"/><circle cx="252" cy="138" r="4" fill="#ff7aa8" opacity="0.6"/>
  <path d="M232 140 q8 8 16 0" stroke="#3a2b2b" stroke-width="2.6" fill="none" stroke-linecap="round"/>

  <!-- 소울 프렌즈 4종 (배웅하며 손 흔들기) -->
  {_friend(504, "#7fd6b5", "#4bb691")}
  {_friend(560, "#7db8ff", "#5691e0")}
  {_friend(616, "#ffd93f", "#e9bd2a")}
  {_friend(670, "#ff8a80", "#e56b61")}
</svg>"""

FACE_SVG = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 60 60">
  <path d="M30 6 l7 13 h-14 z" fill="#ffce54"/>
  <circle cx="30" cy="34" r="21" fill="#ff9ec7" stroke="#f47ba9" stroke-width="2"/>
  <circle cx="22" cy="32" r="3" fill="#3a2b2b"/><circle cx="38" cy="32" r="3" fill="#3a2b2b"/>
  <circle cx="18" cy="40" r="4" fill="#ff7aa8" opacity="0.6"/><circle cx="42" cy="40" r="4" fill="#ff7aa8" opacity="0.6"/>
  <path d="M22 41 q8 8 16 0" stroke="#3a2b2b" stroke-width="3" fill="none" stroke-linecap="round"/>
</svg>"""


def _data_uri(svg: str) -> str:
    b64 = base64.b64encode(svg.encode("utf-8")).decode("ascii")
    return f"data:image/svg+xml;base64,{b64}"


SCENE_URI = _data_uri(SCENE_SVG)
FACE_URI = _data_uri(FACE_SVG)
