/**
 * Модуль рендеринга векторной интерактивной схемы каната (SVG)
 */
export class RopeSvgRenderer {
  constructor(svgElement) {
    this.svg = svgElement;
    this.drawing = this.svg?.querySelector('[data-cfg-drawing]');
    this.prevEnds = [];
  }

  static eyePixels(cm) {
    return Math.min(146, Math.max(60, 46 + Number(cm || 1) * 2));
  }

  static endShape(end, w) {
    const half = w / 2;
    const bury = 34 + w * 1.4;
    switch (end.type) {
      case 'cut': return { width: 18 + half };
      case 'whip': return { width: 48 };
      case 'eye': {
        const L = RopeSvgRenderer.eyePixels(end.eye);
        return { width: bury + L + half, bury, L, h: 14 + L * 0.2 + half };
      }
      case 'thimble': {
        const L = 46 + w * 1.4;
        return { width: bury + L + half, bury, L, h: 12 + w * 0.9 };
      }
      case 'shackle': {
        const L = 46 + w * 1.4;
        const r = 10 + half;
        const pin = bury + L + half + 12 + w * 0.4;
        return { width: pin + 7, bury, L, h: 12 + w * 0.9, r, pin };
      }
      case 'soft': {
        const L = 54;
        const rx = 24 + w * 0.8;
        const ry = 12 + w * 0.6;
        const cx = bury + L + rx * 0.5;
        const knob = 3 + w * 0.62;
        return { width: cx + rx + knob, bury, L, h: 14 + L * 0.2 + half, rx, ry, cx, knob };
      }
      default: return { width: 0 };
    }
  }

