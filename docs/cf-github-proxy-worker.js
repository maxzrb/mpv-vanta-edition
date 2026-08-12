/**
 * ============================================================
 *  AerithDream 下载加速（Cloudflare Worker）
 * ============================================================
 *  基于 hubporg/CF-GitHub-Proxy 定制（MIT License）
 *    https://github.com/hubporg/CF-GitHub-Proxy
 *
 *  功能：
 *    - 代理 maxzrb 用户名下所有仓库的 Release/Archive 下载（白名单 + 流式透传 + Range 断点续传）
 *    - 自动列表页：/ 渲染暗色下载站前端，JS 拉取 /api/latest 自动列出最新 Release 资产
 *    - /api/latest：后端拉 GitHub API 并缓存 10 分钟（可选 GITHUB_TOKEN 环境变量提升配额）
 * ============================================================
 */

'use strict'

// ==================== 配置区 ====================
// 允许代理的 GitHub 用户名（小写；该用户名下所有仓库的 Release / Archive 均可代理）
const ALLOWED_OWNERS = [
    'maxzrb',
]

// 列表页默认展示的仓库（小写）
const LIST_REPO = 'maxzrb/mpv-vanta-edition'
const LIST_REPO_URL = 'https://github.com/' + LIST_REPO

// true  = 仅允许 release/archive 下载（纯下载站，推荐）
// false = 额外允许 blob/raw 等仓库文件代理（相当于整仓镜像）
const DOWNLOAD_ONLY = true

// 可选：GitHub API Token（提升 API 配额；在 Worker 设置环境变量 GITHUB_TOKEN 注入）
const GITHUB_TOKEN = globalThis.GITHUB_TOKEN || ''

// API 响应缓存 TTL（秒）
const API_CACHE_TTL = 600

