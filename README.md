# Personal Portfolio - Karyn Isabelle Dexter

Name: Karyn Isabelle Dexter

NPM: 2506656860

Class: PBP A

## About This Project

A personal portfolio website built with Django, following the MVT (Model-View-Template) pattern. It has four pages, each backed by its own model/view/template and reachable from the navbar:

- **Profile** (`/`) - name, NPM, photo, and a short bio.
- **Education** (`/education/`) - education history as a timeline, pulled from the `Education` model.
- **Experience** (`/experience/`) - organizational/committee experience as a card grid, pulled from the `Experience` model.
- **Hobbies** (`/hobbies/`) - everyday hobbies as an icon grid, pulled from the `Hobby` model.

Every list page shows its data with a Django Template Language `{% for %}` loop and falls back to an empty-state message when there's no data yet - nothing in those lists is hardcoded in the HTML.

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

### Tutorial & Assignment 2
- Implemented the MVT pattern: created the `main` app, an `Experience` model, and pinned Django to `~=5.2` for PWS/PostgreSQL compatibility.
- Moved the profile data (name, NPM, program, bio) from hardcoded HTML into view context (`show_main`), and built a database-backed Experience page (`show_experience`, `/experience/`) with a `{% for %}` loop and an empty-state message. Added 6 unit tests covering the profile page, the experience page, the model, and a 404 case.
- For Assignment 2, applied the same MVT pattern to two more sections: added `Education` and `Hobby` models, `show_education`/`show_hobbies` views, and their own pages at `/education/` and `/hobbies/`, each reachable from the navbar via `{% url %}` and backed by 7 more unit tests (3-4 per page: accessible + correct template, data shown, empty state).
- Removed the old hardcoded Education/Experience/Hobbies sections from the profile page (`index.html`) now that each has its own database-backed page, and cleaned up the CSS rules that were only used by those removed sections.

### Tutorial 3
- Introduced `templates/base.html` as the single skeleton (`{% load static %}`, the font/stylesheet links, the header/nav/theme-toggle, and the footer) and made every page (`index.html`, `experience.html`, `education.html`, `hobbies.html`) `{% extends "base.html" %}` instead of repeating that markup, so a single edit to the header or footer now applies everywhere.
- Added Create, Delete, and JSON data delivery for the `Experience` section: `ExperienceForm` (a `ModelForm` in `main/forms.py`), a `/experience/add/` form page, a delete button wired to `delete_experience` behind a confirmation popover, and a `/api/experience/` endpoint (`get_experience_json`) that serializes the queryset to JSON and supports `?title=` filtering. `show_experience` now fetches from that same JSON endpoint and deserializes it before rendering, instead of querying the model directly.

### Tugas 3
- Applied the same Create/Delete/JSON pattern to the `Education` section, and additionally implemented **Update**: `EducationForm` (`main/forms.py`), a shared `education_form.html` used for both `/education/add/` and `/education/<id>/edit/` (the edit view fetches the row by its UUID with `get_object_or_404` and binds the form to that `instance` before saving), a delete button per timeline entry, and a `/api/education/` JSON endpoint (`get_education_json`, filterable by `?institution=`) that `show_education` now reads and deserializes before rendering the timeline.
- Refactored the CSS/markup that Tutorial 3 had written specifically for Experience (`.experience-header`, `.experience-search`, `.experience-delete-modal`, ...) into generic, reusable classes (`.section-header`, `.search-bar`, `.delete-modal`, `.card-actions`/`.item-actions`, `.data-form`) shared by both the Experience and Education pages, since both sections now have an identical add/search/edit/delete UI shape.

## Reflection Questions

### Assignment 1

