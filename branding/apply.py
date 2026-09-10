#!/usr/bin/env python3
"""
Ramtown branding for the TextBee fork.

CI runs this right before each build, on a checkout of unmodified upstream
source, after the workflow has swapped textbee.dev for our URLs:

    python3 branding/apply.py web
    python3 branding/apply.py android

Nothing here is committed to upstream files, so "Sync fork" never conflicts.
Every edit is anchored on an exact upstream string, and the script stops with
a clear error when an anchor is gone. An upstream change can therefore break
the build, which is the point: it can never ship a half-branded app quietly.

What it does
  web      logo + favicon, page title, brand colours, header wordmark, and it
           removes every sign-up, upgrade, verify-email, community, survey and
           Discord surface. Links that pointed at textbee.dev point at our
           dashboard, the app-download links at our GitHub releases.
  android  launcher icons and in-app logo, theme colours, and every visible
           "textbee" string becomes the brand name; help text that told users
           to create an account at textbee.dev tells them to ask the office.

Environment
  WEB_URL     https://sms.congramtown.org      dashboard, no trailing slash
  API_URL     https://sms-api.congramtown.org  API, no trailing slash
  FORK_REPO   Ramtown613/textbee               where the APK releases live
  BRAND_NAME  Ramtown SMS
"""
import os
import pathlib
import re
import shutil
import sys
from urllib.parse import urlparse

ROOT = pathlib.Path(__file__).resolve().parent.parent
ASSETS = ROOT / "branding" / "assets"

WEB_URL = os.environ.get("WEB_URL", "").rstrip("/")
FORK = os.environ.get("FORK_REPO", "Ramtown613/textbee")
NAME = os.environ.get("BRAND_NAME", "Ramtown SMS")
DASH = f"{WEB_URL}/dashboard"
RELEASES = f"https://github.com/{FORK}/releases/latest"
HOST = urlparse(WEB_URL).netloc

# Brand colours, from the Ramtown Shul print materials.
NAVY, NAVY_DARK, DUSTY, MIST, PARCH, CHAMP = "#2F435B", "#233242", "#71869D", "#E6EEF5", "#FAF7F2", "#B79A72"
BRAND_SCALE = {
    "50": "#F3F6F9", "100": MIST, "200": "#CBD6E0", "300": "#A9B9C9", "400": DUSTY,
    "500": "#4E6480", "600": NAVY, "700": "#263749", "800": "#1E2B3A", "900": "#16202B", "950": "#0E151C",
}
NAVY_HSL = "213 32% 27%"

changed: list[str] = []


def die(msg: str) -> None:
    print(f"::error::branding: {msg}")
    sys.exit(1)


def read(rel: str) -> str:
    p = ROOT / rel
    if not p.is_file():
        die(f"file missing: {rel}")
    return p.read_text(encoding="utf-8")


def write(rel: str, text: str) -> None:
    (ROOT / rel).write_text(text, encoding="utf-8")
    changed.append(rel)


def rep(s: str, old: str, new: str, rel: str, count: int = 0) -> str:
    """Replace an exact anchor. count=0 means every occurrence; the anchor must exist."""
    if old not in s:
        die(f"anchor missing in {rel}: {old[:70]!r}")
    return s.replace(old, new) if count == 0 else s.replace(old, new, count)


def cut(s: str, start: str, end: str, rel: str) -> str:
    """Remove from the start anchor through the end anchor, inclusive."""
    i = s.find(start)
    if i < 0:
        die(f"start anchor missing in {rel}: {start[:70]!r}")
    j = s.find(end, i)
    if j < 0:
        die(f"end anchor missing in {rel}: {end[:70]!r}")
    return s[:i] + s[j + len(end):]


def edit(rel: str, fn) -> None:
    s = read(rel)
    n = fn(s)
    if n == s:
        die(f"no change made to {rel}")
    write(rel, n)


def stub(rel: str) -> None:
    """Replace a React component module with exports that render nothing."""
    s = read(rel)
    default = re.findall(r"^export default function (\w+)", s, re.M)
    named = re.findall(r"^export (?:const|function) (\w+)", s, re.M)
    if not default and not named:
        die(f"no exports recognised in {rel}")
    out = ["// Replaced by branding/apply.py: this surface does not exist on a private install.\n"]
    out += [f"export const {n}: any = () => null\n" for n in named]
    out += [f"export default function {n}() {{\n  return null\n}}\n" for n in default]
    write(rel, "".join(out))


def copy(src: pathlib.Path, rel: str) -> None:
    if not src.is_file():
        die(f"asset missing: {src}")
    dst = ROOT / rel
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(src, dst)
    changed.append(rel)


# --------------------------------------------------------------------------- web

