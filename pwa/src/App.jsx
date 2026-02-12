import JSZip from "jszip";
import { useState, useRef, useCallback, useEffect } from "react";

// ============================================================
// DHG Graphics Resizer PWA — Phase 2
// Resize + Crop + Presets + Backgrounds + Gradients + Zip
// ============================================================

const SIZE_PRESETS = {
  "Headshots & Avatars": [
    { label: "200 × 200", w: 200, h: 200 },
    { label: "300 × 300", w: 300, h: 300 },
    { label: "400 × 400", w: 400, h: 400 },
    { label: "500 × 500", w: 500, h: 500 },
    { label: "800 × 800", w: 800, h: 800 },
  ],
  "Social Media Profiles": [
    { label: "Facebook 170×170", w: 170, h: 170 },
    { label: "Instagram 320×320", w: 320, h: 320 },
    { label: "LinkedIn 400×400", w: 400, h: 400 },
    { label: "X (Twitter) 400×400", w: 400, h: 400 },
    { label: "YouTube 800×800", w: 800, h: 800 },
    { label: "TikTok 200×200", w: 200, h: 200 },
  ],
  "Social Media Posts": [
    { label: "Instagram Square 1080×1080", w: 1080, h: 1080 },
    { label: "Instagram Story 1080×1920", w: 1080, h: 1920 },
    { label: "Instagram Landscape 1080×566", w: 1080, h: 566 },
    { label: "Facebook Post 1200×630", w: 1200, h: 630 },
    { label: "X Post 1200×675", w: 1200, h: 675 },
    { label: "Pinterest Pin 1000×1500", w: 1000, h: 1500 },
    { label: "LinkedIn Post 1200×627", w: 1200, h: 627 },
  ],
  "Banners & Headers": [
    { label: "Facebook Cover 820×312", w: 820, h: 312 },
    { label: "X Header 1500×500", w: 1500, h: 500 },
    { label: "LinkedIn Banner 1584×396", w: 1584, h: 396 },
    { label: "YouTube Banner 2560×1440", w: 2560, h: 1440 },
    { label: "Twitch Banner 1200×480", w: 1200, h: 480 },
  ],
  "Digital Ads (IAB)": [
    { label: "Medium Rectangle 300×250", w: 300, h: 250 },
    { label: "Leaderboard 728×90", w: 728, h: 90 },
    { label: "Wide Skyscraper 160×600", w: 160, h: 600 },
    { label: "Billboard 970×250", w: 970, h: 250 },
    { label: "Large Rectangle 336×280", w: 336, h: 280 },
    { label: "Half Page 300×600", w: 300, h: 600 },
    { label: "Mobile Banner 320×50", w: 320, h: 50 },
    { label: "Mobile Interstitial 320×480", w: 320, h: 480 },
  ],
  "Email & Web": [
    { label: "Email Header 600×200", w: 600, h: 200 },
    { label: "Hero Banner 1200×400", w: 1200, h: 400 },
    { label: "Full HD 1920×1080", w: 1920, h: 1080 },
    { label: "4K UHD 3840×2160", w: 3840, h: 2160 },
    { label: "OG Image 1200×630", w: 1200, h: 630 },
    { label: "Favicon 512×512", w: 512, h: 512 },
  ],
};

const CROP_MODES = [
  { id: "top", label: "Top", desc: "Preserves heads", icon: "↑" },
  { id: "center", label: "Center", desc: "Centered crop", icon: "⊕" },
  { id: "fill", label: "Fill", desc: "Pad edges", icon: "⬜" },
];

const EXPORT_FORMATS = [
  { id: "jpeg", label: "JPEG", ext: ".jpg", mime: "image/jpeg" },
  { id: "png", label: "PNG", ext: ".png", mime: "image/png" },
  { id: "webp", label: "WebP", ext: ".webp", mime: "image/webp" },
];

const B = {
  graphite: "#32374A",
  purple: "#663399",
  orange: "#F77E2D",
};