  static drawEnd(end, geo, w, x0, cy, dir, sleeve = false) {
    const half = w / 2;
    const r1 = (v) => Math.round(v * 10) / 10;
    const X = (x) => r1(x0 + dir * x);
    const Y = (y) => r1(cy + y);
    const P = (x, y) => `${X(x)} ${Y(y)}`;
    const sweep = (flag) => (dir === 1 ? flag : 1 - flag);
    const minX = (a, b) => Math.min(X(a), X(b));

    const strand = (d, width = w, cap = 'butt') => (
      `<path class="rope-preview__edge" d="${d}" stroke-width="${r1(width + 2.5)}" stroke-linecap="${cap}"/>` +
      `<path class="rope-preview__strand" d="${d}" stroke-width="${r1(width)}" stroke-linecap="${cap}"/>`
    );
    const shade = (a, b) => `<rect class="rope-preview__shade" x="${minX(a, b)}" y="${Y(-half)}" width="${r1(Math.abs(b - a))}" height="${r1(w)}"/>`;
    const loop = (b, L, h) => {
      const q = half * 0.5;
      return `M${P(b - 6, -q)} C${P(b + L * 0.3, -h)} ${P(b + L, -h * 0.95)} ${P(b + L, 0)} ` +
        `C${P(b + L, h * 0.95)} ${P(b + L * 0.3, h)} ${P(b - 6, q)}`;
    };
    const taper = (b) => {
      const t = half * 1.45;
      const top = `M${P(-1, -half)} C${P(b * 0.5, -half)} ${P(b * 0.6, -t)} ${P(b, -t)}`;
      const bottom = `M${P(-1, half)} C${P(b * 0.5, half)} ${P(b * 0.6, t)} ${P(b, t)}`;
      const body = `${top} L${P(b + 2, 0)} L${P(b, t)} C${P(b * 0.6, t)} ${P(b * 0.5, half)} ${P(-1, half)} Z`;
      return `<path class="rope-preview__fill" d="${body}"/><path class="rope-preview__shade" d="${body}"/>` +
        `<path class="rope-preview__outline" d="${top} ${bottom}"/>`;
    };
    const thimble = (b, L, h) => {
      const hi = h - half;
      const tip = b + L - half;
      const d = `M${P(b + 8, 0)} C${P(b + L * 0.35, -hi)} ${P(tip, -hi * 0.95)} ${P(tip, 0)} ` +
        `C${P(tip, hi * 0.95)} ${P(b + L * 0.35, hi)} ${P(b + 8, 0)}`;
      return `<path class="rope-preview__metal-edge" d="${d}" stroke-width="5.5"/>` +
        `<path class="rope-preview__metal" d="${d}" stroke-width="3.2"/>`;
    };
    const sleeveOn = (d) => (sleeve
      ? `<path class="rope-preview__sleeve-edge" d="${d}" pathLength="100" stroke-width="${r1(w * 1.3 + 2.5)}"/>` +
        `<path class="rope-preview__sleeve" d="${d}" pathLength="100" stroke-width="${r1(w * 1.3)}"/>`
      : '');

    switch (end.type) {
      case 'cut': {
        const len = 18;
        return strand(`M${P(-2, 0)} L${P(len, 0)}`, w, 'round') + shade(-2, len - half * 0.2) +
          `<ellipse class="rope-preview__melt" cx="${X(len + half * 0.35)}" cy="${Y(0)}" rx="${r1(half * 0.55)}" ry="${r1(half * 0.9)}"/>`;
      }
      case 'whip': {
        const len = 48 - half;
        return strand(`M${P(-2, 0)} L${P(len, 0)}`, w, 'round') + shade(-2, len) +
          `<rect class="rope-preview__whip" x="${minX(14, 36)}" y="${Y(-half - 1.5)}" width="22" height="${r1(w + 3)}" rx="2"/>`;
      }
      case 'eye': {
        const d = loop(geo.bury, geo.L, geo.h);
        return strand(d) + sleeveOn(d) + taper(geo.bury);
      }
      case 'thimble': {
        const d = loop(geo.bury, geo.L, geo.h);
        return strand(d) + thimble(geo.bury, geo.L, geo.h) + taper(geo.bury);
      }
      case 'shackle': {
        const { bury: b, L, h, r, pin } = geo;
        const e = b + L;
        const bow = `M${P(pin, -r)} L${P(e - r * 0.35, -r)} A${r1(r)} ${r1(r)} 0 0 ${sweep(0)} ${P(e - r * 0.35, r)} L${P(pin, r)}`;
        return `<path class="rope-preview__metal-edge" d="${bow}" stroke-width="8"/>` +
          `<path class="rope-preview__metal" d="${bow}" stroke-width="5.4"/>` +
          strand(loop(b, L, h)) + thimble(b, L, h) + taper(b) +
          `<rect class="rope-preview__metal-part" x="${r1(X(pin) - 3.5)}" y="${Y(-r - 7)}" width="7" height="${r1(2 * r + 14)}" rx="3.5"/>` +
          `<circle class="rope-preview__metal-part" cx="${X(pin)}" cy="${Y(-r - 7)}" r="5.5"/>` +
          `<rect class="rope-preview__metal-part" x="${r1(X(pin) - 5)}" y="${Y(r + 4)}" width="10" height="7" rx="1.5"/>`;
      }
      case 'soft': {
        const { bury: b, L, h, rx, ry, cx, knob } = geo;
        const rw = w * 0.8;
        const ring = `M${P(cx - rx, 0)} A${r1(rx)} ${r1(ry)} 0 1 ${sweep(1)} ${P(cx + rx, 0)} ` +
          `A${r1(rx)} ${r1(ry)} 0 1 ${sweep(1)} ${P(cx - rx, 0)}`;
        const top = `M${P(cx - rx, 0)} A${r1(rx)} ${r1(ry)} 0 0 ${sweep(1)} ${P(cx + rx, 0)}`;
        const d = loop(b, L, h);
        const kx = cx + rx;
        return strand(ring, rw) + strand(d) + sleeveOn(d) + taper(b) + strand(top, rw) +
          `<circle class="rope-preview__body" cx="${X(kx)}" cy="${Y(0)}" r="${r1(knob)}"/>` +
          `<path class="rope-preview__knot" d="M${P(kx - knob * 0.5, -knob * 0.8)} Q${P(kx + knob * 0.3, 0)} ${P(kx - knob * 0.5, knob * 0.8)} ` +
          `M${P(kx + knob * 0.2, -knob * 0.9)} Q${P(kx + knob, 0)} ${P(kx + knob * 0.2, knob * 0.9)}"/>`;
      }
      default: return '';
    }
  }