def web() -> None:
    copy(ASSETS / "logo.png", "web/public/images/logo.png")
    copy(ASSETS / "favicon.ico", "web/public/favicon.ico")

    edit("web/app/layout.tsx", lambda s: rep(
        rep(s, "title: 'textbee.dev - sms gateway - dashboard'", f"title: '{NAME}'", "layout.tsx"),
        "new URL('https://textbee.dev')", f"new URL('{WEB_URL}')", "layout.tsx"))

    def routes(s: str) -> str:
        out = []
        for line in s.splitlines(keepends=True):
            if "textbee.dev" in line:
                target = RELEASES if "downloadAndroidApp" in line else DASH
                line = re.sub(r"'https://[a-z.]*textbee\.dev[^']*'", f"'{target}'", line)
            out.append(line)
        return "".join(out)
    edit("web/config/routes.ts", routes)

    def external(s: str) -> str:
        s = rep(s, "'https://github.com/textbee/textbee'", f"'https://github.com/{FORK}'", "external-links.ts")
        return re.sub(
            r"'https://(?:[a-z.]*textbee\.dev|patreon\.com/vernu|x\.com/textbeedotdev|"
            r"www\.linkedin\.com/company/textbeedotdev|polar\.sh/textbee/portal/request)[^']*'",
            f"'{DASH}'", s)
    edit("web/config/external-links.ts", external)

    # Surfaces that only make sense on the public textbee.dev service.
    for rel in [
        "web/app/(app)/dashboard/(components)/alerts/join-discord-banner.tsx",
        "web/app/(app)/dashboard/(components)/alerts/upgrade-to-pro-alert.tsx",
        "web/app/(app)/dashboard/(components)/alerts/verify-email-alert.tsx",
        "web/app/(app)/dashboard/(components)/alerts/past-due-billing-alert.tsx",
        "web/app/(app)/dashboard/(components)/get-started/index.tsx",
        "web/app/(app)/dashboard/(components)/billing/usage-summary.tsx",
        "web/app/(app)/dashboard/(components)/community/community-links.tsx",
        "web/app/(app)/(auth)/(components)/login-with-google.tsx",
        "web/components/shared/survey-modal.tsx",
        "web/components/shared/join-community-modal.tsx",
        "web/components/shared/footer.tsx",
        # Google Analytics and Microsoft Clarity session recording, tagged with the
        # signed-in user's e-mail, reporting to textbee.dev's accounts. Not on ours.
        "web/components/shared/analytics.tsx",
    ]:
        stub(rel)

    # Login page: no "Or / Google" divider, no "Forgot password" or "Sign up".
    def login(s: str) -> str:
        s = cut(s, "          <div className='relative mt-4'>\n",
                "            <LoginWithGoogle />\n          </div>\n", "login/page.tsx")
        return cut(s, "        <CardFooter", "        </CardFooter>\n", "login/page.tsx")
    edit("web/app/(app)/(auth)/login/page.tsx", login)

    # Sidebar: drop the "Need help? Quick start" link to textbee.dev.
    edit("web/app/(app)/dashboard/layout.tsx", lambda s: cut(
        s, "          <p className='text-xs text-muted-foreground'>\n            Need help?",
        "          </p>\n", "dashboard/layout.tsx"))

    # Account area: no billing, no support form.
    def account(s: str) -> str:
        s = rep(s, "          { href: '/dashboard/account/billing', label: 'Billing & plan' },\n", "", "account/layout.tsx")
        s = rep(s, "          { href: '/dashboard/account/support', label: 'Support' },\n", "", "account/layout.tsx")
        return rep(s, "description='Manage your subscription, profile and security'",
                   "description='Manage your profile and security'", "account/layout.tsx")
    edit("web/app/(app)/dashboard/account/layout.tsx", account)

    def nav(s: str) -> str:
        s = rep(s, "  { href: '/dashboard/community', label: 'Community', icon: Users },\n", "", "nav-items.ts")
        return rep(s, "    href: '/dashboard/account/billing',\n    label: 'Account',",
                   "    href: '/dashboard/account/profile',\n    label: 'Account',", "nav-items.ts")
    edit("web/app/(app)/dashboard/(components)/nav-items.ts", nav)

    header_old = (
        "          <Image\n"
        "            src='/images/logo.png'\n"
        "            alt='textbee Logo'\n"
        "            width={24}\n"
        "            height={24}\n"
        "            className='h-6 w-6 rounded-full bg-white'\n"
        "          />\n"
        "          <span className='font-bold'>\n"
        "            text<span className='text-primary'>bee</span>\n"
        "            <span className='align-center text-xs text-muted-foreground'>\n"
        "              .dev\n"
        "            </span>\n"
        "          </span>"
    )
    header_new = (
        "          <Image\n"
        "            src='/images/logo.png'\n"
        "            alt='__NAME__'\n"
        "            width={28}\n"
        "            height={28}\n"
        "            className='h-7 w-7'\n"
        "          />\n"
        "          <span className='font-bold'>__NAME__</span>"
    ).replace("__NAME__", NAME)
    def header(s: str) -> str:
        s = rep(s, header_old, header_new, "app-header.tsx")
        # The two "Get started" sign-up buttons shown to logged-out visitors.
        s, n = re.subn(
            r"
[ ]*<Button
[ ]*asChild
[ ]*className='rounded-full bg-primary text-white hover:bg-primary/90'
[ ]*>
"
            r"[ ]*<Link href=\{Routes\.register\}>Get started</Link>
[ ]*</Button>", "", s)
        if n != 2:
            die(f"expected 2 Get-started buttons in app-header.tsx, found {n}")
        return s
    edit("web/components/shared/app-header.tsx", header)

    def colours(s: str) -> str:
        s = rep(s, "--primary: 21 90% 48%;", f"--primary: {NAVY_HSL};", "main.css")
        s = rep(s, "--ring: 21 90% 48%;", f"--ring: {NAVY_HSL};", "main.css")
        s = rep(s, "--ring: 21 90% 52%;", "--ring: 213 30% 45%;", "main.css")
        for step, hexv in BRAND_SCALE.items():
            s, n = re.subn(rf"(--color-brand-{step}:\s*)#[0-9a-fA-F]{{6}};", rf"\g<1>{hexv};", s)
            if n != 1:
                die(f"brand-{step} colour anchor missing in main.css")
        return s
    edit("web/styles/main.css", colours)

    # The download page lists releases: ours, not upstream's.
    edit("web/app/download/page.tsx", lambda s: rep(
        rep(s, "https://api.github.com/repos/textbee/textbee/releases",
            f"https://api.github.com/repos/{FORK}/releases", "download/page.tsx"),
        "https://github.com/textbee/textbee/releases", f"https://github.com/{FORK}/releases", "download/page.tsx"))


# ----------------------------------------------------------------------- android

def android() -> None:
    res = "android/app/src/main/res"
    for dens in ("mdpi", "hdpi", "xhdpi", "xxhdpi", "xxxhdpi"):
        d = ROOT / res / f"mipmap-{dens}"
        if not d.is_dir():
            die(f"missing {d}")
        for old in d.glob("ic_launcher*.webp"):
            old.unlink()
        for name in ("ic_launcher", "ic_launcher_round", "ic_launcher_foreground"):
            copy(ASSETS / "android" / f"mipmap-{dens}" / f"{name}.png", f"{res}/mipmap-{dens}/{name}.png")
    old_logo = ROOT / res / "drawable" / "ic_app_logo.webp"
    if not old_logo.is_file():
        die("drawable/ic_app_logo.webp missing")
    old_logo.unlink()
    copy(ASSETS / "android" / "ic_app_logo.png", f"{res}/drawable/ic_app_logo.png")

    edit(f"{res}/values/ic_launcher_background.xml", lambda s: rep(s, "#F3F3F3", PARCH, "ic_launcher_background.xml"))

    theme_map = {"#C4620A": NAVY, "#A04405": NAVY_DARK, "#B45309": CHAMP, "#92400E": "#8F7554"}

    def themes(s: str) -> str:
        for old, new in theme_map.items():
            s = rep(s, old, new, "themes.xml")
        return s
    edit(f"{res}/values/themes.xml", themes)

    kt_map = {"0xFFC4620A": "0xFF2F435B", "0xFFA04405": "0xFF233242", "0xFFB45309": "0xFF4E6480",
              "0xFF92400E": "0xFF1E2B3A", "0xFFFFF7ED": "0xFFFAF7F2"}

    def colour_kt(s: str) -> str:
        for old, new in kt_map.items():
            s = rep(s, old, new, "Color.kt")
        return s
    edit("android/app/src/main/java/com/vernu/sms/ui/theme/Color.kt", colour_kt)

    # Visible strings. Only inside "..." literals, so identifiers such as
    # TextbeeUtils are untouched (they are capitalised anyway).
    subs = [
        ("Create a free account at textbee.dev", "Ask the office for your API key"),
        ("https://app.textbee.dev", DASH),
        ("https://textbee.dev", DASH),
        ("app.textbee.dev/dashboard", HOST),
        ("textbee.dev/dashboard", HOST),
        ("textbee.dev", NAME),
        ("textbee", NAME),
    ]
    literal = re.compile(r'"((?:[^"\\\n]|\\.)*)"')
    total = 0
    java = ROOT / "android/app/src/main/java/com/vernu/sms"
    for sub in ("ui", "services", "activities"):
        for f in sorted((java / sub).rglob("*")):
            if f.suffix not in (".kt", ".java"):
                continue
            s = f.read_text(encoding="utf-8")

            def fix(m: re.Match) -> str:
                nonlocal total
                lit = m.group(1)
                new = lit
                for old, rep_ in subs:
                    new = new.replace(old, rep_)
                if new != lit:
                    total += 1
                return f'"{new}"'
            n = literal.sub(fix, s)
            if n != s:
                f.write_text(n, encoding="utf-8")
                changed.append(str(f.relative_to(ROOT)))
    if total < 10:
        die(f"only {total} Android strings rebranded; upstream layout changed?")
    print(f"android: {total} string literals rebranded")


if __name__ == "__main__":
    if not WEB_URL:
        die("WEB_URL is not set")
    target = sys.argv[1] if len(sys.argv) > 1 else ""
    if target == "web":
        web()
    elif target == "android":
        android()
    else:
        die("usage: apply.py web|android")
    print(f"branding applied to {len(changed)} files for {NAME} ({WEB_URL})")
    for c in changed:
        print("  ", c)
