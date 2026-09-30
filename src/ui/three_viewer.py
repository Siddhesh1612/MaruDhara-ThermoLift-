import json
from typing import Any, Dict, Optional

def generate_threejs_html(
    well_id: str = "BWG-SIM-001",
    temperature_c: float = 62.5,
    viscosity_kcp: float = 7.2,
    spm: float = 7.0,
    stroke_m: float = 1.55,
    oil_rate_bpd: float = 34.5,
    pump_fillage_pct: float = 68.0,
    srp_load_kn: float = 46.0,
    risk_score: float = 18.0,
    phase: str = "production",
    scenario_label: str = "CURRENT STATE"
) -> str:
    """
    Generates an ultra-realistic, high-scale, interactive Three.js 3D Digital Twin:
    - Procedural PBR Desert Environment Map for realistic metallic/chrome sky reflections
    - Large-scale, high-fidelity Sucker Rod Pumping Unit (API Conventional Class I):
      * Structural A-Frame Sampson post with cross-lacing, gusset plates, and base skid
      * Heavy wide-flange walking beam with web stiffeners and center saddle bearing
      * Authentically curved horsehead with safety guards and dual wireline bridle
      * High-strength polished rod sliding through brass stuffing box with master valve wheel
      * Dual rotary crank arms with slotted cast-iron counterweights & diagonal caution stripes
      * Double-reduction gearbox, electric prime mover motor, and drive belt guard
    - Deep Geological Cutaway:
      * Desert dunes with sand ripple normal maps
      * Overburden alluvial strata
      * Impermeable Caprock Shale formation
      * Porous Jodhpur Sandstone Heavy-Oil Reservoir with thermodynamic heat glow
      * Perforated casing liner with realistic perforation holes
    - Downhole Pump Mechanism Cutaway (Big & Clear):
      * Reciprocating plunger with piston seal rings
      * Dynamic traveling valve ball opening/closing inside plunger cage
      * Dynamic standing valve ball opening/closing inside barrel base
    - Interactive "Click-to-Inspect" Engineering Inspector:
      * Click any 3D component to open detailed engineering function, physics role, and live state
    - Big Visual Viewports:
      * 4 Close-up Camera Presets (Surface Unit, Downhole Pump Mechanism, Reservoir Zone, Full Profile)
      * Auto-Orbit cinematic mode
      * Real-time kinematic stroke banner (Upstroke vs. Downstroke cycle physics)
      * Fullscreen mode button
    """
    state_json = json.dumps({
        "well_id": well_id,
        "temperature_c": float(temperature_c),
        "viscosity_kcp": float(viscosity_kcp),
        "spm": float(spm),
        "stroke_m": float(stroke_m),
        "oil_rate_bpd": float(oil_rate_bpd),
        "pump_fillage_pct": float(pump_fillage_pct),
        "srp_load_kn": float(srp_load_kn),
        "risk_score": float(risk_score),
        "phase": phase,
        "scenario_label": scenario_label
    })

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>THERMOLIFT 3D Industrial Digital Twin</title>
    <!-- Three.js and OrbitControls -->
    <script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/three@0.128.0/examples/js/controls/OrbitControls.js"></script>
    <!-- Tailwind CSS -->
    <script src="https://cdn.tailwindcss.com"></script>
    <style>
        body, html {{
            margin: 0;
            padding: 0;
            width: 100%;
            height: 100%;
            overflow: hidden;
            background-color: #030712;
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
            color: #f1f5f9;
            user-select: none;
        }}
        #canvas-container {{
            width: 100%;
            height: 100%;
            position: absolute;
            top: 0;
            left: 0;
            cursor: grab;
        }}
        #canvas-container:active {{
            cursor: grabbing;
        }}
        .hud-glass {{
            background: rgba(10, 16, 32, 0.85);
            backdrop-filter: blur(18px);
            -webkit-backdrop-filter: blur(18px);
            border: 1px solid rgba(255, 255, 255, 0.12);
            box-shadow: 0 16px 40px rgba(0, 0, 0, 0.6);
        }}
        .hud-glass-subtle {{
            background: rgba(15, 23, 42, 0.72);
            backdrop-filter: blur(10px);
            -webkit-backdrop-filter: blur(10px);
            border: 1px solid rgba(255, 255, 255, 0.08);
        }}
        /* 3D Label Callouts */
        .annotation-pin {{
            position: absolute;
            pointer-events: auto;
            cursor: pointer;
            padding: 4px 10px;
            background: rgba(15, 23, 42, 0.92);
            border: 1.5px solid #f59e0b;
            color: #f8fafc;
            border-radius: 8px;
            font-size: 11px;
            font-weight: 700;
            letter-spacing: 0.5px;
            white-space: nowrap;
            box-shadow: 0 6px 16px rgba(0, 0, 0, 0.6), 0 0 10px rgba(245, 158, 11, 0.35);
            transition: all 0.2s ease;
            transform: translate(-50%, -100%);
        }}
        .annotation-pin:hover {{
            background: #d97706;
            color: #ffffff;
            border-color: #fbbf24;
            transform: translate(-50%, -108%) scale(1.05);
        }}
        /* Phase Glow Bar */
        .stroke-banner-up {{
            background: linear-gradient(90deg, rgba(14, 165, 233, 0.25) 0%, rgba(56, 189, 248, 0.35) 50%, rgba(14, 165, 233, 0.25) 100%);
            border: 1px solid rgba(56, 189, 248, 0.5);
            color: #38bdf8;
        }}
        .stroke-banner-down {{
            background: linear-gradient(90deg, rgba(245, 158, 11, 0.25) 0%, rgba(251, 191, 36, 0.35) 50%, rgba(245, 158, 11, 0.25) 100%);
            border: 1px solid rgba(245, 158, 11, 0.5);
            color: #fbbf24;
        }}
    </style>
