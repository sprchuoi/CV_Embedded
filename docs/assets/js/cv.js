/*
 * CV page behaviour: the Summary/Full view toggle, and live GitHub star counts.
 *
 *  1. The work history has two views -- the compact flow chart ("Summary", the
 *     default) and the full detail inline ("Full"). They are wired as tabs, so
 *     the keyboard works as well as the mouse (arrow keys move between them).
 *
 *  2. Every link to github.com/<owner>/<repo> gets its real star count from the
 *     GitHub API, cached in localStorage for six hours. Nothing on the CV
 *     depends on this: if GitHub is unreachable, rate-limited or slow, the link
 *     is simply left as it was.
 *
 * Node can load this file for testing (see the bottom and
 * tool/tests/test_cv_index.py); a browser never sees that branch.
 */
(function () {
	'use strict';

	/* --- GitHub link parsing ---------------------------------------------- */

	var GITHUB_REPO_RE =
		/^https?:\/\/github\.com\/([^\/?#]+)\/([^\/?#]+?)(?:\.git)?\/?(?:[?#].*)?$/;

	/**
	 * "https://github.com/owner/repo" -> "owner/repo".
	 * The bare profile, a deep link into a repo, or any other URL -> null.
	 */
	function repoFromHref(href) {
		var match = GITHUB_REPO_RE.exec(href || '');
		return match ? match[1] + '/' + match[2] : null;
	}

	/* --- Summary / Full ---------------------------------------------------- */

	function initViewToggle(section) {
		var tabs = section.querySelectorAll('[role="tab"]');
		var panels = section.querySelectorAll('[role="tabpanel"]');
		if (!tabs.length || !panels.length) {
			return;
		}

		function activate(tab) {
			for (var i = 0; i < tabs.length; i++) {
				var selected = tabs[i] === tab;
				tabs[i].classList.toggle('is-active', selected);
				tabs[i].setAttribute('aria-selected', selected ? 'true' : 'false');
				tabs[i].tabIndex = selected ? 0 : -1;
			}
			for (var j = 0; j < panels.length; j++) {
				panels[j].hidden = panels[j].id !== tab.getAttribute('aria-controls');
			}
		}

		for (var i = 0; i < tabs.length; i++) {
			(function (tab, index) {
				tab.addEventListener('click', function () {
					activate(tab);
				});
				tab.addEventListener('keydown', function (event) {
					var step = event.key === 'ArrowRight' ? 1
						: event.key === 'ArrowLeft' ? -1 : 0;
					if (!step) {
						return;
					}
					event.preventDefault();
					var next = tabs[(index + step + tabs.length) % tabs.length];
					activate(next);
					next.focus();
				});
			}(tabs[i], i));
		}
	}

	/* --- live star counts -------------------------------------------------- */

	var STARS_KEY = 'cv:github-stars:v1';
	var STARS_TTL = 6 * 60 * 60 * 1000; // six hours

	function readCache() {
		try {
			var raw = window.localStorage.getItem(STARS_KEY);
			return raw ? JSON.parse(raw) : {};
		} catch (err) {
			return {};
		}
	}

	function writeCache(cache) {
		try {
			window.localStorage.setItem(STARS_KEY, JSON.stringify(cache));
		} catch (err) {
			/* Private mode or a full quota: the badge still shows this visit. */
		}
	}

	function showStars(link, count) {
		var badge = link.nextElementSibling;
		if (!badge || !badge.classList || !badge.classList.contains('git-stars')) {
			badge = document.createElement('span');
			badge.className = 'git-stars';
			link.parentNode.insertBefore(badge, link.nextSibling);
		}
		badge.textContent = '\u2605 ' + count;
		badge.title = count + (count === 1 ? ' star' : ' stars') + ' on GitHub';
		if (count > 0) {
			badge.classList.add('has-stars');
		}
	}

	function initStars() {
		if (!window.fetch) {
			return;
		}

		var links = document.querySelectorAll(
			'a[href^="https://github.com/"], a[href^="http://github.com/"]');
		var repos = [];
		for (var i = 0; i < links.length; i++) {
			var repo = repoFromHref(links[i].href);
			if (repo && repos.indexOf(repo) === -1) {
				repos.push(repo);
			}
		}
		if (!repos.length) {
			return;
		}

		var cache = readCache();

		function apply(repo, count) {
			for (var k = 0; k < links.length; k++) {
				if (repoFromHref(links[k].href) === repo) {
					showStars(links[k], count);
				}
			}
		}

		function fetchStars(repo) {
			window.fetch('https://api.github.com/repos/' + repo, {
				headers: { Accept: 'application/vnd.github+json' }
			}).then(function (response) {
				if (!response.ok) {
					throw new Error('HTTP ' + response.status);
				}
				return response.json();
			}).then(function (data) {
				if (typeof data.stargazers_count !== 'number') {
					return;
				}
				cache[repo] = { count: data.stargazers_count, at: Date.now() };
				writeCache(cache);
				apply(repo, data.stargazers_count);
			}).catch(function () {
				/* Unreachable, rate-limited or renamed: leave the link alone. */
			});
		}

		for (var r = 0; r < repos.length; r++) {
			var entry = cache[repos[r]];
			if (entry && typeof entry.count === 'number'
					&& Date.now() - entry.at < STARS_TTL) {
				apply(repos[r], entry.count);
			} else {
				fetchStars(repos[r]);
			}
		}
	}

	/* --- bootstrap --------------------------------------------------------- */

	if (typeof document === 'undefined') {
		// Node, running the unit tests: expose the parser and stop.
		if (typeof module === 'object' && module.exports) {
			module.exports = { repoFromHref: repoFromHref };
		}
		return;
	}

	function ready(callback) {
		if (document.readyState === 'loading') {
			document.addEventListener('DOMContentLoaded', callback);
		} else {
			callback();
		}
	}

	ready(function () {
		var section = document.querySelector('.work-section');
		if (section) {
			initViewToggle(section);
		}
		initStars();
	});
}());
