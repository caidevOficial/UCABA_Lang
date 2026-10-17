/**
 * GNU General Public License v3.0 or later (GPL-3.0-or-later)
 *
 * Copyright (c) 2026 [Facu Falcone](a.facundo.falcone@gmail.com) All rights reserved.
 *
 * This program is free software: you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation, either version 3 of the License, or
 * (at your option) any later version.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this program.  If not, see <https://www.gnu.org/licenses/>.
 */

const vscode = require('vscode');
const cp = require('child_process');
const path = require('path');
const fs = require('fs');

/**
 * Encuentra el ejecutable de Python apropiado.
 */
function getPythonPath() {
    const config = vscode.workspace.getConfiguration('ucaba');
    const configuredPath = config.get('pythonPath');
    if (configuredPath && configuredPath.trim().length > 0) {
        return configuredPath.trim();
    }
    return process.platform === 'win32' ? 'python' : 'python3';
}

/**
 * Obtiene el comando o ejecutable de UCABA a utilizar.
 * Prioridad:
 * 1. Configuración explícita `ucaba.cliPath`
 * 2. `ucaba.exe` instalado en %LOCALAPPDATA%\Programs\UCABA\bin\ucaba.exe
 * 3. `ucaba` disponible en PATH
 * 4. Fallback a Python (`ucaba.pythonPath` o `python`/`python3`)
 */
function getUcabaRunner() {
    const config = vscode.workspace.getConfiguration('ucaba');
    const configuredCli = config.get('cliPath');
    if (configuredCli && configuredCli.trim().length > 0 && fs.existsSync(configuredCli.trim())) {
        return { isCli: true, executable: configuredCli.trim() };
    }

    // 1. Binario local de release o debug en el workspace actual
    if (vscode.workspace.workspaceFolders && vscode.workspace.workspaceFolders.length > 0) {
        const root = vscode.workspace.workspaceFolders[0].uri.fsPath;
        const candidateBins = process.platform === 'win32'
            ? [
                path.join(root, 'target', 'release', 'ucaba.exe'),
                path.join(root, 'target', 'debug', 'ucaba.exe')
            ]
            : [
                path.join(root, 'target', 'release', 'ucaba'),
                path.join(root, 'target', 'debug', 'ucaba')
            ];
        for (const candidate of candidateBins) {
            if (fs.existsSync(candidate)) {
                return { isCli: true, executable: candidate };
            }
        }
    }

    // 2. Instalación estándar en Windows
    if (process.platform === 'win32') {
        const localAppData = process.env.LOCALAPPDATA || path.join(process.env.USERPROFILE || '', 'AppData', 'Local');
        const defaultCli = path.join(localAppData, 'Programs', 'UCABA', 'bin', 'ucaba.exe');
        if (fs.existsSync(defaultCli)) {
            return { isCli: true, executable: defaultCli };
        }
    } else {
        // 2b. Rutas estándar en Linux y macOS
        const unixCandidates = ['/usr/local/bin/ucaba', '/usr/bin/ucaba', path.join(process.env.HOME || '', '.local', 'bin', 'ucaba')];
        for (const unixBin of unixCandidates) {
            if (fs.existsSync(unixBin)) {
                return { isCli: true, executable: unixBin };
            }
        }
    }

    // 3. Binario en PATH
    try {
        const testRes = cp.spawnSync(process.platform === 'win32' ? 'ucaba.exe' : 'ucaba', ['--help'], { shell: true, timeout: 1000 });
        const output = (testRes.stdout ? testRes.stdout.toString() : '') + (testRes.stderr ? testRes.stderr.toString() : '');
        if (testRes.status === 0 && !output.includes('UCABA Stub Test Binary')) {
            return { isCli: true, executable: process.platform === 'win32' ? 'ucaba.exe' : 'ucaba' };
        }
    } catch (e) {}

    // 4. Fallback a Python si no se encuentra el binario nativo de Rust
    return { isCli: false, executable: getPythonPath() };
}

/**
 * Obtiene el directorio de trabajo del espacio de trabajo actual o del archivo.
 */
function getWorkingDirectory(document) {
    if (vscode.workspace.workspaceFolders && vscode.workspace.workspaceFolders.length > 0) {
        return vscode.workspace.workspaceFolders[0].uri.fsPath;
    }
    if (document && document.uri && document.uri.fsPath) {
        return path.dirname(document.uri.fsPath);
    }
    return process.cwd();
}

/**
 * Determina si una terminal activa o el entorno actual de VS Code está ejecutando PowerShell.
 * @param {vscode.Terminal} [terminal]
 * @returns {boolean}
 */
function isPowerShellTerminal(terminal) {
    if (process.platform !== 'win32') {
        return false;
    }

    if (terminal && terminal.name) {
        const name = terminal.name.toLowerCase();
        if (name.includes('pwsh') || name.includes('powershell')) {
            return true;
        }
        if (name.includes('cmd') || name.includes('command') || name.includes('bash') || name.includes('zsh') || name.includes('git')) {
            return false;
        }
    }

    if (terminal && terminal.creationOptions) {
        const shell = (terminal.creationOptions.shellPath || '').toLowerCase();
        if (shell.includes('pwsh') || shell.includes('powershell')) {
            return true;
        }
        if (shell.includes('cmd.exe') || shell.includes('bash') || shell.includes('zsh')) {
            return false;
        }
    }

    const envShell = (vscode.env.shell || '').toLowerCase();
    if (envShell.includes('pwsh') || envShell.includes('powershell')) {
        return true;
    }
    if (envShell.includes('cmd.exe') || envShell.includes('bash') || envShell.includes('zsh')) {
        return false;
    }

    // En Windows el terminal integrado predeterminado de VS Code es PowerShell
    return true;
}

/**
 * Genera la cadena de comando lista para enviarse a la terminal de VS Code,
 * asegurando compatibilidad con PowerShell (operador de invocación &) y CMD/Bash.
 *
 * @param {vscode.Terminal} terminal
 * @param {string} executable Ruta o nombre del ejecutable
 * @param {string[]} args Argumentos del comando
 * @returns {string}
 */
function buildTerminalCommand(terminal, executable, args) {
    const isPs = isPowerShellTerminal(terminal);
    const isWin = process.platform === 'win32';

    // En PowerShell o Windows, si el ejecutable contiene espacios o es ruta absoluta, se entrecomilla
    const needsQuotes = executable.includes(' ') || isWin;
    const exeFormatted = needsQuotes ? `"${executable}"` : executable;
    const prefix = isPs ? '& ' : '';

    const formattedArgs = args.map(arg => {
        if (arg.includes(' ') || arg.includes('\t') || arg.includes('\\') || arg.includes('/')) {
            return `"${arg}"`;
        }
        return arg;
    }).join(' ');

    return `${prefix}${exeFormatted} ${formattedArgs}`;
}

/**
 * @param {vscode.ExtensionContext} context
 */