// ==================== 前端页面 ====================
// 注意：页面内联 JS 不使用反引号，避免与外层模板字符串冲突
const LANDING_HTML = `<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="description" content="AerithDream 的下载加速 - GitHub Release 加速代理">
<title>AerithDream的下载加速</title>
<style>
  :root {
    --bg0: #f4f7fb; --bg1: #eef2f8; --card: #ffffff;
    --line: #e3e9f2; --line2: #d3dce8;
    --brand: #56e5f1; --brand-deep: #0e9cb5; --brand-dim: rgba(14,156,181,0.08);
    --text: #1d2937; --muted: #64748b; --accent: #d97706;
    --danger: #dc2626; --ok: #16a34a;
    --radius: 14px; --shadow: 0 10px 30px rgba(35,55,90,.08);
  }
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body {
    font-family: "HarmonyOS Sans SC", "PingFang SC", "Microsoft YaHei", system-ui, -apple-system, sans-serif;
    background: radial-gradient(1200px 600px at 15% -10%, #e1f4f8 0%, transparent 55%),
                radial-gradient(900px 500px at 110% 0%, #e8f1f8 0%, transparent 50%), var(--bg0);
    color: var(--text); line-height: 1.6; min-height: 100vh;
  }
  .wrap { max-width: 900px; margin: 0 auto; padding: 28px 20px 60px; }
  header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 34px; }
  .logo { display: flex; align-items: center; gap: 10px; font-weight: 700; font-size: 18px; letter-spacing: .3px; }
  .logo .dot { width: 12px; height: 12px; border-radius: 4px; background: var(--brand); box-shadow: 0 0 14px var(--brand); }
  .logo small { color: var(--muted); font-weight: 400; font-size: 12px; margin-left: 2px; }
  .gh-link { color: var(--muted); text-decoration: none; font-size: 13px; border: 1px solid var(--line); padding: 7px 12px; border-radius: 999px; transition: .2s; }
  .gh-link:hover { color: var(--brand-deep); border-color: var(--brand-deep); }
  .hero { margin-bottom: 30px; }
  .hero h1 { font-size: 30px; font-weight: 700; letter-spacing: .5px; }
  .hero h1 em { font-style: normal; color: var(--brand-deep); }
  .hero p { color: var(--muted); margin-top: 8px; font-size: 14px; max-width: 620px; }
  .badge { display: inline-flex; align-items: center; gap: 6px; background: var(--brand-dim); color: var(--brand-deep);
           border: 1px solid rgba(14,156,181,.35); border-radius: 999px; padding: 3px 12px; font-size: 12px; margin-top: 14px; }
  .card { background: var(--card); border: 1px solid var(--line); border-radius: var(--radius); box-shadow: var(--shadow); overflow: hidden; }
  .card-head { display: flex; align-items: center; justify-content: space-between; padding: 16px 20px; border-bottom: 1px solid var(--line); flex-wrap: wrap; gap: 8px; }
  .card-head .title { font-size: 15px; font-weight: 600; display: flex; align-items: center; gap: 8px; }
  .card-head .title .v { color: var(--brand-deep); }
  .card-head .date { color: var(--muted); font-size: 12px; }
  .asset { display: flex; align-items: center; gap: 14px; padding: 14px 20px; border-bottom: 1px solid rgba(227,233,242,.9); transition: background .15s; }
  .asset:last-child { border-bottom: none; }
  .asset:hover { background: rgba(14,156,181,.06); }
  .ic { flex: 0 0 40px; height: 40px; border-radius: 10px; display: flex; align-items: center; justify-content: center;
        font-size: 11px; font-weight: 700; letter-spacing: .5px; color: var(--brand-deep);
        background: var(--brand-dim); border: 1px solid rgba(14,156,181,.25); }
  .asset .meta { flex: 1; min-width: 0; }
  .asset .name { font-size: 13.5px; font-weight: 500; word-break: break-all; }
  .asset .size { color: var(--muted); font-size: 12px; margin-top: 2px; }
  .asset .actions { display: flex; gap: 8px; flex: 0 0 auto; }
  .btn { border: 0; border-radius: 8px; padding: 8px 14px; font-size: 13px; font-weight: 600; cursor: pointer;
         text-decoration: none; display: inline-flex; align-items: center; gap: 6px; transition: .15s; font-family: inherit; }
  .btn-primary { background: var(--brand); color: #06323a; }
  .btn-primary:hover { filter: brightness(1.08); box-shadow: 0 0 18px rgba(86,229,241,.4); }
  .btn-ghost { background: transparent; color: var(--muted); border: 1px solid var(--line2); }
  .btn-ghost:hover { color: var(--brand-deep); border-color: var(--brand-deep); }
  .tag { font-size: 10px; border-radius: 6px; padding: 2px 7px; margin-left: 8px; vertical-align: 1px; font-weight: 600; }
  .tag-inst { background: rgba(255,179,71,.15); color: var(--accent); border: 1px solid rgba(255,179,71,.4); }
  .tag-opt { background: rgba(47,208,143,.12); color: var(--ok); border: 1px solid rgba(47,208,143,.35); }
  .status { padding: 14px 20px; color: var(--muted); font-size: 13px; text-align: center; }
  .status .err { color: var(--danger); }
  .grid2 { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; margin-top: 24px; }
  .panel { background: var(--card); border: 1px solid var(--line); border-radius: var(--radius); padding: 18px 20px; }
  .panel h3 { font-size: 14px; margin-bottom: 12px; color: var(--text); display: flex; align-items: center; gap: 8px; }
  .panel h3 .bar { width: 4px; height: 14px; border-radius: 2px; background: var(--brand); }
  .order { list-style: none; display: flex; flex-direction: column; gap: 8px; }
  .order li { font-size: 12.5px; color: var(--muted); display: flex; gap: 8px; align-items: baseline; }
  .order b { color: var(--text); font-weight: 600; white-space: nowrap; }
  .order .req { color: var(--accent); font-size: 11px; }
  .note { font-size: 12.5px; color: var(--muted); margin-top: 10px; line-height: 1.8; }
  .note code { background: #eef3f8; border: 1px solid var(--line); border-radius: 6px; padding: 1px 6px; font-size: 11.5px; word-break: break-all; color: var(--brand-deep); }
  footer { margin-top: 36px; text-align: center; color: #94a3b8; font-size: 12px; }
  footer a { color: #64748b; text-decoration: none; }
  footer a:hover { color: var(--brand-deep); }
  @media (max-width: 640px) {
    .hero h1 { font-size: 24px; }
    .asset { flex-wrap: wrap; }
    .asset .actions { width: 100%; }
    .asset .actions .btn { flex: 1; justify-content: center; }
    .grid2 { grid-template-columns: 1fr; }
    header { flex-direction: column; gap: 12px; align-items: flex-start; }
  }
</style>
</head>
<body>
<div class="wrap">
  <header>
    <div class="logo"><span class="dot"></span>AerithDream<small>的下载加速</small></div>
    <a class="gh-link" href="${LIST_REPO_URL}" target="_blank" rel="noopener">GitHub ↗</a>
  </header>

  <div class="hero">
    <h1>下载 <em>MPV Vanta Edition</em></h1>
    <p>GitHub Release 加速代理 · 流式转发 · 支持多线程与断点续传。资产列表自动同步，点击即可通过加速通道下载。</p>
    <span class="badge" id="badge">加载版本中…</span>
  </div>

  <div class="card" id="releaseCard">
    <div class="card-head">
      <div class="title" id="releaseTitle">最新 Release</div>
      <div class="date" id="releaseDate"></div>
    </div>
    <div class="status" id="releaseBody">正在从 GitHub 获取最新 Release…</div>
  </div>

  <div class="grid2">
    <div class="panel">
      <h3><span class="bar"></span>安装与覆盖顺序</h3>
      <ul class="order">
        <li><b>01</b><span>Base 基础包（含随包 ffmpeg，必须）</span></li>
        <li><b>02</b><span>Extras 扩展包（.001 + .002 放同目录解压）</span></li>
        <li><b>03</b><span>Faster-Whisper AI 字幕 <em class="req">可选</em></span></li>
        <li><b>04</b><span>LSFG 补帧扩展 <em class="req">可选</em></span></li>
        <li><b>05</b><span>Config 个人配置（最后安装覆盖）</span></li>
      </ul>
      <div class="note">按文件名前缀从小到大依次解压覆盖到同一目录即可。</div>
    </div>
    <div class="panel">
      <h3><span class="bar"></span>加速使用说明</h3>
      <div class="note">
        任意 GitHub 下载链接前拼上本域名前缀即可加速：<br>
        <code id="sampleLink">https://dl.loliland.cn/https://github.com/…/releases/download/…</code><br>
        也支持 git clone 与 archive 源码包。
      </div>
    </div>
  </div>

  <footer>
    <a href="${LIST_REPO_URL}/releases" target="_blank" rel="noopener">查看 GitHub Releases</a> ·
    由 Cloudflare Workers 提供边缘加速 · <span id="footerVer"></span>
  </footer>
</div>

<script>
(function () {
  var repo = '${LIST_REPO}';
  var fmtSize = function (b) {
    if (!b && b !== 0) return '';
    if (b >= 1073741824) return (b / 1073741824).toFixed(2) + ' GB';
    if (b >= 1048576) return (b / 1048576).toFixed(1) + ' MB';
    if (b >= 1024) return (b / 1024).toFixed(0) + ' KB';
    return b + ' B';
  };
  var badgeFor = function (name) {
    var n = name.toLowerCase();
    if (n.indexOf('installer') >= 0 || n.endsWith('.exe')) return 'EXE';
    if (n.indexOf('lsfg') >= 0) return 'LSF';
    if (n.indexOf('whisper') >= 0) return 'AI';
    if (n.indexOf('config') >= 0) return 'CFG';
    if (n.indexOf('base') >= 0) return 'APP';
    var m = n.match(/\.([a-z0-9]{1,4})$/);
    if (m) return m[1].toUpperCase();
    return 'FILE';
  };
  var tagFor = function (name) {
    var n = name.toLowerCase();
    if (n.indexOf('installer') >= 0) return '<span class="tag tag-inst">安装器</span>';
    if (n.indexOf('fasterwhisper') >= 0 || n.indexOf('lsfg') >= 0) return '<span class="tag tag-opt">可选</span>';
    return '';
  };
  var sortKey = function (name) {
    var n = name.toLowerCase();
    if (n.indexOf('installer') >= 0) return 0;
    var m = n.match(/(\d\d)-/);
    if (m) return parseInt(m[1], 10) * 10 + (n.indexOf('.001') >= 0 ? 0 : 1);
    return 99;
  };
  var esc = function (s) { return s.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;'); };

  var card = document.getElementById('releaseCard');
  var body = document.getElementById('releaseBody');
  var title = document.getElementById('releaseTitle');
  var date = document.getElementById('releaseDate');
  var badge = document.getElementById('badge');
  var footerVer = document.getElementById('footerVer');

  function render(release) {
    badge.innerHTML = '最新版本 <b style="color:var(--brand-deep)">' + esc(release.tag_name) + '</b>';
    title.innerHTML = '最新 Release <span class="v">' + esc(release.tag_name) + '</span>';
    if (release.published_at) {
      var d = new Date(release.published_at);
      date.textContent = '发布于 ' + d.toLocaleDateString('zh-CN') + ' ' + d.toLocaleTimeString('zh-CN', {hour:'2-digit', minute:'2-digit'});
    }
    footerVer.textContent = release.tag_name;
    var list = release.assets.slice().sort(function (a, b) { return sortKey(a.name) - sortKey(b.name); });
    if (!list.length) {
      body.innerHTML = '<span class="err">该版本暂无资产。</span>';
      return;
    }
    var rows = list.map(function (a) {
      var url = 'https://dl.loliland.cn/' + a.browser_download_url;
      var row = document.createElement('div');
      row.className = 'asset';
      row.innerHTML =
        '<div class="ic">' + badgeFor(a.name) + '</div>' +
        '<div class="meta"><div class="name">' + esc(a.name) + tagFor(a.name) + '</div>' +
        '<div class="size">' + fmtSize(a.size) + '</div></div>' +
        '<div class="actions">' +
        '<a class="btn btn-primary" href="' + esc(url) + '" download>下载</a>' +
        '<button class="btn btn-ghost" type="button" data-url="' + esc(url) + '">复制</button>' +
        '</div>';
      return row;
    });
    body.innerHTML = '';
    rows.forEach(function (r) { body.appendChild(r); });
    body.querySelectorAll('button[data-url]').forEach(function (btn) {
      btn.addEventListener('click', function () {
        var url = btn.getAttribute('data-url');
        if (navigator.clipboard && navigator.clipboard.writeText) {
          navigator.clipboard.writeText(url).then(function () {
            var old = btn.textContent; btn.textContent = '已复制';
            setTimeout(function () { btn.textContent = old; }, 1500);
          });
        } else {
          var ta = document.createElement('textarea');
          ta.value = url; document.body.appendChild(ta); ta.select();
          document.execCommand('copy'); document.body.removeChild(ta);
          var old = btn.textContent; btn.textContent = '已复制';
          setTimeout(function () { btn.textContent = old; }, 1500);
        }
      });
    });
  }

  fetch('/api/latest?repo=' + encodeURIComponent(repo))
    .then(function (r) { if (!r.ok) throw new Error('HTTP ' + r.status); return r.json(); })
    .then(function (data) { render(data); })
    .catch(function (e) {
      badge.innerHTML = '版本获取失败';
      body.innerHTML = '<span class="err">暂时无法连接 GitHub API（可能限流）。请直接访问 ' +
        '<a style="color:var(--brand-deep)" href="' + esc(LIST_REPO_URL) + '/releases" target="_blank">GitHub Releases</a> 页面获取下载链接。</span>';
    });
})();
</script>
</body>
</html>`

