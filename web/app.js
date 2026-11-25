/* =========================================================
   Brisa · Asistente de Céfiro Airlines — lógica de la página
   Habla con el backend (server.py) por /api/chat, que devuelve
   una línea JSON por cada paso del grafo de LangGraph.
   ========================================================= */

// ---------- Iconos (SVG en línea, estilo trazo) ----------
const ICONOS = {
  plus: '<path d="M12 5v14M5 12h14"/>',
  arrowup: '<path d="M12 19V5M5 12l7-7 7 7"/>',
  menu: '<path d="M4 6h16M4 12h16M4 18h16"/>',
  sun: '<circle cx="12" cy="12" r="4"/><path d="M12 2v2M12 20v2M4.93 4.93l1.41 1.41M17.66 17.66l1.41 1.41M2 12h2M20 12h2M6.34 17.66l-1.41 1.41M19.07 4.93l-1.41 1.41"/>',
  moon: '<path d="M12 3a6 6 0 0 0 9 9 9 9 0 1 1-9-9Z"/>',
  calendar: '<rect x="3" y="4" width="18" height="18" rx="2"/><path d="M16 2v4M8 2v4M3 10h18"/>',
  wallet: '<path d="M19 7V4a1 1 0 0 0-1-1H5a2 2 0 0 0 0 4h15a1 1 0 0 1 1 1v4h-3a2 2 0 0 0 0 4h3a1 1 0 0 0 1-1v-2a1 1 0 0 0-1-1"/><path d="M3 5v14a2 2 0 0 0 2 2h15a1 1 0 0 0 1-1v-4"/>',
  house: '<path d="M3 10.5 12 3l9 7.5V20a1 1 0 0 1-1 1h-5v-6H9v6H4a1 1 0 0 1-1-1z"/>',
  plane: '<path d="M17.8 19.2 16 11l3.5-3.5C21 6 21.5 4 21 3c-1-.5-3 0-4.5 1.5L13 8 4.8 6.2c-.5-.1-.9.1-1.1.5l-.3.5c-.2.5-.1 1 .3 1.3L9 12l-2 3H4l-1 1 3 2 2 3 1-1v-3l3-2 3.5 5.3c.3.4.8.5 1.3.3l.5-.2c.4-.3.6-.7.5-1.2z"/>',
  filecheck: '<path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><path d="M14 2v6h6M9 15l2 2 4-4"/>',
  file: '<path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><path d="M14 2v6h6"/>',
  compass: '<circle cx="12" cy="12" r="10"/><path d="m16.24 7.76-2.12 6.36-6.36 2.12 2.12-6.36z"/>',
  book: '<path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20V2H6.5A2.5 2.5 0 0 0 4 4.5z"/><path d="M4 19.5A2.5 2.5 0 0 0 6.5 22H20v-5"/>',
  calculator: '<rect x="4" y="2" width="16" height="20" rx="2"/><path d="M8 6h8M8 10h.01M12 10h.01M16 10h.01M8 14h.01M12 14h.01M16 14h.01M8 18h.01M12 18h.01M16 18h.01"/>',
  sparkles: '<path d="M12 3l1.9 5.1L19 10l-5.1 1.9L12 17l-1.9-5.1L5 10l5.1-1.9z"/><path d="M19 15l.9 2.1L22 18l-2.1.9L19 21l-.9-2.1L16 18l2.1-.9z"/>',
  copy: '<rect x="9" y="9" width="13" height="13" rx="2"/><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/>',
  check: '<path d="M20 6 9 17l-5-5"/>',
  suitcase: '<rect x="6" y="7" width="12" height="14" rx="2"/><path d="M9 7V4a1 1 0 0 1 1-1h4a1 1 0 0 1 1 1v3M10 11v6M14 11v6"/>',
  clock: '<circle cx="12" cy="12" r="10"/><path d="M12 6v6l4 2"/>',
  repeat: '<path d="m17 2 4 4-4 4"/><path d="M3 11v-1a4 4 0 0 1 4-4h14"/><path d="m7 22-4-4 4-4"/><path d="M21 13v1a4 4 0 0 1-4 4H3"/>',
  award: '<circle cx="12" cy="8" r="6"/><path d="M15.477 12.89 17 22l-5-3-5 3 1.523-9.11"/>',
  idcard: '<rect x="3" y="4" width="18" height="16" rx="2"/><circle cx="9" cy="10" r="2"/><path d="M15 8h2M15 12h2M7 16h10"/>',
  chevron: '<path d="m6 9 6 6 6-6"/>',
};
const icono = (n) =>
  `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">${ICONOS[n] || ""}</svg>`;
