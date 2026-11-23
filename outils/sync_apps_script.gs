/**
 * Données partagées du site d'orga (week-end GBU Grand Est).
 * À coller dans le Google Sheet « Orga WE Grand Est · données partagées du site » :
 * Extensions → Apps Script → remplacer le code → Déployer → Nouveau déploiement → Application Web,
 * « Exécuter en tant que : moi », « Qui a accès : Tout le monde ».
 * Une ligne par valeur : clé (chemin dans l'état de la page) | valeur JSON | horodatage | auteur.
 */
const SHEET = 'etat';
function sheet_() {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  let s = ss.getSheetByName(SHEET);
  if (!s) { s = ss.insertSheet(SHEET); s.appendRow(['cle', 'valeur', 'maj', 'par']); s.setFrozenRows(1); }
  return s;
}
function json_(o) { return ContentService.createTextOutput(JSON.stringify(o)).setMimeType(ContentService.MimeType.JSON); }
function doGet(e) {
  const since = Number((e && e.parameter && e.parameter.since) || 0);
  const v = sheet_().getDataRange().getValues();
  const rows = []; let max = 0;
  for (let i = 1; i < v.length; i++) {
    const k = v[i][0], t = Number(v[i][2]) || 0;
    if (!k) continue;
    if (t > max) max = t;
    if (t > since) rows.push([String(k), String(v[i][1]), t]);
  }
  return json_({ max: max, rows: rows });
}
function doPost(e) {
  const lock = LockService.getScriptLock(); lock.waitLock(15000);
  try {
    const d = JSON.parse(e.postData.contents);
    const s = sheet_(); const v = s.getDataRange().getValues();
    const idx = {}; for (let i = 1; i < v.length; i++) if (v[i][0]) idx[v[i][0]] = i + 1;
    let t = Date.now();
    (d.set || []).forEach(function (p) {
      const k = String(p[0]).slice(0, 300), val = p[1] === null ? '' : String(p[1]).slice(0, 45000);
      const row = [k, val, ++t, String(d.by || '').slice(0, 40)];
      if (idx[k]) s.getRange(idx[k], 1, 1, 4).setValues([row]);
      else { s.appendRow(row); idx[k] = s.getLastRow(); }
    });
    return json_({ ok: true, max: t });
  } finally { lock.releaseLock(); }
}
