#!/usr/bin/env python3
"""Offscreen preview of the theme on mock Jellyfin pages.

Loads Jellyfin web's real stylesheets (from a local jellyfin-web install) plus
sepia-paper.css into static pages built from Jellyfin's own templates, and
saves screenshots. It's a mock — no server, no login — for quick visual checks.

usage: QT_QPA_PLATFORM=offscreen python3 dev/preview.py OUTDIR [BACKDROP_IMAGE]
"""
import glob, os, sys
from PySide6.QtCore import QTimer, QUrl, QSize
from PySide6.QtWidgets import QApplication
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtWebEngineCore import QWebEngineSettings

HERE = os.path.dirname(os.path.abspath(__file__))
THEME = os.path.join(HERE, "..", "sepia-paper.css")
WEB = os.environ.get("JELLYFIN_WEB", "/usr/share/jellyfin/web")
OUT = os.path.abspath(sys.argv[1])
BACKDROP = sys.argv[2] if len(sys.argv) > 2 else ""
os.makedirs(OUT, exist_ok=True)


def poster(i, title):
    """an SVG data poster: tinted gradient + title, no outside images needed"""
    hues = [28, 200, 340, 140, 260, 10, 180, 50]
    h = hues[i % len(hues)]
    svg = (f"<svg xmlns='http://www.w3.org/2000/svg' width='300' height='450'>"
           f"<defs><linearGradient id='g' x1='0' y1='0' x2='0' y2='1'>"
           f"<stop offset='0' stop-color='hsl({h},35%,38%)'/><stop offset='1' stop-color='hsl({h},40%,14%)'/>"
           f"</linearGradient></defs><rect width='300' height='450' fill='url(%23g)'/>"
           f"<text x='24' y='400' font-family='Georgia' font-size='30' fill='white' opacity='.85'>{title}</text></svg>")
    return "data:image/svg+xml;utf8," + svg.replace("#", "%23").replace('"', "'")


def head(extra_class=""):
    css = sorted(glob.glob(os.path.join(WEB, "*.css")))
    links = "".join(f'<link rel="stylesheet" href="file://{c}">' for c in css)
    links += f'<link rel="stylesheet" href="file://{WEB}/themes/dark/theme.css">'
    links += f'<link rel="stylesheet" href="file://{os.path.abspath(THEME)}">'
    return (f'<!doctype html><html class="layout-desktop {extra_class}" dir="ltr"><head><meta charset="utf-8">'
            f'{links}</head><body class="force-scroll">'
            '<div class="backdropContainer"></div><div class="backgroundContainer"></div>')


def header(title, tabs=None, transparent=False):
    t = ""
    if tabs:
        btns = "".join(f'<button class="emby-tab-button emby-button{" emby-tab-button-active" if i == 0 else ""}">'
                       f'<div class="emby-button-foreground">{x}</div></button>' for i, x in enumerate(tabs))
        t = f'<div class="headerTabs sectionTabs"><div class="tabs-viewmenubar emby-tabs"><div class="emby-tabs-slider">{btns}</div></div></div>'
    cls = "semiTransparent" if transparent else "skinHeader-withBackground"
    icons = "".join(f'<button class="headerButton paper-icon-button-light"><span class="material-icons {n}"></span></button>'
                    for n in ("search", "cast", "person"))
    return (f'<div class="skinHeader focuscontainer-x {cls}"><div class="flex align-items-center flex-grow headerTop">'
            f'<div class="headerLeft"><button class="headerButton headerButtonLeft paper-icon-button-light"><span class="material-icons menu"></span></button>'
            f'<h3 class="pageTitle">{title}</h3></div><div class="headerRight">{icons}</div></div>{t}</div>')


def card(i, title, sub, progress=None):
    bar = (f'<div class="itemProgressBar"><div class="itemProgressBarForeground" style="width:{progress}%"></div></div>'
           if progress else "")
    return (f'<div class="card portraitCard card-hoverable" style="width:12.5em"><div class="cardBox cardBox-bottompadded">'
            f'<div class="cardScalable"><div class="cardPadder cardPadder-portrait"></div>'
            f'<div class="cardImageContainer coveredImage cardContent" style="background-image:url(&quot;{poster(i, title)}&quot;)">'
            f'{bar}</div></div><div class="cardFooter"><div class="cardText cardTextCentered cardText-first">{title}</div>'
            f'<div class="cardText cardTextCentered cardText-secondary">{sub}</div></div></div></div>')


TITLES = ["Night Train", "The Lighthouse", "Paper Moon", "Harbour", "Saltwater", "Old Maps", "Winter Light", "Atlas"]