const BG_PRESETS = {
  "Solid Colors": [
    { label: "White", value: "#FFFFFF", type: "solid" },
    { label: "Light Gray", value: "#E0E0E0", type: "solid" },
    { label: "Professional Gray", value: "#808080", type: "solid" },
    { label: "Black", value: "#000000", type: "solid" },
    { label: "ONA Teal", value: "#49A3A1", type: "solid" },
    { label: "DHG Graphite", value: "#32374A", type: "solid" },
    { label: "DHG Purple", value: "#663399", type: "solid" },
    { label: "DHG Orange", value: "#F77E2D", type: "solid" },
  ],
  Gradients: [
    { label: "Corporate Blue", value: "#4A7AB5:#E8EEF5", dir: "down", type: "gradient" },
    { label: "NACE Brand", value: "#1D4BB7:#DFE7EF", dir: "down", type: "gradient" },
    { label: "NACE Full", value: "#1D4BB7:#DFE7EF:#1D4BB7", dir: "down", type: "gradient" },
    { label: "ONA Summit", value: "#49A3A1:#FFFFFF", dir: "down", type: "gradient" },
    { label: "DHG Brand", value: "#32374A:#663399:#F77E2D", dir: "down", type: "gradient" },
    { label: "DHG Radial", value: "#663399:#32374A", dir: "radial", type: "gradient" },
    { label: "Sunset Diagonal", value: "#F77E2D:#663399", dir: "diagonal", type: "gradient" },
    { label: "Purple Horizon", value: "#663399:#F77E2D", dir: "right", type: "gradient" },
  ],
  Special: [
    { label: "Transparent (PNG)", value: "TRANSPARENT", type: "transparent" },
  ],
};

function drawBackground(ctx, w, h, bg) {
  if (!bg || bg.type === "transparent") { ctx.clearRect(0, 0, w, h); return; }
  if (bg.type === "solid" || bg.type === "custom_solid") { ctx.fillStyle = bg.value; ctx.fillRect(0, 0, w, h); return; }

  if (bg.type === "gradient" || bg.type === "custom_gradient") {
    const raw = bg.type === "custom_gradient" ? bg.raw : bg.value;
    const parts = raw.split(":");
    const lastPart = parts[parts.length - 1].trim().toLowerCase();
    const directions = ["down", "right", "diagonal", "radial"];
    let dir = bg.dir || "down";
    let colorParts = parts;

    if (bg.type === "custom_gradient" && directions.includes(lastPart)) {
      dir = lastPart;
      colorParts = parts.slice(0, -1);
    }

    let grad;
    if (dir === "radial") {
      const cx = w / 2, cy = h / 2;
      grad = ctx.createRadialGradient(cx, cy, 0, cx, cy, Math.sqrt(cx * cx + cy * cy));
    } else if (dir === "right") {
      grad = ctx.createLinearGradient(0, 0, w, 0);
    } else if (dir === "diagonal") {
      grad = ctx.createLinearGradient(0, 0, w, h);
    } else {
      grad = ctx.createLinearGradient(0, 0, 0, h);
    }

    colorParts.forEach((c, i) => {
      grad.addColorStop(i / Math.max(colorParts.length - 1, 1), c.trim());
    });
    ctx.fillStyle = grad;
    ctx.fillRect(0, 0, w, h);
  }
}

