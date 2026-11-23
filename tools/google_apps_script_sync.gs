/**
 * 《2026西幻小說》GitHub Actions → Google 文件原生分頁（Tabs）單向同步接收器
 *
 * 安裝步驟：
 * 1. 開啟目標 Google 文件 → 上方選單「擴充功能」→「Apps Script」。
 * 2. 將本檔完整貼入編輯器取代原有內容。
 * 3. 左側「服務 +」→ 新增「Google Docs API」（識別碼保持 `Docs`）。
 * 4. 左側齒輪「專案設定」→「指令碼屬性」新增 `SYNC_SECRET`（填入自訂長隨機字串）。
 * 5. 右上角「部署」→「新增部署」→ 類型選「網頁應用程式」：
 *    - 執行身分：「我（文件擁有者）」
 *    - 誰可以存取：「所有人」（實際請求由 SYNC_SECRET 驗證保護）
 * 6. 將產生的 Web App URL 與 SYNC_SECRET 分別存為 GitHub Actions Secrets：
 *    - GDOC_WEBHOOK_URL
 *    - GDOC_WEBHOOK_SECRET
 */

var DEFAULT_DOC_ID = '1Qg63ffCy3DlLNpmr1mBz-_yjHDgRBY-QbFxRNI5jOt4';

function doPost(e) {
  var lock = null;
  try {
    if (!e || !e.postData || !e.postData.contents) {
      return jsonOut({ ok: false, error: 'missing_body' });
    }
    var payload = JSON.parse(e.postData.contents);
    var expectedSecret = PropertiesService.getScriptProperties().getProperty('SYNC_SECRET');
    if (!expectedSecret || payload.secret !== expectedSecret) {
      return jsonOut({ ok: false, error: 'unauthorized' });
    }

    // Never let a caller choose a different Google Doc, even with a valid secret.
    if (payload.docId && payload.docId !== DEFAULT_DOC_ID) {
      return jsonOut({ ok: false, error: 'unexpected_doc_id' });
    }
    var docId = DEFAULT_DOC_ID;
    var chapters = payload.chapters;
    validateChapters_(chapters);
    var reserveExcess = payload.reserveExcessTabs !== false;

    // Serialize all sync requests for this deployment so their writes cannot overlap.
    lock = LockService.getScriptLock();
    if (!lock.tryLock(30000)) {
      return jsonOut({ ok: false, error: 'sync_busy' });
    }

    var doc = Docs.Documents.get(docId, { includeTabsContent: true });
    var rootTabs = getRootTabs_(doc);

    // Add missing tabs, then re-read IDs; never change old tab IDs or delete tabs.
    if (chapters.length > rootTabs.length) {
      var addReqs = [];
      for (var i = rootTabs.length; i < chapters.length; i++) {
        addReqs.push({
          addDocumentTab: { tabProperties: { title: chapters[i].heading, index: i } }
        });
      }
      Docs.Documents.batchUpdate({ requests: addReqs }, docId);
      doc = Docs.Documents.get(docId, { includeTabsContent: true });
      rootTabs = getRootTabs_(doc);
    }

    var requests = [];
    var renameRequests = [];
    var expectedTabs = [];
    var updated = [];
    var reserved = [];

    for (var idx = 0; idx < chapters.length; idx++) {
      var ch = chapters[idx];
      var tab = rootTabs[idx];
      if (!tab) {
        throw new Error('missing_tab_' + (idx + 1));
      }
      var tabId = tab.tabProperties.tabId;
      if (tab.tabProperties.title !== ch.heading) {
        renameRequests.push({
          updateDocumentTabProperties: {
            tabProperties: { tabId: tabId, title: ch.heading },
            fields: 'title'
          }
        });
      }
      pushTabOverwriteRequests_(requests, tab, ch.heading, ch.paragraphs);
      expectedTabs.push({
        id: tabId, title: ch.heading,
        text: ch.heading + '\n\n' + ch.paragraphs.join('\n\n')
      });
      updated.push(ch.heading);
    }

    if (reserveExcess && rootTabs.length > chapters.length) {
      var cnNums = ['', '一', '二', '三', '四', '五', '六', '七', '八', '九', '十'];
      for (var rIdx = chapters.length; rIdx < rootTabs.length; rIdx++) {
        var rTab = rootTabs[rIdx];
        var rTabId = rTab.tabProperties.tabId;
        var label = (rIdx + 1 < cnNums.length) ? ('第' + cnNums[rIdx + 1] + '章') : ('第' + (rIdx + 1) + '章');
        var curLabel = (chapters.length < cnNums.length) ? ('第' + cnNums[chapters.length] + '章') : ('第' + chapters.length + '章');
        var rTitle = '[預留] ' + label + '（PLANNED）';
        var rParagraph = '本分頁保留給後續 [PLANNED] 章節；現行正文已同步至' + curLabel + '。';
        if (rTab.tabProperties.title !== rTitle) {
          renameRequests.push({
            updateDocumentTabProperties: {
              tabProperties: { tabId: rTabId, title: rTitle },
              fields: 'title'
            }
          });
        }
        pushTabOverwriteRequests_(requests, rTab, rTitle, [rParagraph]);
        expectedTabs.push({ id: rTabId, title: rTitle, text: rTitle + '\n\n' + rParagraph });
        reserved.push(rTitle);
      }
    }

    // Content and tab titles must succeed together. Never swallow rename failures.
    // This also means a failed title update cannot leave a newly published body.
    Docs.Documents.batchUpdate({ requests: requests.concat(renameRequests) }, docId);

    // A successful API call is not publication evidence. Read back every tab.
    var after = Docs.Documents.get(docId, { includeTabsContent: true });
    verifyTabs_(getRootTabs_(after), expectedTabs);

    return jsonOut({
      ok: true,
      verified: true,
      verifiedChapters: chapters.length,
      verifiedTabs: expectedTabs.length,
      docId: docId,
      sourceSha: payload.sourceSha || '',
      updated: updated,
      reserved: reserved,
      warnings: []
    });
  } catch (err) {
    return jsonOut({ ok: false, error: String(err) });
  } finally {
    if (lock && lock.hasLock()) {
      lock.releaseLock();
    }
  }
}

