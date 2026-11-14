from pathlib import Path
from xml.sax.saxutils import escape

from piggy import ASSIGNMENT_ROUTE, MEDIA_ROUTE, AssignmentTemplate, Visibility
from piggy.utils import lru_cache_wrapper


def _walk_pages(segment: dict, path: str = "", include_unlisted: bool = False):
    for name, page in segment.items():
        page_path = f"{path}/{name}".strip("/")
        meta = page.get("meta", {})
        visibility = Visibility.from_value(meta.get("visibility"))
        if visibility is Visibility.PRIVATE:
            continue
        if include_unlisted or visibility is not Visibility.UNLISTED:
            yield page_path

        data = page.get("data", {})
        if len(page_path.split("/")) == AssignmentTemplate.ASSIGNMENT.index:
            for language, translation in page.get("translation_meta", {}).items():
                translation_visibility = Visibility.from_value(translation.get("visibility"))
                if translation_visibility is not Visibility.PRIVATE and (
                    include_unlisted or translation_visibility is not Visibility.UNLISTED
                ):
                    yield f"{page_path}/lang/{language}"
            continue

        if data and (include_unlisted or visibility is not Visibility.UNLISTED):
            yield from _walk_pages(data, page_path, include_unlisted)


def get_sitemap_paths(piggymap: dict, *, include_unlisted: bool = False) -> list[str]:
    """Return sorted application paths represented by the piggymap."""
    paths = {"/", f"/{ASSIGNMENT_ROUTE}"}
    paths.update(f"/{ASSIGNMENT_ROUTE}/{path}" for path in _walk_pages(piggymap, include_unlisted=include_unlisted))
    return sorted(paths)


@lru_cache_wrapper
def get_cached_sitemap_paths(piggymap: dict, *, include_unlisted: bool = False) -> list[str]:
    """Return cached sitemap paths for an immutable piggymap."""
    return get_sitemap_paths(piggymap, include_unlisted=include_unlisted)


def get_shortlink_paths(shortlink_map: dict, paths: list[str]) -> list[str]:
    """Return the shortlink paths (/s/<code>) of the given page paths."""
    paths = set(paths)
    return sorted(f"/s/{code}" for code, page in shortlink_map.items() if page["target"] in paths)


def _walk_folders(segment: dict, path: str = ""):
    for name, page in segment.items():
        meta = page.get("meta", {})
        if "system_path" not in meta or Visibility.from_value(meta.get("visibility")) is Visibility.PRIVATE:
            continue
        folder = f"{path}/{name}".strip("/")
        yield folder, Path(meta["system_path"])
        yield from _walk_folders(page.get("data", {}), folder)


def get_static_files(piggymap: dict) -> list[tuple[str, Path]]:
    """Return (url path, file) pairs for the media and attachments of every folder that isn't private."""
    files = []
    for folder, system_path in _walk_folders(piggymap):
        for route, subfolder in ((MEDIA_ROUTE, "media"), (ASSIGNMENT_ROUTE, "attachments")):
            root = system_path / subfolder
            for file in sorted(root.rglob("*")):
                if file.is_file():
                    files.append((f"/{route}/{folder}/{subfolder}/{file.relative_to(root).as_posix()}", file))
    return files


def render_sitemap_xml(paths: list[str], base_url: str) -> str:
    """Render paths as an XML sitemap."""
    urls = "\n".join(f"  <url><loc>{escape(base_url.rstrip('/') + path)}</loc></url>" for path in paths)
    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        f"{urls}\n"
        "</urlset>\n"
    )


def render_internal_sitemap(paths: list[str]) -> str:
    """Render paths as newline-delimited URLs for the static scraper."""
    return "\n".join(paths) + "\n"


def render_internal_files(files: list[tuple[str, Path]]) -> str:
    """Render (url path, file) pairs as tab separated url paths and absolute file paths for the static scraper."""
    return "".join(f"{path}\t{file.resolve()}\n" for path, file in files)
