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
  try {
    if (!e || !e.postData || !e.postData.contents) {
      return jsonOut({ ok: false, error: 'missing_body' });
    }
    var payload = JSON.parse(e.postData.contents);
    var expectedSecret = PropertiesService.getScriptProperties().getProperty('SYNC_SECRET');
    if (!expectedSecret || payload.secret !== expectedSecret) {
      return jsonOut({ ok: false, error: 'unauthorized' });
    }

    var docId = payload.docId || DEFAULT_DOC_ID;
    var chapters = payload.chapters || [];
    if (!chapters.length) {
      return jsonOut({ ok: false, error: 'empty_chapters' });
    }
    var reserveExcess = payload.reserveExcessTabs !== false;

    var doc = Docs.Documents.get(docId, { includeTabsContent: true });
    var rootTabs = doc.tabs || [];

    // 第一階段：若章數增加，先補建不足的原生分頁，再重新讀取分頁清單與邊界
    if (chapters.length > rootTabs.length) {
      var addReqs = [];
      for (var i = rootTabs.length; i < chapters.length; i++) {
        addReqs.push({
          addDocumentTab: {
            tabProperties: {
              title: chapters[i].heading,
              index: i
            }
          }
        });
      }
      Docs.Documents.batchUpdate({ requests: addReqs }, docId);
      doc = Docs.Documents.get(docId, { includeTabsContent: true });
      rootTabs = doc.tabs || [];
    }

    var requests = [];
    var renameRequests = [];
    var updated = [];
    var reserved = [];
    var warnings = [];

    for (var idx = 0; idx < chapters.length; idx++) {
      var ch = chapters[idx];
      var tab = rootTabs[idx];
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
        if (rTab.tabProperties.title !== rTitle) {
          renameRequests.push({
            updateDocumentTabProperties: {
              tabProperties: { tabId: rTabId, title: rTitle },
              fields: 'title'
            }
          });
        }
        pushTabOverwriteRequests_(requests, rTab, rTitle, [
          '本分頁保留給後續 [PLANNED] 章節；現行正文已同步至' + curLabel + '。'
        ]);
        reserved.push(rTitle);
      }
    }

    if (requests.length > 0) {
      Docs.Documents.batchUpdate({ requests: requests }, docId);
    }
    if (renameRequests.length > 0) {
      try {
        Docs.Documents.batchUpdate({ requests: renameRequests }, docId);
      } catch (renameErr) {
        warnings.push('tab rename skipped: ' + String(renameErr));
      }
    }

    return jsonOut({
      ok: true,
      docId: docId,
      sourceSha: payload.sourceSha || '',
      updated: updated,
      reserved: reserved,
      warnings: warnings
    });
  } catch (err) {
    return jsonOut({ ok: false, error: String(err) });
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
