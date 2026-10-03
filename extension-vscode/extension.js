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

    if (process.platform === 'win32') {
        const localAppData = process.env.LOCALAPPDATA || path.join(process.env.USERPROFILE || '', 'AppData', 'Local');
        const defaultCli = path.join(localAppData, 'Programs', 'UCABA', 'bin', 'ucaba.exe');
        if (fs.existsSync(defaultCli)) {
            return { isCli: true, executable: defaultCli };
        }
    }

    try {
        const testRes = cp.spawnSync(process.platform === 'win32' ? 'ucaba.exe' : 'ucaba', ['--help'], { shell: true, timeout: 600 });
        if (testRes.status === 0) {
            return { isCli: true, executable: 'ucaba' };
        }
    } catch (e) {}

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

        const args = runner.isCli ? ['lsp-check', '--lenient'] : ['-m', 'pseudocode.lsp_check', '--lenient'];
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
    // Autocompletado (CompletionItemProvider)
    // -------------------------------------------------------------
    const completionProvider = vscode.languages.registerCompletionItemProvider('ucaba', {
        provideCompletionItems(document, position, token, context) {
            const linePrefix = document.lineAt(position).text.substr(0, position.character);

            // Si es un acceso a propiedad con punto (ej: mi_vector.)
            if (linePrefix.endsWith('.')) {
                const largoItem = new vscode.CompletionItem('largo', vscode.CompletionItemKind.Property);
                largoItem.detail = 'Propiedad: cantidad de elementos';
                largoItem.documentation = new vscode.MarkdownString('Retorna la cantidad de elementos de un vector, filas de una matriz o longitud de una cadena.');

                const findearchivoItem = new vscode.CompletionItem('findearchivo', vscode.CompletionItemKind.Method);
                findearchivoItem.detail = 'Método: fin de archivo';
                findearchivoItem.documentation = new vscode.MarkdownString('Retorna VERDADERO si se alcanzó el fin del archivo.');

                return [largoItem, findearchivoItem];
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
                { name: 'ARCHIVO', desc: 'Descriptor para manejo de archivos' }
            ];

            tipos.forEach(t => {
                const item = new vscode.CompletionItem(t.name, vscode.CompletionItemKind.TypeParameter);
                item.detail = 'Tipo de dato UCABA';
                item.documentation = new vscode.MarkdownString(t.desc);
                items.push(item);
            });

            // Palabras clave
            const keywords = [
                'ALGORITMO', 'INICIO', 'FIN',
                'FUNCION', 'FIN FUNCION',
                'PROCEDIMIENTO', 'FIN PROCEDIMIENTO',
                'RETORNAR',
                'SI', 'ENTONCES', 'SINO', 'SINO SI', 'FIN SI',
                'MIENTRAS', 'FIN MIENTRAS',
                'PARA', 'HASTA', 'PASO', 'HACER', 'FIN PARA',
                'VERDADERO', 'FALSO',
                'MOD', 'Y', 'O', 'NO'
            ];

            keywords.forEach(kw => {
                const item = new vscode.CompletionItem(kw, vscode.CompletionItemKind.Keyword);
                items.push(item);
            });

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
                    snippet: 'ABRIR_ARCHIVO(\"${1:ruta}\", \"${2|r,w,a|}\")',
                    detail: 'ABRIR_ARCHIVO(ruta, modo): ENTERO',
                    doc: 'Abre un archivo en modo lectura ("r"), escritura ("w") o anexo ("a").'
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
    const hoverDocs = {
        'ENTERO': '```ucaba\nENTERO variable = 0\n```\nTipo numérico entero con signo de 32 bits (-2,147,483,648 a 2,147,483,647).',
        'FLOTANTE': '```ucaba\nFLOTANTE variable = 0.0\n```\nTipo coma flotante de 32 bits (IEEE-754 Single Precision).',
        'REAL': '```ucaba\nREAL variable = 0.0\n```\nTipo coma flotante de 64 bits (IEEE-754 Double Precision).',
        'CADENA': '```ucaba\nCADENA texto = "Hola"\n```\nTipo de texto / cadena de caracteres.',
        'CARACTER': '```ucaba\nCARACTER letra = \'A\'\n```\nTipo para un único carácter alfanumérico.',
        'BOOLEANO': '```ucaba\nBOOLEANO flag = VERDADERO\n```\nTipo lógico booleano (`VERDADERO` o `FALSO`).',
        'ARCHIVO': '```ucaba\nENTERO archivo = ABRIR_ARCHIVO("datos.txt", "r")\n```\nManejador de archivos para lectura o escritura.',
        'RETORNAR': '```ucaba\nRETORNAR valor\n```\nDevuelve un valor desde una función o finaliza la ejecución de un procedimiento.',
        'largo': '```ucaba\nENTERO n = vector.largo\n```\nPropiedad nativa que devuelve la cantidad de elementos de un vector o caracteres de una cadena.',
        'MOSTRAR': '```ucaba\nMOSTRAR "Mensaje", variable\n```\nImprime valores en la consola de salida estándar.',
        'LEER': '```ucaba\nLEER variable\n```\nLee un dato ingresado por el usuario por teclado y lo almacena en la variable.',
        'MOD': '```ucaba\nresultado = a MOD b\n```\nCalcula el resto de la división entera entre dos números.',
        'ESPAR': '```ucaba\nESPAR(numero): BOOLEANO\n```\nRetorna `VERDADERO` si el argumento entero es par, `FALSO` si no.',
        'ESIMPAR': '```ucaba\nESIMPAR(numero): BOOLEANO\n```\nRetorna `VERDADERO` si el argumento entero es impar, `FALSO` si no.'
    };

    const hoverProvider = vscode.languages.registerHoverProvider('ucaba', {
        provideHover(document, position, token) {
            const wordRange = document.getWordRangeAtPosition(position);
            if (!wordRange) return null;
            const word = document.getText(wordRange);

            if (hoverDocs[word]) {
                return new vscode.Hover(new vscode.MarkdownString(hoverDocs[word]));
            }
            if (hoverDocs[word.toUpperCase()]) {
                return new vscode.Hover(new vscode.MarkdownString(hoverDocs[word.toUpperCase()]));
            }
            return null;
        }
    });

    context.subscriptions.push(hoverProvider);

    // -------------------------------------------------------------
    // Navegación a Definición (DefinitionProvider: Ctrl + Clic / F12)
    // -------------------------------------------------------------
    function escapeRegex(string) {
        return string.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
    }

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

            // 1. Buscar definición de FUNCION o PROCEDIMIENTO en el documento actual
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

            // 2. Buscar declaración de variable o parámetro en el documento actual
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

            for (let i = 0; i < document.lineCount; i++) {
                const line = document.lineAt(i);
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
                        if (fnHeaderRegex.test(l)) {
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
                if (runner.isCli) {
                    terminal.sendText(`"${runner.executable}" run "${filePath}"`);
                } else {
                    terminal.sendText(`${runner.executable} -m pseudocode run "${filePath}"`);
                }
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
                if (runner.isCli) {
                    terminal.sendText(`"${runner.executable}" check "${filePath}"`);
                } else {
                    terminal.sendText(`${runner.executable} -m pseudocode check "${filePath}"`);
                }
            });
        })
    );
}

function deactivate() {}

module.exports = {
    activate,
    deactivate
};