1. I used HTML5 semantic elements such as `<header>`, `<nav>`, `<main>`, `<section>`, `<article>`, and `<footer>`, plus `<dl>`/`<dt>`/`<dd>` for the NPM and Program fields. Each major content block (Profile, Education, Experience, Hobbies) is wrapped in its own `<section>` with an id, while repeating items inside them (one education entry, one experience card, one hobby card) are wrapped in `<article>` since each one stands on its own as a piece of content. This kept the HTML readable without relying on class-only `<div>`s, made CSS selectors per section straightforward (e.g. `.education`, `.experience-grid`), and gave the nav anchors (`#education`, `#experience`, `#hobbies`) meaning on their own. It also makes the page friendlier to screen readers since landmarks like `<nav>` and `<main>` are explicit.

2. The biggest challenge was the Profile section, which uses a 2-column CSS Grid (`grid-template-areas` for identity, photo, and details) - shrinking it straight down to mobile width made the photo dominate the screen. I solved this by reordering the layout inside a media query (name/kicker first, then photo, then details/bio), since the name is the most important thing to see when quickly scrolling on a phone, while the photo gets a `max-width` cap so it doesn't take over. For the three new sections (Education, Experience, Hobbies) I used `repeat(auto-fit, minmax(...))` on their grids instead of manual breakpoints, so the number of columns adjusts on its own without extra breakpoints per section.

3. Since all the content (education history, experience, hobbies) is hardcoded directly into the HTML, any small change - adding one more organization, for example - means editing the markup and redeploying instead of just filling out a form or admin panel. There's also no structured storage for the data (e.g. to filter projects/skills by technology), and the contact "form" is still just a `mailto:` link since there's no database to store incoming messages. For the next iteration, I'd like to move Education, Experience, and eventually Projects/Skills into Django models (ORM + database) so they can be managed through the Django admin without touching the HTML every time, and eventually add things like a project filter or a contact form that actually persists submissions.

### Assignment 2

1. When a user opens a page like `/education/`, the browser sends a GET request that first hits `portofolio/urls.py` (the project-level URLconf). There, the empty prefix `""` is routed with `include("main.urls")`, handing the rest of the path to `main/urls.py` (the app-level URLconf), which matches `"education/"` to the `show_education` view. That view is the only place allowed to talk to the `Education` model - it calls `Education.objects.all()` to get every row currently in the database, puts the result into a context dictionary along with `name`, and calls `render(request, "education.html", context)`. Django's template engine then loads `education.html`, replaces `{{ name }}`, and loops over `education_list` with `{% for edu in education_list %}` to expand one `<article>` per row (or shows the `{% empty %}` message if there are none), and the resulting HTML is sent back as the response. So: `urls.py` (project) narrows the request down to an app, `urls.py` (app) narrows it down to a view, the view is the only layer that touches the `Model`, and the `Template` is the only layer that decides how that data is displayed - each layer only needs to know about the one right next to it.

2. Storing this data in a model instead of writing it into the template means the content and the presentation are no longer welded together. Adding a new education entry or hobby becomes "create one row" (through the Django admin, a script, or a form later on) instead of editing and redeploying a template file, and the same `{% for %}` loop picks it up automatically without anyone touching HTML. It also means the data can be validated by field type, ordered (like `ordering = ['-started_at']` on `Education`), queried, or reused across multiple pages consistently, and a typo or formatting fix only has to happen once, in the data, instead of in every hardcoded copy scattered through the templates. This is also why removing the old hardcoded Education/Experience/Hobbies sections from the profile page was safe once their DB-backed pages existed - the actual data now lives in one place (the database), not duplicated between `index.html` and the new pages.

3. `makemigrations` compares the current state of `models.py` against the last known state (recorded in the `migrations/` folder) and writes a new migration file describing what changed - it only generates instructions, it never touches the actual database. `migrate` is the step that applies those instructions to the database, creating or altering tables so they match the models. A concrete example from this assignment: after adding the `Education` and `Hobby` classes to `main/models.py`, running `python manage.py makemigrations` generated `main/migrations/0002_education_hobby.py` (a file describing "create these two new tables with these fields") - but the corresponding tables did not exist in `db.sqlite3` yet at that point. Only after running `python manage.py migrate` did Django actually create them, which is what made `Education.objects.create(...)` and `Hobby.objects.create(...)` in the shell work without errors.