function processImage(file, targetW, targetH, cropMode, format, quality, bg) {
  return new Promise((resolve, reject) => {
    const img = new Image();
    img.onload = () => {
      const canvas = document.createElement("canvas");
      canvas.width = targetW;
      canvas.height = targetH;
      const ctx = canvas.getContext("2d");
      const srcW = img.naturalWidth, srcH = img.naturalHeight;

      if (cropMode === "fill") {
        drawBackground(ctx, targetW, targetH, bg || { type: "solid", value: "#FFFFFF" });
        const scale = Math.min(targetW / srcW, targetH / srcH);
        const drawW = srcW * scale, drawH = srcH * scale;
        ctx.drawImage(img, 0, 0, srcW, srcH, (targetW - drawW) / 2, (targetH - drawH) / 2, drawW, drawH);
      } else {
        const scale = Math.max(targetW / srcW, targetH / srcH);
        const drawW = srcW * scale, drawH = srcH * scale;
        const offsetX = (targetW - drawW) / 2;
        const offsetY = cropMode === "top" ? 0 : (targetH - drawH) / 2;
        ctx.drawImage(img, 0, 0, srcW, srcH, offsetX, offsetY, drawW, drawH);
      }

      let actualFormat = format;
      if (bg && bg.type === "transparent" && format === "jpeg") actualFormat = "png";
      const fmt = EXPORT_FORMATS.find((f) => f.id === actualFormat);

      canvas.toBlob(
        (blob) => {
          if (blob) resolve({ blob, name: file.name.replace(/\.[^.]+$/, "") + fmt.ext, width: targetW, height: targetH, size: blob.size });
          else reject(new Error(`Failed to export ${file.name}`));
        },
        fmt.mime,
        actualFormat === "png" ? undefined : quality / 100
      );
      URL.revokeObjectURL(img.src);
    };
    img.onerror = () => { URL.revokeObjectURL(img.src); reject(new Error(`Failed to load ${file.name}`)); };
    img.src = URL.createObjectURL(file);
  });
}

async function downloadAsZip(results, zipName) {
  const zip = new JSZip();
  for (const r of results) zip.file(r.name, r.blob);
  const content = await zip.generateAsync({ type: "blob" });
  const a = document.createElement("a");
  a.href = URL.createObjectURL(content);
  a.download = zipName;
  a.click();
  URL.revokeObjectURL(a.href);
}

function BgSwatch({ bg, size = 24 }) {
  const ref = useRef(null);
  useEffect(() => {
    const canvas = ref.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    canvas.width = size; canvas.height = size;
    if (bg.type === "transparent") {
      const s = size / 4;
      for (let y = 0; y < 4; y++) for (let x = 0; x < 4; x++) {
        ctx.fillStyle = (x + y) % 2 === 0 ? "#ddd" : "#fff";
        ctx.fillRect(x * s, y * s, s, s);
      }
    } else drawBackground(ctx, size, size, bg);
  }, [bg, size]);
  return <canvas ref={ref} style={{ width: size, height: size, borderRadius: 4, border: "1px solid rgba(0,0,0,0.12)", flexShrink: 0 }} />;
}

function SectionLabel({ children }) {
  return <div style={{ fontSize: 11, fontWeight: 700, textTransform: "uppercase", letterSpacing: 1, color: B.purple, marginBottom: 8 }}>{children}</div>;
}

function DropZone({ onFiles, fileCount }) {
  const inputRef = useRef(null);
  const [dragOver, setDragOver] = useState(false);
  const handleDrop = useCallback((e) => { e.preventDefault(); setDragOver(false); const files = [...e.dataTransfer.files].filter((f) => f.type.startsWith("image/")); if (files.length) onFiles(files); }, [onFiles]);

  return (
    <div onDragOver={(e) => { e.preventDefault(); setDragOver(true); }} onDragLeave={() => setDragOver(false)} onDrop={handleDrop} onClick={() => inputRef.current?.click()}
      style={{ border: `2px dashed ${dragOver ? B.orange : B.purple}`, borderRadius: 12, padding: "36px 24px", textAlign: "center", cursor: "pointer", background: dragOver ? "rgba(102,51,153,0.06)" : "rgba(50,55,74,0.02)", transition: "all 0.2s ease" }}>
      <input ref={inputRef} type="file" accept="image/*" multiple style={{ display: "none" }} onChange={(e) => { const files = [...e.target.files].filter((f) => f.type.startsWith("image/")); if (files.length) onFiles(files); e.target.value = ""; }} />
      <div style={{ fontSize: 36, marginBottom: 6 }}>📁</div>
      <div style={{ fontSize: 15, fontWeight: 600, color: B.graphite, marginBottom: 3 }}>{fileCount > 0 ? `${fileCount} image${fileCount > 1 ? "s" : ""} loaded — drop more or click` : "Drop images here or click to browse"}</div>
      <div style={{ fontSize: 12, color: "#999" }}>JPG, PNG, WebP, TIFF, BMP</div>
    </div>
  );
}

