from __future__ import annotations

import re
import logging
from typing import List
from datetime import datetime
from urllib.parse import urlencode
from urllib.request import urlretrieve
from datetime import datetime, timedelta, timezone
from calendar import timegm
import os
import time
import feedparser
from arxiv.utils import _classname


logger = logging.getLogger(__name__)
_DEFAULT_TIME = datetime.min


class Author(object):
    """
    A light inner class for representing a result's authors.
    """

    name: str
    """The author's name."""

    def __init__(self, name: str):
        """
        Constructs an `Author` with the specified name.

        In most cases, prefer using `Author._from_feed_author` to parsing
        and constructing `Author`s yourself.
        """
        self.name = name

    def _from_feed_author(feed_author: feedparser.FeedParserDict) -> 'Author':
        """
        Constructs an `Author` with the name specified in an author object
        from a feed entry.

        See usage in `Result._from_feed_entry`.
        """
        return Author(feed_author.name)

    def __str__(self) -> str:
        return self.name

    def __repr__(self) -> str:
        return "{}({})".format(_classname(self), repr(self.name))

    def __eq__(self, other) -> bool:
        if isinstance(other, Author):
            return self.name == other.name
        return False


class Link(object):
    """
    A light inner class for representing a result's links.
    """

    href: str
    """The link's `href` attribute."""
    title: str
    """The link's title."""
    rel: str
    """The link's relationship to the `Result`."""
    content_type: str
    """The link's HTTP content type."""

    def __init__(
        self,
        href: str,
        title: str = None,
        rel: str = None,
        content_type: str = None,
    ):
        """
        Constructs a `Link` with the specified link metadata.

        In most cases, prefer using `Link._from_feed_link` to parsing and
        constructing `Link`s yourself.
        """
        self.href = href
        self.title = title
        self.rel = rel
        self.content_type = content_type

    def _from_feed_link(feed_link: feedparser.FeedParserDict) -> 'Link':
        """
        Constructs a `Link` with link metadata specified in a link object
        from a feed entry.

        See usage in `Result._from_feed_entry`.
        """
        return Link(
            href=feed_link.href,
            title=feed_link.get("title"),
            rel=feed_link.get("rel"),
            content_type=feed_link.get("content_type"),
        )

    def __str__(self) -> str:
        return self.href

    def __repr__(self) -> str:
        return "{}({}, title={}, rel={}, content_type={})".format(
            _classname(self),
            repr(self.href),
            repr(self.title),
            repr(self.rel),
            repr(self.content_type),
        )

    def __eq__(self, other) -> bool:
        if isinstance(other, Link):
            return self.href == other.href
        return False


class MissingFieldError(Exception):
    """
    An error indicating an entry is unparseable because it lacks required
    fields.
    """

    missing_field: str
    """The required field missing from the would-be entry."""
    message: str
    """Message describing what caused this error."""

    def __init__(self, missing_field):
        self.missing_field = missing_field
        self.message = "Entry from arXiv missing required info"

    def __repr__(self) -> str:
        return "{}({})".format(_classname(self), repr(self.missing_field))


