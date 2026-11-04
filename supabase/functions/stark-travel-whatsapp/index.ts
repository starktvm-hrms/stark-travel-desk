// Stark Travel Desk → WhatsApp Cloud API sender.
//
// POST { "to": "919876543210", "body": "message text" }
// Header x-travel-desk-secret must equal the TRAVEL_DESK_SECRET secret.
//
// Secrets (Supabase → Edge Functions → Secrets):
//   TRAVEL_DESK_SECRET     shared secret, also pasted into the travel desk's Settings
//   WA_TOKEN               permanent access token of a Meta system user with whatsapp_business_messaging
//   WA_PHONE_NUMBER_ID     the sending number's Phone number ID (Meta → WhatsApp → API setup)
//   WA_TEMPLATE_NAME       optional: approved template with ONE body variable {{1}}; when set, every message is
//                          sent through it (needed for business-initiated messages outside the 24-hour window)
//   WA_TEMPLATE_LANG       optional: template language code, default "en"
//   WA_API_VERSION         optional: Graph API version, default "v21.0"

const json = (status: number, obj: unknown) =>
  new Response(JSON.stringify(obj), { status, headers: { "Content-Type": "application/json" } });

function safeEqual(a: string, b: string): boolean {
  if (a.length !== b.length) return false;
  let r = 0;
  for (let i = 0; i < a.length; i++) r |= a.charCodeAt(i) ^ b.charCodeAt(i);
  return r === 0;
}

Deno.serve(async (req) => {
  if (req.method !== "POST") return json(405, { ok: false, error: "Use POST." });

  const secret = Deno.env.get("TRAVEL_DESK_SECRET") ?? "";
  const given = req.headers.get("x-travel-desk-secret") ?? "";
  if (!secret || !safeEqual(given, secret)) return json(401, { ok: false, error: "Wrong or missing travel desk secret." });

  const token = Deno.env.get("WA_TOKEN");
  const phoneId = Deno.env.get("WA_PHONE_NUMBER_ID");
  if (!token || !phoneId) return json(500, { ok: false, error: "WA_TOKEN and WA_PHONE_NUMBER_ID secrets are not set in Supabase." });

  let input: { to?: string; body?: string };
  try {
    input = await req.json();
  } catch {
    return json(400, { ok: false, error: "Body must be JSON." });
  }
  const to = String(input.to ?? "").replace(/\D/g, "");
  const body = String(input.body ?? "").trim();
  if (to.length < 11 || to.length > 15) return json(400, { ok: false, error: "Recipient must include the country code." });
  if (!body) return json(400, { ok: false, error: "Message is empty." });

  const template = Deno.env.get("WA_TEMPLATE_NAME");
  const payload = template
    ? {
      messaging_product: "whatsapp",
      to,
      type: "template",
      template: {
        name: template,
        language: { code: Deno.env.get("WA_TEMPLATE_LANG") ?? "en" },
        components: [{
          type: "body",
          // Template variables may not contain newlines, tabs or 4+ spaces.
          parameters: [{ type: "text", text: body.replace(/\s*\n+\s*/g, " · ").replace(/\s{2,}/g, " ").slice(0, 1000) }],
        }],
      },
    }
    : { messaging_product: "whatsapp", to, type: "text", text: { preview_url: false, body: body.slice(0, 4096) } };

  const version = Deno.env.get("WA_API_VERSION") ?? "v21.0";
  const res = await fetch(`https://graph.facebook.com/${version}/${phoneId}/messages`, {
    method: "POST",
    headers: { Authorization: `Bearer ${token}`, "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  const out = await res.json().catch(() => ({}));
  if (!res.ok) {
    const err = out?.error;
    const msg = err?.error_data?.details || err?.message || `WhatsApp API returned ${res.status}`;
    // 131047: outside the 24h window → a template is required.
    const hint = err?.code === 131047 ? " Set WA_TEMPLATE_NAME to an approved template to message travellers first." : "";
    return json(502, { ok: false, error: msg + hint, code: err?.code ?? null });
  }
  return json(200, { ok: true, id: out?.messages?.[0]?.id ?? "" });
});
