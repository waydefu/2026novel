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

function indexedBody(value) {
  // Match Docs' UTF-16 ranges, including the mandatory initial section break.
  let index = 1;
  const content = [{ endIndex: 1, sectionBreak: {} }];
  for (const line of value.match(/[^\n]*\n|[^\n]+$/g) || []) {
    const startIndex = index;
    index += line.length;
    content.push({ startIndex, endIndex: index, paragraph: {
      elements: [{ startIndex, endIndex: index, textRun: { content: line } }]
    } });
  }
  return content;
}
function bodyText(tab) {
  return tab.documentTab.body.content
    .flatMap(x => (x.paragraph?.elements || []).map(y => y.textRun?.content || "")).join("");
}
function makeTab(i, title = "舊標題") {
  return {
    tabProperties: { tabId: "t.mockid" + i + "x9", title },
    documentTab: { body: { content: indexedBody("舊內文。\n") } }
  };
}

function receiver(opts = {}) {
  let state = { revisionId: "revision-1", tabs: (opts.titles || ["舊一", "舊二"]).map((x, i) => makeTab(i, x)) };
  if (opts.contents) {
    state.tabs.forEach((t, i) => {
      if (opts.contents[i] !== undefined) {
        const value = opts.contents[i] + "\n";
        t.documentTab.body.content = indexedBody(value);
      }
    });
  }
  if (opts.middleSection) state.tabs[0].documentTab.body.content.splice(2, 0, { startIndex: 6, endIndex: 7, sectionBreak: {} });
  if (opts.badIndex) state.tabs[0].documentTab.body.content[1].paragraph.elements[0].startIndex++;
  if (opts.nested) state.tabs[0].childTabs = [makeTab(10, "子分頁")];
  let acquired = false;
  let released = false;
  let batches = 0;
  const history = [];
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
      batchUpdate: ({ requests, writeControl }, docId) => {
        assert.equal(docId, DOC);
        batches++;
        history.push(clone(requests));
        assert.equal(writeControl?.requiredRevisionId, state.revisionId,
          "writes must be guarded by the observed revision");
        if (opts.concurrentBeforeBatch) throw Error("revision conflict: collaborator wrote first");
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
          } else if (req.deleteContentRange || req.insertText) {
            const id = req.deleteContentRange?.range.tabId || req.insertText.location.tabId;
            const tab = findTab(id);
            const before = tab.documentTab.body.content
              .flatMap(x => (x.paragraph?.elements || []).map(y => y.textRun?.content || "")).join("");
            let after;
            if (req.deleteContentRange) {
              const start = req.deleteContentRange.range.startIndex - 1;
              const end = req.deleteContentRange.range.endIndex - 1;
              assert.ok(start >= 0 && end <= before.length - 1, "must not delete final newline");
              assert.ok(end > start, "non-empty deletion");
              after = before.slice(0, start) + before.slice(end);
            } else {
              const index = req.insertText.location.index - 1;
              assert.ok(index >= 0 && index < before.length, "insert before final newline");
              after = before.slice(0, index) + req.insertText.text + before.slice(index);
            }
            tab.documentTab.body.content = indexedBody(after);
          } else if (req.updateParagraphStyle) {
            // Formatting only; no text changes.
          } else {
            throw Error("Unexpected Docs API operation: " + Object.keys(req)[0]);
          }
        }
        if (opts.truncateBody) {
          next.tabs[0].documentTab.body.content = indexedBody("內容被截斷\n");
        }
        next.revisionId = "revision-" + (Number(state.revisionId.split("-")[1]) + 1);
        state = next;
        const appliedRevision = state.revisionId;
        if (opts.concurrentAfterCreation && requests.some(q => q.addDocumentTab)) {
          state.revisionId = "revision-99";
        }
        return { replies: requests.map(() => ({})), writeControl: { requiredRevisionId: appliedRevision } };
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
    requests: () => history,
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

check("unchanged_chapters_are_not_rewritten", () => {
  const original = chapters.map(c => c.heading + "\n\n" + c.paragraphs.join("\n\n"));
  const r = receiver({ titles: chapters.map(c => c.heading), contents: original });
  const result = r.post();
  assert.equal(result.ok, true);
  assert.equal(r.batches(), 0);
  assert.equal(result.unchangedContent.length, 2);
});