function activate(context) {
    console.log('UCABA Pseudocode Language Extension activada.');

    const diagnosticCollection = vscode.languages.createDiagnosticCollection('ucaba');
    context.subscriptions.push(diagnosticCollection);

    let checkTimeout = null;

    /**
     * Ejecuta lsp_check sobre el documento y publica diagnósticos.
     */
    function updateDiagnostics(document) {
        if (!document || (document.languageId !== 'ucaba' && !document.fileName.endsWith('.ucaba'))) {
            return;
        }

        const runner = getUcabaRunner();
        const workingDir = getWorkingDirectory(document);
        const sourceText = document.getText();

        const env = Object.assign({}, process.env);
        // Asegurar que el directorio de trabajo esté en PYTHONPATH para importar pseudocode en modo fallback
        if (env.PYTHONPATH) {
            env.PYTHONPATH = workingDir + path.delimiter + env.PYTHONPATH;
        } else {
            env.PYTHONPATH = workingDir;
        }

        const args = runner.isCli ? ['lsp-check', '--lenient', '--stdin'] : ['-m', 'pseudocode.lsp_check', '--lenient'];
        const proc = cp.spawn(runner.executable, args, {
            cwd: workingDir,
            env: env,
            shell: process.platform === 'win32'
        });

        let stdoutData = '';
        let stderrData = '';

        proc.stdout.on('data', (data) => {
            stdoutData += data.toString('utf-8');
        });

        proc.stderr.on('data', (data) => {
            stderrData += data.toString('utf-8');
        });

        proc.on('close', (code) => {
            if (!stdoutData.trim()) {
                if (stderrData.trim()) {
                    console.error('UCABA linter stderr:', stderrData);
                }
                return;
            }

            try {
                const parsed = JSON.parse(stdoutData);
                const items = parsed.diagnostics || [];
                const diagnostics = [];

                for (const item of items) {
                    const line = Math.max(0, Math.min(item.line, Math.max(0, document.lineCount - 1)));
                    const lineText = line < document.lineCount ? document.lineAt(line).text : '';
                    let char = Math.max(0, item.character || 0);
                    if (char >= lineText.length && lineText.length > 0) {
                        char = Math.max(0, lineText.length - 1);
                    }

                    const length = Math.max(1, item.length || (lineText.length > char ? lineText.length - char : 1));
                    const endChar = Math.min(char + length, Math.max(char + 1, lineText.length));

                    const range = new vscode.Range(line, char, line, endChar);

                    let severity = vscode.DiagnosticSeverity.Error;
                    if (item.severity === 'warning') {
                        severity = vscode.DiagnosticSeverity.Warning;
                    } else if (item.severity === 'info') {
                        severity = vscode.DiagnosticSeverity.Information;
                    } else if (item.severity === 'hint') {
                        severity = vscode.DiagnosticSeverity.Hint;
                    }

                    const diag = new vscode.Diagnostic(range, item.message, severity);
                    diag.source = 'UCABA (' + (item.source || 'linter') + ')';
                    diagnostics.push(diag);
                }

                diagnosticCollection.set(document.uri, diagnostics);
            } catch (err) {
                console.error('Error parseando JSON de UCABA diagnostics:', err, stdoutData);
            }
        });

        proc.on('error', (err) => {
            console.warn('No se pudo invocar el verificador de UCABA:', err.message);
        });

        // Enviar contenido actual del editor vía stdin
        try {
            proc.stdin.write(sourceText, 'utf-8');
            proc.stdin.end();
        } catch (e) {
            // Ignorar errores de pipe roto si el proceso terminó rápido
        }
    }

    // Suscripciones de eventos para diagnósticos en tiempo real
    context.subscriptions.push(
        vscode.workspace.onDidChangeTextDocument((event) => {
            if (event.document.languageId === 'ucaba' || event.document.fileName.endsWith('.ucaba')) {
                if (checkTimeout) {
                    clearTimeout(checkTimeout);
                }
                checkTimeout = setTimeout(() => {
                    updateDiagnostics(event.document);
                }, 250);
            }
        })
    );

    context.subscriptions.push(
        vscode.workspace.onDidOpenTextDocument((doc) => {
            updateDiagnostics(doc);
        })
    );

    context.subscriptions.push(
        vscode.workspace.onDidSaveTextDocument((doc) => {
            updateDiagnostics(doc);
        })
    );

    context.subscriptions.push(
        vscode.workspace.onDidCloseTextDocument((doc) => {
            diagnosticCollection.delete(doc.uri);
        })
    );

    // Revisar documentos visibles al iniciar
    vscode.window.visibleTextEditors.forEach((editor) => {
        if (editor && editor.document) {
            updateDiagnostics(editor.document);
        }
    });

    // -------------------------------------------------------------
    // Utilidades de Análisis de Símbolos, Estructuras y Alcance
    // -------------------------------------------------------------
    const TYPE_KEYWORDS = 'ENTERO|FLOTANTE|REAL|CADENA|CARACTER|BOOLEANO|ARCHIVO|NULO';
    const FN_HEADER_RE = /^\s*(FUNCION|PROCEDIMIENTO)\s+([A-Za-z_][A-Za-z0-9_]*)\s*\(([^)]*)\)\s*(?::\s*([A-Za-z]+(?:\s*\[\s*\])*))?/i;
    const FN_END_RE = /^\s*FIN\s+(?:FUNCION|PROCEDIMIENTO)\b/i;
    const STRUCT_HEADER_RE = /^\s*Estructura\s+([A-Za-z_][A-Za-z0-9_]*)\s*:?/i;
    const STRUCT_END_RE = /^\s*FIN\s*(?:_|\s+)?(?:ESTRUCTURA|STRUCT)\b/i;

    function escapeRegex(string) {
        return string.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
    }

    /** Devuelve los comentarios `//` contiguos que preceden a una línea (documentación). */
    function getLeadingComment(doc, lineNo) {
        const lines = [];
        for (let i = lineNo - 1; i >= 0; i--) {
            const m = doc.lineAt(i).text.match(/^\s*\/\/\s?(.*)$/);
            if (!m) break;
            lines.unshift(m[1]);
        }
        return lines.join('\n');
    }

    /**
     * Parsea una línea de declaración de campo dentro de una ESTRUCTURA.
     * Soporta:
     *   CADENA nombre
     *   ENTERO edad = 0
     *   Nodo proximo_nodo
     *   REAL notas[10] // comentario
     */
    function parseStructFieldLine(lineText) {
        if (!lineText || /^\s*\/\//.test(lineText)) return null;
        const m = lineText.match(/^\s*([A-Za-z_][A-Za-z0-9_]*((?:\s*\[[^\]]*\])*))\s+([A-Za-z_][A-Za-z0-9_]*)((?:\s*\[[^\]]*\])*)\s*(?:=\s*[^/]+)?(?:\s*\/\/\s*(.*))?$/);
        if (!m) return null;
        const baseType = m[1].replace(/\[[^\]]*\]/g, '').trim();
        const dims = (m[1].match(/\[/g) || []).length + (m[4].match(/\[/g) || []).length;
        return {
            type: baseType + '[]'.repeat(dims),
            baseType: baseType,
            name: m[3],
            dims: dims,
            doc: m[5] ? m[5].trim() : '',
            raw: lineText.trim()
        };
    }

    /** Busca la definición de una Estructura por nombre en un documento. */
    function findStructInDocument(doc, name) {
        if (!doc || !name) return null;
        const nameLower = name.toLowerCase();
        for (let i = 0; i < doc.lineCount; i++) {
            const m = doc.lineAt(i).text.match(STRUCT_HEADER_RE);
            if (m && m[1].toLowerCase() === nameLower) {
                const fields = [];
                const parsedFields = [];
                for (let j = i + 1; j < doc.lineCount; j++) {
                    const lineText = doc.lineAt(j).text.trim();
                    if (STRUCT_END_RE.test(lineText)) break;
                    if (lineText && !lineText.startsWith('//')) {
                        fields.push(lineText);
                        const pf = parseStructFieldLine(lineText);
                        if (pf) parsedFields.push(pf);
                    }
                }
                return {
                    doc,
                    line: i,
                    name: m[1],
                    fields,
                    parsedFields,
                    comment: getLeadingComment(doc, i)
                };
            }
        }
        return null;
    }

    /** Busca una estructura en el documento actual o en los documentos abiertos del workspace. */
    function findStructAnywhere(doc, name) {
        if (!name) return null;
        let s = findStructInDocument(doc, name);
        if (s) return s;
        if (vscode.workspace && vscode.workspace.textDocuments) {
            for (const otherDoc of vscode.workspace.textDocuments) {
                if (otherDoc !== doc && (otherDoc.languageId === 'ucaba' || (otherDoc.fileName && otherDoc.fileName.endsWith('.ucaba')))) {
                    s = findStructInDocument(otherDoc, name);
                    if (s) return s;
                }
            }
        }
        return null;
    }

    /** Recolecta todas las estructuras definidas en el documento. */
    function getAllStructs(doc) {
        const structs = new Map();
        if (!doc) return structs;
        for (let i = 0; i < doc.lineCount; i++) {
            const m = doc.lineAt(i).text.match(STRUCT_HEADER_RE);
            if (m) {
                const s = findStructInDocument(doc, m[1]);
                if (s) structs.set(s.name.toLowerCase(), s);
            }
        }
        return structs;
    }

    /**
     * Indica si la posición está dentro de un comentario o de una cadena de texto,
     * recorriendo el documento desde el inicio (soporta """...""", slash-asterisco, // y "..." / '...').
     */
    function isInCommentOrString(document, position) {
        const text = document.getText();
        const target = document.offsetAt(position);
        let i = 0;
        while (i < target) {
            const two = text.substr(i, 2);
            const three = text.substr(i, 3);
            if (three === '"""') {
                const end = text.indexOf('"""', i + 3);
                if (end === -1 || end + 3 > target) return true;
                i = end + 3;
            } else if (two === '/*') {
                const end = text.indexOf('*/', i + 2);
                if (end === -1 || end + 2 > target) return true;
                i = end + 2;
            } else if (two === '//') {
                let end = text.indexOf('\n', i);
                if (end === -1) end = text.length;
                if (end > target) return true;
                i = end;
            } else if (text[i] === '#') {
                let end = text.indexOf('\n', i);
                if (end === -1) end = text.length;
                if (end > target) return true;
                i = end;
            } else if (text[i] === '"' || text[i] === "'") {
                const quote = text[i];
                let j = i + 1;
                while (j < text.length && text[j] !== quote && text[j] !== '\n') {
                    if (text[j] === '\\') j++;
                    j++;
                }
                if (j >= target) return true;
                i = j + 1;
            } else {
                i++;
            }
        }
        return false;
    }

    /** Busca la definición de una FUNCION/PROCEDIMIENTO por nombre en un documento. */
    function findFunctionInDocument(doc, name) {
        if (!doc || !name) return null;
        const nameLower = name.toLowerCase();
        for (let i = 0; i < doc.lineCount; i++) {
            const m = doc.lineAt(i).text.match(FN_HEADER_RE);
            if (m && m[2].toLowerCase() === nameLower) {
                return {
                    doc,
                    line: i,
                    kind: m[1].toUpperCase(),
                    name: m[2],
                    params: m[3].trim(),
                    returnType: (m[4] || '').replace(/\s+/g, ''),
                    comment: getLeadingComment(doc, i)
                };
            }
        }
        return null;
    }

    /**
     * Busca la declaración de una variable o parámetro respetando el alcance:
     * hacia arriba desde la línea actual, saltando cuerpos de otras funciones.
     */
    function findVariableDeclaration(doc, name, fromLine) {
        if (!doc || !name) return null;
        const esc = escapeRegex(name);

        const structNames = [];
        for (let k = 0; k < doc.lineCount; k++) {
            const sm = doc.lineAt(k).text.match(STRUCT_HEADER_RE);
            if (sm) structNames.push(escapeRegex(sm[1]));
        }
        const allTypes = structNames.length > 0 ? `${TYPE_KEYWORDS}|${structNames.join('|')}` : `${TYPE_KEYWORDS}|[A-Za-z_][A-Za-z0-9_]*`;

        const varRe = new RegExp(`\\b(${allTypes})\\s+${esc}\\b((?:\\s*\\[[^\\]]*\\])*)`, 'i');
        const paramRe = new RegExp(`^${esc}((?:\\s*\\[[^\\]]*\\])*)\\s*:\\s*([A-Za-z_][A-Za-z0-9_]*)$`, 'i');
        const paramReAlt = new RegExp(`^([A-Za-z_][A-Za-z0-9_]*)\\s+${esc}((?:\\s*\\[[^\\]]*\\])*)$`, 'i');
        let depth = 0;

        for (let i = fromLine; i >= 0; i--) {
            const text = doc.lineAt(i).text;
            if (/^\s*\/\//.test(text)) continue;

            if (i !== fromLine && FN_END_RE.test(text)) {
                depth++;
                continue;
            }

            const header = text.match(FN_HEADER_RE);
            if (header) {
                if (depth > 0) {
                    depth--;
                    continue;
                }
                const params = header[3].split(',');
                for (const p of params) {
                    const pTrim = p.trim();
                    const pm = pTrim.match(paramRe);
                    if (pm) {
                        const dims = (pm[1].match(/\[/g) || []).length;
                        return { kind: 'parámetro', type: pm[2] + '[]'.repeat(dims), name, line: i };
                    }
                    const pm2 = pTrim.match(paramReAlt);
                    if (pm2) {
                        const dims = (pm2[1].match(/\[/g) || []).length;
                        return { kind: 'parámetro', type: pm2[1] + '[]'.repeat(dims), name, line: i };
                    }
                }
                continue;
            }

            if (depth > 0) continue;

            const vm = text.match(varRe);
            if (vm) {
                const dims = (vm[2].match(/\[/g) || []).length;
                return { kind: 'variable', type: vm[1] + '[]'.repeat(dims), name, line: i };
            }
        }
        return null;
    }

    /**
     * Resuelve el tipo de dato de una expresión (soporta accesos encadenados e indexación,
     * ej: "pepe", "file", "actual.proximo_nodo", "estante[0]").
     */
    function resolveExpressionType(doc, exprString, fromLine) {
        if (!exprString || typeof exprString !== 'string') return null;
        const segments = exprString.split('.');
        if (segments.length === 0) return null;

        const firstSegment = segments[0].trim();
        const firstBase = firstSegment.replace(/\[[^\]]*\]/g, '').trim();
        const firstDims = (firstSegment.match(/\[/g) || []).length;

        let decl = findVariableDeclaration(doc, firstBase, fromLine);
        let currType = null;

        if (decl && decl.type) {
            currType = decl.type;
        } else {
            const directStruct = findStructAnywhere(doc, firstBase);
            if (directStruct) {
                currType = directStruct.name;
            } else if (/^file\b/i.test(firstBase) || /^archivo\b/i.test(firstBase)) {
                currType = 'ARCHIVO';
            }
        }

        if (!currType) return null;

        for (let d = 0; d < firstDims; d++) {
            if (currType.endsWith('[]')) {
                currType = currType.slice(0, -2);
            }
        }

        for (let i = 1; i < segments.length; i++) {
            const seg = segments[i].trim();
            const memberName = seg.replace(/\[[^\]]*\]/g, '').trim();
            const memberDims = (seg.match(/\[/g) || []).length;

            const st = findStructAnywhere(doc, currType);
            if (!st || !st.parsedFields) return null;

            const field = st.parsedFields.find(f => f.name.toLowerCase() === memberName.toLowerCase());
            if (!field) return null;

            currType = field.type;
            for (let d = 0; d < memberDims; d++) {
                if (currType.endsWith('[]')) {
                    currType = currType.slice(0, -2);
                }
            }
        }

        return currType;
    }

    // -------------------------------------------------------------
    // Autocompletado Inteligente (CompletionItemProvider)
    // -------------------------------------------------------------
    const completionProvider = vscode.languages.registerCompletionItemProvider('ucaba', {
        provideCompletionItems(document, position, token, context) {
            if (isInCommentOrString(document, position)) {
                return null;
            }

            const linePrefix = document.lineAt(position).text.substr(0, position.character);

            // Verificar si el usuario está accediendo a un miembro mediante un punto (ej: pepe., file., actual.proximo_nodo.)
            const memberMatch = linePrefix.match(/([A-Za-z_][A-Za-z0-9_]*(?:\[[^\]]*\])?(?:\.[A-Za-z_][A-Za-z0-9_]*(?:\[[^\]]*\])?)*)\s*\.\s*([A-Za-z0-9_]*)$/);

            if (memberMatch) {
                const targetExpr = memberMatch[1].trim();
                const resolvedType = resolveExpressionType(document, targetExpr, position.line);
                const allStructs = getAllStructs(document);
                const memberItems = [];

                // Caso 1: El objeto es de tipo ARCHIVO (o variable de archivo)
                if (resolvedType && resolvedType.toUpperCase() === 'ARCHIVO') {
                    // LEER_LINEA()
                    const leerItem = new vscode.CompletionItem('LEER_LINEA', vscode.CompletionItemKind.Method);
                    leerItem.insertText = new vscode.SnippetString('LEER_LINEA()');
                    leerItem.detail = '(método) LEER_LINEA(): CADENA';
                    leerItem.documentation = new vscode.MarkdownString('Lee y retorna la siguiente línea de texto del archivo.');
                    leerItem.sortText = '0_LEER_LINEA';
                    memberItems.push(leerItem);

                    // ESCRIBIR_LINEA(texto)
                    const escribirItem = new vscode.CompletionItem('ESCRIBIR_LINEA', vscode.CompletionItemKind.Method);
                    escribirItem.insertText = new vscode.SnippetString('ESCRIBIR_LINEA(${1:texto})');
                    escribirItem.detail = '(método) ESCRIBIR_LINEA(texto: CADENA)';
                    escribirItem.documentation = new vscode.MarkdownString('Escribe una línea de texto en el archivo.');
                    escribirItem.sortText = '1_ESCRIBIR_LINEA';
                    memberItems.push(escribirItem);

                    // CERRAR_ARCHIVO()
                    const cerrarItem = new vscode.CompletionItem('CERRAR_ARCHIVO', vscode.CompletionItemKind.Method);
                    cerrarItem.insertText = new vscode.SnippetString('CERRAR_ARCHIVO()');
                    cerrarItem.detail = '(método) CERRAR_ARCHIVO()';
                    cerrarItem.documentation = new vscode.MarkdownString('Cierra el archivo liberando su descriptor en el sistema operativo.');
                    cerrarItem.sortText = '2_CERRAR_ARCHIVO';
                    memberItems.push(cerrarItem);

                    // findearchivo
                    const finItem = new vscode.CompletionItem('findearchivo', vscode.CompletionItemKind.Property);
                    finItem.detail = '(propiedad) findearchivo: BOOLEANO';
                    finItem.documentation = new vscode.MarkdownString('Retorna `VERDADERO` si se alcanzó el fin del archivo.');
                    finItem.sortText = '3_findearchivo';
                    memberItems.push(finItem);

                    return memberItems;
                }

                // Caso 2: El tipo resuelto es una ESTRUCTURA definida por el usuario
                const structObj = resolvedType ? findStructAnywhere(document, resolvedType) : null;
                if (structObj && structObj.parsedFields && structObj.parsedFields.length > 0) {
                    structObj.parsedFields.forEach(f => {
                        const fItem = new vscode.CompletionItem(f.name, vscode.CompletionItemKind.Field);
                        fItem.detail = `(campo) ${f.type} ${structObj.name}.${f.name}`;
                        let docMd = `### Campo de Estructura \`${structObj.name}\`\n\n- **Nombre:** \`${f.name}\`\n- **Tipo:** \`${f.type}\``;
                        if (f.doc) {
                            docMd += `\n- **Descripción:** ${f.doc}`;
                        }
                        fItem.documentation = new vscode.MarkdownString(docMd);
                        fItem.sortText = '0_' + f.name;
                        memberItems.push(fItem);
                    });
                    return memberItems;
                }

                // Caso 3: Es un vector, matriz o CADENA -> propiedad .largo
                if (resolvedType && (resolvedType.includes('[]') || resolvedType.toUpperCase() === 'CADENA')) {
                    const largoItem = new vscode.CompletionItem('largo', vscode.CompletionItemKind.Property);
                    largoItem.detail = '(propiedad) largo: ENTERO';
                    largoItem.documentation = new vscode.MarkdownString('Retorna la cantidad de elementos del vector, filas de la matriz o longitud de la cadena.');
                    largoItem.sortText = '0_largo';
                    memberItems.push(largoItem);
                    return memberItems;
                }

                // Caso 4: Tipo no determinado con certeza (fallback inteligente)
                // Ofrecemos los atributos de las estructuras definidas en el documento
                allStructs.forEach(st => {
                    if (st.parsedFields) {
                        st.parsedFields.forEach(f => {
                            const fItem = new vscode.CompletionItem(f.name, vscode.CompletionItemKind.Field);
                            fItem.detail = `(campo) ${f.type} ${st.name}.${f.name}`;
                            fItem.documentation = new vscode.MarkdownString(`### Campo de Estructura \`${st.name}\`\n\n- **Tipo:** \`${f.type}\``);
                            fItem.sortText = '1_' + st.name + '_' + f.name;
                            memberItems.push(fItem);
                        });
                    }
                });

                // Métodos de archivo como fallback
                const fallbackLeer = new vscode.CompletionItem('LEER_LINEA', vscode.CompletionItemKind.Method);
                fallbackLeer.insertText = new vscode.SnippetString('LEER_LINEA()');
                fallbackLeer.detail = '(método) LEER_LINEA(): CADENA (ARCHIVO)';
                fallbackLeer.sortText = '2_LEER_LINEA';
                memberItems.push(fallbackLeer);

                const fallbackEscribir = new vscode.CompletionItem('ESCRIBIR_LINEA', vscode.CompletionItemKind.Method);
                fallbackEscribir.insertText = new vscode.SnippetString('ESCRIBIR_LINEA(${1:texto})');
                fallbackEscribir.detail = '(método) ESCRIBIR_LINEA(texto) (ARCHIVO)';
                fallbackEscribir.sortText = '2_ESCRIBIR_LINEA';
                memberItems.push(fallbackEscribir);

                const fallbackCerrar = new vscode.CompletionItem('CERRAR_ARCHIVO', vscode.CompletionItemKind.Method);
                fallbackCerrar.insertText = new vscode.SnippetString('CERRAR_ARCHIVO()');
                fallbackCerrar.detail = '(método) CERRAR_ARCHIVO() (ARCHIVO)';
                fallbackCerrar.sortText = '2_CERRAR_ARCHIVO';
                memberItems.push(fallbackCerrar);

                const fallbackFin = new vscode.CompletionItem('findearchivo', vscode.CompletionItemKind.Property);
                fallbackFin.detail = '(propiedad) findearchivo: BOOLEANO (ARCHIVO)';
                fallbackFin.sortText = '2_findearchivo';
                memberItems.push(fallbackFin);

                const fallbackLargo = new vscode.CompletionItem('largo', vscode.CompletionItemKind.Property);
                fallbackLargo.detail = '(propiedad) largo: ENTERO (Vector / Matriz / Cadena)';
                fallbackLargo.sortText = '3_largo';
                memberItems.push(fallbackLargo);

                return memberItems;
            }

            const items = [];

            // Tipos de datos
            const tipos = [
                { name: 'ENTERO', desc: 'Tipo numérico entero de 32 bits (-2^31 a 2^31-1)' },
                { name: 'FLOTANTE', desc: 'Tipo de coma flotante de precisión simple IEEE-754 (32 bits)' },
                { name: 'REAL', desc: 'Tipo de coma flotante de doble precisión IEEE-754 (64 bits)' },
                { name: 'CADENA', desc: 'Cadena de caracteres alfanumérica' },
                { name: 'CARACTER', desc: 'Un solo caracter alfanumérico' },
                { name: 'BOOLEANO', desc: 'Valor lógico: VERDADERO o FALSO' },
                { name: 'ARCHIVO', desc: 'Descriptor para manejo de archivos' },
                { name: 'NULO', desc: 'Tipo y valor nulo o referencia vacía (equivalente a null o None)' }
            ];

            tipos.forEach(t => {
                const item = new vscode.CompletionItem(t.name, vscode.CompletionItemKind.TypeParameter);
                item.detail = 'Tipo de dato UCABA';
                item.documentation = new vscode.MarkdownString(t.desc);
                items.push(item);
            });

            // Estructuras definidas en el documento como tipos sugeridos
            const docStructs = getAllStructs(document);
            docStructs.forEach(st => {
                const item = new vscode.CompletionItem(st.name, vscode.CompletionItemKind.Struct);
                item.detail = `Estructura personalizada '${st.name}'`;
                item.documentation = new vscode.MarkdownString(`### Estructura \`${st.name}\`\n\n${st.fields.map(f => `- \`${f}\``).join('\n')}`);
                items.push(item);
            });

            // Palabras clave
            const keywords = [
                'ALGORITMO', 'INICIO', 'FIN',
                'ESTRUCTURA', 'FIN ESTRUCTURA',
                'FUNCION', 'FIN FUNCION',
                'PROCEDIMIENTO', 'FIN PROCEDIMIENTO',
                'RETORNAR',
                'SI', 'ENTONCES', 'SINO', 'SINO SI', 'FIN SI',
                'MIENTRAS', 'FIN MIENTRAS',
                'PARA', 'HASTA', 'PASO', 'HACER', 'FIN PARA',
                'VERDADERO', 'FALSO',
                'NULO', 'NULL', 'NONE',
                'MOD', 'Y', 'O', 'NO'
            ];

            keywords.forEach(kw => {
                const item = new vscode.CompletionItem(kw, vscode.CompletionItemKind.Keyword);
                items.push(item);
            });

            // Snippet de Estructura
            const structSnippet = new vscode.CompletionItem('ESTRUCTURA', vscode.CompletionItemKind.Struct);
            structSnippet.insertText = new vscode.SnippetString('ESTRUCTURA ${1:Nombre}:\n    ${2:CADENA campo1}\nFIN ESTRUCTURA');
            structSnippet.detail = 'Definición de Estructura';
            structSnippet.documentation = new vscode.MarkdownString('Define una estructura de datos personalizada con campos fuertemente tipados.');
            items.push(structSnippet);

            // Funciones incorporadas (Built-ins)
            const builtins = [
                {
                    name: 'MOSTRAR',
                    kind: vscode.CompletionItemKind.Function,
                    snippet: 'MOSTRAR ${1:expresion}',
                    detail: 'MOSTRAR ...',
                    doc: 'Imprime una o más expresiones por consola.'
                },
                {
                    name: 'IMPRIMIR',
                    kind: vscode.CompletionItemKind.Function,
                    snippet: 'IMPRIMIR(${1:expresion})',
                    detail: 'IMPRIMIR(expresion)',
                    doc: 'Imprime una o más expresiones por consola.'
                },
                {
                    name: 'LEER',
                    kind: vscode.CompletionItemKind.Function,
                    snippet: 'LEER ${1:variable}',
                    detail: 'LEER ...',
                    doc: 'Lee un valor por consola y lo asigna a la variable.'
                },
                {
                    name: 'ESPAR',
                    kind: vscode.CompletionItemKind.Function,
                    snippet: 'ESPAR(${1:numero})',
                    detail: 'ESPAR(num: ENTERO): BOOLEANO',
                    doc: 'Devuelve VERDADERO si el número es par.'
                },
                {
                    name: 'ESIMPAR',
                    kind: vscode.CompletionItemKind.Function,
                    snippet: 'ESIMPAR(${1:numero})',
                    detail: 'ESIMPAR(num: ENTERO): BOOLEANO',
                    doc: 'Devuelve VERDADERO si el número es impar.'
                },
                {
                    name: 'ABRIR_ARCHIVO',
                    kind: vscode.CompletionItemKind.Function,
                    snippet: 'ABRIR_ARCHIVO(\"${1:ruta}\", \"${2|lectura,escritura,anexo|}\")',
                    detail: 'ABRIR_ARCHIVO(ruta, modo): ARCHIVO',
                    doc: 'Abre un archivo y devuelve su manejador.'
                },
                {
                    name: 'LEER_LINEA',
                    kind: vscode.CompletionItemKind.Function,
                    snippet: 'LEER_LINEA(${1:handle})',
                    detail: 'LEER_LINEA(handle): CADENA',
                    doc: 'Lee la siguiente línea de un archivo abierto.'
                },
                {
                    name: 'ESCRIBIR_LINEA',
                    kind: vscode.CompletionItemKind.Function,
                    snippet: 'ESCRIBIR_LINEA(${1:handle}, ${2:texto})',
                    detail: 'ESCRIBIR_LINEA(handle, texto)',
                    doc: 'Escribe una línea de texto en el archivo abierto.'
                },
                {
                    name: 'CERRAR_ARCHIVO',
                    kind: vscode.CompletionItemKind.Function,
                    snippet: 'CERRAR_ARCHIVO(${1:handle})',
                    detail: 'CERRAR_ARCHIVO(handle)',
                    doc: 'Cierra el archivo abierto liberando su descriptor.'
                }
            ];

            builtins.forEach(b => {
                const item = new vscode.CompletionItem(b.name, b.kind);
                item.insertText = new vscode.SnippetString(b.snippet);
                item.detail = b.detail;
                item.documentation = new vscode.MarkdownString(b.doc);
                items.push(item);
            });

            return items;
        }
    }, '.', ' ');

    context.subscriptions.push(completionProvider);

    // -------------------------------------------------------------
    // Información sobre el Cursor (HoverProvider)
    // -------------------------------------------------------------
    // Documentación de palabras reservadas, tipos, built-ins (clave en MAYÚSCULAS).
    const hoverDocs = {
        'ENTERO': '```ucaba\nENTERO variable = 0\n```\nTipo numérico entero con signo (64 bits).',
        'FLOTANTE': '```ucaba\nFLOTANTE variable = 0.0\n```\nTipo coma flotante de 32 bits (IEEE-754 Single Precision).',
        'REAL': '```ucaba\nREAL variable = 0.0\n```\nTipo coma flotante de 64 bits (IEEE-754 Double Precision).',
        'CADENA': '```ucaba\nCADENA texto = "Hola"\n```\nTipo de texto / cadena de caracteres.',
        'CARACTER': '```ucaba\nCARACTER letra = \'A\'\n```\nTipo para un único carácter alfanumérico.',
        'BOOLEANO': '```ucaba\nBOOLEANO flag = VERDADERO\n```\nTipo lógico booleano (`VERDADERO` o `FALSO`).',
        'ARCHIVO': '```ucaba\nARCHIVO f = ABRIR_ARCHIVO("datos.txt", "lectura")\n```\nManejador de archivos para lectura o escritura.',
        'RETORNAR': '```ucaba\nRETORNAR valor\n```\nDevuelve un valor desde una función o finaliza la ejecución de un procedimiento.',
        'FUNCION': '```ucaba\nFUNCION nombre(p1: tipo): tipo_retorno\n    RETORNAR valor\nFIN FUNCION\n```\nDefine una función que devuelve un valor.',
        'PROCEDIMIENTO': '```ucaba\nPROCEDIMIENTO nombre(p1: tipo)\n    // bloque\nFIN PROCEDIMIENTO\n```\nDefine un procedimiento (sin valor de retorno).',
        'MOSTRAR': '```ucaba\nMOSTRAR "Mensaje", variable\n```\nImprime valores en la consola de salida estándar.',
        'IMPRIMIR': '```ucaba\nIMPRIMIR("Mensaje" + variable)\n```\nImprime valores en la consola de salida estándar.',
        'LEER': '```ucaba\nLEER variable\n```\nLee un dato ingresado por el usuario por teclado y lo almacena en la variable.',
        'MOD': '```ucaba\nresultado = a MOD b\n```\nCalcula el resto de la división entera entre dos números.',
        'ESPAR': '```ucaba\nESPAR(numero): BOOLEANO\n```\nRetorna `VERDADERO` si el argumento entero es par, `FALSO` si no.',
        'ESIMPAR': '```ucaba\nESIMPAR(numero): BOOLEANO\n```\nRetorna `VERDADERO` si el argumento entero es impar, `FALSO` si no.',
        'ABRIR_ARCHIVO': '```ucaba\nABRIR_ARCHIVO(ruta: CADENA, modo: CADENA): ARCHIVO\n```\nAbre un archivo y devuelve su manejador.',
        'ESTRUCTURA': '```ucaba\nESTRUCTURA Nombre:\n    CADENA campo1\n    ENTERO campo2\nFIN ESTRUCTURA\n```\nDefine una estructura de datos personalizada con campos fuertemente tipados.',
        'INICIO': 'Marca el comienzo del programa principal.',
        'FIN': 'Cierra un bloque (`FIN SI`, `FIN PARA`, `FIN MIENTRAS`, `FIN FUNCION`, `FIN PROCEDIMIENTO`, `FIN ESTRUCTURA`) o el programa.',
        'SI': '```ucaba\nSI (condicion)\n    // bloque\nSINO\n    // bloque\nFIN SI\n```\nEstructura condicional.',
        'SINO': 'Rama alternativa de una estructura condicional `SI`.',
        'MIENTRAS': '```ucaba\nMIENTRAS (condicion)\n    // bloque\nFIN MIENTRAS\n```\nRepite el bloque mientras la condición sea verdadera.',
        'PARA': '```ucaba\nPARA(ENTERO i = 0; i < 10; i++)\n    // bloque\nFIN PARA\n```\nBucle con contador.',
        'HACER': 'Inicio de un bucle `HACER ... MIENTRAS`.',
        'VERDADERO': 'Constante lógica verdadera (`BOOLEANO`).',
        'FALSO': 'Constante lógica falsa (`BOOLEANO`).',
        'NULO': '```ucaba\nNodo nodo_actual = NULO\nSI (nodo_actual == NULO)\n```\nValor nulo o referencia vacía (equivalente a `null` en C/Java/JS o `None` en Python).',
        'NULL': '```ucaba\nNodo nodo_actual = NULL\n```\nAlias de `NULO` (referencia nula vacía).',
        'NONE': '```ucaba\nNodo nodo_actual = NONE\n```\nAlias de `NULO` (referencia nula vacía).',
        'Y': 'Operador lógico AND.',
        'O': 'Operador lógico OR.',
        'NO': 'Operador lógico NOT.'
    };

    // Propiedades / métodos accedidos con punto (clave en minúsculas).
    const propertyDocs = {
        'largo': '(propiedad) `ENTERO`\n\nCantidad de elementos de un vector, filas de una matriz o caracteres de una cadena.\n\n```ucaba\nENTERO n = vector.largo\nENTERO columnas = matriz[0].largo\n```',
        'findearchivo': '(propiedad) `BOOLEANO`\n\nDevuelve `VERDADERO` si se alcanzó el fin del archivo.\n\n```ucaba\nMIENTRAS NO file.findearchivo\n```',
        'leer_linea': '(método) `LEER_LINEA(): CADENA`\n\nLee la siguiente línea de un archivo abierto.',
        'escribir_linea': '(método) `ESCRIBIR_LINEA(texto: CADENA)`\n\nEscribe una línea de texto en el archivo abierto.',
        'cerrar_archivo': '(método) `CERRAR_ARCHIVO()`\n\nCierra el archivo abierto liberando su descriptor.'
    };

    function makeHover(markdown, range) {
        const md = new vscode.MarkdownString(markdown);
        md.isTrusted = false;
        return new vscode.Hover(md, range);
    }

    const hoverProvider = vscode.languages.registerHoverProvider('ucaba', {
        async provideHover(document, position, token) {
            const wordRange = document.getWordRangeAtPosition(position, /[A-Za-z_][A-Za-z0-9_]*/);
            if (!wordRange) return null;
            if (isInCommentOrString(document, position)) return null;

            const word = document.getText(wordRange);
            const lineText = document.lineAt(position.line).text;
            const isProperty = wordRange.start.character > 0 &&
                /\.\s*$/.test(lineText.substring(0, wordRange.start.character));

            // 1. Propiedades y métodos con punto (vector.largo, archivo.findearchivo, struct.campo, ...)
            if (isProperty) {
                const prop = propertyDocs[word.toLowerCase()];
                if (prop) return makeHover(prop, wordRange);

                // Si es un acceso a propiedad de una estructura (ej: pepe.nombre)
                const preLine = lineText.substring(0, wordRange.start.character);
                const dotMatch = preLine.match(/([A-Za-z_][A-Za-z0-9_]*(?:\[[^\]]*\])?(?:\.[A-Za-z_][A-Za-z0-9_]*(?:\[[^\]]*\])?)*)\s*\.\s*$/);
                if (dotMatch) {
                    const targetExpr = dotMatch[1].trim();
                    const targetType = resolveExpressionType(document, targetExpr, position.line);
                    if (targetType) {
                        const st = findStructAnywhere(document, targetType);
                        if (st && st.parsedFields) {
                            const f = st.parsedFields.find(x => x.name.toLowerCase() === word.toLowerCase());
                            if (f) {
                                let md = '```ucaba\n(campo) ' + f.type + ' ' + st.name + '.' + f.name + '\n```';
                                md += `\n\n*Campo de la estructura* \`${st.name}\``;
                                if (f.doc) md += '\n\n' + f.doc;
                                return makeHover(md, wordRange);
                            }
                        }
                    }
                }
                return null;
            }

            // 2. Palabras reservadas, tipos y funciones incorporadas
            const isReserved = Object.prototype.hasOwnProperty.call(hoverDocs, word.toUpperCase());
            if (isReserved) {
                return makeHover(hoverDocs[word.toUpperCase()], wordRange);
            }

            // 3. Funciones / procedimientos definidos por el usuario
            let fn = findFunctionInDocument(document, word);
            if (!fn) {
                try {
                    const files = await vscode.workspace.findFiles('**/*.ucaba', '**/node_modules/**');
                    for (const fileUri of files) {
                        if (fileUri.toString() === document.uri.toString()) continue;
                        const other = await vscode.workspace.openTextDocument(fileUri);
                        fn = findFunctionInDocument(other, word);
                        if (fn) break;
                    }
                } catch (e) {
                    // Ignorar errores de búsqueda en el workspace
                }
            }
            if (fn) {
                const signature = `${fn.kind} ${fn.name}(${fn.params})${fn.returnType ? ': ' + fn.returnType : ''}`;
                let md = '```ucaba\n' + signature + '\n```';
                md += `\n\n*${fn.kind === 'FUNCION' ? 'Función' : 'Procedimiento'}* definido en línea ${fn.line + 1}`;
                if (fn.doc !== document) {
                    md += ` de \`${path.basename(fn.doc.fileName)}\``;
                }
                if (fn.comment) md += '\n\n' + fn.comment;
                return makeHover(md, wordRange);
            }

            // 4. Estructuras definidas por el usuario
            let st = findStructInDocument(document, word);
            if (!st) {
                try {
                    const files = await vscode.workspace.findFiles('**/*.ucaba', '**/node_modules/**');
                    for (const fileUri of files) {
                        if (fileUri.toString() === document.uri.toString()) continue;
                        const other = await vscode.workspace.openTextDocument(fileUri);
                        st = findStructInDocument(other, word);
                        if (st) break;
                    }
                } catch (e) {
                    // Ignorar errores de búsqueda
                }
            }
            if (st) {
                const fieldsStr = st.fields.length > 0 ? '\n    ' + st.fields.join('\n    ') : '';
                let md = '```ucaba\nEstructura ' + st.name + ':' + fieldsStr + '\nFin Estructura\n```';
                md += `\n\n*Estructura* definida en línea ${st.line + 1}`;
                if (st.doc !== document) {
                    md += ` de \`${path.basename(st.doc.fileName)}\``;
                }
                if (st.comment) md += '\n\n' + st.comment;
                return makeHover(md, wordRange);
            }

            // 5. Variables y parámetros declarados
            const decl = findVariableDeclaration(document, word, position.line);
            if (decl) {
                const md = '```ucaba\n(' + decl.kind + ') ' + decl.type + ' ' + decl.name + '\n```' +
                    `\n\nDeclarado en línea ${decl.line + 1}`;
                return makeHover(md, wordRange);
            }

            return null;
        }
    });

    context.subscriptions.push(hoverProvider);

    // -------------------------------------------------------------
    // Navegación a Definición (DefinitionProvider: Ctrl + Clic / F12)
    // -------------------------------------------------------------
    const definitionProvider = vscode.languages.registerDefinitionProvider('ucaba', {
        async provideDefinition(document, position, token) {
            const wordRange = document.getWordRangeAtPosition(position);
            if (!wordRange) return null;
            const word = document.getText(wordRange);

            if (!word || !/^[A-Za-z_][A-Za-z0-9_]*$/.test(word)) {
                return null;
            }

            // Ignorar palabras reservadas estándar
            const ignoredKeywords = new Set([
                'INICIO', 'FIN', 'SI', 'ENTONCES', 'SINO', 'MIENTRAS', 'PARA', 'HASTA', 'PASO', 'HACER',
                'VERDADERO', 'FALSO', 'MOD', 'Y', 'O', 'NO', 'RETORNAR', 'ALGORITMO',
                'ENTERO', 'FLOTANTE', 'REAL', 'CADENA', 'CARACTER', 'BOOLEANO', 'ARCHIVO', 'VOID'
            ]);
            if (ignoredKeywords.has(word.toUpperCase())) {
                return null;
            }

            // 1. Buscar definición de ESTRUCTURA en el documento actual
            const structDefRegex = new RegExp(`^\\s*Estructura\\s+(${escapeRegex(word)})\\s*:?`, 'i');
            for (let i = 0; i < document.lineCount; i++) {
                const line = document.lineAt(i);
                const match = line.text.match(structDefRegex);
                if (match) {
                    const col = line.text.indexOf(match[1]);
                    const targetRange = new vscode.Range(i, col, i, col + match[1].length);
                    return new vscode.Location(document.uri, targetRange);
                }
            }

            // 2. Buscar definición de FUNCION o PROCEDIMIENTO en el documento actual
            const fnDefRegex = new RegExp(`^\\s*(?:FUNCION|PROCEDIMIENTO)\\s+(${escapeRegex(word)})\\b`, 'i');

            for (let i = 0; i < document.lineCount; i++) {
                const line = document.lineAt(i);
                const match = line.text.match(fnDefRegex);
                if (match) {
                    const col = line.text.indexOf(match[1]);
                    const targetRange = new vscode.Range(i, col, i, col + match[1].length);
                    return new vscode.Location(document.uri, targetRange);
                }
            }

            // 3. Buscar declaración de variable o parámetro en el documento actual
            const typeKeywords = 'ENTERO|FLOTANTE|REAL|CADENA|CARACTER|BOOLEANO|ARCHIVO';
            const varDeclRegex = new RegExp(`(?:\\b(?:${typeKeywords})\\s+(?:\\[[^\\]]*\\]\\s*)*|\\b)(${escapeRegex(word)})\\s*(?::\\s*(?:${typeKeywords})|(?:\\[[^\\]]*\\])?\\s*=)`, 'i');

            // Búsqueda hacia atrás (alcance local más cercano)
            for (let i = position.line - 1; i >= 0; i--) {
                const line = document.lineAt(i);
                const match = line.text.match(varDeclRegex);
                if (match) {
                    const varName = match[1];
                    const col = line.text.indexOf(varName);
                    if (col !== -1) {
                        return new vscode.Location(document.uri, new vscode.Range(i, col, i, col + varName.length));
                    }
                }
                // Si llegamos a la cabecera de la función, revisar sus parámetros
                if (/^\s*(?:FUNCION|PROCEDIMIENTO)\b/i.test(line.text)) {
                    const paramRegex = new RegExp(`\\b(${escapeRegex(word)})\\s*(?:\\[[^\\]]*\\])*\\s*:`, 'i');
                    const paramMatch = line.text.match(paramRegex);
                    if (paramMatch) {
                        const col = line.text.indexOf(paramMatch[1]);
                        return new vscode.Location(document.uri, new vscode.Range(i, col, i, col + paramMatch[1].length));
                    }
                    break;
                }
            }

            // 3. Buscar función en otros archivos .ucaba del workspace
            try {
                const files = await vscode.workspace.findFiles('**/*.ucaba', '**/node_modules/**');
                for (const fileUri of files) {
                    if (fileUri.toString() === document.uri.toString()) continue;
                    const otherDoc = await vscode.workspace.openTextDocument(fileUri);
                    for (let i = 0; i < otherDoc.lineCount; i++) {
                        const line = otherDoc.lineAt(i);
                        const match = line.text.match(fnDefRegex);
                        if (match) {
                            const col = line.text.indexOf(match[1]);
                            return new vscode.Location(fileUri, new vscode.Range(i, col, i, col + match[1].length));
                        }
                    }
                }
            } catch (e) {
                // Continuar si la búsqueda en workspace falla
            }

            return null;
        }
    });

    context.subscriptions.push(definitionProvider);

    // -------------------------------------------------------------
    // Referencias / Usos (ReferenceProvider: Shift + F12)
    // -------------------------------------------------------------
    const referenceProvider = vscode.languages.registerReferenceProvider('ucaba', {
        provideReferences(document, position, refContext, token) {
            const wordRange = document.getWordRangeAtPosition(position);
            if (!wordRange) return null;
            const word = document.getText(wordRange);

            if (!word || !/^[A-Za-z_][A-Za-z0-9_]*$/.test(word)) return null;

            const results = [];
            const wordRegex = new RegExp(`\\b${escapeRegex(word)}\\b`, 'g');

            for (let i = 0; i < document.lineCount; i++) {
                const line = document.lineAt(i);
                let match;
                while ((match = wordRegex.exec(line.text)) !== null) {
                    const isDecl = /^\s*(?:FUNCION|PROCEDIMIENTO)\s+/i.test(line.text) && line.text.indexOf(word) === match.index;
                    if (!refContext.includeDeclaration && isDecl) {
                        continue;
                    }
                    const range = new vscode.Range(i, match.index, i, match.index + word.length);
                    results.push(new vscode.Location(document.uri, range));
                }
            }

            return results;
        }
    });

    context.subscriptions.push(referenceProvider);

    // -------------------------------------------------------------
    // Vista de Estructura / Símbolos (DocumentSymbolProvider: Outline y Ctrl + Shift + O)
    // -------------------------------------------------------------
    const symbolProvider = vscode.languages.registerDocumentSymbolProvider('ucaba', {
        provideDocumentSymbols(document, token) {
            const symbols = [];
            const fnHeaderRegex = /^\s*(FUNCION|PROCEDIMIENTO)\s+([A-Za-z_][A-Za-z0-9_]*)\s*(?:\((.*?)\))?(?:\s*:\s*([A-Za-z0-9_\[\]]+))?/i;
            const endFnRegex = /^\s*FIN\s+(?:FUNCION|PROCEDIMIENTO)\b/i;
            const structHeaderRegex = /^\s*Estructura\s+([A-Za-z_][A-Za-z0-9_]*)\s*:?/i;
            const structEndRegex = /^\s*FIN\s+ESTRUCTURA\b/i;

            for (let i = 0; i < document.lineCount; i++) {
                const line = document.lineAt(i);

                // Estructuras
                const structMatch = line.text.match(structHeaderRegex);
                if (structMatch) {
                    const structName = structMatch[1];
                    const nameCol = line.text.indexOf(structName);
                    const selectionRange = new vscode.Range(i, nameCol, i, nameCol + structName.length);

                    let endLine = i;
                    const fieldSymbols = [];
                    for (let j = i + 1; j < document.lineCount; j++) {
                        const l = document.lineAt(j).text;
                        if (structEndRegex.test(l)) {
                            endLine = j;
                            break;
                        }
                        const fieldMatch = l.match(/^\s*([A-Za-z_][A-Za-z0-9_]*)\s+([A-Za-z_][A-Za-z0-9_]*)/);
                        if (fieldMatch) {
                            const fieldType = fieldMatch[1];
                            const fieldName = fieldMatch[2];
                            const fCol = l.indexOf(fieldName);
                            const fSelRange = new vscode.Range(j, fCol, j, fCol + fieldName.length);
                            const fFullRange = new vscode.Range(j, 0, j, l.length);
                            fieldSymbols.push(new vscode.DocumentSymbol(fieldName, fieldType, vscode.SymbolKind.Field, fFullRange, fSelRange));
                        }
                    }

                    const fullRange = new vscode.Range(i, 0, endLine, document.lineAt(endLine).text.length);
                    const structSymbol = new vscode.DocumentSymbol(structName, 'Estructura', vscode.SymbolKind.Struct, fullRange, selectionRange);
                    structSymbol.children = fieldSymbols;
                    symbols.push(structSymbol);
                    continue;
                }

                // Funciones y Procedimientos
                const match = line.text.match(fnHeaderRegex);
                if (match) {
                    const keyword = match[1].toUpperCase();
                    const fnName = match[2];
                    const params = match[3] || '';
                    const returnType = match[4] || (keyword === 'PROCEDIMIENTO' ? 'VOID' : '');
                    const kind = keyword === 'PROCEDIMIENTO' ? vscode.SymbolKind.Method : vscode.SymbolKind.Function;

                    const nameCol = line.text.indexOf(fnName);
                    const selectionRange = new vscode.Range(i, nameCol, i, nameCol + fnName.length);

                    let endLine = i;
                    for (let j = i + 1; j < document.lineCount; j++) {
                        const l = document.lineAt(j).text;
                        if (endFnRegex.test(l)) {
                            endLine = j;
                            break;
                        }
                        if (fnHeaderRegex.test(l) || structHeaderRegex.test(l)) {
                            endLine = j - 1;
                            break;
                        }
                    }

                    const fullRange = new vscode.Range(i, 0, endLine, document.lineAt(endLine).text.length);
                    const detail = `(${params})${returnType ? ': ' + returnType : ''}`;

                    symbols.push(new vscode.DocumentSymbol(fnName, detail, kind, fullRange, selectionRange));
                }
            }
            return symbols;
        }
    });

    context.subscriptions.push(symbolProvider);

    // -------------------------------------------------------------
    // Comandos de Ejecución y Chequeo
    // -------------------------------------------------------------
    context.subscriptions.push(
        vscode.commands.registerCommand('ucaba.runFile', () => {
            const editor = vscode.window.activeTextEditor;
            if (!editor) {
                vscode.window.showErrorMessage('No hay ningún archivo .ucaba activo.');
                return;
            }
            const filePath = editor.document.fileName;
            if (!filePath.endsWith('.ucaba')) {
                vscode.window.showErrorMessage('Solo se pueden ejecutar archivos con extensión .ucaba');
                return;
            }

            editor.document.save().then(() => {
                const terminal = vscode.window.activeTerminal || vscode.window.createTerminal('UCABA');
                terminal.show();
                const runner = getUcabaRunner();
                const args = runner.isCli ? ['run', filePath] : ['-m', 'pseudocode', 'run', filePath];
                terminal.sendText(buildTerminalCommand(terminal, runner.executable, args));
            });
        })
    );

    context.subscriptions.push(
        vscode.commands.registerCommand('ucaba.checkFile', () => {
            const editor = vscode.window.activeTextEditor;
            if (!editor) {
                vscode.window.showErrorMessage('No hay ningún archivo .ucaba activo.');
                return;
            }
            const filePath = editor.document.fileName;
            if (!filePath.endsWith('.ucaba')) {
                vscode.window.showErrorMessage('Solo se pueden verificar archivos con extensión .ucaba');
                return;
            }

            editor.document.save().then(() => {
                const terminal = vscode.window.activeTerminal || vscode.window.createTerminal('UCABA');
                terminal.show();
                const runner = getUcabaRunner();
                const args = runner.isCli ? ['check', filePath] : ['-m', 'pseudocode', 'check', filePath];
                terminal.sendText(buildTerminalCommand(terminal, runner.executable, args));
            });
        })
    );

    context.subscriptions.push(
        vscode.commands.registerCommand('ucaba.startRepl', () => {
            const terminal = vscode.window.activeTerminal || vscode.window.createTerminal('UCABA REPL');
            terminal.show();
            const runner = getUcabaRunner();
            const args = runner.isCli ? ['repl'] : ['-m', 'pseudocode', 'repl'];
            terminal.sendText(buildTerminalCommand(terminal, runner.executable, args));
        })
    );
}

function deactivate() {}

module.exports = {
    activate,
    deactivate
};
