#!/usr/bin/env python3
"""
Gerador de blog da Chapter.

Uso:
    python3 gerar_blog.py

Le todos os arquivos .md em posts/, gera:
  - blog/index.html         (lista de posts)
  - blog/<slug>.html        (um HTML por post)
  - blog/style.css          (copiado de style.css)

Cada post e um arquivo Markdown com frontmatter no topo:

    ---
    title: Titulo do post
    date: 2026-07-23
    eyebrow: Categoria curta (opcional)
    excerpt: Uma ou duas frases de resumo, usadas na listagem.
    ---

    Corpo do post em Markdown normal a partir daqui.

O nome do arquivo (sem .md) vira a URL do post.
Exemplo: posts/o-que-e-geo.md -> blog/o-que-e-geo.html
"""

import shutil
from pathlib import Path
from datetime import datetime

import frontmatter
import markdown

SOURCE_DIR = Path(__file__).parent
POSTS_DIR = SOURCE_DIR / "posts"
STYLE_FILE = SOURCE_DIR / "style.css"
OUTPUT_DIR = SOURCE_DIR.parent / "blog"  # ../blog relative to blog-source/
SITE_ROOT = SOURCE_DIR.parent            # pasta onde ficam index.html, robots.txt, sitemap.xml
BASE_URL = "https://chaptercom.com.br"

SITE_NAME = "chapter."
SITE_URL_HOME = "../index.html"   # ajuste se a estrutura de pastas final for diferente
BLOG_TITLE = "Notas da Chapter"
BLOG_LEDE = "Reflexões sobre narrativa, imprensa e o jeito como as IAs estão aprendendo a resumir empresas."

MESES_PT = [
    "janeiro", "fevereiro", "março", "abril", "maio", "junho",
    "julho", "agosto", "setembro", "outubro", "novembro", "dezembro",
]


def formatar_data(data_obj):
    return f"{data_obj.day} de {MESES_PT[data_obj.month - 1]} de {data_obj.year}"


def carregar_posts():
    posts = []
    for md_file in sorted(POSTS_DIR.glob("*.md")):
        post = frontmatter.load(md_file)
        slug = md_file.stem
        data = post.get("date")
        if isinstance(data, str):
            data = datetime.strptime(data, "%Y-%m-%d").date()
        posts.append({
            "slug": slug,
            "title": post.get("title", slug),
            "eyebrow": post.get("eyebrow", "Notas da Chapter"),
            "excerpt": post.get("excerpt", ""),
            "date": data,
            "body_md": post.content,
            "body_html": markdown.markdown(post.content, extensions=["extra"]),
        })
    # mais recente primeiro
    posts.sort(key=lambda p: p["date"], reverse=True)
    return posts


def render_header(depth_prefix=""):
    return f"""<header class="blog-header">
  <div class="wrap">
    <a href="{depth_prefix}../index.html" class="wordmark">chapter<span class="dot">.</span></a>
    <nav><a href="{depth_prefix}index.html">Notas</a></nav>
  </div>
</header>"""


def render_footer():
    return """<footer class="blog-footer">
  <div class="wrap">
    <div class="wordmark">chapter<span class="dot">.</span></div>
    <div class="foot-tag">Uma narrativa, múltiplos canais. Do humano às LLMs.</div>
  </div>
</footer>"""


def render_index(posts):
    items = []
    for p in posts:
        items.append(f"""    <div class="post-item">
      <div class="post-date">{formatar_data(p['date'])}</div>
      <h2><a href="{p['slug']}.html">{p['title']}</a></h2>
      <p class="excerpt">{p['excerpt']}</p>
    </div>""")
    items_html = "\n".join(items)

    return f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{BLOG_TITLE} — {SITE_NAME}</title>
<meta name="description" content="{BLOG_LEDE}">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Urbanist:ital,wght@0,400;0,500;0,600;0,700;0,800;1,500;1,600;1,700&family=Hanken+Grotesk:wght@800&display=swap" rel="stylesheet">
<link rel="stylesheet" href="style.css">
</head>
<body>

{render_header()}

<main class="blog-index">
  <div class="wrap">
    <h1>{BLOG_TITLE}</h1>
    <p class="lede">{BLOG_LEDE}</p>
    <div class="post-list">
{items_html}
    </div>
  </div>
</main>

{render_footer()}

</body>
</html>
"""


def render_post(p):
    return f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{p['title']} — {SITE_NAME}</title>
<meta name="description" content="{p['excerpt']}">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Urbanist:ital,wght@0,400;0,500;0,600;0,700;0,800;1,500;1,600;1,700&family=Hanken+Grotesk:wght@800&display=swap" rel="stylesheet">
<link rel="stylesheet" href="style.css">
</head>
<body>

{render_header()}

<main class="post">
  <div class="wrap">
    <a href="index.html" class="back-link">← Notas da Chapter</a>
    <span class="post-eyebrow">{p['eyebrow']}</span>
    <h1>{p['title']}</h1>
    <div class="post-meta">{formatar_data(p['date'])}</div>
    <div class="post-body">
{p['body_html']}
    </div>
  </div>
</main>

{render_footer()}

</body>
</html>
"""


def render_sitemap(posts):
    urls = [
        (f"{BASE_URL}/", "1.0"),
        (f"{BASE_URL}/blog/", "0.8"),
    ]
    for p in posts:
        urls.append((f"{BASE_URL}/blog/{p['slug']}.html", "0.6"))

    entries = "\n".join(
        f'  <url>\n    <loc>{url}</loc>\n    <changefreq>monthly</changefreq>\n    <priority>{priority}</priority>\n  </url>'
        for url, priority in urls
    )
    return f'''<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
{entries}
</urlset>
'''


def main():
    OUTPUT_DIR.mkdir(exist_ok=True)
    posts = carregar_posts()

    (OUTPUT_DIR / "index.html").write_text(render_index(posts), encoding="utf-8")
    for p in posts:
        (OUTPUT_DIR / f"{p['slug']}.html").write_text(render_post(p), encoding="utf-8")

    shutil.copy(STYLE_FILE, OUTPUT_DIR / "style.css")

    sitemap_path = SITE_ROOT / "sitemap.xml"
    sitemap_path.write_text(render_sitemap(posts), encoding="utf-8")

    print(f"OK — {len(posts)} post(s) gerado(s) em {OUTPUT_DIR}/")
    for p in posts:
        print(f"  - {p['slug']}.html  ({formatar_data(p['date'])})")
    print(f"sitemap.xml atualizado em {sitemap_path} (home + blog + {len(posts)} post(s))")


if __name__ == "__main__":
    main()
