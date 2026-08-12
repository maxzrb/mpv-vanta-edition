/**
 * ============================================================
 *  MPV Vanta Edition GitHub Release 下载代理（Cloudflare Worker）
 * ============================================================
 *  基于 hubporg/CF-GitHub-Proxy 定制（MIT License）
 *    https://github.com/hubporg/CF-GitHub-Proxy
 *  原项目版权 (c) hubporg / Geekertao；本文件保留其 MIT 版权声明。
 *
 *  用途：只允许代理 maxzrb 用户名下所有仓库的
 *        Release 资产 / Archive 源码下载，供国内用户加速。
 *
 *  特点：
 *    - 白名单限定仓库，避免域名被当作公共 GitHub 代理滥用
 *    - 流式透传（res.body 不缓冲），支持 1.9GB 大分卷
 *    - 透传 Range / Accept-Ranges，支持断点续传与多线程下载
 *    - 不依赖任何服务器与存储，Cloudflare 免费层即可运行
 *    - 无缓存（实时回源 GitHub；免费版单对象缓存上限 512MB 装不下 02/03）
 * ============================================================
 */

'use strict'

// ==================== 配置区 ====================
// 允许代理的 GitHub 用户名（小写；该用户名下所有仓库的 Release / Archive 均可代理）
const ALLOWED_OWNERS = [
    'maxzrb',
]

// true  = 仅允许 release/archive 下载（纯下载站，推荐）
// false = 额外允许 blob/raw 等仓库文件代理（相当于整仓镜像）
const DOWNLOAD_ONLY = true

// 根路径访问时展示的落地页（可自由修改）
const LANDING_HTML = `<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>AerithDream的下载加速</title>
<style>
  body { font-family: system-ui, sans-serif; max-width: 760px; margin: 48px auto; padding: 0 20px; color: #222; line-height: 1.7; }
  h1 { font-size: 22px; }
  code { background: #f3f4f6; padding: 2px 6px; border-radius: 4px; font-size: 14px; word-break: break-all; }
  .box { border: 1px solid #e5e7eb; border-radius: 8px; padding: 12px 16px; margin: 12px 0; }
</style>
</head>
<body>
<h1>AerithDream的下载加速</h1>
<p>本服务是 GitHub Release 的加速代理，代理
<a href="https://github.com/maxzrb">maxzrb</a> 用户名下
所有仓库的发布资产。请在任意 GitHub 下载链接前加上本域名前缀：</p>
<div class="box">
<code>https://dl.loliland.cn/https://github.com/maxzrb/mpv-vanta-edition/releases/download/v1.5.1/05-mpv-config-v1.5.1.7z</code>
</div>
<p>也可以直接打开
<a href="https://github.com/maxzrb/mpv-vanta-edition/releases">GitHub Releases 页面</a>，
把资产的下载地址拼上本域名前缀。</p>
</body>
</html>`
// ================================================

const PREFLIGHT_INIT = {
    status: 204,
    headers: new Headers({
        'access-control-allow-origin': '*',
        'access-control-allow-methods': 'GET,POST,PUT,PATCH,TRACE,DELETE,HEAD,OPTIONS',
        'access-control-max-age': '1728000',
    }),
}

// release 资产下载与 archive 源码包
const RELEASE_RE = /^(?:https?:\/\/)?github\.com\/.+?\/.+?\/(?:releases\/download|archive)\/.*$/i
// 仓库文件（DOWNLOAD_ONLY=false 时启用）
const FILE_RE = /^(?:https?:\/\/)?github\.com\/.+?\/.+?\/(?:blob|raw)\/.*$/i
// raw.githubusercontent / gist（DOWNLOAD_ONLY=false 时启用）
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
    // 纯字符串前缀判断，避免正则转义问题：
    // 以 https://github.com/<owner>/ 开头即为该用户名下仓库，
    // https://github.com/maxzrb2/ 不会误匹配 maxzrb。
    const lower = target.toLowerCase()
    return ALLOWED_OWNERS.some(owner =>
        lower.startsWith('https://github.com/' + owner + '/')
    )
}

async function fetchHandler(e) {
    const req = e.request
    const urlObj = new URL(req.url)
    const path = urlObj.href.substr(urlObj.origin.length)

    // 根路径：展示落地页
    if (path === '/' || path === '') {
        return makeRes(LANDING_HTML, 200, { 'content-type': 'text/html; charset=utf-8' })
    }

    // 兼容 ?q= 形式（gh-proxy 传统写法），301 到标准前缀形式
    const q = urlObj.searchParams.get('q')
    if (q) {
        return Response.redirect(urlObj.origin + '/' + q, 301)
    }

    // 去掉前导 / 得到目标 URL（自动补 https://）
    let target = path.replace(/^\/+/, '').replace(/^https?:\/+/, 'https://')

    if (!/^https?:\/\//i.test(target)) {
        return makeRes('仅支持 GitHub 下载路径。', 400)
    }

    // 路径模式校验
    let matched = RELEASE_RE.test(target)
    if (!matched && !DOWNLOAD_ONLY) {
        matched = FILE_RE.test(target) || RAW_RE.test(target) || GIST_RE.test(target)
    }
    if (!matched) {
        return makeRes('仅支持 Release / Archive 下载。', 403)
    }

    // 用户名白名单校验
    if (!isAllowedOwner(target)) {
        return makeRes('该用户名不在白名单内。', 403)
    }

    return proxy(req, target)
}

async function proxy(req, urlStr) {
    const reqHdrNew = new Headers(req.headers)

    // CORS 预检
    if (req.method === 'OPTIONS' && req.headers.has('access-control-request-headers')) {
        return new Response(null, PREFLIGHT_INIT)
    }

    const urlObj = new URL(urlStr)
    const reqInit = {
        method: req.method,
        headers: reqHdrNew,
        redirect: 'follow', // release 资产会 302 到对象存储，自动跟随并流式透传
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
