// node_modules/@lit/reactive-element/css-tag.js
var e = globalThis, t = e.ShadowRoot && (e.ShadyCSS === void 0 || e.ShadyCSS.nativeShadow) && "adoptedStyleSheets" in Document.prototype && "replace" in CSSStyleSheet.prototype, n = Symbol(), r = /* @__PURE__ */ new WeakMap(), i = class {
	constructor(e, t, r) {
		if (this._$cssResult$ = !0, r !== n) throw Error("CSSResult is not constructable. Use `unsafeCSS` or `css` instead.");
		this.cssText = e, this.t = t;
	}
	get styleSheet() {
		let e = this.o, n = this.t;
		if (t && e === void 0) {
			let t = n !== void 0 && n.length === 1;
			t && (e = r.get(n)), e === void 0 && ((this.o = e = new CSSStyleSheet()).replaceSync(this.cssText), t && r.set(n, e));
		}
		return e;
	}
	toString() {
		return this.cssText;
	}
}, a = (e) => new i(typeof e == "string" ? e : e + "", void 0, n), o = (e, ...t) => new i(e.length === 1 ? e[0] : t.reduce((t, n, r) => t + ((e) => {
	if (!0 === e._$cssResult$) return e.cssText;
	if (typeof e == "number") return e;
	throw Error("Value passed to 'css' function must be a 'css' function result: " + e + ". Use 'unsafeCSS' to pass non-literal values, but take care to ensure page security.");
})(n) + e[r + 1], e[0]), e, n), s = (n, r) => {
	if (t) n.adoptedStyleSheets = r.map((e) => e instanceof CSSStyleSheet ? e : e.styleSheet);
	else for (let t of r) {
		let r = document.createElement("style"), i = e.litNonce;
		i !== void 0 && r.setAttribute("nonce", i), r.textContent = t.cssText, n.appendChild(r);
	}
}, c = t ? (e) => e : (e) => e instanceof CSSStyleSheet ? ((e) => {
	let t = "";
	for (let n of e.cssRules) t += n.cssText;
	return a(t);
})(e) : e, { is: l, defineProperty: u, getOwnPropertyDescriptor: d, getOwnPropertyNames: f, getOwnPropertySymbols: ee, getPrototypeOf: te } = Object, ne = globalThis, re = ne.trustedTypes, ie = re ? re.emptyScript : "", ae = ne.reactiveElementPolyfillSupport, p = (e, t) => e, m = {
	toAttribute(e, t) {
		switch (t) {
			case Boolean:
				e = e ? ie : null;
				break;
			case Object:
			case Array: e = e == null ? e : JSON.stringify(e);
		}
		return e;
	},
	fromAttribute(e, t) {
		let n = e;
		switch (t) {
			case Boolean:
				n = e !== null;
				break;
			case Number:
				n = e === null ? null : Number(e);
				break;
			case Object:
			case Array: try {
				n = JSON.parse(e);
			} catch {
				n = null;
			}
		}
		return n;
	}
}, oe = (e, t) => !l(e, t), se = {
	attribute: !0,
	type: String,
	converter: m,
	reflect: !1,
	useDefault: !1,
	hasChanged: oe
};
Symbol.metadata ??= Symbol("metadata"), ne.litPropertyMetadata ??= /* @__PURE__ */ new WeakMap();
var h = class extends HTMLElement {
	static addInitializer(e) {
		this._$Ei(), (this.l ??= []).push(e);
	}
	static get observedAttributes() {
		return this.finalize(), this._$Eh && [...this._$Eh.keys()];
	}
	static createProperty(e, t = se) {
		if (t.state && (t.attribute = !1), this._$Ei(), this.prototype.hasOwnProperty(e) && ((t = Object.create(t)).wrapped = !0), this.elementProperties.set(e, t), !t.noAccessor) {
			let n = Symbol(), r = this.getPropertyDescriptor(e, n, t);
			r !== void 0 && u(this.prototype, e, r);
		}
	}
	static getPropertyDescriptor(e, t, n) {
		let { get: r, set: i } = d(this.prototype, e) ?? {
			get() {
				return this[t];
			},
			set(e) {
				this[t] = e;
			}
		};
		return {
			get: r,
			set(t) {
				let a = r?.call(this);
				i?.call(this, t), this.requestUpdate(e, a, n);
			},
			configurable: !0,
			enumerable: !0
		};
	}
	static getPropertyOptions(e) {
		return this.elementProperties.get(e) ?? se;
	}
	static _$Ei() {
		if (this.hasOwnProperty(p("elementProperties"))) return;
		let e = te(this);
		e.finalize(), e.l !== void 0 && (this.l = [...e.l]), this.elementProperties = new Map(e.elementProperties);
	}
	static finalize() {
		if (this.hasOwnProperty(p("finalized"))) return;
		if (this.finalized = !0, this._$Ei(), this.hasOwnProperty(p("properties"))) {
			let e = this.properties, t = [...f(e), ...ee(e)];
			for (let n of t) this.createProperty(n, e[n]);
		}
		let e = this[Symbol.metadata];
		if (e !== null) {
			let t = litPropertyMetadata.get(e);
			if (t !== void 0) for (let [e, n] of t) this.elementProperties.set(e, n);
		}
		this._$Eh = /* @__PURE__ */ new Map();
		for (let [e, t] of this.elementProperties) {
			let n = this._$Eu(e, t);
			n !== void 0 && this._$Eh.set(n, e);
		}
		this.elementStyles = this.finalizeStyles(this.styles);
	}
	static finalizeStyles(e) {
		let t = [];
		if (Array.isArray(e)) {
			let n = new Set(e.flat(1 / 0).reverse());
			for (let e of n) t.unshift(c(e));
		} else e !== void 0 && t.push(c(e));
		return t;
	}
	static _$Eu(e, t) {
		let n = t.attribute;
		return !1 === n ? void 0 : typeof n == "string" ? n : typeof e == "string" ? e.toLowerCase() : void 0;
	}
	constructor() {
		super(), this._$Ep = void 0, this.isUpdatePending = !1, this.hasUpdated = !1, this._$Em = null, this._$Ev();
	}
	_$Ev() {
		this._$ES = new Promise((e) => this.enableUpdating = e), this._$AL = /* @__PURE__ */ new Map(), this._$E_(), this.requestUpdate(), this.constructor.l?.forEach((e) => e(this));
	}
	addController(e) {
		(this._$EO ??= /* @__PURE__ */ new Set()).add(e), this.renderRoot !== void 0 && this.isConnected && e.hostConnected?.();
	}
	removeController(e) {
		this._$EO?.delete(e);
	}
	_$E_() {
		let e = /* @__PURE__ */ new Map(), t = this.constructor.elementProperties;
		for (let n of t.keys()) this.hasOwnProperty(n) && (e.set(n, this[n]), delete this[n]);
		e.size > 0 && (this._$Ep = e);
	}
	createRenderRoot() {
		let e = this.shadowRoot ?? this.attachShadow(this.constructor.shadowRootOptions);
		return s(e, this.constructor.elementStyles), e;
	}
	connectedCallback() {
		this.renderRoot ??= this.createRenderRoot(), this.enableUpdating(!0), this._$EO?.forEach((e) => e.hostConnected?.());
	}
	enableUpdating(e) {}
	disconnectedCallback() {
		this._$EO?.forEach((e) => e.hostDisconnected?.());
	}
	attributeChangedCallback(e, t, n) {
		this._$AK(e, n);
	}
	_$ET(e, t) {
		let n = this.constructor.elementProperties.get(e), r = this.constructor._$Eu(e, n);
		if (r !== void 0 && !0 === n.reflect) {
			let i = (n.converter?.toAttribute === void 0 ? m : n.converter).toAttribute(t, n.type);
			this._$Em = e, i == null ? this.removeAttribute(r) : this.setAttribute(r, i), this._$Em = null;
		}
	}
	_$AK(e, t) {
		let n = this.constructor, r = n._$Eh.get(e);
		if (r !== void 0 && this._$Em !== r) {
			let e = n.getPropertyOptions(r), i = typeof e.converter == "function" ? { fromAttribute: e.converter } : e.converter?.fromAttribute === void 0 ? m : e.converter;
			this._$Em = r;
			let a = i.fromAttribute(t, e.type);
			this[r] = a ?? this._$Ej?.get(r) ?? a, this._$Em = null;
		}
	}
	requestUpdate(e, t, n, r = !1, i) {
		if (e !== void 0) {
			let a = this.constructor;
			if (!1 === r && (i = this[e]), n ??= a.getPropertyOptions(e), !((n.hasChanged ?? oe)(i, t) || n.useDefault && n.reflect && i === this._$Ej?.get(e) && !this.hasAttribute(a._$Eu(e, n)))) return;
			this.C(e, t, n);
		}
		!1 === this.isUpdatePending && (this._$ES = this._$EP());
	}
	C(e, t, { useDefault: n, reflect: r, wrapped: i }, a) {
		n && !(this._$Ej ??= /* @__PURE__ */ new Map()).has(e) && (this._$Ej.set(e, a ?? t ?? this[e]), !0 !== i || a !== void 0) || (this._$AL.has(e) || (this.hasUpdated || n || (t = void 0), this._$AL.set(e, t)), !0 === r && this._$Em !== e && (this._$Eq ??= /* @__PURE__ */ new Set()).add(e));
	}
	async _$EP() {
		this.isUpdatePending = !0;
		try {
			await this._$ES;
		} catch (e) {
			Promise.reject(e);
		}
		let e = this.scheduleUpdate();
		return e != null && await e, !this.isUpdatePending;
	}
	scheduleUpdate() {
		return this.performUpdate();
	}
	performUpdate() {
		if (!this.isUpdatePending) return;
		if (!this.hasUpdated) {
			if (this.renderRoot ??= this.createRenderRoot(), this._$Ep) {
				for (let [e, t] of this._$Ep) this[e] = t;
				this._$Ep = void 0;
			}
			let e = this.constructor.elementProperties;
			if (e.size > 0) for (let [t, n] of e) {
				let { wrapped: e } = n, r = this[t];
				!0 !== e || this._$AL.has(t) || r === void 0 || this.C(t, void 0, n, r);
			}
		}
		let e = !1, t = this._$AL;
		try {
			e = this.shouldUpdate(t), e ? (this.willUpdate(t), this._$EO?.forEach((e) => e.hostUpdate?.()), this.update(t)) : this._$EM();
		} catch (t) {
			throw e = !1, this._$EM(), t;
		}
		e && this._$AE(t);
	}
	willUpdate(e) {}
	_$AE(e) {
		this._$EO?.forEach((e) => e.hostUpdated?.()), this.hasUpdated || (this.hasUpdated = !0, this.firstUpdated(e)), this.updated(e);
	}
	_$EM() {
		this._$AL = /* @__PURE__ */ new Map(), this.isUpdatePending = !1;
	}
	get updateComplete() {
		return this.getUpdateComplete();
	}
	getUpdateComplete() {
		return this._$ES;
	}
	shouldUpdate(e) {
		return !0;
	}
	update(e) {
		this._$Eq &&= this._$Eq.forEach((e) => this._$ET(e, this[e])), this._$EM();
	}
	updated(e) {}
	firstUpdated(e) {}
};
h.elementStyles = [], h.shadowRootOptions = { mode: "open" }, h[p("elementProperties")] = /* @__PURE__ */ new Map(), h[p("finalized")] = /* @__PURE__ */ new Map(), ae?.({ ReactiveElement: h }), (ne.reactiveElementVersions ??= []).push("2.1.2");
// node_modules/lit-html/lit-html.js
var ce = globalThis, le = (e) => e, ue = ce.trustedTypes, de = ue ? ue.createPolicy("lit-html", { createHTML: (e) => e }) : void 0, fe = "$lit$", g = `lit$${Math.random().toFixed(9).slice(2)}$`, pe = "?" + g, me = `<${pe}>`, _ = document, v = () => _.createComment(""), y = (e) => e === null || typeof e != "object" && typeof e != "function", he = Array.isArray, ge = (e) => he(e) || typeof e?.[Symbol.iterator] == "function", _e = "[ 	\n\f\r]", b = /<(?:(!--|\/[^a-zA-Z])|(\/?[a-zA-Z][^>\s]*)|(\/?$))/g, ve = /-->/g, ye = />/g, x = RegExp(`>|${_e}(?:([^\\s"'>=/]+)(${_e}*=${_e}*(?:[^ \t\n\f\r"'\`<>=]|("|')|))|$)`, "g"), be = /'/g, xe = /"/g, Se = /^(?:script|style|textarea|title)$/i, Ce = (e) => (t, ...n) => ({
	_$litType$: e,
	strings: t,
	values: n
}), S = Ce(1), we = Ce(2), C = Symbol.for("lit-noChange"), w = Symbol.for("lit-nothing"), Te = /* @__PURE__ */ new WeakMap(), T = _.createTreeWalker(_, 129);
function Ee(e, t) {
	if (!he(e) || !e.hasOwnProperty("raw")) throw Error("invalid template strings array");
	return de === void 0 ? t : de.createHTML(t);
}
var De = (e, t) => {
	let n = e.length - 1, r = [], i, a = t === 2 ? "<svg>" : t === 3 ? "<math>" : "", o = b;
	for (let t = 0; t < n; t++) {
		let n = e[t], s, c, l = -1, u = 0;
		for (; u < n.length && (o.lastIndex = u, c = o.exec(n), c !== null);) u = o.lastIndex, o === b ? c[1] === "!--" ? o = ve : c[1] === void 0 ? c[2] === void 0 ? c[3] !== void 0 && (o = x) : (Se.test(c[2]) && (i = RegExp("</" + c[2], "g")), o = x) : o = ye : o === x ? c[0] === ">" ? (o = i ?? b, l = -1) : c[1] === void 0 ? l = -2 : (l = o.lastIndex - c[2].length, s = c[1], o = c[3] === void 0 ? x : c[3] === "\"" ? xe : be) : o === xe || o === be ? o = x : o === ve || o === ye ? o = b : (o = x, i = void 0);
		let d = o === x && e[t + 1].startsWith("/>") ? " " : "";
		a += o === b ? n + me : l >= 0 ? (r.push(s), n.slice(0, l) + fe + n.slice(l) + g + d) : n + g + (l === -2 ? t : d);
	}
	return [Ee(e, a + (e[n] || "<?>") + (t === 2 ? "</svg>" : t === 3 ? "</math>" : "")), r];
}, Oe = class e {
	constructor({ strings: t, _$litType$: n }, r) {
		let i;
		this.parts = [];
		let a = 0, o = 0, s = t.length - 1, c = this.parts, [l, u] = De(t, n);
		if (this.el = e.createElement(l, r), T.currentNode = this.el.content, n === 2 || n === 3) {
			let e = this.el.content.firstChild;
			e.replaceWith(...e.childNodes);
		}
		for (; (i = T.nextNode()) !== null && c.length < s;) {
			if (i.nodeType === 1) {
				if (i.hasAttributes()) for (let e of i.getAttributeNames()) if (e.endsWith(fe)) {
					let t = u[o++], n = i.getAttribute(e).split(g), r = /([.?@])?(.*)/.exec(t);
					c.push({
						type: 1,
						index: a,
						name: r[2],
						strings: n,
						ctor: r[1] === "." ? Me : r[1] === "?" ? Ne : r[1] === "@" ? Pe : je
					}), i.removeAttribute(e);
				} else e.startsWith(g) && (c.push({
					type: 6,
					index: a
				}), i.removeAttribute(e));
				if (Se.test(i.tagName)) {
					let e = i.textContent.split(g), t = e.length - 1;
					if (t > 0) {
						i.textContent = ue ? ue.emptyScript : "";
						for (let n = 0; n < t; n++) i.append(e[n], v()), T.nextNode(), c.push({
							type: 2,
							index: ++a
						});
						i.append(e[t], v());
					}
				}
			} else if (i.nodeType === 8) {
				if (i.data === pe) c.push({
					type: 2,
					index: a
				});
				else {
					let e = -1;
					for (; (e = i.data.indexOf(g, e + 1)) !== -1;) c.push({
						type: 7,
						index: a
					}), e += g.length - 1;
				}
			}
			a++;
		}
	}
	static createElement(e, t) {
		let n = _.createElement("template");
		return n.innerHTML = e, n;
	}
};
function E(e, t, n = e, r) {
	if (t === C) return t;
	let i = r === void 0 ? n._$Cl : n._$Co?.[r], a = y(t) ? void 0 : t._$litDirective$;
	return i?.constructor !== a && (i?._$AO?.(!1), a === void 0 ? i = void 0 : (i = new a(e), i._$AT(e, n, r)), r === void 0 ? n._$Cl = i : (n._$Co ??= [])[r] = i), i !== void 0 && (t = E(e, i._$AS(e, t.values), i, r)), t;
}
var ke = class {
	constructor(e, t) {
		this._$AV = [], this._$AN = void 0, this._$AD = e, this._$AM = t;
	}
	get parentNode() {
		return this._$AM.parentNode;
	}
	get _$AU() {
		return this._$AM._$AU;
	}
	u(e) {
		let { el: { content: t }, parts: n } = this._$AD, r = (e?.creationScope ?? _).importNode(t, !0);
		T.currentNode = r;
		let i = T.nextNode(), a = 0, o = 0, s = n[0];
		for (; s !== void 0;) {
			if (a === s.index) {
				let t;
				s.type === 2 ? t = new Ae(i, i.nextSibling, this, e) : s.type === 1 ? t = new s.ctor(i, s.name, s.strings, this, e) : s.type === 6 && (t = new Fe(i, this, e)), this._$AV.push(t), s = n[++o];
			}
			a !== s?.index && (i = T.nextNode(), a++);
		}
		return T.currentNode = _, r;
	}
	p(e) {
		let t = 0;
		for (let n of this._$AV) n !== void 0 && (n.strings === void 0 ? n._$AI(e[t]) : (n._$AI(e, n, t), t += n.strings.length - 2)), t++;
	}
}, Ae = class e {
	get _$AU() {
		return this._$AM?._$AU ?? this._$Cv;
	}
	constructor(e, t, n, r) {
		this.type = 2, this._$AH = w, this._$AN = void 0, this._$AA = e, this._$AB = t, this._$AM = n, this.options = r, this._$Cv = r?.isConnected ?? !0;
	}
	get parentNode() {
		let e = this._$AA.parentNode, t = this._$AM;
		return t !== void 0 && e?.nodeType === 11 && (e = t.parentNode), e;
	}
	get startNode() {
		return this._$AA;
	}
	get endNode() {
		return this._$AB;
	}
	_$AI(e, t = this) {
		e = E(this, e, t), y(e) ? e === w || e == null || e === "" ? (this._$AH !== w && this._$AR(), this._$AH = w) : e !== this._$AH && e !== C && this._(e) : e._$litType$ === void 0 ? e.nodeType === void 0 ? ge(e) ? this.k(e) : this._(e) : this.T(e) : this.$(e);
	}
	O(e) {
		return this._$AA.parentNode.insertBefore(e, this._$AB);
	}
	T(e) {
		this._$AH !== e && (this._$AR(), this._$AH = this.O(e));
	}
	_(e) {
		this._$AH !== w && y(this._$AH) ? this._$AA.nextSibling.data = e : this.T(_.createTextNode(e)), this._$AH = e;
	}
	$(e) {
		let { values: t, _$litType$: n } = e, r = typeof n == "number" ? this._$AC(e) : (n.el === void 0 && (n.el = Oe.createElement(Ee(n.h, n.h[0]), this.options)), n);
		if (this._$AH?._$AD === r) this._$AH.p(t);
		else {
			let e = new ke(r, this), n = e.u(this.options);
			e.p(t), this.T(n), this._$AH = e;
		}
	}
	_$AC(e) {
		let t = Te.get(e.strings);
		return t === void 0 && Te.set(e.strings, t = new Oe(e)), t;
	}
	k(t) {
		he(this._$AH) || (this._$AH = [], this._$AR());
		let n = this._$AH, r, i = 0;
		for (let a of t) i === n.length ? n.push(r = new e(this.O(v()), this.O(v()), this, this.options)) : r = n[i], r._$AI(a), i++;
		i < n.length && (this._$AR(r && r._$AB.nextSibling, i), n.length = i);
	}
	_$AR(e = this._$AA.nextSibling, t) {
		for (this._$AP?.(!1, !0, t); e !== this._$AB;) {
			let t = le(e).nextSibling;
			le(e).remove(), e = t;
		}
	}
	setConnected(e) {
		this._$AM === void 0 && (this._$Cv = e, this._$AP?.(e));
	}
}, je = class {
	get tagName() {
		return this.element.tagName;
	}
	get _$AU() {
		return this._$AM._$AU;
	}
	constructor(e, t, n, r, i) {
		this.type = 1, this._$AH = w, this._$AN = void 0, this.element = e, this.name = t, this._$AM = r, this.options = i, n.length > 2 || n[0] !== "" || n[1] !== "" ? (this._$AH = Array(n.length - 1).fill(/* @__PURE__ */ new String()), this.strings = n) : this._$AH = w;
	}
	_$AI(e, t = this, n, r) {
		let i = this.strings, a = !1;
		if (i === void 0) e = E(this, e, t, 0), a = !y(e) || e !== this._$AH && e !== C, a && (this._$AH = e);
		else {
			let r = e, o, s;
			for (e = i[0], o = 0; o < i.length - 1; o++) s = E(this, r[n + o], t, o), s === C && (s = this._$AH[o]), a ||= !y(s) || s !== this._$AH[o], s === w ? e = w : e !== w && (e += (s ?? "") + i[o + 1]), this._$AH[o] = s;
		}
		a && !r && this.j(e);
	}
	j(e) {
		e === w ? this.element.removeAttribute(this.name) : this.element.setAttribute(this.name, e ?? "");
	}
}, Me = class extends je {
	constructor() {
		super(...arguments), this.type = 3;
	}
	j(e) {
		this.element[this.name] = e === w ? void 0 : e;
	}
}, Ne = class extends je {
	constructor() {
		super(...arguments), this.type = 4;
	}
	j(e) {
		this.element.toggleAttribute(this.name, !!e && e !== w);
	}
}, Pe = class extends je {
	constructor(e, t, n, r, i) {
		super(e, t, n, r, i), this.type = 5;
	}
	_$AI(e, t = this) {
		if ((e = E(this, e, t, 0) ?? w) === C) return;
		let n = this._$AH, r = e === w && n !== w || e.capture !== n.capture || e.once !== n.once || e.passive !== n.passive, i = e !== w && (n === w || r);
		r && this.element.removeEventListener(this.name, this, n), i && this.element.addEventListener(this.name, this, e), this._$AH = e;
	}
	handleEvent(e) {
		typeof this._$AH == "function" ? this._$AH.call(this.options?.host ?? this.element, e) : this._$AH.handleEvent(e);
	}
}, Fe = class {
	constructor(e, t, n) {
		this.element = e, this.type = 6, this._$AN = void 0, this._$AM = t, this.options = n;
	}
	get _$AU() {
		return this._$AM._$AU;
	}
	_$AI(e) {
		E(this, e);
	}
}, Ie = ce.litHtmlPolyfillSupport;
Ie?.(Oe, Ae), (ce.litHtmlVersions ??= []).push("3.3.3");
var Le = (e, t, n) => {
	let r = n?.renderBefore ?? t, i = r._$litPart$;
	if (i === void 0) {
		let e = n?.renderBefore ?? null;
		r._$litPart$ = i = new Ae(t.insertBefore(v(), e), e, void 0, n ?? {});
	}
	return i._$AI(e), i;
}, Re = globalThis, D = class extends h {
	constructor() {
		super(...arguments), this.renderOptions = { host: this }, this._$Do = void 0;
	}
	createRenderRoot() {
		let e = super.createRenderRoot();
		return this.renderOptions.renderBefore ??= e.firstChild, e;
	}
	update(e) {
		let t = this.render();
		this.hasUpdated || (this.renderOptions.isConnected = this.isConnected), super.update(e), this._$Do = Le(t, this.renderRoot, this.renderOptions);
	}
	connectedCallback() {
		super.connectedCallback(), this._$Do?.setConnected(!0);
	}
	disconnectedCallback() {
		super.disconnectedCallback(), this._$Do?.setConnected(!1);
	}
	render() {
		return C;
	}
};
D._$litElement$ = !0, D.finalized = !0, Re.litElementHydrateSupport?.({ LitElement: D });
var ze = Re.litElementPolyfillSupport;
ze?.({ LitElement: D }), (Re.litElementVersions ??= []).push("4.2.2");
// node_modules/@lit/reactive-element/decorators/custom-element.js
var O = (e) => (t, n) => {
	n === void 0 ? customElements.define(e, t) : n.addInitializer(() => {
		customElements.define(e, t);
	});
}, Be = {
	attribute: !0,
	type: String,
	converter: m,
	reflect: !1,
	hasChanged: oe
}, Ve = (e = Be, t, n) => {
	let { kind: r, metadata: i } = n, a = globalThis.litPropertyMetadata.get(i);
	if (a === void 0 && globalThis.litPropertyMetadata.set(i, a = /* @__PURE__ */ new Map()), r === "setter" && ((e = Object.create(e)).wrapped = !0), a.set(n.name, e), r === "accessor") {
		let { name: r } = n;
		return {
			set(n) {
				let i = t.get.call(this);
				t.set.call(this, n), this.requestUpdate(r, i, e, !0, n);
			},
			init(t) {
				return t !== void 0 && this.C(r, void 0, e, t), t;
			}
		};
	}
	if (r === "setter") {
		let { name: r } = n;
		return function(n) {
			let i = this[r];
			t.call(this, n), this.requestUpdate(r, i, e, !0, n);
		};
	}
	throw Error("Unsupported decorator location: " + r);
};
function k(e) {
	return (t, n) => typeof n == "object" ? Ve(e, t, n) : ((e, t, n) => {
		let r = t.hasOwnProperty(n);
		return t.constructor.createProperty(n, e), r ? Object.getOwnPropertyDescriptor(t, n) : void 0;
	})(e, t, n);
}
// node_modules/@lit/reactive-element/decorators/state.js
function A(e) {
	return k({
		...e,
		state: !0,
		attribute: !1
	});
}
// src/format.ts
var He = "−";
function Ue(e, t, n) {
	return new Intl.NumberFormat(t, {
		minimumFractionDigits: n,
		maximumFractionDigits: n
	}).format(e);
}
function j(e, t) {
	let n = new Intl.NumberFormat(t, {
		style: "currency",
		currency: "EUR",
		minimumFractionDigits: 2,
		maximumFractionDigits: 2
	}).format(Math.abs(e));
	return e < 0 ? He + n : n;
}
function We(e, t) {
	let n = Math.abs(e);
	return n >= 1e3 ? `${Ue(n / 1e3, t, 2)} kW` : `${Ue(Math.round(n / 10) * 10, t, 0)} W`;
}
function Ge(e, t) {
	return (e > 0 ? "+" : e < 0 ? He : "") + We(e, t);
}
function M(e, t, n = 1) {
	return `${Ue(e, t, n)} kWh`;
}
function N(e, t) {
	return `${Ue(Math.round(e), t, 0)} %`;
}
function P(e, t, n) {
	return new Intl.DateTimeFormat(t, {
		hour: "2-digit",
		minute: "2-digit",
		hour12: !1,
		timeZone: n
	}).format(new Date(e));
}
function F(e, t, n) {
	return new Intl.DateTimeFormat(t, {
		weekday: "short",
		day: "numeric",
		month: "short",
		timeZone: n
	}).format(new Date(e));
}
function Ke(e, t) {
	return Math.max(0, Math.round((new Date(e).getTime() - t) / 6e4));
}
function I(e, t, n) {
	let r = new Intl.DateTimeFormat("en-CA", {
		year: "numeric",
		month: "2-digit",
		day: "2-digit",
		timeZone: n
	});
	return r.format(new Date(e)) === r.format(new Date(t));
}
// src/i18n.ts
var qe = {
	nl: {
		menu: {
			label: "Hoofdmenu",
			plan: "Plan",
			sets: "Sets",
			battery: "Accu",
			settings: "Instellingen",
			diagnostics: "Diagnose",
			savings: "Besparing"
		},
		header: {
			live: "Stuurt",
			shadow: "Rekent mee",
			live_title: "ZEPHYR stuurt de accu",
			shadow_title: "Schaduwmodus: ZEPHYR rekent mee maar stuurt niets"
		},
		mode: {
			standby: "Standby",
			zero_meter: "Nul op de meter",
			fast_charge: "Snel opladen",
			fast_discharge: "Snel ontladen",
			dynamic_forecasting: "Dynamische Forecasting"
		},
		action: {
			standby: "Standby",
			charge: "Laden",
			deliver: "Leveren",
			hold: "Vasthouden",
			export: "Terugleveren",
			blocked: "Geblokkeerd",
			calibration: "Kalibratie"
		},
		now: {
			title: "Nu",
			waiting: "Wacht op de eerste meting…",
			grid: "Net {value}",
			shadow_note: "Zo zou ZEPHYR het doen (schaduwmodus)."
		},
		battery: {
			title: "Accu",
			of: "{energy} van {capacity}",
			limits: "Grenzen {min}–{max} %",
			buffer: "buffer {value} %",
			sets: "{online} van {total} sets online",
			set: "1 set",
			set_offline: "set offline",
			unknown: "Nog geen gegevens van de set"
		},
		next: {
			title: "Volgende stap",
			in: "over {time}",
			now: "nu",
			hours: "{h} u {m} min",
			minutes: "{m} min",
			at: "{time} · {action}",
			tomorrow: "morgen {time} · {action}",
			charge: "{kwh} uit het net, gemiddeld {price}.",
			deliver: "{kwh} uit de accu; stroom kost dan gemiddeld {price}.",
			export: "{kwh} terugleveren voor gemiddeld {price}.",
			hold: "Accu houdt de lading vast; stroom kost dan gemiddeld {price}.",
			indicative: "Indicatief: de prijzen van morgen zijn nog niet bekend.",
			none: "Geen wissel meer in het plan.",
			no_price_source: "Kies een prijsbron in de opties om een plan te maken.",
			no_prices: "Geen prijzen sinds {time}; ZEPHYR houdt het net op nul.",
			price_now: "Stroom kost nu {price}"
		},
		status: {
			loading: "ZEPHYR laden…",
			not_loaded: "ZEPHYR is niet geladen. Controleer de integratie onder Instellingen → Apparaten en diensten.",
			disconnected: "Geen verbinding met Home Assistant. De waarden hieronder zijn van {time}.",
			reloading: "ZEPHYR wordt opnieuw geladen…",
			coming: "Dit scherm komt in een volgende versie van het paneel."
		},
		plan: {
			title: "Prijzen en plan",
			title_today: "vandaag",
			title_tomorrow: "morgen",
			title_both: "vandaag en morgen",
			period: "Periode",
			today: "Vandaag",
			tomorrow: "Morgen",
			both: "48 uur",
			now: "Nu · {time}",
			per_kwh: "per kWh, all-in",
			unknown: "nog niet bekend",
			expected_at: "meestal rond 13:00",
			known_at: "bekend sinds {time}",
			stats: "gem. {avg} · laagst {low} · hoogst {high}",
			no_prices: "Geen prijzen voor nu. ZEPHYR houdt het net op nul tot er weer prijzen zijn.",
			reserve: "Bewaarde prijzen: de prijsbron heeft nog geen prijs voor nu.",
			indicative: "De prijzen van morgen zijn nog niet bekend. Het plan voor morgen is indicatief (patroon van vandaag, gestreept).",
			no_quarters: "Geen prijzen voor deze periode.",
			now_short: "nu",
			indicative_short: "indicatief",
			tip_buy: "Inkoop {price}",
			tip_sell: "Teruglevering {price}",
			tip_soc: "SOC na dit kwartier {soc}",
			tip_energy: "Zon {solar} · huis {load}",
			aria: "Prijzen per kwartier; laagst {low} om {low_time}, hoogst {high} om {high_time}. Pijltjestoetsen tonen een kwartier.",
			legend_price: "Prijs per kwartier",
			legend_soc: "SOC verwacht",
			legend_past: "Lichter = voorbij (wat er echt gebeurde)",
			mode_note: "Zo zou het plan zijn. ZEPHYR volgt nu de modus {mode}.",
			shadow_note: "ZEPHYR rekent dit plan mee, maar stuurt de accu niet (schaduwmodus).",
			legend_soc_past: "SOC gemeten",
			actual: "werkelijk",
			no_record: "Niet vastgelegd (HA stond uit)",
			tip_soc_past: "SOC na dit kwartier {soc} (gemeten)",
			tip_energy_past: "Zon {solar} · huis {load}",
			legend_solar: "Zon",
			tip_airco: "Airco {kwh} (niet uit de accu)",
			legend_solar_over: "Zon over (accu kan laden)",
			spread: "spread {value}",
			spread_title: "Hoeveel duurder het duurste kwartier is dan het goedkoopste. Ruwe maat voor wat laden en later leveren kan opleveren, vóór verlies (± 14 %) en slijtage. Bij prijzen rond nul of negatief: het verschil in euro."
		},
		blocks: {
			title: "Blokken",
			none: "Geen blokken in het plan.",
			tomorrow: "morgen",
			charge: "{kwh} · gem. {price}",
			deliver: "{kwh} · stroom gem. {price}",
			hold: "stroom gem. {price}",
			export: "{kwh} · gem. {price}",
			what_charge: "Laden uit het net",
			what_deliver: "Leveren aan het huis",
			what_hold: "Vasthouden",
			what_export: "Terugleveren uit de accu",
			indicative: "indicatief",
			title_today: "Blokken vandaag",
			title_tomorrow: "Blokken morgen",
			title_both: "Blokken, 48 uur",
			none_tomorrow: "Nog geen blokken voor morgen."
		},
		why: {
			title: "Waarom dit plan",
			cheapest: "Goedkoopst laden: {time} (gemiddeld {price}).",
			peak: "Duurste moment: {time} ({price}). Daar levert de accu het meeste op.",
			no_charge: "Laden uit het net is in deze periode niet goedkoper dan wachten; de accu gebruikt wat er is.",
			indicative: "Morgen is nog indicatief; de prijzen komen meestal rond 13:00 en dan rekent het plan opnieuw.",
			title_today: "Waarom dit plan, vandaag",
			title_tomorrow: "Waarom dit plan, morgen",
			title_both: "Waarom dit plan"
		},
		sets: {
			none: "Nog geen set gevonden.",
			summary: "Samenvatting",
			batteries: "Accu's",
			all_online: "{n} · alle online",
			some_offline: "{n} · niet alle online",
			soc_spread: "SOC-spreiding",
			warmest: "Warmste accu",
			largest_delta: "Celverschil nu",
			in_short: "In het kort:",
			line_ok: "alles in orde.",
			offline_line: "{sets} is offline; de waarden zijn van de laatste meting.",
			set: "Set {n}",
			packs_n: "{n} accu's",
			power: "Vermogen",
			solar: "Zon",
			inverter: "Omvormer",
			last_full: "Laatst 100 %",
			today: "vandaag",
			unknown: "onbekend",
			switches: "Schakelingen",
			switches_n: "{n} in 24 u",
			limits: "Grenzen in de set",
			add: "+ Set toevoegen",
			max_sets: "Maximaal 3 sets",
			in_set: "Accu's in de set",
			pack_power_note: "Vermogen aan de accukant · − = leveren",
			built_in: "Ingebouwd",
			pack: "Accu {n}",
			unknown_type: "type onbekend",
			temp: "Temperatuur",
			cells: "Cellen",
			cell_delta: "Celverschil",
			cell: {
				good: "Goed",
				balancing: "Balanceert",
				imbalance: "Onbalans",
				null: "–"
			},
			cell_note: "Celverschil = hoogste min laagste celspanning in de accu (de set meldt per 10 mV). In het midden van de lading zegt het weinig: de spanning van LiFePO4 is daar vlak. Het wordt beoordeeld als de accu (bijna) vol is en met weinig stroom laadt (hooguit 0,1 C): tot 30 mV Goed, tot 100 mV Balanceert (normaal bovenin; de set werkt het weg), daarboven Onbalans.",
			balance_title: "Celverschil per dag · afgelopen 7 dagen",
			balance_note: "Grootste celverschil als de accu (bijna) vol was · ▲ = dag met 100 %",
			no_judged: "Niet (bijna) vol geweest",
			full_day: "100 % gehaald",
			activity_title: "Wat deed de set · afgelopen 24 uur",
			no_activity: "Nog geen kwartieren in het kostenlogboek.",
			status: {
				offline: "Offline",
				fault: "Storing",
				calibrating: "Kalibreert",
				bypass: "Bypass",
				standby: "Standby",
				charging: "Laden",
				discharging: "Leveren",
				full: "Vol",
				empty: "Leeg"
			},
			line_now: "{pack} is nu uit balans ({mv} mV). Laat de set een paar keer helemaal vol laden.",
			line_recent: "{pack} was {day} uit balans ({mv} mV); dat trekt meestal bij na een volle lading.",
			line_persistent: "{pack} blijft uit balans ({days} van de laatste 7 dagen). Laat de set een paar keer vol laden; blijft het, neem dan contact op met Zendure.",
			line_not_full: "de accu's zijn deze week niet (bijna) vol geweest; het celverschil is daarom niet beoordeeld.",
			largest_delta_day: "Celverschil {day}",
			not_judged: "bij vol beoordeeld",
			not_judged_title: "Het celverschil wordt beoordeeld als de accu (bijna) vol is en met weinig stroom laadt."
		},
		settings: {
			title: "Instellingen",
			groups: {
				battery: "Accu en grenzen",
				sources: "Bronnen",
				tariffs: "Tarieven",
				planner: "Planner",
				corrections: "Correcties",
				zero_meter: "Nul op de meter zonder planner",
				testing: "Testfase"
			},
			modified_n: "{n} gewijzigd",
			default: "standaard: {value}",
			none: "leeg",
			yes: "aan",
			no: "uit",
			more: "Meer uitleg over {label}",
			readonly: "Alleen een beheerder kan instellingen wijzigen.",
			reload_note: "Wijzigingen in deze groep bewaar je samen; ZEPHYR start daarna kort opnieuw.",
			supplier_note: "Met een leverancier gelden de bedragen uit de tarieventabel ({source}). Alleen bij eigen tarieven zijn ze aan te passen.",
			in_use: "in gebruik: {value}",
			status: {
				unset: "niet ingesteld",
				missing: "niet gevonden: {entities}",
				ok: "werkt",
				interval: "meldt elke {s} s",
				slots: "{n} prijzen in de sensor",
				unavailable: "niet beschikbaar",
				climate: "{mode} · {action}",
				no_step: "nog geen meting",
				steps: "elke {every} een stap van {kwh} kWh"
			},
			own: "Eigen tarieven",
			options: {
				single: "Eén sensor (afname − teruglevering)",
				import_export: "Twee sensoren (afname en teruglevering)",
				heat: "Verwarmen",
				cool: "Koelen",
				dry: "Drogen",
				fan_only: "Ventileren",
				heat_cool: "Verwarmen/koelen",
				auto: "Automatisch",
				off: "Uit"
			},
			fields: {
				min_soc: {
					label: "Minimaal laadpercentage",
					help: "Hieronder levert de accu niet meer.",
					more: "Standaard 10 %. Lager geeft meer bruikbare energie, maar de accu staat dan vaker bijna leeg. Wordt ook in de set zelf gezet, zodat die stopt als ZEPHYR niet draait.\nVoorbeeld: 11 kWh en 10 % = 1,1 kWh blijft altijd over."
				},
				max_soc: {
					label: "Maximaal laadpercentage",
					help: "Hierboven laadt de accu niet verder.",
					more: "Niet op 100 % laden scheelt een beetje slijtage. De set heeft af en toe 100 % nodig om zijn SOC-meting gelijk te zetten en de cellen te balanceren."
				},
				p1_source: {
					label: "P1-meting",
					help: "Eén sensor met het netto vermogen, of afname en teruglevering apart.",
					more: "ZEPHYR kijkt naar het netvermogen en stuurt de accu bij tot het net op nul staat. Hoe vaker de meter meldt, hoe sneller en nauwkeuriger dat gaat. Meldt de meter langer dan 10 s niets, dan stopt ZEPHYR veilig."
				},
				p1_entity: {
					label: "P1-sensor (netto)",
					help: "Vermogen van het net: + = afname, − = teruglevering.",
					more: "Een sensor in W of kW."
				},
				p1_import_entity: {
					label: "P1 afname",
					help: "Vermogen dat uit het net komt.",
					more: "Samen met de teruglevering-sensor; ZEPHYR rekent afname − teruglevering."
				},
				p1_export_entity: {
					label: "P1 teruglevering",
					help: "Vermogen dat naar het net gaat.",
					more: "Samen met de afname-sensor."
				},
				price_entity: {
					label: "Prijssensor",
					help: "Nord Pool met de prijzen van vandaag en morgen.",
					more: "De prijzen van morgen komen rond 13:00. Zonder prijssensor maakt ZEPHYR geen plan; zonder prijzen voor nu valt de planner terug op nul op de meter."
				},
				solar_forecast_entity: {
					label: "Zonverwachting",
					help: "Solcast (morgen) met detail per half uur.",
					more: "Zonder verwachting neemt de planner de opbrengst van gisteren per uur."
				},
				solar_energy_entity: {
					label: "Zonnepanelen-teller",
					help: "Opbrengst in kWh (oplopend).",
					more: "Hiermee weet ZEPHYR wat je panelen echt opbrachten: voor het huisverbruik, het kostenlogboek en het bijstellen van de zonverwachting."
				},
				excluded_energy_entity: {
					label: "Airco: energieteller",
					help: "kWh-teller van een verbruiker die niet uit de accu mag.",
					more: "ZEPHYR schat het vermogen uit de stappen van de teller en levert niet voor de airco zolang die in een geblokkeerde stand draait. De rest van het huis komt wel uit de accu; zon over laadt de accu gewoon."
				},
				excluded_climate_entity: {
					label: "Airco: klimaat-entiteit",
					help: "Zegt direct of hij draait en in welke stand.",
					more: "Zonder deze entiteit ziet ZEPHYR geen verschil tussen verwarmen en koelen en komt de airco nooit uit de accu; een stop merkt ZEPHYR dan pas aan de teller."
				},
				excluded_hvac_modes: {
					label: "Airco: niet uit de accu bij",
					help: "Standen waarin de accu de airco niet voedt.",
					more: "Standaard verwarmen: dan haalt de airco zijn stroom uit het net of van de zon."
				},
				cost_import_counters: {
					label: "Tellers afname",
					help: "De kWh-tellers van je slimme meter (tarief 1 en 2).",
					more: "Voor het kostenlogboek: preciezer dan het vermogen optellen."
				},
				cost_export_counters: {
					label: "Tellers teruglevering",
					help: "De kWh-tellers voor teruglevering (tarief 1 en 2).",
					more: "Voor het kostenlogboek."
				},
				tariff_supplier: {
					label: "Energieleverancier",
					help: "Bedragen uit de tarieventabel van ZEPHYR, of eigen tarieven.",
					more: "De tabel wordt met updates bijgewerkt en elke dag opgehaald. Staat je leverancier er niet in, kies dan eigen tarieven."
				},
				tariff_energy_tax: {
					label: "Energiebelasting",
					help: "Per kWh, zonder btw.",
					more: "Wettelijk bedrag; staat per jaar in de tabel."
				},
				tariff_markup_import: {
					label: "Opslag inkoop",
					help: "Wat de leverancier bovenop de marktprijs rekent, zonder btw.",
					more: "Staat op je contract of factuur."
				},
				tariff_markup_export: {
					label: "Opslag teruglevering",
					help: "Bij de marktprijs opgeteld (negatief = kosten), zonder btw.",
					more: "Sommige leveranciers trekken een vast bedrag af van wat je terugkrijgt: vul dat dan negatief in."
				},
				tariff_vat: {
					label: "Btw",
					help: "Over marktprijs, opslag en energiebelasting.",
					more: "Wettelijk tarief."
				},
				tariff_solar_bonus: {
					label: "Zonnebonus",
					help: "Extra op de terugleverprijs overdag.",
					more: "Bijvoorbeeld 10 % bij Zonneplan. ZEPHYR telt dit alleen mee als de zon op is."
				},
				tariff_fixed_month: {
					label: "Vaste kosten per maand",
					help: "Leveringskosten en netbeheer min heffingskorting.",
					more: "Alleen voor het kostenlogboek; verandert het plan niet."
				},
				plan_wear_cost: {
					label: "Slijtagekosten",
					help: "Per kWh door de accu.",
					more: "De planner laadt en levert alleen als het verschil groter is dan dit bedrag. Standaard € 0,03 (B39)."
				},
				plan_grid_charge_cost: {
					label: "Drempel laden uit het net",
					help: "Minimale winst per kWh om uit het net te laden.",
					more: "Voorkomt laden uit het net voor een heel klein voordeel. Standaard € 0,01."
				},
				plan_allow_export: {
					label: "Terugleveren uit de accu",
					help: "Mag de accu naar het net leveren als dat loont?",
					more: "Alleen zinvol als de terugleverprijs soms hoger is dan wat het later kost om bij te laden, inclusief verlies en slijtage. Standaard uit."
				},
				plan_load_margin: {
					label: "Laadmarge",
					help: "Rekenen met meer verbruik dan geleerd.",
					more: "Bij 10 % rekent de planner met 10 % meer verbruik. Nuttig als de accu op drukke avonden te vroeg leeg is."
				},
				plan_buffer: {
					label: "Buffer",
					help: "Deel van de accu dat de planner niet inplant.",
					more: "De regelaar mag de buffer wel gebruiken als het verbruik hoger uitvalt dan verwacht. Daarna vult de planner hem bij als dat goedkoper is (B37)."
				},
				expensive_hours: {
					label: "Dure uren",
					help: "Zonder planner: alleen in de N duurste uren leveren.",
					more: "Geldt in de modus Nul op de meter met een prijssensor, maar zonder Dynamische Forecasting."
				},
				reserve_soc: {
					label: "Reserve",
					help: "Zonder planner: bijladen tot dit percentage vóór de dure uren.",
					more: "Gaat op in de buffer van de planner (B37)."
				},
				min_price: {
					label: "Minimumprijs",
					help: "Zonder planner: niet leveren onder deze prijs.",
					more: "Leeg = geen minimum."
				},
				live_off_after_restart: {
					label: "Live sturen uit na herstart",
					help: "Na een herstart van HA eerst in de schaduw.",
					more: "Voor de testfase: na elke herstart zet je live sturen zelf weer aan."
				},
				vacation_when_away: {
					label: "Vakantie als niemand thuis is",
					help: "Vanzelf aan na 24 uur zonder iemand thuis.",
					more: "Gebruikt zone.home (het aantal mensen thuis). Uit zodra er iemand terug is. De schakelaar Vakantie (met Vakantie tot) werkt daarnaast altijd."
				},
				workday_entity: {
					label: "Werkdag-sensor",
					help: "Feestdagen tellen als weekenddag.",
					more: "ZEPHYR vraagt de integratie Workday (actie workday.check_date) naar vandaag, morgen en de dagen van de eerste vulling. Zonder sensor zijn maandag t/m vrijdag werkdagen."
				}
			},
			restarting: "ZEPHYR start opnieuw met de nieuwe instellingen…",
			pending: "{n} wijzigingen nog niet bewaard · ZEPHYR start kort opnieuw",
			pending_one: "1 wijziging nog niet bewaard · ZEPHYR start kort opnieuw",
			cancel: "Annuleren",
			save_restart: "Bewaren en herstarten",
			saving: "Bezig…",
			saved: "bewaard",
			not_saved: "niet bewaard",
			reset: "Standaard terugzetten",
			clear: "Leegmaken",
			remove: "Weghalen",
			choose_entity: "Kies of typ een entiteit",
			actions: {
				heating: "draait",
				cooling: "draait",
				drying: "draait",
				fan: "draait",
				preheating: "draait",
				defrosting: "ontdooit",
				idle: "staat stil",
				off: "uit"
			},
			errors: {
				out_of_range: "Buiten de grenzen.",
				off_step: "Past niet bij de stapgrootte.",
				not_a_number: "Geen getal.",
				not_a_bool: "Ongeldige waarde.",
				required: "Mag niet leeg zijn.",
				unknown_choice: "Onbekende keuze.",
				choose_one: "Kies minstens één stand. Uitzetten: maak de teller leeg.",
				not_an_entity: "Dit soort entiteit past hier niet.",
				entity_missing: "Entiteit niet gevonden.",
				unknown_key: "Onbekende instelling.",
				p1_missing: "Kies een P1-sensor.",
				p1_pair_incomplete: "Kies zowel de afname- als de terugleversensor.",
				p1_pair_same: "Afname en teruglevering moeten twee verschillende sensoren zijn.",
				excluded_needs_counter: "De klimaat-entiteit werkt alleen samen met de energieteller van de airco. Kies de teller of maak de klimaat-entiteit leeg.",
				failed: "Bewaren lukte niet. Probeer het opnieuw.",
				range: "Kies een waarde van {min} tot en met {max}{unit}."
			}
		},
		airco: {
			blocked: "Airco {kw} kW · niet uit de accu",
			blocked_unknown: "Airco · niet uit de accu",
			kept_off: "({kw} kW nu buiten de accu)",
			allowed: "Airco {mode} · mag uit de accu",
			estimate: "schatting",
			estimate_more: "Geschat uit de energieteller van de airco (stappen van {kwh} kWh). Tussen twee stappen zakt de schatting vanzelf; stoppen ziet ZEPHYR direct aan de klimaat-entiteit."
		},
		control: {
			mode: "Modus",
			fast: "Snel laden of ontladen",
			fast_charge: "Snel laden",
			fast_discharge: "Snel ontladen",
			running_fast_charge: "Snel laden loopt tot de bovengrens.",
			running_fast_discharge: "Snel ontladen loopt tot de ondergrens.",
			shadow_note: "Schaduwmodus: ZEPHYR rekent mee maar stuurt niets.",
			live_title: "Live sturen aanzetten",
			live_text: "ZEPHYR gaat de accu echt sturen. Uitzetten kan altijd met dezelfde knop.",
			live_blocked: "Live sturen kan nu niet:",
			live_start: "Live sturen",
			cancel: "Annuleren",
			failed: "Lukte niet: {error}",
			close: "Sluiten",
			blocker: {
				no_p1: "Geen P1-sensor gekozen.",
				p1_silent: "De P1-sensor meldt niets.",
				no_sets: "Geen sets.",
				offline: "Set {set} is offline.",
				serial: "Set {set} meldt een ander serienummer.",
				fault: "Set {set} meldt een fout.",
				test: "Er loopt een schrijftest."
			},
			stop_fast: "{mode} stoppen",
			back_to: "Daarna terug naar {mode}."
		},
		diag: {
			title: "Diagnose",
			intro: "Voor een melding op GitHub of hulp op het forum: download de diagnose. Serienummers en IP-adressen worden weggelaten; namen van je entiteiten staan er wel in.",
			download: "Diagnose downloaden",
			export: "Kostenlogboek exporteren",
			busy: "Bezig…",
			exported: "Bewaard in {path} ({rows} kwartieren).",
			failed: "Lukte niet: {error}",
			counters: "Schrijfacties, laatste 24 uur",
			set: "Set",
			ram: "Vermogen",
			flash: "Flash",
			relay: "Relais",
			failed_col: "Mislukt",
			counters_note: "Vermogensopdrachten gaan naar het werkgeheugen; standby en laadgrenzen naar flash (zo min mogelijk). Relais telt de wissels tussen leveren, laden en uit.",
			last_error: "Laatste fout: {error}",
			no_sets: "Geen sets.",
			events: "Gebeurtenissen",
			refresh: "Vernieuwen",
			no_events: "Nog geen gebeurtenissen sinds de laatste start.",
			kind: {
				control: "Regeling",
				mode: "Modus",
				live: "Sturen",
				airco: "Airco",
				write: "Flash",
				warning: "Let op"
			},
			event: {
				reason_code: "Reden: {code}",
				mode: "Modus: {mode}",
				live: "Live sturen aan",
				shadow: "Live sturen uit (schaduwmodus)",
				test: "Schrijftest {power} W",
				test_end: "Schrijftest klaar",
				second_controller: "Iets anders stuurt de set ook (tweede regelaar)",
				excluded_on: "Airco buiten de accu: {kw} kW",
				excluded_off: "Airco niet meer buiten de accu",
				flash: "Set {set}: {cause} in flash geschreven"
			},
			cause: {
				standby: "standby",
				soc_limits: "laadgrenzen",
				test: "schrijftest"
			},
			counters_shadow: "Opdrachten, laatste 24 uur (schaduw)",
			shadow_counts: "Schaduwmodus: geteld wat ZEPHYR zou sturen. Er is niets naar de set geschreven; Mislukt telt alleen echte schrijfacties.",
			profile: "Verbruiksprofiel",
			workday: "Werkdag",
			weekend: "Weekend",
			profile_source: "Geleerd verbruik per uur, waarmee de planner rekent. Bron: {source}.",
			profile_total: "Huis per dag: {kwh} kWh",
			profile_airco: "airco {kwh} kWh (niet uit de accu)",
			profile_house: "Huis (zonder airco)",
			profile_airco_legend: "Airco",
			profile_learned: "nog niet geleerd ({n} van 24 wel): de planner rekent daar met het gemiddelde, {mean} kWh per uur",
			profile_hour: "{hour}:00 · huis {house} kWh · airco {airco} kWh · {n}× gemeten",
			profile_empty_workday: "Nog geen werkdagen geleerd. Tot dan rekent de planner elk uur met het gemiddelde ({mean} kWh).",
			profile_empty_weekend: "Nog geen weekenddagen geleerd. Tot dan rekent de planner op zaterdag en zondag elk uur met het gemiddelde ({mean} kWh)."
		},
		savings: {
			title: "Besparing door de accu",
			period: "Periode",
			p_today: "Vandaag",
			p_week: "Deze week",
			p_month: "Deze maand",
			p_year: "Dit jaar",
			saved: "bespaard",
			lost: "verloren",
			without: "Zonder accu",
			paid: "Betaald",
			no_data: "Nog geen gegevens voor deze periode.",
			incomplete: "{n} van {total} kwartieren zijn onvolledig (HA stond uit of er was geen prijs); de bedragen zijn dan te laag.",
			days_title: "Per dag, laatste 30 dagen",
			days_total: "Samen {amount} over {n} dagen.",
			unknown: "onbekend",
			day_incomplete: "onvolledig",
			leg_win: "Bespaard",
			leg_loss: "Verloren",
			leg_part: "Dag onvolledig",
			split_title: "Waar het vandaan komt, {period}",
			solar_part: "Zon bewaard",
			solar_part_help: "Zon die overdag in de accu ging en 's avonds of 's nachts het huis voedde, in plaats van terug te leveren tegen een lagere prijs.",
			trade_part: "Prijsverschil",
			trade_part_help: "Uit het net laden als stroom goedkoop is en leveren als die duur is. Na verlies; kan negatief zijn als het verschil te klein was.",
			charged: "geladen",
			delivered: "geleverd",
			per_kwh: "bespaard per geleverde kWh",
			notes_title: "Wat telt mee",
			note_compare: "Vergelijking: hetzelfde huis en dezelfde zon, één keer met en één keer zonder accu, met je eigen tarieven per kwartier.",
			note_fixed: "Vaste kosten (vastrecht, netbeheer) zijn met en zonder accu gelijk en tellen niet mee.",
			note_saldering: "Saldering loopt tot {date}; tot dan is teruglevering bijna evenveel waard als afname, en levert zon bewaren minder op.",
			note_since: "Het kostenlogboek loopt sinds {date}; daarvoor is er niets bekend.",
			ps_today: "Vandaag",
			ps_week: "Week",
			ps_month: "Maand",
			ps_year: "Jaar",
			note_hourly: "Dagen vóór {date} zijn achteraf teruggerekend uit de uurstatistiek van HA, met dezelfde rekenwijze maar per uur in plaats van per kwartier: iets minder precies.",
			day_hourly: "teruggerekend per uur",
			leg_hourly: "Teruggerekend per uur",
			optional: "optioneel",
			choose_entity: "Kies of typ een entiteit",
			bf_title: "Eerdere dagen terugrekenen",
			bf_intro: "Het kostenlogboek meet sinds {date}. Voor de dagen daarvoor rekent ZEPHYR de besparing terug uit de uurstatistiek van Home Assistant: je P1-tellers (uit Instellingen), de laad- en leverteller van de accu, zon en prijs.",
			bf_first: "Vanaf",
			bf_charge: "Accu geladen (energieteller, kWh)",
			bf_discharge: "Accu geleverd (energieteller, kWh)",
			bf_solar: "Zon (energieteller)",
			bf_price: "Prijs",
			bf_help: "Kies de tellers van de set uit de periode vóór ZEPHYR, bijvoorbeeld die van de vorige integratie. Uren zonder tellerstand tellen niet mee; uren zonder prijs krijgen geen bedrag. Nog een keer terugrekenen vervangt de vorige keer.",
			bf_run: "Terugrekenen",
			bf_busy: "Bezig…",
			bf_clear: "Teruggerekende dagen weghalen ({n})",
			bf_done: "{n} dagen teruggerekend ({first} – {last}). {skipped} uur zonder tellerstand, {unpriced} uur zonder prijs.",
			bf_nothing: "Geen dagen om terug te rekenen in deze periode.",
			bf_removed: "{n} teruggerekende dagen weggehaald.",
			bf_err_no_counters: "Kies eerst de P1-tellers voor afname en teruglevering in Instellingen → Bronnen.",
			bf_err_no_battery_counters: "Kies de laad- en leverteller van de accu.",
			bf_err_entity_missing: "Niet gevonden: {entities}.",
			bf_err_bad_date: "Ongeldige datum.",
			bf_err_no_connection: "Geen verbinding met Home Assistant.",
			bf_price_ez: "EnergyZero (marktprijs NL per uur, wordt opgehaald)",
			bf_price_sensor: "Een sensor met statistiek in HA",
			bf_price_pick: "Prijssensor",
			bf_ez_failed: "EnergyZero gaf voor {n} dag(en) geen prijzen; probeer het later nog eens."
		}
	},
	en: {
		menu: {
			label: "Main menu",
			plan: "Plan",
			sets: "Sets",
			battery: "Battery",
			settings: "Settings",
			diagnostics: "Diagnostics",
			savings: "Savings"
		},
		header: {
			live: "In control",
			shadow: "Shadow",
			live_title: "ZEPHYR controls the battery",
			shadow_title: "Shadow mode: ZEPHYR calculates but does not control"
		},
		mode: {
			standby: "Standby",
			zero_meter: "Zero on the meter",
			fast_charge: "Fast charge",
			fast_discharge: "Fast discharge",
			dynamic_forecasting: "Dynamic Forecasting"
		},
		action: {
			standby: "Standby",
			charge: "Charging",
			deliver: "Delivering",
			hold: "Holding",
			export: "Exporting",
			blocked: "Blocked",
			calibration: "Calibration"
		},
		now: {
			title: "Now",
			waiting: "Waiting for the first measurement…",
			grid: "Grid {value}",
			shadow_note: "What ZEPHYR would do (shadow mode)."
		},
		battery: {
			title: "Battery",
			of: "{energy} of {capacity}",
			limits: "Limits {min}–{max} %",
			buffer: "buffer {value} %",
			sets: "{online} of {total} sets online",
			set: "1 set",
			set_offline: "set offline",
			unknown: "No data from the set yet"
		},
		next: {
			title: "Next step",
			in: "in {time}",
			now: "now",
			hours: "{h} h {m} min",
			minutes: "{m} min",
			at: "{time} · {action}",
			tomorrow: "tomorrow {time} · {action}",
			charge: "{kwh} from the grid, {price} on average.",
			deliver: "{kwh} from the battery; power then costs {price} on average.",
			export: "{kwh} exported for {price} on average.",
			hold: "The battery keeps its charge; power then costs {price} on average.",
			indicative: "Indicative: tomorrow's prices are not known yet.",
			none: "No more changes in the plan.",
			no_price_source: "Choose a price source in the options to get a plan.",
			no_prices: "No prices since {time}; ZEPHYR keeps the grid at zero.",
			price_now: "Power costs {price} now"
		},
		status: {
			loading: "Loading ZEPHYR…",
			not_loaded: "ZEPHYR is not loaded. Check the integration under Settings → Devices & services.",
			disconnected: "No connection to Home Assistant. The values below are from {time}.",
			reloading: "ZEPHYR is reloading…",
			coming: "This screen comes in a later version of the panel."
		},
		plan: {
			title: "Prices and plan",
			title_today: "today",
			title_tomorrow: "tomorrow",
			title_both: "today and tomorrow",
			period: "Period",
			today: "Today",
			tomorrow: "Tomorrow",
			both: "48 hours",
			now: "Now · {time}",
			per_kwh: "per kWh, all-in",
			unknown: "not known yet",
			expected_at: "usually around 13:00",
			known_at: "known since {time}",
			stats: "avg {avg} · lowest {low} · highest {high}",
			no_prices: "No prices for now. ZEPHYR keeps the grid at zero until prices are back.",
			reserve: "Saved prices: the price source has no price for now yet.",
			indicative: "Tomorrow's prices are not known yet. The plan for tomorrow is indicative (today's pattern, striped).",
			no_quarters: "No prices for this period.",
			now_short: "now",
			indicative_short: "indicative",
			tip_buy: "Buy {price}",
			tip_sell: "Export {price}",
			tip_soc: "SOC after this quarter {soc}",
			tip_energy: "Solar {solar} · house {load}",
			aria: "Prices per quarter; lowest {low} at {low_time}, highest {high} at {high_time}. Arrow keys show a quarter.",
			legend_price: "Price per quarter",
			legend_soc: "SOC expected",
			legend_past: "Lighter = past (what actually happened)",
			mode_note: "This is what the plan would be. ZEPHYR now follows the mode {mode}.",
			shadow_note: "ZEPHYR calculates this plan but does not control the battery (shadow mode).",
			legend_soc_past: "SOC measured",
			actual: "actual",
			no_record: "Not recorded (HA was off)",
			tip_soc_past: "SOC after this quarter {soc} (measured)",
			tip_energy_past: "Solar {solar} · house {load}",
			legend_solar: "Solar",
			tip_airco: "Air con {kwh} (not from the battery)",
			legend_solar_over: "Solar to spare (battery can charge)",
			spread: "spread {value}",
			spread_title: "How much more the most expensive quarter costs than the cheapest. A rough measure of what charging and delivering later can earn, before losses (about 14 %) and wear. With prices around zero or negative: the difference in euro."
		},
		blocks: {
			title: "Blocks",
			none: "No blocks in the plan.",
			tomorrow: "tomorrow",
			charge: "{kwh} · avg {price}",
			deliver: "{kwh} · power avg {price}",
			hold: "power avg {price}",
			export: "{kwh} · avg {price}",
			what_charge: "Charging from the grid",
			what_deliver: "Delivering to the house",
			what_hold: "Holding",
			what_export: "Exporting from the battery",
			indicative: "indicative",
			title_today: "Blocks today",
			title_tomorrow: "Blocks tomorrow",
			title_both: "Blocks, 48 hours",
			none_tomorrow: "No blocks for tomorrow yet."
		},
		why: {
			title: "Why this plan",
			cheapest: "Cheapest charging: {time} ({price} on average).",
			peak: "Most expensive moment: {time} ({price}). That is where the battery saves the most.",
			no_charge: "Charging from the grid is not cheaper than waiting in this period; the battery uses what it has.",
			indicative: "Tomorrow is still indicative; prices usually come around 13:00 and the plan is then recalculated.",
			title_today: "Why this plan, today",
			title_tomorrow: "Why this plan, tomorrow",
			title_both: "Why this plan"
		},
		sets: {
			none: "No set found yet.",
			summary: "Summary",
			batteries: "Batteries",
			all_online: "{n} · all online",
			some_offline: "{n} · not all online",
			soc_spread: "SOC spread",
			warmest: "Warmest battery",
			largest_delta: "Cell difference now",
			in_short: "In short:",
			line_ok: "all fine.",
			offline_line: "{sets} is offline; the values are from the last reading.",
			set: "Set {n}",
			packs_n: "{n} batteries",
			power: "Power",
			solar: "Solar",
			inverter: "Inverter",
			last_full: "Last 100 %",
			today: "today",
			unknown: "unknown",
			switches: "Switches",
			switches_n: "{n} in 24 h",
			limits: "Limits in the set",
			add: "+ Add set",
			max_sets: "At most 3 sets",
			in_set: "Batteries in the set",
			pack_power_note: "Power on the battery side · − = delivering",
			built_in: "Built-in",
			pack: "Battery {n}",
			unknown_type: "unknown type",
			temp: "Temperature",
			cells: "Cells",
			cell_delta: "Cell difference",
			cell: {
				good: "Good",
				balancing: "Balancing",
				imbalance: "Imbalance",
				null: "–"
			},
			cell_note: "Cell difference = highest minus lowest cell voltage in the battery (the set reports per 10 mV). In the middle of the charge it says little: the voltage of LiFePO4 is flat there. It is judged when the battery is (nearly) full with a small current (at most 0.1 C): up to 30 mV Good, up to 100 mV Balancing (normal near full; the set works it away), above that Imbalance.",
			balance_title: "Cell difference per day · last 7 days",
			balance_note: "Largest cell difference when the battery was (nearly) full · ▲ = day with 100 %",
			no_judged: "Not (nearly) full",
			full_day: "reached 100 %",
			activity_title: "What the set did · last 24 hours",
			no_activity: "No quarters in the cost log yet.",
			status: {
				offline: "Offline",
				fault: "Fault",
				calibrating: "Calibrating",
				bypass: "Bypass",
				standby: "Standby",
				charging: "Charging",
				discharging: "Delivering",
				full: "Full",
				empty: "Empty"
			},
			line_now: "{pack} is out of balance now ({mv} mV). Let the set charge fully a few times.",
			line_recent: "{pack} was out of balance on {day} ({mv} mV); that usually evens out after a full charge.",
			line_persistent: "{pack} stays out of balance ({days} of the last 7 days). Let the set charge fully a few times; if it stays, contact Zendure.",
			line_not_full: "the batteries were not (nearly) full this week, so the cell difference was not judged.",
			largest_delta_day: "Cell difference {day}",
			not_judged: "judged when full",
			not_judged_title: "The cell difference is judged when the battery is (nearly) full and the current is small."
		},
		settings: {
			title: "Settings",
			groups: {
				battery: "Battery and limits",
				sources: "Sources",
				tariffs: "Tariffs",
				planner: "Planner",
				corrections: "Corrections",
				zero_meter: "Zero on the meter without planner",
				testing: "Test phase"
			},
			modified_n: "{n} changed",
			default: "standard: {value}",
			none: "empty",
			yes: "on",
			no: "off",
			more: "More about {label}",
			readonly: "Only an administrator can change settings.",
			reload_note: "Changes in this group are saved together; ZEPHYR then restarts briefly.",
			supplier_note: "With a supplier the amounts from the tariff table apply ({source}). They can only be changed with own tariffs.",
			in_use: "in use: {value}",
			status: {
				unset: "not set",
				missing: "not found: {entities}",
				ok: "working",
				interval: "reports every {s} s",
				slots: "{n} prices in the sensor",
				unavailable: "unavailable",
				climate: "{mode} · {action}",
				no_step: "no measurement yet",
				steps: "a step of {kwh} kWh every {every}"
			},
			own: "Own tariffs",
			options: {
				single: "One sensor (import − export)",
				import_export: "Two sensors (import and export)",
				heat: "Heating",
				cool: "Cooling",
				dry: "Drying",
				fan_only: "Fan",
				heat_cool: "Heating/cooling",
				auto: "Auto",
				off: "Off"
			},
			fields: {
				min_soc: {
					label: "Minimum state of charge",
					help: "Below this the battery stops delivering.",
					more: "Default 10 %. Lower gives more usable energy, but the battery is more often nearly empty. Also written to the set, so it stops when ZEPHYR is not running."
				},
				max_soc: {
					label: "Maximum state of charge",
					help: "Above this the battery stops charging.",
					more: "Not charging to 100 % saves a little wear. The set needs 100 % now and then to reset its SOC and balance the cells."
				},
				p1_source: {
					label: "P1 measurement",
					help: "One sensor with net power, or import and export separately.",
					more: "ZEPHYR watches the grid and steers the battery until the grid is at zero. The more often the meter reports, the faster and more precise. When the meter is silent for more than 10 s, ZEPHYR stops safely."
				},
				p1_entity: {
					label: "P1 sensor (net)",
					help: "Grid power: + = import, − = export.",
					more: "A sensor in W or kW."
				},
				p1_import_entity: {
					label: "P1 import",
					help: "Power from the grid.",
					more: "Together with the export sensor; ZEPHYR uses import − export."
				},
				p1_export_entity: {
					label: "P1 export",
					help: "Power to the grid.",
					more: "Together with the import sensor."
				},
				price_entity: {
					label: "Price sensor",
					help: "Nord Pool with today's and tomorrow's prices.",
					more: "Tomorrow's prices arrive around 13:00. Without a price sensor ZEPHYR makes no plan."
				},
				solar_forecast_entity: {
					label: "Solar forecast",
					help: "Solcast (tomorrow) with half-hour detail.",
					more: "Without a forecast the planner uses yesterday's production per hour."
				},
				solar_energy_entity: {
					label: "Solar counter",
					help: "Production in kWh (increasing).",
					more: "Tells ZEPHYR what your panels really produced: for the house consumption, the cost log and correcting the forecast."
				},
				excluded_energy_entity: {
					label: "Air conditioner: energy counter",
					help: "kWh counter of a load the battery may not feed.",
					more: "ZEPHYR estimates the power from the counter steps and does not deliver for the air conditioner while it runs in a blocked mode. The rest of the house still comes from the battery; solar surplus still charges it."
				},
				excluded_climate_entity: {
					label: "Air conditioner: climate entity",
					help: "Says at once whether it runs and in which mode.",
					more: "Without it ZEPHYR cannot tell heating from cooling and never feeds the air conditioner from the battery; it also notices a stop only from the counter."
				},
				excluded_hvac_modes: {
					label: "Air conditioner: not from the battery when",
					help: "Modes in which the battery does not feed it.",
					more: "Default heating: while heating, the air conditioner takes from the grid or from solar."
				},
				cost_import_counters: {
					label: "Import counters",
					help: "The kWh counters of your smart meter (tariff 1 and 2).",
					more: "For the cost log: more precise than adding up power."
				},
				cost_export_counters: {
					label: "Export counters",
					help: "The kWh counters for export (tariff 1 and 2).",
					more: "For the cost log."
				},
				tariff_supplier: {
					label: "Energy supplier",
					help: "Amounts from ZEPHYR's tariff table, or own tariffs.",
					more: "The table is updated with releases and fetched daily. Supplier not listed? Choose own tariffs."
				},
				tariff_energy_tax: {
					label: "Energy tax",
					help: "Per kWh, excluding VAT.",
					more: "Statutory amount; listed per year in the table."
				},
				tariff_markup_import: {
					label: "Import margin",
					help: "What the supplier adds to the market price, excluding VAT.",
					more: "See your contract or invoice."
				},
				tariff_markup_export: {
					label: "Export margin",
					help: "Added to the market price (negative = a fee), excluding VAT.",
					more: "Some suppliers deduct a fixed amount from what you get back: enter it as negative."
				},
				tariff_vat: {
					label: "VAT",
					help: "On market price, margin and energy tax.",
					more: "Statutory rate."
				},
				tariff_solar_bonus: {
					label: "Solar bonus",
					help: "Extra on the export price during the day.",
					more: "For example 10 % with Zonneplan. Only counted while the sun is up."
				},
				tariff_fixed_month: {
					label: "Fixed costs per month",
					help: "Supply and network costs minus tax credit.",
					more: "Only for the cost log; does not change the plan."
				},
				plan_wear_cost: {
					label: "Wear cost",
					help: "Per kWh through the battery.",
					more: "The planner only charges and delivers when the difference is larger than this. Default €0.03 (B39)."
				},
				plan_grid_charge_cost: {
					label: "Grid charging threshold",
					help: "Minimum gain per kWh to charge from the grid.",
					more: "Avoids charging from the grid for a tiny gain. Default €0.01."
				},
				plan_allow_export: {
					label: "Export from the battery",
					help: "May the battery deliver to the grid when that pays?",
					more: "Only useful when the export price is sometimes higher than recharging later, including losses and wear. Off by default."
				},
				plan_load_margin: {
					label: "Consumption margin",
					help: "Plan with more consumption than learned.",
					more: "At 10 % the planner assumes 10 % more consumption."
				},
				plan_buffer: {
					label: "Buffer",
					help: "Part of the battery the planner keeps free.",
					more: "The controller may use the buffer when consumption is higher than expected; the planner refills it when that is cheaper (B37)."
				},
				expensive_hours: {
					label: "Expensive hours",
					help: "Without planner: only deliver in the N most expensive hours.",
					more: "Applies in Zero on the meter with a price sensor but without Dynamic Forecasting."
				},
				reserve_soc: {
					label: "Reserve",
					help: "Without planner: charge to this level before the expensive hours.",
					more: "Becomes the planner's buffer (B37)."
				},
				min_price: {
					label: "Minimum price",
					help: "Without planner: do not deliver below this price.",
					more: "Empty = no minimum."
				},
				live_off_after_restart: {
					label: "Control off after restart",
					help: "After a restart of HA start in shadow mode.",
					more: "For the test phase: after every restart you switch control on yourself."
				},
				vacation_when_away: {
					label: "Vacation when nobody is home",
					help: "On by itself after 24 hours with nobody home.",
					more: "Uses zone.home (the number of people at home). Off as soon as someone is back. The switch Vacation (with Vacation until) always works as well."
				},
				workday_entity: {
					label: "Workday sensor",
					help: "Holidays count as weekend days.",
					more: "ZEPHYR asks the Workday integration (action workday.check_date) about today, tomorrow and the days of the first fill. Without it Monday to Friday are workdays."
				}
			},
			restarting: "ZEPHYR is restarting with the new settings…",
			pending: "{n} changes not saved yet · ZEPHYR restarts briefly",
			pending_one: "1 change not saved yet · ZEPHYR restarts briefly",
			cancel: "Cancel",
			save_restart: "Save and restart",
			saving: "Saving…",
			saved: "saved",
			not_saved: "not saved",
			reset: "Restore standard",
			clear: "Clear",
			remove: "Remove",
			choose_entity: "Choose or type an entity",
			actions: {
				heating: "running",
				cooling: "running",
				drying: "running",
				fan: "running",
				preheating: "running",
				defrosting: "defrosting",
				idle: "idle",
				off: "off"
			},
			errors: {
				out_of_range: "Outside the limits.",
				off_step: "Does not fit the step size.",
				not_a_number: "Not a number.",
				not_a_bool: "Invalid value.",
				required: "May not be empty.",
				unknown_choice: "Unknown choice.",
				choose_one: "Choose at least one mode. To switch off: clear the counter.",
				not_an_entity: "This kind of entity does not fit here.",
				entity_missing: "Entity not found.",
				unknown_key: "Unknown setting.",
				p1_missing: "Choose a P1 sensor.",
				p1_pair_incomplete: "Choose both the import and the export sensor.",
				p1_pair_same: "Import and export must be two different sensors.",
				excluded_needs_counter: "The climate entity only works together with the air conditioner's energy counter. Choose the counter or clear the climate entity.",
				failed: "Saving failed. Please try again.",
				range: "Choose a value from {min} to {max}{unit}."
			}
		},
		airco: {
			blocked: "Air conditioner {kw} kW · not from the battery",
			blocked_unknown: "Air conditioner · not from the battery",
			kept_off: "({kw} kW kept off the battery now)",
			allowed: "Air conditioner {mode} · may use the battery",
			estimate: "estimate",
			estimate_more: "Estimated from the air conditioner's energy counter (steps of {kwh} kWh). Between two steps the estimate drops by itself; ZEPHYR sees a stop at once from the climate entity."
		},
		control: {
			mode: "Mode",
			fast: "Fast charge or discharge",
			fast_charge: "Fast charge",
			fast_discharge: "Fast discharge",
			running_fast_charge: "Fast charging runs up to the upper limit.",
			running_fast_discharge: "Fast discharging runs down to the lower limit.",
			shadow_note: "Shadow mode: ZEPHYR computes but does not control.",
			live_title: "Turn on live control",
			live_text: "ZEPHYR will really control the battery. You can always turn it off with the same button.",
			live_blocked: "Live control is not possible now:",
			live_start: "Control live",
			cancel: "Cancel",
			failed: "Did not work: {error}",
			close: "Close",
			blocker: {
				no_p1: "No P1 sensor chosen.",
				p1_silent: "The P1 sensor is not reporting.",
				no_sets: "No sets.",
				offline: "Set {set} is offline.",
				serial: "Set {set} reports a different serial number.",
				fault: "Set {set} reports an error.",
				test: "A write test is running."
			},
			stop_fast: "Stop {mode}",
			back_to: "Then back to {mode}."
		},
		diag: {
			title: "Diagnostics",
			intro: "For an issue on GitHub or help on the forum: download the diagnostics. Serial numbers and IP addresses are left out; your entity names are included.",
			download: "Download diagnostics",
			export: "Export cost log",
			busy: "Working…",
			exported: "Saved in {path} ({rows} quarters).",
			failed: "Did not work: {error}",
			counters: "Writes, last 24 hours",
			set: "Set",
			ram: "Power",
			flash: "Flash",
			relay: "Relay",
			failed_col: "Failed",
			counters_note: "Power commands go to working memory; standby and charge limits to flash (as few as possible). Relay counts the switches between delivering, charging and off.",
			last_error: "Last error: {error}",
			no_sets: "No sets.",
			events: "Events",
			refresh: "Refresh",
			no_events: "No events since the last start.",
			kind: {
				control: "Control",
				mode: "Mode",
				live: "Live",
				airco: "Air con",
				write: "Flash",
				warning: "Warning"
			},
			event: {
				reason_code: "Reason: {code}",
				mode: "Mode: {mode}",
				live: "Live control on",
				shadow: "Live control off (shadow mode)",
				test: "Write test {power} W",
				test_end: "Write test finished",
				second_controller: "Something else controls the set too (second controller)",
				excluded_on: "Air conditioner outside the battery: {kw} kW",
				excluded_off: "Air conditioner no longer outside the battery",
				flash: "Set {set}: {cause} written to flash"
			},
			cause: {
				standby: "standby",
				soc_limits: "charge limits",
				test: "write test"
			},
			counters_shadow: "Commands, last 24 hours (shadow)",
			shadow_counts: "Shadow mode: counted what ZEPHYR would send. Nothing was written to the set; Failed only counts real writes.",
			profile: "Use profile",
			workday: "Workday",
			weekend: "Weekend",
			profile_source: "Learned use per hour that the planner works with. Source: {source}.",
			profile_total: "House per day: {kwh} kWh",
			profile_airco: "air con {kwh} kWh (not from the battery)",
			profile_house: "House (without air con)",
			profile_airco_legend: "Air con",
			profile_learned: "not learned yet ({n} of 24 are): the planner uses the mean there, {mean} kWh per hour",
			profile_hour: "{hour}:00 · house {house} kWh · air con {airco} kWh · measured {n}×",
			profile_empty_workday: "No workdays learned yet. Until then the planner uses the mean for every hour ({mean} kWh).",
			profile_empty_weekend: "No weekend days learned yet. Until then the planner uses the mean for every hour on Saturday and Sunday ({mean} kWh)."
		},
		savings: {
			title: "Savings from the battery",
			period: "Period",
			p_today: "Today",
			p_week: "This week",
			p_month: "This month",
			p_year: "This year",
			saved: "saved",
			lost: "lost",
			without: "Without battery",
			paid: "Paid",
			no_data: "No data for this period yet.",
			incomplete: "{n} of {total} quarters are incomplete (HA was off or there was no price); the amounts are then too low.",
			days_title: "Per day, last 30 days",
			days_total: "Together {amount} over {n} days.",
			unknown: "unknown",
			day_incomplete: "incomplete",
			leg_win: "Saved",
			leg_loss: "Lost",
			leg_part: "Day incomplete",
			split_title: "Where it comes from, {period}",
			solar_part: "Solar kept",
			solar_part_help: "Solar that went into the battery during the day and fed the house in the evening or night, instead of being exported at a lower price.",
			trade_part: "Price difference",
			trade_part_help: "Charging from the grid when power is cheap and delivering when it is expensive. After losses; can be negative when the difference was too small.",
			charged: "charged",
			delivered: "delivered",
			per_kwh: "saved per delivered kWh",
			notes_title: "What counts",
			note_compare: "Comparison: the same house and the same solar, once with and once without the battery, with your own tariffs per quarter.",
			note_fixed: "Fixed costs (standing charge, grid operator) are the same with and without the battery and do not count.",
			note_saldering: "Net metering runs until {date}; until then exporting is worth almost as much as importing, and keeping solar earns less.",
			note_since: "The cost log runs since {date}; nothing is known before that.",
			ps_today: "Today",
			ps_week: "Week",
			ps_month: "Month",
			ps_year: "Year",
			note_hourly: "Days before {date} were worked out afterwards from HA's hourly statistics, with the same method but per hour instead of per quarter: a little less precise.",
			day_hourly: "worked out per hour",
			leg_hourly: "Worked out per hour",
			optional: "optional",
			choose_entity: "Choose or type an entity",
			bf_title: "Work out earlier days",
			bf_intro: "The cost log measures since {date}. For the days before, ZEPHYR works out the savings from Home Assistant's hourly statistics: your P1 counters (from Settings), the battery's charge and discharge counters, solar and price.",
			bf_first: "From",
			bf_charge: "Battery charged (energy counter, kWh)",
			bf_discharge: "Battery delivered (energy counter, kWh)",
			bf_solar: "Solar (energy counter)",
			bf_price: "Price",
			bf_help: "Choose the set's counters from the period before ZEPHYR, for example those of the previous integration. Hours without a counter reading do not count; hours without a price get no amount. Working out again replaces the previous run.",
			bf_run: "Work out",
			bf_busy: "Working…",
			bf_clear: "Remove worked-out days ({n})",
			bf_done: "{n} days worked out ({first} – {last}). {skipped} hours without a counter reading, {unpriced} hours without a price.",
			bf_nothing: "No days to work out in this period.",
			bf_removed: "{n} worked-out days removed.",
			bf_err_no_counters: "First choose the P1 counters for import and export in Settings → Sources.",
			bf_err_no_battery_counters: "Choose the battery's charge and discharge counters.",
			bf_err_entity_missing: "Not found: {entities}.",
			bf_err_bad_date: "Invalid date.",
			bf_err_no_connection: "No connection with Home Assistant.",
			bf_price_ez: "EnergyZero (Dutch market price per hour, fetched)",
			bf_price_sensor: "A sensor with statistics in HA",
			bf_price_pick: "Price sensor",
			bf_ez_failed: "EnergyZero gave no prices for {n} day(s); try again later."
		}
	}
};
function Je(e) {
	return e?.toLowerCase().startsWith("nl") ? "nl" : "en";
}
function L(e, t, n = {}) {
	let r = (e) => {
		let n = e;
		for (let e of t.split(".")) {
			if (typeof n != "object" || !n) return;
			n = n[e];
		}
		return typeof n == "string" ? n : void 0;
	};
	return (r(qe[e]) ?? r(qe.en) ?? t).replace(/\{(\w+)\}/g, (e, t) => t in n ? String(n[t]) : e);
}
// src/airco.ts
var Ye = /* @__PURE__ */ new Set(["idle", "off"]);
function Xe(e, t) {
	return new Intl.NumberFormat(t, {
		minimumFractionDigits: 1,
		maximumFractionDigits: 1
	}).format(e / 1e3);
}
function Ze(e, t, n) {
	if (!e) return null;
	let r = e.mode === "heat" ? "heat" : e.mode === "cool" ? "cool" : null;
	if (e.active) {
		let i = e.power_w > 0 ? L(t, "airco.blocked", { kw: Xe(e.power_w, n) }) : L(t, "airco.blocked_unknown");
		e.excluded_w > 0 && e.excluded_w < e.power_w - 50 && (i += ` ${L(t, "airco.kept_off", { kw: Xe(e.excluded_w, n) })}`);
		let a = e.quality === "fading" || e.quality === "starting" ? L(t, "airco.estimate_more", { kwh: new Intl.NumberFormat(n, { maximumFractionDigits: 2 }).format(e.last_step_kwh || .25) }) : null;
		return {
			text: i,
			allowed: !1,
			estimate: a,
			icon: r
		};
	}
	return e.has_climate && e.mode && e.mode !== "off" && e.action && !Ye.has(e.action) ? {
		text: L(t, "airco.allowed", { mode: L(t, `settings.options.${e.mode}`).toLowerCase() }),
		allowed: !0,
		estimate: null,
		icon: r
	} : null;
}
// src/plan.ts
var R = (e, t) => new Intl.DateTimeFormat("en-CA", {
	year: "numeric",
	month: "2-digit",
	day: "2-digit",
	timeZone: t
}).format(new Date(e));
function Qe(e, t) {
	let n = [];
	for (let r of e) {
		let e = R(r.start, t);
		n[n.length - 1] !== e && n.push(e);
	}
	return n;
}
function $e(e, t, n) {
	if (t === "both") return e;
	let r = Qe(e, n)[t === "today" ? 0 : 1];
	return r ? e.filter((e) => R(e.start, n) === r) : [];
}
function z(e, t, n) {
	let r = Qe(e, n)[t];
	return r ? e.filter((e) => R(e.start, n) === r) : [];
}
function B(e) {
	let t = e.filter((e) => e.buy !== null && !e.indicative);
	if (!t.length) return null;
	let n = t[0], r = t[0], i = 0;
	for (let e of t) {
		let t = e.buy;
		t < n.buy && (n = e), t > r.buy && (r = e), i += t;
	}
	return {
		min: n,
		max: r,
		avg: i / t.length
	};
}
function V(e) {
	return e.findIndex((e) => !e.past);
}
function et(e) {
	let t = [];
	return e.forEach((e, n) => {
		let r = t[t.length - 1];
		r && r.action === e.action && r.past === e.past ? r.count += 1 : t.push({
			action: e.action,
			past: e.past,
			from: n,
			count: 1
		});
	}), t;
}
function tt(e) {
	let t = e.map((e) => e.buy).filter((e) => e !== null);
	if (!t.length) return {
		lo: 0,
		hi: .4
	};
	let n = Math.min(0, Math.floor(Math.min(...t) * 20) / 20);
	return {
		lo: n,
		hi: Math.max(n + .05, Math.ceil(Math.max(...t) * 20) / 20)
	};
}
function nt(e, t) {
	let n = t.hi - t.lo, r = Math.min(e, 0), i = Math.max(e, 0);
	return {
		bottom: (r - t.lo) / n * 100,
		height: Math.max((i - r) / n * 100, .8)
	};
}
function rt(e, t, n) {
	let r = new Intl.DateTimeFormat("en-GB", {
		hour: "2-digit",
		minute: "2-digit",
		hour12: !1,
		timeZone: n
	}), i = [];
	return e.forEach((e, n) => {
		let [a, o] = r.format(new Date(e.start)).split(":").map(Number);
		o === 0 && a % t === 0 && i.push(n);
	}), i;
}
function it(e, t) {
	let n = V(e), r = [];
	return n >= 0 && t !== null && r.push(`${n},${(100 - t).toFixed(1)}`), e.forEach((e, t) => {
		!e.past && e.soc !== null && r.push(`${t + 1},${(100 - e.soc).toFixed(1)}`);
	}), r.join(" ");
}
function at(e, t) {
	let n = V(e), r = [], i = [];
	return e.forEach((e, t) => {
		e.past && (e.soc === null ? (i.length && r.push(i), i = []) : i.push(`${t + 1},${(100 - e.soc).toFixed(1)}`));
	}), i.length && (n >= 0 && t !== null && i[i.length - 1].startsWith(`${n},`) && i.push(`${n},${(100 - t).toFixed(1)}`), r.push(i)), r.filter((e) => e.length > 1).map((e) => e.join(" "));
}
function ot(e, t) {
	let n = new Date(t).getTime();
	return e.filter((e) => new Date(e.end).getTime() > n);
}
function st(e, t, n, r, i) {
	let a = ot(e, n);
	if (t === "both") return a;
	let o = t === "today" ? R(n, i) : r;
	return o ? a.filter((e) => {
		let t = R(e.start, i), n = R((/* @__PURE__ */ new Date(new Date(e.end).getTime() - 1)).toISOString(), i);
		return t <= o && o <= n;
	}) : [];
}
function ct(e) {
	if (!e.some((e) => e.solar !== null)) return null;
	let t = Math.max(.05, ...e.map((e) => e.solar ?? 0));
	return e.map((e) => {
		let n = e.solar ?? 0, r = (e.load ?? 0) + (e.excluded ?? 0);
		return {
			height: n > 0 ? Math.round(n / t * 1e3) / 10 : 0,
			past: e.past,
			over: n > 0 && e.load !== null && n > r
		};
	});
}
function lt(e, t) {
	return e <= .005 ? null : Math.round((t - e) / e * 100);
}
// src/theme.ts
var ut = o`
  :host {
    --z-bg: #f4f5f2;
    --z-card: #ffffff;
    --z-border: #e1e4de;
    --z-text: #1a1e1c;
    --z-muted: #565d59;
    --z-track: #e8ebe6;
    --z-on-text: #ffffff;
    --z-charge: #1f5fc4;
    --z-deliver: #f0a04b;
    --z-hold-a: #aeb8c8;
    --z-hold-b: #eef1f6;
    --z-export: #16917a;
    --z-solar: #f2c230;
    --z-warn-bg: #fdebd5;
    --z-warn-text: #5c3300;
    --z-info-bg: #eef3fb;
    --z-bar: #8c9792;
    --z-good-bg: #ddf2ec;
    --z-good-text: #0b5a4b;
    --z-bad-bg: #fbdcdc;
    --z-bad-text: #7a1414;
    --z-font: Inter, system-ui, -apple-system, "Segoe UI", sans-serif;
    --z-font-head: "Space Grotesk", Inter, system-ui, sans-serif;
  }
  :host([dark]) {
    --z-bg: #0f1211;
    --z-card: #191d1b;
    --z-border: #2b312e;
    --z-text: #ecefec;
    --z-muted: #a4aca7;
    --z-track: #2b312e;
    --z-on-text: #0f1211;
    --z-charge: #3d7be6;
    --z-deliver: #f2a65a;
    --z-hold-a: #56607a;
    --z-hold-b: #232833;
    --z-export: #3cc4a8;
    --z-solar: #e8c547;
    --z-warn-bg: #3a2a14;
    --z-warn-text: #f7d4a8;
    --z-info-bg: #1b2433;
    --z-bar: #6f7a75;
    --z-good-bg: #163b33;
    --z-good-text: #9fe3cf;
    --z-bad-bg: #3d1a1a;
    --z-bad-text: #f5b4b4;
  }
`;
function H(e) {
	switch (e) {
		case "charge": return "var(--z-charge)";
		case "deliver": return "var(--z-deliver)";
		case "export": return "var(--z-export)";
		case "hold": return "repeating-linear-gradient(45deg, var(--z-hold-a) 0 3px, var(--z-hold-b) 3px 6px)";
		default: return "var(--z-muted)";
	}
}
// \0@oxc-project+runtime@0.156.0/helpers/esm/decorate.js
function U(e, t, n, r) {
	var i = arguments.length, a = i < 3 ? t : r === null ? r = Object.getOwnPropertyDescriptor(t, n) : r, o;
	if (typeof Reflect == "object" && typeof Reflect.decorate == "function") a = Reflect.decorate(e, t, n, r);
	else for (var s = e.length - 1; s >= 0; s--) (o = e[s]) && (a = (i < 3 ? o(a) : i > 3 ? o(t, n, a) : o(t, n)) || a);
	return i > 3 && a && Object.defineProperty(t, n, a), a;
}
// src/prices-plan.ts
var dt = "zephyr.period", ft = [
	["today", "plan.today"],
	["tomorrow", "plan.tomorrow"],
	["both", "plan.both"]
];
function pt() {
	try {
		let e = window.localStorage.getItem(dt);
		return e === "tomorrow" || e === "both" ? e : "today";
	} catch {
		return "today";
	}
}
var W = class extends D {
	constructor(...e) {
		super(...e), this.uiLang = "en", this.locale = "en", this.timeZone = "UTC", this.narrow = !1, this.period = pt(), this.sel = null, this.scrolledFor = "";
	}
	tr(e, t = {}) {
		return L(this.uiLang, e, t);
	}
	pick(e) {
		this.period = e, this.dispatchEvent(new CustomEvent("zephyr-period", {
			detail: e,
			bubbles: !0,
			composed: !0
		})), this.sel = null, this.scrolledFor = "";
		try {
			window.localStorage.setItem(dt, e);
		} catch {}
	}
	updated(e) {
		let t = this.renderRoot.querySelector(".scroll"), n = this.visible(), r = `${this.period}|${this.view?.now ?? ""}`;
		if (!t || t.scrollWidth <= t.clientWidth || this.scrolledFor === r) return;
		this.scrolledFor = r;
		let i = V(n);
		i > 0 && (t.scrollLeft = Math.max(0, i - 8) / n.length * t.scrollWidth);
	}
	visible() {
		return this.view ? $e(this.view.quarters, this.period, this.timeZone) : [];
	}
	render() {
		let e = this.view;
		if (!e) return S`<section class="card"><div class="skeleton" aria-hidden="true"></div></section>`;
		let t = this.visible(), n = z(e.quarters, 0, this.timeZone), r = z(e.quarters, 1, this.timeZone), i = B(n), a = B(r), o = V(e.quarters), s = o >= 0 ? e.quarters[o] : void 0, c = this.period === "today" ? "plan.title_today" : this.period === "tomorrow" ? "plan.title_tomorrow" : "plan.title_both";
		return S`<section class="card" aria-label=${this.tr("plan.title")}>
      <div class="head">
        <h2>${this.tr("plan.title")} · ${this.tr(c)}</h2>
        <div class="tabs" role="group" aria-label=${this.tr("plan.period")}>
          ${ft.map(([e, t]) => S`<button
                type="button"
                class=${this.period === e ? "on" : ""}
                aria-pressed=${this.period === e ? "true" : "false"}
                @click=${() => this.pick(e)}
              >
                ${this.tr(t)}
              </button>`)}
        </div>
      </div>
      <div class="prices">
        <div class="cell now">
          <span class="cap">${this.tr("plan.now", { time: s ? P(s.start, this.locale, this.timeZone) : "–" })}</span>
          <span class="value">${s?.buy == null ? "–" : j(s.buy, this.locale)}</span>
          <span class="sub">${this.tr("plan.per_kwh")}</span>
        </div>
        ${this.statCell(n, i, "plan.today")} ${this.statCell(r, a, "plan.tomorrow", !0)}
      </div>
      ${this.notes(e, a)} ${t.length ? this.chart(t) : S`<p class="empty">${this.tr("plan.no_quarters")}</p>`}
      ${this.legend()}
    </section>`;
	}
	spreadText(e) {
		let t = e.min.buy, n = e.max.buy, r = lt(t, n);
		return r === null ? this.tr("plan.spread", { value: j(n - t, this.locale) }) : this.tr("plan.spread", { value: `${r} %` });
	}
	statCell(e, t, n, r = !1) {
		let i = e.length ? F(e[0].start, this.locale, this.timeZone) : "";
		if (!t) return S`<div class="cell">
        <span class="cap">${this.tr(n)} · ${i}</span>
        <span class="value small">${this.tr("plan.unknown")}</span>
        <span class="sub">${r ? this.tr("plan.expected_at") : ""}</span>
      </div>`;
		let a = r && this.view?.tomorrow_known_at ? ` · ${this.tr("plan.known_at", { time: P(this.view.tomorrow_known_at, this.locale, this.timeZone) })}` : "";
		return S`<div class="cell">
      <span class="cap">${this.tr(n)} · ${i}</span>
      <span class="value"
        >${j(t.min.buy, this.locale)} – ${j(t.max.buy, this.locale)}<span class="spread" title=${this.tr("plan.spread_title")}
          >${this.spreadText(t)}</span
        ></span
      >
      <span class="sub"
        >${this.tr("plan.stats", {
			avg: j(t.avg, this.locale),
			low: P(t.min.start, this.locale, this.timeZone),
			high: P(t.max.start, this.locale, this.timeZone)
		})}${a}</span
      >
    </div>`;
	}
	notes(e, t) {
		let n = [];
		return e.state === "no_prices" && n.push(S`<p class="note warn">${this.tr("plan.no_prices")}</p>`), e.state === "price_reserve" && n.push(S`<p class="note">${this.tr("plan.reserve")}</p>`), !t && this.period !== "today" && n.push(S`<p class="note">${this.tr("plan.indicative")}</p>`), n.length ? S`${n}` : w;
	}
	chart(e) {
		let t = e.length, n = tt(e), r = V(e), i = (e) => `${(e / t * 100).toFixed(3)}%`, a = Qe(e, this.timeZone), o = a.length > 1 ? e.findIndex((t) => new Date(t.start).getTime() >= new Date(z(e, 1, this.timeZone)[0].start).getTime()) : -1, s = [];
		for (let t = 0; t < a.length; t++) {
			let n = B(z(e, t, this.timeZone));
			n && (s.push({
				q: n.min,
				i: e.indexOf(n.min),
				kind: "plan.lowest"
			}), s.push({
				q: n.max,
				i: e.indexOf(n.max),
				kind: "plan.highest"
			}));
		}
		let c = rt(e, this.period === "both" ? 6 : 3, this.timeZone), l = this.sel !== null && this.sel < t ? this.sel : null, u = it(e, this.view?.soc_now ?? null), d = at(e, this.view?.soc_now ?? null), f = n.lo < 0 ? (0 - n.lo) / (n.hi - n.lo) * 100 : null;
		return S`<div class="scroll">
      <div class="chart ${t > 100 ? "wide" : ""}">
        <div class="axis left" aria-hidden="true">
          <span>${j(n.hi, this.locale)}</span><span>${j((n.hi + n.lo) / 2, this.locale)}</span><span>${j(n.lo, this.locale)}</span>
        </div>
        <div class="axis right" aria-hidden="true"><span>100 %</span><span>50 %</span><span>0 %</span></div>
        <div
          class="plot"
          tabindex="0"
          role="img"
          aria-label=${this.summary(e)}
          @pointermove=${(e) => this.hover(e, t)}
          @pointerleave=${() => this.sel = null}
          @keydown=${(e) => this.key(e, t, r)}
          @blur=${() => this.sel = null}
        >
          <div class="grid" style="top:0"></div>
          <div class="grid" style="top:50%"></div>
          ${f === null ? w : S`<div class="zero" style="bottom:${f}%"></div>`}
          ${e.map((e, t) => {
			if (e.buy === null) return w;
			let a = nt(e.buy, n);
			return S`<div class=${`bar${e.past ? " past" : ""}${e.indicative ? " ind" : ""}${t === r ? " cur" : ""}${t === l ? " focus" : ""}`} style="left:${i(t)};width:${i(1)};bottom:${a.bottom}%;height:${a.height}%"></div>`;
		})}
          <svg viewBox="0 0 ${t} 100" preserveAspectRatio="none" aria-hidden="true">
            ${d.map((e) => we`<polyline class="halo" points=${e}></polyline><polyline class="soc measured" points=${e}></polyline>`)}
            ${u ? we`<polyline class="halo" points=${u}></polyline><polyline class="soc" points=${u}></polyline>` : w}
          </svg>
          ${o > 0 ? S`<div class="split" style="left:${i(o)}"></div>
                <span class="dayname" style="left:calc(${i(o)} + 6px)">${F(e[o].start, this.locale, this.timeZone)}</span>` : w}
          ${s.map(({ q: e, i: r }) => {
			let i = Math.min(94, Math.max(6, (r + .5) / t * 100)), a = nt(e.buy, n);
			return S`<span class="mark" style="left:${i}%;bottom:calc(${a.bottom + a.height}% + 6px)"
              >${j(e.buy, this.locale)} · ${P(e.start, this.locale, this.timeZone)}</span
            >`;
		})}
          ${r >= 0 ? S`<div class="nowline" style="left:${i(r)}"></div>
                <span class="nowpill" style="left:${i(r)}">${this.tr("plan.now_short")}</span>` : w}
          ${l === null ? w : this.tooltip(e[l], l, t)}
        </div>
        <div class="band" aria-hidden="true">
          ${et(e).map((e) => S`<div
                class=${e.past ? "seg past" : "seg"}
                style="flex:${e.count} 1 0;background:${e.action ? H(e.action) : "transparent"}"
              ></div>`)}
        </div>
        ${this.sun(e)}
        <div class="ticks" aria-hidden="true">
          ${c.map((t) => S`<span style="left:${i(t)}">${P(e[t].start, this.locale, this.timeZone)}</span>`)}
        </div>
      </div>
    </div>`;
	}
	sun(e) {
		let t = ct(e);
		return t ? S`<div class="sunlane" aria-hidden="true">
      ${t.map((e) => S`<div class="sq">
          ${e.height > 0 ? S`<i class=${`${e.past ? "" : "fut"}${e.over ? " over" : ""}`} style="height:${e.height}%"></i>` : w}
        </div>`)}
    </div>` : w;
	}
	hover(e, t) {
		let n = e.currentTarget.getBoundingClientRect(), r = Math.floor((e.clientX - n.left) / n.width * t);
		this.sel = Math.max(0, Math.min(t - 1, r));
	}
	key(e, t, n) {
		let r = e.shiftKey ? 4 : 1;
		if (e.key === "ArrowRight") this.sel = Math.min(t - 1, (this.sel ?? Math.max(n, 0)) + r);
		else if (e.key === "ArrowLeft") this.sel = Math.max(0, (this.sel ?? Math.max(n, 0)) - r);
		else if (e.key === "Escape") this.sel = null;
		else return;
		e.preventDefault();
	}
	tooltip(e, t, n) {
		let r = (t + .5) / n * 100, i = (r > 60 ? "right" : "left") == "left" ? `left:calc(${r}% + 10px)` : `right:calc(${100 - r}% + 10px)`, a = e.action ? this.tr(`action.${e.action}`) + (e.past ? ` (${this.tr("plan.actual")})` : e.indicative ? ` (${this.tr("plan.indicative_short")})` : "") : e.past ? this.tr("plan.no_record") : null;
		return S`<div class="tip" role="status" style=${i}>
      <strong>${F(e.start, this.locale, this.timeZone)} ${P(e.start, this.locale, this.timeZone)}</strong>
      ${e.buy === null ? S`<span>${this.tr("plan.unknown")}</span>` : S`<span>${this.tr("plan.tip_buy", { price: j(e.buy, this.locale) })}</span>
            <span>${this.tr("plan.tip_sell", { price: j(e.sell, this.locale) })}</span>`}
      ${a ? S`<span>${a}</span>` : w}
      ${e.soc === null ? w : S`<span>${this.tr(e.past ? "plan.tip_soc_past" : "plan.tip_soc", { soc: N(e.soc, this.locale) })}</span>`}
      ${e.solar !== null && e.load !== null ? S`<span>${this.tr(e.past ? "plan.tip_energy_past" : "plan.tip_energy", {
			solar: M(e.solar, this.locale, 2),
			load: M(e.load, this.locale, 2)
		})}</span>` : w}
      ${e.excluded ? S`<span>${this.tr("plan.tip_airco", { kwh: M(e.excluded, this.locale, 2) })}</span>` : w}
    </div>`;
	}
	summary(e) {
		let t = B(e);
		return t ? this.tr("plan.aria", {
			low: j(t.min.buy, this.locale),
			low_time: P(t.min.start, this.locale, this.timeZone),
			high: j(t.max.buy, this.locale),
			high_time: P(t.max.start, this.locale, this.timeZone)
		}) : this.tr("plan.title");
	}
	legend() {
		let e = (e, t, n = "sw") => S`<span class="li"><span class=${n} style="background:${e}"></span>${this.tr(t)}</span>`;
		return S`<div class="legend">
      ${e("var(--z-bar)", "plan.legend_price")} ${e(H("charge"), "action.charge")} ${e(H("deliver"), "action.deliver")}
      ${e(H("hold"), "action.hold")} ${e(H("export"), "action.export")}
      ${e("var(--z-solar)", "plan.legend_solar")} ${e("var(--z-solar)", "plan.legend_solar_over", "sw over")}
      <span class="li"><span class="line solid"></span>${this.tr("plan.legend_soc_past")}</span>
      <span class="li"><span class="line"></span>${this.tr("plan.legend_soc")}</span>
      <span class="li">${this.tr("plan.legend_past")}</span>
    </div>`;
	}
	static {
		this.styles = [o`
      :host {
        display: block;
      }
      .card {
        background: var(--z-card);
        border: 1px solid var(--z-border);
        border-radius: 16px;
        padding: 20px 24px 18px;
        display: flex;
        flex-direction: column;
        gap: 16px;
        color: var(--z-text);
        font-family: var(--z-font);
      }
      .spread {
        margin-left: 10px;
        padding: 2px 8px;
        border-radius: 999px;
        background: var(--z-info-bg);
        font-family: var(--z-font);
        font-size: 12px;
        font-weight: 600;
        vertical-align: middle;
        white-space: nowrap;
      }
      .skeleton {
        height: 320px;
        border-radius: 12px;
        background: var(--z-track);
      }
      .head {
        display: flex;
        flex-wrap: wrap;
        align-items: center;
        justify-content: space-between;
        gap: 12px;
      }
      h2 {
        margin: 0;
        font-family: var(--z-font-head);
        font-size: 20px;
      }
      .tabs {
        display: flex;
        gap: 4px;
        padding: 4px;
        border-radius: 999px;
        background: var(--z-bg);
        border: 1px solid var(--z-border);
      }
      .tabs button {
        min-height: 36px;
        padding: 0 16px;
        border: 0;
        border-radius: 999px;
        background: transparent;
        color: var(--z-text);
        font: inherit;
        font-size: 14px;
        cursor: pointer;
      }
      .tabs button.on {
        background: var(--z-text);
        color: var(--z-on-text);
        font-weight: 600;
      }
      .tabs button:focus-visible,
      .plot:focus-visible {
        outline: 2px solid var(--z-charge);
        outline-offset: 2px;
      }
      .prices {
        display: flex;
        flex-wrap: wrap;
        border: 1px solid var(--z-border);
        border-radius: 12px;
        overflow: hidden;
      }
      .cell {
        flex: 1 1 220px;
        padding: 12px 16px;
        display: flex;
        flex-direction: column;
        gap: 2px;
        border-left: 1px solid var(--z-border);
        margin-left: -1px;
      }
      .cell.now {
        flex: 1 1 150px;
        background: var(--z-bg);
      }
      .cap {
        font-size: 12px;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        color: var(--z-muted);
      }
      .value {
        font-family: var(--z-font-head);
        font-size: 22px;
        font-weight: 700;
        font-variant-numeric: tabular-nums;
      }
      .value.small {
        font-size: 18px;
      }
      .sub {
        font-size: 13px;
        color: var(--z-muted);
        font-variant-numeric: tabular-nums;
      }
      .note {
        margin: 0;
        padding: 10px 14px;
        border-radius: 10px;
        background: var(--z-info-bg);
        font-size: 14px;
        line-height: 1.5;
      }
      .note.warn {
        background: var(--z-warn-bg);
        color: var(--z-warn-text);
      }
      .empty {
        margin: 0;
        color: var(--z-muted);
      }
      .scroll {
        overflow-x: auto;
        overflow-y: visible;
      }
      .chart {
        position: relative;
        padding: 26px 44px 0 52px;
      }
      .axis {
        position: absolute;
        top: 26px;
        height: 220px;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
        font-size: 12px;
        color: var(--z-muted);
        font-variant-numeric: tabular-nums;
      }
      .axis.left {
        left: 0;
        width: 46px;
        text-align: right;
      }
      .axis.right {
        right: 0;
        width: 40px;
        white-space: nowrap;
      }
      .plot {
        position: relative;
        height: 220px;
        border-bottom: 1px solid var(--z-border);
        touch-action: pan-x;
      }
      .grid {
        position: absolute;
        left: 0;
        right: 0;
        border-top: 1px dashed var(--z-border);
      }
      .zero {
        position: absolute;
        left: 0;
        right: 0;
        border-top: 1px solid var(--z-muted);
      }
      .bar {
        position: absolute;
        box-sizing: border-box;
        border-left: 0.5px solid var(--z-card);
        background: var(--z-bar);
      }
      .bar.past {
        opacity: 0.4;
      }
      .bar.ind {
        background: repeating-linear-gradient(45deg, var(--z-bar) 0 3px, transparent 3px 6px);
        opacity: 0.7;
      }
      .bar.cur {
        background: var(--z-text);
        opacity: 1;
      }
      .bar.focus {
        background: var(--z-charge);
        opacity: 1;
      }
      svg {
        position: absolute;
        inset: 0;
        width: 100%;
        height: 100%;
        overflow: visible;
        pointer-events: none;
      }
      .halo,
      .soc {
        fill: none;
        stroke-linejoin: round;
        vector-effect: non-scaling-stroke;
      }
      .halo {
        stroke: var(--z-card);
        stroke-width: 7;
      }
      .soc {
        stroke: var(--z-text);
        stroke-width: 3;
        stroke-dasharray: 6 5;
      }
      .soc.measured {
        stroke-dasharray: none;
        opacity: 0.7;
      }
      .split {
        position: absolute;
        top: -20px;
        bottom: 0;
        border-left: 1px solid var(--z-border);
      }
      .dayname {
        position: absolute;
        top: -22px;
        font-size: 12px;
        font-weight: 600;
        color: var(--z-muted);
        white-space: nowrap;
      }
      .mark {
        position: absolute;
        transform: translateX(-50%);
        padding: 2px 8px;
        border-radius: 999px;
        background: var(--z-card);
        border: 1px solid var(--z-border);
        font-size: 11px;
        font-weight: 600;
        white-space: nowrap;
        font-variant-numeric: tabular-nums;
        pointer-events: none;
      }
      .nowline {
        position: absolute;
        top: -8px;
        bottom: 0;
        border-left: 2px solid var(--z-text);
        pointer-events: none;
      }
      .nowpill {
        position: absolute;
        top: -26px;
        transform: translateX(-50%);
        padding: 2px 8px;
        border-radius: 999px;
        background: var(--z-text);
        color: var(--z-on-text);
        font-size: 11px;
        font-weight: 600;
        pointer-events: none;
      }
      .tip {
        position: absolute;
        top: 8px;
        z-index: 2;
        min-width: 170px;
        padding: 10px 12px;
        border-radius: 10px;
        background: var(--z-card);
        border: 1px solid var(--z-border);
        box-shadow: 0 4px 16px rgba(0, 0, 0, 0.12);
        display: flex;
        flex-direction: column;
        gap: 2px;
        font-size: 13px;
        font-variant-numeric: tabular-nums;
        pointer-events: none;
      }
      .band {
        display: flex;
        height: 14px;
        margin-top: 6px;
        border-radius: 4px;
        overflow: hidden;
        background: var(--z-track);
      }
      .seg.past {
        opacity: 0.4;
      }
      .sunlane {
        display: flex;
        align-items: flex-end;
        height: 18px;
        margin-top: 2px;
        border-radius: 3px;
        overflow: hidden;
        background: var(--z-track);
      }
      .sq {
        flex: 1 1 0;
        height: 100%;
        display: flex;
        align-items: flex-end;
      }
      .sq i {
        display: block;
        width: 100%;
        background: var(--z-solar);
      }
      .sq i.fut {
        opacity: 0.55;
      }
      .sq i.over {
        box-shadow: inset 0 2px 0 var(--z-export);
      }
      .sw.over {
        box-shadow: inset 0 3px 0 var(--z-export);
      }
      .ticks {
        position: relative;
        height: 22px;
      }
      .ticks span {
        position: absolute;
        top: 5px;
        transform: translateX(-50%);
        font-size: 11px;
        color: var(--z-muted);
        white-space: nowrap;
        font-variant-numeric: tabular-nums;
      }
      .ticks span:first-child {
        transform: none;
      }
      .legend {
        display: flex;
        flex-wrap: wrap;
        gap: 8px 16px;
        font-size: 13px;
        color: var(--z-muted);
      }
      .li {
        display: inline-flex;
        align-items: center;
        gap: 6px;
      }
      .sw {
        width: 14px;
        height: 14px;
        border-radius: 3px;
        display: inline-block;
      }
      .line {
        width: 18px;
        border-top: 3px dashed var(--z-text);
        display: inline-block;
      }
      .line.solid {
        border-top-style: solid;
        opacity: 0.7;
      }
      @media (max-width: 700px) {
        .card {
          padding: 16px;
        }
        /* Scroll sideways; the chart starts 2 hours before now (see updated()). */
        .chart {
          min-width: 680px;
        }
        .chart.wide {
          min-width: 1300px;
        }
      }
    `];
	}
};
U([k({ attribute: !1 })], W.prototype, "view", void 0), U([k({ attribute: !1 })], W.prototype, "uiLang", void 0), U([k()], W.prototype, "locale", void 0), U([k()], W.prototype, "timeZone", void 0), U([k({ type: Boolean })], W.prototype, "narrow", void 0), U([k({ attribute: !1 })], W.prototype, "period", void 0), U([A()], W.prototype, "sel", void 0), W = U([O("zephyr-prices-plan")], W);
// src/sets.ts
function G(e, t, n) {
	return e.built_in ? L(n, "sets.built_in") : e.model ? t.filter((t) => t.model === e.model).length > 1 ? `${e.model} ${e.number}` : e.model : L(n, "sets.pack", { n: e.index + 1 });
}
var mt = (e) => e <= 30 ? "good" : e <= 100 ? "balancing" : "imbalance";
function ht(e) {
	let t = e.flatMap((e) => e.packs), n = t.map((e) => e.soc), r = t.map((e) => e.temp).filter((e) => e !== null), i = null;
	for (let e of t) e.cell_judged && e.cell_delta_mv !== null && e.cell_status !== null && (!i || e.cell_delta_mv > i.mv) && (i = {
		pack: e,
		mv: e.cell_delta_mv,
		status: e.cell_status
	});
	let a = null, o = t[0]?.history.map((e) => e.day) ?? [];
	for (let e = o.length - 1; e >= 0 && !a; e--) {
		let n = t.map((t) => t.history[e]?.max_mv).filter((e) => e != null);
		if (n.length) {
			let t = Math.max(...n);
			a = {
				day: o[e],
				mv: t,
				status: mt(t)
			};
		}
	}
	let s = null;
	for (let e of t) {
		let t = e.history.filter((e) => e.status === "imbalance");
		if (!t.length) continue;
		let n = t[t.length - 1];
		(!s || t.length > s.days) && (s = {
			pack: e,
			days: t.length,
			lastDay: n.day,
			mv: n.max_mv
		});
	}
	let c = t.some((e) => e.history.some((e) => e.max_mv !== null));
	return {
		packs: t.length,
		online: e.every((e) => e.online),
		socMin: n.length ? Math.min(...n) : null,
		socMax: n.length ? Math.max(...n) : null,
		warmest: r.length ? Math.max(...r) : null,
		now: i,
		lastDay: a,
		imbalance: s,
		notFull: !i && !c,
		offline: e.filter((e) => !e.online)
	};
}
var K = class extends D {
	constructor(...e) {
		super(...e), this.uiLang = "en", this.locale = "en", this.timeZone = "UTC";
	}
	tr(e, t = {}) {
		return L(this.uiLang, e, t);
	}
	num(e, t = 0) {
		return new Intl.NumberFormat(this.locale, {
			minimumFractionDigits: t,
			maximumFractionDigits: t
		}).format(e);
	}
	render() {
		let e = this.view;
		if (!e) return S`<div class="card skeleton" aria-hidden="true"></div>`;
		if (!e.sets.length) return S`<section class="card"><p class="text">${this.tr("sets.none")}</p></section>`;
		let t = ht(e.sets), n = e.sets.flatMap((e) => e.packs);
		return S`
      ${this.renderSummary(t, e.sets)}
      ${e.sets.map((t) => S`<div class="row">
          ${this.renderSet(t, e.sets.length)} ${this.renderPacks(t)}
        </div>`)}
      ${n.length ? this.renderBalance(e.sets) : w} ${e.sets.length === 1 ? this.renderActivity(e) : w}
    `;
	}
	stat(e, t) {
		return S`<div class="stat"><span class="cap">${e}</span><span class="value">${t}</span></div>`;
	}
	renderSummary(e, t) {
		let n = t.flatMap((e) => e.packs), r;
		r = e.offline.length ? this.tr("sets.offline_line", { sets: e.offline.map((e) => this.tr("sets.set", { n: e.number })).join(", ") }) : e.imbalance && e.imbalance.days >= 3 ? this.tr("sets.line_persistent", {
			pack: G(e.imbalance.pack, n, this.uiLang),
			days: e.imbalance.days
		}) : e.now?.status === "imbalance" ? this.tr("sets.line_now", {
			pack: G(e.now.pack, n, this.uiLang),
			mv: e.now.mv
		}) : e.imbalance ? this.tr("sets.line_recent", {
			pack: G(e.imbalance.pack, n, this.uiLang),
			day: F(`${e.imbalance.lastDay}T12:00:00Z`, this.locale, this.timeZone),
			mv: e.imbalance.mv
		}) : e.notFull ? this.tr("sets.line_not_full") : this.tr("sets.line_ok");
		let i = e.now ? `${this.num(e.now.mv)} mV · ${this.tr(`sets.cell.${e.now.status}`)}` : e.lastDay ? `${this.num(e.lastDay.mv)} mV · ${this.tr(`sets.cell.${e.lastDay.status}`)}` : "–";
		return S`<section class="card summary" aria-label=${this.tr("sets.summary")}>
      ${this.stat(this.tr("sets.batteries"), this.tr(e.online ? "sets.all_online" : "sets.some_offline", { n: e.packs }))}
      ${this.stat(this.tr("sets.soc_spread"), e.socMin === null ? "–" : e.socMin === e.socMax ? N(e.socMin, this.locale) : `${this.num(e.socMin)}–${N(e.socMax, this.locale)}`)}
      ${this.stat(this.tr("sets.warmest"), e.warmest === null ? "–" : `${this.num(e.warmest)} °C`)}
      ${this.stat(e.now || !e.lastDay ? this.tr("sets.largest_delta") : this.tr("sets.largest_delta_day", { day: F(`${e.lastDay.day}T12:00:00Z`, this.locale, this.timeZone) }), i)}
      <p class="line"><strong>${this.tr("sets.in_short")}</strong> ${r}</p>
    </section>`;
	}
	renderSet(e, t) {
		let n = e.soc ?? 0, r = e.online ? e.status ?? "standby" : "offline", i = (e, t) => S`<div><dt>${e}</dt><dd>${t}</dd></div>`, a = e.last_full ? I(e.last_full, Date.now(), this.timeZone) ? `${this.tr("sets.today")} ${P(e.last_full, this.locale, this.timeZone)}` : F(e.last_full, this.locale, this.timeZone) : this.tr("sets.unknown");
		return S`<article class="card set">
      <div class="head">
        <div>
          <h2>${this.tr("sets.set", { n: e.number })}</h2>
          <span class="muted"
            >${e.model}${e.packs.length ? ` · ${this.tr("sets.packs_n", { n: e.packs.length })}` : ""}${e.capacity_kwh ? ` · ${M(e.capacity_kwh, this.locale)}` : ""}</span
          >
        </div>
        <span class="chip ${r}">${this.tr(`sets.status.${r}`)}</span>
      </div>
      ${e.soc === null ? S`<p class="text">${this.tr("battery.unknown")}</p>` : S`<div class="big-row">
              <span class="big">${N(n, this.locale)}</span>
              ${e.energy_kwh !== null && e.capacity_kwh ? S`<span class="muted">${this.tr("battery.of", {
			energy: M(e.energy_kwh, this.locale),
			capacity: M(e.capacity_kwh, this.locale)
		})}</span>` : w}
            </div>
            <div class="bar" role="meter" aria-valuemin="0" aria-valuemax="100" aria-valuenow=${Math.round(n)} aria-label=${this.tr("battery.title")}>
              <div class="fill" style="width:${n}%"></div>
              ${e.limits?.min == null ? w : S`<div class="mark" style="left:${e.limits.min}%"></div>`}
              ${e.limits?.max == null ? w : S`<div class="mark" style="left:${e.limits.max}%"></div>`}
            </div>`}
      <dl>
        ${i(this.tr("sets.power"), e.power_w === null ? "–" : Ge(e.power_w, this.locale))}
        ${e.solar_w ? i(this.tr("sets.solar"), Ge(e.solar_w, this.locale).replace("+", "")) : w}
        ${i(this.tr("sets.inverter"), e.enclosure_temp === null ? "–" : `${this.num(e.enclosure_temp)} °C`)}
        ${i(this.tr("sets.last_full"), a)}
        ${i(this.tr("sets.switches"), e.relays_24h === null ? "–" : this.tr("sets.switches_n", { n: e.relays_24h }))}
        ${i(this.tr("sets.limits"), e.limits?.min != null && e.limits?.max != null ? `${this.num(e.limits.min)}–${this.num(e.limits.max)} %` : "–")}
      </dl>
      <div class="foot">
        <span>${t >= 3 ? this.tr("sets.max_sets") : ""}</span>
        ${t < 3 ? S`<a class="button" href="/config/integrations/integration/zephyr">${this.tr("sets.add")}</a>` : w}
      </div>
    </article>`;
	}
	renderPacks(e) {
		return e.packs.length ? S`<section class="card packs" aria-label=${this.tr("sets.in_set")}>
      <div class="head">
        <h2>${this.tr("sets.in_set")}</h2>
        <span class="muted">${this.tr("sets.pack_power_note")}</span>
      </div>
      <div class="grid">
        ${e.packs.map((t) => {
			let n = t.cell_status;
			return S`<div class="pack ${e.online ? "" : "off"}">
            <div class="ph"><strong>${G(t, e.packs, this.uiLang)}</strong><span class="muted">${t.capacity_kwh ? M(t.capacity_kwh, this.locale, 2) : this.tr("sets.unknown_type")}</span></div>
            <div class="big-row">
              <span class="mid">${N(t.soc, this.locale)}</span>
              ${t.energy_kwh === null ? w : S`<span class="muted">${M(t.energy_kwh, this.locale, 2)}</span>`}
            </div>
            <div class="bar thin"><div class="fill" style="width:${t.soc}%"></div></div>
            <dl>
              <div><dt>${this.tr("sets.power")}</dt><dd>${Ge(t.power_w, this.locale)}</dd></div>
              <div><dt>${this.tr("sets.temp")}</dt><dd>${t.temp === null ? "–" : `${this.num(t.temp)} °C`}</dd></div>
              <div>
                <dt>${this.tr("sets.cells")}</dt>
                <dd>${t.cell_min_v === null || t.cell_max_v === null ? "–" : `${this.num(t.cell_min_v, 2)}–${this.num(t.cell_max_v, 2)} V`}</dd>
              </div>
              <div>
                <dt>${this.tr("sets.cell_delta")}</dt>
                <dd class="delta">
                  ${t.cell_delta_mv === null ? "–" : `${this.num(t.cell_delta_mv)} mV`}
                  ${n ? S`<span class="tag ${n}">${this.tr(`sets.cell.${n}`)}</span>` : t.cell_delta_mv === null ? w : S`<span class="tag none" title=${this.tr("sets.not_judged_title")}>${this.tr("sets.not_judged")}</span>`}
                </dd>
              </div>
            </dl>
          </div>`;
		})}
      </div>
      <p class="text small">${this.tr("sets.cell_note")}</p>
    </section>` : S``;
	}
	renderBalance(e) {
		let t = e.find((e) => e.packs.length)?.packs[0]?.history ?? [];
		return S`<section class="card" aria-label=${this.tr("sets.balance_title")}>
      <div class="head">
        <h2>${this.tr("sets.balance_title")}</h2>
        <span class="muted">${this.tr("sets.balance_note")}</span>
      </div>
      <div class="table" role="table">
        <div class="tr" role="row">
          <span role="columnheader"></span>
          ${t.map((e) => S`<span role="columnheader" class="dh">${F(`${e.day}T12:00:00Z`, this.locale, this.timeZone)}</span>`)}
        </div>
        ${e.flatMap((t) => t.packs.map((n) => S`<div class="tr" role="row">
              <span role="rowheader" class="rh">${e.length > 1 ? `${t.number} · ` : ""}${G(n, t.packs, this.uiLang)}</span>
              ${n.history.map((e) => S`<span
                  role="cell"
                  class="cell ${e.status ?? "none"}"
                  title=${e.max_mv === null ? this.tr("sets.no_judged") : `${e.max_mv} mV · ${this.tr(`sets.cell.${e.status}`)}`}
                  >${e.max_mv === null ? "–" : this.num(e.max_mv)}${e.full ? S` <span aria-label=${this.tr("sets.full_day")}>▲</span>` : w}</span
                >`)}
            </div>`))}
      </div>
    </section>`;
	}
	renderActivity(e) {
		let t = new Date(e.now).getTime(), n = t - 864e5, r = (e) => Math.max(0, Math.min(100, (new Date(e).getTime() - n) / (t - n) * 100)), i = {
			charge: 0,
			deliver: 0
		};
		return S`<section class="card" aria-label=${this.tr("sets.activity_title")}>
      <div class="head">
        <h2>${this.tr("sets.activity_title")}</h2>
        <div class="legend">
          <span><i style="background:${H("charge")}"></i>${this.tr("action.charge")}</span>
          <span><i style="background:${H("deliver")}"></i>${this.tr("action.deliver")}</span>
          <span><i style="background:${H("hold")}"></i>${this.tr("action.hold")}</span>
        </div>
      </div>
      <div class="activity" aria-hidden="true">
        ${e.activity_24h.map((e) => {
			e.action in i && (i[e.action] += 1);
			let t = r(e.start);
			return S`<div
            title="${P(e.start, this.locale, this.timeZone)}–${P(e.end, this.locale, this.timeZone)} · ${this.tr(`action.${e.action}`)}"
            style="left:${t}%;width:${r(e.end) - t}%;background:${H(e.action)}"
          ></div>`;
		})}
      </div>
      <div class="hours">
        ${[
			0,
			4,
			8,
			12,
			16,
			20
		].map((e) => S`<span>${P(new Date(n + e * 36e5).toISOString(), this.locale, this.timeZone)}</span>`)}
        <span>${this.tr("plan.now_short")}</span>
      </div>
      ${e.activity_24h.length ? w : S`<p class="text small">${this.tr("sets.no_activity")}</p>`}
    </section>`;
	}
	static {
		this.styles = o`
    :host {
      display: flex;
      flex-direction: column;
      gap: 20px;
      color: var(--z-text);
      font-family: var(--z-font);
    }
    .card {
      background: var(--z-card);
      border: 1px solid var(--z-border);
      border-radius: 16px;
      padding: 20px 24px;
      display: flex;
      flex-direction: column;
      gap: 14px;
      min-width: 0;
    }
    .skeleton {
      min-height: 300px;
    }
    h2 {
      margin: 0;
      font-family: var(--z-font-head);
      font-size: 20px;
    }
    .head {
      display: flex;
      flex-wrap: wrap;
      align-items: baseline;
      justify-content: space-between;
      gap: 8px 12px;
    }
    .muted {
      font-size: 13px;
      color: var(--z-muted);
    }
    .text {
      margin: 0;
      font-size: 14px;
      line-height: 1.5;
      color: var(--z-muted);
    }
    .text.small {
      font-size: 13px;
    }
    .summary {
      flex-direction: row;
      flex-wrap: wrap;
      align-items: center;
      gap: 16px 32px;
    }
    .stat {
      display: flex;
      flex-direction: column;
      gap: 2px;
    }
    .cap {
      font-size: 12px;
      font-weight: 600;
      text-transform: uppercase;
      letter-spacing: 0.08em;
      color: var(--z-muted);
    }
    .value {
      font-family: var(--z-font-head);
      font-size: 24px;
      font-weight: 700;
      font-variant-numeric: tabular-nums;
    }
    .line {
      flex: 1 1 300px;
      margin: 0;
      font-size: 14px;
      line-height: 1.5;
      color: var(--z-muted);
    }
    .line strong {
      color: var(--z-text);
    }
    .row {
      display: flex;
      flex-wrap: wrap;
      gap: 16px;
      align-items: stretch;
    }
    .set {
      flex: 1 1 340px;
      max-width: 460px;
    }
    .packs {
      flex: 999 1 520px;
    }
    .chip {
      padding: 6px 12px;
      border-radius: 999px;
      font-size: 13px;
      font-weight: 600;
      white-space: nowrap;
      background: var(--z-track);
    }
    .chip.charging {
      background: var(--z-charge);
      color: #fff;
    }
    .chip.discharging {
      background: var(--z-warn-bg);
      color: var(--z-warn-text);
    }
    .chip.offline,
    .chip.fault {
      background: var(--z-warn-bg);
      color: var(--z-warn-text);
    }
    .big-row {
      display: flex;
      flex-wrap: wrap;
      align-items: baseline;
      gap: 4px 10px;
    }
    .big {
      font-family: var(--z-font-head);
      font-size: 34px;
      font-weight: 700;
    }
    .mid {
      font-family: var(--z-font-head);
      font-size: 26px;
      font-weight: 700;
    }
    .bar {
      position: relative;
      height: 12px;
      background: var(--z-track);
      border-radius: 6px;
      overflow: hidden;
    }
    .bar.thin {
      height: 8px;
    }
    .fill {
      height: 100%;
      background: var(--z-text);
      border-radius: 6px;
    }
    .mark {
      position: absolute;
      top: 0;
      bottom: 0;
      border-left: 2px solid var(--z-card);
    }
    dl {
      margin: 0;
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 10px 16px;
    }
    dt {
      font-size: 12px;
      color: var(--z-muted);
    }
    dd {
      margin: 0;
      font-weight: 600;
      font-variant-numeric: tabular-nums;
    }
    .foot {
      margin-top: auto;
      padding-top: 12px;
      border-top: 1px solid var(--z-border);
      display: flex;
      flex-wrap: wrap;
      align-items: center;
      justify-content: space-between;
      gap: 8px;
      font-size: 13px;
      color: var(--z-muted);
    }
    .button {
      min-height: 44px;
      display: inline-flex;
      align-items: center;
      padding: 0 16px;
      border-radius: 999px;
      border: 1px solid var(--z-border);
      text-decoration: none;
      font-size: 14px;
      color: var(--z-text);
    }
    .button:focus-visible {
      outline: 2px solid var(--z-charge);
      outline-offset: 2px;
    }
    .grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
      gap: 12px;
    }
    .pack {
      border: 1px solid var(--z-border);
      border-radius: 12px;
      padding: 14px 16px;
      display: flex;
      flex-direction: column;
      gap: 10px;
    }
    .pack.off {
      opacity: 0.6;
    }
    .ph {
      display: flex;
      justify-content: space-between;
      align-items: baseline;
      gap: 8px;
    }
    .pack dl {
      font-size: 14px;
      gap: 8px 12px;
    }
    .delta {
      display: flex;
      flex-wrap: wrap;
      align-items: center;
      gap: 6px;
    }
    .tag {
      padding: 2px 8px;
      border-radius: 999px;
      font-size: 11px;
      font-weight: 600;
    }
    .tag.good,
    .cell.good {
      background: var(--z-good-bg);
      color: var(--z-good-text);
    }
    .tag.balancing,
    .cell.balancing {
      background: var(--z-warn-bg);
      color: var(--z-warn-text);
    }
    .tag.imbalance,
    .cell.imbalance {
      background: var(--z-bad-bg);
      color: var(--z-bad-text);
    }
    .tag.none {
      background: var(--z-track);
      color: var(--z-muted);
    }
    .table {
      display: flex;
      flex-direction: column;
      gap: 6px;
      overflow-x: auto;
    }
    .tr {
      display: grid;
      grid-template-columns: 130px repeat(7, minmax(52px, 1fr));
      gap: 6px;
      align-items: center;
    }
    .dh {
      text-align: center;
      font-size: 12px;
      color: var(--z-muted);
    }
    .rh {
      font-size: 14px;
      font-weight: 600;
    }
    .cell {
      min-height: 36px;
      display: flex;
      align-items: center;
      justify-content: center;
      border-radius: 8px;
      font-size: 13px;
      font-weight: 600;
      font-variant-numeric: tabular-nums;
    }
    .cell.none {
      background: var(--z-track);
      color: var(--z-muted);
    }
    .legend {
      display: flex;
      flex-wrap: wrap;
      gap: 12px;
      font-size: 13px;
      color: var(--z-muted);
    }
    .legend span {
      display: inline-flex;
      align-items: center;
      gap: 6px;
    }
    .legend i {
      width: 14px;
      height: 14px;
      border-radius: 3px;
      display: inline-block;
    }
    .activity {
      position: relative;
      height: 22px;
      border-radius: 6px;
      overflow: hidden;
      background: var(--z-track);
    }
    .activity div {
      position: absolute;
      top: 0;
      bottom: 0;
    }
    .hours {
      display: flex;
      justify-content: space-between;
      font-size: 11px;
      color: var(--z-muted);
      font-variant-numeric: tabular-nums;
    }
    @media (max-width: 700px) {
      .card {
        padding: 16px;
      }
      .set {
        max-width: none;
      }
    }
  `;
	}
};
U([k({ attribute: !1 })], K.prototype, "view", void 0), U([k({ attribute: !1 })], K.prototype, "uiLang", void 0), U([k()], K.prototype, "locale", void 0), U([k()], K.prototype, "timeZone", void 0), K = U([O("zephyr-sets")], K);
// src/settings-edit.ts
function gt(e, t) {
	let n = e.trim().replace(/\s/g, "");
	if (!n || (n = (new Intl.NumberFormat(t).format(1.5).includes(",") ? "," : ".") == "," ? n.replace(/\.(?=\d{3}(\D|$))/g, "").replace(",", ".") : n.replace(/,(?=\d{3}(\D|$))/g, ""), !/^[-+]?\d*\.?\d+$/.test(n))) return null;
	let r = Number(n);
	return Number.isFinite(r) ? r : null;
}
function _t(e, t, n) {
	return e ? Object.entries(e).filter(([e, r]) => e.startsWith(`${t}.`) && (!n || r.attributes?.device_class === n)).map(([e, t]) => ({
		id: e,
		name: String(t.attributes?.friendly_name ?? e)
	})).sort((e, t) => e.name.localeCompare(t.name) || e.id.localeCompare(t.id)) : [];
}
function vt(e, t) {
	let n = e.trim();
	if (!n) return null;
	let r = t.find((e) => e.id === n);
	if (r) return r.id;
	let i = /\(([a-z0-9_]+\.[a-z0-9_]+)\)$/.exec(n);
	if (i && t.some((e) => e.id === i[1])) return i[1];
	let a = t.filter((e) => e.name.toLowerCase() === n.toLowerCase());
	return a.length === 1 ? a[0].id : null;
}
function q(e) {
	return e.name === e.id ? e.id : `${e.name} (${e.id})`;
}
function yt(e, t) {
	return Array.isArray(e) && Array.isArray(t) ? e.length === t.length && e.every((e, n) => e === t[n]) : (e ?? null) === (t ?? null);
}
function bt(e, t, n) {
	let r = e.includes(t) ? e.filter((e) => e !== t) : [...e, t];
	return n.filter((e) => r.includes(e));
}
function xt(e, t) {
	return e < 90 ? `${Math.round(e)} s` : `${new Intl.NumberFormat(t, { maximumFractionDigits: 1 }).format(e / 60)} min`;
}
// src/settings.ts
var J = Symbol("reset");
function Y(e, t, n) {
	let r = typeof t == "number" && t < 1 ? Math.min(5, Math.max(0, Math.ceil(-Math.log10(t) - 1e-9))) : t === "any" ? 5 : 0;
	return new Intl.NumberFormat(n, {
		minimumFractionDigits: 0,
		maximumFractionDigits: r
	}).format(e);
}
var X = class extends D {
	constructor(...e) {
		super(...e), this.uiLang = "en", this.locale = "en", this.friendlyName = () => void 0, this.group = 0, this.tip = null, this.draft = {}, this.errors = {}, this.busy = !1, this.saved = null, this.restarting = !1;
	}
	willUpdate(e) {
		e.has("view") && e.get("view") !== void 0 && (this.restarting = !1);
	}
	get editable() {
		return !!(this.view?.can_edit && this.save);
	}
	shown(e) {
		if (!(e.key in this.draft)) return e.value;
		let t = this.draft[e.key];
		return t === J ? e.default : t;
	}
	isModified(e) {
		if (e.kind === "entity" || e.kind === "entities") return !1;
		if (!(e.key in this.draft)) return e.modified;
		let t = this.draft[e.key];
		return t !== J && !yt(t, e.default) && (!e.optional || t !== null && t !== "");
	}
	change(e, t) {
		let { [e.key]: n, ...r } = this.errors;
		if (this.errors = r, e.reload) {
			let { [e.key]: n, ...r } = this.draft;
			this.draft = yt(t, e.value) ? r : {
				...r,
				[e.key]: t
			};
		} else yt(t, e.value) || this.send({ [e.key]: t }, [], e.key);
	}
	reset(e) {
		e.reload ? this.draft = {
			...this.draft,
			[e.key]: J
		} : this.send({}, [e.key], e.key);
	}
	localError(e, t) {
		this.errors = {
			...this.errors,
			[e.key]: t
		}, this.requestUpdate();
	}
	async send(e, t, n) {
		if (!this.save || this.busy) return !1;
		this.busy = !0;
		try {
			let r = await this.save(e, t);
			return r.ok ? (n && (this.saved = n, window.clearTimeout(this.savedTimer), this.savedTimer = window.setTimeout(() => this.saved = null, 2500)), !0) : (this.errors = {
				...this.errors,
				...r.errors ?? { base: "failed" }
			}, !1);
		} catch {
			return this.errors = {
				...this.errors,
				[n ?? "base"]: "failed"
			}, !1;
		} finally {
			this.busy = !1;
		}
	}
	async saveDraft() {
		let e = {}, t = [];
		for (let [n, r] of Object.entries(this.draft)) r === J ? t.push(n) : e[n] = r;
		let { base: n, ...r } = this.errors;
		this.errors = r, await this.send(e, t, null) && (this.draft = {}, this.restarting = !0);
	}
	cancelDraft() {
		this.draft = {}, this.errors = {};
	}
	tr(e, t = {}) {
		return L(this.uiLang, e, t);
	}
	label(e) {
		return this.tr(`settings.fields.${e}.label`);
	}
	render() {
		let e = this.view;
		if (!e) return S`<div class="card skeleton" aria-hidden="true"></div>`;
		let t = Math.min(this.group, e.groups.length - 1), n = e.groups[t];
		return S`<div class="layout">
      <nav class="card groups" aria-label=${this.tr("settings.title")}>
        ${e.groups.map((e, n) => S`<button
            type="button"
            class=${n === t ? "on" : ""}
            aria-current=${n === t ? "true" : "false"}
            @click=${() => {
			this.group = n, this.tip = null;
		}}
          >
            <span>${this.tr(`settings.groups.${e.key}`)}</span>
            ${e.modified ? S`<span class="badge">${this.tr("settings.modified_n", { n: e.modified })}</span>` : w}
          </button>`)}
      </nav>
      <section class="card fields" aria-labelledby="group-title">
        <div class="head">
          <h2 id="group-title">${this.tr(`settings.groups.${n.key}`)}</h2>
        </div>
        ${e.can_edit ? w : S`<p class="note">${this.tr("settings.readonly")}</p>`}
        ${this.restarting ? S`<p class="note" role="status">${this.tr("settings.restarting")}</p>` : w}
        ${n.fields.some((e) => e.reload) ? S`<p class="muted">${this.tr("settings.reload_note")}</p>` : w}
        ${n.key === "tariffs" && e.supplier !== "own" ? S`<p class="muted">${this.tr("settings.supplier_note", { source: e.tariffs_source ?? "–" })}</p>` : w}
        <ul>
          ${n.fields.map((e) => this.renderField(e))}
        </ul>
        ${this.renderBar()}
      </section>
    </div>`;
	}
	renderBar() {
		let e = Object.keys(this.draft).length, t = this.errors.base;
		return !e && !t ? w : S`<div class="bar" role="region" aria-label=${this.tr("settings.pending", { n: e })}>
      ${t ? S`<p class="error" role="alert">${this.tr(`settings.errors.${t}`)}</p>` : w}
      ${e ? S`<div class="barrow">
            <span>${this.tr(e === 1 ? "settings.pending_one" : "settings.pending", { n: e })}</span>
            <span class="buttons">
              <button type="button" class="ghost" ?disabled=${this.busy} @click=${() => this.cancelDraft()}>${this.tr("settings.cancel")}</button>
              <button type="button" class="primary" ?disabled=${this.busy} @click=${() => void this.saveDraft()}>
                ${this.tr(this.busy ? "settings.saving" : "settings.save_restart")}
              </button>
            </span>
          </div>` : w}
    </div>`;
	}
	renderField(e) {
		let t = this.tip === e.key, n = `f-${e.key}`;
		return S`<li class=${e.active === !1 ? "inactive" : ""}>
      <div class="text">
        <div class="labelrow">
          <label for=${n}>${this.label(e.key)}</label>
          <button
            type="button"
            class=${t ? "info on" : "info"}
            aria-expanded=${t ? "true" : "false"}
            aria-label=${this.tr("settings.more", { label: this.label(e.key) })}
            @click=${() => this.tip = t ? null : e.key}
          >
            i
          </button>
          ${this.isModified(e) ? S`<span class="dot" title=${this.defaultText(e)}></span>` : w}
          ${e.key in this.draft ? S`<span class="pending">${this.tr("settings.not_saved")}</span>` : w}
          ${this.saved === e.key ? S`<span class="saved" role="status">${this.tr("settings.saved")}</span>` : w}
        </div>
        <span class="help">${this.tr(`settings.fields.${e.key}.help`)}</span>
        ${t ? S`<div class="more" role="note">${this.tr(`settings.fields.${e.key}.more`)}</div>` : w}
        ${this.meta(e)}
        ${this.errors[e.key] ? S`<span class="error" role="alert">${this.errorText(e, this.errors[e.key])}</span>` : w}
      </div>
      <div class="control">${this.control(e, n)}</div>
    </li>`;
	}
	errorText(e, t) {
		return t === "out_of_range" && e.min !== null && e.max !== null ? this.tr("settings.errors.range", {
			min: Y(e.min, e.step, this.locale),
			max: Y(e.max, e.step, this.locale),
			unit: e.unit ? ` ${e.unit}` : ""
		}) : this.tr(`settings.errors.${t}`);
	}
	defaultText(e) {
		return this.tr("settings.default", { value: this.display(e, e.default) });
	}
	display(e, t) {
		return t == null || t === "" || Array.isArray(t) && !t.length ? this.tr("settings.none") : e.kind === "bool" ? this.tr(t ? "settings.yes" : "settings.no") : e.kind === "number" ? `${Y(Number(t), e.step, this.locale)}${e.unit ? ` ${e.unit}` : ""}` : e.kind === "select" ? e.key === "tariff_supplier" ? e.choices?.find((e) => e.value === t)?.label ?? this.tr("settings.own") : Array.isArray(t) ? t.map((e) => this.tr(`settings.options.${e}`)).join(", ") : this.tr(`settings.options.${String(t)}`) : (Array.isArray(t) ? t : [String(t)]).map((e) => this.friendlyName(e) ?? e).join(", ");
	}
	meta(e) {
		let t = [], n = this.isModified(e);
		n && t.push(this.defaultText(e)), e.tariff && e.active === !1 && e.in_use !== void 0 && e.in_use !== null && t.push(this.tr("settings.in_use", { value: this.display(e, e.in_use) }));
		let r = e.status;
		r && (r.state === "unset" ? t.push(this.tr("settings.status.unset")) : r.state === "missing" ? t.push(this.tr("settings.status.missing", { entities: (r.entities ?? []).join(", ") })) : r.state === "unavailable" ? t.push(this.tr("settings.status.unavailable")) : r.mode === void 0 ? r.no_step ? t.push(this.tr("settings.status.no_step")) : r.step_interval_s != null && r.step_kwh != null ? t.push(this.tr("settings.status.steps", {
			every: xt(r.step_interval_s, this.locale),
			kwh: Y(r.step_kwh, .01, this.locale)
		})) : r.interval_s == null ? r.price_slots == null ? t.push(this.tr("settings.status.ok")) : t.push(this.tr("settings.status.slots", { n: r.price_slots })) : t.push(this.tr("settings.status.interval", { s: Y(r.interval_s, .1, this.locale) })) : t.push(r.action ? this.tr("settings.status.climate", {
			mode: this.tr(`settings.options.${r.mode}`),
			action: this.tr(`settings.actions.${r.action}`)
		}) : this.tr(`settings.options.${r.mode}`)));
		let i = n && this.editable && !(e.key in this.draft && this.draft[e.key] === J);
		return !t.length && !i ? w : S`<span class=${r && r.state !== "ok" && r.state !== "unset" ? "meta warn" : "meta"}
      >${t.join(" · ")}${i ? S` <button type="button" class="link" ?disabled=${this.busy} @click=${() => this.reset(e)}>${this.tr("settings.reset")}</button>` : w}</span
    >`;
	}
	control(e, t) {
		let n = !this.editable || this.busy || e.active === !1 && e.tariff, r = this.shown(e);
		switch (e.kind) {
			case "bool": return S`<button
          id=${t}
          type="button"
          role="switch"
          class="switch"
          aria-checked=${r ? "true" : "false"}
          ?disabled=${n}
          @click=${() => this.change(e, !r)}
        >
          <span></span>
        </button>`;
			case "number": return S`<span class="num">
          <input
            id=${t}
            type="text"
            inputmode="decimal"
            .value=${r == null ? "" : Y(Number(r), e.step, this.locale)}
            ?disabled=${n}
            aria-invalid=${this.errors[e.key] ? "true" : "false"}
            @change=${(t) => this.numberChanged(e, t.target)}
            @keydown=${(e) => e.key === "Enter" && e.target.blur()}
          />${e.unit ? S`<span class="unit">${e.unit}</span>` : w}
        </span>`;
			case "select": return e.multiple ? this.multi(e, t, r ?? [], n) : S`<select id=${t} ?disabled=${n} @change=${(t) => this.change(e, t.target.value)}>
          ${(e.choices ?? e.options.map((e) => ({
				value: e,
				label: null
			}))).map((t) => S`<option value=${t.value} ?selected=${t.value === r}>
              ${t.label ?? (e.key === "tariff_supplier" ? this.tr("settings.own") : this.tr(`settings.options.${t.value}`))}
            </option>`)}
        </select>`;
			case "entities": return this.entities(e, t, r ?? [], n);
			default: return this.entity(e, t, r ?? null, n);
		}
	}
	numberChanged(e, t) {
		let n = gt(t.value, this.locale);
		n === null ? !t.value.trim() && e.optional ? this.change(e, null) : this.localError(e, t.value.trim() ? "not_a_number" : "required") : this.change(e, n);
	}
	multi(e, t, n, r) {
		return S`<div id=${t} class="chips" role="group" aria-label=${this.label(e.key)}>
      ${e.options.map((t) => S`<button
          type="button"
          class="chip"
          aria-pressed=${n.includes(t) ? "true" : "false"}
          ?disabled=${r}
          @click=${() => {
			let r = bt(n, t, e.options);
			r.length ? this.change(e, r) : this.localError(e, "choose_one");
		}}
        >
          ${this.tr(`settings.options.${t}`)}
        </button>`)}
    </div>`;
	}
	choices(e) {
		return _t(this.states, e.domain, e.device_class);
	}
	picker(e, t, n, r, i) {
		let a = this.choices(e);
		return S`<input
        id=${t}
        class="pick"
        type="text"
        list=${`${t}-list`}
        placeholder=${this.tr("settings.choose_entity")}
        autocomplete="off"
        .value=${n}
        ?disabled=${r}
        aria-invalid=${this.errors[e.key] ? "true" : "false"}
        @change=${(e) => {
			let t = e.target.value;
			i(vt(t, a), t);
		}}
      />
      <datalist id=${`${t}-list`}>${a.map((e) => S`<option value=${q(e)}></option>`)}</datalist>`;
	}
	entity(e, t, n, r) {
		let i = n ? this.choices(e).find((e) => e.id === n) ?? {
			id: n,
			name: this.friendlyName(n) ?? n
		} : null;
		return S`<span class="entityrow">
      ${this.picker(e, t, i ? q(i) : "", r, (t, n) => {
			t ? this.change(e, t) : n.trim() ? this.localError(e, "entity_missing") : e.optional ? this.change(e, null) : this.localError(e, "required");
		})}
      ${n && e.optional ? S`<button type="button" class="clear" ?disabled=${r} aria-label=${this.tr("settings.clear")} @click=${() => this.change(e, null)}>
            ×
          </button>` : w}
    </span>`;
	}
	entities(e, t, n, r) {
		return S`<div class="multi">
      ${n.length ? S`<ul class="chips">
            ${n.map((t) => S`<li class="chip on">
                <span>${this.friendlyName(t) ?? t}</span>
                <button
                  type="button"
                  class="x"
                  ?disabled=${r}
                  aria-label=${`${this.tr("settings.remove")}: ${this.friendlyName(t) ?? t}`}
                  @click=${() => this.change(e, n.filter((e) => e !== t))}
                >
                  ×
                </button>
              </li>`)}
          </ul>` : w}
      ${this.picker(e, t, "", r, (t, r) => {
			t ? n.includes(t) || this.change(e, [...n, t]) : r.trim() && this.localError(e, "entity_missing");
		})}
    </div>`;
	}
	static {
		this.styles = o`
    :host {
      display: block;
      color: var(--z-text);
      font-family: var(--z-font);
    }
    .card {
      background: var(--z-card);
      border: 1px solid var(--z-border);
      border-radius: 16px;
      padding: 20px 24px;
      min-width: 0;
    }
    .skeleton {
      min-height: 300px;
    }
    .layout {
      display: flex;
      flex-wrap: wrap;
      gap: 16px;
      align-items: flex-start;
    }
    .groups {
      flex: 1 1 240px;
      max-width: 300px;
      padding: 10px;
      display: flex;
      flex-direction: column;
      gap: 2px;
    }
    .groups button {
      display: flex;
      justify-content: space-between;
      align-items: center;
      gap: 8px;
      width: 100%;
      min-height: 44px;
      padding: 10px 14px;
      border: 0;
      border-radius: 10px;
      background: transparent;
      color: var(--z-text);
      font: inherit;
      font-size: 14px;
      text-align: left;
      cursor: pointer;
    }
    .groups button.on {
      background: var(--z-text);
      color: var(--z-on-text);
      font-weight: 600;
    }
    .groups button:focus-visible,
    .info:focus-visible {
      outline: 2px solid var(--z-charge);
      outline-offset: 2px;
    }
    .badge {
      font-size: 11px;
      padding: 2px 8px;
      border-radius: 999px;
      background: var(--z-info-bg);
      color: var(--z-text);
      white-space: nowrap;
    }
    .fields {
      flex: 999 1 520px;
      display: flex;
      flex-direction: column;
      gap: 12px;
    }
    h2 {
      margin: 0;
      font-family: var(--z-font-head);
      font-size: 20px;
    }
    .note {
      margin: 0;
      padding: 10px 14px;
      border-radius: 10px;
      background: var(--z-info-bg);
      font-size: 14px;
      line-height: 1.5;
    }
    .note a {
      margin-left: 6px;
      color: var(--z-charge);
      font-weight: 600;
    }
    .muted {
      margin: 0;
      font-size: 13px;
      color: var(--z-muted);
      line-height: 1.5;
    }
    ul {
      list-style: none;
      margin: 0;
      padding: 0;
    }
    li {
      display: flex;
      flex-wrap: wrap;
      justify-content: space-between;
      align-items: flex-start;
      gap: 10px 24px;
      padding: 16px 0;
      border-top: 1px solid var(--z-border);
    }
    li.inactive .control {
      opacity: 0.5;
    }
    .text {
      flex: 1 1 300px;
      display: flex;
      flex-direction: column;
      gap: 4px;
      min-width: 0;
    }
    .labelrow {
      display: flex;
      align-items: center;
      gap: 8px;
    }
    label {
      font-weight: 600;
      font-size: 15px;
    }
    .info {
      width: 24px;
      height: 24px;
      padding: 0;
      border-radius: 50%;
      border: 1px solid var(--z-charge);
      background: var(--z-card);
      color: var(--z-charge);
      font: inherit;
      font-size: 13px;
      font-weight: 700;
      font-style: italic;
      cursor: pointer;
      display: inline-flex;
      align-items: center;
      justify-content: center;
    }
    .info.on {
      background: var(--z-charge);
      color: #fff;
    }
    .dot {
      width: 8px;
      height: 8px;
      border-radius: 50%;
      background: var(--z-deliver);
    }
    .help {
      font-size: 13px;
      line-height: 1.5;
      color: var(--z-muted);
    }
    .more {
      margin-top: 6px;
      padding: 12px 14px;
      border-radius: 10px;
      background: var(--z-info-bg);
      font-size: 13px;
      line-height: 1.6;
      white-space: pre-line;
      max-width: 640px;
    }
    .meta {
      font-size: 12px;
      color: var(--z-muted);
    }
    .meta.warn {
      color: var(--z-warn-text);
    }
    .control {
      flex: 0 1 auto;
      display: flex;
      align-items: center;
      min-height: 44px;
    }
    .num {
      display: inline-flex;
      align-items: center;
      gap: 6px;
    }
    input,
    select {
      min-height: 40px;
      box-sizing: border-box;
      padding: 0 10px;
      border: 1px solid var(--z-border);
      border-radius: 8px;
      background: var(--z-bg);
      color: var(--z-text);
      font: inherit;
      font-size: 14px;
    }
    input {
      width: 110px;
      text-align: right;
      font-variant-numeric: tabular-nums;
    }
    select {
      max-width: 280px;
    }
    .unit {
      font-size: 13px;
      color: var(--z-muted);
      min-width: 44px;
    }
    .entity {
      font-size: 14px;
      max-width: 320px;
      overflow-wrap: anywhere;
      text-align: right;
    }
    .pending,
    .saved {
      font-size: 11px;
      padding: 1px 8px;
      border-radius: 999px;
      background: var(--z-info-bg);
      color: var(--z-muted);
    }
    .saved {
      color: var(--z-good-text, var(--z-text));
      background: var(--z-good-bg, var(--z-info-bg));
    }
    .error {
      margin: 0;
      font-size: 13px;
      color: var(--z-bad-text, #b3261e);
    }
    [aria-invalid="true"] {
      border-color: var(--z-bad-text, #b3261e);
    }
    .link {
      padding: 0;
      border: 0;
      background: none;
      color: var(--z-charge);
      font: inherit;
      font-weight: 600;
      cursor: pointer;
    }
    .entityrow {
      display: inline-flex;
      align-items: center;
      gap: 6px;
    }
    input.pick {
      width: 280px;
      max-width: 70vw;
      text-align: left;
    }
    .clear,
    .x {
      width: 32px;
      height: 32px;
      padding: 0;
      border: 0;
      border-radius: 50%;
      background: transparent;
      color: var(--z-muted);
      font-size: 18px;
      cursor: pointer;
    }
    .multi {
      display: flex;
      flex-direction: column;
      align-items: flex-end;
      gap: 8px;
      max-width: 360px;
    }
    .chips {
      display: flex;
      flex-wrap: wrap;
      justify-content: flex-end;
      gap: 6px;
      margin: 0;
      padding: 0;
      list-style: none;
    }
    .chip {
      display: inline-flex;
      align-items: center;
      gap: 2px;
      min-height: 36px;
      padding: 0 12px;
      border: 1px solid var(--z-border);
      border-radius: 999px;
      background: var(--z-bg);
      color: var(--z-text);
      font: inherit;
      font-size: 13px;
      cursor: pointer;
    }
    li.chip {
      padding: 0 2px 0 12px;
      border-top: 1px solid var(--z-border);
    }
    .chip[aria-pressed="true"],
    .chip.on {
      background: var(--z-info-bg);
      border-color: var(--z-charge);
      font-weight: 600;
    }
    .bar {
      position: sticky;
      bottom: 12px;
      display: flex;
      flex-direction: column;
      gap: 8px;
      padding: 12px 14px;
      border-radius: 12px;
      background: var(--z-card);
      border: 1px solid var(--z-charge);
      box-shadow: 0 4px 16px rgba(0, 0, 0, 0.12);
    }
    .barrow {
      display: flex;
      flex-wrap: wrap;
      justify-content: space-between;
      align-items: center;
      gap: 10px;
      font-size: 14px;
    }
    .buttons {
      display: flex;
      gap: 8px;
    }
    .buttons button {
      min-height: 40px;
      padding: 0 16px;
      border-radius: 10px;
      font: inherit;
      font-size: 14px;
      font-weight: 600;
      cursor: pointer;
    }
    .ghost {
      border: 1px solid var(--z-border);
      background: transparent;
      color: var(--z-text);
    }
    .primary {
      border: 0;
      background: var(--z-text);
      color: var(--z-on-text);
    }
    .switch {
      width: 48px;
      height: 28px;
      padding: 0;
      border-radius: 999px;
      border: 0;
      background: var(--z-track);
      position: relative;
      cursor: pointer;
    }
    .switch span {
      position: absolute;
      top: 3px;
      left: 3px;
      width: 22px;
      height: 22px;
      border-radius: 50%;
      background: var(--z-card);
      box-shadow: 0 1px 2px rgba(0, 0, 0, 0.2);
      transition: left 0.15s;
    }
    .switch[aria-checked="true"] {
      background: var(--z-charge);
    }
    .switch[aria-checked="true"] span {
      left: 23px;
    }
    :disabled {
      cursor: not-allowed;
    }
    @media (max-width: 700px) {
      .card {
        padding: 16px;
      }
      .groups {
        max-width: none;
        flex-direction: row;
        flex-wrap: wrap;
      }
      .groups button {
        width: auto;
      }
      .control {
        width: 100%;
      }
    }
  `;
	}
};
U([k({ attribute: !1 })], X.prototype, "view", void 0), U([k({ attribute: !1 })], X.prototype, "uiLang", void 0), U([k()], X.prototype, "locale", void 0), U([k({ attribute: !1 })], X.prototype, "friendlyName", void 0), U([k({ attribute: !1 })], X.prototype, "states", void 0), U([k({ attribute: !1 })], X.prototype, "save", void 0), U([A()], X.prototype, "group", void 0), U([A()], X.prototype, "tip", void 0), U([A()], X.prototype, "draft", void 0), U([A()], X.prototype, "errors", void 0), U([A()], X.prototype, "busy", void 0), U([A()], X.prototype, "saved", void 0), U([A()], X.prototype, "restarting", void 0), X = U([O("zephyr-settings")], X);
// src/diag.ts
function St(e, t, n) {
	let r = (e) => new Intl.NumberFormat(n, {
		minimumFractionDigits: 1,
		maximumFractionDigits: 1
	}).format(e / 1e3);
	switch (e.kind) {
		case "reason": return e.text?.[t] ?? L(t, "diag.event.reason_code", { code: e.code ?? "?" });
		case "mode": return L(t, "diag.event.mode", { mode: L(t, `mode.${e.mode ?? ""}`) });
		case "test": return L(t, "diag.event.test", { power: new Intl.NumberFormat(n).format(e.power ?? 0) });
		case "excluded_on": return L(t, "diag.event.excluded_on", { kw: r(e.power ?? 0) });
		case "flash": return L(t, "diag.event.flash", {
			set: e.set ?? "?",
			cause: L(t, `diag.cause.${e.cause ?? ""}`)
		});
		default: return L(t, `diag.event.${e.kind}`);
	}
}
function Ct(e) {
	return e.kind === "mode" ? "mode" : e.kind === "live" || e.kind === "shadow" || e.kind === "test" || e.kind === "test_end" ? "live" : e.kind === "excluded_on" || e.kind === "excluded_off" ? "airco" : e.kind === "flash" ? "write" : e.kind === "second_controller" ? "warning" : "control";
}
function wt(e, t, n) {
	let r = n === "fast_charge" || n === "fast_discharge" ? "zero_meter" : n;
	return ["fast_charge", "fast_discharge"].filter((e) => t.includes(e)).map((t) => ({
		mode: t,
		active: e === t,
		target: e === t ? r : t
	}));
}
var Tt = [
	[/^no P1 sensor chosen$/, "no_p1"],
	[/^P1 is not reporting$/, "p1_silent"],
	[/^no sets$/, "no_sets"],
	[/^set (\d+) is offline$/, "offline"],
	[/^set (\d+) reports a different serial number$/, "serial"],
	[/^set (\d+) reports an error$/, "fault"],
	[/^a write test is running$/, "test"]
];
function Et(e, t) {
	for (let [n, r] of Tt) {
		let i = n.exec(e);
		if (i) return L(t, `control.blocker.${r}`, { set: i[1] ?? "" });
	}
	return e;
}
function Dt(e) {
	let t = e.house.reduce((e, t) => e + t, 0), n = e.airco.reduce((e, t) => e + t, 0), r = Math.max(0, ...e.house.map((t, n) => t + (e.airco[n] ?? 0)));
	return {
		total: t,
		aircoTotal: n,
		top: Math.max(.5, Math.ceil(r * 2) / 2),
		learned: e.counts.filter((t) => t >= e.min_count).length
	};
}
// src/diagnostics.ts
var Z = class extends D {
	constructor(...e) {
		super(...e), this.uiLang = "en", this.locale = "en", this.timeZone = "UTC", this.admin = !1, this.busy = null, this.note = null, this.dayKind = "workday";
	}
	tr(e, t = {}) {
		return L(this.uiLang, e, t);
	}
	async run(e) {
		if (!this.busy) {
			this.busy = e, this.note = null;
			try {
				if (e === "download") await this.download?.();
				else {
					let e = await this.exportCosts?.();
					e && (this.note = {
						text: this.tr("diag.exported", {
							path: e.path,
							rows: e.rows
						}),
						error: !1
					});
				}
			} catch (e) {
				this.note = {
					text: this.tr("diag.failed", { error: e?.message ?? String(e) }),
					error: !0
				};
			} finally {
				this.busy = null;
			}
		}
	}
	render() {
		let e = this.view;
		return S`<div class="layout">
      <section class="card tools">
        <h2>${this.tr("diag.title")}</h2>
        <p class="muted">${this.tr("diag.intro")}</p>
        <div class="buttons">
          <button type="button" class="primary" ?disabled=${!e || this.busy !== null} @click=${() => void this.run("download")}>
            ${this.tr(this.busy === "download" ? "diag.busy" : "diag.download")}
          </button>
          ${this.admin ? S`<button type="button" class="ghost" ?disabled=${this.busy !== null} @click=${() => void this.run("export")}>
                ${this.tr(this.busy === "export" ? "diag.busy" : "diag.export")}
              </button>` : w}
        </div>
        ${this.note ? S`<p class=${this.note.error ? "note error" : "note"} role="status">${this.note.text}</p>` : w}
        ${e ? this.renderCounters(e) : S`<div class="skeleton"></div>`}
      </section>
      ${e?.profile ? this.renderProfile(e.profile) : w}
      <section class="card events" aria-labelledby="events-title">
        <div class="head">
          <h2 id="events-title">${this.tr("diag.events")}</h2>
          <button type="button" class="ghost small" @click=${() => this.refresh?.()}>${this.tr("diag.refresh")}</button>
        </div>
        ${e ? this.renderEvents(e) : S`<div class="skeleton"></div>`}
      </section>
    </div>`;
	}
	renderCounters(e) {
		if (!e.sets.length) return S`<p class="muted">${this.tr("diag.no_sets")}</p>`;
		let t = (e) => e === null ? "–" : new Intl.NumberFormat(this.locale).format(e);
		return S`<h3>${this.tr(e.shadow ? "diag.counters_shadow" : "diag.counters")}</h3>
      ${e.shadow ? S`<p class="note">${this.tr("diag.shadow_counts")}</p>` : w}
      <table>
        <thead>
          <tr>
            <th scope="col">${this.tr("diag.set")}</th>
            <th scope="col">${this.tr("diag.ram")}</th>
            <th scope="col">${this.tr("diag.flash")}</th>
            <th scope="col">${this.tr("diag.relay")}</th>
            <th scope="col">${this.tr("diag.failed_col")}</th>
          </tr>
        </thead>
        <tbody>
          ${e.sets.map((e) => S`<tr>
                <th scope="row">${e.number}</th>
                <td>${t(e.ram_24h)}</td>
                <td>${t(e.flash_24h)}</td>
                <td>${t(e.relay_24h)}</td>
                <td class=${e.failed_24h ? "bad" : ""}>${t(e.failed_24h)}</td>
              </tr>
              ${e.last_error ? S`<tr>
                    <td colspan="5" class="lasterror">${this.tr("diag.last_error", { error: e.last_error })}</td>
                  </tr>` : w}`)}
        </tbody>
      </table>
      <p class="muted small">${this.tr("diag.counters_note")}</p>`;
	}
	renderProfile(e) {
		let t = e[this.dayKind], n = Dt(t), r = (e, t = 1) => new Intl.NumberFormat(this.locale, {
			minimumFractionDigits: t,
			maximumFractionDigits: t
		}).format(e), i = t.airco.some((e) => e > 0) || e.workday.airco.some((e) => e > 0);
		return S`<section class="card profile" aria-labelledby="profile-title">
      <div class="head">
        <h2 id="profile-title">${this.tr("diag.profile")}</h2>
        <div class="tabs" role="group">
          ${["workday", "weekend"].map((e) => S`<button type="button" class=${this.dayKind === e ? "on" : ""} aria-pressed=${this.dayKind === e ? "true" : "false"} @click=${() => this.dayKind = e}>
              ${this.tr(`diag.${e}`)}
            </button>`)}
        </div>
      </div>
      <p class="muted">${this.tr("diag.profile_source", {
			source: e.source,
			hours: e.hours
		})}</p>
      ${n.learned === 0 ? S`<p class="note">${this.tr(`diag.profile_empty_${this.dayKind}`, { mean: r(e.mean, 2) })}</p>` : S`<p class="sum">
              ${this.tr("diag.profile_total", { kwh: r(n.total) })}${i ? S` · ${this.tr("diag.profile_airco", { kwh: r(n.aircoTotal) })}` : w}
            </p>
            <div class="pchart" role="img" aria-label=${this.tr("diag.profile_total", { kwh: r(n.total) })}>
              <div class="paxis"><span>${r(n.top)}</span><span>0</span></div>
              <div class="pbars">
                ${t.house.map((e, i) => {
			let a = t.airco[i] ?? 0;
			return S`<div class=${t.counts[i] >= t.min_count ? "pcol" : "pcol none"} title=${this.tr("diag.profile_hour", {
				hour: i,
				house: r(e, 2),
				airco: r(a, 2),
				n: t.counts[i]
			})}>
                    ${a > 0 ? S`<i class="air" style="height:${a / n.top * 100}%"></i>` : w}
                    <i class="house" style="height:${e / n.top * 100}%"></i>
                  </div>`;
		})}
              </div>
              <div class="pticks">${[
			0,
			6,
			12,
			18,
			23
		].map((e) => S`<span style="left:${(e + .5) / 24 * 100}%">${String(e).padStart(2, "0")}</span>`)}</div>
            </div>
            <div class="plegend">
              <span><i class="sw house"></i>${this.tr("diag.profile_house")}</span>
              ${i ? S`<span><i class="sw air"></i>${this.tr("diag.profile_airco_legend")}</span>` : w}
              <span><i class="sw house faint"></i>${this.tr("diag.profile_learned", {
			n: n.learned,
			mean: r(e.mean, 2)
		})}</span>
            </div>`}
    </section>`;
	}
	renderEvents(e) {
		if (!e.events.length) return S`<p class="muted">${this.tr("diag.no_events")}</p>`;
		let t = (/* @__PURE__ */ new Date()).toISOString();
		return S`<ol>
      ${e.events.map((e) => {
			let n = Ct(e), r = I(e.time, t, this.timeZone) ? P(e.time, this.locale, this.timeZone) : `${F(e.time, this.locale, this.timeZone)} ${P(e.time, this.locale, this.timeZone)}`;
			return S`<li>
          <time datetime=${e.time}>${r}</time>
          <span class="kind k-${n}">${this.tr(`diag.kind.${n}`)}</span>
          <span class="text">${St(e, this.uiLang, this.locale)}</span>
        </li>`;
		})}
    </ol>`;
	}
	static {
		this.styles = o`
    :host {
      display: block;
      color: var(--z-text);
      font-family: var(--z-font);
    }
    .layout {
      display: flex;
      flex-wrap: wrap;
      gap: 16px;
      align-items: flex-start;
    }
    .card {
      background: var(--z-card);
      border: 1px solid var(--z-border);
      border-radius: 16px;
      padding: 20px 24px;
      min-width: 0;
      box-sizing: border-box;
    }
    .tools {
      flex: 1 1 320px;
      max-width: 440px;
      display: flex;
      flex-direction: column;
      gap: 12px;
    }
    .events {
      flex: 999 1 480px;
    }
    .profile {
      flex: 999 1 480px;
      display: flex;
      flex-direction: column;
      gap: 10px;
    }
    .tabs {
      display: inline-flex;
      padding: 3px;
      border-radius: 999px;
      background: var(--z-track);
    }
    .tabs button {
      min-height: 32px;
      padding: 0 12px;
      border: 0;
      border-radius: 999px;
      background: transparent;
      color: var(--z-text);
      font-weight: 500;
    }
    .tabs button.on {
      background: var(--z-text);
      color: var(--z-on-text);
      font-weight: 600;
    }
    .sum {
      margin: 0;
      font-size: 14px;
      font-weight: 600;
    }
    .pchart {
      position: relative;
      height: 150px;
      margin: 6px 0 28px 40px;
    }
    .paxis {
      position: absolute;
      left: -40px;
      top: -6px;
      bottom: -6px;
      width: 34px;
      display: flex;
      flex-direction: column;
      justify-content: space-between;
      align-items: flex-end;
      font-size: 11px;
      color: var(--z-muted);
    }
    .pbars {
      display: flex;
      align-items: flex-end;
      gap: 3px;
      height: 100%;
      border-bottom: 1px solid var(--z-border);
    }
    .pcol {
      flex: 1 1 0;
      height: 100%;
      display: flex;
      flex-direction: column;
      justify-content: flex-end;
    }
    .pcol i {
      display: block;
      width: 100%;
    }
    .pcol .house {
      background: var(--z-charge);
      border-radius: 0 0 2px 2px;
    }
    .pcol .air {
      background: repeating-linear-gradient(45deg, var(--z-deliver) 0 2px, transparent 2px 5px);
      border: 1px solid var(--z-deliver);
      border-bottom: 0;
      box-sizing: border-box;
      border-radius: 2px 2px 0 0;
    }
    .pcol.none i {
      opacity: 0.35;
    }
    .pticks {
      position: absolute;
      left: 0;
      right: 0;
      bottom: -18px;
      font-size: 11px;
      color: var(--z-muted);
    }
    .pticks span {
      position: absolute;
      transform: translateX(-50%);
    }
    .plegend {
      display: flex;
      flex-wrap: wrap;
      gap: 6px 14px;
      font-size: 12px;
      color: var(--z-muted);
    }
    .plegend span {
      display: inline-flex;
      align-items: center;
      gap: 6px;
    }
    .sw {
      width: 12px;
      height: 12px;
      border-radius: 3px;
      display: inline-block;
    }
    .sw.house {
      background: var(--z-charge);
    }
    .sw.faint {
      opacity: 0.35;
    }
    .sw.air {
      background: repeating-linear-gradient(45deg, var(--z-deliver) 0 2px, transparent 2px 4px);
      border: 1px solid var(--z-deliver);
      box-sizing: border-box;
    }
    h2 {
      margin: 0;
      font-family: var(--z-font-head);
      font-size: 20px;
    }
    h3 {
      margin: 8px 0 0;
      font-size: 14px;
    }
    .head {
      display: flex;
      justify-content: space-between;
      align-items: center;
      gap: 12px;
      margin-bottom: 8px;
    }
    .muted {
      margin: 0;
      font-size: 13px;
      color: var(--z-muted);
      line-height: 1.5;
    }
    .small {
      font-size: 12px;
    }
    .buttons {
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
    }
    button {
      min-height: 44px;
      padding: 0 16px;
      border-radius: 10px;
      font: inherit;
      font-size: 14px;
      font-weight: 600;
      cursor: pointer;
    }
    button.small {
      min-height: 36px;
      padding: 0 12px;
      font-size: 13px;
    }
    .primary {
      border: 0;
      background: var(--z-text);
      color: var(--z-on-text);
    }
    .ghost {
      border: 1px solid var(--z-border);
      background: transparent;
      color: var(--z-text);
    }
    button:focus-visible {
      outline: 2px solid var(--z-charge);
      outline-offset: 2px;
    }
    :disabled {
      opacity: 0.6;
      cursor: not-allowed;
    }
    .note {
      margin: 0;
      padding: 10px 14px;
      border-radius: 10px;
      background: var(--z-info-bg);
      font-size: 13px;
      overflow-wrap: anywhere;
    }
    .note.error {
      color: var(--z-bad-text, #b3261e);
    }
    table {
      width: 100%;
      border-collapse: collapse;
      font-size: 13px;
      font-variant-numeric: tabular-nums;
    }
    th,
    td {
      padding: 6px 4px;
      text-align: right;
      border-bottom: 1px solid var(--z-border);
    }
    thead th {
      color: var(--z-muted);
      font-weight: 500;
      font-size: 12px;
    }
    th:first-child {
      text-align: left;
    }
    td.bad {
      color: var(--z-bad-text, #b3261e);
      font-weight: 700;
    }
    .lasterror {
      text-align: left;
      color: var(--z-muted);
      font-size: 12px;
      overflow-wrap: anywhere;
    }
    ol {
      list-style: none;
      margin: 0;
      padding: 0;
    }
    li {
      display: grid;
      grid-template-columns: auto auto 1fr;
      gap: 4px 12px;
      align-items: baseline;
      padding: 10px 0;
      border-top: 1px solid var(--z-border);
      font-size: 14px;
      line-height: 1.45;
    }
    time {
      color: var(--z-muted);
      font-variant-numeric: tabular-nums;
      font-size: 13px;
      white-space: nowrap;
    }
    .kind {
      font-size: 11px;
      padding: 1px 8px;
      border-radius: 999px;
      background: var(--z-info-bg);
      white-space: nowrap;
    }
    .k-warning {
      background: var(--z-warn-bg, var(--z-info-bg));
      color: var(--z-warn-text, var(--z-text));
    }
    .k-airco {
      background: var(--z-deliver-bg, var(--z-info-bg));
    }
    .skeleton {
      min-height: 120px;
      border-radius: 10px;
      background: var(--z-info-bg);
    }
    @media (max-width: 700px) {
      .card {
        padding: 16px;
      }
      .tools {
        max-width: none;
      }
      li {
        grid-template-columns: auto 1fr;
      }
      li .text {
        grid-column: 1 / -1;
      }
    }
  `;
	}
};
U([k({ attribute: !1 })], Z.prototype, "view", void 0), U([k({ attribute: !1 })], Z.prototype, "uiLang", void 0), U([k()], Z.prototype, "locale", void 0), U([k()], Z.prototype, "timeZone", void 0), U([k({ type: Boolean })], Z.prototype, "admin", void 0), U([k({ attribute: !1 })], Z.prototype, "download", void 0), U([k({ attribute: !1 })], Z.prototype, "exportCosts", void 0), U([k({ attribute: !1 })], Z.prototype, "refresh", void 0), U([A()], Z.prototype, "busy", void 0), U([A()], Z.prototype, "note", void 0), U([A()], Z.prototype, "dayKind", void 0), Z = U([O("zephyr-diagnostics")], Z);
// src/savings.ts
var Ot, kt = (e) => e <= 0 ? 0 : Math.ceil(e * 2) / 2;
function At(e) {
	let t = e.map((e) => e.savings_battery ?? 0), n = t.map(Math.abs).filter((e) => e > 0).sort((e, t) => e - t), r = n.length ? n[Math.floor(n.length * .75)] : .5, i = Math.max(.5, r * 2), a = Math.min(i, Math.max(0, ...t)), o = Math.max(-i, Math.min(0, ...t));
	return {
		top: Math.max(.5, kt(a)),
		bottom: -kt(-o)
	};
}
var Q = class extends D {
	static {
		Ot = this;
	}
	constructor(...e) {
		super(...e), this.uiLang = "en", this.locale = "en", this.timeZone = "UTC", this.admin = !1, this.period = "month", this.form = Ot.storedForm(), this.busy = !1, this.result = null;
	}
	tr(e, t = {}) {
		return L(this.uiLang, e, t);
	}
	render() {
		let e = this.view;
		if (!e) return S`<div class="skeleton"></div>`;
		let t = e.periods[this.period];
		return S`<div class="layout">
      <section class="card hero" aria-labelledby="sv-title">
        <div class="head">
          <h2 id="sv-title">${this.tr("savings.title")}</h2>
          <div class="tabs" role="group" aria-label=${this.tr("savings.period")}>
            ${[
			"today",
			"week",
			"month",
			"year"
		].map((e) => S`<button type="button" class=${e === this.period ? "on" : ""} aria-pressed=${e === this.period ? "true" : "false"} @click=${() => this.period = e}>
                <span class="long">${this.tr(`savings.p_${e}`)}</span><span class="short">${this.tr(`savings.ps_${e}`)}</span>
              </button>`)}
          </div>
        </div>
        ${this.renderHero(t)}
      </section>
      <section class="card split" aria-labelledby="sv-split">
        <h2 id="sv-split">${this.tr("savings.split_title", { period: this.tr(`savings.p_${this.period}`).toLowerCase() })}</h2>
        ${this.renderSplit(t)}
      </section>
      <section class="card days" aria-labelledby="sv-days">
        <h2 id="sv-days">${this.tr("savings.days_title")}</h2>
        ${this.renderDays(e.days)}
      </section>
      <section class="card notes" aria-labelledby="sv-notes">
        <h2 id="sv-notes">${this.tr("savings.notes_title")}</h2>
        <ul>
          <li>${this.tr("savings.note_compare")}</li>
          <li>${this.tr("savings.note_fixed")}</li>
          ${e.saldering_until ? S`<li>${this.tr("savings.note_saldering", { date: this.date(e.saldering_until) })}</li>` : w}
          ${e.backfilled_days && e.measured_since ? S`<li>${this.tr("savings.note_hourly", { date: this.date(e.measured_since) })}</li>` : w}
          ${e.since ? S`<li>${this.tr("savings.note_since", { date: this.date(e.since) })}</li>` : w}
        </ul>
      </section>
      ${this.admin && e.can_backfill ? this.renderBackfill(e) : w}
    </div>`;
	}
	choices(e, t = "sensor") {
		return _t(this.states, t, e);
	}
	picker(e, t, n, r, i) {
		let a = `bf-${e}`, o = r ? n.find((e) => e.id === r) ?? {
			id: r,
			name: r
		} : null;
		return S`<label class="field" for=${a}>
      <span>${t}${i ? S` <em>(${this.tr("savings.optional")})</em>` : w}</span>
      <input
        id=${a}
        type="text"
        list=${`${a}-list`}
        autocomplete="off"
        placeholder=${this.tr("savings.choose_entity")}
        .value=${o ? q(o) : ""}
        @change=${(t) => {
			let r = t.target.value;
			this.form = {
				...this.form,
				[e]: vt(r, n) ?? (r.trim() ? r.trim() : null)
			};
		}}
      />
      <datalist id=${`${a}-list`}>${n.map((e) => S`<option value=${q(e)}></option>`)}</datalist>
    </label>`;
	}
	defaultFirst(e) {
		let t = e.measured_since ?? (/* @__PURE__ */ new Date()).toISOString().slice(0, 10), n = /* @__PURE__ */ new Date(`${t}T12:00:00Z`);
		return n.setUTCDate(n.getUTCDate() - 30), n.toISOString().slice(0, 10);
	}
	static storedForm() {
		try {
			let e = window.localStorage.getItem("zephyr.backfill"), t = e ? JSON.parse(e) : {};
			return {
				charge_entity: t.charge_entity,
				discharge_entity: t.discharge_entity,
				price_entity: t.price_entity
			};
		} catch {
			return {};
		}
	}
	async run(e) {
		if (this.backfill && !this.busy) {
			if (e) try {
				window.localStorage.setItem("zephyr.backfill", JSON.stringify(e));
			} catch {}
			this.busy = !0, this.result = null;
			try {
				this.result = await this.backfill(e);
			} catch (e) {
				this.result = {
					ok: !1,
					error: e?.message ?? String(e)
				};
			} finally {
				this.busy = !1;
			}
		}
	}
	renderBackfill(e) {
		let t = this.choices("energy"), n = {
			first: this.form.first ?? this.defaultFirst(e),
			charge_entity: this.form.charge_entity ?? "",
			discharge_entity: this.form.discharge_entity ?? "",
			solar_entity: this.form.solar_entity === void 0 ? e.defaults?.solar_entity ?? null : this.form.solar_entity,
			price_entity: this.form.price_entity === void 0 ? e.defaults?.price_entity ?? null : this.form.price_entity
		}, r = !!(n.first && n.charge_entity && n.discharge_entity), i = this.result;
		return S`<section class="card backfill" aria-labelledby="sv-bf">
      <h2 id="sv-bf">${this.tr("savings.bf_title")}</h2>
      <p class="muted">${this.tr("savings.bf_intro", { date: e.measured_since ? this.date(e.measured_since) : "–" })}</p>
      <div class="form">
        <label class="field" for="bf-first">
          <span>${this.tr("savings.bf_first")}</span>
          <input id="bf-first" type="date" .value=${n.first} max=${e.measured_since ?? ""} @change=${(e) => this.form = {
			...this.form,
			first: e.target.value
		}} />
        </label>
        ${this.picker("charge_entity", this.tr("savings.bf_charge"), t, n.charge_entity, !1)}
        ${this.picker("discharge_entity", this.tr("savings.bf_discharge"), t, n.discharge_entity, !1)}
        ${this.picker("solar_entity", this.tr("savings.bf_solar"), t, n.solar_entity, !0)}
        <fieldset class="field price">
          <legend>${this.tr("savings.bf_price")}</legend>
          <label class="radio">
            <input type="radio" name="bf-price" .checked=${n.price_entity === "energyzero"} @change=${() => this.form = {
			...this.form,
			price_entity: "energyzero"
		}} />
            ${this.tr("savings.bf_price_ez")}
          </label>
          <label class="radio">
            <input
              type="radio"
              name="bf-price"
              .checked=${n.price_entity !== "energyzero"}
              @change=${() => this.form = {
			...this.form,
			price_entity: e.defaults?.price_entity === "energyzero" ? null : e.defaults?.price_entity ?? null
		}}
            />
            ${this.tr("savings.bf_price_sensor")}
          </label>
          ${n.price_entity === "energyzero" ? w : this.picker("price_entity", this.tr("savings.bf_price_pick"), this.choices(null), n.price_entity, !1)}
        </fieldset>
      </div>
      <p class="muted small">${this.tr("savings.bf_help")}</p>
      <div class="buttons">
        <button type="button" class="primary" ?disabled=${!r || this.busy} @click=${() => void this.run(n)}>
          ${this.tr(this.busy ? "savings.bf_busy" : "savings.bf_run")}
        </button>
        ${e.backfilled_days ? S`<button type="button" class="ghost" ?disabled=${this.busy} @click=${() => void this.run(null)}>
              ${this.tr("savings.bf_clear", { n: e.backfilled_days })}
            </button>` : w}
      </div>
      ${i ? S`<p class=${i.ok ? "result" : "result bad"} role="status">
            ${i.ok ? i.removed === void 0 ? i.days ? this.tr("savings.bf_done", {
			n: i.days,
			first: this.date(i.first),
			last: this.date(i.last),
			skipped: i.skipped ?? 0,
			unpriced: (i.hours ?? 0) - (i.priced_hours ?? 0)
		}) + (i.price_failed_days ? ` ${this.tr("savings.bf_ez_failed", { n: i.price_failed_days })}` : "") : this.tr("savings.bf_nothing") : this.tr("savings.bf_removed", { n: i.removed }) : this.tr(`savings.bf_err_${i.error}`, { entities: (i.entities ?? []).join(", ") })}
          </p>` : w}
    </section>`;
	}
	date(e) {
		return new Intl.DateTimeFormat(this.locale, {
			day: "numeric",
			month: "long",
			year: "numeric",
			timeZone: this.timeZone
		}).format(new Date(e));
	}
	renderHero(e) {
		if (e.cost === null || e.cost_no_battery === null || e.savings_battery === null) return S`<p class="muted">${this.tr("savings.no_data")}</p>`;
		let t = e.savings_battery, n = t < 0, r = Math.max(e.cost, e.cost_no_battery, .01);
		return S`<div class="big ${n ? "loss" : "win"}">
        <span class="amount">${n ? "−" : ""}${j(Math.abs(t), this.locale)}</span>
        <span class="label">${this.tr(n ? "savings.lost" : "savings.saved")}</span>
      </div>
      <div class="compare">
        <div class="row">
          <span class="name">${this.tr("savings.without")}</span>
          <span class="bar"><i class="nb" style="width:${Math.max(0, e.cost_no_battery) / r * 100}%"></i></span>
          <span class="val">${j(e.cost_no_battery, this.locale)}</span>
        </div>
        <div class="row">
          <span class="name">${this.tr("savings.paid")}</span>
          <span class="bar"><i class="paid" style="width:${Math.max(0, e.cost) / r * 100}%"></i></span>
          <span class="val">${j(e.cost, this.locale)}</span>
        </div>
      </div>
      ${e.incomplete_quarters ? S`<p class="warn">${this.tr("savings.incomplete", {
			n: e.incomplete_quarters,
			total: e.quarters
		})}</p>` : w}`;
	}
	renderDays(e) {
		if (!e.length) return S`<p class="muted">${this.tr("savings.no_data")}</p>`;
		let { top: t, bottom: n } = At(e), r = t - n, i = t / r * 100, a = (e) => new Intl.DateTimeFormat(this.locale, {
			weekday: "short",
			day: "numeric",
			month: "short",
			timeZone: "UTC"
		}).format(/* @__PURE__ */ new Date(`${e}T12:00:00Z`)), o = e.reduce((e, t) => e + (t.savings_battery ?? 0), 0);
		return S`<p class="muted">${this.tr("savings.days_total", {
			n: e.length,
			amount: j(o, this.locale)
		})}</p>
      <div class="dchart">
        <div class="daxis" aria-hidden="true">
          <span style="top:0">${j(t, this.locale)}</span>
          <span style="top:${i}%">€ 0</span>
          ${n < 0 ? S`<span style="top:100%">−${j(-n, this.locale)}</span>` : w}
        </div>
        <div class="dbars">
          <div class="zero" style="top:${i}%"></div>
          ${e.map((e) => {
			let o = e.savings_battery ?? 0, s = Math.max(n, Math.min(t, o)), c = s !== o, l = Math.abs(s) / r * 100, u = o >= 0 ? `top:${i - l}%;height:${l}%` : `top:${i}%;height:${l}%`, d = [e.incomplete ? this.tr("savings.day_incomplete") : "", e.hourly ? this.tr("savings.day_hourly") : ""].filter(Boolean), f = `${a(e.day)}: ${e.savings_battery === null ? this.tr("savings.unknown") : j(o, this.locale)}${d.length ? ` (${d.join(", ")})` : ""}`;
			return S`<div class="dcol" title=${f} aria-label=${f}>
              <i class=${`${o >= 0 ? "win" : "loss"}${e.incomplete ? " part" : ""}${c ? " cut" : ""}${e.hourly ? " hourly" : ""}`} style=${u}></i>
              ${c ? S`<span class=${o >= 0 ? "cutlabel up" : "cutlabel down"}>${o >= 0 ? "▲" : "▼"} ${j(o, this.locale)}</span>` : w}
            </div>`;
		})}
        </div>
        <div class="dticks" aria-hidden="true">
          ${e.map((t, n) => n % 7 == 0 && e.length - n > 3 ? S`<span style="left:${(n + .5) / e.length * 100}%">${new Intl.DateTimeFormat(this.locale, {
			day: "numeric",
			month: "short",
			timeZone: "UTC"
		}).format(/* @__PURE__ */ new Date(`${t.day}T12:00:00Z`))}</span>` : w)}
        </div>
      </div>
      <div class="legend">
        <span><i class="sw win"></i>${this.tr("savings.leg_win")}</span>
        <span><i class="sw loss"></i>${this.tr("savings.leg_loss")}</span>
        <span><i class="sw part"></i>${this.tr("savings.leg_part")}</span>
        ${e.some((e) => e.hourly) ? S`<span><i class="sw hourly"></i>${this.tr("savings.leg_hourly")}</span>` : w}
      </div>`;
	}
	renderSplit(e) {
		let t = e.savings_solar_via_battery, n = e.savings_trade, r = e.discharge_kwh > 0 && e.savings_battery !== null ? e.savings_battery / e.discharge_kwh : null;
		return S`<dl>
        <div>
          <dt><i class="sw solar"></i>${this.tr("savings.solar_part")}</dt>
          <dd>${t === null ? "–" : j(t, this.locale)}</dd>
          <p>${this.tr("savings.solar_part_help")}</p>
        </div>
        <div>
          <dt><i class="sw trade"></i>${this.tr("savings.trade_part")}</dt>
          <dd>${n === null ? "–" : j(n, this.locale)}</dd>
          <p>${this.tr("savings.trade_part_help")}</p>
        </div>
      </dl>
      <div class="facts">
        <span><b>${M(e.charge_kwh, this.locale)}</b> ${this.tr("savings.charged")}</span>
        <span><b>${M(e.discharge_kwh, this.locale)}</b> ${this.tr("savings.delivered")}</span>
        ${r === null ? w : S`<span><b>${j(r, this.locale)}</b> ${this.tr("savings.per_kwh")}</span>`}
      </div>`;
	}
	static {
		this.styles = o`
    :host {
      display: block;
      color: var(--z-text);
      font-family: var(--z-font);
    }
    .layout {
      display: grid;
      grid-template-columns: minmax(0, 1fr) minmax(0, 1fr);
      gap: 16px;
    }
    .card {
      background: var(--z-card);
      border: 1px solid var(--z-border);
      border-radius: 16px;
      padding: 20px 24px;
      min-width: 0;
      display: flex;
      flex-direction: column;
      gap: 12px;
    }
    h2 {
      margin: 0;
      font-family: var(--z-font-head);
      font-size: 20px;
    }
    .head {
      display: flex;
      justify-content: space-between;
      align-items: center;
      gap: 12px;
      flex-wrap: wrap;
    }
    .tabs {
      display: inline-flex;
      padding: 3px;
      border-radius: 999px;
      background: var(--z-track);
    }
    .tabs button {
      min-height: 32px;
      padding: 0 12px;
      border: 0;
      border-radius: 999px;
      background: transparent;
      color: var(--z-text);
      font: inherit;
      font-size: 13px;
      cursor: pointer;
    }
    .tabs button.on {
      background: var(--z-text);
      color: var(--z-on-text);
      font-weight: 600;
    }
    .muted {
      margin: 0;
      color: var(--z-muted);
      font-size: 13px;
    }
    .big {
      display: flex;
      align-items: baseline;
      gap: 10px;
    }
    .amount {
      font-family: var(--z-font-head);
      font-size: 44px;
      font-weight: 700;
      font-variant-numeric: tabular-nums;
    }
    .big.win .amount {
      color: var(--z-export);
    }
    .big.loss .amount {
      color: var(--z-deliver);
    }
    .label {
      color: var(--z-muted);
      font-size: 15px;
    }
    .compare {
      display: flex;
      flex-direction: column;
      gap: 8px;
    }
    .row {
      display: grid;
      grid-template-columns: 110px 1fr auto;
      align-items: center;
      gap: 10px;
      font-size: 14px;
    }
    .bar {
      height: 12px;
      border-radius: 6px;
      background: var(--z-track);
      overflow: hidden;
    }
    .bar i {
      display: block;
      height: 100%;
      border-radius: 6px;
    }
    .bar .nb {
      background: var(--z-hold-a);
    }
    .bar .paid {
      background: var(--z-text);
    }
    .val {
      font-weight: 600;
      font-variant-numeric: tabular-nums;
    }
    .warn {
      margin: 0;
      padding: 8px 12px;
      border-radius: 10px;
      background: var(--z-warn-bg);
      color: var(--z-warn-text);
      font-size: 13px;
    }
    .days,
    .notes {
      grid-column: 1 / -1;
    }
    .dchart {
      position: relative;
      height: 200px;
      margin: 6px 0 26px 56px;
    }
    .daxis span {
      position: absolute;
      left: -56px;
      width: 50px;
      transform: translateY(-50%);
      text-align: right;
      font-size: 11px;
      color: var(--z-muted);
    }
    .dbars {
      position: absolute;
      inset: 0;
      display: flex;
      gap: 3px;
    }
    .zero {
      position: absolute;
      left: 0;
      right: 0;
      border-top: 1px solid var(--z-border);
    }
    .dcol {
      position: relative;
      flex: 1 1 0;
    }
    .dcol i {
      position: absolute;
      left: 0;
      right: 0;
      border-radius: 2px;
    }
    i.win,
    .sw.win {
      background: var(--z-export);
    }
    i.loss,
    .sw.loss {
      background: var(--z-deliver);
    }
    i.part {
      opacity: 0.45;
    }
    i.loss.cut {
      border-bottom: 3px dashed var(--z-card);
    }
    i.win.cut {
      border-top: 3px dashed var(--z-card);
    }
    .cutlabel {
      position: absolute;
      left: 50%;
      transform: translateX(-50%);
      white-space: nowrap;
      font-size: 11px;
      font-weight: 700;
      color: var(--z-text);
      background: var(--z-card);
      padding: 0 4px;
      border-radius: 4px;
    }
    .cutlabel.down {
      top: calc(100% + 2px);
    }
    .cutlabel.up {
      bottom: calc(100% + 2px);
    }
    .dcol:last-child .cutlabel {
      left: auto;
      right: 0;
      transform: none;
    }
    .short {
      display: none;
    }
    i.hourly {
      background-image: repeating-linear-gradient(135deg, rgba(255, 255, 255, 0.45) 0 2px, transparent 2px 5px);
    }
    .sw.hourly {
      background: var(--z-export) repeating-linear-gradient(135deg, rgba(255, 255, 255, 0.55) 0 2px, transparent 2px 4px);
    }
    .backfill {
      grid-column: 1 / -1;
    }
    .form {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
      gap: 12px 16px;
    }
    .field {
      display: flex;
      flex-direction: column;
      gap: 4px;
      font-size: 13px;
      font-weight: 600;
    }
    .field em {
      font-weight: 400;
      color: var(--z-muted);
    }
    fieldset.field {
      margin: 0;
      padding: 0;
      border: 0;
      min-width: 0;
    }
    fieldset.field legend {
      padding: 0;
      margin-bottom: 4px;
    }
    .radio {
      display: flex;
      align-items: center;
      gap: 8px;
      min-height: 32px;
      font-weight: 400;
    }
    .radio input {
      min-height: 0;
      width: 18px;
      height: 18px;
      margin: 0;
    }
    .field input {
      min-height: 40px;
      padding: 0 10px;
      border: 1px solid var(--z-border);
      border-radius: 10px;
      background: var(--z-bg);
      color: var(--z-text);
      font: inherit;
      font-weight: 400;
    }
    .small {
      font-size: 12px;
    }
    .buttons {
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
    }
    .buttons button {
      min-height: 44px;
      padding: 0 16px;
      border-radius: 10px;
      font: inherit;
      font-size: 14px;
      font-weight: 600;
      cursor: pointer;
    }
    .primary {
      border: 0;
      background: var(--z-text);
      color: var(--z-on-text);
    }
    .ghost {
      border: 1px solid var(--z-border);
      background: transparent;
      color: var(--z-text);
    }
    button:disabled {
      opacity: 0.5;
      cursor: not-allowed;
    }
    .result {
      margin: 0;
      padding: 10px 14px;
      border-radius: 10px;
      background: var(--z-good-bg);
      color: var(--z-good-text);
      font-size: 13px;
    }
    .result.bad {
      background: var(--z-bad-bg);
      color: var(--z-bad-text);
    }
    .sw.part {
      background: repeating-linear-gradient(45deg, var(--z-export) 0 2px, transparent 2px 4px);
      border: 1px solid var(--z-export);
      box-sizing: border-box;
    }
    .dticks {
      position: absolute;
      left: 0;
      right: 0;
      bottom: -20px;
      font-size: 11px;
      color: var(--z-muted);
    }
    .dticks span {
      position: absolute;
      transform: translateX(-50%);
      white-space: nowrap;
    }
    .legend {
      display: flex;
      flex-wrap: wrap;
      gap: 6px 14px;
      font-size: 12px;
      color: var(--z-muted);
    }
    .legend span,
    dt {
      display: inline-flex;
      align-items: center;
      gap: 6px;
    }
    .sw {
      width: 12px;
      height: 12px;
      border-radius: 3px;
      display: inline-block;
      flex: none;
    }
    .sw.solar {
      background: var(--z-solar);
    }
    .sw.trade {
      background: var(--z-charge);
    }
    dl {
      margin: 0;
      display: flex;
      flex-direction: column;
      gap: 12px;
    }
    dl div {
      display: grid;
      grid-template-columns: 1fr auto;
      gap: 2px 12px;
    }
    dt {
      font-weight: 600;
      font-size: 14px;
    }
    dd {
      margin: 0;
      font-weight: 700;
      font-variant-numeric: tabular-nums;
    }
    dl p {
      grid-column: 1 / -1;
      margin: 0;
      font-size: 13px;
      color: var(--z-muted);
      line-height: 1.45;
    }
    .facts {
      display: flex;
      flex-wrap: wrap;
      gap: 6px 16px;
      padding-top: 10px;
      border-top: 1px solid var(--z-border);
      font-size: 13px;
      color: var(--z-muted);
    }
    .facts b {
      color: var(--z-text);
    }
    .notes ul {
      margin: 0;
      padding-left: 18px;
      font-size: 13px;
      color: var(--z-muted);
      line-height: 1.5;
      display: flex;
      flex-direction: column;
      gap: 4px;
    }
    .skeleton {
      height: 320px;
      border-radius: 16px;
      background: var(--z-track);
    }
    @media (max-width: 900px) {
      .layout {
        grid-template-columns: 1fr;
      }

      .card {
        padding: 16px;
      }
      .amount {
        font-size: 36px;
      }
      .long {
        display: none;
      }
      .short {
        display: inline;
      }
      .row {
        grid-template-columns: 90px 1fr auto;
      }
    }
  `;
	}
};
U([k({ attribute: !1 })], Q.prototype, "view", void 0), U([k({ attribute: !1 })], Q.prototype, "uiLang", void 0), U([k()], Q.prototype, "locale", void 0), U([k()], Q.prototype, "timeZone", void 0), U([k({ type: Boolean })], Q.prototype, "admin", void 0), U([k({ attribute: !1 })], Q.prototype, "states", void 0), U([k({ attribute: !1 })], Q.prototype, "backfill", void 0), U([A()], Q.prototype, "period", void 0), U([A()], Q.prototype, "form", void 0), U([A()], Q.prototype, "busy", void 0), U([A()], Q.prototype, "result", void 0), Q = Ot = U([O("zephyr-savings")], Q);
// src/zephyr-panel.ts
var jt = "/zephyr_static", Mt = [
	[
		"Inter",
		400,
		"inter-latin-400-normal.woff2"
	],
	[
		"Inter",
		600,
		"inter-latin-600-normal.woff2"
	],
	[
		"Inter",
		700,
		"inter-latin-700-normal.woff2"
	],
	[
		"Space Grotesk",
		700,
		"space-grotesk-latin-700-normal.woff2"
	]
];
function Nt(e) {
	let t = "zephyr-fonts";
	if (document.getElementById(t)) return;
	let n = document.createElement("style");
	n.id = t, n.textContent = Mt.map(([t, n, r]) => `@font-face{font-family:"${t}";font-style:normal;font-weight:${n};font-display:swap;src:url("${e}/fonts/${r}") format("woff2");}`).join("\n"), document.head.appendChild(n);
}
var $ = class extends D {
	constructor(...e) {
		super(...e), this.narrow = !1, this.status = "loading", this.view = "plan", this.clockMs = Date.now(), this.period = pt(), this.confirmLive = !1, this.controlBusy = !1, this.controlError = null, this.pendingMode = null, this.planFor = "", this.planBusy = !1, this.subscribing = !1, this.onReady = () => {
			this.status = "loading", this.subscribe();
		}, this.onDisconnected = () => {
			this.unsubscribe = void 0, this.status = "disconnected";
		}, this.backfillSavings = async (e) => {
			if (!this.hass) return {
				ok: !1,
				error: "no_connection"
			};
			let t = await this.hass.callWS(e ? {
				type: "zephyr/savings/backfill",
				...e
			} : {
				type: "zephyr/savings/backfill",
				clear: !0
			});
			return t.ok && await this.loadSavings(), t;
		}, this.downloadDiagnostics = async () => {
			if (!this.hass || !this.eventsView) return;
			let e = await this.hass.callWS({
				type: "auth/sign_path",
				path: `/api/diagnostics/config_entry/${this.eventsView.entry_id}`
			}), t = document.createElement("a");
			t.href = e.path, t.download = "", document.body.appendChild(t), t.click(), t.remove();
		}, this.exportCosts = async () => {
			if (!this.hass) throw Error("no connection");
			return (await this.hass.callWS({
				type: "call_service",
				domain: "zephyr",
				service: "export_costs",
				service_data: {},
				return_response: !0
			})).response;
		}, this.saveSettings = async (e, t) => {
			if (!this.hass) return {
				ok: !1,
				errors: { base: "failed" }
			};
			let n = await this.hass.callWS({
				type: "zephyr/settings/set",
				changes: e,
				reset: t
			});
			return n.ok && (n.reload ? (window.setTimeout(() => void this.loadSettings(), 3e3), window.setTimeout(() => void this.loadSettings(), 8e3)) : this.loadSettings()), n;
		};
	}
	get base() {
		return this.panel?.config?.static ?? jt;
	}
	get uiLang() {
		return Je(this.hass?.locale?.language ?? this.hass?.language);
	}
	get locale() {
		return this.hass?.locale?.language ?? this.hass?.language ?? "en";
	}
	get timeZone() {
		return this.hass?.config.time_zone ?? Intl.DateTimeFormat().resolvedOptions().timeZone;
	}
	tr(e, t = {}) {
		return L(this.uiLang, e, t);
	}
	connectedCallback() {
		super.connectedCallback(), Nt(this.base), this.clockTimer = window.setInterval(() => this.clockMs = Date.now(), 3e4), this.planTimer = window.setInterval(() => void this.loadPlan(!0), 3e5), this.hass && this.subscribe();
	}
	disconnectedCallback() {
		super.disconnectedCallback(), window.clearInterval(this.clockTimer), window.clearInterval(this.planTimer), window.clearInterval(this.setsTimer), window.clearTimeout(this.retryTimer), this.watch(void 0), this.stop();
	}
	updated(e) {
		e.has("hass") && this.hass && (this.toggleAttribute("dark", !!this.hass.themes?.darkMode), this.hass.connection !== this.watchedConnection && this.watch(this.hass.connection), !this.unsubscribe && !this.subscribing && this.status !== "disconnected" && this.subscribe());
	}
	watch(e) {
		this.watchedConnection?.removeEventListener("ready", this.onReady), this.watchedConnection?.removeEventListener("disconnected", this.onDisconnected), this.watchedConnection = e, e?.addEventListener("ready", this.onReady), e?.addEventListener("disconnected", this.onDisconnected);
	}
	async subscribe() {
		if (!(!this.hass || this.subscribing || this.unsubscribe)) {
			this.subscribing = !0, window.clearTimeout(this.retryTimer);
			try {
				this.unsubscribe = await this.hass.connection.subscribeMessage((e) => this.onEvent(e), { type: "zephyr/subscribe" });
			} catch (e) {
				e.code === "not_loaded" && (this.status = "not_loaded"), this.retry(1e4);
			} finally {
				this.subscribing = !1;
			}
		}
	}
	async stop() {
		let e = this.unsubscribe;
		this.unsubscribe = void 0;
		try {
			await e?.();
		} catch {}
	}
	async loadPlan(e = !1) {
		let t = this.now;
		if (!this.hass || !t?.price_entity || this.planBusy) {
			t && !t.price_entity && (this.planView = void 0);
			return;
		}
		let n = t.plan?.calculated_at ?? "none";
		if (e || n !== this.planFor) {
			this.planBusy = !0;
			try {
				this.planView = await this.hass.callWS({ type: "zephyr/plan" }), this.planFor = n;
			} catch {} finally {
				this.planBusy = !1;
			}
		}
	}
	async loadSets() {
		if (this.hass && this.view === "sets") try {
			this.setsView = await this.hass.callWS({ type: "zephyr/sets" });
		} catch {}
	}
	async loadSavings() {
		if (this.hass && this.view === "savings") try {
			this.savingsView = await this.hass.callWS({ type: "zephyr/savings" });
		} catch {}
	}
	async loadSettings() {
		if (this.hass) try {
			this.settingsView = await this.hass.callWS({ type: "zephyr/settings/get" });
		} catch {}
	}
	async loadEvents() {
		if (this.hass && this.view === "diagnostics") try {
			this.eventsView = await this.hass.callWS({ type: "zephyr/events" });
		} catch {}
	}
	get admin() {
		return !!this.hass?.user?.is_admin;
	}
	async callService(e, t, n) {
		if (this.hass && !this.controlBusy) {
			this.controlBusy = !0, this.controlError = null;
			try {
				await this.hass.callWS({
					type: "call_service",
					domain: e,
					service: t,
					service_data: n
				});
			} catch (e) {
				this.controlError = e?.message ?? String(e);
			} finally {
				this.controlBusy = !1;
			}
		}
	}
	setMode(e) {
		let t = this.now?.entities.mode;
		t && e !== this.now?.mode && (this.pendingMode = e, window.clearTimeout(this.pendingTimer), this.pendingTimer = window.setTimeout(() => this.pendingMode = null, 5e3), this.callService("select", "select_option", {
			entity_id: t,
			option: e
		}));
	}
	async setLive(e) {
		let t = this.now?.entities.live;
		this.confirmLive = !1, t && await this.callService("switch", e ? "turn_on" : "turn_off", { entity_id: t });
	}
	show(e) {
		this.view = e, window.clearInterval(this.setsTimer), e === "sets" ? (this.loadSets(), this.setsTimer = window.setInterval(() => void this.loadSets(), 1e4)) : e === "settings" ? this.loadSettings() : e === "savings" ? this.loadSavings() : e === "diagnostics" && (this.loadEvents(), this.setsTimer = window.setInterval(() => void this.loadEvents(), 15e3));
	}
	retry(e) {
		window.clearTimeout(this.retryTimer), this.retryTimer = window.setTimeout(() => void this.subscribe(), e);
	}
	onEvent(e) {
		e.type === "now" ? (this.now = e.data, this.pendingMode === e.data.mode && (this.pendingMode = null), this.status = "ok", this.clockMs = Date.now(), this.loadPlan()) : e.type === "unloaded" && (this.unsubscribe = void 0, this.status = "reloading", this.retry(3e3));
	}
	render() {
		return S`
      <div class="page">
        ${this.renderHeader()}
        <main>${this.renderBanner()} ${this.renderView()}</main>
      </div>
    `;
	}
	renderHeader() {
		let e = this.now, t = [
			["plan", "menu.plan"],
			["sets", (e?.sets_total ?? 1) <= 1 ? "menu.battery" : "menu.sets"],
			["savings", "menu.savings"],
			["settings", "menu.settings"],
			["diagnostics", "menu.diagnostics"]
		];
		return S`
      <header>
        <div class="brand">
          <img src="${this.base}/logo.png" alt="" width="32" height="32" />
          <span>ZEPHYR</span>
        </div>
        <nav aria-label=${this.tr("menu.label")}>
          ${t.map(([e, t]) => S`<button
                type="button"
                class=${this.view === e ? "tab active" : "tab"}
                aria-current=${this.view === e ? "page" : "false"}
                @click=${() => this.show(e)}
              >
                ${this.tr(t)}
              </button>`)}
        </nav>
        <div class="meta">
          ${e ? this.renderControls(e) : w}
          <span class="time">${P(new Date(this.clockMs).toISOString(), this.locale, this.timeZone)}</span>
        </div>
      </header>
    `;
	}
	renderControls(e) {
		let t = this.admin && !!e.entities?.mode, n = this.admin && !!e.entities?.live, r = this.tr(e.live ? "header.live" : "header.shadow"), i = this.tr(e.live ? "header.live_title" : "header.shadow_title");
		return S`${t ? S`<label class="chipselect">
            <span class="sr">${this.tr("control.mode")}</span>
            <select class="chip" ?disabled=${this.controlBusy} @change=${(e) => this.setMode(e.target.value)}>
              ${e.modes.map((t) => S`<option value=${t} ?selected=${t === e.mode}>${this.tr(`mode.${t}`)}</option>`)}
            </select>
          </label>` : S`<span class="chip">${this.tr(`mode.${e.mode}`)}</span>`}
      ${n ? S`<span class="livewrap">
            <button
              type="button"
              class=${e.live ? "chip live" : "chip"}
              title=${i}
              aria-pressed=${e.live ? "true" : "false"}
              aria-expanded=${this.confirmLive ? "true" : "false"}
              ?disabled=${this.controlBusy}
              @click=${() => e.live ? void this.setLive(!1) : this.confirmLive = !this.confirmLive}
            >
              ${r}
            </button>
            ${this.confirmLive && !e.live ? this.renderConfirmLive(e) : w}
          </span>` : S`<span class=${e.live ? "chip live" : "chip"} title=${i}>${r}</span>`}`;
	}
	renderConfirmLive(e) {
		let t = e.blockers.length > 0;
		return S`<div class="popover" role="dialog" aria-label=${this.tr("control.live_title")}>
      <strong>${this.tr("control.live_title")}</strong>
      <p>${this.tr(t ? "control.live_blocked" : "control.live_text")}</p>
      ${t ? S`<ul>${e.blockers.map((e) => S`<li>${Et(e, this.uiLang)}</li>`)}</ul>` : w}
      <div class="row">
        <button type="button" class="ghost" @click=${() => this.confirmLive = !1}>${this.tr("control.cancel")}</button>
        <button type="button" class="primary" ?disabled=${t || this.controlBusy} @click=${() => void this.setLive(!0)}>
          ${this.tr("control.live_start")}
        </button>
      </div>
    </div>`;
	}
	renderFast(e) {
		if (!this.admin || !e.entities?.mode) return w;
		let t = wt(e.mode, e.modes, e.previous_mode), n = this.pendingMode !== null && this.pendingMode !== e.mode, r = t.find((e) => e.active);
		return S`<div class="fast" role="group" aria-label=${this.tr("control.fast")}>
      ${t.map((e) => S`<button
          type="button"
          class=${e.active ? "primary" : "ghost"}
          aria-pressed=${e.active ? "true" : "false"}
          ?disabled=${this.controlBusy || n}
          @click=${() => this.setMode(e.target)}
        >
          ${e.active ? this.tr("control.stop_fast", { mode: this.tr(`control.${e.mode}`) }) : this.tr(`control.${e.mode}`)}
        </button>`)}
      ${r ? S`<span class="fastnote">${this.tr(`control.running_${r.mode}`)} ${this.tr("control.back_to", { mode: this.tr(`mode.${r.target}`) })}</span>` : w}
      ${e.live ? w : S`<span class="fastnote">${this.tr("control.shadow_note")}</span>`}
    </div>`;
	}
	renderBanner() {
		if (this.controlError && this.status === "ok") return S`<div class="banner" role="alert">
        ${this.tr("control.failed", { error: this.controlError })}
        <button type="button" class="link" @click=${() => this.controlError = null}>${this.tr("control.close")}</button>
      </div>`;
		switch (this.status) {
			case "not_loaded": return S`<div class="banner" role="status">${this.tr("status.not_loaded")}</div>`;
			case "reloading": return S`<div class="banner info" role="status">${this.tr("status.reloading")}</div>`;
			case "disconnected": return S`<div class="banner" role="status">
          ${this.tr("status.disconnected", { time: this.now ? P(this.now.updated_at, this.locale, this.timeZone) : "–" })}
        </div>`;
			default: return w;
		}
	}
	renderView() {
		return this.view === "plan" ? this.renderPlan() : this.view === "sets" ? S`<zephyr-sets
        class=${this.status === "ok" ? "" : "stale"}
        .view=${this.setsView}
        .uiLang=${this.uiLang}
        .locale=${this.locale}
        .timeZone=${this.timeZone}
      ></zephyr-sets>` : this.view === "settings" ? S`<zephyr-settings
        class=${this.status === "ok" ? "" : "stale"}
        .view=${this.settingsView}
        .uiLang=${this.uiLang}
        .locale=${this.locale}
        .friendlyName=${(e) => this.hass?.states?.[e]?.attributes?.friendly_name}
        .states=${this.hass?.states}
        .save=${this.saveSettings}
      ></zephyr-settings>` : this.view === "savings" ? S`<zephyr-savings
        class=${this.status === "ok" ? "" : "stale"}
        .view=${this.savingsView}
        .uiLang=${this.uiLang}
        .locale=${this.locale}
        .timeZone=${this.timeZone}
        ?admin=${this.admin}
        .states=${this.hass?.states}
        .backfill=${this.backfillSavings}
      ></zephyr-savings>` : this.view === "diagnostics" ? S`<zephyr-diagnostics
        class=${this.status === "ok" ? "" : "stale"}
        .view=${this.eventsView}
        .uiLang=${this.uiLang}
        .locale=${this.locale}
        .timeZone=${this.timeZone}
        ?admin=${this.admin}
        .download=${this.downloadDiagnostics}
        .exportCosts=${this.exportCosts}
        .refresh=${() => void this.loadEvents()}
      ></zephyr-diagnostics>` : this.renderComing();
	}
	renderComing() {
		return S`<section class="card coming">${this.tr("status.coming")}</section>`;
	}
	renderPlan() {
		let e = this.now;
		if (!e) return S`<section class="cards" aria-busy="true">
        ${[
			0,
			1,
			2
		].map(() => S`<div class="card skeleton" aria-hidden="true"></div>`)}
      </section>`;
		let t = this.status === "ok" ? "" : "stale";
		return S`<section class="cards ${t}" aria-label=${this.tr("now.title")}>
        ${this.renderNow(e)} ${this.renderBattery(e)} ${this.renderNext(e)}
      </section>
      ${this.renderFast(e)} ${e.price_entity ? this.renderPlanParts(e, t) : w}`;
	}
	renderPlanParts(e, t) {
		let n = null;
		return e.mode === "dynamic_forecasting" ? e.live || (n = this.tr("plan.shadow_note")) : n = this.tr("plan.mode_note", { mode: this.tr(`mode.${e.mode}`) }), S`${n ? S`<div class="banner info" role="note">${n}</div>` : w}
      <zephyr-prices-plan
        class=${t}
        .view=${this.planView}
        .uiLang=${this.uiLang}
        .locale=${this.locale}
        .timeZone=${this.timeZone}
        ?narrow=${this.narrow}
        .period=${this.period}
        @zephyr-period=${(e) => this.period = e.detail}
      ></zephyr-prices-plan>
      ${this.planView ? S`<section class="duo ${t}">${this.renderBlocks(this.planView)} ${this.renderWhy(this.planView)}</section>` : w}`;
	}
	range(e) {
		let t = P(e.start, this.locale, this.timeZone), n = P(e.end, this.locale, this.timeZone), r = `${this.tr("blocks.tomorrow")} `, i = I(e.start, this.clockMs, this.timeZone), a = I(new Date(e.end).getTime() - 1, this.clockMs, this.timeZone);
		return `${i ? "" : r}${t}–${i && !a ? r : ""}${n}`;
	}
	shownBlocks(e) {
		let t = Qe(e.quarters, this.timeZone)[1] ?? null;
		return st(e.blocks, this.period, new Date(this.clockMs).toISOString(), t, this.timeZone);
	}
	renderBlocks(e) {
		let t = this.shownBlocks(e).slice(0, 12);
		return S`<article class="card">
      <h2>${this.tr(`blocks.title_${this.period}`)}</h2>
      ${t.length ? S`<ul class="blocks">
            ${t.map((e) => S`<li>
                <span class="when">${this.range(e)}</span>
                <span class="swatch" style="background:${H(e.action)}"></span>
                <span class="what"
                  >${this.tr(`blocks.what_${e.action}`)}${e.indicative ? S` <em>(${this.tr("blocks.indicative")})</em>` : w}</span
                >
                <span class="detail">${this.tr(`blocks.${e.action}`, {
			kwh: M(e.kwh, this.locale),
			price: j(e.price, this.locale)
		})}</span>
              </li>`)}
          </ul>` : S`<p class="text">${this.tr(this.period === "tomorrow" ? "blocks.none_tomorrow" : "blocks.none")}</p>`}
    </article>`;
	}
	renderWhy(e) {
		let t = [];
		e.reason && this.period !== "tomorrow" && t.push(e.reason[this.uiLang]);
		let n = this.shownBlocks(e).filter((e) => !e.indicative), r = n.filter((e) => e.action === "charge").sort((e, t) => e.price - t.price)[0];
		r ? t.push(this.tr("why.cheapest", {
			time: this.range(r),
			price: j(r.price, this.locale)
		})) : n.length && t.push(this.tr("why.no_charge"));
		let i = $e(e.quarters, this.period, this.timeZone).filter((e) => !e.past), a = B(i)?.max;
		if (a && a.action === "deliver") {
			let e = `${I(a.start, this.clockMs, this.timeZone) ? "" : `${this.tr("blocks.tomorrow")} `}${P(a.start, this.locale, this.timeZone)}`;
			t.push(this.tr("why.peak", {
				time: e,
				price: j(a.buy, this.locale)
			}));
		}
		return i.some((e) => e.indicative) && t.push(this.tr("why.indicative")), S`<article class="card">
      <h2>${this.tr(`why.title_${this.period}`)}</h2>
      <ul class="why">
        ${t.map((e) => S`<li>${e}</li>`)}
      </ul>
    </article>`;
	}
	renderNow(e) {
		let t = e.action ?? "standby", n = e.battery_w !== null && Math.abs(e.battery_w) >= 10 ? ` · ${We(e.battery_w, this.locale)}` : "";
		return S`<article class="card">
      <div class="label"><span class="dot" style="background:${H(t)}"></span>${this.tr("now.title")}</div>
      <div class="big">${e.action ? this.tr(`action.${t}`) + n : this.tr("now.waiting")}</div>
      ${e.reason ? S`<p class="text">${e.reason[this.uiLang]}</p>` : w} ${this.renderAirco(e)}
      <div class="foot">
        ${e.grid_w === null ? w : S`<span>${this.tr("now.grid", { value: Ge(e.grid_w, this.locale) })}</span>`}
        ${e.live ? w : S`<span>${this.tr("now.shadow_note")}</span>`}
      </div>
    </article>`;
	}
	renderAirco(e) {
		let t = Ze(e.excluded, this.uiLang, this.locale);
		if (!t) return w;
		let n = t.icon === "heat" ? we`<path d="M12 3c1 3 4 4.5 4 8.5a4 4 0 0 1-8 0c0-2 1-3 2-4 0 2 1 3 2 3 0-3-1-5 0-7.5Z"/>` : t.icon === "cool" ? we`<path d="M12 3v18M4.2 7.5l15.6 9M4.2 16.5l15.6-9M9.5 4.5 12 7l2.5-2.5M9.5 19.5 12 17l2.5 2.5"/>` : w;
		return S`<p class=${t.allowed ? "airco allowed" : "airco"}>
      ${t.icon ? S`<svg viewBox="0 0 24 24" aria-hidden="true">${n}</svg>` : w}
      <span
        >${t.text}${t.estimate ? S` <span class="estimate" tabindex="0" title=${t.estimate} aria-label=${`${this.tr("airco.estimate")}: ${t.estimate}`}
                >${this.tr("airco.estimate")}</span
              >` : w}</span
      >
    </p>`;
	}
	renderBattery(e) {
		if (e.soc === null) return S`<article class="card">
        <div class="label">${this.tr("battery.title")}</div>
        <p class="text">${this.tr("battery.unknown")}</p>
      </article>`;
		let t = Math.max(0, Math.min(100, e.soc)), n = Math.max(0, e.buffer_pct), r = e.sets_total <= 1 ? e.sets_online >= 1 ? this.tr("battery.set") : this.tr("battery.set_offline") : this.tr("battery.sets", {
			online: e.sets_online,
			total: e.sets_total
		});
		return S`<article class="card">
      <div class="label">${this.tr("battery.title")}</div>
      <div class="big-row">
        <span class="big">${N(t, this.locale)}</span>
        ${e.energy_kwh !== null && e.capacity_kwh !== null ? S`<span class="muted"
              >${this.tr("battery.of", {
			energy: M(e.energy_kwh, this.locale),
			capacity: M(e.capacity_kwh, this.locale)
		})}</span
            >` : w}
      </div>
      <div
        class="bar"
        role="meter"
        aria-valuemin="0"
        aria-valuemax="100"
        aria-valuenow=${Math.round(t)}
        aria-label=${this.tr("battery.title")}
      >
        <div class="fill" style="width:${t}%"></div>
        ${n > 0 ? S`<div class="buffer" style="left:${e.min_soc}%;width:${Math.min(n, 100 - e.min_soc)}%"></div>` : w}
        <div class="mark" style="left:${e.min_soc}%"></div>
        <div class="mark" style="left:${e.max_soc}%"></div>
      </div>
      <div class="foot">
        <span
          >${this.tr("battery.limits", {
			min: Math.round(e.min_soc),
			max: Math.round(e.max_soc)
		})}${n > 0 ? ` · ${this.tr("battery.buffer", { value: Math.round(n) })}` : ""}</span
        >
        <span>${r}</span>
      </div>
    </article>`;
	}
	renderNext(e) {
		let t = e.plan, n = (e = "") => S`<div class="label">
        <span class="dot" style="background:${H(t?.next?.action)}"></span>${this.tr("next.title")}${e}
      </div>`;
		if (!e.price_entity) return S`<article class="card">${n()}<p class="text">${this.tr("next.no_price_source")}</p></article>`;
		if (!t) return S`<article class="card">${n()}<p class="text">${this.tr("status.loading")}</p></article>`;
		if (t.state === "no_prices") {
			let e = t.no_prices_since ?? t.calculated_at;
			return S`<article class="card">
        ${n()}
        <p class="text warn">${this.tr("next.no_prices", { time: e ? P(e, this.locale, this.timeZone) : "–" })}</p>
      </article>`;
		}
		let r = t.next, i = t.price_now ? S`<div class="foot"><span>${this.tr("next.price_now", { price: j(t.price_now.import, this.locale) })}</span></div>` : w;
		if (!r) return S`<article class="card">${n()}<p class="text">${this.tr("next.none")}</p>${i}</article>`;
		let a = Ke(r.start, this.clockMs), o = a <= 0 ? this.tr("next.now") : this.tr("next.in", { time: a >= 60 ? this.tr("next.hours", {
			h: Math.floor(a / 60),
			m: a % 60
		}) : this.tr("next.minutes", { m: a }) }), s = P(r.start, this.locale, this.timeZone), c = this.tr(`action.${r.action}`), l = I(r.start, this.clockMs, this.timeZone) ? this.tr("next.at", {
			time: s,
			action: c
		}) : this.tr("next.tomorrow", {
			time: s,
			action: c
		});
		return S`<article class="card">
      ${n(` · ${o}`)}
      <div class="big">${l}</div>
      <p class="text">${this.detail(t)}</p>
      ${r.indicative ? S`<p class="text muted">${this.tr("next.indicative")}</p>` : w} ${i}
    </article>`;
	}
	detail(e) {
		let t = e.next;
		if (!t) return "";
		let n = {
			kwh: M(t.kwh, this.locale),
			price: j(t.price, this.locale)
		};
		return this.tr(`next.${t.action}`, n);
	}
	static {
		this.styles = [ut, o`
      :host {
        display: block;
        min-height: 100%;
        background: var(--z-bg);
        color: var(--z-text);
        font-family: var(--z-font);
        -webkit-font-smoothing: antialiased;
      }
      .page {
        min-height: 100vh;
        display: flex;
        flex-direction: column;
      }
      header {
        display: flex;
        flex-wrap: wrap;
        align-items: center;
        gap: 12px 28px;
        padding: 12px 32px;
        background: var(--z-card);
        border-bottom: 1px solid var(--z-border);
      }
      .brand {
        display: flex;
        align-items: center;
        gap: 10px;
        font-family: var(--z-font-head);
        font-weight: 700;
        font-size: 22px;
        letter-spacing: 0.12em;
      }
      .brand img {
        display: block;
        width: 32px;
        height: 32px;
      }
      nav {
        display: flex;
        flex-wrap: wrap;
        gap: 4px;
        flex: 1 1 auto;
      }
      .tab {
        min-height: 44px;
        padding: 0 16px;
        border: 0;
        border-radius: 999px;
        background: transparent;
        color: var(--z-text);
        font: inherit;
        font-size: 14px;
        cursor: pointer;
      }
      .tab:hover {
        background: var(--z-track);
      }
      .tab.active {
        background: var(--z-text);
        color: var(--z-on-text);
        font-weight: 600;
      }
      .tab:focus-visible {
        outline: 2px solid var(--z-charge);
        outline-offset: 2px;
      }
      .meta {
        display: flex;
        flex-wrap: wrap;
        align-items: center;
        gap: 8px 12px;
        font-size: 14px;
        color: var(--z-muted);
      }
      .chip {
        padding: 6px 12px;
        border-radius: 999px;
        border: 1px solid var(--z-border);
        color: var(--z-text);
      }
      .chip.live {
        background: var(--z-text);
        color: var(--z-on-text);
        border-color: var(--z-text);
      }
      button.chip,
      select.chip {
        font: inherit;
        font-size: inherit;
        background: var(--z-card);
        min-height: 36px;
        cursor: pointer;
      }
      button.chip.live {
        background: var(--z-text);
      }
      select.chip {
        padding-right: 28px;
      }
      .sr {
        position: absolute;
        width: 1px;
        height: 1px;
        overflow: hidden;
        clip: rect(0 0 0 0);
      }
      .livewrap {
        position: relative;
      }
      .popover {
        position: absolute;
        right: 0;
        top: calc(100% + 8px);
        z-index: 5;
        width: min(320px, 85vw);
        box-sizing: border-box;
        padding: 14px 16px;
        border-radius: 12px;
        background: var(--z-card);
        border: 1px solid var(--z-border);
        box-shadow: 0 6px 24px rgba(0, 0, 0, 0.18);
        font-size: 14px;
        line-height: 1.5;
        text-align: left;
      }
      .popover p {
        margin: 6px 0;
        color: var(--z-muted);
      }
      .popover ul {
        margin: 0 0 6px;
        padding-left: 18px;
        color: var(--z-warn-text);
      }
      .popover .row,
      .fast {
        display: flex;
        flex-wrap: wrap;
        gap: 8px;
        align-items: center;
      }
      .popover .row {
        justify-content: flex-end;
        margin-top: 8px;
      }
      .popover button,
      .fast button {
        min-height: 44px;
        padding: 0 16px;
        border-radius: 10px;
        font: inherit;
        font-size: 14px;
        font-weight: 600;
        cursor: pointer;
      }
      .ghost {
        border: 1px solid var(--z-border);
        background: var(--z-card);
        color: var(--z-text);
      }
      .primary {
        border: 0;
        background: var(--z-text);
        color: var(--z-on-text);
      }
      .fastnote {
        font-size: 13px;
        color: var(--z-muted);
      }
      .banner .link {
        margin-left: 8px;
        border: 0;
        background: none;
        color: inherit;
        font: inherit;
        font-weight: 600;
        text-decoration: underline;
        cursor: pointer;
      }
      :disabled {
        opacity: 0.6;
        cursor: not-allowed;
      }
      .time {
        font-variant-numeric: tabular-nums;
      }
      main {
        flex: 1;
        width: 100%;
        max-width: 1376px;
        margin: 0 auto;
        box-sizing: border-box;
        padding: 24px 32px 40px;
        display: flex;
        flex-direction: column;
        gap: 20px;
      }
      .banner {
        padding: 12px 16px;
        border-radius: 12px;
        background: var(--z-warn-bg);
        color: var(--z-warn-text);
        font-size: 14px;
        line-height: 1.5;
      }
      .banner.info {
        background: var(--z-info-bg);
        color: var(--z-text);
      }
      .cards {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
        gap: 16px;
      }
      .cards.stale,
      .duo.stale,
      zephyr-prices-plan.stale,
      zephyr-sets.stale,
      zephyr-settings.stale {
        opacity: 0.6;
      }
      .duo {
        display: flex;
        flex-wrap: wrap;
        gap: 16px;
      }
      .duo > .card {
        flex: 1 1 420px;
      }
      h2 {
        margin: 0;
        font-family: var(--z-font-head);
        font-size: 20px;
      }
      .blocks,
      .why {
        margin: 0;
        padding: 0;
        list-style: none;
        font-size: 14px;
        line-height: 1.5;
      }
      .blocks li {
        display: grid;
        grid-template-columns: minmax(110px, auto) 4px 1fr auto;
        align-items: center;
        gap: 12px;
        padding: 10px 0;
        border-top: 1px solid var(--z-border);
      }
      .blocks .when {
        font-weight: 600;
        font-variant-numeric: tabular-nums;
        white-space: nowrap;
      }
      .blocks .swatch {
        width: 4px;
        height: 24px;
        border-radius: 2px;
      }
      @media (max-width: 700px) {
        .blocks li {
          grid-template-columns: 4px 1fr auto;
          grid-template-areas: "sw when when" "sw what detail";
          gap: 2px 12px;
        }
        .blocks .when {
          grid-area: when;
        }
        .blocks .swatch {
          grid-area: sw;
          height: 100%;
        }
        .blocks .what {
          grid-area: what;
        }
        .blocks .detail {
          grid-area: detail;
        }
      }
      .blocks .detail {
        color: var(--z-muted);
        font-variant-numeric: tabular-nums;
        text-align: right;
      }
      .blocks em {
        color: var(--z-muted);
        font-style: normal;
      }
      .why {
        display: flex;
        flex-direction: column;
        gap: 10px;
      }
      .why li {
        padding-left: 18px;
        position: relative;
      }
      .why li::before {
        content: "";
        position: absolute;
        left: 4px;
        top: 0.6em;
        width: 6px;
        height: 6px;
        border-radius: 50%;
        background: var(--z-muted);
      }
      .card {
        background: var(--z-card);
        border: 1px solid var(--z-border);
        border-radius: 16px;
        padding: 20px;
        display: flex;
        flex-direction: column;
        gap: 10px;
        min-width: 0;
      }
      .skeleton {
        min-height: 150px;
        background: linear-gradient(90deg, var(--z-card), var(--z-track), var(--z-card));
        background-size: 200% 100%;
        animation: shimmer 1.4s linear infinite;
      }
      @keyframes shimmer {
        to {
          background-position: -200% 0;
        }
      }
      @media (prefers-reduced-motion: reduce) {
        .skeleton {
          animation: none;
        }
      }
      .coming {
        color: var(--z-muted);
        font-size: 15px;
      }
      .label {
        display: flex;
        align-items: center;
        gap: 8px;
        font-size: 12px;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        color: var(--z-muted);
      }
      .dot {
        width: 10px;
        height: 10px;
        border-radius: 50%;
        flex: none;
      }
      .big {
        font-family: var(--z-font-head);
        font-size: 26px;
        font-weight: 700;
        font-variant-numeric: tabular-nums;
      }
      .big-row {
        display: flex;
        flex-wrap: wrap;
        align-items: baseline;
        gap: 4px 10px;
      }
      .text {
        margin: 0;
        font-size: 14px;
        line-height: 1.5;
        color: var(--z-muted);
      }
      .airco {
        margin: 0;
        display: flex;
        align-items: flex-start;
        gap: 8px;
        line-height: 1.5;
        font-size: 14px;
        font-weight: 600;
        color: var(--z-text);
      }
      .airco.allowed {
        font-weight: 400;
        color: var(--z-muted);
      }
      .airco svg {
        width: 18px;
        height: 18px;
        fill: none;
        stroke: currentColor;
        stroke-width: 1.8;
        stroke-linecap: round;
        stroke-linejoin: round;
        flex: none;
        margin-top: 1px;
      }
      .estimate {
        white-space: nowrap;
        padding: 2px 8px;
        border-radius: 999px;
        background: var(--z-info-bg);
        font-size: 11px;
        font-weight: 600;
        cursor: help;
      }
      .text.warn {
        color: var(--z-warn-text);
        background: var(--z-warn-bg);
        padding: 10px 12px;
        border-radius: 10px;
      }
      .muted {
        font-size: 14px;
        color: var(--z-muted);
      }
      .foot {
        margin-top: auto;
        display: flex;
        flex-wrap: wrap;
        justify-content: space-between;
        gap: 4px 12px;
        font-size: 13px;
        color: var(--z-muted);
        font-variant-numeric: tabular-nums;
      }
      .bar {
        position: relative;
        height: 12px;
        background: var(--z-track);
        border-radius: 6px;
        overflow: hidden;
      }
      .fill {
        height: 100%;
        background: var(--z-text);
        border-radius: 6px;
      }
      .buffer {
        position: absolute;
        top: 0;
        bottom: 0;
        background: repeating-linear-gradient(45deg, var(--z-hold-a) 0 3px, transparent 3px 6px);
        opacity: 0.8;
      }
      .mark {
        position: absolute;
        top: 0;
        bottom: 0;
        border-left: 2px solid var(--z-card);
      }
      @media (max-width: 700px) {
        header {
          padding: 10px 16px;
        }
        main {
          padding: 16px;
        }
      }
    `];
	}
};
U([k({ attribute: !1 })], $.prototype, "hass", void 0), U([k({ type: Boolean })], $.prototype, "narrow", void 0), U([k({ attribute: !1 })], $.prototype, "panel", void 0), U([A()], $.prototype, "now", void 0), U([A()], $.prototype, "status", void 0), U([A()], $.prototype, "view", void 0), U([A()], $.prototype, "clockMs", void 0), U([A()], $.prototype, "planView", void 0), U([A()], $.prototype, "setsView", void 0), U([A()], $.prototype, "settingsView", void 0), U([A()], $.prototype, "period", void 0), U([A()], $.prototype, "eventsView", void 0), U([A()], $.prototype, "savingsView", void 0), U([A()], $.prototype, "confirmLive", void 0), U([A()], $.prototype, "controlBusy", void 0), U([A()], $.prototype, "controlError", void 0), U([A()], $.prototype, "pendingMode", void 0), $ = U([O("zephyr-panel")], $);
export { $ as ZephyrPanel };