function validateChapters_(chapters) {
  if (!Array.isArray(chapters) || chapters.length === 0) {
    throw new Error('empty_chapters');
  }
  for (var i = 0; i < chapters.length; i++) {
    var ch = chapters[i];
    if (!ch || ch.number !== i + 1 || typeof ch.heading !== 'string' ||
        !ch.heading.trim() || !Array.isArray(ch.paragraphs) || ch.paragraphs.length === 0) {
      throw new Error('invalid_chapter_' + (i + 1));
    }
    for (var j = 0; j < ch.paragraphs.length; j++) {
      if (typeof ch.paragraphs[j] !== 'string' || !ch.paragraphs[j].trim()) {
        throw new Error('invalid_paragraph_' + (i + 1));
      }
    }
  }
}

function getRootTabs_(doc) {
  if (!doc || !Array.isArray(doc.tabs) || doc.tabs.length === 0) {
    throw new Error('missing_document_tabs');
  }
  for (var i = 0; i < doc.tabs.length; i++) {
    if (!doc.tabs[i].tabProperties || !doc.tabs[i].tabProperties.tabId ||
        (doc.tabs[i].childTabs && doc.tabs[i].childTabs.length)) {
      throw new Error('unsupported_tab_structure_' + (i + 1));
    }
  }
  return doc.tabs;
}

function getTabText_(tab) {
  var body = tab.documentTab && tab.documentTab.body;
  if (!body || !Array.isArray(body.content)) {
    throw new Error('missing_tab_body');
  }
  var text = '';
  for (var i = 0; i < body.content.length; i++) {
    var item = body.content[i];
    if (item.sectionBreak) continue;
    if (!item.paragraph || !Array.isArray(item.paragraph.elements)) {
      throw new Error('unsupported_tab_content');
    }
    for (var j = 0; j < item.paragraph.elements.length; j++) {
      var run = item.paragraph.elements[j].textRun;
      if (!run || typeof run.content !== 'string') {
        throw new Error('unsupported_tab_element');
      }
      text += run.content;
    }
  }
  return text.replace(/\n+$/, '');
}

function verifyTabs_(tabs, expectedTabs) {
  if (tabs.length < expectedTabs.length) {
    throw new Error('tab_count_mismatch');
  }
  for (var i = 0; i < expectedTabs.length; i++) {
    var expected = expectedTabs[i];
    var actual = tabs[i];
    if (actual.tabProperties.tabId !== expected.id ||
        actual.tabProperties.title !== expected.title) {
      throw new Error('tab_title_mismatch_' + (i + 1));
    }
    if (getTabText_(actual) !== expected.text.replace(/\n+$/, '')) {
      throw new Error('tab_body_mismatch_' + (i + 1));
    }
  }
}

function pushTabOverwriteRequests_(requests, tab, heading, paragraphs) {
  var tabId = tab.tabProperties.tabId;
  var content = (tab.documentTab && tab.documentTab.body && tab.documentTab.body.content) || [];
  var endIndex = content.length ? content[content.length - 1].endIndex : 1;

  if (endIndex > 2) {
    requests.push({
      deleteContentRange: {
        range: {
          tabId: tabId,
          startIndex: 1,
          endIndex: endIndex - 1
        }
      }
    });
  }

  var joinedBody = paragraphs.join('\n\n');
  var fullText = heading + '\n\n' + joinedBody;
  requests.push({
    insertText: {
      location: { tabId: tabId, index: 1 },
      text: fullText
    }
  });

  // JavaScript String length matches UTF-16 code units used by Google Docs API
  requests.push({
    updateParagraphStyle: {
      range: {
        tabId: tabId,
        startIndex: 1,
        endIndex: 1 + heading.length + 1
      },
      paragraphStyle: { namedStyleType: 'HEADING_2' },
      fields: 'namedStyleType'
    }
  });

  if (joinedBody.length > 0) {
    requests.push({
      updateParagraphStyle: {
        range: {
          tabId: tabId,
          startIndex: 1 + heading.length + 1,
          endIndex: 1 + fullText.length
        },
        paragraphStyle: { namedStyleType: 'NORMAL_TEXT' },
        fields: 'namedStyleType'
      }
    });
  }
}

function jsonOut(obj) {
  return ContentService.createTextOutput(JSON.stringify(obj))
    .setMimeType(ContentService.MimeType.JSON);
}