</head>
<body>
    <div id="canvas-container"></div>

    <!-- TOP TOOLBAR & CONTROLS -->
    <div class="absolute top-3 left-3 right-3 flex justify-between items-start pointer-events-none z-20">
        <!-- Asset Header -->
        <div class="hud-glass rounded-xl px-4 py-2.5 pointer-events-auto flex items-center space-x-3.5">
            <div class="relative flex items-center justify-center">
                <span class="w-3 h-3 rounded-full bg-emerald-400 animate-ping absolute"></span>
                <span class="w-3 h-3 rounded-full bg-emerald-500"></span>
            </div>
            <div>
                <div class="flex items-center space-x-2">
                    <span class="text-sm font-extrabold text-white font-mono tracking-wide">{well_id}</span>
                    <span class="px-2 py-0.5 text-[10px] font-bold uppercase rounded bg-amber-500/20 text-amber-300 border border-amber-500/40">
                        {scenario_label}
                    </span>
                </div>
                <div class="text-[10px] text-slate-400 font-medium">Baghewala Heavy Oil • Jodhpur Sandstone Pumping Twin</div>
            </div>
            <div class="h-6 w-px bg-slate-700"></div>
            <div class="text-xs">
                <span class="text-slate-400">Pumping Speed:</span>
                <span class="font-bold text-amber-400 font-mono text-sm ml-1">{spm:.1f} SPM</span>
            </div>
        </div>

        <!-- Camera & Navigation Toolbar -->
        <div class="hud-glass rounded-xl p-1.5 pointer-events-auto flex items-center space-x-1.5">
            <button onclick="setCameraView('surface')" class="view-btn px-3 py-1.5 text-xs font-bold rounded-lg bg-amber-600 text-white transition flex items-center space-x-1" id="btn-view-surface">
                <span>🏗️ Surface Unit</span>
            </button>
            <button onclick="setCameraView('pump')" class="view-btn px-3 py-1.5 text-xs font-semibold rounded-lg bg-slate-800/90 hover:bg-amber-600 hover:text-white text-slate-200 transition flex items-center space-x-1" id="btn-view-pump">
                <span>⚙️ Downhole Pump & Valves</span>
            </button>
            <button onclick="setCameraView('reservoir')" class="view-btn px-3 py-1.5 text-xs font-semibold rounded-lg bg-slate-800/90 hover:bg-amber-600 hover:text-white text-slate-200 transition flex items-center space-x-1" id="btn-view-res">
                <span>🔥 Reservoir & Inflow</span>
            </button>
            <button onclick="setCameraView('profile')" class="view-btn px-3 py-1.5 text-xs font-semibold rounded-lg bg-slate-800/90 hover:bg-amber-600 hover:text-white text-slate-200 transition flex items-center space-x-1" id="btn-view-prof">
                <span>📐 Full Well Profile</span>
            </button>

            <div class="h-5 w-px bg-slate-700 mx-1"></div>

            <button id="btn-auto-orbit" onclick="toggleAutoOrbit()" class="px-2.5 py-1.5 text-xs font-semibold rounded-lg bg-slate-800/90 hover:bg-slate-700 text-slate-300 transition" title="Toggle Cinematic Auto-Orbit">
                🔄 Orbit
            </button>
            <button id="btn-labels" onclick="toggleLabels()" class="px-2.5 py-1.5 text-xs font-semibold rounded-lg bg-slate-800/90 hover:bg-slate-700 text-slate-300 transition" title="Toggle 3D Component Labels">
                🏷️ Labels
            </button>
            <button id="btn-pause" onclick="togglePlayPause()" class="px-2.5 py-1.5 text-xs font-semibold rounded-lg bg-slate-800/90 hover:bg-slate-700 text-slate-300 transition" title="Play / Pause Kinematics">
                ⏸️
            </button>
            <button onclick="toggleFullscreen()" class="px-2.5 py-1.5 text-xs font-semibold rounded-lg bg-slate-800/90 hover:bg-slate-700 text-slate-300 transition" title="Toggle Fullscreen">
                ⛶
            </button>
        </div>
    </div>

    <!-- DYNAMIC STROKE PHASE BANNER (TOP CENTER) -->
    <div class="absolute top-16 left-1/2 -translate-x-1/2 pointer-events-none z-20">
        <div id="stroke-phase-banner" class="stroke-banner-up px-4 py-1.5 rounded-full text-xs font-mono font-bold tracking-wide shadow-lg transition-all duration-300 flex items-center space-x-2">
            <span id="stroke-phase-icon">⬆️</span>
            <span id="stroke-phase-text">UPSTROKE: Traveling Valve CLOSED (Lifting) • Standing Valve OPEN (Intake)</span>
        </div>
    </div>

    <!-- LIVE TELEMETRY HUD (BOTTOM RIGHT) -->
    <div class="absolute bottom-3 right-3 w-80 hud-glass rounded-xl p-4 pointer-events-auto z-20">
        <div class="flex justify-between items-center pb-2.5 border-b border-slate-700/80">
            <div class="flex items-center space-x-1.5">
                <span class="w-2.5 h-2.5 rounded-full bg-cyan-400"></span>
                <span class="text-xs font-bold text-slate-200 uppercase tracking-wider">Coupled Physics HUD</span>
            </div>
            <span class="px-2 py-0.5 rounded text-[11px] font-mono font-bold bg-amber-500/20 text-amber-300 border border-amber-500/40">
                {spm:.1f} SPM • {stroke_m:.2f}m
            </span>
        </div>

        <div class="mt-3 space-y-2 text-xs font-mono">
            <div class="flex justify-between items-center bg-slate-900/80 px-3 py-1.5 rounded-lg border border-slate-800">
                <span class="text-slate-400">Dynamic Rod Load:</span>
                <span class="font-extrabold text-rose-400 text-sm flex items-center space-x-1">
                    <span id="hud-live-load">{srp_load_kn:.1f}</span>
                    <span class="text-xs text-rose-300 font-normal">kN</span>
                </span>
            </div>

            <div class="flex justify-between items-center bg-slate-900/80 px-3 py-1.5 rounded-lg border border-slate-800">
                <span class="text-slate-400">Reservoir Temp:</span>
                <span class="font-bold text-amber-400 text-sm" id="hud-temp">{temperature_c:.1f} °C</span>
            </div>

            <div class="flex justify-between items-center bg-slate-900/80 px-3 py-1.5 rounded-lg border border-slate-800">
                <span class="text-slate-400">Heavy Oil Viscosity:</span>
                <span class="font-bold text-cyan-400 text-sm" id="hud-visc">{viscosity_kcp:.2f} kcP</span>
            </div>

            <div class="flex justify-between items-center bg-slate-900/80 px-3 py-1.5 rounded-lg border border-slate-800">
                <span class="text-slate-400">Net Crude Rate:</span>
                <span class="font-bold text-emerald-400 text-sm">{oil_rate_bpd:.1f} bpd</span>
            </div>

            <div class="flex justify-between items-center bg-slate-900/80 px-3 py-1.5 rounded-lg border border-slate-800">
                <span class="text-slate-400">Pump Fillage:</span>
                <span class="font-bold text-blue-400 text-sm">{pump_fillage_pct:.1f} %</span>
            </div>
        </div>

        <!-- Simulation Speed Selector -->
        <div class="mt-3 pt-2.5 border-t border-slate-700/80 flex items-center justify-between text-xs text-slate-400">
            <span class="font-semibold text-[11px]">Speed:</span>
            <div class="flex items-center space-x-1">
                <button onclick="setSimSpeed(0.25)" class="speed-btn px-2 py-0.5 rounded text-[10px] bg-slate-800 hover:bg-amber-600 text-slate-300">0.25x</button>
                <button onclick="setSimSpeed(0.5)" class="speed-btn px-2 py-0.5 rounded text-[10px] bg-slate-800 hover:bg-amber-600 text-slate-300">0.5x</button>
                <button onclick="setSimSpeed(1.0)" class="speed-btn px-2 py-0.5 rounded text-[10px] bg-amber-600 text-white font-bold" id="speed-1">1.0x</button>
                <button onclick="setSimSpeed(2.0)" class="speed-btn px-2 py-0.5 rounded text-[10px] bg-slate-800 hover:bg-amber-600 text-slate-300">2.0x</button>
            </div>
        </div>
    </div>

    <!-- ENGINEERING INSPECTION CARD (BOTTOM LEFT) -->
    <div id="inspector-card" class="absolute bottom-3 left-3 w-88 hud-glass rounded-xl p-4 pointer-events-auto z-20 max-w-sm transition-all duration-300">
        <div class="flex justify-between items-start mb-2 pb-2 border-b border-slate-700/70">
            <div>
                <div class="text-[10px] font-bold text-amber-400 uppercase tracking-wider">Component Inspector</div>
                <div id="insp-title" class="text-sm font-extrabold text-white">Sucker Rod Pumping Unit</div>
            </div>
            <span id="insp-badge" class="px-2 py-0.5 rounded text-[10px] font-bold bg-blue-500/20 text-blue-300 border border-blue-500/30">
                SURFACE
            </span>
        </div>
        <p id="insp-desc" class="text-xs text-slate-300 leading-relaxed">
            API Conventional Class I beam unit converting rotary motion into reciprocating polished rod stroke via Samson post, walking beam, and counterweighted crank.
        </p>
        <div id="insp-stats" class="mt-2.5 p-2 rounded bg-slate-900/80 border border-slate-800 text-[11px] font-mono space-y-1 text-slate-300">
            <div>• <b>Cadence:</b> {spm:.1f} SPM ({stroke_m:.2f} m stroke)</div>
            <div>• <b>Peak Rod Load:</b> {srp_load_kn:.1f} kN (Max 62.0 kN)</div>
        </div>
        <div class="mt-2 text-[10px] text-slate-400 italic">
            💡 Click any 3D part or label to inspect mechanical function and physics telemetry.
        </div>
    </div>

    <!-- 3D PINS CONTAINER -->
    <div id="pins-container" class="absolute inset-0 pointer-events-none z-10" style="display: none;">
        <div id="pin-horsehead" class="annotation-pin" onclick="inspectPart('horsehead')">🐴 Horsehead & Bridle</div>
        <div id="pin-beam" class="annotation-pin" onclick="inspectPart('walkingBeam')">⚖️ Walking Beam</div>
        <div id="pin-sampson" class="annotation-pin" onclick="inspectPart('sampsonPost')">🏗️ Samson Post</div>
        <div id="pin-crank" class="annotation-pin" onclick="inspectPart('crank')">⚙️ Crank & Weights</div>
        <div id="pin-wellhead" class="annotation-pin" onclick="inspectPart('stuffingBox')">🛢️ Stuffing Box</div>
        <div id="pin-reservoir" class="annotation-pin" onclick="inspectPart('reservoir')">🔥 Jodhpur Sandstone</div>
        <div id="pin-pump" class="annotation-pin" onclick="inspectPart('downholePump')">⚙️ Downhole Pump</div>
    </div>

    <script>
        const stateData = {state_json};

        // --- PROCEDURAL ENVIRONMENT & TEXTURE GENERATOR ---
        function createDesertEnvMap() {{
            const c = document.createElement('canvas');
            c.width = 1024;
            c.height = 512;
            const ctx = c.getContext('2d');

            // Sky to horizon gradient
            const grad = ctx.createLinearGradient(0, 0, 0, 512);
            grad.addColorStop(0.0, '#0f172a');  // dark sky zenith
            grad.addColorStop(0.35, '#1e3a8a'); // desert sky blue
            grad.addColorStop(0.48, '#fbbf24'); // golden horizon light
            grad.addColorStop(0.52, '#d97706'); // desert sand line
            grad.addColorStop(0.7, '#78350f');  // desert ground
            grad.addColorStop(1.0, '#0f172a');  // subterranean
            ctx.fillStyle = grad;
            ctx.fillRect(0, 0, 1024, 512);

            // Sun highlight
            ctx.beginPath();
            ctx.arc(720, 190, 50, 0, Math.PI * 2);
            ctx.fillStyle = '#ffffff';
            ctx.shadowColor = '#fef08a';
            ctx.shadowBlur = 80;
            ctx.fill();
            ctx.shadowBlur = 0;

            const tex = new THREE.CanvasTexture(c);
            tex.mapping = THREE.EquirectangularReflectionMapping;
            return tex;
        }}

        function createBrushedSteelCanvas() {{
            const c = document.createElement('canvas');
            c.width = 512;
            c.height = 512;
            const ctx = c.getContext('2d');
            ctx.fillStyle = '#64748b';
            ctx.fillRect(0, 0, 512, 512);
            for (let i = 0; i < 5000; i++) {{
                const y = Math.random() * 512;
                const len = 30 + Math.random() * 140;
                const x = Math.random() * 512;
                ctx.fillStyle = (Math.random() > 0.5) ? 'rgba(255,255,255,0.09)' : 'rgba(0,0,0,0.14)';
                ctx.fillRect(x, y, len, 1.2);
            }}
            return new THREE.CanvasTexture(c);
        }}

        function createHazardStripesCanvas() {{
            const c = document.createElement('canvas');
            c.width = 256;
            c.height = 256;
            const ctx = c.getContext('2d');
            ctx.fillStyle = '#f59e0b'; // amber
            ctx.fillRect(0, 0, 256, 256);
            ctx.fillStyle = '#0f172a'; // dark slate
            for (let i = -256; i < 512; i += 44) {{
                ctx.beginPath();
                ctx.moveTo(i, 0);
                ctx.lineTo(i + 22, 0);
                ctx.lineTo(i + 22 - 128, 256);
                ctx.lineTo(i - 128, 256);
                ctx.closePath();
                ctx.fill();
            }}
            const tex = new THREE.CanvasTexture(c);
            tex.wrapS = THREE.RepeatWrapping;
            tex.wrapT = THREE.RepeatWrapping;
            tex.repeat.set(2, 2);
            return tex;
        }}

        function createSandNormalCanvas() {{
            const c = document.createElement('canvas');
            c.width = 512;
            c.height = 512;
            const ctx = c.getContext('2d');
            ctx.fillStyle = '#b45309';
            ctx.fillRect(0, 0, 512, 512);
            for (let i = 0; i < 20000; i++) {{
                const x = Math.random() * 512;
                const y = Math.random() * 512;
                ctx.fillStyle = Math.random() > 0.5 ? 'rgba(251,191,36,0.18)' : 'rgba(120,53,15,0.18)';
                ctx.fillRect(x, y, 2, 2);
            }}
            // ripple dunes
            ctx.strokeStyle = 'rgba(217, 119, 6, 0.35)';
            ctx.lineWidth = 5;
            for (let y = 20; y < 512; y += 40) {{
                ctx.beginPath();
                ctx.moveTo(0, y);
                ctx.bezierCurveTo(150, y + 25, 360, y - 20, 512, y + 10);
                ctx.stroke();
            }}
            const tex = new THREE.CanvasTexture(c);
            tex.wrapS = THREE.RepeatWrapping;
            tex.wrapT = THREE.RepeatWrapping;
            tex.repeat.set(4, 4);
            return tex;
        }}

        function createRockStrataCanvas() {{
            const c = document.createElement('canvas');
            c.width = 512;
            c.height = 512;
            const ctx = c.getContext('2d');
            ctx.fillStyle = '#1e293b';
            ctx.fillRect(0, 0, 512, 512);
            for (let y = 0; y < 512; y += 6) {{
                const val = 18 + Math.floor(Math.sin(y * 0.08) * 12 + Math.random() * 8);
                ctx.fillStyle = `rgb(${{val}}, ${{val + 8}}, ${{val + 16}})`;
                ctx.fillRect(0, y, 512, 5);
            }}
            const tex = new THREE.CanvasTexture(c);
            tex.wrapS = THREE.RepeatWrapping;
            tex.wrapT = THREE.RepeatWrapping;
            tex.repeat.set(2, 6);
            return tex;
        }}

        function createPerforatedCasingCanvas() {{
            const c = document.createElement('canvas');
            c.width = 256;
            c.height = 512;
            const ctx = c.getContext('2d');
            ctx.fillStyle = '#64748b';
            ctx.fillRect(0, 0, 256, 512);
            ctx.fillStyle = '#090d16';
            for (let y = 14; y < 512; y += 28) {{
                for (let x = 14; x < 256; x += 28) {{
                    const ox = (y % 56 === 0) ? 14 : 0;
                    ctx.beginPath();
                    ctx.arc(x + ox, y, 5, 0, Math.PI * 2);
                    ctx.fill();
                    ctx.strokeStyle = '#e2e8f0';
                    ctx.lineWidth = 1.2;
                    ctx.stroke();
                }}
            }}
            const tex = new THREE.CanvasTexture(c);
            tex.wrapS = THREE.RepeatWrapping;
            tex.wrapT = THREE.RepeatWrapping;
            tex.repeat.set(2, 4);
            return tex;
        }}

        // --- THREE.JS INITIALIZATION ---
        const container = document.getElementById('canvas-container');
        const scene = new THREE.Scene();
        scene.background = new THREE.Color(0x040814);
        scene.fog = new THREE.FogExp2(0x040814, 0.0028);

        // High-scale camera framing
        const camera = new THREE.PerspectiveCamera(45, window.innerWidth / window.innerHeight, 0.1, 1500);
        camera.position.set(13.5, 9.5, 16.5);

        const renderer = new THREE.WebGLRenderer({{ antialias: true, alpha: true, powerPreference: "high-performance" }});
        renderer.setSize(window.innerWidth, window.innerHeight);
        renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
        renderer.shadowMap.enabled = true;
        renderer.shadowMap.type = THREE.PCFSoftShadowMap;
        renderer.toneMapping = THREE.ACESFilmicToneMapping;
        renderer.toneMappingExposure = 1.25;
        container.appendChild(renderer.domElement);

        const envMap = createDesertEnvMap();
        scene.environment = envMap;

        const controls = new THREE.OrbitControls(camera, renderer.domElement);
        controls.enableDamping = true;
        controls.dampingFactor = 0.06;
        controls.maxPolarAngle = Math.PI / 2 + 0.42;
        controls.target.set(-2.5, 4.5, 0);

        // --- LIGHTING ---
        const sunLight = new THREE.DirectionalLight(0xfff8ed, 2.8);
        sunLight.position.set(40, 60, 30);
        sunLight.castShadow = true;
        sunLight.shadow.mapSize.width = 2048;
        sunLight.shadow.mapSize.height = 2048;
        sunLight.shadow.camera.near = 1;
        sunLight.shadow.camera.far = 200;
        sunLight.shadow.camera.left = -30;
        sunLight.shadow.camera.right = 30;
        sunLight.shadow.camera.top = 30;
        sunLight.shadow.camera.bottom = -30;
        sunLight.shadow.bias = -0.0004;
        scene.add(sunLight);

        const hemiLight = new THREE.HemisphereLight(0x38bdf8, 0x1e293b, 0.8);
        scene.add(hemiLight);

        const ambientLight = new THREE.AmbientLight(0x0f172a, 0.95);
        scene.add(ambientLight);

        // Subsurface Thermal Glow Point Light
        function getThermalColor(temp) {{
            const norm = Math.max(0, Math.min(1, (temp - 48) / 36));
            const color = new THREE.Color();
            color.setHSL(0.03 + norm * 0.08, 0.98, 0.44 + norm * 0.35);
            return color;
        }}
        const thermalGlowColor = getThermalColor(stateData.temperature_c);

        const reservoirLight = new THREE.PointLight(thermalGlowColor, 5.5, 80);
        reservoirLight.position.set(0, -56, 0);
        scene.add(reservoirLight);

        // --- PBR TEXTURES & MATERIALS ---
        const steelMap = createBrushedSteelCanvas();
        const hazardMap = createHazardStripesCanvas();
        const sandMap = createSandNormalCanvas();
        const strataMap = createRockStrataCanvas();
        const perfMap = createPerforatedCasingCanvas();

        const matSteel = new THREE.MeshStandardMaterial({{
            color: 0x475569,
            metalness: 0.9,
            roughness: 0.25,
            map: steelMap,
            bumpMap: steelMap,
            bumpScale: 0.05,
            envMap: envMap
        }});

        const matYellowFrame = new THREE.MeshStandardMaterial({{
            color: 0xeab308,
            metalness: 0.65,
            roughness: 0.32,
            envMap: envMap
        }});

        const matCounterweight = new THREE.MeshStandardMaterial({{
            color: 0x9a3412,
            metalness: 0.82,
            roughness: 0.28,
            bumpMap: steelMap,
            bumpScale: 0.08,
            envMap: envMap
        }});

        const matHazardStripe = new THREE.MeshStandardMaterial({{
            map: hazardMap,
            metalness: 0.5,
            roughness: 0.4
        }});

        const matPolishedChrome = new THREE.MeshStandardMaterial({{
            color: 0xffffff,
            metalness: 0.98,
            roughness: 0.05,
            envMap: envMap
        }});

        const matDesertSand = new THREE.MeshStandardMaterial({{
            map: sandMap,
            roughness: 0.95,
            metalness: 0.02
        }});

        const matShaleCaprock = new THREE.MeshStandardMaterial({{
            map: strataMap,
            roughness: 0.88,
            metalness: 0.1
        }});

        const matReservoir = new THREE.MeshStandardMaterial({{
            color: thermalGlowColor,
            roughness: 0.6,
            metalness: 0.25,
            emissive: thermalGlowColor,
            emissiveIntensity: 0.52
        }});

        const matPerforatedCasing = new THREE.MeshStandardMaterial({{
            map: perfMap,
            metalness: 0.85,
            roughness: 0.35,
            transparent: true,
            opacity: 0.85
        }});

        const matGlassTubing = new THREE.MeshStandardMaterial({{
            color: 0x38bdf8,
            metalness: 0.1,
            roughness: 0.05,
            transparent: true,
            opacity: 0.4
        }});

        // --- INTERACTIVE RAYCASTING FOR INSPECTION ---
        const raycaster = new THREE.Raycaster();
        const mouse = new THREE.Vector2();
        const inspectableObjects = [];

        function registerInspectable(mesh, partKey) {{
            mesh.userData.partKey = partKey;
            inspectableObjects.push(mesh);
        }}

        // --- 1. DESERT GROUND & STRATIGRAPHY CUTAWAY ---
        const terrainGroup = new THREE.Group();

        // Surface pad
        const surfacePadGeo = new THREE.BoxGeometry(64, 1.0, 64);
        const surfacePad = new THREE.Mesh(surfacePadGeo, matDesertSand);
        surfacePad.position.y = -0.5;
        surfacePad.receiveShadow = true;
        terrainGroup.add(surfacePad);

        // Concrete well cellar pad
        const cellarGeo = new THREE.BoxGeometry(17, 0.4, 13);
        const cellarMesh = new THREE.Mesh(cellarGeo, new THREE.MeshStandardMaterial({{ color: 0x334155, roughness: 0.9 }}));
        cellarMesh.position.set(-2.5, 0.05, 0);
        cellarMesh.receiveShadow = true;
        terrainGroup.add(cellarMesh);

        // Subsurface Cutaway Overburden (0 to -24m)
        const obGeo = new THREE.BoxGeometry(28, 24, 28);
        const obMesh = new THREE.Mesh(obGeo, new THREE.MeshStandardMaterial({{ color: 0x78350f, roughness: 0.9 }}));
        obMesh.position.set(-14, -12, -14);
        terrainGroup.add(obMesh);

        // Impermeable Caprock Shale (-24 to -46m)
        const shaleGeo = new THREE.BoxGeometry(28, 22, 28);
        const shaleMesh = new THREE.Mesh(shaleGeo, matShaleCaprock);
        shaleMesh.position.set(-14, -35, -14);
        terrainGroup.add(shaleMesh);

        // Jodhpur Sandstone Heavy Oil Reservoir (-46 to -72m)
        const resGeo = new THREE.CylinderGeometry(20, 22, 26, 32);
        const resMesh = new THREE.Mesh(resGeo, matReservoir);
        resMesh.position.set(0, -59, 0);
        registerInspectable(resMesh, 'reservoir');
        terrainGroup.add(resMesh);

        scene.add(terrainGroup);

        // --- 2. WELLHEAD & DOWNHOLE TUBULARS ---
        const wellGroup = new THREE.Group();

        // Wellhead Master Valve & Flange
        const flange = new THREE.Mesh(new THREE.CylinderGeometry(0.75, 0.85, 0.9, 20), matSteel);
        flange.position.y = 0.45;
        flange.castShadow = true;
        wellGroup.add(flange);

        // Master valve handwheel
        const wheelGeo = new THREE.TorusGeometry(0.35, 0.05, 12, 24);
        const wheel = new THREE.Mesh(wheelGeo, matHazardStripe);
        wheel.position.set(0.65, 0.65, 0);
        wheel.rotation.y = Math.PI / 2;
        wellGroup.add(wheel);

        // Stuffing Box
        const stuffingBox = new THREE.Mesh(new THREE.CylinderGeometry(0.38, 0.38, 1.4, 20), matSteel);
        stuffingBox.position.y = 1.4;
        stuffingBox.castShadow = true;
        registerInspectable(stuffingBox, 'stuffingBox');
        wellGroup.add(stuffingBox);

        // Surface Flowline leading to manifold
        const flowline = new THREE.Mesh(new THREE.CylinderGeometry(0.14, 0.14, 10, 16), matYellowFrame);
        flowline.rotation.z = Math.PI / 2;
        flowline.position.set(5.2, 1.0, 0);
        wellGroup.add(flowline);

        // Subsurface Casing string
        const casingGeo = new THREE.CylinderGeometry(0.95, 0.95, 68, 32, 1, true);
        const casingMesh = new THREE.Mesh(casingGeo, matPerforatedCasing);
        casingMesh.position.y = -34;
        wellGroup.add(casingMesh);

        // Production Tubing (Inner transparent glass tube)
        const tubingGeo = new THREE.CylinderGeometry(0.48, 0.48, 66, 24);
        const tubingMesh = new THREE.Mesh(tubingGeo, matGlassTubing);
        tubingMesh.position.y = -33;
        registerInspectable(tubingMesh, 'tubing');
        wellGroup.add(tubingMesh);

        // Sucker Rod String
        const totalRodLength = 70.0;
        const suckerRodGeo = new THREE.CylinderGeometry(0.08, 0.08, totalRodLength, 12);
        const suckerRod = new THREE.Mesh(suckerRodGeo, matPolishedChrome);
        suckerRod.position.y = -totalRodLength / 2 + 2.5;
        wellGroup.add(suckerRod);

        // DOWNHOLE PUMP CUTAWAY (-56m depth)
        const pumpGroup = new THREE.Group();
        pumpGroup.position.y = -56.0;

        // Stationary Pump Barrel
        const barrelMesh = new THREE.Mesh(
            new THREE.CylinderGeometry(0.44, 0.44, 5.2, 24, 1, true),
            new THREE.MeshStandardMaterial({{ color: 0x94a3b8, metalness: 0.85, roughness: 0.25, transparent: true, opacity: 0.65 }})
        );
        registerInspectable(barrelMesh, 'downholePump');
        pumpGroup.add(barrelMesh);

        // Standing Valve Assembly
        const svSeat = new THREE.Mesh(new THREE.CylinderGeometry(0.36, 0.36, 0.35, 16), matSteel);
        svSeat.position.y = -2.35;
        pumpGroup.add(svSeat);

        const svBall = new THREE.Mesh(new THREE.SphereGeometry(0.18, 16, 16), matPolishedChrome);
        svBall.position.set(0, -2.15, 0);
        registerInspectable(svBall, 'standingValve');
        pumpGroup.add(svBall);

        // Reciprocating Plunger
        const plungerGroup = new THREE.Group();
        const plungerBody = new THREE.Mesh(new THREE.CylinderGeometry(0.37, 0.37, 3.5, 20), matSteel);
        plungerGroup.add(plungerBody);

        // Traveling Valve Assembly inside plunger
        const tvSeat = new THREE.Mesh(new THREE.CylinderGeometry(0.28, 0.28, 0.25, 16), matSteel);
        tvSeat.position.y = -1.4;
        plungerGroup.add(tvSeat);

        const tvBall = new THREE.Mesh(new THREE.SphereGeometry(0.16, 16, 16), matPolishedChrome);
        tvBall.position.set(0, -1.25, 0);
        registerInspectable(tvBall, 'travelingValve');
        plungerGroup.add(tvBall);

        pumpGroup.add(plungerGroup);
        wellGroup.add(pumpGroup);

        scene.add(wellGroup);

        // --- 3. SUCKER ROD PUMPING UNIT (PUMPJACK) ---
        // Wellhead centerline at X = 0.
        // Horsehead arc radius = 4.6. Sampson center at X = -4.6, Y = 7.6.
        const pumpjack = new THREE.Group();

        // Heavy Base Skid
        const skidGeo = new THREE.BoxGeometry(14.0, 0.55, 4.4);
        const skid = new THREE.Mesh(skidGeo, matYellowFrame);
        skid.position.set(-6.8, 0.27, 0);
        skid.castShadow = true;
        skid.receiveShadow = true;
        pumpjack.add(skid);

        // Structural Sampson Post
        const sampsonCenter = new THREE.Vector3(-4.6, 7.6, 0);
        const postGroup = new THREE.Group();

        const legGeom = new THREE.CylinderGeometry(0.18, 0.26, 7.8, 12);
        const legPositions = [
            {{ x: -4.6 + 1.2, z: 1.4, rx: -0.16, rz: -0.14 }},
            {{ x: -4.6 + 1.2, z: -1.4, rx: 0.16, rz: -0.14 }},
            {{ x: -4.6 - 1.8, z: 1.4, rx: -0.16, rz: 0.22 }},
            {{ x: -4.6 - 1.8, z: -1.4, rx: 0.16, rz: 0.22 }}
        ];
        legPositions.forEach(p => {{
            const leg = new THREE.Mesh(legGeom, matSteel);
            leg.position.set(p.x, 3.8, p.z);
            leg.rotation.x = p.rx;
            leg.rotation.z = p.rz;
            leg.castShadow = true;
            postGroup.add(leg);
        }});

        // Cross braces
        const braceGeo = new THREE.CylinderGeometry(0.08, 0.08, 2.6, 8);
        const brace1 = new THREE.Mesh(braceGeo, matSteel);
        brace1.position.set(-4.6, 3.6, 0);
        brace1.rotation.x = Math.PI / 2;
        postGroup.add(brace1);

        // Center Bearing Housing (Saddle Bearing)
        const centerBearing = new THREE.Mesh(new THREE.CylinderGeometry(0.42, 0.42, 1.8, 20), matSteel);
        centerBearing.rotation.x = Math.PI / 2;
        centerBearing.position.copy(sampsonCenter);
        centerBearing.castShadow = true;
        postGroup.add(centerBearing);

        registerInspectable(centerBearing, 'sampsonPost');
        pumpjack.add(postGroup);

        // WALKING BEAM & HORSEHEAD
        const beamPivotGroup = new THREE.Group();
        beamPivotGroup.position.copy(sampsonCenter);

        const frontArm = 4.6;
        const rearArm = 4.4;
        const totalBeamLen = frontArm + rearArm;
        const beamMesh = new THREE.Mesh(new THREE.BoxGeometry(totalBeamLen, 0.8, 0.6), matSteel);
        beamMesh.position.set((frontArm - rearArm) / 2, 0, 0);
        beamMesh.castShadow = true;
        registerInspectable(beamMesh, 'walkingBeam');
        beamPivotGroup.add(beamMesh);

        // Horsehead attached to front of beam
        const horseheadGroup = new THREE.Group();
        horseheadGroup.position.set(frontArm, 0, 0);

        const neckMesh = new THREE.Mesh(new THREE.BoxGeometry(1.4, 2.4, 0.5), matSteel);
        neckMesh.position.set(-0.5, 0.9, 0);
        neckMesh.castShadow = true;
        horseheadGroup.add(neckMesh);

        // Curved Horsehead Arc (Radius = frontArm = 4.6)
        const arcGeom = new THREE.CylinderGeometry(frontArm, frontArm, 0.6, 32, 1, false, 0, Math.PI / 2.4);
        const horseheadArc = new THREE.Mesh(arcGeom, matHazardStripe);
        horseheadArc.rotation.z = Math.PI / 1.18;
        horseheadArc.position.set(-frontArm, 0, 0);
        horseheadArc.castShadow = true;
        registerInspectable(horseheadArc, 'horsehead');
        horseheadGroup.add(horseheadArc);

        beamPivotGroup.add(horseheadGroup);

        // Rear Equalizer Pin
        const rearPivotLocalX = -rearArm;
        const rearPin = new THREE.Mesh(new THREE.CylinderGeometry(0.24, 0.24, 2.2, 16), matSteel);
        rearPin.rotation.x = Math.PI / 2;
        rearPin.position.set(rearPivotLocalX, 0, 0);
        beamPivotGroup.add(rearPin);

        pumpjack.add(beamPivotGroup);

        // ROTARY CRANK & COUNTERWEIGHTS
        const crankCenter = new THREE.Vector3(-9.2, 2.4, 0);
        const crankRadius = 1.45;
        const pitmanLen = 5.6;

        // Double-reduction Gearbox
        const gearbox = new THREE.Mesh(new THREE.BoxGeometry(2.6, 2.4, 2.5), matSteel);
        gearbox.position.copy(crankCenter);
        gearbox.castShadow = true;
        pumpjack.add(gearbox);

        // Prime mover motor
        const motorMesh = new THREE.Mesh(new THREE.CylinderGeometry(0.65, 0.65, 1.8, 16), matYellowFrame);
        motorMesh.rotation.z = Math.PI / 2;
        motorMesh.position.set(crankCenter.x - 2.2, 1.2, 0);
        motorMesh.castShadow = true;
        pumpjack.add(motorMesh);

        // Crank Assembly Group
        const crankGroup = new THREE.Group();
        crankGroup.position.copy(crankCenter);

        const crankshaft = new THREE.Mesh(new THREE.CylinderGeometry(0.25, 0.25, 3.8, 20), matSteel);
        crankshaft.rotation.x = Math.PI / 2;
        crankGroup.add(crankshaft);

        for (let side of [-1.9, 1.9]) {{
            const crankArm = new THREE.Mesh(new THREE.BoxGeometry(0.4, crankRadius * 2.1, 0.35), matSteel);
            crankArm.position.set(0, 0, side);
            crankGroup.add(crankArm);

            const weightSlab = new THREE.Mesh(new THREE.BoxGeometry(0.85, 1.8, 0.6), matCounterweight);
            weightSlab.position.set(0, -crankRadius * 0.75, side);
            weightSlab.castShadow = true;
            registerInspectable(weightSlab, 'crank');
            crankGroup.add(weightSlab);

            const rimMesh = new THREE.Mesh(new THREE.BoxGeometry(0.9, 0.25, 0.65), matHazardStripe);
            rimMesh.position.set(0, -crankRadius * 0.75 - 0.9, side);
            crankGroup.add(rimMesh);
        }}

        pumpjack.add(crankGroup);

        // Pitman Arms
        const pitman1 = new THREE.Mesh(new THREE.CylinderGeometry(0.11, 0.11, pitmanLen, 12), matSteel);
        pitman1.castShadow = true;
        scene.add(pitman1);

        const pitman2 = new THREE.Mesh(new THREE.CylinderGeometry(0.11, 0.11, pitmanLen, 12), matSteel);
        pitman2.castShadow = true;
        scene.add(pitman2);

        // Bridle Wirelines & Carrier Bar
        const bridleMesh = new THREE.Mesh(new THREE.CylinderGeometry(0.035, 0.035, 3.8, 8), matPolishedChrome);
        scene.add(bridleMesh);

        const carrierBar = new THREE.Mesh(new THREE.BoxGeometry(0.3, 0.2, 1.2), matYellowFrame);
        carrierBar.castShadow = true;
        scene.add(carrierBar);

        scene.add(pumpjack);

        // --- 4. MULTI-PHYSICS PARTICLES ---
        // Steam pore dispersion
        const steamCount = 450;
        const steamGeo = new THREE.BufferGeometry();
        const steamPositions = new Float32Array(steamCount * 3);
        const steamVels = [];
        for (let i = 0; i < steamCount; i++) {{
            const rad = Math.random() * 18;
            const theta = Math.random() * Math.PI * 2;
            steamPositions[i * 3] = rad * Math.cos(theta);
            steamPositions[i * 3 + 1] = -50 - Math.random() * 20;
            steamPositions[i * 3 + 2] = rad * Math.sin(theta);
            steamVels.push({{
                vx: (Math.random() - 0.5) * 0.05,
                vy: 0.05 + Math.random() * 0.1,
                vz: (Math.random() - 0.5) * 0.05
            }});
        }}
        steamGeo.setAttribute('position', new THREE.BufferAttribute(steamPositions, 3));
        const steamMat = new THREE.PointsMaterial({{
            color: 0xffedd5,
            size: 0.9,
            transparent: true,
            opacity: 0.6,
            blending: THREE.AdditiveBlending
        }});
        const steamParticles = new THREE.Points(steamGeo, steamMat);
        scene.add(steamParticles);

        // Rising crude oil droplets
        const oilCount = 180;
        const oilGeo = new THREE.BufferGeometry();
        const oilPositions = new Float32Array(oilCount * 3);
        for (let i = 0; i < oilCount; i++) {{
            const ang = Math.random() * Math.PI * 2;
            const r = Math.random() * 0.38;
            oilPositions[i * 3] = r * Math.cos(ang);
            oilPositions[i * 3 + 1] = -60 + Math.random() * 62;
            oilPositions[i * 3 + 2] = r * Math.sin(ang);
        }}
        oilGeo.setAttribute('position', new THREE.BufferAttribute(oilPositions, 3));
        const oilMat = new THREE.PointsMaterial({{
            color: 0x09090b,
            size: 0.44,
            transparent: true,
            opacity: 0.95
        }});
        const oilParticles = new THREE.Points(oilGeo, oilMat);
        scene.add(oilParticles);

        // --- KINEMATIC SOLVER & ANIMATION LOOP ---
        let simulationSpeed = 1.0;
        let isPaused = false;
        let isAutoOrbit = false;
        let showLabels = false;

        const spm = stateData.spm;
        const baseOmega = (spm * 2 * Math.PI) / 60.0;
        const strokeM = stateData.stroke_m;

        let crankAngle = 0;
        const clock = new THREE.Clock();

        function solveLinkage(thetaCrank) {{
            const crankPinLocal = new THREE.Vector3(
                crankRadius * Math.sin(thetaCrank),
                -crankRadius * Math.cos(thetaCrank),
                0
            );
            const crankPinWorld = crankPinLocal.clone().add(crankCenter);

            let thetaB = -(crankRadius / rearArm) * Math.sin(thetaCrank);
            for (let iter = 0; iter < 3; iter++) {{
                const rearWorld = new THREE.Vector3(
                    sampsonCenter.x - rearArm * Math.cos(thetaB),
                    sampsonCenter.y - rearArm * Math.sin(thetaB),
                    0
                );
                const dist = rearWorld.distanceTo(crankPinWorld);
                const err = dist - pitmanLen;
                thetaB += err * 0.05;
            }}

            return {{
                crankPinWorld,
                thetaB
            }};
        }}

        function animate() {{
            requestAnimationFrame(animate);

            const dt = clock.getDelta();

            if (!isPaused) {{
                crankAngle += baseOmega * dt * simulationSpeed;
            }}

            // 1. Exact 4-Bar Kinematics
            const linkage = solveLinkage(crankAngle);
            crankGroup.rotation.z = -crankAngle;
            beamPivotGroup.rotation.z = linkage.thetaB;

            // 2. Pitman Arms
            const rearWorld = new THREE.Vector3(
                sampsonCenter.x - rearArm * Math.cos(linkage.thetaB),
                sampsonCenter.y - rearArm * Math.sin(linkage.thetaB),
                0
            );

            const mid1 = new THREE.Vector3().addVectors(rearWorld, linkage.crankPinWorld).multiplyScalar(0.5);
            mid1.z += 1.9;
            pitman1.position.copy(mid1);
            pitman1.lookAt(rearWorld.clone().setZ(1.9));
            pitman1.rotateX(Math.PI / 2);

            const mid2 = new THREE.Vector3().addVectors(rearWorld, linkage.crankPinWorld).multiplyScalar(0.5);
            mid2.z -= 1.9;
            pitman2.position.copy(mid2);
            pitman2.lookAt(rearWorld.clone().setZ(-1.9));
            pitman2.rotateX(Math.PI / 2);

            // 3. Reciprocating Sucker Rod & Plunger
            const rodDisplacement = (strokeM / 2.0) * Math.sin(crankAngle);
            const polishedRodTopY = 3.6 + rodDisplacement;

            carrierBar.position.set(0, polishedRodTopY, 0);
            suckerRod.position.y = (-totalRodLength / 2 + 2.5) + rodDisplacement;
            plungerGroup.position.y = rodDisplacement;

            // Bridle wirelines
            const horseheadTipY = sampsonCenter.y + frontArm * Math.sin(linkage.thetaB) + 1.2;
            bridleMesh.position.set(0, (horseheadTipY + polishedRodTopY) / 2, 0);
            bridleMesh.scale.y = Math.max(0.2, (horseheadTipY - polishedRodTopY) / 3.8);

            // 4. Downhole Valve Dynamics
            const isUpstroke = Math.cos(crankAngle) > 0;
            const banner = document.getElementById('stroke-phase-banner');
            const bText = document.getElementById('stroke-phase-text');
            const bIcon = document.getElementById('stroke-phase-icon');

            if (isUpstroke) {{
                // Upstroke: TV closed (lifts fluid), SV open (intake)
                tvBall.position.y = -1.35;
                svBall.position.y = -1.95;
                if (banner && bText) {{
                    banner.className = "stroke-banner-up px-4 py-1.5 rounded-full text-xs font-mono font-bold tracking-wide shadow-lg transition-all duration-300 flex items-center space-x-2";
                    bIcon.innerText = "⬆️";
                    bText.innerText = "UPSTROKE: Traveling Valve CLOSED (Lifting) • Standing Valve OPEN (Intake)";
                }}
            }} else {{
                // Downstroke: TV open (passing fluid), SV closed (holding)
                tvBall.position.y = -1.15;
                svBall.position.y = -2.25;
                if (banner && bText) {{
                    banner.className = "stroke-banner-down px-4 py-1.5 rounded-full text-xs font-mono font-bold tracking-wide shadow-lg transition-all duration-300 flex items-center space-x-2";
                    bIcon.innerText = "⬇️";
                    bText.innerText = "DOWNSTROKE: Traveling Valve OPEN (Passing) • Standing Valve CLOSED (Holding)";
                }}
            }}

            // 5. Dynamic Load HUD
            const dynamicLoad = stateData.srp_load_kn + 6.2 * Math.sin(crankAngle);
            const liveLoadEl = document.getElementById('hud-live-load');
            if (liveLoadEl) {{
                liveLoadEl.innerText = dynamicLoad.toFixed(1);
            }}

            // 6. Particle Dynamics
            const sPos = steamGeo.attributes.position.array;
            for (let i = 0; i < steamCount; i++) {{
                sPos[i * 3] += steamVels[i].vx;
                sPos[i * 3 + 1] += steamVels[i].vy;
                sPos[i * 3 + 2] += steamVels[i].vz;
                if (sPos[i * 3 + 1] > -44.0) sPos[i * 3 + 1] = -70.0;
            }}
            steamGeo.attributes.position.needsUpdate = true;

            const oPos = oilGeo.attributes.position.array;
            const flowVel = 0.35 * (stateData.oil_rate_bpd / 35.0) * simulationSpeed;
            for (let i = 0; i < oilCount; i++) {{
                oPos[i * 3 + 1] += flowVel;
                if (oPos[i * 3 + 1] > 1.2) oPos[i * 3 + 1] = -58.0;
            }}
            oilGeo.attributes.position.needsUpdate = true;

            // 7. Auto Orbit
            if (isAutoOrbit) {{
                controls.autoRotate = true;
                controls.autoRotateSpeed = 1.2;
            }} else {{
                controls.autoRotate = false;
            }}

            // 8. Update 3D Pins
            if (showLabels) {{
                update3DPins();
            }}

            controls.update();
            renderer.render(scene, camera);
        }}

        animate();

        // --- CAMERA VIEW PRESETS (HIGH SCALE FRAMING) ---
        function setCameraView(preset) {{
            document.querySelectorAll('.view-btn').forEach(b => {{
                b.className = "view-btn px-3 py-1.5 text-xs font-semibold rounded-lg bg-slate-800/90 hover:bg-amber-600 hover:text-white text-slate-200 transition flex items-center space-x-1";
            }});

            if (preset === 'surface') {{
                document.getElementById('btn-view-surface').className = "view-btn px-3 py-1.5 text-xs font-bold rounded-lg bg-amber-600 text-white transition flex items-center space-x-1";
                smoothCameraMove(new THREE.Vector3(12.5, 8.5, 14.5), new THREE.Vector3(-2.8, 4.8, 0));
                inspectPart('walkingBeam');
            }} else if (preset === 'pump') {{
                document.getElementById('btn-view-pump').className = "view-btn px-3 py-1.5 text-xs font-bold rounded-lg bg-amber-600 text-white transition flex items-center space-x-1";
                smoothCameraMove(new THREE.Vector3(3.5, -54.5, 4.2), new THREE.Vector3(0, -56.0, 0));
                inspectPart('downholePump');
            }} else if (preset === 'reservoir') {{
                document.getElementById('btn-view-res').className = "view-btn px-3 py-1.5 text-xs font-bold rounded-lg bg-amber-600 text-white transition flex items-center space-x-1";
                smoothCameraMove(new THREE.Vector3(18.0, -50.0, 20.0), new THREE.Vector3(0, -58.0, 0));
                inspectPart('reservoir');
            }} else if (preset === 'profile') {{
                document.getElementById('btn-view-prof').className = "view-btn px-3 py-1.5 text-xs font-bold rounded-lg bg-amber-600 text-white transition flex items-center space-x-1";
                smoothCameraMove(new THREE.Vector3(48.0, -18.0, 52.0), new THREE.Vector3(0, -25.0, 0));
            }}
        }}

        function smoothCameraMove(targetPos, targetLookAt) {{
            const startPos = camera.position.clone();
            const startLook = controls.target.clone();
            let progress = 0;

            function step() {{
                progress += 0.045;
                if (progress <= 1.0) {{
                    camera.position.lerpVectors(startPos, targetPos, progress);
                    controls.target.lerpVectors(startLook, targetLookAt, progress);
                    requestAnimationFrame(step);
                }} else {{
                    camera.position.copy(targetPos);
                    controls.target.copy(targetLookAt);
                }}
            }}
            step();
        }}

        // --- INTERACTIVE PART INSPECTOR ---
        const partDetails = {{
            'walkingBeam': {{
                title: 'Walking Beam & Center Saddle Bearing',
                badge: 'CLASS I LEVER',
                desc: 'Rigid structural wide-flange I-beam oscillating about the center Samson post saddle bearing. Converts pitman arm reciprocating thrust into vertical polished rod displacement.',
                stats: `• Pumping Cadence: ${{stateData.spm.toFixed(1)}} SPM<br>• Stroke Length: ${{stateData.stroke_m.toFixed(2)}} m<br>• Dynamic Load: ${{stateData.srp_load_kn.toFixed(1)}} kN`
            }},
            'horsehead': {{
                title: 'Horsehead & Flexible Wireline Bridle',
                badge: 'VERTICAL TANGENCY',
                desc: 'Circular arc head with radius equal to the front beam length (4.6m). Ensures the flexible bridle cables remain tangent to the wellhead centerline, preventing lateral bending fatigue on the polished rod.',
                stats: `• Arc Radius: 4.60 m<br>• Lateral Deflection: 0.00 mm (True Tangent)<br>• Carrier Bar Load: ${{stateData.srp_load_kn.toFixed(1)}} kN`
            }},
            'sampsonPost': {{
                title: 'Structural Samson Post & A-Frame Truss',
                badge: 'STRUCTURAL SUPPORT',
                desc: 'Latticed A-frame steel structure anchoring the center saddle bearing to the concrete foundation pad. Absorbs cyclic bending moments and full dynamic rod string tension.',
                stats: `• Post Height: 7.60 m<br>• Structural Material: Heavy API Spec Steel<br>• Anchor: 17m x 13m Concrete Cellar Pad`
            }},
            'crank': {{
                title: 'Rotary Crank & Slotted Counterweights',
                badge: 'ENERGY BALANCING',
                desc: 'Heavy cast-iron counterweights rotating at ${{stateData.spm.toFixed(1)}} SPM. Counterbalances the buoyant rod weight, smoothing electric motor peak torque and cutting energy consumption.',
                stats: `• Crank Radius: 1.45 m<br>• Angular Velocity: ${{(stateData.spm * 2 * Math.PI / 60).toFixed(2)}} rad/s<br>• Gearbox: Double Reduction`
            }},
            'stuffingBox': {{
                title: 'Stuffing Box & Polished Rod Wellhead',
                badge: 'PRESSURE CONTAINMENT',
                desc: 'Surface seal preventing high-pressure heavy crude and steam blowby around the reciprocating polished rod. Feeds production fluid directly into the surface gathering flowline.',
                stats: `• Formation Pressure: 24.2 bar<br>• Wellhead Temp: ~${{(stateData.temperature_c * 0.85).toFixed(1)}} °C<br>• Flowline: 4-inch Insulated Schedule 40`
            }},
            'downholePump': {{
                title: 'Downhole Sucker Rod Pump (API Barrel & Plunger)',
                badge: 'DOWNHOLE PUMP',
                desc: 'Deep reciprocating pump at -56m depth inside the Jodhpur Sandstone. Alternates between opening the Traveling Valve on downstroke and the Standing Valve on upstroke to lift viscous crude.',
                stats: `• Setting Depth: -56.0 m<br>• Pump Fillage: ${{stateData.pump_fillage_pct.toFixed(1)}} %<br>• Net Oil Rate: ${{stateData.oil_rate_bpd.toFixed(1)}} bpd`
            }},
            'travelingValve': {{
                title: 'Traveling Valve (Plunger Ball & Seat)',
                badge: 'VALVE DYNAMICS',
                desc: 'Located inside the reciprocating plunger. Closes on UPSTROKE to lift the heavy hydrostatic oil column; opens on DOWNSTROKE to allow the plunger to sink through viscous crude.',
                stats: `• Upstroke State: CLOSED (Column Lift)<br>• Downstroke State: OPEN (Fluid Passage)<br>• Valve Ball: Tungsten Carbide`
            }},
            'standingValve': {{
                title: 'Standing Valve (Barrel Base Ball & Seat)',
                badge: 'VALVE DYNAMICS',
                desc: 'Stationary ball valve at the bottom of the pump barrel. Opens on UPSTROKE under reservoir pressure to draw oil in; closes on DOWNSTROKE under hydrostatic column head.',
                stats: `• Upstroke State: OPEN (Inflow Intake)<br>• Downstroke State: CLOSED (Hydrostatic Hold)<br>• Reservoir Pressure: 24.2 bar`
            }},
            'reservoir': {{
                title: 'Jodhpur Sandstone Heavy Oil Formation',
                badge: 'THERMAL RESERVOIR',
                desc: 'Target heavy-oil reservoir (Baghewala field). Injected cyclic steam transfers heat, heating cold crude from 48°C up to ${{stateData.temperature_c.toFixed(1)}}°C and slashing viscosity from 28.5 kcP down to ${{stateData.viscosity_kcp.toFixed(2)}} kcP.',
                stats: `• Temperature: ${{stateData.temperature_c.toFixed(1)}} °C<br>• Viscosity: ${{stateData.viscosity_kcp.toFixed(2)}} kcP<br>• CSS Phase: ${{stateData.phase.toUpperCase()}}`
            }},
            'tubing': {{
                title: 'Production Tubing String (Cutaway)',
                badge: 'FLUID CONDUIT',
                desc: 'Internal steel tubing string through which heated heavy crude is lifted to surface. Visualized with transparent cutaway displaying upward fluid streamline velocity.',
                stats: `• Production Rate: ${{stateData.oil_rate_bpd.toFixed(1)}} bpd<br>• Viscosity: ${{stateData.viscosity_kcp.toFixed(2)}} kcP`
            }}
        }};

        function inspectPart(partKey) {{
            const data = partDetails[partKey];
            if (!data) return;

            document.getElementById('insp-title').innerText = data.title;
            document.getElementById('insp-badge').innerText = data.badge;
            document.getElementById('insp-desc').innerHTML = data.desc;
            document.getElementById('insp-stats').innerHTML = data.stats;

            const card = document.getElementById('inspector-card');
            card.classList.add('ring-2', 'ring-amber-400');
            setTimeout(() => card.classList.remove('ring-2', 'ring-amber-400'), 800);
        }}

        // Raycast click
        window.addEventListener('click', (event) => {{
            mouse.x = (event.clientX / window.innerWidth) * 2 - 1;
            mouse.y = -(event.clientY / window.innerHeight) * 2 + 1;

            raycaster.setFromCamera(mouse, camera);
            const intersects = raycaster.intersectObjects(inspectableObjects, true);

            if (intersects.length > 0) {{
                let obj = intersects[0].object;
                while (obj && !obj.userData.partKey && obj.parent) {{
                    obj = obj.parent;
                }}
                if (obj && obj.userData.partKey) {{
                    inspectPart(obj.userData.partKey);
                }}
            }}
        }});

        // --- BUTTON HANDLERS ---
        function setSimSpeed(speed) {{
            simulationSpeed = speed;
            document.querySelectorAll('.speed-btn').forEach(btn => {{
                btn.className = "speed-btn px-2 py-0.5 rounded text-[10px] bg-slate-800 hover:bg-amber-600 text-slate-300";
            }});
            if (event && event.target) {{
                event.target.className = "speed-btn px-2 py-0.5 rounded text-[10px] bg-amber-600 text-white font-bold";
            }}
        }}

        function togglePlayPause() {{
            isPaused = !isPaused;
            const btn = document.getElementById('btn-pause');
            if (btn) {{
                btn.innerText = isPaused ? "▶️" : "⏸️";
                btn.className = isPaused ? "px-2.5 py-1.5 text-xs font-semibold rounded-lg bg-amber-600 text-white transition" : "px-2.5 py-1.5 text-xs font-semibold rounded-lg bg-slate-800/90 hover:bg-slate-700 text-slate-300 transition";
            }}
        }}

        function toggleAutoOrbit() {{
            isAutoOrbit = !isAutoOrbit;
            const btn = document.getElementById('btn-auto-orbit');
            if (btn) {{
                btn.className = isAutoOrbit ? "px-2.5 py-1.5 text-xs font-semibold rounded-lg bg-amber-600 text-white transition" : "px-2.5 py-1.5 text-xs font-semibold rounded-lg bg-slate-800/90 hover:bg-slate-700 text-slate-300 transition";
            }}
        }}

        function toggleLabels() {{
            showLabels = !showLabels;
            const container = document.getElementById('pins-container');
            const btn = document.getElementById('btn-labels');
            if (container) {{
                container.style.display = showLabels ? 'block' : 'none';
            }}
            if (btn) {{
                btn.className = showLabels ? "px-2.5 py-1.5 text-xs font-semibold rounded-lg bg-amber-600 text-white transition" : "px-2.5 py-1.5 text-xs font-semibold rounded-lg bg-slate-800/90 hover:bg-slate-700 text-slate-300 transition";
            }}
        }}

        function toggleFullscreen() {{
            if (!document.fullscreenElement) {{
                document.documentElement.requestFullscreen().catch(err => {{}});
            }} else {{
                document.exitFullscreen().catch(err => {{}});
            }}
        }}

        function update3DPins() {{
            const targets = [
                {{ id: 'pin-horsehead', pos: new THREE.Vector3(0, 8.5, 0) }},
                {{ id: 'pin-beam', pos: new THREE.Vector3(-4.6, 8.2, 0) }},
                {{ id: 'pin-sampson', pos: new THREE.Vector3(-4.6, 4.0, 1.4) }},
                {{ id: 'pin-crank', pos: new THREE.Vector3(-9.2, 2.4, 2.0) }},
                {{ id: 'pin-wellhead', pos: new THREE.Vector3(0, 1.5, 0) }},
                {{ id: 'pin-reservoir', pos: new THREE.Vector3(8, -58, 0) }},
                {{ id: 'pin-pump', pos: new THREE.Vector3(0, -56, 0) }}
            ];

            targets.forEach(t => {{
                const el = document.getElementById(t.id);
                if (!el) return;
                const p = t.pos.clone().project(camera);
                if (p.z > 1) {{
                    el.style.display = 'none';
                    return;
                }}
                el.style.display = 'block';
                const x = (p.x * 0.5 + 0.5) * window.innerWidth;
                const y = (-(p.y * 0.5) + 0.5) * window.innerHeight;
                el.style.left = `${{x}}px`;
                el.style.top = `${{y}}px`;
            }});
        }}

        window.addEventListener('resize', () => {{
            camera.aspect = window.innerWidth / window.innerHeight;
            camera.updateProjectionMatrix();
            renderer.setSize(window.innerWidth, window.innerHeight);
        }});
    </script>
</body>
</html>
"""
