/* объёмная верёвка под LIROS */
(function () {
  'use strict';

  const motion = window.matchMedia('(prefers-reduced-motion: reduce)');
  const radius = 14;
  const step = 2.5;
  const sides = 28;

  function photoTexture(photo) {
    const strip = document.createElement('canvas');
    strip.width = 256;
    strip.height = 128;
    const paint = strip.getContext('2d');
    paint.translate(0, 64);
    paint.scale(256 / 270, 128 / 104);
    paint.rotate(-Math.atan2(59, 263));
    paint.translate(-650, -359);
    paint.drawImage(photo, 0, 0);

    const tile = document.createElement('canvas');
    tile.width = 512;
    tile.height = 128;
    const surface = tile.getContext('2d');
    surface.drawImage(strip, 0, 0);
    surface.translate(tile.width, 0);
    surface.scale(-1, 1);
    surface.drawImage(strip, 0, 0);
    return tile;
  }

  function normalize(vector) {
    const size = Math.hypot(...vector) || 1;
    return vector.map(value => value / size);
  }

  const yieldFrame = () => new Promise(resolve => setTimeout(resolve, 0));
  async function tube(path) {
    const length = path.getTotalLength();
    const segments = Math.ceil(length / step);
    const centers = [];
    for (let i = 0; i <= segments; i++) {
      if(i && i % 32 === 0) await yieldFrame();
      const at = length * i / segments;
      const point = path.getPointAtLength(at);
      const before = path.getPointAtLength(Math.max(0, at - 1));
      const after = path.getPointAtLength(Math.min(length, at + 1));
      const direction = normalize([after.x - before.x, after.y - before.y, 0]);
      // Поднимаем возвращающуюся часть петель над уходящей.
      centers.push({ x: point.x, y: point.y, z: direction[1] * 25, at });
    }

    const vertices = [];
    const indices = [];
    const frames = [];
    const repeat = radius * 2 * 4;
    for (let i=0;i<centers.length;i++) {
      if(i && i % 32 === 0) await yieldFrame();
      const center=centers[i];
      const before = centers[Math.max(0, i - 1)];
      const after = centers[Math.min(segments, i + 1)];
      const tangent = normalize([after.x - before.x, after.y - before.y, after.z - before.z]);
      const normal = normalize([-tangent[1], tangent[0], 0]);
      const binormal = normalize([
        tangent[1] * normal[2] - tangent[2] * normal[1],
        tangent[2] * normal[0] - tangent[0] * normal[2],
        tangent[0] * normal[1] - tangent[1] * normal[0]
      ]);
      frames.push({ tangent, normal, binormal });
      for (let side = 0; side <= sides; side++) {
        const angle = -Math.PI + side / sides * Math.PI * 2;
        const radial = normal.map((value, axis) => value * Math.sin(angle) + binormal[axis] * Math.cos(angle));
        const around = normal.map((value, axis) => value * Math.cos(angle) - binormal[axis] * Math.sin(angle));
        const r = radius * (1 + 0.012 * Math.cos(center.at / repeat * Math.PI * 24));
        vertices.push(center.x + radial[0] * r, center.y + radial[1] * r, center.z + radial[2] * r,
          ...radial, center.at / repeat, 0.5 + angle / Math.PI, center.at, ...tangent, ...around);
        if (i < segments && side < sides) {
          const a = i * (sides + 1) + side;
          const b = a + sides + 1;
          indices.push(a, b, a + 1, a + 1, b, b + 1);
        }
      }
    }
    return { length, segments, centers, frames, repeat,
      vertices: new Float32Array(vertices), indices: new Uint16Array(indices) };
  }

  function renderer(canvas, mesh, texture) {
    const gl = canvas.getContext('webgl', { alpha: true, antialias: true, preserveDrawingBuffer: true });
    if (!gl) throw new Error('WebGL unavailable');
    function shader(type, source) {
      const result = gl.createShader(type);
      gl.shaderSource(result, source);
      gl.compileShader(result);
      if (!gl.getShaderParameter(result, gl.COMPILE_STATUS)) throw new Error(gl.getShaderInfoLog(result));
      return result;
    }
    const program = gl.createProgram();
    gl.attachShader(program, shader(gl.VERTEX_SHADER, `
      attribute vec3 aPosition;
      attribute vec3 aNormal;
      attribute vec2 aUV;
      attribute float aDistance;
      attribute vec3 aTangent;
      attribute vec3 aAround;
      uniform vec4 uViewport;
      uniform float uScale;
      varying vec3 vPosition;
      varying vec3 vNormal;
      varying vec2 vUV;
      varying float vDistance;
      varying vec3 vTangent;
      varying vec3 vAround;
      void main() {
        vec3 centered = aPosition - vec3(720.0, 150.0, 0.0);
        vec3 tilted = vec3(centered.x, centered.y * 0.99027 - centered.z * 0.13917,
          centered.y * 0.13917 + centered.z * 0.99027);
        vec3 camera = vec3(tilted.x * 0.99756 - tilted.z * 0.06976, tilted.y,
          tilted.x * 0.06976 + tilted.z * 0.99756);
        vec2 screen = (camera.xy + vec2(720.0, 150.0)) * uScale + uViewport.zw;
        gl_Position = vec4(screen.x / uViewport.x * 2.0 - 1.0,
          1.0 - screen.y / uViewport.y * 2.0, -camera.z / 200.0, 1.0);
        vPosition = aPosition;
        vNormal = aNormal;
        vUV = aUV;
        vDistance = aDistance;
        vTangent = aTangent;
        vAround = aAround;
      }
    `));
    gl.attachShader(program, shader(gl.FRAGMENT_SHADER, `
      precision mediump float;
      uniform sampler2D uPhoto;
      uniform float uReveal;
      varying vec3 vPosition;
      varying vec3 vNormal;
      varying vec2 vUV;
      varying float vDistance;
      varying vec3 vTangent;
      varying vec3 vAround;
      float relief(vec2 uv) {
        return dot(texture2D(uPhoto, uv).rgb, vec3(0.25, 0.5, 0.25));
      }
      void main() {
        if (vDistance > uReveal) discard;
        vec3 color = texture2D(uPhoto, vUV).rgb;
        float along = relief(vUV + vec2(0.004, 0.0)) - relief(vUV - vec2(0.004, 0.0));
        float across = relief(vUV + vec2(0.0, 0.01)) - relief(vUV - vec2(0.0, 0.01));
        vec3 normal = normalize(vNormal - vTangent * along * 1.4 - vAround * across * 0.45);
        vec3 light = normalize(vec3(-0.35, -0.6, 0.72));
        vec3 view = normalize(vec3(0.06976, 0.13883, 0.98785));
        float diffuse = max(0.0, dot(normal, light));
        float shine = pow(max(0.0, dot(normal, normalize(light + view))), 28.0);
        float facing = max(0.0, dot(normal, view));
        float rounded = 0.18 + 0.82 * pow(facing, 0.45);
        vec3 linear = pow(color, vec3(2.2));
        linear *= (0.19 + diffuse * 1.25) * rounded;
        linear += vec3(0.1, 0.2, 0.32) * shine * 0.55;

        // Контактная тень на нижней пряди двух пересечений.
        vec2 first = vPosition.xy - vec2(591.0, 193.0);
        vec2 second = vPosition.xy - vec2(841.0, 193.0);
        float distance1 = abs(dot(first, normalize(vec2(-0.73, 0.68))));
        float distance2 = abs(dot(second, normalize(vec2(-0.73, 0.68))));
        float contact = max((1.0 - smoothstep(12.0, 24.0, distance1)) * (1.0 - smoothstep(22.0, 38.0, length(first))),
          (1.0 - smoothstep(12.0, 24.0, distance2)) * (1.0 - smoothstep(22.0, 38.0, length(second))));
        linear *= 1.0 - contact * (1.0 - smoothstep(-5.0, 10.0, vPosition.z)) * 0.75;
        gl_FragColor = vec4(pow(max(linear, vec3(0.0)), vec3(1.0 / 2.2)), 1.0);
      }
    `));
    gl.linkProgram(program);
    if (!gl.getProgramParameter(program, gl.LINK_STATUS)) throw new Error(gl.getProgramInfoLog(program));
    gl.useProgram(program);
    const attributes = [['aPosition', 3], ['aNormal', 3], ['aUV', 2], ['aDistance', 1], ['aTangent', 3], ['aAround', 3]];
    function bindVertices(buffer) {
      gl.bindBuffer(gl.ARRAY_BUFFER, buffer);
      let offset = 0;
      attributes.forEach(([name, size]) => {
        const location = gl.getAttribLocation(program, name);
        gl.enableVertexAttribArray(location);
        gl.vertexAttribPointer(location, size, gl.FLOAT, false, 15 * 4, offset * 4);
        offset += size;
      });
    }
    const vertexBuffer = gl.createBuffer();
    gl.bindBuffer(gl.ARRAY_BUFFER, vertexBuffer);
    gl.bufferData(gl.ARRAY_BUFFER, mesh.vertices, gl.STATIC_DRAW);
    const indexBuffer = gl.createBuffer();
    gl.bindBuffer(gl.ELEMENT_ARRAY_BUFFER, indexBuffer);
    gl.bufferData(gl.ELEMENT_ARRAY_BUFFER, mesh.indices, gl.STATIC_DRAW);
    const capBuffer = gl.createBuffer();
    const photo = gl.createTexture();
    gl.bindTexture(gl.TEXTURE_2D, photo);
    gl.texImage2D(gl.TEXTURE_2D, 0, gl.RGBA, gl.RGBA, gl.UNSIGNED_BYTE, texture);
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MIN_FILTER, gl.LINEAR_MIPMAP_LINEAR);
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MAG_FILTER, gl.LINEAR);
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_S, gl.REPEAT);
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_T, gl.REPEAT);
    gl.generateMipmap(gl.TEXTURE_2D);
    gl.enable(gl.DEPTH_TEST);
    gl.depthFunc(gl.LEQUAL);
    const viewport = gl.getUniformLocation(program, 'uViewport');
    const scaleUniform = gl.getUniformLocation(program, 'uScale');
    const reveal = gl.getUniformLocation(program, 'uReveal');

    return {
      resize(width, height, scale, x, y, ratio) {
        canvas.width = Math.round(width * ratio);
        canvas.height = Math.round(height * ratio);
        gl.viewport(0, 0, canvas.width, canvas.height);
        gl.uniform4f(viewport, width, height, x, y);
        gl.uniform1f(scaleUniform, scale);
      },
      draw(end) {
        gl.clearColor(0, 0, 0, 0);
        gl.clear(gl.COLOR_BUFFER_BIT | gl.DEPTH_BUFFER_BIT);
        if (!end) return;
        gl.uniform1f(reveal, end + 0.01);
        bindVertices(vertexBuffer);
        gl.bindBuffer(gl.ELEMENT_ARRAY_BUFFER, indexBuffer);
        const count = Math.min(mesh.segments, Math.ceil(end / mesh.length * mesh.segments)) * sides * 6;
        gl.drawElements(gl.TRIANGLES, count, gl.UNSIGNED_SHORT, 0);

        if (end < mesh.length) {
          const i = Math.min(mesh.segments - 1, Math.floor(end / mesh.length * mesh.segments));
          const a = mesh.centers[i];
          const b = mesh.centers[i + 1];
          const mix = (end - a.at) / (b.at - a.at);
          const center = [a.x + (b.x - a.x) * mix, a.y + (b.y - a.y) * mix, a.z + (b.z - a.z) * mix];
          const frame = mesh.frames[i];
          const cap = [];
          function vertex(position, uv) {
            cap.push(...position, ...frame.tangent, ...uv, end, ...frame.normal, ...frame.binormal);
          }
          vertex(center, [end / mesh.repeat, 0.5]);
          for (let side = 0; side <= sides; side++) {
            const angle = side / sides * Math.PI * 2;
            const radial = frame.normal.map((value, axis) => value * Math.sin(angle) + frame.binormal[axis] * Math.cos(angle));
            vertex(center.map((value, axis) => value + radial[axis] * radius),
              [end / mesh.repeat + Math.sin(angle) * 0.07, 0.5 + Math.cos(angle) * 0.5]);
          }
          gl.bindBuffer(gl.ARRAY_BUFFER, capBuffer);
          gl.bufferData(gl.ARRAY_BUFFER, new Float32Array(cap), gl.DYNAMIC_DRAW);
          bindVertices(capBuffer);
          gl.drawArrays(gl.TRIANGLE_FAN, 0, sides + 2);
        }
      }
    };
  }

  async function init(section) {
    const rope = section.querySelector('.specialist__rope');
    const canvas = section.querySelector('.specialist__tube');
    const shadow = section.querySelector('.specialist__shadow');
    const path = section.querySelector('#specialist-path');
    const mask = section.querySelector('.specialist__mask');
    if (!rope || !canvas || !path || !shadow || !mask) return;
    const mesh = await tube(path);
    const paint = shadow.getContext('2d');
    let scene = null;
    let raf = 0;
    let scale = 1;
    let x = 0;
    let y = 0;
    let ratio = 1;
    let last = -1;

    function drawShadow(end) {
      paint.setTransform(1, 0, 0, 1, 0, 0);
      paint.clearRect(0, 0, shadow.width, shadow.height);
      if (!end) return;
      paint.setTransform(scale * ratio, 0, 0, scale * ratio, x * ratio, y * ratio);
      paint.beginPath();
      mesh.centers.forEach((point, i) => {
        if (point.at <= end) {
          i ? paint.lineTo(point.x, point.y) : paint.moveTo(point.x, point.y);
        }
      });
      const tip = path.getPointAtLength(end);
      paint.lineTo(tip.x, tip.y);
      paint.lineWidth = radius * 2 - 2;
      paint.lineCap = 'round';
      paint.strokeStyle = 'rgba(0, 4, 10, 0.5)';
      paint.shadowColor = 'rgba(0, 0, 0, 0.9)';
      paint.shadowBlur = 8 * scale * ratio;
      paint.shadowOffsetX = 3 * scale * ratio;
      paint.shadowOffsetY = 8 * scale * ratio;
      paint.stroke();
    }

    function draw() {
      raf = 0;
      const top = rope.getBoundingClientRect().top;
      const progress = motion.matches ? 1 : Math.min(1, Math.max(0,
        (innerHeight * 0.7 - top) / (innerHeight * 0.45)));
      mask.style.strokeDashoffset = (1 - progress).toFixed(5);
      const end = progress * mesh.length;
      if (!scene || Math.abs(last - end) < 0.1) return;
      last = end;
      drawShadow(end);
      scene.draw(end);
    }

    function request() {
      if (!raf) raf = requestAnimationFrame(draw);
    }

    function resize() {
      if (scene) {
        const bounds = rope.getBoundingClientRect();
        ratio = Math.min(devicePixelRatio || 1, 2);
        scale = Math.max(bounds.width / 1440, bounds.height / 300);
        x = (bounds.width - 1440 * scale) / 2;
        y = (bounds.height - 300 * scale) / 2;
        shadow.width = Math.round(bounds.width * ratio);
        shadow.height = Math.round(bounds.height * ratio);
        scene.resize(bounds.width, bounds.height, scale, x, y, ratio);
        last = -1;
      }
      request();
    }

    function fallback(reason) {
      scene = null;
      rope.classList.remove('specialist__rope--ready');
      rope.dataset.renderer = 'image';
      if (reason) console.warn('Rope 3D uses its prerendered image:', reason.message || reason);
      request();
    }

    canvas.addEventListener('webglcontextlost', event => {
      event.preventDefault();
      fallback();
    });
    addEventListener('scroll', request, { passive: true });
    addEventListener('resize', resize);
    motion.addEventListener('change', request);
    if ('ResizeObserver' in window) new ResizeObserver(resize).observe(rope);
    if (document.fonts) document.fonts.ready.then(request);
    if (location.protocol === 'file:') {
      fallback();
      return;
    }
    const photo = new Image();
    photo.addEventListener('load', () => {
      try {
        scene = renderer(canvas, mesh, photoTexture(photo));
        resize();
        draw();
        rope.classList.add('specialist__rope--ready');
        rope.dataset.renderer = 'webgl';
      } catch (error) {
        fallback(error);
      }
    }, { once: true });
    photo.addEventListener('error', () => fallback(), { once: true });
    photo.src = canvas.dataset.ropePhoto;
    draw();
  }

  function start() {
    const sections=document.querySelectorAll('.specialist');
    if(!('IntersectionObserver' in window)){sections.forEach(init);return;}
    const observer=new IntersectionObserver(entries=>{
      for(const entry of entries)if(entry.isIntersecting){observer.unobserve(entry.target);init(entry.target);}
    },{rootMargin:'200px'});
    sections.forEach(section=>observer.observe(section));
  }
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', start, { once: true });
  } else {
    start();
  }
})();