def thumb(i, title):
    """a wide SVG 'episode still'"""
    hues = [28, 200, 340, 140, 260, 10, 180, 50]
    h = hues[i % len(hues)]
    svg = (f"<svg xmlns='http://www.w3.org/2000/svg' width='480' height='270'>"
           f"<defs><linearGradient id='g' x1='0' y1='0' x2='1' y2='1'>"
           f"<stop offset='0' stop-color='hsl({h},30%,42%)'/><stop offset='1' stop-color='hsl({(h + 40) % 360},35%,16%)'/>"
           f"</linearGradient></defs><rect width='480' height='270' fill='url(%23g)'/>"
           f"<circle cx='{120 + i * 37 % 260}' cy='110' r='46' fill='white' opacity='.12'/></svg>")
    return "data:image/svg+xml;utf8," + svg.replace("#", "%23").replace('"', "'")


def jcard(kind, i, title, sub, progress=None):
    """card markup as Jellyfin's cardBuilder writes it"""
    pad = {"overflowPortraitCard": "150%", "portraitCard": "150%", "overflowBackdropCard": "56.25%",
           "overflowSmallBackdropCard": "56.25%"}[kind]
    img = poster(i, title) if "ortrait" in kind else thumb(i, title)
    bar = (f'<div class="innerCardFooter fullInnerCardFooter innerCardFooterClear"><div class="itemProgressBar">'
           f'<div class="itemProgressBarForeground" style="width:{progress}%"></div></div></div>' if progress else "")
    return (f'<div class="card {kind} card-hoverable card-withuserdata"><div class="cardBox cardBox-bottompadded">'
            f'<div class="cardScalable"><div class="cardPadder cardPadder-{kind.replace("Card", "")}" style="padding-bottom:{pad}"></div>'
            f'<a class="cardImageContainer coveredImage cardContent itemAction" style="background-image:url(&quot;{img}&quot;)">{bar}</a>'
            f'<div class="cardOverlayContainer itemAction"></div></div>'
            f'<div class="cardText cardTextCentered cardText-first"><bdi>{title}</bdi></div>'
            f'<div class="cardText cardTextCentered cardText-secondary"><bdi>{sub}</bdi></div></div></div>')


MOVIES = ["Night Train", "The Lighthouse", "Paper Moon", "Harbour", "Saltwater", "Old Maps", "Winter Light", "Atlas",
          "Low Tide", "The Orchard", "Glass Rivers", "Small Hours", "Northbound", "Inkwell"]
SHOWS = ["The Keepers", "Ferryman", "Quiet Street", "Marginalia", "Second Draft", "Field Notes", "Tidewater",
         "The Archive", "Long Division", "Overcast", "Postmark", "Hinterland"]


def section(i, title, cards, link=False):
    if link:
        head = (f'<div class="sectionTitleContainer sectionTitleContainer-cards padded-left">'
                f'<a is="emby-linkbutton" class="more button-flat button-flat-mini sectionTitleTextButton emby-button">'
                f'<h2 class="sectionTitle sectionTitle-cards">{title}</h2><span class="material-icons chevron_right"></span></a></div>')
    else:
        head = f'<h2 class="sectionTitle sectionTitle-cards padded-left">{title}</h2>'
    return (f'<div class="verticalSection section{i}">{head}'
            f'<div is="emby-scroller" class="padded-top-focusscale padded-bottom-focusscale emby-scroller">'
            f'<div is="emby-itemscontainer" class="itemsContainer scrollSlider focuscontainer-x" style="display:flex;white-space:nowrap">'
            f'{cards}</div></div></div>')