check("localized_edit_does_not_replace_whole_chapter", () => {
  const original = chapters.map(c => c.heading + "\n\n" + c.paragraphs.join("\n\n"));
  const slightlyWrong = original.slice();
  slightlyWrong[0] = slightlyWrong[0].replace("內容乙。", "內容異。");
  const r = receiver({ titles: chapters.map(c => c.heading), contents: slightlyWrong });
  const result = r.post();
  assert.equal(result.ok, true);
  assert.equal(r.batches(), 1);
  assert.equal(result.unchangedContent.length, 1);
  const changed = r.requests()[0];
  const del = changed.filter(q => q.deleteContentRange);
  const ins = changed.filter(q => q.insertText);
  assert.equal(del.length, 1);
  assert.equal(ins.length, 1);
  assert.equal(del[0].deleteContentRange.range.endIndex - del[0].deleteContentRange.range.startIndex, 1,
    "single-character typo must not cause whole-chapter deletion");
  assert.equal(ins[0].insertText.text.length, 1);
  assert.equal(bodyText(r.tabs()[0]).trim(), original[0]);
});

check("utf16_surrogate_pairs_remain_intact", () => {
  const original = chapters.map(c => c.heading + "\n\n" + c.paragraphs.join("\n\n"));
  const before = original.slice();
  before[0] = original[0] + "🚀";
  const r = receiver({ titles: chapters.map(c => c.heading), contents: before });
  // The old trailing emoji is deleted as a complete surrogate pair.
  const res = r.post();
  assert.equal(res.ok, true);
  const deletes = r.requests().flat().filter(q => q.deleteContentRange);
  assert.equal(deletes.length, 1);
  assert.equal(deletes[0].deleteContentRange.range.endIndex -
    deletes[0].deleteContentRange.range.startIndex, 2);
  assert.equal(bodyText(r.tabs()[0]).trim(), original[0]);
});

check("revision_conflict_blocks_all_writes", () => {
  const r = receiver({ concurrentBeforeBatch: true });
  assert.equal(r.post().ok, false);
  assert.equal(r.batches(), 1);
  assert.ok(r.released());
});

check("failed_rename_is_a_hard_error_and_body_is_atomic", () => {
  const r = receiver({ throwRename: true });
  const result = r.post();
  assert.equal(result.ok, false);
  assert.match(result.error, /rename failed/);
  assert.equal(bodyText(r.tabs()[0]), "舊內文。\n");
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

check("middle_section_break_rejected_before_any_write", () => {
  const r = receiver({ titles: ["舊一"], middleSection: true });
  assert.match(r.post().error, /unsupported_section_break/);
  assert.equal(r.batches(), 0);
  assert.ok(r.released());
});
check("malformed_utf16_index_rejected_before_any_write", () => {
  const r = receiver({ badIndex: true });
  assert.match(r.post().error, /tab_element_index_mismatch/);
  assert.equal(r.batches(), 0);
});
check("extra_trailing_newlines_are_removed", () => {
  const original = chapters.map(c => c.heading + "\n\n" + c.paragraphs.join("\n\n"));
  const r = receiver({ titles: chapters.map(c => c.heading), contents: [original[0] + "\n\n", original[1]] });
  assert.equal(r.post().ok, true);
  assert.equal(bodyText(r.tabs()[0]), original[0] + "\n");
});
check("shared_surrogate_halves_are_not_split", () => {
  for (const [before, after] of [["🚀", "🚁"], ["\u{10000}", "\u{10400}"]]) {
    const desired = clone(chapters);
    desired[0].paragraphs[0] += after;
    const original = desired.map(c => c.heading + "\n\n" + c.paragraphs.join("\n\n"));
    const r = receiver({ titles: desired.map(c => c.heading), contents: [original[0].replace(after, before), original[1]] });
    assert.equal(r.post({chapters: desired}).ok, true);
    const del = r.requests().flat().find(q => q.deleteContentRange).deleteContentRange.range;
    assert.equal(del.endIndex - del.startIndex, 2);
    assert.equal(bodyText(r.tabs()[0]), original[0] + "\n");
  }
});
check("collaborator_change_between_creation_and_content_is_rejected", () => {
  const r = receiver({ titles: ["舊一"], concurrentAfterCreation: true });
  assert.match(r.post().error, /revision_changed_after_tab_creation/);
  assert.equal(r.batches(), 1, "only the tab creation batch may have applied");
  assert.equal(bodyText(r.tabs()[0]), "舊內文。\n");
  assert.ok(r.released());
});
process.stdout.write("OK google_doc_sync_receiver: 17 tests\n");