function PresetSelector({ selected, onSelect, customW, customH, onCustomW, onCustomH }) {
  const [expanded, setExpanded] = useState(null);
  return (
    <div>
      <SectionLabel>Size Preset</SectionLabel>
      {Object.entries(SIZE_PRESETS).map(([cat, presets]) => (
        <div key={cat} style={{ marginBottom: 2 }}>
          <button onClick={() => setExpanded(expanded === cat ? null : cat)} style={{ width: "100%", textAlign: "left", padding: "7px 10px", background: expanded === cat ? "rgba(102,51,153,0.07)" : "transparent", border: "none", borderRadius: 5, cursor: "pointer", fontSize: 12, fontWeight: 600, color: B.graphite, display: "flex", justifyContent: "space-between", alignItems: "center" }}>
            {cat}<span style={{ transform: expanded === cat ? "rotate(90deg)" : "none", transition: "transform 0.15s", fontSize: 10 }}>▶</span>
          </button>
          {expanded === cat && (
            <div style={{ padding: "2px 0 6px 10px" }}>
              {presets.map((p) => {
                const isSel = selected && selected.w === p.w && selected.h === p.h && selected.label === p.label;
                return <button key={p.label} onClick={() => onSelect(p)} style={{ display: "block", width: "100%", textAlign: "left", padding: "5px 8px", margin: "1px 0", background: isSel ? B.purple : "transparent", color: isSel ? "#fff" : B.graphite, border: "none", borderRadius: 4, cursor: "pointer", fontSize: 11.5, fontWeight: isSel ? 600 : 400, transition: "all 0.1s" }}>{p.label}</button>;
              })}
            </div>
          )}
        </div>
      ))}
      <div style={{ marginTop: 6, padding: "8px 10px", background: "rgba(50,55,74,0.04)", borderRadius: 6 }}>
        <div style={{ fontSize: 11, fontWeight: 600, color: B.graphite, marginBottom: 6 }}>Custom Size</div>
        <div style={{ display: "flex", gap: 6, alignItems: "center" }}>
          <input type="number" placeholder="W" value={customW} onChange={(e) => onCustomW(e.target.value)} onFocus={() => onSelect(null)} style={{ flex: 1, padding: "5px 7px", border: "1px solid #ccc", borderRadius: 4, fontSize: 12, outline: "none" }} />
          <span style={{ color: "#999", fontSize: 12 }}>×</span>
          <input type="number" placeholder="H" value={customH} onChange={(e) => onCustomH(e.target.value)} onFocus={() => onSelect(null)} style={{ flex: 1, padding: "5px 7px", border: "1px solid #ccc", borderRadius: 4, fontSize: 12, outline: "none" }} />
        </div>
      </div>
    </div>
  );
}

function CropModeSelector({ mode, onChange }) {
  return (
    <div style={{ marginTop: 16 }}>
      <SectionLabel>Crop Mode</SectionLabel>
      <div style={{ display: "flex", gap: 5 }}>
        {CROP_MODES.map((cm) => (
          <button key={cm.id} onClick={() => onChange(cm.id)} style={{ flex: 1, padding: "8px 4px", background: mode === cm.id ? B.graphite : "#f3f3f6", color: mode === cm.id ? "#fff" : B.graphite, border: "none", borderRadius: 7, cursor: "pointer", transition: "all 0.15s" }}>
            <div style={{ fontSize: 16 }}>{cm.icon}</div>
            <div style={{ fontSize: 11, fontWeight: 600, marginTop: 1 }}>{cm.label}</div>
            <div style={{ fontSize: 9, opacity: 0.7, marginTop: 1 }}>{cm.desc}</div>
          </button>
        ))}
      </div>
    </div>
  );
}

