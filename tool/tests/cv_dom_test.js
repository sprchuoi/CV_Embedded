/*
 * A DOM just big enough to run docs/assets/js/cv.js for real: the Summary/Full
 * toggle and the GitHub star badges, exercised without a browser.
 *
 * This repo has no jsdom and no Node test runner, so tool/tests/test_cv_index.py
 * shells out to this file and fails when it exits non-zero. Everything here is
 * a stub of the handful of DOM APIs cv.js touches -- the point is to prove the
 * toggle switches panes, the arrow keys move between tabs, and the badges are
 * filled from the API while non-repo links are left alone.
 */
'use strict';

const path = require('path');

const CV_JS = path.join(__dirname, '..', '..', 'docs', 'assets', 'js', 'cv.js');

let failures = 0;

function check(name, actual, expected) {
	if (JSON.stringify(actual) !== JSON.stringify(expected)) {
		failures++;
		console.log(`FAIL ${name}: got ${JSON.stringify(actual)}, want ${JSON.stringify(expected)}`);
	} else {
		console.log(`ok   ${name}`);
	}
}

/* --- a fake element ------------------------------------------------------ */

function Element(tag) {
	this.tagName = String(tag).toUpperCase();
	this.id = '';
	this.hidden = false;
	this.tabIndex = 0;
	this.textContent = '';
	this.title = '';
	this.className = '';
	this.attributes = {};
	this.listeners = {};
	this.parentNode = null;
	this.nextElementSibling = null;
	this._classes = [];

	const self = this;
	this.classList = {
		add(c) {
			if (self._classes.indexOf(c) === -1) {
				self._classes.push(c);
			}
		},
		remove(c) {
			const i = self._classes.indexOf(c);
			if (i !== -1) {
				self._classes.splice(i, 1);
			}
		},
		contains(c) {
			return self._classes.indexOf(c) !== -1;
		},
		toggle(c, on) {
			const want = (on === undefined) ? !self.classList.contains(c) : !!on;
			if (want) {
				self.classList.add(c);
			} else {
				self.classList.remove(c);
			}
			return want;
		}
	};
}

Element.prototype.setAttribute = function (key, value) {
	this.attributes[key] = String(value);
};

Element.prototype.getAttribute = function (key) {
	return Object.prototype.hasOwnProperty.call(this.attributes, key)
		? this.attributes[key] : null;
};

Element.prototype.addEventListener = function (type, fn) {
	(this.listeners[type] = this.listeners[type] || []).push(fn);
};

Element.prototype.dispatch = function (type, event) {
	(this.listeners[type] || []).forEach(function (fn) {
		fn(Object.assign({ preventDefault() {} }, event));
	});
};

Element.prototype.focus = function () {
	global.document.activeElement = this;
};

/* --- the fixtures -------------------------------------------------------- */

function buildSection() {
	const tabs = [new Element('button'), new Element('button')];
	tabs[0].id = 'work-tab-summary';
	tabs[0].setAttribute('aria-controls', 'work-view-summary');
	tabs[0].setAttribute('aria-selected', 'true');
	tabs[0].classList.add('is-active');
	tabs[1].id = 'work-tab-full';
	tabs[1].setAttribute('aria-controls', 'work-view-full');
	tabs[1].setAttribute('aria-selected', 'false');
	tabs[1].tabIndex = -1;

	const panels = [new Element('div'), new Element('div')];
	panels[0].id = 'work-view-summary';
	panels[1].id = 'work-view-full';
	panels[1].hidden = true;

	const section = new Element('section');
	section.querySelectorAll = function (selector) {
		if (selector === '[role="tab"]') {
			return tabs;
		}
		if (selector === '[role="tabpanel"]') {
			return panels;
		}
		return [];
	};
	return { section, tabs, panels };
}

function buildLink(href) {
	const link = new Element('a');
	link.href = href;
	link.nextSibling = null;
	const para = new Element('p');
	para.insertBefore = function (node) {
		node.parentNode = para;
		link.nextElementSibling = node;
		return node;
	};
	link.parentNode = para;
	return link;
}

const STARS = {
	'sprchuoi/Smart_Server': 42,
	'sprchuoi/smart_home_zephyr': 0
};

const { section, tabs, panels } = buildSection();
const links = [
	buildLink('https://github.com/sprchuoi/Smart_Server'),
	buildLink('https://github.com/sprchuoi/smart_home_zephyr'),
	buildLink('https://github.com/sprchuoi/CV_Embedded/releases/download/latest/CV.pdf')
];
const fetched = [];

global.window = {
	localStorage: {
		getItem: function () { return null; },
		setItem: function () {}
	},
	fetch: function (url) {
		fetched.push(url);
		const repo = url.replace('https://api.github.com/repos/', '');
		return Promise.resolve({
			ok: true,
			json: function () {
				return Promise.resolve({ stargazers_count: STARS[repo] || 0 });
			}
		});
	}
};

global.document = {
	readyState: 'complete',
	activeElement: null,
	querySelector: function (selector) {
		return selector === '.work-section' ? section : null;
	},
	querySelectorAll: function (selector) {
		return selector.indexOf('github.com') !== -1 ? links : [];
	},
	createElement: function (tag) { return new Element(tag); },
	addEventListener: function () {}
};

/* --- run it -------------------------------------------------------------- */

require(CV_JS);

check('starts on Summary', [panels[0].hidden, panels[1].hidden], [false, true]);

tabs[1].dispatch('click');
check('click Full hides Summary', [panels[0].hidden, panels[1].hidden], [true, false]);
check('click Full updates aria-selected',
	[tabs[0].getAttribute('aria-selected'), tabs[1].getAttribute('aria-selected')],
	['false', 'true']);
check('click Full moves is-active',
	[tabs[0].classList.contains('is-active'), tabs[1].classList.contains('is-active')],
	[false, true]);
check('click Full moves the tab stop', [tabs[0].tabIndex, tabs[1].tabIndex], [-1, 0]);

tabs[1].dispatch('keydown', { key: 'ArrowLeft' });
check('ArrowLeft returns to Summary', [panels[0].hidden, panels[1].hidden], [false, true]);
check('ArrowLeft focuses the tab', document.activeElement === tabs[0], true);

tabs[0].dispatch('keydown', { key: 'ArrowRight' });
check('ArrowRight goes to Full', [panels[0].hidden, panels[1].hidden], [true, false]);

tabs[1].dispatch('keydown', { key: 'ArrowRight' });
check('ArrowRight wraps to Summary', [panels[0].hidden, panels[1].hidden], [false, true]);

/* The badge fetches are promises: let every microtask drain first. */
setImmediate(function () {
	check('only repo links are fetched', fetched.sort(), [
		'https://api.github.com/repos/sprchuoi/Smart_Server',
		'https://api.github.com/repos/sprchuoi/smart_home_zephyr'
	]);
	check('star count is rendered', links[0].nextElementSibling.textContent, '\u2605 42');
	check('a starred repo is flagged',
		links[0].nextElementSibling.classList.contains('has-stars'), true);
	check('a zero-star repo is not flagged',
		links[1].nextElementSibling.classList.contains('has-stars'), false);
	check('a non-repo GitHub link gets no badge', links[2].nextElementSibling, null);

	console.log(failures ? `${failures} failure(s)` : 'all DOM checks passed');
	process.exit(failures ? 1 : 0);
});
