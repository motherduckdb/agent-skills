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

function parseInput() {
  const input = fs.readFileSync(0, "utf8");
  const snippets = JSON.parse(input);
  if (!Array.isArray(snippets)) {
    throw new Error("Expected a JSON array of snippets");
  }
  return snippets;
}

function wrappedTsxCandidates(code) {
  return [
    `function __SnippetWrapper__() {\n  return (<>\n${code}\n  </>);\n}`,
    `function __SnippetWrapper__() {\n${code}\n}`,
  ];
}

function validateSnippet(snippet, index) {
  const kindName = snippet.kind || "TS";
  const kind = SCRIPT_KINDS[kindName] || ts.ScriptKind.TS;
  const ext = FILE_EXTENSIONS[kindName] || "ts";
  const fileName = `snippet_${index}.${ext}`;

  const initialErrors = parseSnippet(snippet.code, fileName, kind);
  if (initialErrors.length === 0) {
    return { index, errors: [] };
  }

  if (kindName === "TSX") {
    for (const candidate of wrappedTsxCandidates(snippet.code)) {
      if (parseSnippet(candidate, fileName, kind).length === 0) {
        return { index, errors: [] };
      }
    }
  }

  return { index, errors: initialErrors };
}

function main() {
  const snippets = parseInput();
  const results = snippets.map((snippet, index) => validateSnippet(snippet, index));
  const hasErrors = results.some((entry) => entry.errors.length > 0);
  process.stdout.write(JSON.stringify(results));
  process.exit(hasErrors ? 1 : 0);
}

try {
  main();
} catch (error) {
  const message = error instanceof Error ? error.message : String(error);
  process.stderr.write(`${message}\n`);
  process.exit(1);
}