### Tugas 3

1. We use `ModelForm` instead of a hand-written HTML form because it derives the fields, widgets, and validation rules directly from the model, instead of me duplicating them. In `main/forms.py`, `EducationForm`'s `Meta.model = Education` means Django already knows `institution` is a `CharField` (so it renders a text input and enforces `max_length=255`) and `started_at`/`ended_at` are `DateField`s, without me writing that logic twice. If I wrote the form by hand, every time a field changed in `models.py` I'd also have to update the raw `<input>` markup and re-implement the validation the model already declares, and I'd have to manually read `request.POST`, construct the model instance, and call `.full_clean()` myself instead of just calling `form.is_valid()` and `form.save()`. `{% csrf_token %}` is required because Django's `CsrfViewMiddleware` blocks any unsafe request (POST/PUT/PATCH/DELETE) that doesn't carry a valid token tied to the current session. Without it, a malicious page on another site could trick a logged-in user's browser into silently submitting a request to one of my endpoints (say, `POST /education/<id>/delete/`) using that user's own session cookies - a Cross-Site Request Forgery. The token proves the request actually came from a form my server rendered, not from an attacker's page.

2. JSON is preferred over XML mainly because it is lighter and cheaper to parse. JSON has no closing tags to repeat, so the same data is consistently smaller in bytes than the XML equivalent, and it maps almost one-to-one onto the data structures JavaScript (and Python, and most other languages) already use - objects and arrays - so a JSON string becomes a native object with a single call (`JSON.parse()` in JS, or `serializers.deserialize("json", ...)` in this project's Django code), whereas XML needs a separate DOM-parsing step plus manual traversal (`getElementsByTagName`, XPath) to pull values back out. That combination of a smaller payload and a near-zero-effort parse-to-object step is why JSON is now the default format for REST APIs, while XML is mostly seen in older or more document-oriented systems (like SOAP or RSS) where its stricter schema/validation story still matters.

3. When `/api/education/` is requested, `get_education_json` first builds a queryset (`Education.objects.all()`, narrowed with `.filter(institution__icontains=...)` if a search term was given), then calls `serializers.serialize("json", education)` and wraps the result in an `HttpResponse` with `content_type="application/json"`. A `QuerySet` holds live `Education` model instances - Python objects - which can't be sent over HTTP as-is, since HTTP only carries bytes/text; serialization is the step that walks each instance's fields and turns them into a flat, language-agnostic JSON string (a list of `{"model", "pk", "fields"}` entries) that any client - a browser, Postman, another backend - can read regardless of what language it's written in. On the display side, `show_education` calls that same `get_education_json` view internally, runs `serializers.deserialize("json", ...)` on its `.content`, pulls the real `Education` objects back out with `[e.object for e in ...]`, and hands that list to `education.html`'s `{% for edu in education_list %}` loop. So the page is always rendering exactly what the JSON endpoint would return, instead of the API and the page silently drifting apart if someone edited one but not the other.

## AI Usage

I used an AI coding assistant (Claude Code) to help write the HTML markup and CSS for the new sections (Education, Experience, Hobbies), to help debug two Django configuration issues found while testing the site locally (`TEMPLATES` dirs and `STATICFILES_DIRS` misconfiguration that broke the page and the static files), to help implement the MVT layer for Assignment 2 (the `main` app, the `Experience`/`Education`/`Hobby` models, views, templates, and unit tests), to build the `base.html` skeleton plus the Experience Create/Delete/JSON flow for Tutorial 3, and to implement the Education Create/Update/Delete/JSON flow and the accompanying CSS refactor for Tugas 3. All content in the sections (education history, experience, hobbies, contact info) and the reflection answers above are my own.