const pintarIconos = (raiz = document) =>
  raiz.querySelectorAll("i[data-i]").forEach((el) => (el.innerHTML = icono(el.dataset.i)));

// ---------- Agentes del grafo ----------
const AGENTES = {
  supervisor: { nombre: "Supervisor", color: "var(--c-sup)" },
  documentalista: { nombre: "Documentalista", color: "var(--c-doc)" },
  calculadora: { nombre: "Calculadora", color: "var(--c-calc)" },
  FIN: { nombre: "Respuesta", color: "var(--c-resp)" },
};

// ---------- Elementos ----------
const $ = (s) => document.querySelector(s);
const mensajes = $("#mensajes");
const bienvenida = $("#bienvenida");
const entrada = $("#entrada");
const btnEnviar = $("#btnEnviar");
const formulario = $("#formulario");
const lateral = $("#lateral");
const velo = $("#velo");

let historial = []; // [{rol: "usuario"|"asistente", texto}]
let ocupado = false;

// ---------- Markdown mínimo (negritas, listas, tablas, títulos, citas) ----------
const escapar = (s) => s.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
const enLinea = (s) =>
  escapar(s)
    .replace(/`([^`]+)`/g, "<code>$1</code>")
    .replace(/\*\*([^*]+)\*\*/g, "<strong>$1</strong>")
    .replace(/(^|[^*])\*([^*\n]+)\*/g, "$1<em>$2</em>")
    .replace(/\(([\w\-]+\.md)\)/g, '<span class="cita">$1</span>')
    // Algunos modelos (gpt-oss) citan así: 【fichero.md · apartado】
    .replace(/【\s*([\w\-]+\.md)[^】]*】/g, ' <span class="cita">$1</span>');

function markdown(src) {
  const lineas = src.replace(/\r/g, "").split("\n");
  let html = "", lista = null, parrafo = [];
  const cerrarP = () => { if (parrafo.length) { html += `<p>${enLinea(parrafo.join(" "))}</p>`; parrafo = []; } };
  const cerrarL = () => { if (lista) { html += `</${lista}>`; lista = null; } };
  const celdas = (f) => f.trim().replace(/^\||\|$/g, "").split("|").map((c) => enLinea(c.trim()));

  for (let i = 0; i < lineas.length; i++) {
    const t = lineas[i].trim();
    let m;
    if (!t) { cerrarP(); cerrarL(); continue; }
    if (/^\|.*\|$/.test(t) && /^\|[\s:\-|]+\|$/.test((lineas[i + 1] || "").trim())) {
      cerrarP(); cerrarL();
      html += `<div class="tabla"><table><thead><tr>${celdas(t).map((c) => `<th>${c}</th>`).join("")}</tr></thead><tbody>`;
      i += 2;
      while (i < lineas.length && /^\|.*\|$/.test(lineas[i].trim())) {
        html += `<tr>${celdas(lineas[i]).map((c) => `<td>${c}</td>`).join("")}</tr>`;
        i++;
      }
      i--;
      html += "</tbody></table></div>";
      continue;
    }
    if ((m = t.match(/^#{1,4}\s+(.*)/))) { cerrarP(); cerrarL(); html += `<h4>${enLinea(m[1])}</h4>`; continue; }
    if ((m = t.match(/^[-*•]\s+(.*)/))) { cerrarP(); if (lista !== "ul") { cerrarL(); html += "<ul>"; lista = "ul"; } html += `<li>${enLinea(m[1])}</li>`; continue; }
    if ((m = t.match(/^\d+[.)]\s+(.*)/))) { cerrarP(); if (lista !== "ol") { cerrarL(); html += "<ol>"; lista = "ol"; } html += `<li>${enLinea(m[1])}</li>`; continue; }
    cerrarL();
    parrafo.push(t);
  }
  cerrarP(); cerrarL();
  return html;
}

const nombreFuente = (f) => {
  const s = f.replace(/\.md$/, "").replace(/_/g, " ");
  return s.charAt(0).toUpperCase() + s.slice(1);
};

// ---------- Pintar mensajes ----------
function bajar() { mensajes.scrollTop = mensajes.scrollHeight; }

function mensajeUsuario(texto) {
  const el = document.createElement("div");
  el.className = "msg usuario";
  el.innerHTML = `<div class="burbuja"></div>`;
  el.querySelector(".burbuja").textContent = texto;
  mensajes.appendChild(el);
  bajar();
}

function mensajeBot() {
  const el = document.createElement("div");
  el.className = "msg bot";
  el.innerHTML = `
    <div class="avatar">${icono("plane")}</div>
    <div class="cuerpo">
      <div class="traza cargando abierta">
        <button class="traza-cab"><span class="girando"></span><span class="txt">Pensando…</span><span class="chev">${icono("chevron")}</span></button>
        <div class="pasos"></div>
      </div>
      <div class="burbuja"><div class="respuesta"><span class="escribiendo"><span></span><span></span><span></span></span></div></div>
    </div>`;
  mensajes.appendChild(el);
  const traza = el.querySelector(".traza");
  el.querySelector(".traza-cab").addEventListener("click", () => {
    if (!traza.classList.contains("cargando")) traza.classList.toggle("abierta");
  });
  bajar();
  return {
    el,
    traza,
    pasos: el.querySelector(".pasos"),
    cabecera: el.querySelector(".traza-cab .txt"),
    respuesta: el.querySelector(".respuesta"),
    cuerpo: el.querySelector(".cuerpo"),
    n: 0,
  };
}

function anadirPaso(bot, agente, titulo, detalle) {
  const info = AGENTES[agente] || AGENTES.supervisor;
  const paso = document.createElement("div");
  paso.className = "paso";
  paso.style.setProperty("--color", info.color);
  paso.innerHTML = titulo;
  if (detalle) {
    const p = document.createElement("p");
    p.textContent = detalle;
    p.title = "Clic para ver completo";
    p.addEventListener("click", () => p.classList.toggle("completo"));
    paso.appendChild(p);
  }
  bot.pasos.appendChild(paso);
  bot.n++;
  bajar();
}

function marcarActivo(agente) {
  document.querySelectorAll(".agente").forEach((a) => a.classList.toggle("activo", a.dataset.agente === agente));
}

function escribirPocoAPoco(contenedor, texto) {
  if (matchMedia("(prefers-reduced-motion: reduce)").matches) {
    contenedor.innerHTML = markdown(texto); // sin animación si el usuario lo prefiere
    return Promise.resolve();
  }
  return new Promise((resolver) => {
    let i = 0;
    const paso = Math.max(3, Math.round(texto.length / 120));
    contenedor.classList.add("cursor");
    const t = setInterval(() => {
      i = Math.min(texto.length, i + paso);
      contenedor.innerHTML = markdown(texto.slice(0, i));
      bajar();
      if (i >= texto.length) {
        clearInterval(t);
        contenedor.classList.remove("cursor");
        resolver();
      }
    }, 16);
  });
}

function pie(bot, fuentes, texto) {
  const pie = document.createElement("div");
  pie.className = "pie";
  fuentes.forEach((f) => {
    const chip = document.createElement("span");
    chip.className = "fuente";
    chip.title = f;
    chip.innerHTML = `${icono("file")}${escapar(nombreFuente(f))}`;
    pie.appendChild(chip);
  });
  const copiar = document.createElement("button");
  copiar.className = "btn-copiar";
  copiar.innerHTML = `${icono("copy")}Copiar`;
  copiar.addEventListener("click", async () => {
    await navigator.clipboard.writeText(texto);
    copiar.innerHTML = `${icono("check")}Copiado`;
    setTimeout(() => (copiar.innerHTML = `${icono("copy")}Copiar`), 1600);
  });
  pie.appendChild(copiar);
  bot.cuerpo.appendChild(pie);
}

function cerrarTraza(bot) {
  bot.traza.classList.remove("cargando", "abierta");
  bot.cabecera.textContent = bot.n ? `Ver cómo lo he resuelto · ${bot.n} pasos` : "Respuesta directa";
  marcarActivo(null);
}

// ---------- Enviar una pregunta ----------
async function enviar(texto) {
  texto = texto.trim();
  if (!texto || ocupado) return;
  ocupado = true;
  actualizarBoton();
  bienvenida.remove?.();
  cerrarMenu();
  entrada.value = "";
  autoAltura();

  mensajeUsuario(texto);
  const bot = mensajeBot();
  marcarActivo("supervisor");

  let final = null;
  try {
    const res = await fetch("/api/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ mensaje: texto, historial }),
    });
    if (!res.ok) throw new Error(`El servidor respondió ${res.status}`);
    const lector = res.body.getReader();
    const deco = new TextDecoder();
    let buffer = "";
    while (true) {
      const { done, value } = await lector.read();
      if (done) break;
      buffer += deco.decode(value, { stream: true });
      let corte;
      while ((corte = buffer.indexOf("\n")) >= 0) {
        const linea = buffer.slice(0, corte).trim();
        buffer = buffer.slice(corte + 1);
        if (!linea) continue;
        const ev = JSON.parse(linea);

        if (ev.tipo === "decision") {
          if (ev.destino === "FIN") {
            anadirPaso(bot, "FIN", `<b style="color:var(--c-sup)">Supervisor</b><span class="flecha">→</span><b>Redactar respuesta</b>`);
            bot.cabecera.textContent = "Redactando la respuesta…";
            marcarActivo(null);
          } else {
            const destino = AGENTES[ev.destino]?.nombre || ev.destino;
            anadirPaso(bot, "supervisor", `<b>Supervisor</b><span class="flecha">→</span><b style="color:${AGENTES[ev.destino]?.color}">${destino}</b>`, ev.tarea);
            bot.cabecera.textContent = `${destino} trabajando…`;
            marcarActivo(ev.destino);
          }
        } else if (ev.tipo === "hallazgo") {
          const accion = ev.agente === "documentalista" ? "ha buscado en las normas" : "ha hecho las cuentas";
          anadirPaso(bot, ev.agente, `<b>${AGENTES[ev.agente]?.nombre || ev.agente}</b> ${accion}`, ev.texto);
          bot.cabecera.textContent = "El supervisor está decidiendo…";
          marcarActivo("supervisor");
        } else if (ev.tipo === "respuesta") {
          final = ev;
        } else if (ev.tipo === "error") {
          throw new Error(ev.texto);
        }
      }
    }
    if (!final) throw new Error("No ha llegado ninguna respuesta.");
    cerrarTraza(bot);
    await escribirPocoAPoco(bot.respuesta, final.texto);
    pie(bot, final.fuentes || [], final.texto);
    historial.push({ rol: "usuario", texto }, { rol: "asistente", texto: final.texto });
  } catch (err) {
    cerrarTraza(bot);
    bot.respuesta.innerHTML = `<p class="error">${escapar(err.message || String(err))}</p>`;
  } finally {
    ocupado = false;
    actualizarBoton();
    entrada.focus();
  }
}

// ---------- Caja de texto ----------
function autoAltura() {
  entrada.style.height = "auto";
  entrada.style.height = Math.min(entrada.scrollHeight, 180) + "px";
}
function actualizarBoton() { btnEnviar.disabled = ocupado || !entrada.value.trim(); }

entrada.addEventListener("input", () => { autoAltura(); actualizarBoton(); });
entrada.addEventListener("keydown", (e) => {
  if (e.key === "Enter" && !e.shiftKey && !e.isComposing) {
    e.preventDefault();
    enviar(entrada.value);
  }
});
formulario.addEventListener("submit", (e) => { e.preventDefault(); enviar(entrada.value); });
document.querySelectorAll("[data-pregunta]").forEach((b) => b.addEventListener("click", () => enviar(b.dataset.pregunta)));

// ---------- Nueva conversación ----------
$("#btnNueva").addEventListener("click", () => {
  if (ocupado) return;
  historial = [];
  mensajes.innerHTML = "";
  mensajes.appendChild(bienvenida);
  cerrarMenu();
  entrada.focus();
});

// ---------- Tema claro / oscuro ----------
function aplicarTema(tema) {
  document.documentElement.dataset.tema = tema;
  $("#btnTema").innerHTML = icono(tema === "oscuro" ? "sun" : "moon");
  localStorage.setItem("tema", tema);
}
$("#btnTema").addEventListener("click", () =>
  aplicarTema(document.documentElement.dataset.tema === "oscuro" ? "claro" : "oscuro"));

// ---------- Menú en móvil ----------
function cerrarMenu() { lateral.classList.remove("abierta"); velo.classList.remove("visible"); }
$("#btnMenu").addEventListener("click", () => { lateral.classList.add("abierta"); velo.classList.add("visible"); });
velo.addEventListener("click", cerrarMenu);

// ---------- Estado del backend ----------
async function comprobarEstado() {
  const punto = $("#estado"), texto = $("#estadoTexto"), alerta = $("#alerta");
  try {
    const r = await (await fetch("/api/estado")).json();
    punto.className = "estado " + (r.listo ? "ok" : "mal");
    texto.textContent = r.listo ? `En línea · ${r.modelo} + LangGraph` : "No disponible";
    alerta.hidden = r.listo;
    if (!r.listo) alerta.textContent = `⚠️ ${r.error}`;
  } catch {
    punto.className = "estado mal";
    texto.textContent = "Sin conexión con el servidor";
  }
}

// ---------- Arranque ----------
pintarIconos();
aplicarTema(localStorage.getItem("tema") || (matchMedia("(prefers-color-scheme: dark)").matches ? "oscuro" : "claro"));
comprobarEstado();
entrada.focus();
// Permite abrir la web con una pregunta ya lanzada: /?q=¿Cuántas vacaciones tengo?
const preguntaUrl = new URLSearchParams(location.search).get("q");
if (preguntaUrl) enviar(preguntaUrl);