// ==================== 代理逻辑 ====================
const PREFLIGHT_INIT = {
    status: 204,
    headers: new Headers({
        'access-control-allow-origin': '*',
        'access-control-allow-methods': 'GET,POST,PUT,PATCH,TRACE,DELETE,HEAD,OPTIONS',
        'access-control-max-age': '1728000',
    }),
}

const RELEASE_RE = /^(?:https?:\/\/)?github\.com\/.+?\/.+?\/(?:releases\/download|archive)\/.*$/i
const FILE_RE = /^(?:https?:\/\/)?github\.com\/.+?\/.+?\/(?:blob|raw)\/.*$/i
const RAW_RE = /^(?:https?:\/\/)?raw\.(?:githubusercontent|github)\.com\/.+?\/.+?\/.+?\/.+$/i
const GIST_RE = /^(?:https?:\/\/)?gist\.(?:githubusercontent|github)\.com\/.+?\/.+?\/.+$/i

function makeRes(body, status = 200, headers = {}) {
    headers['access-control-allow-origin'] = '*'
    headers['access-control-expose-headers'] = '*'
    return new Response(body, { status, headers })
}

addEventListener('fetch', e => {
    const ret = fetchHandler(e).catch(err => makeRes('worker error:\n' + err.stack, 502))
    e.respondWith(ret)
})

