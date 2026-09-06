# Personal Portfolio - Karyn Isabelle Dexter

Name: Karyn Isabelle Dexter

NPM: 2506656860

Class: PBP A

## About This Project

A personal portfolio website built on top of a Django project. As of Assignment 1, the "About Me" page is still pure HTML5 + CSS3 (no database or MVT architecture yet) and includes:

- **Profile** - name, NPM, photo, and a short bio.
- **Education** - education history laid out as a timeline.
- **Experience** - organizational/committee experience as a card grid.
- **Hobbies** - everyday hobbies as an icon grid.

## Running the Project

1. Clone this repository and enter the project folder.
2. Create and activate a virtual environment:
   ```
   python -m venv env
   source env/bin/activate
   ```
3. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
4. Run the development server:
   ```
   python manage.py runserver
   ```
5. Open `http://127.0.0.1:8000/` in your browser.

## Weekly Progress

### Tutorial & Assignment 1
- Built the base "About Me" page from Tutorial 01 (profile section: name, NPM, photo, bio).
- Added three new sections for Assignment 1: Education (timeline), Experience (card grid), and Hobbies (icon grid), each with its own CSS rules (Flexbox/Grid layout, hover effects).
- Fixed a couple of Django config bugs found while testing locally that were breaking the site (`TEMPLATES` dirs pointing nowhere caused a 500 error, and a missing `STATICFILES_DIRS` was causing the CSS/image to 404).

## Reflection Questions

### Assignment 1

1. I used HTML5 semantic elements such as `<header>`, `<nav>`, `<main>`, `<section>`, `<article>`, and `<footer>`, plus `<dl>`/`<dt>`/`<dd>` for the NPM and Program fields. Each major content block (Profile, Education, Experience, Hobbies) is wrapped in its own `<section>` with an id, while repeating items inside them (one education entry, one experience card, one hobby card) are wrapped in `<article>` since each one stands on its own as a piece of content. This kept the HTML readable without relying on class-only `<div>`s, made CSS selectors per section straightforward (e.g. `.education`, `.experience-grid`), and gave the nav anchors (`#education`, `#experience`, `#hobbies`) meaning on their own. It also makes the page friendlier to screen readers since landmarks like `<nav>` and `<main>` are explicit.

2. The biggest challenge was the Profile section, which uses a 2-column CSS Grid (`grid-template-areas` for identity, photo, and details) - shrinking it straight down to mobile width made the photo dominate the screen. I solved this by reordering the layout inside a media query (name/kicker first, then photo, then details/bio), since the name is the most important thing to see when quickly scrolling on a phone, while the photo gets a `max-width` cap so it doesn't take over. For the three new sections (Education, Experience, Hobbies) I used `repeat(auto-fit, minmax(...))` on their grids instead of manual breakpoints, so the number of columns adjusts on its own without extra breakpoints per section.

3. Since all the content (education history, experience, hobbies) is hardcoded directly into the HTML, any small change - adding one more organization, for example - means editing the markup and redeploying instead of just filling out a form or admin panel. There's also no structured storage for the data (e.g. to filter projects/skills by technology), and the contact "form" is still just a `mailto:` link since there's no database to store incoming messages. For the next iteration, I'd like to move Education, Experience, and eventually Projects/Skills into Django models (ORM + database) so they can be managed through the Django admin without touching the HTML every time, and eventually add things like a project filter or a contact form that actually persists submissions.

## AI Usage

I used an AI coding assistant (Claude Code) to help write the HTML markup and CSS for the new sections (Education, Experience, Hobbies), and to help debug two Django configuration issues found while testing the site locally (`TEMPLATES` dirs and `STATICFILES_DIRS` misconfiguration that broke the page and the static files). All content in the sections (education history, experience, hobbies, contact info) and the reflection answers above are my own.
