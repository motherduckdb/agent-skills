#!/usr/bin/env node
/**
 * Syntax-check TypeScript/TSX/JS code from stdin.
 *
 * Input:  JSON array of {code: string, kind: "TS"|"TSX"|"JS"} on stdin
 * Output: JSON array of {index: number, errors: [{line, character, message}]} on stdout
 *
 * Exit code: 0 = no parse errors, 1 = at least one snippet has errors.
 *
 * For TSX snippets that fail initial parsing (JSX fragments, expression snippets),
 * retries by wrapping in a component function.
 */

const ts = require("typescript");
const fs = require("fs");

const SCRIPT_KINDS = {
  TS: ts.ScriptKind.TS,
  TSX: ts.ScriptKind.TSX,
  JS: ts.ScriptKind.JS,
};

const FILE_EXTENSIONS = {
  TS: "ts",
  TSX: "tsx",
  JS: "js",
};

function parseSnippet(code, fileName, kind) {
  const sourceFile = ts.createSourceFile(
    fileName,
    code,
    ts.ScriptTarget.Latest,
    /* setParentNodes */ true,
    kind
  );
  return (sourceFile.parseDiagnostics || []).map((d) => {
    const pos = sourceFile.getLineAndCharacterOfPosition(d.start || 0);
    return {
      line: pos.line + 1,
      character: pos.character + 1,
      message: ts.flattenDiagnosticMessageText(d.messageText, "\n"),
    };
  });
}

const input = fs.readFileSync(0, "utf8");
const snippets = JSON.parse(input);
let hasErrors = false;

const results = snippets.map((snippet, index) => {
  const kind = SCRIPT_KINDS[snippet.kind] || ts.ScriptKind.TS;
  const ext = FILE_EXTENSIONS[snippet.kind] || "ts";
  const fileName = `snippet_${index}.${ext}`;

  // First attempt: parse as-is
  const errors = parseSnippet(snippet.code, fileName, kind);

  if (errors.length === 0) {
    return { index, errors: [] };
  }

  // For TSX snippets, retry by wrapping in a component (handles JSX fragments)
  if (snippet.kind === "TSX") {
    const wrapped = `function __SnippetWrapper__() {\n  return (<>\n${snippet.code}\n  </>);\n}`;
    const wrappedErrors = parseSnippet(wrapped, fileName, kind);
    if (wrappedErrors.length === 0) {
      return { index, errors: [] };
    }

    // Also try wrapping as a statement block (handles expression snippets)
    const wrappedBlock = `function __SnippetWrapper__() {\n${snippet.code}\n}`;
    const blockErrors = parseSnippet(wrappedBlock, fileName, kind);
    if (blockErrors.length === 0) {
      return { index, errors: [] };
    }
  }

  hasErrors = true;
  return { index, errors };
});

process.stdout.write(JSON.stringify(results));
process.exit(hasErrors ? 1 : 0);