function isAllowedOwner(target) {
    const lower = target.toLowerCase()
    return ALLOWED_OWNERS.some(owner =>
        lower.startsWith('https://github.com/' + owner + '/')
    )
}

async function fetchHandler(e) {
    const req = e.request
    const urlObj = new URL(req.url)
    const path = urlObj.href.substr(urlObj.origin.length)

    // 根路径：渲染下载站前端
    if (path === '/' || path === '') {
        return makeRes(LANDING_HTML, 200, { 'content-type': 'text/html; charset=utf-8' })
    }

    // /api/latest：返回最新 Release 精简 JSON（带 10 分钟缓存）
    if (path.startsWith('/api/latest')) {
        return apiLatest(urlObj)
    }

    // 兼容 ?q= 形式
    const q = urlObj.searchParams.get('q')
    if (q) {
        return Response.redirect(urlObj.origin + '/' + q, 301)
    }

    let target = path.replace(/^\/+/, '').replace(/^https?:\/+/, 'https://')
    if (!/^https?:\/\//i.test(target)) {
        return makeRes('仅支持 GitHub 下载路径。', 400)
    }

    let matched = RELEASE_RE.test(target)
    if (!matched && !DOWNLOAD_ONLY) {
        matched = FILE_RE.test(target) || RAW_RE.test(target) || GIST_RE.test(target)
    }
    if (!matched) {
        return makeRes('仅支持 Release / Archive 下载。', 403)
    }
    if (!isAllowedOwner(target)) {
        return makeRes('该用户名不在白名单内。', 403)
    }

    return proxy(req, target)
}

