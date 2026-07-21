# BLUEPRINT: PICKLE TIME DUVALL HIGH-CONVERSION WEBSITE

Follows the High-Turnover Food & Beverage vertical spec from `../Website SETUP architecture.md`, matching the real-world pattern already used for Pho Than Brothers and Pacific Northwest Brewing Center.

## 1. Architectural Constraints
- **Framework Target:** Static HTML5, vanilla CSS, vanilla JS. No build step, no frameworks. Optimized for instant mobile load and zero layout shift.
- **Styling:** Palette and type pulled directly from the real mascot logo (`assets/logo.jpg`) and illuminated storefront sign, once supplied by the client. Rounded display font (Google Fonts 'Fredoka') for headings/buttons matching the logo's chunky lettering, 'Inter' for body copy.
  - Background: Cream badge-ring tone (`#FDF6E3`), deep pickle green-black for dark sections (`#172913`)
  - Accent: Pickle green (`#4C9A2A`, hover `#367A1D`)
  - Secondary accents: Mustard (`#F2B705`, chef hat/gloves), Red (`#D6402E`, mascot shoes)
  - Text: near-black (`#201F0F`), muted olive-grey (`#6E6A50`)
- **Menu Architecture:** Zero PDFs. Full menu (Hot Subs, Burgers, Wraps, Fish & Chips, Kids Meals, Sides, Shakes & Smoothies, Drinks & Add-Ons) built as static semantic HTML (`<article class="menu-item">`) with `data-category` attributes, filtered client-side via tab buttons — no fetch/CMS layer needed for a single-location static menu.
- **Conversion Loop:** Primary CTA is **Order Online**, deep-linking to the client's existing Menu11 ordering platform (`https://pickletimeduvall.menu11.com/duvall/order`) — surfaced in the header, hero, CTA banner, footer, location card, and mobile sticky bar. Click-to-call ((425) 788-8605) and Get Directions are secondary actions.
- **Social Proof:** Curated real Google review excerpts in a testimonials section.
- **SEO & Schema:** Hardcoded JSON-LD `FoodEstablishment` schema in `<head>` with address, phone, geo, hours, price range, menu URL anchor.
- **Dynamic Behavior:** Open/closed status badge computed client-side from real per-day store hours (Mon–Sat 10:30–20:30, Sun closed).

## 2. Dependency & Impact Graph
- `index.html` -> Core markup: header/nav, hero, menu (all categories + tabs), testimonials, hours/location, footer, JSON-LD.
- `css/style.css` -> Theme variables, layout, responsive grid, sticky mobile CTA bar, tab/menu-card styling.
- `js/app.js` -> Mobile nav toggle, menu category tab filtering, live open/closed status from real hours table, smooth scroll.
- `assets/` -> Real client photography: `logo.jpg` (mascot logo, used in header/footer/hero/favicon/JSON-LD), `bacon-burger.jpg` (hero image), `storefront.jpg`, `storefront-window.jpg`, `interior-1.jpg`, `interior-2.jpg` (gallery section), `pickle-time-sign.jpg` (CTA banner background).

## 3. Milestone Checklist
- [x] **Milestone 1:** Project structure + CSS design system (variables, reset, typography).
- [x] **Milestone 2:** Semantic HTML: hero, sticky CTA bar, full categorized menu, testimonials, hours/location, footer.
- [x] **Milestone 3:** Responsive mobile-first layout, tab-filtered menu grid, hover/press states.
- [x] **Milestone 4:** JSON-LD FoodEstablishment schema injection for local SEO.
- [x] **Milestone 5:** JS: nav toggle, tab filtering, real-hours-based open/closed badge, smooth scroll.
- [x] **Milestone 6:** Swap in real photography/logo assets, re-theme color palette and typography to match the logo.

## 4. Verification Plan
- Open `index.html` directly in a browser; confirm responsive layout at mobile/tablet/desktop widths.
- Confirm tab filtering shows/hides the correct `data-category` items.
- Confirm the open/closed badge matches the real Mon–Sat 10:30–20:30 / Sun closed schedule at the time of testing.
- Validate JSON-LD with a structured data checker.
- No external JS/CSS frameworks loaded; only Google Fonts.
