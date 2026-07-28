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


SCENE_SVG = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 760 300">
  <defs>
    <linearGradient id="sky" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0" stop-color="#ffe9d6"/><stop offset="1" stop-color="#e4f1ff"/>
    </linearGradient>
  </defs>
  <rect width="760" height="300" rx="24" fill="url(#sky)"/>
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
  <rect x="0" y="236" width="760" height="64" fill="#cdd8e8"/>
  <rect x="0" y="236" width="760" height="8" fill="#b9c6da"/>
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

  <!-- 소울 프렌즈 5종 (휠체어 타고 배웅하며 손 흔들기) -->
  <g>
    <ellipse cx="504" cy="210" rx="19" ry="24" fill="#7fd6b5" stroke="#4bb691" stroke-width="3"/>
    <path d="M488 214 q-8 3 -9 12" stroke="#7fd6b5" stroke-width="7" fill="none" stroke-linecap="round"/>
    <path d="M519 200 q16 -8 20 -26" stroke="#7fd6b5" stroke-width="7" fill="none" stroke-linecap="round"/>
    <circle cx="498" cy="204" r="2.6" fill="#3a2b2b"/><circle cx="510" cy="204" r="2.6" fill="#3a2b2b"/>
    <circle cx="494" cy="210" r="3.4" fill="#ff9a9a" opacity="0.55"/><circle cx="514" cy="210" r="3.4" fill="#ff9a9a" opacity="0.55"/>
    <path d="M498 211 q6 5 12 0" stroke="#3a2b2b" stroke-width="2.4" fill="none" stroke-linecap="round"/>
    <path d="M486 220 q-2 12 8 16" fill="none" stroke="#4bb691" stroke-width="3.4" stroke-linecap="round"/>
    <path d="M517 188 q8 -3 10 -13" fill="none" stroke="#4bb691" stroke-width="3.4" stroke-linecap="round"/>
    <circle cx="509" cy="229" r="18" fill="none" stroke="#368a68" stroke-width="4"/>
    <g stroke="#368a68" stroke-width="1.8" opacity="0.9">
      <line x1="496" y1="229" x2="522" y2="229"/>
      <line x1="509" y1="216" x2="509" y2="242"/>
      <line x1="500" y1="220" x2="518" y2="238"/>
      <line x1="500" y1="238" x2="518" y2="220"/>
    </g>
    <circle cx="509" cy="229" r="3.4" fill="#368a68"/>
    <circle cx="487" cy="236" r="5.5" fill="#4bb691"/>
  </g>
  <g>
    <ellipse cx="560" cy="210" rx="19" ry="24" fill="#7db8ff" stroke="#5691e0" stroke-width="3"/>
    <path d="M544 214 q-8 3 -9 12" stroke="#7db8ff" stroke-width="7" fill="none" stroke-linecap="round"/>
    <path d="M575 200 q16 -8 20 -26" stroke="#7db8ff" stroke-width="7" fill="none" stroke-linecap="round"/>
    <circle cx="554" cy="204" r="2.6" fill="#3a2b2b"/><circle cx="566" cy="204" r="2.6" fill="#3a2b2b"/>
    <circle cx="550" cy="210" r="3.4" fill="#ff9a9a" opacity="0.55"/><circle cx="570" cy="210" r="3.4" fill="#ff9a9a" opacity="0.55"/>
    <path d="M554 211 q6 5 12 0" stroke="#3a2b2b" stroke-width="2.4" fill="none" stroke-linecap="round"/>
    <path d="M542 220 q-2 12 8 16" fill="none" stroke="#5691e0" stroke-width="3.4" stroke-linecap="round"/>
    <path d="M573 188 q8 -3 10 -13" fill="none" stroke="#5691e0" stroke-width="3.4" stroke-linecap="round"/>
    <circle cx="565" cy="229" r="18" fill="none" stroke="#3f6bc2" stroke-width="4"/>
    <g stroke="#3f6bc2" stroke-width="1.8" opacity="0.9">
      <line x1="552" y1="229" x2="578" y2="229"/>
      <line x1="565" y1="216" x2="565" y2="242"/>
      <line x1="556" y1="220" x2="574" y2="238"/>
      <line x1="556" y1="238" x2="574" y2="220"/>
    </g>
    <circle cx="565" cy="229" r="3.4" fill="#3f6bc2"/>
    <circle cx="543" cy="236" r="5.5" fill="#5691e0"/>
  </g>
  <g>
    <ellipse cx="616" cy="210" rx="19" ry="24" fill="#ffd93f" stroke="#e9bd2a" stroke-width="3"/>
    <path d="M600 214 q-8 3 -9 12" stroke="#ffd93f" stroke-width="7" fill="none" stroke-linecap="round"/>
    <path d="M631 200 q16 -8 20 -26" stroke="#ffd93f" stroke-width="7" fill="none" stroke-linecap="round"/>
    <circle cx="610" cy="204" r="2.6" fill="#3a2b2b"/><circle cx="622" cy="204" r="2.6" fill="#3a2b2b"/>
    <circle cx="606" cy="210" r="3.4" fill="#ff9a9a" opacity="0.55"/><circle cx="626" cy="210" r="3.4" fill="#ff9a9a" opacity="0.55"/>
    <path d="M610 211 q6 5 12 0" stroke="#3a2b2b" stroke-width="2.4" fill="none" stroke-linecap="round"/>
    <path d="M598 220 q-2 12 8 16" fill="none" stroke="#e9bd2a" stroke-width="3.4" stroke-linecap="round"/>
    <path d="M629 188 q8 -3 10 -13" fill="none" stroke="#e9bd2a" stroke-width="3.4" stroke-linecap="round"/>
    <circle cx="621" cy="229" r="18" fill="none" stroke="#c99a12" stroke-width="4"/>
    <g stroke="#c99a12" stroke-width="1.8" opacity="0.9">
      <line x1="608" y1="229" x2="634" y2="229"/>
      <line x1="621" y1="216" x2="621" y2="242"/>
      <line x1="612" y1="220" x2="630" y2="238"/>
      <line x1="612" y1="238" x2="630" y2="220"/>
    </g>
    <circle cx="621" cy="229" r="3.4" fill="#c99a12"/>
    <circle cx="599" cy="236" r="5.5" fill="#e9bd2a"/>
  </g>
  <g>
    <ellipse cx="670" cy="210" rx="19" ry="24" fill="#ff8a80" stroke="#e56b61" stroke-width="3"/>
    <path d="M654 214 q-8 3 -9 12" stroke="#ff8a80" stroke-width="7" fill="none" stroke-linecap="round"/>
    <path d="M685 200 q16 -8 20 -26" stroke="#ff8a80" stroke-width="7" fill="none" stroke-linecap="round"/>
    <circle cx="664" cy="204" r="2.6" fill="#3a2b2b"/><circle cx="676" cy="204" r="2.6" fill="#3a2b2b"/>
    <circle cx="660" cy="210" r="3.4" fill="#ff9a9a" opacity="0.55"/><circle cx="680" cy="210" r="3.4" fill="#ff9a9a" opacity="0.55"/>
    <path d="M664 211 q6 5 12 0" stroke="#3a2b2b" stroke-width="2.4" fill="none" stroke-linecap="round"/>
    <path d="M652 220 q-2 12 8 16" fill="none" stroke="#e56b61" stroke-width="3.4" stroke-linecap="round"/>
    <path d="M683 188 q8 -3 10 -13" fill="none" stroke="#e56b61" stroke-width="3.4" stroke-linecap="round"/>
    <circle cx="675" cy="229" r="18" fill="none" stroke="#c14a41" stroke-width="4"/>
    <g stroke="#c14a41" stroke-width="1.8" opacity="0.9">
      <line x1="662" y1="229" x2="688" y2="229"/>
      <line x1="675" y1="216" x2="675" y2="242"/>
      <line x1="666" y1="220" x2="684" y2="238"/>
      <line x1="666" y1="238" x2="684" y2="220"/>
    </g>
    <circle cx="675" cy="229" r="3.4" fill="#c14a41"/>
    <circle cx="653" cy="236" r="5.5" fill="#e56b61"/>
  </g>

  <g>
    <!-- 몸통 -->
    <ellipse cx="718" cy="210" rx="19" ry="24" fill="#caa6f2" stroke="#9a68d9" stroke-width="3"/>
    <path d="M702 214 q-8 3 -9 12" stroke="#caa6f2" stroke-width="7" fill="none" stroke-linecap="round"/>
    <path d="M733 200 q16 -8 20 -26" stroke="#caa6f2" stroke-width="7" fill="none" stroke-linecap="round"/>
    <circle cx="712" cy="204" r="2.6" fill="#3a2b2b"/><circle cx="724" cy="204" r="2.6" fill="#3a2b2b"/>
    <circle cx="708" cy="210" r="3.4" fill="#ff9a9a" opacity="0.55"/><circle cx="728" cy="210" r="3.4" fill="#ff9a9a" opacity="0.55"/>
    <path d="M712 211 q6 5 12 0" stroke="#3a2b2b" stroke-width="2.4" fill="none" stroke-linecap="round"/>
    <!-- 휠체어 (몸통 위로, 뚜렷하게) -->
    <path d="M700 220 q-2 12 8 16" fill="none" stroke="#9a68d9" stroke-width="3.4" stroke-linecap="round"/>
    <path d="M731 188 q8 -3 10 -13" fill="none" stroke="#9a68d9" stroke-width="3.4" stroke-linecap="round"/>
    <circle cx="723" cy="229" r="18" fill="none" stroke="#7c4bc4" stroke-width="4"/>
    <g stroke="#7c4bc4" stroke-width="1.8" opacity="0.9">
      <line x1="710" y1="229" x2="736" y2="229"/>
      <line x1="723" y1="216" x2="723" y2="242"/>
      <line x1="714" y1="220" x2="732" y2="238"/>
      <line x1="714" y1="238" x2="732" y2="220"/>
    </g>
    <circle cx="723" cy="229" r="3.4" fill="#7c4bc4"/>
    <circle cx="701" cy="236" r="5.5" fill="#9a68d9"/>
  </g>
</svg>"""

FACE_SVG = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 60 60">
  <path d="M30 6 l7 13 h-14 z" fill="#ffce54"/>
  <circle cx="30" cy="34" r="21" fill="#ffd93f" stroke="#e9bd2a" stroke-width="2"/>
  <circle cx="22" cy="32" r="3" fill="#3a2b2b"/><circle cx="38" cy="32" r="3" fill="#3a2b2b"/>
  <circle cx="18" cy="40" r="4" fill="#ffb84d" opacity="0.6"/><circle cx="42" cy="40" r="4" fill="#ffb84d" opacity="0.6"/>
  <path d="M22 41 q8 8 16 0" stroke="#3a2b2b" stroke-width="3" fill="none" stroke-linecap="round"/>
</svg>"""


def _data_uri(svg: str) -> str:
    b64 = base64.b64encode(svg.encode("utf-8")).decode("ascii")
    return f"data:image/svg+xml;base64,{b64}"


SCENE_URI = _data_uri(SCENE_SVG)
FACE_URI = _data_uri(FACE_SVG)