// 获取最新 Release 精简 JSON（优先缓存）
async function apiLatest(urlObj) {
    let repo = urlObj.searchParams.get('repo') || LIST_REPO
    const cacheKey = 'https://cache.local/api/latest?repo=' + encodeURIComponent(repo.toLowerCase())
    const cache = caches.default

    const cached = await cache.match(cacheKey)
    if (cached) {
        return new Response(cached.body, {
            headers: { 'content-type': 'application/json; charset=utf-8', 'cache-control': 'no-store' },
        })
    }

    const headers = { 'User-Agent': 'vanta-dl', 'Accept': 'application/vnd.github+json' }
    if (GITHUB_TOKEN) headers['Authorization'] = 'Bearer ' + GITHUB_TOKEN

    const res = await fetch('https://api.github.com/repos/' + repo + '/releases/latest', { headers })
    if (!res.ok) {
        return makeRes(JSON.stringify({ error: 'GitHub API ' + res.status }), 502, { 'content-type': 'application/json; charset=utf-8' })
    }
    const data = await res.json()
    const slim = {
        tag_name: data.tag_name || '',
        name: data.name || '',
        published_at: data.published_at || '',
        html_url: data.html_url || '',
        assets: (data.assets || []).map(a => ({
            name: a.name,
            size: a.size,
            content_type: a.content_type,
            browser_download_url: a.browser_download_url,
        })),
    }
    const body = JSON.stringify(slim)
    const resp = new Response(body, {
        headers: { 'content-type': 'application/json; charset=utf-8', 'cache-control': 'no-store' },
    })
    // 缓存 10 分钟（不阻塞响应；fire-and-forget 并兜住异常）
    cache.put(cacheKey, resp.clone()).catch(function () {})
    return resp
}

async function proxy(req, urlStr) {
    const reqHdrNew = new Headers(req.headers)
    if (req.method === 'OPTIONS' && req.headers.has('access-control-request-headers')) {
        return new Response(null, PREFLIGHT_INIT)
    }
    const urlObj = new URL(urlStr)
    const reqInit = {
        method: req.method,
        headers: reqHdrNew,
        redirect: 'follow',
        body: (req.method === 'GET' || req.method === 'HEAD') ? undefined : req.body,
    }
    const res = await fetch(urlObj.href, reqInit)
    const resHdrNew = new Headers(res.headers)
    resHdrNew.set('access-control-expose-headers', '*')
    resHdrNew.set('access-control-allow-origin', '*')
    resHdrNew.delete('content-security-policy')
    resHdrNew.delete('content-security-policy-report-only')
    resHdrNew.delete('clear-site-data')
    return new Response(res.body, { status: res.status, headers: resHdrNew })
}
