import { Hono } from "hono"
import { cors } from "hono/cors"
import { zValidator } from "@hono/zod-validator"
import { z } from "zod"
import { logger } from "hono/logger"
import { proxy } from "hono/proxy"

const app = new Hono()

app.use(cors())

app.use(logger())

app.use(async (c, next) => {
  await next()
  c.res.headers.set("X-Accel-Buffering", "no")
})

app.get("/", (c) => c.text("A proxy for AI!"))

const fetchWithTimeout = async (
  url: string,
  { timeout, ...options }: RequestInit & { timeout: number },
) => {
  const controller = new AbortController()

  const timeoutId = setTimeout(() => {
    controller.abort()
  }, timeout)

  try {
    const res = await proxy(url, {
      ...options,
      signal: controller.signal,
      // @ts-expect-error
      duplex: "half",
    })
    clearTimeout(timeoutId)
    return res
  } catch (error) {
    clearTimeout(timeoutId)
    if (controller.signal.aborted) {
      return new Response("Request timeout", {
        status: 504,
      })
    }

    throw error
  }
}

const proxies: { pathSegment: string; target: string; orHostname?: string }[] =
  [
    {
      pathSegment: "generativelanguage",
      orHostname: "gooai.chatkit.app",
      target: "https://generativelanguage.googleapis.com",
    },
    {
      pathSegment: "groq",
      target: "https://api.groq.com",
    },
    {
      pathSegment: "anthropic",
      target: "https://api.anthropic.com",
    },
    {
      pathSegment: "pplx",
      target: "https://api.perplexity.ai",
    },
    {
      pathSegment: "openai",
      target: "https://api.openai.com",
    },
    {
      pathSegment: "mistral",
      target: "https://api.mistral.ai",
    },
    {
      pathSegment: "openrouter/api",
      target: "https://openrouter.ai/api",
    },
    {
      pathSegment: "openrouter",
      target: "https://openrouter.ai/api",
    },
    {
      pathSegment: "xai",
      target: "https://api.x.ai",
    },
    {
      pathSegment: "cerebras",
      target: "https://api.cerebras.ai",
    },
    {
      pathSegment: "googleapis-cloudcode-pa",
      target: "https://cloudcode-pa.googleapis.com",
    },
  ]

app.post(
  "/custom-model-proxy",
  zValidator(
    "query",
    z.object({
      url: z.string().url(),
    }),
  ),
  async (c) => {
    const { url } = c.req.valid("query")

    const res = await proxy(url, {
      method: c.req.method,
      body: c.req.raw.body,
      headers: c.req.raw.headers,
    })

    return new Response(res.body, {
      headers: res.headers,
      status: res.status,
    })
  },
)

app.use(async (c, next) => {
  const url = new URL(c.req.url)

  const proxy = proxies.find(
    (p) =>
      url.pathname.startsWith(`/${p.pathSegment}/`) ||
      (p.orHostname && url.hostname === p.orHostname),
  )

  if (proxy) {
    const headers = new Headers()
    headers.set("host", new URL(proxy.target).hostname)

    // 收集原始请求的 headers，但要特别处理 Content-Type
    let contentType: string | null = null
    c.req.raw.headers.forEach((value, key) => {
      const k = key.toLowerCase()
      if (
        !k.startsWith("cf-") &&
        !k.startsWith("x-forwarded-") &&
        !k.startsWith("cdn-") &&
        k !== "x-real-ip" &&
        k !== "host"
      ) {
        // 对于 Content-Type，先保存下来，后面单独处理
        if (k === "content-type") {
          contentType = value
        } else {
          headers.set(key, value)
        }
      }
    })

    // 单独设置 Content-Type，确保不会被重复设置
    if (contentType) {
      headers.set("Content-Type", contentType)
    }

    const targetUrl = `${proxy.target}${url.pathname.replace(
      `/${proxy.pathSegment}/`,
      "/",
    )}${url.search}`

    // 对于 Google 文件上传请求，增加超时时间并打印调试信息
    const isFileUpload = url.pathname.includes("/upload/") || url.searchParams.has("upload_type")
    const timeout = isFileUpload ? 300000 : 60000 // 文件上传超时设为 5 分钟

    // 调试日志：打印文件上传请求的关键信息
    if (isFileUpload) {
      console.log("[File Upload] Target URL:", targetUrl)
      console.log("[File Upload] Content-Type:", contentType)
      console.log("[File Upload] Method:", c.req.method)
    }

    const res = await fetchWithTimeout(targetUrl, {
      method: c.req.method,
      headers,
      body: c.req.raw.body,
      timeout,
    })

    return new Response(res.body, {
      headers: res.headers,
      status: res.status,
    })
  }

  next()
})

export default app