def home(buttons=False):
    if buttons:
        icons = [("Movies", "movie"), ("Shows", "tv"), ("Music", "library_music"), ("Collections", "folder")]
        lib = ('<div class="verticalSection verticalSection-extrabottompadding section0">'
               '<h2 class="sectionTitle sectionTitle-cards padded-left">My Media</h2>'
               '<div class="homeLibraryButtonContainer itemsContainer padded-left padded-right vertical-wrap focuscontainer-x">'
               + "".join(f'<a is="emby-linkbutton" class="raised homeLibraryButton emby-button"><span class="material-icons homeLibraryIcon {ic}"></span>'
                         f'<span class="homeLibraryText">{n}</span></a>' for n, ic in icons) + '</div></div>')
    else:
        lib = section(0, "My Media", "".join(jcard("overflowSmallBackdropCard", i, n, "") for i, n in
                                             enumerate(["Movies", "Shows", "Music", "Collections"])))
    body = (lib
            + section(1, "Continue Watching", "".join(jcard("overflowBackdropCard", i + 1, n, s, p) for i, (n, s, p) in enumerate(
                [("The Keepers", "S2:E4 · Low Water", 62), ("Night Train", "2023", 35), ("Ferryman", "S1:E7 · Crossings", 80),
                 ("Paper Moon", "2021", 18), ("Marginalia", "S3:E1 · Footnotes", 47)])))
            + section(2, "Next Up", "".join(jcard("overflowBackdropCard", i + 4, n, s) for i, (n, s) in enumerate(
                [("Quiet Street", "S1:E3 · Number Nine"), ("Second Draft", "S2:E1 · Revisions"), ("Field Notes", "S1:E9 · Moss"),
                 ("Tidewater", "S4:E2 · Ebb"), ("The Archive", "S1:E5 · Index")])), link=True)
            + section(3, "Latest Movies", "".join(jcard("overflowPortraitCard", i, n, str(2026 - i % 4)) for i, n in enumerate(MOVIES)), link=True)
            + section(4, "Latest Shows", "".join(jcard("overflowPortraitCard", i + 3, n, str(2025 - i % 3)) for i, n in enumerate(SHOWS)), link=True))
    return (head() + header("", ["Home", "Favorites"]) +
            '<div class="mainAnimatedPages skinBody"><div class="mainAnimatedPage"><div style="height:3.7em"></div>'
            '<div id="indexPage" class="page homePage libraryPage allLibraryPage backdropPage pageWithAbsoluteTabs withTabs" style="padding-top:4.2em">'
            f'<div class="tabContent pageTabContent is-active" id="homeTab" data-index="0"><div class="sections homeSectionsContainer">{body}</div></div>'
            '</div></div></div></body></html>')


def library():
    cards = "".join(jcard("portraitCard", i, n, str(2026 - i % 5)) for i, n in enumerate((MOVIES + SHOWS) * 2))
    return (head() + header("Movies", ["Movies", "Suggestions", "Favorites", "Collections", "Genres"]) +
            '<div class="mainAnimatedPages skinBody"><div class="mainAnimatedPage"><div class="page libraryPage" style="padding-top:4.5em">'
            f'<div is="emby-itemscontainer" class="itemsContainer vertical-wrap centered padded-left padded-right" style="display:flex;flex-wrap:wrap">{cards}</div>'
            '</div></div></div></body></html>')


def details():
    """hand-built from Jellyfin 12.4's itemDetails template hierarchy"""
    bd = f' style="background-image:url(&quot;file://{BACKDROP}&quot;)"' if BACKDROP else ""
    btn = lambda cls, icon: (f'<button is="emby-button" type="button" class="button-flat {cls} detailButton emby-button">'
                             f'<div class="detailButton-content"><span class="material-icons detailButton-icon {icon}"></span></div></button>')
    buttons = btn("btnPlay", "play_arrow") + btn("btnPlayTrailer", "theaters") + btn("btnPlaystate", "check") + \
        btn("btnUserRating", "favorite") + btn("btnMoreCommands", "more_vert")
    over = ("A retired lighthouse keeper returns to the island he left thirty years ago, where the tides, "
            "an unfinished letter and an old friend are still waiting for him. Slow, salt-bitten and quietly funny, "
            "it is a film about the things we keep meaning to say.")
    cast = "".join(card(i, t, "as Someone") for i, t in enumerate(["Ada Lind", "Tomas Berg", "Mira Holt", "Jon Ash", "Eli Varga", "Nora Quill"]))
    similar = "".join(card(i + 2, t, "2023") for i, t in enumerate(TITLES[:6]))
    section = lambda title, cards: (f'<div class="verticalSection detailVerticalSection"><h2 class="sectionTitle sectionTitle-cards padded-right">{title}</h2>'
                                    f'<div class="padded-top-focusscale padded-bottom-focusscale no-padding"><div class="scrollSlider focuscontainer-x itemsContainer" style="display:flex;gap:.6em">{cards}</div></div></div>')
    page = f'''<div id="itemDetailPage" data-role="page" class="page libraryPage itemDetailPage noSecondaryNavPage selfBackdropPage">
<div id="itemBackdrop" class="itemBackdrop"{bd}></div><div class="detailLogo"></div>
<div class="detailPageWrapperContainer"><div class="detailPagePrimaryContainer">
 <div class="detailImageContainer hide-mobile"><div class="card backdropCard"><div class="cardBox"><div class="cardScalable"><div class="cardPadder cardPadder-portrait"></div><div class="cardImageContainer coveredImage" style="background-image:url(&quot;{poster(3, "Saltwater")}&quot;)"></div></div></div></div></div>
 <div class="detailRibbon padded-left padded-right"><div class="infoWrapper"><div class="nameContainer"><h1 class="itemName infoText parentNameLast">Saltwater</h1></div>
  <div class="itemMiscInfo itemMiscInfo-primary" style="margin-bottom:.6em"><div class="mediaInfoItem">2024</div><div class="mediaInfoItem mediaInfoText mediaInfoOfficialRating">PG-13</div><div class="mediaInfoItem">1h 52m</div><div class="starRatingContainer mediaInfoItem"><span class="material-icons starIcon star"></span>7.6</div><div class="mediaInfoItem">Ends at 23:41</div></div>
  <div class="itemMiscInfo itemMiscInfo-secondary" style="margin-bottom:.6em"></div></div>
  <div class="mainDetailButtons focuscontainer-x">{buttons}</div></div>
 <div class="detailPagePrimaryContent padded-right"><div class="detailSection">
  <div class="detailSectionContent"><h3 class="tagline">Some currents bring you home.</h3><p class="overview itemOverview">{over}</p></div>
  <div class="itemDetailsGroup"><div class="detailsGroupItem genresGroup"><div class="genresLabel label">Genres</div><div class="genres content focuscontainer-x"><a href="#">Drama</a>, <a href="#">Mystery</a></div></div>
   <div class="detailsGroupItem directorsGroup"><div class="directorsLabel label">Director</div><div class="directors content"><a href="#">Ilse Marr</a></div></div></div>
 </div></div></div>
<div class="detailPageSecondaryContainer padded-left padded-bottom-page"><div class="detailPageContent">{section("Cast &amp; Crew", cast)}{section("More Like This", similar)}</div></div>
</div></div>'''
    return (head() + header("", transparent=True) +
            f'<div class="mainAnimatedPages skinBody"><div class="mainAnimatedPage">{page}</div></div></body></html>')


