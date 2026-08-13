#!/usr/bin/env node
/**
 * Build step for the catalog feeds.
 *
 * Parses every CSV in the repository root and fails when a file is malformed:
 * a row whose field count differs from the header, an unterminated quoted
 * field, or a file that is empty. Exits 0 only when every file is clean.
 */

const fs = require("node:fs");
const path = require("node:path");

const ROOT = path.resolve(__dirname, "..");

/** Parse RFC 4180 style CSV into rows of fields. */
function parse(text) {
  const rows = [];
  let field = "";
  let row = [];
  let quoted = false;

  for (let i = 0; i < text.length; i++) {
    const char = text[i];

    if (quoted) {
      if (char === '"') {
        if (text[i + 1] === '"') {
          field += '"';
          i++;
        } else {
          quoted = false;
        }
      } else {
        field += char;
      }
      continue;
    }

    if (char === '"') {
      quoted = true;
    } else if (char === ",") {
      row.push(field);
      field = "";
    } else if (char === "\n" || char === "\r") {
      if (char === "\r" && text[i + 1] === "\n") i++;
      row.push(field);
      rows.push(row);
      field = "";
      row = [];
    } else {
      field += char;
    }
  }

  if (field !== "" || row.length > 0) {
    row.push(field);
    rows.push(row);
  }

  return { rows, unterminated: quoted };
}

function check(file) {
  const errors = [];
  const text = fs.readFileSync(path.join(ROOT, file), "utf8");

  if (text.trim() === "") {
    errors.push(`${file}: file is empty`);
    return errors;
  }

  const { rows, unterminated } = parse(text);

  if (unterminated) {
    errors.push(`${file}: unterminated quoted field — a '"' is never closed`);
  }

  const header = rows[0];
  const expected = header.length;
  console.log(`  ${file}: ${rows.length - 1} rows, ${expected} columns`);

  rows.slice(1).forEach((row, index) => {
    // Trailing newline produces one empty final row; ignore it.
    if (row.length === 1 && row[0] === "") return;
    if (row.length !== expected) {
      errors.push(
        `${file}:${index + 2}: has ${row.length} fields, expected ${expected}` +
          ` — an unescaped comma or line break is the usual cause`
      );
    }
  });

  return errors;
}

function main() {
  const files = fs
    .readdirSync(ROOT)
    .filter((name) => name.toLowerCase().endsWith(".csv"))
    .sort();

  if (files.length === 0) {
    console.error("No CSV files found to build.");
    process.exit(1);
  }

  console.log(`Validating ${files.length} CSV file(s):`);
  const errors = files.flatMap(check);

  if (errors.length > 0) {
    console.error(`\nBuild failed with ${errors.length} error(s):\n`);
    for (const error of errors) console.error(`  ${error}`);
    process.exit(1);
  }

  console.log("\nBuild succeeded. All CSV files are well formed.");
}

main();
