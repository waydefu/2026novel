#!/usr/bin/env node
"use strict";

// Deterministic Apps Script receiver contract tests. No Google credentials or
// actual document changes; mock both Docs API batches and the final readback.
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const vm = require("node:vm");

const source = fs.readFileSync(
  path.join(__dirname, "..", "tools", "google_apps_script_sync.gs"), "utf8"
);
const DOC = "1Qg63ffCy3DlLNpmr1mBz-_yjHDgRBY-QbFxRNI5jOt4";
const SECRET = "test-secret";
const chapters = [
  { number: 1, heading: "第一章｜新標題", paragraphs: ["內容甲。", "內容乙。"] },
  { number: 2, heading: "第二章｜新標題", paragraphs: ["內容丙。"] },
];
const clone = value => JSON.parse(JSON.stringify(value));

function makeTab(i, title = "舊標題") {
  return {
    tabProperties: { tabId: "t." + i, title },
    documentTab: { body: { content: [
      { endIndex: 8, paragraph: { elements: [{ textRun: { content: "舊內文。\n" } }] } }
    ] } }
  };
}

function receiver(opts = {}) {
  let state = { tabs: (opts.titles || ["舊一", "舊二"]).map((x, i) => makeTab(i, x)) };
  if (opts.nested) state.tabs[0].childTabs = [makeTab(10, "子分頁")];
  let acquired = false;
  let released = false;
  let batches = 0;
  const sandbox = {
    JSON, Array, String,
    PropertiesService: {
      getScriptProperties: () => ({ getProperty: key => key === "SYNC_SECRET" ? SECRET : null })
    },
    LockService: {
      getScriptLock: () => ({
        tryLock: () => { acquired = !opts.busy; return acquired; },
        hasLock: () => acquired && !released,
        releaseLock: () => { released = true; },
      })
    },
    ContentService: {
      MimeType: { JSON: "application/json" },
      createTextOutput: value => ({
        value, setMimeType() { return this; }, getContent() { return this.value; }
      })
    },
    Docs: { Documents: {
      get: docId => {
        assert.equal(docId, DOC);
        return clone(state);
      },
      batchUpdate: ({ requests }, docId) => {
        assert.equal(docId, DOC);
        batches++;
        const next = clone(state);
        const findTab = id => {
          const tab = next.tabs.find(t => t.tabProperties.tabId === id);
          assert.ok(tab, "tab ID must exist");
          return tab;
        };
        for (const req of requests) {
          if (req.addDocumentTab) {
            const p = req.addDocumentTab.tabProperties;
            next.tabs.splice(p.index, 0, makeTab(p.index, p.title));
          } else if (req.updateDocumentTabProperties) {
            if (opts.throwRename) throw Error("Docs API tab rename failed");
            if (!opts.dropRename) {
              const p = req.updateDocumentTabProperties.tabProperties;
              findTab(p.tabId).tabProperties.title = p.title;
            }
          } else if (req.deleteContentRange) {
            const id = req.deleteContentRange.range.tabId;
            findTab(id).documentTab.body.content = [];
          } else if (req.insertText) {
            const id = req.insertText.location.tabId;
            const text = req.insertText.text + "\n";
            findTab(id).documentTab.body.content = [
              { endIndex: 1 + text.length, paragraph: {
                elements: [{ textRun: { content: text } }]
              } }
            ];
          } else if (req.updateParagraphStyle) {
            // Formatting only; no text changes.
          } else {
            throw Error("Unexpected Docs API operation: " + Object.keys(req)[0]);
          }
        }
        if (opts.truncateBody) {
          next.tabs[0].documentTab.body.content[0].paragraph.elements[0].textRun.content = "內容被截斷\n";
        }
        state = next;
        return { replies: requests.map(() => ({})) };
      }
    } }
  };
  vm.runInNewContext(source, sandbox, { filename: "google_apps_script_sync.gs" });
  return {
    post: (overrides = {}) => JSON.parse(sandbox.doPost({
      postData: { contents: JSON.stringify({
        secret: SECRET, docId: DOC, sourceSha: "abc123", chapters: clone(chapters), ...overrides
      }) }
    }).getContent()),
    tabs: () => state.tabs,
    batches: () => batches,
    released: () => released,
  };
}

function check(name, run) {
  run();
  process.stdout.write("PASS " + name + "\n");
}

check("renames_and_full_content_are_verified", () => {
  const r = receiver({ titles: ["第一章｜舊名", "第二章｜舊名"] });
  const result = r.post();
  assert.equal(result.ok, true);
  assert.equal(result.verified, true);
  assert.equal(result.verifiedChapters, 2);
  assert.equal(result.verifiedTabs, 2);
  assert.equal(result.sourceSha, "abc123");
  assert.deepEqual(r.tabs().map(t => t.tabProperties.title), chapters.map(c => c.heading));
  assert.ok(r.released());
  assert.equal(r.batches(), 1);
});

check("failed_rename_is_a_hard_error_and_body_is_atomic", () => {
  const r = receiver({ throwRename: true });
  const result = r.post();
  assert.equal(result.ok, false);
  assert.match(result.error, /rename failed/);
  assert.equal(r.tabs()[0].documentTab.body.content[0].paragraph.elements[0].textRun.content, "舊內文。\n");
});

check("silent_title_mismatch_is_detected", () => {
  const r = receiver({ dropRename: true });
  const result = r.post();
  assert.equal(result.ok, false);
  assert.match(result.error, /tab_title_mismatch/);
});

check("silent_body_mismatch_is_detected", () => {
  const r = receiver({ truncateBody: true });
  const result = r.post();
  assert.equal(result.ok, false);
  assert.match(result.error, /tab_body_mismatch/);
});

check("extra_tab_is_reserved_and_verified", () => {
  const r = receiver({ titles: ["舊一", "舊二", "舊三"] });
  const result = r.post();
  assert.equal(result.ok, true);
  assert.equal(result.verifiedTabs, 3);
  assert.equal(r.tabs()[2].tabProperties.title, "[預留] 第三章（PLANNED）");
});

check("missing_tab_is_created", () => {
  const r = receiver({ titles: ["舊一"] });
  assert.equal(r.post().ok, true);
  assert.deepEqual(r.tabs().map(t => t.tabProperties.title), chapters.map(c => c.heading));
  assert.equal(r.batches(), 2);
});

check("unauthorized_destination_and_nested_tabs_are_rejected", () => {
  const r = receiver();
  assert.equal(r.post({ secret: "bad" }).error, "unauthorized");
  assert.equal(r.post({ docId: "another-document" }).error, "unexpected_doc_id");
  assert.equal(r.batches(), 0);
  const nested = receiver({ nested: true });
  assert.match(nested.post().error, /unsupported_tab_structure/);
  assert.equal(nested.batches(), 0);
});

check("invalid_chapters_and_lock_contention_fail_closed", () => {
  const invalid = receiver();
  assert.match(invalid.post({ chapters: [{ number: 2, heading: "bad", paragraphs: [] }] }).error, /invalid_chapter/);
  assert.equal(invalid.batches(), 0);
  const busy = receiver({ busy: true });
  assert.equal(busy.post().error, "sync_busy");
  assert.equal(busy.batches(), 0);
});

process.stdout.write("OK google_doc_sync_receiver: 8 tests\n");