def dialog():
    return (head() + header("Settings", ["Profile", "Display", "Playback"]) +
            '<div class="mainAnimatedPages skinBody"><div class="mainAnimatedPage"><div class="page libraryPage" style="padding:6em 3.3vw">'
            '<h2 class="sectionTitle">Display</h2>'
            '<div class="inputContainer" style="max-width:30em"><label class="inputLabel inputLabelUnfocused">Display language</label>'
            '<input is="emby-input" class="emby-input" value="English"></div>'
            '<div class="selectContainer" style="max-width:30em"><label class="selectLabel">Theme</label>'
            '<select is="emby-select" class="emby-select-withcolor emby-select"><option>Dark</option></select></div>'
            '<label class="emby-checkbox-label"><input type="checkbox" is="emby-checkbox" class="emby-checkbox" checked>'
            '<span class="checkboxLabel">Enable backdrops</span><span class="checkboxOutline"><span class="material-icons checkboxIcon checkboxIcon-checked check"></span></span></label>'
            '<div style="margin-top:2em;display:flex;gap:.6em"><button is="emby-button" class="raised button-submit emby-button"><span>Save</span></button>'
            '<button is="emby-button" class="raised emby-button"><span>Cancel</span></button></div>'
            '</div></div></div></body></html>')


PAGES = [("home", home(), 0), ("home-buttons", home(True), 0), ("library", library(), 0), ("details", details(), 0), ("details-scrolled", details(), 760), ("settings", dialog(), 0)]

app = QApplication(sys.argv)
view = QWebEngineView()
view.settings().setAttribute(QWebEngineSettings.WebAttribute.LocalContentCanAccessFileUrls, True)
view.settings().setAttribute(QWebEngineSettings.WebAttribute.LocalContentCanAccessRemoteUrls, True)
view.resize(QSize(1920, 1080))
view.show()
queue = list(PAGES)


def next_page():
    if not queue:
        app.quit()
        return
    name, html, scroll = queue[0]
    path = os.path.join(OUT, f"{name}.html")
    open(path, "w").write(html)
    view.load(QUrl.fromLocalFile(path))


def loaded(ok):
    name, _, scroll = queue[0]

    def shoot():
        view.grab().save(os.path.join(OUT, f"{name}.png"))
        queue.pop(0)
        next_page()
    view.page().runJavaScript(f"window.scrollTo(0,{scroll})")
    QTimer.singleShot(2500, shoot)


view.loadFinished.connect(loaded)
next_page()
app.exec()
