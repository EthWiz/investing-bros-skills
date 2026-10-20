# WhatsApp share of the live episode

Step 7 of `investing-bros-episode-upload`. The WhatsApp ownership rules, show tag and **approved destinations** table are in `investing-bros-show`.

## Inputs
1. **Public episode URL** (RedCircle).
2. **Destinations** — only ids from the approved-destinations table that Amitai asked for. `achim` only when he explicitly wants a live ping there.
3. **Text per destination** — ask Amitai for the copy if he hasn't given it. Don't invent promo copy.
4. **Artwork** (optional, only if the run asks for it) — the show cover, or the episode's square cover or 16:9 thumbnail (`promo/`) once approved.

## Steps
1. For each destination, prepare: exact group name, exact message text ending with the show tag, the public URL, artwork path or note (if any), and one line of context (which episode, why).
2. Send that to the WhatsApp owner and ask for a yes/no per destination. Don't open WhatsApp Web yourself.
3. Wait for confirmation; report to Amitai.

## Done when
Each destination is confirmed sent, or has a clear blocker (group not found, WhatsApp down), and you've reported the status to Amitai.

## Never
- Drive WhatsApp Web or scan a QR.
- Add groups that aren't in the approved table without Amitai's OK.
- Delete earlier WhatsApp messages.
