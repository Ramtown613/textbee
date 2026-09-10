# Ramtown branding

Everything in this folder belongs to the fork, not to upstream. Upstream never
has a `branding/` directory, so syncing the fork never conflicts with it.

- `apply.py` is run by the Ramtown release workflow right before each build.
  It rebrands the working copy: logo, icons, colours, the page title, every
  visible "textbee", and it removes the sign-up, upgrade, verify-email,
  community, survey and Discord surfaces. Upstream files in git stay untouched.
- `assets/` holds the ram from the Ramtown Shul logo, cut to a transparent
  square, in every size the dashboard and the Android launcher need.
- `make_icons.py` builds the launcher icons in `assets/android` from
  `assets/logo.png`: the ram with the word SMS under it, so the icon says what
  the app is. Run it again whenever the logo or the word changes, then commit
  the PNGs. Needs Pillow and a bold TrueType font.

On the phone, `apply.py` also removes the Subscription card and the Explore
Docs button from the dashboard, and the "Sign up free" and textbee.dev links
from onboarding. There is no plan, no upgrade and no sign-up on a private
install.

If an upstream release moves something the script anchors on, the build fails
with a `branding:` error naming the anchor. Fix the anchor in `apply.py`, push,
and the build runs again. That is deliberate: a half-branded app must never
ship quietly.
