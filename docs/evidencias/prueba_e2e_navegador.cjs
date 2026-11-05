// Prueba de uso del frontend con los tres roles (Playwright + Chromium).
const { chromium } = require('playwright');
const path = require('path');
const fs = require('fs');

const BASE = 'http://localhost:4200';
const SHOTS = process.argv[2] || '/tmp/shots';
const FOTOS = '/home/claude/work/objetos_perdidos_ces/postman/fotos';
fs.mkdirSync(SHOTS, { recursive: true });

const results = [];
function check(name, ok, detail = '') {
  results.push({ name, ok, detail });
  console.log(`${ok ? 'OK  ' : 'FALLA'} ${name}${detail ? ' — ' + detail : ''}`);
}

async function login(page, email, password) {
  await page.goto(BASE + '/login');
  await page.fill('#email', email);
  await page.fill('#password', password);
  await page.click('button[type=submit]');
  await page.waitForURL((url) => !url.pathname.startsWith('/login'), { timeout: 10000 });
}

async function logout(page) {
  await page.click('text=Salir');
  await page.waitForURL('**/login**');
}

(async () => {
  const browser = await chromium.launch();
  const context = await browser.newContext({ viewport: { width: 1366, height: 900 }, acceptDownloads: true });
  const page = await context.newPage();
  const consoleErrors = [];
  page.on('console', (msg) => { if (msg.type() === 'error') consoleErrors.push(msg.text()); });

  // ---------------- login inválido y válido
  await page.goto(BASE + '/login');
  await page.screenshot({ path: path.join(SHOTS, '01_login.png') });
  await page.fill('#email', 'admin@ces.test');
  await page.fill('#password', 'Equivocada2026!');
  await page.click('button[type=submit]');
  await page.waitForSelector('.alert-error');
  check('Login con contraseña errónea muestra el mensaje del backend', (await page.textContent('.alert-error')).includes('Credenciales inválidas'));

  await login(page, 'admin@ces.test', 'Admin2026!');
  await page.waitForSelector('.kpi-value');
  check('ADMIN entra al dashboard', page.url().endsWith('/dashboard'));
  const kpis = await page.$$eval('.kpi-value', (els) => els.map((e) => Number(e.textContent)));
  check('Dashboard muestra 5 indicadores', kpis.length === 5, JSON.stringify(kpis));
  check('Total = disponibles + devueltos + inactivos', kpis[0] === kpis[1] + kpis[2] + kpis[3]);
  await page.waitForSelector('.bar-row');
  await page.screenshot({ path: path.join(SHOTS, '02_dashboard.png'), fullPage: true });

  // indicador -> listado correspondiente
  await page.click('.kpi.ok');
  await page.waitForURL('**/objetos?**');
  await page.waitForSelector('table tbody tr');
  const statuses = await page.$$eval('tbody tr td:last-child .badge:first-child', (els) => els.map((e) => e.textContent.trim()));
  check('Indicador «Disponibles» abre el listado filtrado', statuses.length > 0 && statuses.every((s) => s === 'DISPONIBLE'), `${statuses.length} filas`);
  await page.waitForTimeout(800);
  await page.screenshot({ path: path.join(SHOTS, '03_objetos.png') });

  // ---------------- recepción con fotos, tipo nuevo desde el modal
  await page.click('text=Recepción');
  await page.waitForSelector('#category');
  await page.selectOption('#category', { label: 'Tecnología' });
  await page.click('text=+ Crear tipo de objeto');
  await page.waitForSelector('#type-name');
  const typeName = 'Lector de huella E2E ' + Date.now().toString().slice(-5);
  await page.fill('#type-name', typeName);
  await page.click('text=Guardar y seleccionar');
  await page.waitForSelector('#type-name', { state: 'detached' });
  await page.waitForTimeout(500);
  const selectedType = await page.$eval('#type', (el) => el.options[el.selectedIndex].textContent.trim());
  check('El tipo creado en el modal queda seleccionado', selectedType === typeName, selectedType);

  await page.fill('#description', 'Lector biométrico gris con cable USB (prueba e2e)');
  await page.selectOption('#found-campus', { label: 'Poblado' });
  await page.waitForTimeout(400);
  await page.selectOption('#found-block', { label: 'Bloque B' });
  await page.fill('#found-location', 'Laboratorio de cómputo');
  await page.selectOption('#custody-campus', { label: 'Poblado' });
  await page.waitForTimeout(400);
  await page.selectOption('#custody-block', { label: 'Bloque A' });
  await page.fill('#custody-location', 'Oficina 101, estante 3');
  await page.fill('input[name=person-search]', 'DEMO-1001');
  await page.click('.picker >> text=Buscar');
  await page.waitForSelector('.results button');
  await page.click('.results button');
  await page.setInputFiles('input[type=file]', [path.join(FOTOS, 'foto_prueba_1.jpg'), path.join(FOTOS, 'foto_prueba_2.png'), path.join(FOTOS, 'foto_prueba_3.jpg')]);
  await page.waitForSelector('.photo-card img');
  check('Vista previa de 3 fotos', (await page.$$('.photo-card')).length === 3);
  await page.click('.photo-card >> nth=2 >> text=Quitar');
  await page.waitForFunction(() => document.querySelectorAll('.photo-card').length === 2, null, { timeout: 5000 }).catch(() => {});
  check('Retirar una foto antes de guardar', (await page.$$('.photo-card')).length === 2);
  await page.screenshot({ path: path.join(SHOTS, '04_recepcion.png'), fullPage: true });
  await page.click('text=Guardar recepción');
  await page.waitForURL(/\/objetos\/\d+\?created=1/, { timeout: 15000 });
  await page.waitForSelector('.alert-success');
  const title = await page.textContent('h1');
  check('Recepción guardada: detalle con código OBJ-', /OBJ-\d{6}/.test(title), title.trim());
  await page.waitForSelector('.photo-card img');
  check('Detalle muestra 2 fotos autorizadas', (await page.$$('.photo-card img')).length === 2);
  const detailText = await page.textContent('body');
  check('Detalle muestra quién entrega y quién recibe', detailText.includes('Laura Restrepo Demo') && detailText.includes('Administrador de Pruebas'));
  const objectUrl = page.url().split('?')[0];

  // ---------------- edición con motivo
  await page.click('a:has-text("Editar")');
  await page.waitForSelector('#description');
  await page.waitForTimeout(800);
  await page.fill('#description', 'Lector biométrico gris con cable USB y funda negra');
  await page.click('text=Guardar cambios');
  await page.waitForSelector('.alert-error');
  check('Edición sin motivo es rechazada en el formulario', (await page.textContent('.alert-error')).includes('motivo'));
  await page.fill('textarea[name=reason]', 'Se precisa la descripción');
  await page.click('text=Guardar cambios');
  await page.waitForURL(/updated=1/);
  await page.waitForSelector('.timeline li');
  const historyText = await page.textContent('.timeline');
  check('Historial muestra la edición con antes/después', historyText.includes('Edición') && historyText.includes('funda negra'));

  // ---------------- inactivar foto (confirmación con motivo)
  await page.click('.photo-card >> nth=0 >> text=Inactivar');
  await page.fill('#reason', 'Foto borrosa');
  await page.click('.modal >> button:has-text("Inactivar foto")');
  await page.waitForSelector('.photo-card.inactive');
  check('Foto inactivada con motivo (se conserva visible como inactiva)', (await page.$$('.photo-card.inactive')).length === 1);

  // ---------------- reclamación, aceptación y devolución
  await page.click('text=+ Registrar reclamación');
  await page.fill('.claim-form input[name=person-search]', 'DEMO-1004');
  await page.click('.claim-form >> text=Buscar');
  await page.waitForSelector('.claim-form .results button');
  await page.click('.claim-form .results button');
  await page.fill('#evidence', 'Conoce el número de serie escrito debajo');
  await page.check('input[name=verified]');
  await page.click('text=Guardar reclamación');
  await page.waitForSelector('text=Reclamación registrada');
  await page.click('button:has-text("Aceptar")');
  await page.fill('#reason', 'Evidencia y documento verificados');
  await page.click('.modal >> button:has-text("Aceptar")');
  await page.waitForSelector('text=Registrar devolución');
  await page.fill('#summary', 'Cédula verificada y número de serie correcto');
  await page.check('input[name=confirmation]');
  await page.screenshot({ path: path.join(SHOTS, '05_devolucion.png'), fullPage: true });
  await page.click('button:has-text("Registrar devolución")');
  await page.waitForSelector('text=Devolución al propietario');
  const afterReturn = await page.textContent('body');
  check('Objeto queda DEVUELTO con constancia y responsables', afterReturn.includes('DEVUELTO') && afterReturn.includes('CONST-'));
  const [receipt] = await Promise.all([page.waitForEvent('download'), page.click('text=Descargar PDF')]);
  const receiptPath = path.join(SHOTS, 'constancia.pdf');
  await receipt.saveAs(receiptPath);
  check('Constancia PDF descargada', fs.readFileSync(receiptPath).slice(0, 4).toString() === '%PDF');
  await page.screenshot({ path: path.join(SHOTS, '06_detalle_devuelto.png'), fullPage: true });

  // ---------------- inventario y exportación
  await page.click('nav >> text=Inventario');
  await page.waitForSelector('.big');
  await page.selectOption('#i-campus', { label: 'Sabaneta' });
  await page.click('button:has-text("Filtrar")');
  await page.waitForTimeout(800);
  const [inventoryPdf] = await Promise.all([page.waitForEvent('download'), page.click('text=Exportar PDF')]);
  const inventoryPath = path.join(SHOTS, 'inventario.pdf');
  await inventoryPdf.saveAs(inventoryPath);
  check('Inventario exporta PDF con filtros', fs.readFileSync(inventoryPath).slice(0, 4).toString() === '%PDF');
  await page.screenshot({ path: path.join(SHOTS, '07_inventario.png'), fullPage: true });

  // ---------------- catálogos (crear sede) y usuarios
  await page.click('nav >> text=Catálogos');
  await page.waitForSelector('#new-name');
  const campusName = 'Sede E2E ' + Date.now().toString().slice(-5);
  await page.fill('#new-name', campusName);
  await page.click('button:has-text("Agregar")');
  await page.waitForSelector('.alert-success');
  check('ADMIN crea una sede desde catálogos', (await page.textContent('table')).includes(campusName));
  await page.fill('#new-name', 'poblado');
  await page.click('button:has-text("Agregar")');
  await page.waitForSelector('.alert-error');
  check('Duplicado normalizado muestra 409 del backend', (await page.textContent('.alert-error')).includes('Ya existe'));
  await page.screenshot({ path: path.join(SHOTS, '08_catalogos.png') });

  await page.click('nav >> text=Usuarios');
  await page.waitForSelector('table tbody tr');
  check('ADMIN ve la administración de usuarios', (await page.textContent('table')).includes('operador.demo@ces.test'));
  await page.click('nav >> text=Auditoría');
  await page.waitForSelector('table tbody tr');
  check('ADMIN ve la auditoría', (await page.$$('table tbody tr')).length > 0);
  await logout(page);

  // ---------------- OPERADOR
  await login(page, 'operador.demo@ces.test', 'Demo2026!');
  await page.waitForSelector('table tbody tr');
  check('OPERADOR entra a Objetos (sin dashboard)', page.url().includes('/objetos'));
  const operatorMenu = await page.$$eval('nav a', (els) => els.map((e) => e.textContent.trim()));
  check('Menú de OPERADOR sin Dashboard, Usuarios ni Auditoría', !operatorMenu.includes('Dashboard') && !operatorMenu.includes('Usuarios') && !operatorMenu.includes('Auditoría'), operatorMenu.join(', '));
  await page.goto(BASE + '/dashboard');
  await page.waitForTimeout(800);
  check('OPERADOR no puede abrir /dashboard (redirige)', !page.url().includes('/dashboard'));
  await page.goto(objectUrl);
  await page.waitForSelector('h1');
  await page.waitForTimeout(800);
  check('OPERADOR no ve «Corrección administrativa» en un DEVUELTO', !(await page.textContent('body')).includes('Corrección administrativa'));
  await logout(page);

  // ---------------- CONSULTA
  await login(page, 'consulta.demo@ces.test', 'Demo2026!');
  await page.waitForSelector('table tbody tr');
  const headers = await page.$$eval('thead th', (els) => els.map((e) => e.textContent.trim()));
  check('CONSULTA no ve columna de fotos ni bloque', !headers.includes('Foto') && !headers.includes('Bloque'), headers.join(', '));
  const consultaMenu = await page.$$eval('nav a', (els) => els.map((e) => e.textContent.trim()));
  check('Menú de CONSULTA solo Objetos y Mi cuenta', consultaMenu.join(',') === 'Objetos,Mi cuenta', consultaMenu.join(', '));
  await page.click('table tbody tr >> nth=0');
  await page.waitForSelector('.details');
  const consultaDetail = await page.textContent('.card');
  check('Detalle de CONSULTA sin descripción ni personas', !consultaDetail.includes('Descripción') && !consultaDetail.includes('Entrega'));
  await page.screenshot({ path: path.join(SHOTS, '09_consulta.png') });
  await page.goto(BASE + '/usuarios');
  await page.waitForTimeout(800);
  check('CONSULTA no puede abrir /usuarios', !page.url().includes('/usuarios'));
  await logout(page);

  // ---------------- móvil
  const mobile = await browser.newContext({ viewport: { width: 390, height: 844 }, isMobile: true });
  const mpage = await mobile.newPage();
  await login(mpage, 'admin@ces.test', 'Admin2026!');
  await mpage.waitForSelector('.kpi-value');
  const overflow = await mpage.evaluate(() => document.documentElement.scrollWidth > window.innerWidth + 1);
  check('Dashboard usable en móvil (sin scroll horizontal)', !overflow);
  await mpage.screenshot({ path: path.join(SHOTS, '10_movil.png'), fullPage: true });

  // ---------------- registro y recuperación
  const p2 = await (await browser.newContext()).newPage();
  await p2.goto(BASE + '/register');
  await p2.fill('#identification', 'E2E-' + Date.now());
  await p2.fill('#full-name', 'Usuario E2E');
  await p2.fill('#email', `e2e.${Date.now()}@ces.test`);
  await p2.fill('#password', 'corta');
  await p2.fill('#password-confirmation', 'corta');
  await p2.click('button[type=submit]');
  await p2.waitForSelector('.alert-error');
  check('Registro valida la contraseña en el formulario', (await p2.textContent('.alert-error')).includes('8 caracteres'));
  await p2.fill('#password', 'Usuario2026!');
  await p2.fill('#password-confirmation', 'Usuario2026!');
  await p2.click('button[type=submit]');
  await p2.waitForURL('**/login?registered=1');
  check('Registro exitoso vuelve al login con mensaje', (await p2.textContent('.alert-info')).includes('Cuenta creada'));
  await p2.goto(BASE + '/forgot-password');
  await p2.fill('#email', 'no-existe@ces.test');
  await p2.click('button[type=submit]');
  await p2.waitForSelector('.alert-success');
  check('Olvidé contraseña muestra el mensaje genérico', (await p2.textContent('.alert-success')).includes('Si el correo está registrado'));

  check('Sin errores de consola en el navegador', consoleErrors.filter((e) => !e.includes('401') && !e.includes('409') && !e.includes('400')).length === 0, consoleErrors.slice(0, 3).join(' | '));

  await browser.close();
  const failed = results.filter((r) => !r.ok);
  console.log(`\n${results.length - failed.length}/${results.length} comprobaciones correctas`);
  fs.writeFileSync(path.join(SHOTS, 'resultado_e2e.json'), JSON.stringify({ fecha: new Date().toISOString(), results }, null, 2));
  process.exit(failed.length ? 1 : 0);
})().catch((error) => {
  console.error(error);
  process.exit(2);
});