function BackgroundSelector({ bg, onBg }) {
  const [customInput, setCustomInput] = useState("");
  const [showCustom, setShowCustom] = useState(false);
  const parseCustom = (raw) => {
    const t = raw.trim();
    if (!t) return null;
    if (t.toUpperCase() === "TRANSPARENT") return { type: "transparent", value: "TRANSPARENT" };
    if (/^#[0-9a-fA-F]{3,8}$/.test(t)) return { type: "custom_solid", value: t };
    if (t.includes(":")) return { type: "custom_gradient", raw: t, value: t };
    return null;
  };

  return (
    <div style={{ marginTop: 16 }}>
      <SectionLabel>Background</SectionLabel>
      <div style={{ fontSize: 10, color: "#999", marginBottom: 8 }}>Applies to Fill crop mode. Phase 3 adds BG removal for Top/Center modes.</div>
      {Object.entries(BG_PRESETS).map(([cat, items]) => (
        <div key={cat} style={{ marginBottom: 8 }}>
          <div style={{ fontSize: 10, fontWeight: 700, color: "#888", textTransform: "uppercase", letterSpacing: 0.8, marginBottom: 4 }}>{cat}</div>
          <div style={{ display: "flex", flexWrap: "wrap", gap: 4 }}>
            {items.map((item) => {
              const isSel = bg && bg.value === item.value && bg.type === item.type && (bg.dir || "down") === (item.dir || "down");
              return <button key={item.label} onClick={() => onBg(item)} title={item.label} style={{ display: "flex", alignItems: "center", gap: 5, padding: "4px 8px 4px 4px", background: isSel ? "rgba(102,51,153,0.12)" : "#f5f5f7", border: isSel ? `2px solid ${B.purple}` : "2px solid transparent", borderRadius: 6, cursor: "pointer", fontSize: 10.5, color: B.graphite, transition: "all 0.12s" }}><BgSwatch bg={item} size={18} />{item.label}</button>;
            })}
          </div>
        </div>
      ))}
      <button onClick={() => setShowCustom(!showCustom)} style={{ fontSize: 11, color: B.purple, background: "none", border: "none", cursor: "pointer", fontWeight: 600, padding: 0, marginTop: 4 }}>{showCustom ? "▾ Hide Custom" : "▸ Custom Color / Gradient"}</button>
      {showCustom && (
        <div style={{ marginTop: 6, padding: "8px 10px", background: "rgba(50,55,74,0.04)", borderRadius: 6 }}>
          <input type="text" placeholder="#hex or #c1:#c2:direction" value={customInput} onChange={(e) => setCustomInput(e.target.value)} onKeyDown={(e) => { if (e.key === "Enter") { const p = parseCustom(customInput); if (p) onBg(p); } }} style={{ width: "100%", padding: "5px 7px", border: "1px solid #ccc", borderRadius: 4, fontSize: 11, outline: "none", fontFamily: "monospace", boxSizing: "border-box" }} />
          <div style={{ fontSize: 9, color: "#999", marginTop: 4, lineHeight: 1.4 }}>Solid: <code>#663399</code> · Gradient: <code>#c1:#c2</code> · Direction: <code>#c1:#c2:right</code><br />Multi-stop: <code>#c1:#c2:#c3</code> · Radial: <code>#c1:#c2:radial</code></div>
          <button onClick={() => { const p = parseCustom(customInput); if (p) onBg(p); }} style={{ marginTop: 6, padding: "5px 12px", background: B.purple, color: "#fff", border: "none", borderRadius: 4, fontSize: 11, fontWeight: 600, cursor: "pointer" }}>Apply</button>
        </div>
      )}
      {bg && (
        <div style={{ marginTop: 8, display: "flex", alignItems: "center", gap: 6 }}>
          <BgSwatch bg={bg} size={20} />
          <span style={{ fontSize: 11, color: B.graphite, fontWeight: 600 }}>{bg.label || bg.value}</span>
          <button onClick={() => onBg(null)} style={{ marginLeft: "auto", background: "none", border: "none", color: "#c00", fontSize: 11, cursor: "pointer", fontWeight: 600 }}>Clear</button>
        </div>
      )}
    </div>
  );
}

function ExportSettings({ format, onFormat, quality, onQuality }) {
  return (
    <div style={{ marginTop: 16 }}>
      <SectionLabel>Export Format</SectionLabel>
      <div style={{ display: "flex", gap: 5, marginBottom: 8 }}>
        {EXPORT_FORMATS.map((f) => <button key={f.id} onClick={() => onFormat(f.id)} style={{ flex: 1, padding: "7px", background: format === f.id ? B.orange : "#f3f3f6", color: format === f.id ? "#fff" : B.graphite, border: "none", borderRadius: 5, cursor: "pointer", fontSize: 12, fontWeight: 600, transition: "all 0.15s" }}>{f.label}</button>)}
      </div>
      {format !== "png" && (
        <div>
          <div style={{ display: "flex", justifyContent: "space-between", fontSize: 11, color: "#888", marginBottom: 3 }}><span>Quality</span><span style={{ fontWeight: 600, color: B.graphite }}>{quality}%</span></div>
          <input type="range" min="50" max="100" value={quality} onChange={(e) => onQuality(Number(e.target.value))} style={{ width: "100%", accentColor: B.orange }} />
        </div>
      )}
    </div>
  );
}

function FileList({ files, onRemove, onClear }) {
  if (!files.length) return null;
  return (
    <div style={{ marginTop: 10 }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 6 }}>
        <span style={{ fontSize: 12, fontWeight: 600, color: B.graphite }}>{files.length} image{files.length > 1 ? "s" : ""}</span>
        <button onClick={onClear} style={{ background: "none", border: "none", color: "#c00", fontSize: 11, cursor: "pointer", fontWeight: 600 }}>Clear All</button>
      </div>
      <div style={{ maxHeight: 140, overflowY: "auto", background: "#fafafa", borderRadius: 6, padding: 4 }}>
        {files.map((f, i) => (
          <div key={i} style={{ display: "flex", justifyContent: "space-between", alignItems: "center", padding: "4px 6px", fontSize: 11, color: B.graphite, borderBottom: i < files.length - 1 ? "1px solid #eee" : "none" }}>
            <span style={{ overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap", maxWidth: "82%" }}>{f.name}</span>
            <button onClick={() => onRemove(i)} style={{ background: "none", border: "none", color: "#c00", cursor: "pointer", fontSize: 13, padding: "0 3px" }}>×</button>
          </div>
        ))}
      </div>
    </div>
  );
}

function ProgressLog({ logs, progress }) {
  const logRef = useRef(null);
  useEffect(() => { if (logRef.current) logRef.current.scrollTop = logRef.current.scrollHeight; }, [logs]);
  if (!logs.length) return null;
  return (
    <div style={{ marginTop: 14 }}>
      {progress !== null && <div style={{ height: 5, background: "#eee", borderRadius: 3, overflow: "hidden", marginBottom: 6 }}><div style={{ height: "100%", width: `${progress}%`, background: `linear-gradient(90deg, ${B.purple}, ${B.orange})`, borderRadius: 3, transition: "width 0.3s ease" }} /></div>}
      <div ref={logRef} style={{ maxHeight: 150, overflowY: "auto", background: B.graphite, borderRadius: 8, padding: 10, fontFamily: "'SF Mono', 'Fira Code', monospace", fontSize: 10.5, lineHeight: 1.6 }}>
        {logs.map((log, i) => <div key={i} style={{ color: log.type === "error" ? "#ff6b6b" : log.type === "success" ? "#69db7c" : log.type === "warn" ? "#ffd43b" : "#ccc" }}>{log.msg}</div>)}
      </div>
    </div>
  );
}

function PreviewGrid({ results }) {
  if (!results.length) return null;
  return (
    <div style={{ marginTop: 14 }}>
      <SectionLabel>Results Preview</SectionLabel>
      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(110px, 1fr))", gap: 8 }}>
        {results.map((r, i) => {
          const url = URL.createObjectURL(r.blob);
          return (
            <div key={i} style={{ background: "#f3f3f6", borderRadius: 7, overflow: "hidden", textAlign: "center" }}>
              <div style={{ width: "100%", aspectRatio: "1", backgroundColor: "#e8e8ec", backgroundImage: `url(${url}), linear-gradient(45deg, #ccc 25%, transparent 25%), linear-gradient(-45deg, #ccc 25%, transparent 25%), linear-gradient(45deg, transparent 75%, #ccc 75%), linear-gradient(-45deg, transparent 75%, #ccc 75%)`, backgroundSize: "contain, 12px 12px, 12px 12px, 12px 12px, 12px 12px", backgroundPosition: "center, 0 0, 0 6px, 6px -6px, -6px 0px", backgroundRepeat: "no-repeat, repeat, repeat, repeat, repeat" }} />
              <div style={{ padding: "4px 4px 6px", fontSize: 9.5, color: "#888", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>{r.name}<br /><span style={{ fontWeight: 600, color: B.graphite }}>{r.width}×{r.height}</span><span style={{ marginLeft: 4, color: "#aaa" }}>{(r.size / 1024).toFixed(0)}KB</span></div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

// ============================================================
// Main App
// ============================================================
export default function DHGGraphicsResizer() {
  const [files, setFiles] = useState([]);
  const [preset, setPreset] = useState({ label: "500 × 500", w: 500, h: 500 });
  const [customW, setCustomW] = useState("");
  const [customH, setCustomH] = useState("");
  const [cropMode, setCropMode] = useState("center");
  const [bg, setBg] = useState(null);
  const [format, setFormat] = useState("jpeg");
  const [quality, setQuality] = useState(92);
  const [processing, setProcessing] = useState(false);
  const [logs, setLogs] = useState([]);
  const [progress, setProgress] = useState(null);
  const [results, setResults] = useState([]);

  const addFiles = useCallback((newFiles) => { setFiles((prev) => [...prev, ...newFiles]); setResults([]); setLogs([]); setProgress(null); }, []);
  const removeFile = useCallback((idx) => { setFiles((prev) => prev.filter((_, i) => i !== idx)); }, []);
  const getTargetSize = () => { if (preset) return { w: preset.w, h: preset.h }; const w = parseInt(customW), h = parseInt(customH); if (w > 0 && h > 0) return { w, h }; return null; };
  const canProcess = files.length > 0 && getTargetSize() && !processing;

  const handleProcess = async () => {
    const size = getTargetSize();
    if (!size || !files.length) return;
    setProcessing(true); setLogs([]); setResults([]); setProgress(0);
    const newLogs = [], newResults = [];
    const log = (msg, type = "info") => { newLogs.push({ msg, type }); setLogs([...newLogs]); };
    const bgDesc = bg ? (bg.type === "transparent" ? "transparent" : bg.type === "solid" || bg.type === "custom_solid" ? bg.value : bg.label || bg.value || bg.raw) : "white (default)";
    log(`▸ Batch: ${files.length} image${files.length > 1 ? "s" : ""} → ${size.w}×${size.h}`);
    log(`  Mode: ${cropMode} | Format: ${format.toUpperCase()} ${format !== "png" ? quality + "%" : ""} | BG: ${bgDesc}`);
    if (bg && bg.type === "transparent" && format === "jpeg") log(`  ⚠ Transparent BG with JPEG — auto-switching to PNG`, "warn");

    for (let i = 0; i < files.length; i++) {
      const file = files[i];
      try {
        log(`  [${i + 1}/${files.length}] ${file.name}...`);
        const result = await processImage(file, size.w, size.h, cropMode, format, quality, bg);
        newResults.push(result);
        log(`  ✓ ${result.name} — ${(result.size / 1024).toFixed(1)} KB`, "success");
      } catch (err) { log(`  ✗ ${file.name}: ${err.message}`, "error"); }
      setProgress(Math.round(((i + 1) / files.length) * 100));
    }

    setResults([...newResults]);
    const totalKB = newResults.reduce((s, r) => s + r.size, 0) / 1024;
    log(`▸ Done: ${newResults.length}/${files.length} processed (${totalKB < 1024 ? totalKB.toFixed(0) + " KB" : (totalKB / 1024).toFixed(1) + " MB"} total)`, newResults.length === files.length ? "success" : "error");
    setProcessing(false);
  };

  const handleDownload = async () => {
    if (results.length === 1) { const a = document.createElement("a"); a.href = URL.createObjectURL(results[0].blob); a.download = results[0].name; a.click(); URL.revokeObjectURL(a.href); }
    else if (results.length > 1) {
      try { const size = getTargetSize(); await downloadAsZip(results, `dhg-resized-${size?.w || ""}x${size?.h || ""}.zip`); }
      catch { results.forEach((r, i) => { setTimeout(() => { const a = document.createElement("a"); a.href = URL.createObjectURL(r.blob); a.download = r.name; a.click(); }, i * 200); }); }
    }
  };

  return (
    <div style={{ minHeight: "100vh", background: "#f7f7f9", fontFamily: "'DM Sans', -apple-system, BlinkMacSystemFont, sans-serif" }}>
      <div style={{ background: `linear-gradient(135deg, ${B.graphite} 0%, ${B.purple} 60%, ${B.orange} 100%)`, padding: "16px 24px", color: "#fff" }}>
        <div style={{ maxWidth: 1140, margin: "0 auto", display: "flex", alignItems: "center", justifyContent: "space-between" }}>
          <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
            <div style={{ width: 34, height: 34, borderRadius: 7, background: "rgba(255,255,255,0.18)", backdropFilter: "blur(8px)", display: "flex", alignItems: "center", justifyContent: "center", fontSize: 16, fontWeight: 800, color: "#fff" }}>D</div>
            <div><div style={{ fontSize: 16, fontWeight: 700, letterSpacing: -0.2 }}>DHG Graphics Resizer</div><div style={{ fontSize: 10, opacity: 0.65 }}>Phase 2 — Resize · Crop · Backgrounds · Gradients · Export</div></div>
          </div>
          <div style={{ fontSize: 10, opacity: 0.55, display: "flex", gap: 12 }}><span>✅ Resize</span><span>✅ Backgrounds</span><span style={{ opacity: 0.5 }}>⬜ AI BG Removal</span><span style={{ opacity: 0.5 }}>⬜ PWA</span></div>
        </div>
      </div>

      <div style={{ maxWidth: 1140, margin: "0 auto", padding: "20px 24px", display: "flex", gap: 20 }}>
        <div style={{ width: 272, flexShrink: 0, background: "#fff", borderRadius: 10, padding: 16, boxShadow: "0 1px 4px rgba(0,0,0,0.05)", maxHeight: "calc(100vh - 100px)", overflowY: "auto" }}>
          <PresetSelector selected={preset} onSelect={setPreset} customW={customW} customH={customH} onCustomW={(v) => { setCustomW(v); if (v && customH) setPreset(null); }} onCustomH={(v) => { setCustomH(v); if (customW && v) setPreset(null); }} />
          <CropModeSelector mode={cropMode} onChange={setCropMode} />
          <BackgroundSelector bg={bg} onBg={setBg} />
          <ExportSettings format={format} onFormat={setFormat} quality={quality} onQuality={setQuality} />
        </div>
        <div style={{ flex: 1, minWidth: 0 }}>
          <DropZone onFiles={addFiles} fileCount={files.length} />
          <FileList files={files} onRemove={removeFile} onClear={() => { setFiles([]); setResults([]); setLogs([]); setProgress(null); }} />
          <div style={{ marginTop: 14, display: "flex", gap: 8 }}>
            <button onClick={handleProcess} disabled={!canProcess} style={{ flex: 1, padding: "12px 18px", background: canProcess ? `linear-gradient(135deg, ${B.purple}, ${B.orange})` : "#ddd", color: canProcess ? "#fff" : "#999", border: "none", borderRadius: 8, fontSize: 14, fontWeight: 700, cursor: canProcess ? "pointer" : "not-allowed", transition: "all 0.2s", letterSpacing: 0.2 }}>{processing ? "Processing..." : `Resize ${files.length || ""} Image${files.length !== 1 ? "s" : ""}`}</button>
            {results.length > 0 && <button onClick={handleDownload} style={{ padding: "12px 20px", background: B.graphite, color: "#fff", border: "none", borderRadius: 8, fontSize: 14, fontWeight: 700, cursor: "pointer", transition: "all 0.2s", whiteSpace: "nowrap" }}>⬇ {results.length > 1 ? `Download ZIP (${results.length})` : "Download"}</button>}
          </div>
          <ProgressLog logs={logs} progress={progress} />
          <PreviewGrid results={results} />
        </div>
      </div>
    </div>
  );
}