class Result(object):
    """
    An entry in an arXiv query results feed.

    See [the arXiv API User's Manual: Details of Atom Results
    Returned](https://arxiv.org/help/api/user-manual#_details_of_atom_results_returned).
    """

    entry_id: str
    """A url of the form `https://arxiv.org/abs/{id}`."""
    updated: datetime
    """When the result was last updated."""
    published: datetime
    """When the result was originally published."""
    title: str
    """The title of the result."""
    authors: List[Author]
    """The result's authors."""
    summary: str
    """The result abstract."""
    comment: str
    """The authors' comment if present."""
    journal_ref: str
    """A journal reference if present."""
    doi: str
    """A URL for the resolved DOI to an external resource if present."""
    primary_category: str
    """
    The result's primary arXiv category. See [arXiv: Category
    Taxonomy](https://arxiv.org/category_taxonomy).
    """
    categories: List[str]
    """
    All of the result's categories. See [arXiv: Category
    Taxonomy](https://arxiv.org/category_taxonomy).
    """
    links: List[Link]
    """Up to three URLs associated with this result."""
    pdf_url: str
    """The URL of a PDF version of this result if present among links."""
    _raw: feedparser.FeedParserDict
    """
    The raw feedparser result object if this Result was constructed with
    Result._from_feed_entry.
    """

    def __init__(
        self,
        entry_id: str,
        updated: datetime = _DEFAULT_TIME,
        published: datetime = _DEFAULT_TIME,
        title: str = "",
        authors: List[Author] = [],
        summary: str = "",
        comment: str = "",
        journal_ref: str = "",
        doi: str = "",
        primary_category: str = "",
        categories: List[str] = [],
        links: List[Link] = [],
        _raw: feedparser.FeedParserDict = None,
    ):
        """
        Constructs an arXiv search result item.

        In most cases, prefer using `Result._from_feed_entry` to parsing and
        constructing `Result`s yourself.
        """
        self.entry_id = entry_id
        self.updated = updated
        self.published = published
        self.title = title
        self.authors = authors
        self.summary = summary
        self.comment = comment
        self.journal_ref = journal_ref
        self.doi = doi
        self.primary_category = primary_category
        self.categories = categories
        self.links = links
        # Calculated members
        self.pdf_url = Result._get_pdf_url(links)
        # Debugging
        self._raw = _raw

    def _from_feed_entry(entry: feedparser.FeedParserDict) -> 'Result':
        """
        Converts a feedparser entry for an arXiv search result feed into a
        Result object.
        """
        if not hasattr(entry, "id"):
            raise Result.MissingFieldError("id")
        # Title attribute may be absent for certain titles. Defaulting to "0" as
        # it's the only title observed to cause this bug.
        # https://github.com/lukasschwab/arxiv.py/issues/71
        # title = entry.title if hasattr(entry, "title") else "0"
        title = "0"
        if hasattr(entry, "title"):
            title = entry.title
        else:
            logger.warning("Result %s is missing title attribute; defaulting to '0'", entry.id)
        return Result(
            entry_id=entry.id,
            updated=Result._to_datetime(entry.updated_parsed),
            published=Result._to_datetime(entry.published_parsed),
            title=re.sub(r"\s+", " ", title),
            authors=[Author._from_feed_author(a) for a in entry.authors],
            summary=entry.summary,
            comment=entry.get("arxiv_comment"),
            journal_ref=entry.get("arxiv_journal_ref"),
            doi=entry.get("arxiv_doi"),
            primary_category=entry.arxiv_primary_category.get("term"),
            categories=[tag.get("term") for tag in entry.tags],
            links=[Link._from_feed_link(link) for link in entry.links],
            _raw=entry,
        )

    def __str__(self) -> str:
        return self.entry_id

    def __repr__(self) -> str:
        return (
            "{}(entry_id={}, updated={}, published={}, title={}, authors={}, "
            "summary={}, comment={}, journal_ref={}, doi={}, "
            "primary_category={}, categories={}, links={})"
        ).format(
            _classname(self),
            repr(self.entry_id),
            repr(self.updated),
            repr(self.published),
            repr(self.title),
            repr(self.authors),
            repr(self.summary),
            repr(self.comment),
            repr(self.journal_ref),
            repr(self.doi),
            repr(self.primary_category),
            repr(self.categories),
            repr(self.links),
        )

    def __eq__(self, other) -> bool:
        if isinstance(other, Result):
            return self.entry_id == other.entry_id
        return False

    def get_short_id(self) -> str:
        """
        Returns the short ID for this result.

        + If the result URL is `"https://arxiv.org/abs/2107.05580v1"`,
        `result.get_short_id()` returns `2107.05580v1`.

        + If the result URL is `"https://arxiv.org/abs/quant-ph/0201082v1"`,
        `result.get_short_id()` returns `"quant-ph/0201082v1"` (the pre-March
        2007 arXiv identifier format).

        For an explanation of the difference between arXiv's legacy and current
        identifiers, see [Understanding the arXiv
        identifier](https://arxiv.org/help/arxiv_identifier).
        """
        return self.entry_id.split("arxiv.org/abs/")[-1]

    def _get_default_filename(self, extension: str = "pdf") -> str:
        """
        A default `to_filename` function for the extension given.
        """
        nonempty_title = self.title if self.title else "UNTITLED"
        return ".".join(
            [
                self.get_short_id().replace("/", "_"),
                re.sub(r"[^\w]", "_", nonempty_title),
                extension,
            ]
        )

    def download_pdf(self, dirpath: str = "./", filename: str = "") -> str:
        """
        Downloads the PDF for this result to the specified directory.

        The filename is generated by calling `to_filename(self)`.
        """
        if not filename:
            filename = self._get_default_filename()
        path = os.path.join(dirpath, filename)
        written_path, _ = urlretrieve(self.pdf_url, path)
        return written_path

    def download_source(self, dirpath: str = "./", filename: str = "") -> str:
        """
        Downloads the source tarfile for this result to the specified
        directory.

        The filename is generated by calling `to_filename(self)`.
        """
        if not filename:
            filename = self._get_default_filename("tar.gz")
        path = os.path.join(dirpath, filename)
        # Bodge: construct the source URL from the PDF URL.
        source_url = self.pdf_url.replace("/pdf/", "/src/")
        written_path, _ = urlretrieve(source_url, path)
        return written_path

    def _get_pdf_url(links: List[Link]) -> str:
        """
        Finds the PDF link among a result's links and returns its URL.

        Should only be called once for a given `Result`, in its constructor.
        After construction, the URL should be available in `Result.pdf_url`.
        """
        pdf_urls = [link.href for link in links if link.title == "pdf"]
        if len(pdf_urls) == 0:
            return None
        elif len(pdf_urls) > 1:
            logger.warning("Result has multiple PDF links; using %s", pdf_urls[0])
        return pdf_urls[0]

    def _to_datetime(ts: time.struct_time) -> datetime:
        """
        Converts a UTC time.struct_time into a time-zone-aware datetime.

        This will be replaced with feedparser functionality [when it becomes
        available](https://github.com/kurtmckee/feedparser/issues/212).
        """
        return datetime.fromtimestamp(timegm(ts), tz=timezone.utc)