  render({ diameterMm = 10, ends = [{ type: 'cut' }, { type: 'cut' }], lengthM = 10, sleeve = false }) {
    if (!this.svg || !this.drawing) return;

    const d = diameterMm;
    const box = this.svg.getBoundingClientRect().width || 800;
    const vbW = Math.round(Math.min(1000, Math.max(620, box)));
    const vbH = 250;
    const cy = 112;
    const pad = 30;
    const k = vbW / box;
    const w = 5 + d * 1.15;
    const half = w / 2;
    const geo = ends.map((e) => RopeSvgRenderer.endShape(e, w));
    const xA = pad + geo[0].width;
    const xB = vbW - pad - geo[1].width;
    const xm = (xA + xB) / 2;
    const r1 = (v) => Math.round(v * 10) / 10;

    this.svg.setAttribute('viewBox', `0 0 ${vbW} ${vbH}`);
    const changed = ends.map((e, i) => !this.prevEnds[i] || this.prevEnds[i].type !== e.type || this.prevEnds[i].eye !== e.eye);
    this.prevEnds = ends;
    const endGroup = (i, markup) => `<g class="rope-preview__end${changed[i] ? ' rope-preview__end--enter' : ''}">${markup}</g>`;

    let s = `<path class="rope-preview__edge" d="M${r1(xA)} ${cy}H${r1(xB)}" stroke-width="${r1(w + 2.5)}"/>`;
    s += endGroup(0, RopeSvgRenderer.drawEnd(ends[0], geo[0], w, xA, cy, -1, sleeve));
    s += endGroup(1, RopeSvgRenderer.drawEnd(ends[1], geo[1], w, xB, cy, 1, sleeve));
    s += `<rect class="rope-preview__fill" x="${r1(xA)}" y="${r1(cy - half)}" width="${r1(xB - xA)}" height="${r1(w)}"/>`;
    s += `<rect class="rope-preview__shade" x="${r1(xA)}" y="${r1(cy - half)}" width="${r1(xB - xA)}" height="${r1(w)}"/>`;

    // Разрыв посередине при длинном отображении
    if (xB - xA > 120) {
      const t = cy - half - 7;
      const b = cy + half + 7;
      s += `<path class="rope-preview__gap" d="M${r1(xm - 3)} ${r1(t)}H${r1(xm + 7)}L${r1(xm + 3)} ${r1(b)}H${r1(xm - 7)}Z"/>`;
      s += `<path class="rope-preview__gap-line" d="M${r1(xm - 3)} ${r1(t)}L${r1(xm - 7)} ${r1(b)}M${r1(xm + 7)} ${r1(t)}L${r1(xm + 3)} ${r1(b)}"/>`;
    }

    // Метки концов A и B
    const markR = r1(12 * Math.min(k, 1.6));
    [[pad + geo[0].width / 2, 'A'], [vbW - pad - geo[1].width / 2, 'B']].forEach(([x, letter]) => {
      s += `<circle class="rope-preview__mark" cx="${r1(x)}" cy="${markR + 2}" r="${markR}"/>`;
      s += `<text class="rope-preview__mark-text" x="${r1(x)}" y="${r1(markR + 2 + markR * 0.36)}" font-size="${r1(markR)}">${letter}</text>`;
    });

    // Размерная линия рабочей длины
    const dy = vbH - 24;
    const fs = r1(15 * Math.min(k, 1.7));
    const gap = fs * 3.6;
    const x1 = pad;
    const x2 = vbW - pad;
    s += `<path class="rope-preview__dim-guide" d="M${x1} ${r1(cy + half + 8)}V${dy - 8}M${x2} ${r1(cy + half + 8)}V${dy - 8}"/>`;
    s += `<path class="rope-preview__dim" d="M${x1} ${dy}H${r1(xm - gap)}M${r1(xm + gap)} ${dy}H${x2}` +
      `M${x1 - 4} ${dy + 4}L${x1 + 4} ${dy - 4}M${x2 - 4} ${dy + 4}L${x2 + 4} ${dy - 4}"/>`;
    s += `<text class="rope-preview__dim-text" x="${r1(xm)}" y="${r1(dy + fs * 0.36)}" font-size="${fs}">${lengthM} м</text>`;

    this.drawing.innerHTML = s;
  }
}
