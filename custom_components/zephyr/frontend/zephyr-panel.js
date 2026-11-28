// src/define.ts
function e(e) {
	return (t) => (customElements.get(e) || customElements.define(e, t), t);
}
// node_modules/@lit/reactive-element/css-tag.js
var t = globalThis, n = t.ShadowRoot && (t.ShadyCSS === void 0 || t.ShadyCSS.nativeShadow) && "adoptedStyleSheets" in Document.prototype && "replace" in CSSStyleSheet.prototype, r = Symbol(), i = /* @__PURE__ */ new WeakMap(), a = class {
	constructor(e, t, n) {
		if (this._$cssResult$ = !0, n !== r) throw Error("CSSResult is not constructable. Use `unsafeCSS` or `css` instead.");
		this.cssText = e, this.t = t;
	}
	get styleSheet() {
		let e = this.o, t = this.t;
		if (n && e === void 0) {
			let n = t !== void 0 && t.length === 1;
			n && (e = i.get(t)), e === void 0 && ((this.o = e = new CSSStyleSheet()).replaceSync(this.cssText), n && i.set(t, e));
		}
		return e;
	}
	toString() {
		return this.cssText;
	}
}, o = (e) => new a(typeof e == "string" ? e : e + "", void 0, r), s = (e, ...t) => new a(e.length === 1 ? e[0] : t.reduce((t, n, r) => t + ((e) => {
	if (!0 === e._$cssResult$) return e.cssText;
	if (typeof e == "number") return e;
	throw Error("Value passed to 'css' function must be a 'css' function result: " + e + ". Use 'unsafeCSS' to pass non-literal values, but take care to ensure page security.");
})(n) + e[r + 1], e[0]), e, r), c = (e, r) => {
	if (n) e.adoptedStyleSheets = r.map((e) => e instanceof CSSStyleSheet ? e : e.styleSheet);
	else for (let n of r) {
		let r = document.createElement("style"), i = t.litNonce;
		i !== void 0 && r.setAttribute("nonce", i), r.textContent = n.cssText, e.appendChild(r);
	}
}, l = n ? (e) => e : (e) => e instanceof CSSStyleSheet ? ((e) => {
	let t = "";
	for (let n of e.cssRules) t += n.cssText;
	return o(t);
})(e) : e, { is: u, defineProperty: d, getOwnPropertyDescriptor: f, getOwnPropertyNames: p, getOwnPropertySymbols: m, getPrototypeOf: ee } = Object, h = globalThis, te = h.trustedTypes, ne = te ? te.emptyScript : "", g = h.reactiveElementPolyfillSupport, _ = (e, t) => e, re = {
	toAttribute(e, t) {
		switch (t) {
			case Boolean:
				e = e ? ne : null;
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
}, ie = (e, t) => !u(e, t), ae = {
	attribute: !0,
	type: String,
	converter: re,
	reflect: !1,
	useDefault: !1,
	hasChanged: ie
};
Symbol.metadata ??= Symbol("metadata"), h.litPropertyMetadata ??= /* @__PURE__ */ new WeakMap();
var oe = class extends HTMLElement {
	static addInitializer(e) {
		this._$Ei(), (this.l ??= []).push(e);
	}
	static get observedAttributes() {
		return this.finalize(), this._$Eh && [...this._$Eh.keys()];
	}
	static createProperty(e, t = ae) {
		if (t.state && (t.attribute = !1), this._$Ei(), this.prototype.hasOwnProperty(e) && ((t = Object.create(t)).wrapped = !0), this.elementProperties.set(e, t), !t.noAccessor) {
			let n = Symbol(), r = this.getPropertyDescriptor(e, n, t);
			r !== void 0 && d(this.prototype, e, r);
		}
	}
	static getPropertyDescriptor(e, t, n) {
		let { get: r, set: i } = f(this.prototype, e) ?? {
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
		return this.elementProperties.get(e) ?? ae;
	}
	static _$Ei() {
		if (this.hasOwnProperty(_("elementProperties"))) return;
		let e = ee(this);
		e.finalize(), e.l !== void 0 && (this.l = [...e.l]), this.elementProperties = new Map(e.elementProperties);
	}
	static finalize() {
		if (this.hasOwnProperty(_("finalized"))) return;
		if (this.finalized = !0, this._$Ei(), this.hasOwnProperty(_("properties"))) {
			let e = this.properties, t = [...p(e), ...m(e)];
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
			for (let e of n) t.unshift(l(e));
		} else e !== void 0 && t.push(l(e));
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
		return c(e, this.constructor.elementStyles), e;
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
			let i = (n.converter?.toAttribute === void 0 ? re : n.converter).toAttribute(t, n.type);
			this._$Em = e, i == null ? this.removeAttribute(r) : this.setAttribute(r, i), this._$Em = null;
		}
	}
	_$AK(e, t) {
		let n = this.constructor, r = n._$Eh.get(e);
		if (r !== void 0 && this._$Em !== r) {
			let e = n.getPropertyOptions(r), i = typeof e.converter == "function" ? { fromAttribute: e.converter } : e.converter?.fromAttribute === void 0 ? re : e.converter;
			this._$Em = r;
			let a = i.fromAttribute(t, e.type);
			this[r] = a ?? this._$Ej?.get(r) ?? a, this._$Em = null;
		}
	}
	requestUpdate(e, t, n, r = !1, i) {
		if (e !== void 0) {
			let a = this.constructor;
			if (!1 === r && (i = this[e]), n ??= a.getPropertyOptions(e), !((n.hasChanged ?? ie)(i, t) || n.useDefault && n.reflect && i === this._$Ej?.get(e) && !this.hasAttribute(a._$Eu(e, n)))) return;
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
oe.elementStyles = [], oe.shadowRootOptions = { mode: "open" }, oe[_("elementProperties")] = /* @__PURE__ */ new Map(), oe[_("finalized")] = /* @__PURE__ */ new Map(), g?.({ ReactiveElement: oe }), (h.reactiveElementVersions ??= []).push("2.1.2");
// node_modules/lit-html/lit-html.js
var se = globalThis, ce = (e) => e, le = se.trustedTypes, ue = le ? le.createPolicy("lit-html", { createHTML: (e) => e }) : void 0, de = "$lit$", v = `lit$${Math.random().toFixed(9).slice(2)}$`, fe = "?" + v, pe = `<${fe}>`, me = document, he = () => me.createComment(""), ge = (e) => e === null || typeof e != "object" && typeof e != "function", _e = Array.isArray, ve = (e) => _e(e) || typeof e?.[Symbol.iterator] == "function", ye = "[ 	\n\f\r]", be = /<(?:(!--|\/[^a-zA-Z])|(\/?[a-zA-Z][^>\s]*)|(\/?$))/g, xe = /-->/g, Se = />/g, y = RegExp(`>|${ye}(?:([^\\s"'>=/]+)(${ye}*=${ye}*(?:[^ \t\n\f\r"'\`<>=]|("|')|))|$)`, "g"), Ce = /'/g, we = /"/g, Te = /^(?:script|style|textarea|title)$/i, Ee = (e) => (t, ...n) => ({
	_$litType$: e,
	strings: t,
	values: n
}), b = Ee(1), x = Ee(2), S = Symbol.for("lit-noChange"), C = Symbol.for("lit-nothing"), De = /* @__PURE__ */ new WeakMap(), w = me.createTreeWalker(me, 129);
function Oe(e, t) {
	if (!_e(e) || !e.hasOwnProperty("raw")) throw Error("invalid template strings array");
	return ue === void 0 ? t : ue.createHTML(t);
}
var ke = (e, t) => {
	let n = e.length - 1, r = [], i, a = t === 2 ? "<svg>" : t === 3 ? "<math>" : "", o = be;
	for (let t = 0; t < n; t++) {
		let n = e[t], s, c, l = -1, u = 0;
		for (; u < n.length && (o.lastIndex = u, c = o.exec(n), c !== null);) u = o.lastIndex, o === be ? c[1] === "!--" ? o = xe : c[1] === void 0 ? c[2] === void 0 ? c[3] !== void 0 && (o = y) : (Te.test(c[2]) && (i = RegExp("</" + c[2], "g")), o = y) : o = Se : o === y ? c[0] === ">" ? (o = i ?? be, l = -1) : c[1] === void 0 ? l = -2 : (l = o.lastIndex - c[2].length, s = c[1], o = c[3] === void 0 ? y : c[3] === "\"" ? we : Ce) : o === we || o === Ce ? o = y : o === xe || o === Se ? o = be : (o = y, i = void 0);
		let d = o === y && e[t + 1].startsWith("/>") ? " " : "";
		a += o === be ? n + pe : l >= 0 ? (r.push(s), n.slice(0, l) + de + n.slice(l) + v + d) : n + v + (l === -2 ? t : d);
	}
	return [Oe(e, a + (e[n] || "<?>") + (t === 2 ? "</svg>" : t === 3 ? "</math>" : "")), r];
}, Ae = class e {
	constructor({ strings: t, _$litType$: n }, r) {
		let i;
		this.parts = [];
		let a = 0, o = 0, s = t.length - 1, c = this.parts, [l, u] = ke(t, n);
		if (this.el = e.createElement(l, r), w.currentNode = this.el.content, n === 2 || n === 3) {
			let e = this.el.content.firstChild;
			e.replaceWith(...e.childNodes);
		}
		for (; (i = w.nextNode()) !== null && c.length < s;) {
			if (i.nodeType === 1) {
				if (i.hasAttributes()) for (let e of i.getAttributeNames()) if (e.endsWith(de)) {
					let t = u[o++], n = i.getAttribute(e).split(v), r = /([.?@])?(.*)/.exec(t);
					c.push({
						type: 1,
						index: a,
						name: r[2],
						strings: n,
						ctor: r[1] === "." ? Fe : r[1] === "?" ? Ie : r[1] === "@" ? Le : Pe
					}), i.removeAttribute(e);
				} else e.startsWith(v) && (c.push({
					type: 6,
					index: a
				}), i.removeAttribute(e));
				if (Te.test(i.tagName)) {
					let e = i.textContent.split(v), t = e.length - 1;
					if (t > 0) {
						i.textContent = le ? le.emptyScript : "";
						for (let n = 0; n < t; n++) i.append(e[n], he()), w.nextNode(), c.push({
							type: 2,
							index: ++a
						});
						i.append(e[t], he());
					}
				}
			} else if (i.nodeType === 8) {
				if (i.data === fe) c.push({
					type: 2,
					index: a
				});
				else {
					let e = -1;
					for (; (e = i.data.indexOf(v, e + 1)) !== -1;) c.push({
						type: 7,
						index: a
					}), e += v.length - 1;
				}
			}
			a++;
		}
	}
	static createElement(e, t) {
		let n = me.createElement("template");
		return n.innerHTML = e, n;
	}
};
function je(e, t, n = e, r) {
	if (t === S) return t;
	let i = r === void 0 ? n._$Cl : n._$Co?.[r], a = ge(t) ? void 0 : t._$litDirective$;
	return i?.constructor !== a && (i?._$AO?.(!1), a === void 0 ? i = void 0 : (i = new a(e), i._$AT(e, n, r)), r === void 0 ? n._$Cl = i : (n._$Co ??= [])[r] = i), i !== void 0 && (t = je(e, i._$AS(e, t.values), i, r)), t;
}
var Me = class {
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
		let { el: { content: t }, parts: n } = this._$AD, r = (e?.creationScope ?? me).importNode(t, !0);
		w.currentNode = r;
		let i = w.nextNode(), a = 0, o = 0, s = n[0];
		for (; s !== void 0;) {
			if (a === s.index) {
				let t;
				s.type === 2 ? t = new Ne(i, i.nextSibling, this, e) : s.type === 1 ? t = new s.ctor(i, s.name, s.strings, this, e) : s.type === 6 && (t = new Re(i, this, e)), this._$AV.push(t), s = n[++o];
			}
			a !== s?.index && (i = w.nextNode(), a++);
		}
		return w.currentNode = me, r;
	}
	p(e) {
		let t = 0;
		for (let n of this._$AV) n !== void 0 && (n.strings === void 0 ? n._$AI(e[t]) : (n._$AI(e, n, t), t += n.strings.length - 2)), t++;
	}
}, Ne = class e {
	get _$AU() {
		return this._$AM?._$AU ?? this._$Cv;
	}
	constructor(e, t, n, r) {
		this.type = 2, this._$AH = C, this._$AN = void 0, this._$AA = e, this._$AB = t, this._$AM = n, this.options = r, this._$Cv = r?.isConnected ?? !0;
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
		e = je(this, e, t), ge(e) ? e === C || e == null || e === "" ? (this._$AH !== C && this._$AR(), this._$AH = C) : e !== this._$AH && e !== S && this._(e) : e._$litType$ === void 0 ? e.nodeType === void 0 ? ve(e) ? this.k(e) : this._(e) : this.T(e) : this.$(e);
	}
	O(e) {
		return this._$AA.parentNode.insertBefore(e, this._$AB);
	}
	T(e) {
		this._$AH !== e && (this._$AR(), this._$AH = this.O(e));
	}
	_(e) {
		this._$AH !== C && ge(this._$AH) ? this._$AA.nextSibling.data = e : this.T(me.createTextNode(e)), this._$AH = e;
	}
	$(e) {
		let { values: t, _$litType$: n } = e, r = typeof n == "number" ? this._$AC(e) : (n.el === void 0 && (n.el = Ae.createElement(Oe(n.h, n.h[0]), this.options)), n);
		if (this._$AH?._$AD === r) this._$AH.p(t);
		else {
			let e = new Me(r, this), n = e.u(this.options);
			e.p(t), this.T(n), this._$AH = e;
		}
	}
	_$AC(e) {
		let t = De.get(e.strings);
		return t === void 0 && De.set(e.strings, t = new Ae(e)), t;
	}
	k(t) {
		_e(this._$AH) || (this._$AH = [], this._$AR());
		let n = this._$AH, r, i = 0;
		for (let a of t) i === n.length ? n.push(r = new e(this.O(he()), this.O(he()), this, this.options)) : r = n[i], r._$AI(a), i++;
		i < n.length && (this._$AR(r && r._$AB.nextSibling, i), n.length = i);
	}
	_$AR(e = this._$AA.nextSibling, t) {
		for (this._$AP?.(!1, !0, t); e !== this._$AB;) {
			let t = ce(e).nextSibling;
			ce(e).remove(), e = t;
		}
	}
	setConnected(e) {
		this._$AM === void 0 && (this._$Cv = e, this._$AP?.(e));
	}
}, Pe = class {
	get tagName() {
		return this.element.tagName;
	}
	get _$AU() {
		return this._$AM._$AU;
	}
	constructor(e, t, n, r, i) {
		this.type = 1, this._$AH = C, this._$AN = void 0, this.element = e, this.name = t, this._$AM = r, this.options = i, n.length > 2 || n[0] !== "" || n[1] !== "" ? (this._$AH = Array(n.length - 1).fill(/* @__PURE__ */ new String()), this.strings = n) : this._$AH = C;
	}
	_$AI(e, t = this, n, r) {
		let i = this.strings, a = !1;
		if (i === void 0) e = je(this, e, t, 0), a = !ge(e) || e !== this._$AH && e !== S, a && (this._$AH = e);
		else {
			let r = e, o, s;
			for (e = i[0], o = 0; o < i.length - 1; o++) s = je(this, r[n + o], t, o), s === S && (s = this._$AH[o]), a ||= !ge(s) || s !== this._$AH[o], s === C ? e = C : e !== C && (e += (s ?? "") + i[o + 1]), this._$AH[o] = s;
		}
		a && !r && this.j(e);
	}
	j(e) {
		e === C ? this.element.removeAttribute(this.name) : this.element.setAttribute(this.name, e ?? "");
	}
}, Fe = class extends Pe {
	constructor() {
		super(...arguments), this.type = 3;
	}
	j(e) {
		this.element[this.name] = e === C ? void 0 : e;
	}
}, Ie = class extends Pe {
	constructor() {
		super(...arguments), this.type = 4;
	}
	j(e) {
		this.element.toggleAttribute(this.name, !!e && e !== C);
	}
}, Le = class extends Pe {
	constructor(e, t, n, r, i) {
		super(e, t, n, r, i), this.type = 5;
	}
	_$AI(e, t = this) {
		if ((e = je(this, e, t, 0) ?? C) === S) return;
		let n = this._$AH, r = e === C && n !== C || e.capture !== n.capture || e.once !== n.once || e.passive !== n.passive, i = e !== C && (n === C || r);
		r && this.element.removeEventListener(this.name, this, n), i && this.element.addEventListener(this.name, this, e), this._$AH = e;
	}
	handleEvent(e) {
		typeof this._$AH == "function" ? this._$AH.call(this.options?.host ?? this.element, e) : this._$AH.handleEvent(e);
	}
}, Re = class {
	constructor(e, t, n) {
		this.element = e, this.type = 6, this._$AN = void 0, this._$AM = t, this.options = n;
	}
	get _$AU() {
		return this._$AM._$AU;
	}
	_$AI(e) {
		je(this, e);
	}
}, ze = se.litHtmlPolyfillSupport;
ze?.(Ae, Ne), (se.litHtmlVersions ??= []).push("3.3.3");
var Be = (e, t, n) => {
	let r = n?.renderBefore ?? t, i = r._$litPart$;
	if (i === void 0) {
		let e = n?.renderBefore ?? null;
		r._$litPart$ = i = new Ne(t.insertBefore(he(), e), e, void 0, n ?? {});
	}
	return i._$AI(e), i;
}, Ve = globalThis, T = class extends oe {
	constructor() {
		super(...arguments), this.renderOptions = { host: this }, this._$Do = void 0;
	}
	createRenderRoot() {
		let e = super.createRenderRoot();
		return this.renderOptions.renderBefore ??= e.firstChild, e;
	}
	update(e) {
		let t = this.render();
		this.hasUpdated || (this.renderOptions.isConnected = this.isConnected), super.update(e), this._$Do = Be(t, this.renderRoot, this.renderOptions);
	}
	connectedCallback() {
		super.connectedCallback(), this._$Do?.setConnected(!0);
	}
	disconnectedCallback() {
		super.disconnectedCallback(), this._$Do?.setConnected(!1);
	}
	render() {
		return S;
	}
};
T._$litElement$ = !0, T.finalized = !0, Ve.litElementHydrateSupport?.({ LitElement: T });
var He = Ve.litElementPolyfillSupport;
He?.({ LitElement: T }), (Ve.litElementVersions ??= []).push("4.2.2");
// node_modules/@lit/reactive-element/decorators/property.js
var Ue = {
	attribute: !0,
	type: String,
	converter: re,
	reflect: !1,
	hasChanged: ie
}, We = (e = Ue, t, n) => {
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
function E(e) {
	return (t, n) => typeof n == "object" ? We(e, t, n) : ((e, t, n) => {
		let r = t.hasOwnProperty(n);
		return t.constructor.createProperty(n, e), r ? Object.getOwnPropertyDescriptor(t, n) : void 0;
	})(e, t, n);
}
// node_modules/@lit/reactive-element/decorators/state.js
function D(e) {
	return E({
		...e,
		state: !0,
		attribute: !1
	});
}
// src/format.ts
var Ge = "−", Ke = /* @__PURE__ */ new Map(), qe = /* @__PURE__ */ new Map();
function Je(e, t) {
	let n = `${e}|${JSON.stringify(t)}`, r = Ke.get(n);
	return r || (r = new Intl.DateTimeFormat(e, t), Ke.set(n, r)), r;
}
function Ye(e, t) {
	let n = `${e}|${JSON.stringify(t)}`, r = qe.get(n);
	return r || (r = new Intl.NumberFormat(e, t), qe.set(n, r)), r;
}
function Xe(e, t, n) {
	return Ye(t, {
		minimumFractionDigits: n,
		maximumFractionDigits: n
	}).format(e);
}
function O(e, t) {
	let n = Ye(t, {
		style: "currency",
		currency: "EUR",
		minimumFractionDigits: 2,
		maximumFractionDigits: 2
	}).format(Math.abs(e));
	return e < 0 ? Ge + n : n;
}
function k(e, t) {
	let n = Math.abs(e);
	return n >= 1e3 ? `${Xe(n / 1e3, t, 2)} kW` : `${Xe(Math.round(n / 10) * 10, t, 0)} W`;
}
function Ze(e, t) {
	return (e > 0 ? "+" : e < 0 ? Ge : "") + k(e, t);
}
function A(e, t, n = 1) {
	return `${Xe(e, t, n)} kWh`;
}
function j(e, t) {
	return `${Xe(Math.round(e), t, 0)} %`;
}
function M(e, t, n) {
	return Je(t, {
		hour: "2-digit",
		minute: "2-digit",
		hour12: !1,
		timeZone: n
	}).format(new Date(e));
}
function N(e, t, n) {
	return Je(t, {
		weekday: "short",
		day: "numeric",
		month: "short",
		timeZone: n
	}).format(new Date(e));
}
function Qe(e, t) {
	return Math.max(0, Math.round((new Date(e).getTime() - t) / 6e4));
}
function P(e, t, n) {
	let r = Je("en-CA", {
		year: "numeric",
		month: "2-digit",
		day: "2-digit",
		timeZone: n
	});
	return r.format(new Date(e)) === r.format(new Date(t));
}
// src/i18n.ts
var $e = {
	nl: {
		menu: {
			label: "Hoofdmenu",
			plan: "Plan",
			sets: "Sets",
			battery: "Accu",
			settings: "Instellingen",
			diagnostics: "Diagnose",
			savings: "Besparing",
			stroom: "Stroom"
		},
		header: {
			live: "Actief",
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
			shadow_note: "Zo zou ZEPHYR het doen (schaduwmodus).",
			p1_import: "P1 · afname",
			p1_export: "P1 · teruglevering",
			p1_zero: "P1"
		},
		battery: {
			title: "Accu",
			of: "{energy} van {capacity}",
			limits: "Grenzen {min}–{max} %",
			buffer: "buffer {value} %",
			sets: "{online} van {total} sets online",
			set: "1 set",
			set_offline: "set offline",
			unknown: "Nog geen gegevens van de set",
			rte: "RTE {value}",
			rte_title: "Round-trip efficiency: geleverd ÷ geladen, met de verandering in SoC verrekend, over de laatste 7 dagen (of minder als het kostenlogboek korter loopt). Zelfde als op het scherm Accu."
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
			spread_title: "Hoeveel duurder het duurste kwartier is dan het gemiddelde van de dag. Ruwe maat voor wat leveren op de duurste momenten oplevert, vóór verlies (± 14 %) en slijtage. Bij een gemiddelde rond nul of negatief: het verschil in euro.",
			tip_appliances: "Apparaten: {kwh}",
			runs_label: "Geplande apparaten",
			curtail_mark: "Zonoverschot wordt afgeknepen",
			tip_curtail: "Terugleverprijs {price}: zonoverschot {kwh} wordt afgeknepen",
			tip_export_cost: "Teruglevering kost {euro} (geen afknijpen ingesteld)",
			neg_today: "Vandaag {hours} uur negatieve terugleverprijs. Afknijpen staat uit; dat kost naar verwachting {euro}.",
			neg_tomorrow: "Morgen {hours} uur negatieve terugleverprijs. Afknijpen staat uit; dat kost naar verwachting {euro}.",
			neg_both: "Vandaag en morgen {hours} uur negatieve terugleverprijs. Afknijpen staat uit; dat kost naar verwachting {euro}.",
			neg_link: "Instelling aanpassen →",
			legend_negative: "Negatieve terugleverprijs",
			fc_peak: "(verwacht {when}: {price}, kans 80 %: {low}–{high})",
			fc_would: "Met de verwachting zou ZEPHYR nu {action}.",
			fc_used: "Het plan rekent met de prijsverwachting.",
			fc_day: "Verwachting {day}: gemiddeld {avg}, duurst {high} om {at}, goedkoopst {low} om {lowat}.",
			fc_source: "Verwachting: Bron:",
			fc_action_L: "laden",
			fc_action_H: "vasthouden",
			fc_action_N: "leveren",
			fc_action_X: "terugleveren"
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
			not_judged_title: "Het celverschil wordt beoordeeld als de accu (bijna) vol is en met weinig stroom laadt.",
			days_title: "Wat deed de accu per dag · afgelopen 7 dagen",
			days_solar: "laden uit zon",
			days_grid: "laden uit net",
			days_house: "leveren aan huis",
			days_export: "leveren aan net",
			days_note: "kWh aan de accukant van de omvormer (AC) · vandaag tot nu",
			days_up: "geladen ↑",
			days_down: "geleverd ↓",
			days_charged: "Geladen",
			days_charged_sub: "zon + net",
			days_delivered: "Geleverd",
			days_delivered_sub: "huis + net",
			days_cycles: "Cycli",
			days_soc: "SoC",
			days_soc_sub: "laagste – hoogste",
			days_week: "Week",
			days_week_charged: "geladen {kwh} kWh (zon {solar} · net {grid})",
			days_week_delivered: "geleverd {kwh} kWh",
			days_week_cycles: "{n} cycli",
			days_week_efficiency: "rendement {pct}",
			days_week_price: "uit net gem. {price}/kWh",
			days_explain: "Cycli = geleverd ÷ bruikbare capaciteit ({usable} kWh tussen de grenzen). Rendement = geleverd ÷ geladen over de week, met de verandering in SoC verrekend. Uit het kostenlogboek, per afgesloten kwartier.",
			days_n: "{n} dagen"
		},
		settings: /* @__PURE__ */ JSON.parse("{\"title\":\"Instellingen\",\"groups\":{\"battery\":\"Accu en grenzen\",\"sources\":\"Bronnen\",\"tariffs\":\"Tarieven\",\"planner\":\"Planner\",\"corrections\":\"Correcties\",\"zero_meter\":\"Nul op de meter zonder planner\",\"testing\":\"Testfase\",\"vacation\":\"Vakantie\",\"house\":\"Apparaten\"},\"default\":\"standaard: {value}\",\"none\":\"leeg\",\"yes\":\"aan\",\"no\":\"uit\",\"more\":\"Meer uitleg over {label}\",\"readonly\":\"Alleen een beheerder kan instellingen wijzigen.\",\"reload_note\":\"Wijzigingen in deze groep bewaar je samen; ZEPHYR start daarna kort opnieuw.\",\"supplier_note\":\"Met een leverancier gelden de bedragen uit de tarieventabel ({source}). De grijze vakken tonen die bedragen; alleen bij eigen tarieven zijn ze aan te passen.\",\"status\":{\"unset\":\"niet ingesteld\",\"missing\":\"niet gevonden: {entities}\",\"ok\":\"werkt\",\"interval\":\"meldt elke {s} s\",\"slots\":\"{n} prijzen in de sensor\",\"unavailable\":\"niet beschikbaar\",\"climate\":\"{mode} · {action}\",\"no_step\":\"nog geen meting\",\"steps\":\"elke {every} een stap van {kwh} kWh\"},\"own\":\"Eigen tarieven\",\"options\":{\"single\":\"Eén sensor (afname − teruglevering)\",\"import_export\":\"Twee sensoren (afname en teruglevering)\",\"heat\":\"Verwarmen\",\"cool\":\"Koelen\",\"dry\":\"Drogen\",\"fan_only\":\"Ventileren\",\"heat_cool\":\"Verwarmen/koelen\",\"auto\":\"Automatisch\",\"off\":\"Uit\",\"curtail_off\":\"Uit (gaat het net op, kost geld)\",\"curtail_external\":\"Ander systeem knijpt af\",\"curtail_zephyr\":\"ZEPHYR knijpt af\",\"indicative\":\"Indicatief (alleen tonen)\",\"use\":\"Meerekenen\",\"low\":\"Laag (voorzichtig)\",\"mid\":\"Midden\"},\"fields\":{\"min_soc\":{\"label\":\"Minimaal laadpercentage\",\"help\":\"Hieronder levert de accu niet meer.\",\"more\":\"Standaard 10 %; gangbaar 5–15 %. Lager = meer bruikbare energie, maar de accu staat vaker bijna leeg. ZEPHYR zet dit ook in de set, zodat die stopt als ZEPHYR niet draait. Voorbeeld: 11 kWh en 10 % → 1,1 kWh blijft altijd over.\"},\"max_soc\":{\"label\":\"Maximaal laadpercentage\",\"help\":\"Hierboven laadt de accu niet verder.\",\"more\":\"Standaard 95 %; 90–95 % scheelt een beetje slijtage, 100 % geeft ± 5 % meer bruikbare energie. De set moet af en toe 100 % halen om de SOC-meting gelijk te zetten en de cellen te balanceren; zie Kalibratie na dagen.\"},\"p1_source\":{\"label\":\"P1-meting\",\"help\":\"Eén sensor met het netto vermogen, of afname en teruglevering apart.\",\"more\":\"Kies Eén sensor als je meter één vermogen geeft dat negatief wordt bij teruglevering (meestal bij een P1-dongle zoals HomeWizard). Kies Afname en teruglevering bij twee aparte sensoren (DSMR-integratie). Hoe vaker de meter meldt, hoe beter: DSMR 5 meldt elke seconde, DSMR 4 elke 10 s. Meldt de meter langer dan 10 s niets, dan stopt ZEPHYR veilig.\"},\"p1_entity\":{\"label\":\"P1-sensor (netto)\",\"help\":\"Vermogen van het net: + = afname, − = teruglevering.\",\"more\":\"Een vermogenssensor in W of kW, positief bij afname. Bijvoorbeeld Active power van een HomeWizard P1-meter. Niet de kWh-teller.\"},\"p1_import_entity\":{\"label\":\"P1 afname\",\"help\":\"Vermogen dat uit het net komt.\",\"more\":\"Bijvoorbeeld Power consumption van de DSMR-integratie (in kW of W). ZEPHYR rekent afname − teruglevering.\"},\"p1_export_entity\":{\"label\":\"P1 teruglevering\",\"help\":\"Vermogen dat naar het net gaat.\",\"more\":\"Bijvoorbeeld Power production van de DSMR-integratie. Hoort bij dezelfde meter als de afname-sensor.\"},\"price_entity\":{\"label\":\"Prijssensor\",\"help\":\"Nord Pool: de integratie van HACS, of de huidige prijs van de Nord Pool-integratie van HA zelf.\",\"more\":\"Bijvoorbeeld de Nord Pool-integratie (HACS) of de Nord Pool-integratie van HA, gebied NL, prijzen per kwartier zonder belasting (ZEPHYR telt opslag, belasting en btw zelf op). De prijzen van morgen komen rond 13:00. Zonder prijssensor maakt ZEPHYR geen plan en regelt het alleen nul op de meter.\"},\"solar_forecast_entity\":{\"label\":\"Zonverwachting\",\"help\":\"Solcast (morgen) met detail per half uur. Leeg: de zonverwachting uit het Energie-dashboard van HA.\",\"more\":\"Aanrader: Solcast (gratis voor thuis), het meest precies per half uur. Leeg laten werkt met elke bron in het Energie-dashboard (Forecast.Solar, Open-Meteo …), per uur. Zonder verwachting neemt de planner de opbrengst van gisteren.\"},\"solar_energy_entity\":{\"label\":\"Zonnepanelen-teller\",\"help\":\"Opbrengst in kWh (oplopend).\",\"more\":\"De oplopende kWh-teller van je omvormer, bijv. Lifetime energy van SolarEdge. Dezelfde als in het Energie-dashboard bij Zonnepanelen. Gebruikt voor het huisverbruik, het kostenlogboek en het bijstellen van de zonverwachting.\"},\"excluded_energy_entity\":{\"label\":\"Airco: energieteller\",\"help\":\"kWh-teller van een verbruiker die niet uit de accu mag.\",\"more\":\"Een kWh-teller van alleen de airco, bijv. van een slimme stekker of tussenmeter, of de energiesensor van de airco-integratie. ZEPHYR levert niet voor de airco zolang die in een geblokkeerde stand draait; de rest van het huis komt wel uit de accu.\"},\"excluded_climate_entity\":{\"label\":\"Airco: klimaat-entiteit\",\"help\":\"Zegt direct of hij draait en in welke stand.\",\"more\":\"De climate-entiteit van de airco. Daarmee ziet ZEPHYR direct of hij aan staat en of hij verwarmt of koelt. Zonder: de airco komt nooit uit de accu en een stop merkt ZEPHYR pas aan de teller.\"},\"excluded_hvac_modes\":{\"label\":\"Airco: niet uit de accu bij\",\"help\":\"Standen waarin de accu de airco niet voedt.\",\"more\":\"Standaard verwarmen: in de winter verbruikt de airco veel, en stroom uit het net is dan vaak goedkoper dan uit de accu. Kies ook koelen als de airco nooit uit de accu mag.\"},\"cost_import_counters\":{\"label\":\"Tellers afname\",\"help\":\"De kWh-tellers van je slimme meter (tarief 1 en 2).\",\"more\":\"Kies beide kWh-tellers van je slimme meter: Energy consumption (tarif 1) en (tarif 2). Preciezer dan het vermogen optellen; voor het kostenlogboek en de besparing.\"},\"cost_export_counters\":{\"label\":\"Tellers teruglevering\",\"help\":\"De kWh-tellers voor teruglevering (tarief 1 en 2).\",\"more\":\"Kies beide terugleveringstellers: Energy production (tarif 1) en (tarif 2). Voor het kostenlogboek.\"},\"tariff_supplier\":{\"label\":\"Energieleverancier\",\"help\":\"Bedragen uit de tarieventabel van ZEPHYR, of eigen tarieven.\",\"more\":\"Staat je leverancier in de lijst, kies die: belasting, opslagen en zonnebonus komen dan uit de tabel en lopen mee met nieuwe tarieven. Staat hij er niet in, kies Eigen tarieven en vul de bedragen van je contract in.\"},\"tariff_energy_tax\":{\"label\":\"Energiebelasting\",\"help\":\"Per kWh, zonder btw.\",\"more\":\"Wettelijk bedrag per kWh, zonder btw; nu {in_use}. Verandert elk jaar op 1 januari; met een leverancier uit de tabel gaat dat vanzelf.\"},\"tariff_markup_import\":{\"label\":\"Opslag inkoop\",\"help\":\"Wat de leverancier bovenop de marktprijs rekent, zonder btw.\",\"more\":\"Wat de leverancier per kWh bovenop de marktprijs rekent, zonder btw. Gangbaar € 0,01–0,03; Zonneplan € 0,01653. Staat op je contract of in de tariefkaart, soms als inkoopvergoeding.\"},\"tariff_markup_export\":{\"label\":\"Opslag teruglevering\",\"help\":\"Bij de marktprijs opgeteld (negatief = kosten), zonder btw.\",\"more\":\"Wat je per teruggeleverde kWh bovenop de marktprijs krijgt, zonder btw. Trekt je leverancier er iets af (terugleverkosten), vul het negatief in, bijv. −0,02. Bij Zonneplan + € 0,01653.\"},\"tariff_vat\":{\"label\":\"Btw\",\"help\":\"Over marktprijs, opslag en energiebelasting.\",\"more\":\"Wettelijk tarief, 21 % in Nederland. Telt over marktprijs, opslag en energiebelasting.\"},\"tariff_solar_bonus\":{\"label\":\"Zonnebonus\",\"help\":\"Extra op de terugleverprijs overdag.\",\"more\":\"Extra percentage op de terugleverprijs zolang de zon op is, bijv. 10 % bij Zonneplan. Geen zonnebonus: 0.\"},\"tariff_fixed_month\":{\"label\":\"Vaste kosten per maand\",\"help\":\"Leveringskosten en netbeheer min heffingskorting.\",\"more\":\"Vaste leveringskosten + netbeheerkosten − vermindering energiebelasting, per maand en inclusief btw. Staat op je jaarafrekening of tariefkaart. Alleen voor het kostenlogboek; verandert het plan niet.\"},\"plan_wear_cost\":{\"label\":\"Slijtagekosten\",\"help\":\"Per kWh door de accu.\",\"more\":\"Standaard € 0,03 per kWh: ongeveer de aanschafprijs gedeeld door wat de accu in zijn leven levert (bijv. € 3.000 / 6.000 cycli / 10 kWh ≈ € 0,05). Hoger = de accu werkt alleen bij grotere prijsverschillen.\"},\"plan_grid_charge_cost\":{\"label\":\"Drempel laden uit het net\",\"help\":\"Minimale winst per kWh om uit het net te laden.\",\"more\":\"Standaard € 0,01. Laden uit het net gebeurt alleen als het per kWh minstens zoveel oplevert, na verlies en slijtage. Hoger = minder vaak laden uit het net voor een klein voordeel.\"},\"plan_allow_export\":{\"label\":\"Terugleveren uit de accu\",\"help\":\"Mag de accu naar het net leveren als dat loont?\",\"more\":\"Standaard uit. Aan is alleen zinvol als de terugleverprijs soms hoger is dan wat bijladen later kost, inclusief ± 15 % verlies en slijtage. Met saldering (tot 2027) levert het zelden iets op.\"},\"plan_load_margin\":{\"label\":\"Laadmarge\",\"help\":\"Rekenen met meer verbruik dan geleerd.\",\"more\":\"Standaard 0 %; 5–15 % als de accu op drukke avonden te vroeg leeg is. De planner rekent dan met zoveel meer verbruik dan geleerd.\"},\"plan_buffer\":{\"label\":\"Buffer\",\"help\":\"Deel van de accu dat de planner niet inplant.\",\"more\":\"Standaard 0 %; bijv. 10 % als je een reserve wilt voor onverwacht verbruik. De planner plant dit deel niet in; de regelaar mag het wel gebruiken als het verbruik hoger uitvalt. Daarna vult de planner het bij als dat goedkoop kan.\"},\"expensive_hours\":{\"label\":\"Dure uren\",\"help\":\"Zonder planner: alleen in de N duurste uren leveren.\",\"more\":\"Standaard 4: de accu levert alleen in de 4 duurste uren van de dag en houdt de lading verder vast. Alleen in de modus Nul op de meter met een prijssensor; Dynamische Forecasting kiest zelf.\"},\"reserve_soc\":{\"label\":\"Reserve\",\"help\":\"Zonder planner: bijladen tot dit percentage vóór de dure uren.\",\"more\":\"Standaard 20 %: vóór de dure uren laadt ZEPHYR bij tot dit percentage. Alleen zonder planner; met Dynamische Forecasting telt het als buffer.\"},\"min_price\":{\"label\":\"Minimumprijs\",\"help\":\"Zonder planner: niet leveren onder deze prijs.\",\"more\":\"Bijv. € 0,25: onder deze prijs (all-in, per kWh) levert de accu niet. Leeg = geen minimum.\"},\"live_off_after_restart\":{\"label\":\"Live sturen uit na een herstart (testfase)\",\"help\":\"Uit (standaard): na een herstart komt live sturen vanzelf terug zodra de P1 meldt en de sets online zijn (als het aan stond). Aan: het blijft uit en je zet het zelf weer aan.\",\"more\":\"Standaard uit: na een herstart komt live sturen vanzelf terug. Aan alleen tijdens het testen, als je na elke herstart eerst wilt kijken voordat ZEPHYR de accu weer stuurt.\"},\"vacation_when_away\":{\"label\":\"Vakantie als niemand thuis is\",\"help\":\"Vanzelf aan na 24 uur zonder iemand thuis.\",\"more\":\"Na 24 uur zonder iemand thuis (zone.home = 0) gaat vakantie vanzelf aan: de planner rekent dan met weinig verbruik. Uit zodra er iemand terug is. Werkt alleen als telefoons met de HA-app hun locatie delen.\"},\"workday_entity\":{\"label\":\"Werkdag-sensor\",\"help\":\"Feestdagen tellen als weekenddag.\",\"more\":\"Installeer de integratie Workday (land NL) en kies de sensor. Dan tellen feestdagen als weekenddag in het verbruiksprofiel. Zonder sensor zijn maandag t/m vrijdag werkdagen.\"},\"curtail_negative\":{\"label\":\"Zonoverschot bij negatieve prijs\",\"help\":\"Wat er met zonoverschot gebeurt als de terugleverprijs onder nul is. Uit: het gaat het net op en kost geld, de planner maakt eerst ruimte in de accu. Ander systeem: een omvormerbegrenzer knijpt zelf af. ZEPHYR: ZEPHYR blokkeert teruglevering van de eigen panelen van de sets en knijpt de omvormer af: met de schakelaar of met de vermogensbegrenzing hieronder (één van beide).\",\"more\":\"Met saldering (tot 2027) is de terugleverprijs zelden negatief. Zonder saldering gebeurt het op zonnige middagen in voorjaar en zomer. Kies ZEPHYR als je omvormer via HA te begrenzen is (bijv. SolarEdge via Modbus), Ander systeem als iets anders dat al doet.\"},\"curtail_switch\":{\"label\":\"Schakelaar omvormer afknijpen\",\"help\":\"Aan zolang de terugleverprijs negatief is. Alternatief voor de vermogensbegrenzing.\",\"more\":\"Een schakelaar die je omvormer laat stoppen met terugleveren, bijv. een sjabloon-schakelaar die de exportbegrenzing van je omvormer zet. ZEPHYR zet hem aan bij een negatieve terugleverprijs en daarna weer uit. Kies dit óf de vermogensbegrenzing.\"},\"solar_power_entities\":{\"label\":\"Zonnepanelen-vermogen\",\"help\":\"Vermogenssensoren (W) van omvormers, worden opgeteld.\",\"more\":\"Vermogen in W van omvormers die niet aan een Zendure-set hangen, bijv. AC power van SolarEdge; meerdere worden opgeteld. Niet de PV van de Zendure-set zelf: die leest ZEPHYR al. Leeg: ZEPHYR schat het uit de zonnepanelen-teller (grover, loopt achter).\"},\"curtail_number\":{\"label\":\"Vermogensbegrenzing omvormer\",\"help\":\"Getal-entiteit die het vermogen van de omvormer begrenst in % (bijv. SolarEdge Modbus active power limit). Alleen met ZEPHYR knijpt af.\",\"more\":\"Bijv. Active power limit van de SolarEdge Modbus-integratie (getal in %). ZEPHYR zet die elke 10 s zo dat de omvormer alleen levert wat huis en accu afnemen, en daarna terug op 100 %. Nodig: het nominaal vermogen hieronder en het zonnepanelen-vermogen (Bronnen).\"},\"curtail_inverter_w\":{\"label\":\"Nominaal vermogen omvormer\",\"help\":\"Nominaal AC-vermogen van die omvormer (W), om de gewenste productie om te zetten in %. 0 = niet ingesteld.\",\"more\":\"Het AC-vermogen op het typeplaatje, bijv. 5000 W voor een SolarEdge SE5K, 3680 W voor een SE3680H.\"},\"calibration_days\":{\"label\":\"Kalibratie na dagen\",\"help\":\"Na zoveel dagen zonder 100 % laadt de planner de accu vol en laat hij de set kalibreren.\",\"more\":\"Standaard 21 dagen; 0 = uit. Hoe langer de accu niet vol was, hoe verder de packs uit elkaar lopen. Vanaf de helft van deze dagen zoekt de planner een goedkoop moment of zon om vol te laden; op de laatste dag moet het. Daarna levert ZEPHYR niet tot de set klaar is met kalibreren (max. 2 uur).\"},\"price_forecast_entity\":{\"label\":\"Prijsvoorspelling (jeroen.nl)\",\"help\":\"Optioneel: de sensor van ha-jeroen-nl, om voorbij de bekende prijzen te kijken.\",\"more\":\"Installeer de HACS-integratie ha-jeroen-nl met je eigen API-sleutel van jeroen.nl en kies hier de prijssensor. ZEPHYR leest alleen die sensor en haalt zelf nooit iets op bij jeroen.nl. Alleen voorspelde kwartieren na de laatste bekende Nord Pool-prijs worden gebruikt; Nord Pool blijft leidend. Bron: jeroen.nl.\"},\"price_forecast_mode\":{\"label\":\"Gebruik in het plan\",\"help\":\"Indicatief: het plan blijft gelijk. Meerekenen: de planner plant met de voorspelling.\",\"more\":\"Indicatief: de diagnose vergelijkt het plan met en zonder voorspelling. Meerekenen: de planner kijkt ook naar de voorspelde dagen (standaard de dag na de bekende prijzen, dus na ongeveer 13:00 overmorgen). Het niveau van de voorspelling kan ernaast zitten, de tendens is meestal duidelijk; met de waarde Laag blijft de planner voorzichtig. Blokken op voorspelde kwartieren blijven indicatief en tellen niet mee in de totalen. De opgeslagen voorspellingen geven na ongeveer 6 weken een backtest.\"},\"price_forecast_days\":{\"label\":\"Voorspelde dagen\",\"help\":\"Hoeveel dagen voorbij de laatste bekende prijs.\",\"more\":\"Standaard 1: vóór ongeveer 13:00 staat de voorspelling in voor morgen; daarna komt overmorgen erbij. 0 = de voorspelling alleen bewaren voor de kwaliteitscijfers.\"},\"price_forecast_value\":{\"label\":\"Waarde uit de band\",\"help\":\"Laag is voorzichtig: niet laden op een optimistische verwachting.\",\"more\":\"jeroen.nl geeft een band van 80 % (p10–p90). Laag gebruikt p10 voor inkoop en teruglevering, zodat de planner niet laadt voor, of energie vasthoudt voor, een piek die misschien niet komt. Midden gebruikt de verwachte waarde.\"}},\"restarting\":\"ZEPHYR start opnieuw met de nieuwe instellingen…\",\"pending\":\"{n} wijzigingen nog niet bewaard · ZEPHYR start kort opnieuw\",\"pending_one\":\"1 wijziging nog niet bewaard · ZEPHYR start kort opnieuw\",\"cancel\":\"Annuleren\",\"save_restart\":\"Bewaren en herstarten\",\"saving\":\"Bezig…\",\"saved\":\"bewaard\",\"not_saved\":\"niet bewaard\",\"reset\":\"Standaard terugzetten\",\"clear\":\"Leegmaken\",\"remove\":\"Weghalen\",\"choose_entity\":\"Kies of typ een entiteit\",\"actions\":{\"heating\":\"draait\",\"cooling\":\"draait\",\"drying\":\"draait\",\"fan\":\"draait\",\"preheating\":\"draait\",\"defrosting\":\"ontdooit\",\"idle\":\"staat stil\",\"off\":\"uit\"},\"errors\":{\"out_of_range\":\"Buiten de grenzen.\",\"off_step\":\"Past niet bij de stapgrootte.\",\"not_a_number\":\"Geen getal.\",\"not_a_bool\":\"Ongeldige waarde.\",\"required\":\"Mag niet leeg zijn.\",\"unknown_choice\":\"Onbekende keuze.\",\"choose_one\":\"Kies minstens één stand. Uitzetten: maak de teller leeg.\",\"not_an_entity\":\"Dit soort entiteit past hier niet.\",\"entity_missing\":\"Entiteit niet gevonden.\",\"unknown_key\":\"Onbekende instelling.\",\"p1_missing\":\"Kies een P1-sensor.\",\"p1_pair_incomplete\":\"Kies zowel de afname- als de terugleversensor.\",\"p1_pair_same\":\"Afname en teruglevering moeten twee verschillende sensoren zijn.\",\"excluded_needs_counter\":\"De klimaat-entiteit werkt alleen samen met de energieteller van de airco. Kies de teller of maak de klimaat-entiteit leeg.\",\"failed\":\"Bewaren lukte niet. Probeer het opnieuw.\",\"range\":\"Kies een waarde van {min} tot en met {max}{unit}.\",\"entity_domain\":\"Dit veld verwacht een {domain}-entiteit\"},\"vac_active\":\"Op vakantie\",\"vac_home\":\"Thuis\",\"vac_off\":\"De planner rekent met het gewone verbruik.\",\"vac_until\":\"Tot {until}. De planner rekent tot dan met het verbruik bij afwezigheid en laadt op tijd voor de terugkomst.\",\"vac_open\":\"Zonder einddatum; zet het uit als je terug bent.\",\"vac_auto\":\"Vanzelf aan sinds {since}: niemand is 24 uur thuis geweest (optie hieronder). Gaat uit zodra iemand thuiskomt.\",\"vac_until_label\":\"Terug op\",\"vac_start\":\"Vakantie aanzetten\",\"vac_stop\":\"Vakantie uitzetten\",\"vac_help\":\"Tijdens een vakantie rekent de planner met het sluimerverbruik en leert hij dat apart; het gewone verbruiksprofiel blijft schoon. Een einddatum is optioneel.\",\"house_note\":\"Wanneer je je apparaten meestal laat draaien. Met één tik onder Prijzen en plan kiest ZEPHYR de goedkoopste start binnen dit venster. Een nieuw apparaat met slimme stekker voeg je toe via Apparaten en diensten → ZEPHYR → Apparaat toevoegen. Het venster wijzigen herlaadt ZEPHYR even.\",\"house_floor\":\"Verdieping\",\"save\":\"Opslaan\",\"discard\":\"Annuleren\",\"floors\":{\"attic\":\"Zolder\",\"first\":\"1e verdieping\",\"ground\":\"Begane grond\",\"shed\":\"Schuur\",\"outside\":\"Buiten\"},\"appl_learned\":\"geleerd uit {n} runs\",\"appl_default\":\"standaardprofiel\",\"appl_airco\":\"niet uit de accu (Correcties)\",\"appl_from\":\"Niet vóór\",\"appl_until\":\"Klaar om\",\"appl_shown\":\"Tonen op Stroom\",\"appl_after\":\"Altijd na de was\",\"appl_after_help\":\"plan de droger mee (één keer, na de laatste was) als je de was plant\",\"curtail_head\":\"Omvormer buiten de sets (kies één)\",\"curtail_rated_missing\":\"Vul het nominale vermogen in, anders begrenst ZEPHYR niet.\",\"sections\":{\"meter\":\"Meter\",\"prices\":\"Prijzen\",\"solar\":\"Zon\",\"counters\":\"Tellers\",\"plan\":\"Plan\",\"curtail\":\"Afknijpen\"},\"group_sub\":{\"battery\":\"min, max, kalibratie\",\"tariffs\":\"leverancier, belasting, btw\",\"corrections\":\"airco\",\"vacation\":\"niemand thuis\",\"house\":\"plaatje, verdiepingen, apparaten\",\"zero_meter\":\"dure uren, reserve\",\"testing\":\"live na herstart\"}}"),
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
			}
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
				test: "schrijftest",
				grid_reverse: "terugleverblokkade"
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
			profile_empty_weekend: "Nog geen weekenddagen geleerd. Tot dan rekent de planner op zaterdag en zondag elk uur met het gemiddelde ({mean} kWh).",
			check_title: "Plan tegen werkelijkheid",
			check_intro: "Wat het plan van de avond ervoor verwachtte, naast wat er gebeurde. Laatste {n} hele dagen; alleen kwartieren waarvoor een plan was.",
			check_none: "Nog geen hele dag met een plan van de dag ervoor. Dit vult zich vanaf morgen.",
			check_expected: "Verwacht",
			check_actual: "Gemeten",
			check_diff: "Verschil",
			check_daily: "Gem. per dag ernaast",
			check_per_day: "Per dag: {metric}",
			check_partial: "{n} van {of} kwartieren met een plan",
			m_load: "Verbruik huis",
			m_solar: "Zon",
			m_import: "Afname",
			m_export: "Teruglevering",
			m_cost: "Kosten",
			energy_title: "Energietellers",
			energy_sub: "ZEPHYR's eigen tellers per set (kWh sinds de start), met wat er na een gat is aangevuld",
			energy_charged: "Geladen",
			energy_discharged: "Geleverd",
			energy_solar: "Zon",
			energy_estimated: "Geschat",
			energy_failed: "Mislukte reads",
			energy_total: "Totaal",
			energy_open: "Set niet bereikbaar sinds {since}: wordt aangevuld zodra hij terug is.",
			energy_open_restart: "Herstart sinds {since}: wordt aangevuld bij het eerste rapport.",
			energy_gaps: "Laatste gaten",
			energy_no_gaps: "Geen gaten: de tellers liepen zonder onderbreking.",
			energy_m_none: "niets aan te vullen",
			energy_m_interpolate: "doorgetrokken",
			energy_m_soc: "uit de laadstand",
			energy_restart: "herstart",
			energy_nothing: "0 kWh",
			energy_note: "Geschat = aangevuld na een gat (doorgetrokken bij korte gaten, anders uit het verschil in laadstand). Mislukte reads tellen sinds de start van ZEPHYR.",
			peaks_title: "Korte pieken",
			peaks_line: "Korte pieken uit het net: vandaag {today} ({n}×), gemiddeld {mean} per dag",
			peaks_info: "Plotselinge stijgingen van meer dan 800 W (zoals een Quooker) volgt ZEPHYR de eerste 10 s niet. Dat scheelt schrijfacties en heen-en-weer regelen; deze energie komt uit het net.",
			peaks_bars: "Korte pieken per dag, laatste 14 dagen",
			peaks_note: "Na een herstart van HA begint deze reeks opnieuw.",
			appl_title: "Apparaatprofielen",
			appl_empty: "Nog geen apparaten. Voeg ze toe bij Apparaten en diensten → ZEPHYR → Apparaat toevoegen.",
			appl_learned: "geleerd uit {n} runs",
			appl_default: "standaardprofiel",
			appl_per_run: "{kwh} en {time} per run",
			appl_plug: "met stekker",
			appl_noplug: "zonder stekker",
			appl_running: "Draait nu",
			appl_chart: "Vermogen per minuut van een run, tot {max} W",
			appl_max: "max {w} W",
			kind_washer: "wasmachine",
			kind_dryer: "droger",
			kind_dishwasher: "vaatwasser",
			kind_other: "overig",
			sec_planner: "Planner",
			sec_measure: "Meting en set",
			sec_log: "Logboek",
			energy_gaps_all: "Toon alle {n} gaten",
			energy_gaps_less: "Toon minder"
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
			incomplete: "{n} van {total} kwartieren zonder gegevens; de bedragen zijn dan te laag.",
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
			bf_ez_failed: "EnergyZero gaf voor {n} dag(en) geen prijzen; probeer het later nog eens.",
			estimated: "{n} van {total} kwartieren geschat (HA stond uit, de set was even onbereikbaar of de prijs ontbrak).",
			estimated_price: "Waarvan {n} met een voorlopige prijs; die wordt vervangen zodra de echte er is.",
			title_solar: "Besparing door zon en accu",
			without_both: "Zonder zon en accu",
			sun_group: "Zon",
			sun_direct: "Zon direct gebruikt",
			sun_direct_help: "zon die het huis meteen gebruikte, in plaats van stroom te kopen.",
			sun_export: "Zon teruggeleverd",
			sun_export_help: "Zon die naar het net ging; tot 2027 bijna evenveel waard als afname, plus 10 % bonus overdag.",
			sun_bonus: "Waarvan zonnebonus {euro}.",
			sun_after_saldering: "Vanaf 1-1-2027 levert teruglevering alleen marktprijs + opslag + bonus op.",
			battery_group: "Accu",
			sun_total: "zon",
			self_consumption: "zelf gebruikt",
			note_solar: "Zon = wat je zonder zonnepanelen méér had betaald: direct verbruik tegen de inkoopprijs en teruglevering tegen de terugleverprijs.",
			battery_only: "Alleen accu",
			day_split: "zon {sun}, accu {bat}",
			day_estimated: "deels geschat",
			leg_sun: "Zon",
			leg_estimated: "Deels geschat",
			bf_soc: "Laadtoestand accu (%)",
			bf_warn_pv: "Let op: deze tellers zijn van een andere Zendure-integratie en bevatten de zonnepanelen op de set; in de zomer telt die zon dan als accu."
		},
		flow: {
			title: "Nu",
			solar: "Zon",
			house: "Huis",
			airco: "waarvan airco {w}",
			none: "geen",
			balanced: "op nul",
			shadow_chip: "Schaduw",
			s_idle: "Er loopt nu bijna geen stroom.",
			s_solar_house: "zon {w} naar het huis",
			s_solar_battery: "zon {w} naar de accu",
			s_export: "{w} teruglevering",
			s_grid_house: "net {w} naar het huis",
			s_grid_battery: "net {w} naar de accu",
			s_battery_house: "accu {w} naar het huis",
			grid: "Net",
			grid_in: "Afname",
			grid_out: "Teruglevering",
			charging: "Accu laadt",
			delivering: "Accu levert",
			battery: "Accu",
			estimated: "geschat",
			curtailed: "Afgeknepen tot {pct} %",
			inverter_off: "Omvormer uit",
			export_blocked: "Teruglevering geblokkeerd"
		},
		stroom: {
			zero_title: "Nul op de meter vandaag",
			zero_sub: "Tijd dat de meter binnen ±{band} W van zijn doel bleef, zolang ZEPHYR stuurde",
			zero_empty: "ZEPHYR heeft vandaag nog niet op nul gestuurd.",
			zero_shadow: "ZEPHYR stuurt niet (schaduw): er is geen score.",
			zero_good: "goed · doel {goal}",
			zero_low: "onder het doel van {goal}",
			zero_in: "binnen ±{band} W",
			zero_import: "afname",
			zero_export: "teruglevering",
			zero_idle: "niet op nul (laden, vasthouden, schaduw)",
			zero_strip: "Per 5 minuten: binnen de band, afname, teruglevering of niet op nul",
			zero_imported: "Afgenomen tijdens sturen",
			zero_exported: "Teruggeleverd tijdens sturen",
			zero_mean: "Gem. afwijking",
			routes_title: "Energie per route vandaag",
			routes_sub: "Waar de stroom vandaan kwam en heen ging, 00:00–{until} (per kwartier geschat)",
			routes_none: "Nog geen afgesloten kwartier vandaag.",
			src_solar: "Zon",
			src_grid: "Net",
			src_battery: "Accu",
			to_house: "huis",
			to_battery: "accu",
			to_grid: "net",
			self_use: "Zelf gebruikt van de zon",
			own_source: "Huis uit eigen bron",
			grid_battery_price: "Net → accu, gem. prijs",
			airco_title: "Airco vandaag",
			airco_sub: "Telt mee in het huis, maar de accu voedt hem niet",
			airco_share: "{share} van het huisverbruik",
			airco_fed: "Gevoed door",
			airco_cost: "Airco-stroom van het net",
			airco_price: "Gem. prijs",
			reg_title: "Regeling · laatste 10 minuten",
			reg_sub: "Of ZEPHYR snel genoeg bijstuurt en de accu doet wat gevraagd wordt",
			reg_empty: "Nog geen metingen sinds de start.",
			reg_p1: "P1 t.o.v. doel (afname +)",
			reg_battery: "Accu (+ laden, − leveren)",
			reg_ago: "−{m} min",
			reg_now: "nu",
			reg_dev: "P1 t.o.v. doel",
			reg_sp: "gevraagd aan accu",
			reg_bat: "accu werkelijk",
			reg_idle: "niet op nul",
			reg_shadow: "schaduw: ZEPHYR stuurt niet",
			reg_recovery: "Hersteltijd na een piek (mediaan)",
			reg_seconds: "{s} s",
			reg_follow: "Accu volgt opdracht, gem. verschil",
			reg_peaks: "Pieken > 150 W",
			devices_title: "Verbruikers vandaag",
			devices_sub: "Per apparaat met een eigen stekker of meter (kWh, 00:00–nu)",
			rest: "Overig huis",
			airco_not_battery: "Airco niet uit de accu",
			airco_fed_line: "zon {solar} · net {grid}",
			house_total: "Huis totaal",
			devices_hint: "Voeg apparaten met een slimme stekker toe via Apparaten en diensten → ZEPHYR → Apparaat toevoegen.",
			kind_airco: "Airco",
			kind_washer: "Wasmachine",
			kind_dishwasher: "Vaatwasser",
			kind_dryer_heat_pump: "Droger",
			kind_dryer_condenser: "Droger",
			kind_other: "Apparaat"
		},
		appl: {
			title: "Apparaten plannen",
			running: "Draait nu",
			today: "vandaag",
			tomorrow: "morgen",
			calculating: "beste start wordt berekend…",
			tap: "Tik om te plannen",
			per_run: "~{euro} per keer",
			start: "start",
			and: "en",
			after_wash: "na de was",
			cheaper: "{euro} goedkoper dan nu",
			tap_plan: "Plannen",
			tap_more: "Nog een keer plannen",
			tap_clear: "Niet meer plannen"
		},
		house: {
			title: "Nu",
			sub: "Stroom in huis en omgeving",
			roof: "Zonnepanelen (dak)",
			shed_solar: "Zonnepanelen (schuur)",
			battery: "Accu",
			charging: "Laden",
			delivering: "Leveren",
			idle: "Rust",
			ev: "Laadpaal",
			grid: "Net",
			import: "Import",
			export: "Export",
			rest: "Overig",
			sun: "Zon",
			production: "(productie)",
			charging_l: "(laden)",
			delivering_l: "(leveren)",
			idle_l: "(rust)",
			consumers: "Verbruikers",
			house: "(huis)",
			ev_sub: "(elektrische auto)",
			import_l: "(afname)",
			export_t: "Net → op nul",
			export_l: "(teruglevering)",
			home: "Huis",
			total: "Totaal",
			rest_of: "waarvan overig",
			to_battery: "→ accu",
			to_house: "→ huis",
			to_grid: "→ net",
			src_sun: "Zon",
			src_batt: "Accu",
			src_grid: "Net",
			dst_house: "huis",
			dst_battery: "accu",
			dst_grid: "net"
		},
		picture: {
			title: "Plaatje op Stroom",
			default: "Standaard huis",
			own: "Eigen afbeelding",
			note: "Je afbeelding blijft in je eigen Home Assistant. JPG, PNG of WebP; ZEPHYR verkleint hem vóór het uploaden.",
			pick: "Kies een onderdeel en tik op het plaatje: eerst waar het vak komt, dan waar de lijn aansluit.",
			step_box: "Tik waar het vak van {item} komt.",
			step_point: "Tik waar de lijn van {item} aansluit.",
			hide: "Verberg",
			show: "Toon",
			reset: "Opnieuw plaatsen",
			replace: "Andere afbeelding",
			delete: "Afbeelding verwijderen",
			uploading: "Uploaden…",
			error: "Uploaden mislukt: {msg}",
			unplaced: "Nog niet geplaatst",
			hidden: "Verborgen"
		},
		version: {
			update: "Update {latest}",
			busy: "Bezig met bijwerken…",
			update_title: "ZEPHYR bijwerken naar {latest}?",
			update_text: "Nu: {running}. HACS installeert de nieuwe versie. Daarna moet Home Assistant opnieuw starten; tot dan draait {running} door.",
			update_do: "Bijwerken",
			notes: "Wat is er nieuw",
			update_other: "v{running} · update {latest}",
			restart: "Herstart nodig",
			restart_title: "Home Assistant herstarten?",
			restart_text: "Versie {installed} is geïnstalleerd, maar {running} draait nog. Na een herstart van Home Assistant draait {installed}.",
			restart_do: "Herstarten",
			restart_other: "v{running} · herstart nodig"
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
			savings: "Savings",
			stroom: "Power"
		},
		header: {
			live: "Active",
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
			shadow_note: "What ZEPHYR would do (shadow mode).",
			p1_import: "P1 · import",
			p1_export: "P1 · export",
			p1_zero: "P1"
		},
		battery: {
			title: "Battery",
			of: "{energy} of {capacity}",
			limits: "Limits {min}–{max} %",
			buffer: "buffer {value} %",
			sets: "{online} of {total} sets online",
			set: "1 set",
			set_offline: "set offline",
			unknown: "No data from the set yet",
			rte: "RTE {value}",
			rte_title: "Round-trip efficiency: delivered ÷ charged, corrected for the change in SoC, over the last 7 days (or fewer if the cost log is shorter). Same as on the screen Accu."
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
			spread_title: "How much more the most expensive quarter costs than the day's mean. A rough measure of what delivering at the most expensive moments earns, before losses (about 14 %) and wear. With a mean around zero or negative: the difference in euro.",
			tip_appliances: "Appliances: {kwh}",
			runs_label: "Planned appliances",
			curtail_mark: "Solar surplus is curtailed",
			tip_curtail: "Export price {price}: solar surplus {kwh} is curtailed",
			tip_export_cost: "Exporting costs {euro} (no curtailing set up)",
			neg_today: "Today {hours} h of negative export price. Curtailing is off; that is expected to cost {euro}.",
			neg_tomorrow: "Tomorrow {hours} h of negative export price. Curtailing is off; that is expected to cost {euro}.",
			neg_both: "Today and tomorrow {hours} h of negative export price. Curtailing is off; that is expected to cost {euro}.",
			neg_link: "Change the setting →",
			legend_negative: "Negative export price",
			fc_peak: "(expected {when}: {price}, 80 % chance {low}–{high})",
			fc_would: "With the forecast ZEPHYR would {action} now.",
			fc_used: "The plan takes the price forecast into account.",
			fc_day: "Forecast {day}: on average {avg}, dearest {high} at {at}, cheapest {low} at {lowat}.",
			fc_source: "Forecast: Source:",
			fc_action_L: "charge",
			fc_action_H: "hold",
			fc_action_N: "deliver",
			fc_action_X: "export"
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
			not_judged_title: "The cell difference is judged when the battery is (nearly) full and the current is small.",
			days_title: "What the battery did per day · last 7 days",
			days_solar: "charged from solar",
			days_grid: "charged from grid",
			days_house: "delivered to house",
			days_export: "delivered to grid",
			days_note: "kWh at the battery side of the inverter (AC) · today so far",
			days_up: "charged ↑",
			days_down: "delivered ↓",
			days_charged: "Charged",
			days_charged_sub: "solar + grid",
			days_delivered: "Delivered",
			days_delivered_sub: "house + grid",
			days_cycles: "Cycles",
			days_soc: "SoC",
			days_soc_sub: "lowest – highest",
			days_week: "Week",
			days_week_charged: "charged {kwh} kWh (solar {solar} · grid {grid})",
			days_week_delivered: "delivered {kwh} kWh",
			days_week_cycles: "{n} cycles",
			days_week_efficiency: "efficiency {pct}",
			days_week_price: "from grid avg. {price}/kWh",
			days_explain: "Cycles = delivered ÷ usable capacity ({usable} kWh between the limits). Efficiency = delivered ÷ charged over the week, corrected for the change in SoC. From the cost log, per closed quarter.",
			days_n: "{n} days"
		},
		settings: /* @__PURE__ */ JSON.parse("{\"title\":\"Settings\",\"groups\":{\"battery\":\"Battery and limits\",\"sources\":\"Sources\",\"tariffs\":\"Tariffs\",\"planner\":\"Planner\",\"corrections\":\"Corrections\",\"zero_meter\":\"Zero on the meter without planner\",\"testing\":\"Test phase\",\"vacation\":\"Vacation\",\"house\":\"Appliances\"},\"default\":\"standard: {value}\",\"none\":\"empty\",\"yes\":\"on\",\"no\":\"off\",\"more\":\"More about {label}\",\"readonly\":\"Only an administrator can change settings.\",\"reload_note\":\"Changes in this group are saved together; ZEPHYR then restarts briefly.\",\"supplier_note\":\"With a supplier the amounts from the tariff table apply ({source}). The greyed-out fields show those amounts; they can only be changed with own tariffs.\",\"status\":{\"unset\":\"not set\",\"missing\":\"not found: {entities}\",\"ok\":\"working\",\"interval\":\"reports every {s} s\",\"slots\":\"{n} prices in the sensor\",\"unavailable\":\"unavailable\",\"climate\":\"{mode} · {action}\",\"no_step\":\"no measurement yet\",\"steps\":\"a step of {kwh} kWh every {every}\"},\"own\":\"Own tariffs\",\"options\":{\"single\":\"One sensor (import − export)\",\"import_export\":\"Two sensors (import and export)\",\"heat\":\"Heating\",\"cool\":\"Cooling\",\"dry\":\"Drying\",\"fan_only\":\"Fan\",\"heat_cool\":\"Heating/cooling\",\"auto\":\"Auto\",\"off\":\"Off\",\"curtail_off\":\"Off (exported, costs money)\",\"curtail_external\":\"Another system curtails\",\"curtail_zephyr\":\"ZEPHYR curtails\",\"indicative\":\"Indicative (show only)\",\"use\":\"Take into account\",\"low\":\"Low (careful)\",\"mid\":\"Middle\"},\"fields\":{\"min_soc\":{\"label\":\"Minimum state of charge\",\"help\":\"Below this the battery stops delivering.\",\"more\":\"Default 10 %; common 5–15 %. Lower = more usable energy, but the battery is more often nearly empty. ZEPHYR also sets this in the set, so it stops when ZEPHYR is not running. Example: 11 kWh and 10 % → 1.1 kWh always stays.\"},\"max_soc\":{\"label\":\"Maximum state of charge\",\"help\":\"Above this the battery stops charging.\",\"more\":\"Default 95 %; 90–95 % saves a little wear, 100 % gives about 5 % more usable energy. Now and then the set needs 100 % to reset its SOC reading and balance the cells; see Calibration after days.\"},\"p1_source\":{\"label\":\"P1 measurement\",\"help\":\"One sensor with net power, or import and export separately.\",\"more\":\"Choose One sensor if your meter gives one power that goes negative when exporting (usually a P1 dongle such as HomeWizard). Choose Import and export with two separate sensors (DSMR integration). The more often the meter reports, the better: DSMR 5 reports every second, DSMR 4 every 10 s. If the meter is silent for more than 10 s, ZEPHYR stops safely.\"},\"p1_entity\":{\"label\":\"P1 sensor (net)\",\"help\":\"Grid power: + = import, − = export.\",\"more\":\"A power sensor in W or kW, positive when importing. For example Active power of a HomeWizard P1 meter. Not the kWh counter.\"},\"p1_import_entity\":{\"label\":\"P1 import\",\"help\":\"Power from the grid.\",\"more\":\"For example Power consumption of the DSMR integration (in kW or W). ZEPHYR uses import − export.\"},\"p1_export_entity\":{\"label\":\"P1 export\",\"help\":\"Power to the grid.\",\"more\":\"For example Power production of the DSMR integration. Must belong to the same meter as the import sensor.\"},\"price_entity\":{\"label\":\"Price sensor\",\"help\":\"Nord Pool: the HACS integration, or the current price of Home Assistant's own Nord Pool integration.\",\"more\":\"For example the Nord Pool integration (HACS) or HA's own Nord Pool integration, area NL, prices per quarter without taxes (ZEPHYR adds markup, tax and VAT itself). Tomorrow's prices arrive around 13:00. Without a price sensor ZEPHYR makes no plan and only keeps the meter at zero.\"},\"solar_forecast_entity\":{\"label\":\"Solar forecast\",\"help\":\"Solcast (tomorrow) with half-hour detail. Empty: the solar forecast of HA's Energy dashboard.\",\"more\":\"Recommended: Solcast (free for home use), most precise per half hour. Leaving it empty works with any source in HA's Energy dashboard (Forecast.Solar, Open-Meteo …), per hour. Without a forecast the planner uses yesterday's yield.\"},\"solar_energy_entity\":{\"label\":\"Solar counter\",\"help\":\"Production in kWh (increasing).\",\"more\":\"Your inverter's increasing kWh counter, e.g. Lifetime energy of SolarEdge. The same as Solar panels in the Energy dashboard. Used for house consumption, the cost log and tuning the solar forecast.\"},\"excluded_energy_entity\":{\"label\":\"Air conditioner: energy counter\",\"help\":\"kWh counter of a load the battery may not feed.\",\"more\":\"A kWh counter of the air conditioner only, e.g. from a smart plug or sub-meter, or the energy sensor of the air conditioner integration. ZEPHYR does not deliver for it while it runs in a blocked mode; the rest of the house still comes from the battery.\"},\"excluded_climate_entity\":{\"label\":\"Air conditioner: climate entity\",\"help\":\"Says at once whether it runs and in which mode.\",\"more\":\"The air conditioner's climate entity. With it ZEPHYR sees right away whether it is on and whether it heats or cools. Without: it never comes from the battery and ZEPHYR only notices a stop from the counter.\"},\"excluded_hvac_modes\":{\"label\":\"Air conditioner: not from the battery when\",\"help\":\"Modes in which the battery does not feed it.\",\"more\":\"Default heating: in winter the air conditioner uses a lot, and grid power is then often cheaper than battery power. Also choose cooling if it must never come from the battery.\"},\"cost_import_counters\":{\"label\":\"Import counters\",\"help\":\"The kWh counters of your smart meter (tariff 1 and 2).\",\"more\":\"Choose both kWh counters of your smart meter: Energy consumption (tarif 1) and (tarif 2). More precise than adding up power; for the cost log and savings.\"},\"cost_export_counters\":{\"label\":\"Export counters\",\"help\":\"The kWh counters for export (tariff 1 and 2).\",\"more\":\"Choose both export counters: Energy production (tarif 1) and (tarif 2). For the cost log.\"},\"tariff_supplier\":{\"label\":\"Energy supplier\",\"help\":\"Amounts from ZEPHYR's tariff table, or own tariffs.\",\"more\":\"If your supplier is in the list, choose it: tax, markups and solar bonus then come from the table and follow new tariffs. If not, choose Own tariffs and enter the amounts from your contract.\"},\"tariff_energy_tax\":{\"label\":\"Energy tax\",\"help\":\"Per kWh, excluding VAT.\",\"more\":\"Statutory amount per kWh, without VAT; now {in_use}. Changes every year on 1 January; with a supplier from the table that happens automatically.\"},\"tariff_markup_import\":{\"label\":\"Import margin\",\"help\":\"What the supplier adds to the market price, excluding VAT.\",\"more\":\"What the supplier charges per kWh on top of the market price, without VAT. Common € 0.01–0.03; Zonneplan € 0.01653. On your contract or tariff sheet, sometimes as purchase fee.\"},\"tariff_markup_export\":{\"label\":\"Export margin\",\"help\":\"Added to the market price (negative = a fee), excluding VAT.\",\"more\":\"What you get per exported kWh on top of the market price, without VAT. If your supplier deducts something (export fee), enter it negative, e.g. −0.02. Zonneplan + € 0.01653.\"},\"tariff_vat\":{\"label\":\"VAT\",\"help\":\"On market price, margin and energy tax.\",\"more\":\"Statutory rate, 21 % in the Netherlands. Applies to market price, markup and energy tax.\"},\"tariff_solar_bonus\":{\"label\":\"Solar bonus\",\"help\":\"Extra on the export price during the day.\",\"more\":\"Extra percentage on the export price while the sun is up, e.g. 10 % at Zonneplan. No solar bonus: 0.\"},\"tariff_fixed_month\":{\"label\":\"Fixed costs per month\",\"help\":\"Supply and network costs minus tax credit.\",\"more\":\"Fixed supply charge + grid operator charge − energy tax reduction, per month including VAT. On your annual bill or tariff sheet. Only for the cost log; does not change the plan.\"},\"plan_wear_cost\":{\"label\":\"Wear cost\",\"help\":\"Per kWh through the battery.\",\"more\":\"Default € 0.03 per kWh: roughly the purchase price divided by what the battery delivers in its life (e.g. € 3,000 / 6,000 cycles / 10 kWh ≈ € 0.05). Higher = the battery only works at larger price differences.\"},\"plan_grid_charge_cost\":{\"label\":\"Grid charging threshold\",\"help\":\"Minimum gain per kWh to charge from the grid.\",\"more\":\"Default € 0.01. Charging from the grid only happens when it earns at least this much per kWh, after losses and wear. Higher = less often charging from the grid for a small gain.\"},\"plan_allow_export\":{\"label\":\"Export from the battery\",\"help\":\"May the battery deliver to the grid when that pays?\",\"more\":\"Default off. On only makes sense if the export price is sometimes higher than what recharging costs later, including about 15 % loss and wear. With net metering (until 2027) it rarely pays.\"},\"plan_load_margin\":{\"label\":\"Consumption margin\",\"help\":\"Plan with more consumption than learned.\",\"more\":\"Default 0 %; 5–15 % if the battery runs empty too early on busy evenings. The planner then counts on that much more consumption than learned.\"},\"plan_buffer\":{\"label\":\"Buffer\",\"help\":\"Part of the battery the planner keeps free.\",\"more\":\"Default 0 %; e.g. 10 % if you want a reserve for unexpected consumption. The planner does not plan this part; the controller may use it when consumption turns out higher. The planner then refills it when that is cheap.\"},\"expensive_hours\":{\"label\":\"Expensive hours\",\"help\":\"Without planner: only deliver in the N most expensive hours.\",\"more\":\"Default 4: the battery only delivers in the 4 most expensive hours of the day and holds its charge otherwise. Only in the mode Zero on the meter with a price sensor; Dynamic Forecasting chooses itself.\"},\"reserve_soc\":{\"label\":\"Reserve\",\"help\":\"Without planner: charge to this level before the expensive hours.\",\"more\":\"Default 20 %: before the expensive hours ZEPHYR charges up to this percentage. Only without the planner; with Dynamic Forecasting it counts as buffer.\"},\"min_price\":{\"label\":\"Minimum price\",\"help\":\"Without planner: do not deliver below this price.\",\"more\":\"E.g. € 0.25: below this price (all-in, per kWh) the battery does not deliver. Empty = no minimum.\"},\"live_off_after_restart\":{\"label\":\"Live control off after a restart (test phase)\",\"help\":\"Off (default): after a restart live control comes back on its own as soon as the P1 reports and the sets are online (if it was on). On: it stays off and you switch it on yourself.\",\"more\":\"Default off: after a restart live control comes back by itself. On only while testing, if you want to check after every restart before ZEPHYR controls the battery again.\"},\"vacation_when_away\":{\"label\":\"Vacation when nobody is home\",\"help\":\"On by itself after 24 hours with nobody home.\",\"more\":\"After 24 hours with nobody home (zone.home = 0) vacation turns on by itself: the planner then counts on low consumption. Off as soon as someone is back. Only works if phones with the HA app share their location.\"},\"workday_entity\":{\"label\":\"Workday sensor\",\"help\":\"Holidays count as weekend days.\",\"more\":\"Install the Workday integration (your country) and choose its sensor. Public holidays then count as weekend days in the consumption profile. Without a sensor Monday to Friday are workdays.\"},\"curtail_negative\":{\"label\":\"Surplus solar at a negative price\",\"help\":\"What happens to surplus solar when the export price is below zero. Off: it is exported and costs money, the planner makes room in the battery first. Another system: an inverter limiter curtails it by itself. ZEPHYR: ZEPHYR blocks export of the sets' own panels and curtails the inverter: with the switch or with the power limit below (one of the two).\",\"more\":\"With net metering (until 2027) the export price is rarely negative. Without it, it happens on sunny afternoons in spring and summer. Choose ZEPHYR if your inverter can be limited via HA (e.g. SolarEdge via Modbus), Other system if something else already does it.\"},\"curtail_switch\":{\"label\":\"Inverter curtail switch\",\"help\":\"On while the export price is negative. Alternative to the power limit.\",\"more\":\"A switch that makes your inverter stop exporting, e.g. a template switch that sets your inverter's export limit. ZEPHYR turns it on at a negative export price and off again afterwards. Choose this or the power limit.\"},\"solar_power_entities\":{\"label\":\"Solar panel power\",\"help\":\"Power sensors (W) of inverters, added up.\",\"more\":\"Power in W of inverters not connected to a Zendure set, e.g. AC power of SolarEdge; several are added up. Not the PV of the Zendure set itself: ZEPHYR already reads that. Empty: ZEPHYR estimates it from the solar counter (coarser, lags behind).\"},\"curtail_number\":{\"label\":\"Inverter power limit\",\"help\":\"Number entity that limits the inverter's power in % (e.g. SolarEdge Modbus active power limit). Only with ZEPHYR curtails.\",\"more\":\"E.g. Active power limit of the SolarEdge Modbus integration (a number in %). ZEPHYR sets it every 10 s so the inverter only produces what house and battery take, and back to 100 % afterwards. Needs: the rated power below and the solar power (Sources).\"},\"curtail_inverter_w\":{\"label\":\"Inverter rated power\",\"help\":\"Rated AC power of that inverter (W), to turn the wanted production into a %. 0 = not set.\",\"more\":\"The AC power on the rating plate, e.g. 5000 W for a SolarEdge SE5K, 3680 W for an SE3680H.\"},\"calibration_days\":{\"label\":\"Calibration after days\",\"help\":\"After this many days without 100 % the planner charges the battery full and lets the set calibrate.\",\"more\":\"Default 21 days; 0 = off. The longer the battery has not been full, the further the packs drift apart. From half of these days the planner looks for a cheap moment or sun to charge to full; on the last day it must. ZEPHYR then does not deliver until the set has finished calibrating (max. 2 hours).\"},\"price_forecast_entity\":{\"label\":\"Price forecast (jeroen.nl)\",\"help\":\"Optional: the sensor of ha-jeroen-nl, to look past the known prices.\",\"more\":\"Install the HACS integration ha-jeroen-nl with your own jeroen.nl API key and choose its price sensor here. ZEPHYR reads only that sensor and never fetches anything from jeroen.nl itself. Only forecast quarters after the last known Nord Pool price are used; Nord Pool always leads. Source: jeroen.nl.\"},\"price_forecast_mode\":{\"label\":\"Use in the plan\",\"help\":\"Indicative: the plan stays the same. Take into account: the planner plans with the forecast.\",\"more\":\"Indicative: the diagnostics compare the plan with and without the forecast. Take into account: the planner also looks at the forecast days (by default: the day after the known prices, so after about 13:00 the day after tomorrow). The level of the forecast can be off, the trend is usually clear; with the value Low the planner stays careful. Blocks on forecast quarters stay indicative and do not count in the totals. The stored forecasts give a backtest after about 6 weeks.\"},\"price_forecast_days\":{\"label\":\"Forecast days\",\"help\":\"How many days past the last known price.\",\"more\":\"Default 1: before about 13:00 the forecast stands in for tomorrow; after that it adds the day after tomorrow. 0 = only store the forecast for the quality figures.\"},\"price_forecast_value\":{\"label\":\"Value from the band\",\"help\":\"Low is careful: no charging on an optimistic guess.\",\"more\":\"jeroen.nl gives an 80 % band (p10–p90). Low uses p10 for buying and selling, so the planner does not charge for, or hold energy for, a peak that may not come. Middle uses the expected value.\"}},\"restarting\":\"ZEPHYR is restarting with the new settings…\",\"pending\":\"{n} changes not saved yet · ZEPHYR restarts briefly\",\"pending_one\":\"1 change not saved yet · ZEPHYR restarts briefly\",\"cancel\":\"Cancel\",\"save_restart\":\"Save and restart\",\"saving\":\"Saving…\",\"saved\":\"saved\",\"not_saved\":\"not saved\",\"reset\":\"Restore standard\",\"clear\":\"Clear\",\"remove\":\"Remove\",\"choose_entity\":\"Choose or type an entity\",\"actions\":{\"heating\":\"running\",\"cooling\":\"running\",\"drying\":\"running\",\"fan\":\"running\",\"preheating\":\"running\",\"defrosting\":\"defrosting\",\"idle\":\"idle\",\"off\":\"off\"},\"errors\":{\"out_of_range\":\"Outside the limits.\",\"off_step\":\"Does not fit the step size.\",\"not_a_number\":\"Not a number.\",\"not_a_bool\":\"Invalid value.\",\"required\":\"May not be empty.\",\"unknown_choice\":\"Unknown choice.\",\"choose_one\":\"Choose at least one mode. To switch off: clear the counter.\",\"not_an_entity\":\"This kind of entity does not fit here.\",\"entity_missing\":\"Entity not found.\",\"unknown_key\":\"Unknown setting.\",\"p1_missing\":\"Choose a P1 sensor.\",\"p1_pair_incomplete\":\"Choose both the import and the export sensor.\",\"p1_pair_same\":\"Import and export must be two different sensors.\",\"excluded_needs_counter\":\"The climate entity only works together with the air conditioner's energy counter. Choose the counter or clear the climate entity.\",\"failed\":\"Saving failed. Please try again.\",\"range\":\"Choose a value from {min} to {max}{unit}.\",\"entity_domain\":\"This field expects a {domain} entity\"},\"vac_active\":\"On vacation\",\"vac_home\":\"At home\",\"vac_off\":\"The planner uses the normal use.\",\"vac_until\":\"Until {until}. Until then the planner uses the use while away and charges in time for the return.\",\"vac_open\":\"Without an end date; switch it off when you are back.\",\"vac_auto\":\"On by itself since {since}: nobody has been home for 24 hours (option below). Goes off as soon as someone comes home.\",\"vac_until_label\":\"Back on\",\"vac_start\":\"Start vacation\",\"vac_stop\":\"End vacation\",\"vac_help\":\"During a vacation the planner uses the standby use and learns it apart; the normal use profile stays clean. An end date is optional.\",\"house_note\":\"When you usually run your appliances. One tap under Prices and plan lets ZEPHYR pick the cheapest start within this window. Add a new appliance with a smart plug via Devices & services → ZEPHYR → Add appliance. Changing the window reloads ZEPHYR briefly.\",\"house_floor\":\"Floor\",\"save\":\"Save\",\"discard\":\"Cancel\",\"floors\":{\"attic\":\"Attic\",\"first\":\"First floor\",\"ground\":\"Ground floor\",\"shed\":\"Shed\",\"outside\":\"Outside\"},\"appl_learned\":\"learned from {n} runs\",\"appl_default\":\"standard profile\",\"appl_airco\":\"not from the battery (Corrections)\",\"appl_from\":\"Not before\",\"appl_until\":\"Done by\",\"appl_shown\":\"Show on Power\",\"appl_after\":\"Always after the washing\",\"appl_after_help\":\"plan the dryer along (once, after the last wash) when you plan the washing\",\"curtail_head\":\"Inverter outside the sets (choose one)\",\"curtail_rated_missing\":\"Fill in the rated power, or ZEPHYR does not limit.\",\"sections\":{\"meter\":\"Meter\",\"prices\":\"Prices\",\"solar\":\"Solar\",\"counters\":\"Counters\",\"plan\":\"Plan\",\"curtail\":\"Curtail\"},\"group_sub\":{\"battery\":\"min, max, calibration\",\"tariffs\":\"supplier, tax, VAT\",\"corrections\":\"air conditioner\",\"vacation\":\"nobody home\",\"house\":\"picture, floors, appliances\",\"zero_meter\":\"expensive hours, reserve\",\"testing\":\"live after restart\"}}"),
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
			}
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
				test: "write test",
				grid_reverse: "export block"
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
			profile_empty_weekend: "No weekend days learned yet. Until then the planner uses the mean for every hour on Saturday and Sunday ({mean} kWh).",
			check_title: "Plan against reality",
			check_intro: "What the plan of the evening before expected, next to what happened. Last {n} whole days; only quarters that had a plan.",
			check_none: "No whole day with a plan from the day before yet. This fills from tomorrow.",
			check_expected: "Expected",
			check_actual: "Measured",
			check_diff: "Difference",
			check_daily: "Mean miss per day",
			check_per_day: "Per day: {metric}",
			check_partial: "{n} of {of} quarters with a plan",
			m_load: "House use",
			m_solar: "Solar",
			m_import: "Import",
			m_export: "Export",
			m_cost: "Cost",
			energy_title: "Energy counters",
			energy_sub: "ZEPHYR's own counters per set (kWh since the start), with what was filled in after a gap",
			energy_charged: "Charged",
			energy_discharged: "Delivered",
			energy_solar: "Solar",
			energy_estimated: "Estimated",
			energy_failed: "Failed reads",
			energy_total: "Total",
			energy_open: "Set unreachable since {since}: filled in once it is back.",
			energy_open_restart: "Restart since {since}: filled in at the first report.",
			energy_gaps: "Latest gaps",
			energy_no_gaps: "No gaps: the counters ran without a break.",
			energy_m_none: "nothing to fill in",
			energy_m_interpolate: "interpolated",
			energy_m_soc: "from the state of charge",
			energy_restart: "restart",
			energy_nothing: "0 kWh",
			energy_note: "Estimated = filled in after a gap (interpolated for short gaps, else from the change in state of charge). Failed reads count since ZEPHYR started.",
			peaks_title: "Short peaks",
			peaks_line: "Short peaks from the grid: today {today} ({n}×), on average {mean} per day",
			peaks_info: "ZEPHYR does not follow sudden rises of more than 800 W (like a boiling-water tap) for the first 10 s. That saves writes and back-and-forth; this energy comes from the grid.",
			peaks_bars: "Short peaks per day, last 14 days",
			peaks_note: "After a restart of HA this series starts again.",
			appl_title: "Appliance profiles",
			appl_empty: "No appliances yet. Add them in Devices & services → ZEPHYR → Add appliance.",
			appl_learned: "learned from {n} runs",
			appl_default: "standard profile",
			appl_per_run: "{kwh} and {time} per run",
			appl_plug: "with plug",
			appl_noplug: "without plug",
			appl_running: "Running now",
			appl_chart: "Power per minute of a run, up to {max} W",
			appl_max: "max {w} W",
			kind_washer: "washing machine",
			kind_dryer: "dryer",
			kind_dishwasher: "dishwasher",
			kind_other: "other",
			sec_planner: "Planner",
			sec_measure: "Measurement and set",
			sec_log: "Log",
			energy_gaps_all: "Show all {n} gaps",
			energy_gaps_less: "Show fewer"
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
			incomplete: "{n} of {total} quarters without data; the amounts are then too low.",
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
			bf_ez_failed: "EnergyZero gave no prices for {n} day(s); try again later.",
			estimated: "{n} of {total} quarters estimated (HA was off, the set was briefly unreachable or the price was missing).",
			estimated_price: "Of these, {n} with a provisional price; it is replaced as soon as the real one is known.",
			title_solar: "Savings from solar and battery",
			without_both: "Without solar and battery",
			sun_group: "Solar",
			sun_direct: "Solar used directly",
			sun_direct_help: "solar the house used straight away, instead of buying power.",
			sun_export: "Solar exported",
			sun_export_help: "Solar that went to the grid; until 2027 worth almost as much as import, plus a 10 % bonus by day.",
			sun_bonus: "Of which solar bonus {euro}.",
			sun_after_saldering: "From 1-1-2027 export only earns the market price + margin + bonus.",
			battery_group: "Battery",
			sun_total: "solar",
			self_consumption: "used yourself",
			note_solar: "Solar = what you would have paid more without solar panels: direct use at the buy price and export at the export price.",
			battery_only: "Battery only",
			day_split: "solar {sun}, battery {bat}",
			day_estimated: "partly estimated",
			leg_sun: "Solar",
			leg_estimated: "Partly estimated",
			bf_soc: "Battery state of charge (%)",
			bf_warn_pv: "Note: these counters belong to another Zendure integration and include the panels on the set; in summer that solar then counts as battery."
		},
		flow: {
			title: "Now",
			solar: "Solar",
			house: "House",
			airco: "of which air con {w}",
			none: "none",
			balanced: "at zero",
			shadow_chip: "Shadow",
			s_idle: "Hardly any power is flowing now.",
			s_solar_house: "solar {w} to the house",
			s_solar_battery: "solar {w} to the battery",
			s_export: "{w} export",
			s_grid_house: "grid {w} to the house",
			s_grid_battery: "grid {w} to the battery",
			s_battery_house: "battery {w} to the house",
			grid: "Grid",
			grid_in: "Import",
			grid_out: "Export",
			charging: "Battery charging",
			delivering: "Battery delivering",
			battery: "Battery",
			estimated: "estimated",
			curtailed: "Curtailed to {pct} %",
			inverter_off: "Inverter off",
			export_blocked: "Export blocked"
		},
		stroom: {
			zero_title: "Zero on the meter today",
			zero_sub: "Time the meter stayed within ±{band} W of its target while ZEPHYR was steering",
			zero_empty: "ZEPHYR has not steered to zero yet today.",
			zero_shadow: "ZEPHYR is not steering (shadow): no score.",
			zero_good: "good · goal {goal}",
			zero_low: "below the goal of {goal}",
			zero_in: "within ±{band} W",
			zero_import: "import",
			zero_export: "export",
			zero_idle: "not at zero (charging, holding, shadow)",
			zero_strip: "Per 5 minutes: within the band, import, export or not at zero",
			zero_imported: "Imported while steering",
			zero_exported: "Exported while steering",
			zero_mean: "Mean deviation",
			routes_title: "Energy per route today",
			routes_sub: "Where the power came from and went, 00:00–{until} (estimated per quarter)",
			routes_none: "No closed quarter yet today.",
			src_solar: "Solar",
			src_grid: "Grid",
			src_battery: "Battery",
			to_house: "house",
			to_battery: "battery",
			to_grid: "grid",
			self_use: "Solar used yourself",
			own_source: "House from own sources",
			grid_battery_price: "Grid → battery, avg price",
			airco_title: "Air con today",
			airco_sub: "Counts in the house, but the battery does not feed it",
			airco_share: "{share} of the house use",
			airco_fed: "Fed by",
			airco_cost: "Air con power from the grid",
			airco_price: "Avg price",
			reg_title: "Regulation · last 10 minutes",
			reg_sub: "Whether ZEPHYR corrects fast enough and the battery does what it is asked",
			reg_empty: "No samples since the start yet.",
			reg_p1: "P1 against target (import +)",
			reg_battery: "Battery (+ charging, − delivering)",
			reg_ago: "−{m} min",
			reg_now: "now",
			reg_dev: "P1 against target",
			reg_sp: "asked of the battery",
			reg_bat: "battery actual",
			reg_idle: "not at zero",
			reg_shadow: "shadow: ZEPHYR is not steering",
			reg_recovery: "Recovery after a peak (median)",
			reg_seconds: "{s} s",
			reg_follow: "Battery follows, avg difference",
			reg_peaks: "Peaks > 150 W",
			devices_title: "Consumers today",
			devices_sub: "Per appliance with its own plug or meter (kWh, 00:00–now)",
			rest: "Rest of the house",
			airco_not_battery: "Air con not from the battery",
			airco_fed_line: "solar {solar} · grid {grid}",
			house_total: "House total",
			devices_hint: "Add appliances with a smart plug via Devices & services → ZEPHYR → Add appliance.",
			kind_airco: "Air con",
			kind_washer: "Washing machine",
			kind_dishwasher: "Dishwasher",
			kind_dryer_heat_pump: "Dryer",
			kind_dryer_condenser: "Dryer",
			kind_other: "Appliance"
		},
		appl: {
			title: "Plan appliances",
			running: "Running now",
			today: "today",
			tomorrow: "tomorrow",
			calculating: "working out the best start…",
			tap: "Tap to plan",
			per_run: "~{euro} per run",
			start: "start",
			and: "and",
			after_wash: "after the washing",
			cheaper: "{euro} cheaper than now",
			tap_plan: "Plan",
			tap_more: "Plan one more",
			tap_clear: "Clear"
		},
		house: {
			title: "Now",
			sub: "Power in and around the house",
			roof: "Solar panels (roof)",
			shed_solar: "Solar panels (shed)",
			battery: "Battery",
			charging: "Charging",
			delivering: "Delivering",
			idle: "Idle",
			ev: "Charger",
			grid: "Grid",
			import: "Import",
			export: "Export",
			rest: "Other",
			sun: "Solar",
			production: "(production)",
			charging_l: "(charging)",
			delivering_l: "(delivering)",
			idle_l: "(idle)",
			consumers: "Consumers",
			house: "(house)",
			ev_sub: "(electric car)",
			import_l: "(import)",
			export_t: "Grid → zero",
			export_l: "(export)",
			home: "House",
			total: "Total",
			rest_of: "of which other",
			to_battery: "→ battery",
			to_house: "→ house",
			to_grid: "→ grid",
			src_sun: "Sun",
			src_batt: "Battery",
			src_grid: "Grid",
			dst_house: "house",
			dst_battery: "battery",
			dst_grid: "grid"
		},
		picture: {
			title: "Picture on Power",
			default: "Default house",
			own: "Own picture",
			note: "Your picture stays in your own Home Assistant. JPG, PNG or WebP; ZEPHYR scales it down before uploading.",
			pick: "Pick an item and tap the picture: first where its box goes, then where its line connects.",
			step_box: "Tap where the box of {item} goes.",
			step_point: "Tap where the line of {item} connects.",
			hide: "Hide",
			show: "Show",
			reset: "Place again",
			replace: "Other picture",
			delete: "Remove picture",
			uploading: "Uploading…",
			error: "Upload failed: {msg}",
			unplaced: "Not placed yet",
			hidden: "Hidden"
		},
		version: {
			update: "Update {latest}",
			busy: "Updating…",
			update_title: "Update ZEPHYR to {latest}?",
			update_text: "Now: {running}. HACS installs the new version. Home Assistant must restart afterwards; until then {running} keeps running.",
			update_do: "Update",
			notes: "What's new",
			update_other: "v{running} · update {latest}",
			restart: "Restart needed",
			restart_title: "Restart Home Assistant?",
			restart_text: "Version {installed} is installed, but {running} is still running. After a restart of Home Assistant, {installed} runs.",
			restart_do: "Restart",
			restart_other: "v{running} · restart needed"
		}
	}
};
function et(e) {
	return e?.toLowerCase().startsWith("nl") ? "nl" : "en";
}
function F(e, t, n = {}) {
	let r = (e) => {
		let n = e;
		for (let e of t.split(".")) {
			if (typeof n != "object" || !n) return;
			n = n[e];
		}
		return typeof n == "string" ? n : void 0;
	};
	return (r($e[e]) ?? r($e.en) ?? t).replace(/\{(\w+)\}/g, (e, t) => t in n ? String(n[t]) : e);
}
// src/airco.ts
var tt = /* @__PURE__ */ new Set(["idle", "off"]);
function nt(e, t) {
	return new Intl.NumberFormat(t, {
		minimumFractionDigits: 1,
		maximumFractionDigits: 1
	}).format(e / 1e3);
}
function rt(e, t, n) {
	if (!e) return null;
	let r = e.mode === "heat" ? "heat" : e.mode === "cool" ? "cool" : null;
	if (e.active) {
		let i = e.power_w > 0 ? F(t, "airco.blocked", { kw: nt(e.power_w, n) }) : F(t, "airco.blocked_unknown");
		e.excluded_w > 0 && e.excluded_w < e.power_w - 50 && (i += ` ${F(t, "airco.kept_off", { kw: nt(e.excluded_w, n) })}`);
		let a = e.quality === "fading" || e.quality === "starting" ? F(t, "airco.estimate_more", { kwh: new Intl.NumberFormat(n, { maximumFractionDigits: 2 }).format(e.last_step_kwh || .25) }) : null;
		return {
			text: i,
			allowed: !1,
			estimate: a,
			icon: r
		};
	}
	return e.has_climate && e.mode && e.mode !== "off" && e.action && !tt.has(e.action) ? {
		text: F(t, "airco.allowed", { mode: F(t, `settings.options.${e.mode}`).toLowerCase() }),
		allowed: !0,
		estimate: null,
		icon: r
	} : null;
}
// src/plan.ts
function it(e, t) {
	return Math.max(0, Math.min(100, (e - t.lo) / (t.hi - t.lo) * 100));
}
function at(e, t, n) {
	if (!t?.length) return [];
	let r = new Map(t.map((e) => [new Date(e.start).getTime(), e])), i = [], a = [], o = () => {
		if (a.length) {
			let e = (e) => (100 - it(e, n)).toFixed(2), t = a.map(({ i: t, f: n }) => `${t + .5},${e(n.buy)}`).join(" "), r = a.map(({ i: t, f: n }) => `${t + .5},${e(n.buy_high)}`), o = a.map(({ i: t, f: n }) => `${t + .5},${e(n.buy_low)}`).reverse();
			i.push({
				line: t,
				band: [...r, ...o].join(" ")
			});
		}
		a = [];
	};
	return e.forEach((e, t) => {
		let n = r.get(new Date(e.start).getTime());
		n ? a.push({
			i: t,
			f: n
		}) : o();
	}), o(), i;
}
function ot(e, t, n) {
	if (!e?.length) return [];
	let r = new Set(t.map((e) => I(e.start, n))), i = /* @__PURE__ */ new Map();
	for (let t of e) {
		let e = I(t.start, n);
		r.has(e) || i.set(e, [...i.get(e) ?? [], t]);
	}
	return [...i.entries()].map(([e, t]) => ({
		day: e,
		avg: t.reduce((e, t) => e + t.buy, 0) / t.length,
		max: t.reduce((e, t) => t.buy > e.buy ? t : e),
		min: t.reduce((e, t) => t.buy < e.buy ? t : e)
	}));
}
var I = (e, t) => Je("en-CA", {
	year: "numeric",
	month: "2-digit",
	day: "2-digit",
	timeZone: t
}).format(new Date(e));
function st(e, t) {
	let n = [];
	for (let r of e) {
		let e = I(r.start, t);
		n[n.length - 1] !== e && n.push(e);
	}
	return n;
}
function ct(e, t, n) {
	if (t === "both") return e;
	let r = st(e, n)[t === "today" ? 0 : 1];
	return r ? e.filter((e) => I(e.start, n) === r) : [];
}
function lt(e, t, n) {
	let r = st(e, n)[t];
	return r ? e.filter((e) => I(e.start, n) === r) : [];
}
function ut(e) {
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
function dt(e, t = Date.now()) {
	let n = e.findIndex((e) => !e.past);
	if (n !== 0) return n;
	let r = new Date(e[0].start).getTime();
	return t >= r && t < r + 9e5 ? 0 : -1;
}
function ft(e) {
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
function pt(e) {
	let t = e.flatMap((e) => [e.buy, e.sell !== null && e.sell < 0 ? e.sell : null]).filter((e) => e !== null);
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
function mt(e, t) {
	let n = t.hi - t.lo, r = Math.min(e, 0), i = Math.max(e, 0);
	return {
		bottom: (r - t.lo) / n * 100,
		height: Math.max((i - r) / n * 100, .8)
	};
}
function ht(e, t, n) {
	let r = Je("en-GB", {
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
function gt(e, t) {
	let n = dt(e), r = [];
	if (n >= 0 && t !== null) r.push(`${n},${(100 - t).toFixed(1)}`);
	else if (n < 0) {
		let t = e.find((e) => !e.past && e.soc !== null);
		t && t.soc !== null && r.push(`0,${(100 - t.soc).toFixed(1)}`);
	}
	return e.forEach((e, t) => {
		!e.past && e.soc !== null && r.push(`${t + 1},${(100 - e.soc).toFixed(1)}`);
	}), r.join(" ");
}
function _t(e, t) {
	let n = dt(e), r = [], i = [];
	return e.forEach((e, t) => {
		e.past && (e.soc === null ? (i.length && r.push(i), i = []) : i.push(`${t + 1},${(100 - e.soc).toFixed(1)}`));
	}), i.length && (n >= 0 && t !== null && i[i.length - 1].startsWith(`${n},`) && i.push(`${n},${(100 - t).toFixed(1)}`), r.push(i)), r.filter((e) => e.length > 1).map((e) => e.join(" "));
}
function vt(e, t) {
	let n = new Date(t).getTime();
	return e.filter((e) => new Date(e.end).getTime() > n);
}
function yt(e, t, n, r, i) {
	let a = vt(e, n);
	if (t === "both") return a;
	let o = t === "today" ? I(n, i) : r;
	return o ? a.filter((e) => {
		let t = I(e.start, i), n = I((/* @__PURE__ */ new Date(new Date(e.end).getTime() - 1)).toISOString(), i);
		return t <= o && o <= n;
	}) : [];
}
function bt(e) {
	if (!e.some((e) => e.solar !== null)) return null;
	let t = Math.max(.05, ...e.map((e) => e.solar ?? 0));
	return e.map((e) => {
		let n = e.solar ?? 0, r = (e.load ?? 0) + (e.excluded ?? 0) + (e.appliances ?? 0);
		return {
			height: n > 0 ? Math.round(n / t * 1e3) / 10 : 0,
			past: e.past,
			over: n > 0 && e.load !== null && n > r
		};
	});
}
function xt(e, t) {
	return e <= .005 ? null : Math.round((t - e) / e * 100);
}
function St(e, t) {
	if (!e.length) return [];
	let n = new Date(e[0].start).getTime(), r = e.length, i = [], a = [];
	for (let e of [...t].sort((e, t) => e.start.localeCompare(t.start))) {
		let t = (new Date(e.start).getTime() - n) / 9e5, o = Math.max(.5, e.minutes / 15);
		if (t + o <= 0 || t >= r) continue;
		let s = Math.max(0, t), c = Math.min(r, t + o), l = a.findIndex((e) => e <= s);
		l < 0 && (l = a.length), a[l] = c, i.push({
			name: e.name,
			fixed: e.fixed,
			left: s,
			width: c - s,
			row: l
		});
	}
	return i;
}
function Ct(e, t) {
	let n = e.filter((e) => !e.past && e.sell !== null && e.sell < 0);
	if (!n.length) return null;
	let r = st(e, t)[0], i = n.some((e) => I(e.start, t) === r), a = n.some((e) => I(e.start, t) !== r);
	return {
		hours: n.length / 4,
		cost: n.reduce((e, t) => e + (t.export_cost ?? 0), 0),
		when: i && a ? "both" : i ? "today" : "tomorrow"
	};
}
// src/theme.ts
var wt = s`
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
    --z-import: #c62828;
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
    --z-import: #ff7a7a;
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
function L(e) {
	switch (e) {
		case "charge": return "var(--z-charge)";
		case "deliver": return "var(--z-deliver)";
		case "export": return "var(--z-export)";
		case "hold": return "repeating-linear-gradient(45deg, var(--z-hold-a) 0 3px, var(--z-hold-b) 3px 6px)";
		default: return "var(--z-muted)";
	}
}
// \0@oxc-project+runtime@0.156.0/helpers/esm/decorate.js
function R(e, t, n, r) {
	var i = arguments.length, a = i < 3 ? t : r === null ? r = Object.getOwnPropertyDescriptor(t, n) : r, o;
	if (typeof Reflect == "object" && typeof Reflect.decorate == "function") a = Reflect.decorate(e, t, n, r);
	else for (var s = e.length - 1; s >= 0; s--) (o = e[s]) && (a = (i < 3 ? o(a) : i > 3 ? o(t, n, a) : o(t, n)) || a);
	return i > 3 && a && Object.defineProperty(t, n, a), a;
}
// src/prices-plan.ts
var Tt = "zephyr.period", Et = (e, t) => Ye(t, { maximumFractionDigits: 2 }).format(e), Dt = [
	["today", "plan.today"],
	["tomorrow", "plan.tomorrow"],
	["both", "plan.both"]
];
function Ot() {
	try {
		let e = window.localStorage.getItem(Tt);
		return e === "tomorrow" || e === "both" ? e : "today";
	} catch {
		return "today";
	}
}
var z = class extends T {
	constructor(...e) {
		super(...e), this.uiLang = "en", this.locale = "en", this.timeZone = "UTC", this.narrow = !1, this.runs = [], this.period = Ot(), this.sel = null, this.scrolledFor = "";
	}
	tr(e, t = {}) {
		return F(this.uiLang, e, t);
	}
	pick(e) {
		this.period = e, this.dispatchEvent(new CustomEvent("zephyr-period", {
			detail: e,
			bubbles: !0,
			composed: !0
		})), this.sel = null, this.scrolledFor = "";
		try {
			window.localStorage.setItem(Tt, e);
		} catch {}
	}
	updated(e) {
		let t = this.renderRoot.querySelector(".scroll"), n = this.visible(), r = `${this.period}|${this.view?.now ?? ""}`;
		if (!t || t.scrollWidth <= t.clientWidth || this.scrolledFor === r) return;
		this.scrolledFor = r;
		let i = dt(n);
		i > 0 && (t.scrollLeft = Math.max(0, i - 8) / n.length * t.scrollWidth);
	}
	visible() {
		return this.view ? ct(this.view.quarters, this.period, this.timeZone) : [];
	}
	render() {
		let e = this.view;
		if (!e) return b`<section class="card">
        <div class="skeleton" aria-hidden="true"></div>
      </section>`;
		let t = this.visible(), n = lt(e.quarters, 0, this.timeZone), r = lt(e.quarters, 1, this.timeZone), i = ut(n), a = ut(r), o = dt(e.quarters), s = o >= 0 ? e.quarters[o] : void 0, c = this.period === "today" ? "plan.title_today" : this.period === "tomorrow" ? "plan.title_tomorrow" : "plan.title_both";
		return b`<section class="card" aria-label=${this.tr("plan.title")}>
      <div class="head">
        <h2>${this.tr("plan.title")} · ${this.tr(c)}</h2>
        <div class="tabs" role="group" aria-label=${this.tr("plan.period")}>
          ${Dt.map(([e, t]) => b`<button
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
          <span class="cap"
            >${this.tr("plan.now", { time: s ? M(s.start, this.locale, this.timeZone) : "–" })}</span
          >
          <span class="value"
            >${s?.buy == null ? "–" : O(s.buy, this.locale)}</span
          >
          <span class="sub">${this.tr("plan.per_kwh")}</span>
        </div>
        ${this.statCell(n, i, "plan.today")}
        ${this.statCell(r, a, "plan.tomorrow", !0)}
      </div>
      ${this.notes(e, a)}${this.forecastNotes(e, t)}
      ${t.length ? this.chart(t) : b`<p class="empty">${this.tr("plan.no_quarters")}</p>`}
      ${this.legend(t)}
      <slot></slot>
    </section>`;
	}
	spreadText(e) {
		let t = e.max.buy, n = xt(e.avg, t);
		return n === null ? this.tr("plan.spread", { value: O(t - e.avg, this.locale) }) : this.tr("plan.spread", { value: `${n} %` });
	}
	statCell(e, t, n, r = !1) {
		let i = e.length ? N(e[0].start, this.locale, this.timeZone) : "";
		if (!t) return b`<div class="cell">
        <span class="cap">${this.tr(n)} · ${i}</span>
        <span class="value small">${this.tr("plan.unknown")}</span>
        <span class="sub">${r ? this.tr("plan.expected_at") : ""}</span>
      </div>`;
		let a = r && this.view?.tomorrow_known_at ? ` · ${this.tr("plan.known_at", { time: M(this.view.tomorrow_known_at, this.locale, this.timeZone) })}` : "";
		return b`<div class="cell">
      <span class="cap">${this.tr(n)} · ${i}</span>
      <span class="value"
        >${O(t.min.buy, this.locale)} –
        ${O(t.max.buy, this.locale)}<span
          class="spread"
          title=${this.tr("plan.spread_title")}
          >${this.spreadText(t)}</span
        ></span
      >
      <span class="sub"
        >${this.tr("plan.stats", {
			avg: O(t.avg, this.locale),
			low: M(t.min.start, this.locale, this.timeZone),
			high: M(t.max.start, this.locale, this.timeZone)
		})}${a}</span
      >
    </div>`;
	}
	notes(e, t) {
		let n = [];
		e.state === "no_prices" && n.push(b`<p class="note warn">${this.tr("plan.no_prices")}</p>`), e.state === "price_reserve" && n.push(b`<p class="note">${this.tr("plan.reserve")}</p>`), !t && this.period !== "today" && n.push(b`<p class="note">${this.tr("plan.indicative")}</p>`);
		let r = e.curtail_mode === "curtail_off" ? Ct(e.quarters, this.timeZone) : null;
		return r && r.cost >= .01 && n.push(b`<p class="note warn negnote">
          ${this.tr(`plan.neg_${r.when}`, {
			hours: Et(r.hours, this.locale),
			euro: O(r.cost, this.locale)
		})}
          <button
            type="button"
            class="link"
            @click=${() => this.dispatchEvent(new CustomEvent("zephyr-open-settings", {
			detail: "planner:curtail",
			bubbles: !0,
			composed: !0
		}))}
          >
            ${this.tr("plan.neg_link")}
          </button>
        </p>`), n.length ? b`${n}` : C;
	}
	forecastNotes(e, t) {
		let n = e.price_forecast;
		if (!n || !n.slots.length) return C;
		let r = [], i = n.slots.reduce((e, t) => t.buy > e.buy ? t : e), a = `${N(i.start, this.locale, this.timeZone)} ${M(i.start, this.locale, this.timeZone)}`, o = this.tr("plan.fc_peak", {
			when: a,
			price: O(i.buy, this.locale),
			low: O(i.buy_low, this.locale),
			high: O(i.buy_high, this.locale)
		}), s = n.compare;
		n.mode === "indicative" && s?.first_action_differs && r.push(b`<p class="note">
          ${this.tr("plan.fc_would", { action: this.tr(`plan.fc_action_${s.action_with}`) })} ${o}
        </p>`), n.mode === "use" && r.push(b`<p class="note">${this.tr("plan.fc_used")} ${o}</p>`);
		for (let e of ot(n.slots, t, this.timeZone)) r.push(b`<p class="note">
          ${this.tr("plan.fc_day", {
			day: N(e.max.start, this.locale, this.timeZone),
			avg: O(e.avg, this.locale),
			high: O(e.max.buy, this.locale),
			at: M(e.max.start, this.locale, this.timeZone),
			low: O(e.min.buy, this.locale),
			lowat: M(e.min.start, this.locale, this.timeZone)
		})}
        </p>`);
		return r.push(b`<p class="note source">
        <span class="swf" aria-hidden="true"></span>${this.tr("plan.fc_source")}
        <a href=${n.source.url} target="_blank" rel="noreferrer">${n.source.name}</a>
      </p>`), b`${r}`;
	}
	chart(e) {
		let t = e.length, n = pt(e), r = dt(e), i = (e) => `${(e / t * 100).toFixed(3)}%`, a = st(e, this.timeZone), o = a.length > 1 ? new Date(lt(e, 1, this.timeZone)[0].start).getTime() : null, s = o === null ? -1 : e.findIndex((e) => new Date(e.start).getTime() >= o), c = [];
		for (let t = 0; t < a.length; t++) {
			let n = ut(lt(e, t, this.timeZone));
			n && (c.push({
				q: n.min,
				i: e.indexOf(n.min),
				kind: "plan.lowest"
			}), c.push({
				q: n.max,
				i: e.indexOf(n.max),
				kind: "plan.highest"
			}));
		}
		let l = ht(e, this.period === "both" ? 6 : 3, this.timeZone), u = this.sel !== null && this.sel < t ? this.sel : null, d = gt(e, this.view?.soc_now ?? null), f = _t(e, this.view?.soc_now ?? null), p = n.lo < 0 ? (0 - n.lo) / (n.hi - n.lo) * 100 : null;
		return b`<div class="scroll">
      <div class="chart ${t > 100 ? "wide" : ""}">
        <div class="axis left" aria-hidden="true">
          <span>${O(n.hi, this.locale)}</span
          ><span>${O((n.hi + n.lo) / 2, this.locale)}</span
          ><span>${O(n.lo, this.locale)}</span>
        </div>
        <div class="axis right" aria-hidden="true">
          <span>100 %</span><span>50 %</span><span>0 %</span>
        </div>
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
          ${p === null ? C : b`<div class="zero" style="bottom:${p}%"></div>`}
          ${e.map((e, t) => {
			if (e.buy === null) return C;
			let a = mt(e.buy, n), o = `bar${e.past ? " past" : ""}${e.indicative ? " ind" : ""}${t === r ? " cur" : ""}${t === u ? " focus" : ""}`, s = e.sell !== null && e.sell < 0 ? mt(e.sell, n) : null;
			return b`<div
                class=${o}
                style="left:${i(t)};width:${i(1)};bottom:${a.bottom}%;height:${a.height}%"
              ></div>
              ${s ? b`<div class=${`neg${e.past ? " past" : ""}`} style="left:${i(t)};width:${i(1)};bottom:${s.bottom}%;height:${s.height}%"></div>` : C}
              ${(e.curtail_kwh ?? 0) > 0 ? b`<span class="cut" style="left:${i(t + .5)}" title=${this.tr("plan.curtail_mark")}></span>` : C}`;
		})}
          <svg
            viewBox="0 0 ${t} 100"
            preserveAspectRatio="none"
            aria-hidden="true"
          >
            ${at(e, this.view?.price_forecast?.slots, n).map((e) => x`<polygon class="fband" points=${e.band}></polygon><polyline class="fline" points=${e.line}></polyline>`)}
            ${f.map((e) => x`<polyline class="halo" points=${e}></polyline><polyline class="soc measured" points=${e}></polyline>`)}
            ${d ? x`<polyline class="halo" points=${d}></polyline><polyline class="soc" points=${d}></polyline>` : C}
          </svg>
          ${s > 0 ? b`<div class="split" style="left:${i(s)}"></div>
                  <span class="dayname" style="left:calc(${i(s)} + 6px)"
                    >${N(e[s].start, this.locale, this.timeZone)}</span
                  >` : C}
          ${c.map(({ q: e, i: r }) => {
			let i = Math.min(94, Math.max(6, (r + .5) / t * 100)), a = mt(e.buy, n);
			return b`<span
              class="mark"
              style="left:${i}%;bottom:calc(${a.bottom + a.height}% + 6px)"
              >${O(e.buy, this.locale)} ·
              ${M(e.start, this.locale, this.timeZone)}</span
            >`;
		})}
          ${r >= 0 ? b`<div class="nowline" style="left:${i(r)}"></div>
                  <span class="nowpill" style="left:${i(r)}"
                    >${this.tr("plan.now_short")}</span
                  >` : C}
          ${u === null ? C : this.tooltip(e[u], u, t)}
        </div>
        <div class="band" aria-hidden="true">
          ${ft(e).map((e) => b`<div
                class=${e.past ? "seg past" : "seg"}
                style="flex:${e.count} 1 0;background:${e.action ? L(e.action) : "transparent"}"
              ></div>`)}
        </div>
        ${this.sun(e)} ${this.runLane(e)}
        <div class="ticks" aria-hidden="true">
          ${l.map((t) => b`<span style="left:${i(t)}">${M(e[t].start, this.locale, this.timeZone)}</span>`)}
        </div>
      </div>
    </div>`;
	}
	runLane(e) {
		let t = St(e, this.runs);
		if (!t.length) return C;
		let n = e.length;
		return b`<div
      class="runlane"
      style="height:${(Math.max(...t.map((e) => e.row)) + 1) * 20}px"
      aria-label=${this.tr("plan.runs_label")}
    >
      ${t.map((e) => b`<div
            class="run"
            style="left:${(e.left / n * 100).toFixed(3)}%;width:${(e.width / n * 100).toFixed(3)}%;top:${e.row * 20}px"
            title=${e.name}
          >
            ${e.fixed ? "🔒 " : ""}${e.name}
          </div>`)}
    </div>`;
	}
	sun(e) {
		let t = bt(e);
		return t ? b`<div class="sunlane" aria-hidden="true">
      ${t.map((e) => b`<div class="sq">
            ${e.height > 0 ? b`<i class=${`${e.past ? "" : "fut"}${e.over ? " over" : ""}`} style="height:${e.height}%"></i>` : C}
          </div>`)}
    </div>` : C;
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
		return b`<div class="tip" role="status" style=${i}>
      <strong
        >${N(e.start, this.locale, this.timeZone)}
        ${M(e.start, this.locale, this.timeZone)}</strong
      >
      ${e.buy === null ? b`<span>${this.tr("plan.unknown")}</span>` : b`<span
                >${this.tr("plan.tip_buy", { price: O(e.buy, this.locale) })}</span
              >
              <span class=${e.sell !== null && e.sell < 0 ? "negtext" : ""}
                >${this.tr("plan.tip_sell", { price: O(e.sell, this.locale) })}</span
              >
              ${(e.curtail_kwh ?? 0) > 0 ? b`<span
                      >${this.tr("plan.tip_curtail", {
			price: O(e.sell, this.locale),
			kwh: A(e.curtail_kwh ?? 0, this.locale, 1)
		})}</span
                    >` : (e.export_cost ?? 0) > 0 ? b`<span
                        >${this.tr("plan.tip_export_cost", { euro: O(e.export_cost ?? 0, this.locale) })}</span
                      >` : C}`}
      ${a ? b`<span>${a}</span>` : C}
      ${e.soc === null ? C : b`<span>${this.tr(e.past ? "plan.tip_soc_past" : "plan.tip_soc", { soc: j(e.soc, this.locale) })}</span>`}
      ${e.solar !== null && e.load !== null ? b`<span
              >${this.tr(e.past ? "plan.tip_energy_past" : "plan.tip_energy", {
			solar: A(e.solar, this.locale, 2),
			load: A(e.load, this.locale, 2)
		})}</span
            >` : C}
      ${e.excluded ? b`<span>${this.tr("plan.tip_airco", { kwh: A(e.excluded, this.locale, 2) })}</span>` : C}
      ${e.appliances ? b`<span>${this.tr("plan.tip_appliances", { kwh: A(e.appliances, this.locale, 2) })}</span>` : C}
    </div>`;
	}
	summary(e) {
		let t = ut(e);
		return t ? this.tr("plan.aria", {
			low: O(t.min.buy, this.locale),
			low_time: M(t.min.start, this.locale, this.timeZone),
			high: O(t.max.buy, this.locale),
			high_time: M(t.max.start, this.locale, this.timeZone)
		}) : this.tr("plan.title");
	}
	legend(e = []) {
		let t = e.some((e) => e.sell !== null && e.sell < 0), n = (e, t, n = "sw") => b`<span class="li"
        ><span class=${n} style="background:${e}"></span
        >${this.tr(t)}</span
      >`;
		return b`<div class="legend">
      ${n("var(--z-bar)", "plan.legend_price")}
      ${n(L("charge"), "action.charge")}
      ${n(L("deliver"), "action.deliver")}
      ${n(L("hold"), "action.hold")}
      ${n(L("export"), "action.export")}
      ${n("var(--z-solar)", "plan.legend_solar")}
      ${n("var(--z-solar)", "plan.legend_solar_over", "sw over")}
      ${t ? n("var(--z-red, #d64545)", "plan.legend_negative") : C}
      <span class="li"
        ><span class="line solid"></span
        >${this.tr("plan.legend_soc_past")}</span
      >
      <span class="li"
        ><span class="line"></span>${this.tr("plan.legend_soc")}</span
      >
      <span class="li">${this.tr("plan.legend_past")}</span>
    </div>`;
	}
	static {
		this.styles = [s`
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
      .fline {
        fill: none;
        stroke: var(--z-text);
        stroke-width: 1.5px;
        stroke-dasharray: 4 3;
        vector-effect: non-scaling-stroke;
      }
      .fband {
        fill: var(--z-text);
        opacity: 0.08;
        stroke: none;
      }
      .note.source {
        display: flex;
        align-items: center;
        gap: 6px;
      }
      .swf {
        width: 18px;
        border-top: 2px dashed var(--z-text);
      }
      .bar.ind {
        background: repeating-linear-gradient(
          45deg,
          var(--z-bar) 0 3px,
          transparent 3px 6px
        );
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
      .neg {
        position: absolute;
        background: var(--z-red, #d64545);
        opacity: 0.8;
        border-radius: 0 0 2px 2px;
      }
      .neg.past {
        opacity: 0.35;
      }
      .cut {
        position: absolute;
        bottom: 2px;
        width: 10px;
        height: 10px;
        margin-left: -5px;
        border-radius: 2px;
        background:
          linear-gradient(
            135deg,
            transparent 42%,
            var(--z-red, #d64545) 42% 58%,
            transparent 58%
          ),
          var(--z-solar);
        opacity: 0.9;
      }
      .negtext {
        color: var(--z-red, #d64545);
        font-weight: 600;
      }
      .negnote {
        display: flex;
        flex-wrap: wrap;
        gap: 6px 12px;
        align-items: center;
      }
      button.link {
        border: 0;
        background: none;
        padding: 0;
        font: inherit;
        font-weight: 700;
        color: inherit;
        text-decoration: underline;
        cursor: pointer;
      }
      .runlane {
        position: relative;
        margin-top: 4px;
      }
      .run {
        position: absolute;
        height: 16px;
        border-radius: 5px;
        background: repeating-linear-gradient(
          135deg,
          color-mix(in srgb, var(--z-charge) 30%, transparent) 0 4px,
          color-mix(in srgb, var(--z-charge) 18%, transparent) 4px 8px
        );
        border: 1px solid color-mix(in srgb, var(--z-charge) 60%, transparent);
        color: var(--z-text);
        font-size: 10.5px;
        line-height: 14px;
        padding: 0 4px;
        overflow: hidden;
        white-space: nowrap;
        text-overflow: ellipsis;
        box-sizing: border-box;
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
R([E({ attribute: !1 })], z.prototype, "view", void 0), R([E({ attribute: !1 })], z.prototype, "uiLang", void 0), R([E()], z.prototype, "locale", void 0), R([E()], z.prototype, "timeZone", void 0), R([E({ type: Boolean })], z.prototype, "narrow", void 0), R([E({ attribute: !1 })], z.prototype, "runs", void 0), R([E({ attribute: !1 })], z.prototype, "period", void 0), R([D()], z.prototype, "sel", void 0), z = R([e("zephyr-prices-plan")], z);
// src/sets.ts
function kt(e, t, n) {
	return e.built_in ? F(n, "sets.built_in") : e.model ? t.filter((t) => t.model === e.model).length > 1 ? `${e.model} ${e.number}` : e.model : F(n, "sets.pack", { n: e.index + 1 });
}
function At(e, t) {
	let n = Math.max(.5, ...e.map((e) => Math.max(e.solar_battery + e.grid_battery, e.battery_house + e.battery_grid))), r = (e) => Math.round(Math.max(e, 0) / n * t * 10) / 10;
	return e.map((e) => ({
		solar: r(e.solar_battery),
		grid: r(e.grid_battery),
		house: r(e.battery_house),
		export: r(e.battery_grid)
	}));
}
var jt = (e) => e <= 30 ? "good" : e <= 100 ? "balancing" : "imbalance";
function Mt(e) {
	let t = e.flatMap((e) => e.packs), n = t.map((e) => e.soc), r = e.map((e) => e.enclosure_temp).filter((e) => e !== null), i = null;
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
				status: jt(t)
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
		inverter: r.length ? Math.max(...r) : null,
		now: i,
		lastDay: a,
		imbalance: s,
		notFull: !i && !c,
		offline: e.filter((e) => !e.online)
	};
}
var B = class extends T {
	constructor(...e) {
		super(...e), this.uiLang = "en", this.locale = "en", this.timeZone = "UTC";
	}
	tr(e, t = {}) {
		return F(this.uiLang, e, t);
	}
	num(e, t = 0) {
		return new Intl.NumberFormat(this.locale, {
			minimumFractionDigits: t,
			maximumFractionDigits: t
		}).format(e);
	}
	render() {
		let e = this.view;
		if (!e) return b`<div class="card skeleton" aria-hidden="true"></div>`;
		if (!e.sets.length) return b`<section class="card">
        <p class="text">${this.tr("sets.none")}</p>
      </section>`;
		let t = Mt(e.sets);
		return b`
      ${this.renderSummary(t, e.sets)}
      ${e.sets.map((t) => b`<div class="row">
            ${this.renderSet(t, e.sets.length)} ${this.renderPacks(t)}
          </div>`)}
      ${this.days ? this.renderDays(this.days) : C}
      ${e.sets.length === 1 ? this.renderActivity(e) : C}
    `;
	}
	stat(e, t) {
		return b`<div class="stat">
      <span class="cap">${e}</span><span class="value">${t}</span>
    </div>`;
	}
	renderSummary(e, t) {
		let n = t.flatMap((e) => e.packs), r;
		r = e.offline.length ? this.tr("sets.offline_line", { sets: e.offline.map((e) => this.tr("sets.set", { n: e.number })).join(", ") }) : e.imbalance && e.imbalance.days >= 3 ? this.tr("sets.line_persistent", {
			pack: kt(e.imbalance.pack, n, this.uiLang),
			days: e.imbalance.days
		}) : e.now?.status === "imbalance" ? this.tr("sets.line_now", {
			pack: kt(e.now.pack, n, this.uiLang),
			mv: e.now.mv
		}) : e.imbalance ? this.tr("sets.line_recent", {
			pack: kt(e.imbalance.pack, n, this.uiLang),
			day: N(`${e.imbalance.lastDay}T12:00:00Z`, this.locale, this.timeZone),
			mv: e.imbalance.mv
		}) : e.notFull ? this.tr("sets.line_not_full") : this.tr("sets.line_ok");
		let i = e.now ? `${this.num(e.now.mv)} mV · ${this.tr(`sets.cell.${e.now.status}`)}` : e.lastDay ? `${this.num(e.lastDay.mv)} mV · ${this.tr(`sets.cell.${e.lastDay.status}`)}` : "–";
		return b`<section
      class="card summary"
      aria-label=${this.tr("sets.summary")}
    >
      ${this.stat(this.tr("sets.batteries"), this.tr(e.online ? "sets.all_online" : "sets.some_offline", { n: e.packs }))}
      ${this.stat(this.tr("sets.soc_spread"), e.socMin === null ? "–" : e.socMin === e.socMax ? j(e.socMin, this.locale) : `${this.num(e.socMin)}–${j(e.socMax, this.locale)}`)}
      ${this.stat(this.tr("sets.inverter"), e.inverter === null ? "–" : `${this.num(e.inverter)} °C`)}
      ${this.stat(e.now || !e.lastDay ? this.tr("sets.largest_delta") : this.tr("sets.largest_delta_day", { day: N(`${e.lastDay.day}T12:00:00Z`, this.locale, this.timeZone) }), i)}
      <p class="line"><strong>${this.tr("sets.in_short")}</strong> ${r}</p>
    </section>`;
	}
	renderSet(e, t) {
		let n = e.soc ?? 0, r = e.online ? e.status ?? "standby" : "offline", i = (e, t) => b`<div>
        <dt>${e}</dt>
        <dd>${t}</dd>
      </div>`, a = e.last_full ? P(e.last_full, Date.now(), this.timeZone) ? `${this.tr("sets.today")} ${M(e.last_full, this.locale, this.timeZone)}` : N(e.last_full, this.locale, this.timeZone) : this.tr("sets.unknown");
		return b`<article class="card set">
      <div class="head">
        <div>
          <h2>${this.tr("sets.set", { n: e.number })}</h2>
          <span class="muted"
            >${e.model}${e.packs.length ? ` · ${this.tr("sets.packs_n", { n: e.packs.length })}` : ""}${e.capacity_kwh ? ` · ${A(e.capacity_kwh, this.locale)}` : ""}</span
          >
        </div>
        <span class="chip ${r}">${this.tr(`sets.status.${r}`)}</span>
      </div>
      ${e.soc === null ? b`<p class="text">${this.tr("battery.unknown")}</p>` : b`<div class="big-row">
                <span class="big">${j(n, this.locale)}</span>
                ${e.energy_kwh !== null && e.capacity_kwh ? b`<span class="muted"
                        >${this.tr("battery.of", {
			energy: A(e.energy_kwh, this.locale),
			capacity: A(e.capacity_kwh, this.locale)
		})}</span
                      >` : C}
              </div>
              <div
                class="bar"
                role="meter"
                aria-valuemin="0"
                aria-valuemax="100"
                aria-valuenow=${Math.round(n)}
                aria-label=${this.tr("battery.title")}
              >
                <div class="fill" style="width:${n}%"></div>
                ${e.limits?.min == null ? C : b`<div class="mark" style="left:${e.limits.min}%"></div>`}
                ${e.limits?.max == null ? C : b`<div class="mark" style="left:${e.limits.max}%"></div>`}
              </div>`}
      <dl>
        ${i(this.tr("sets.power"), e.power_w === null ? "–" : Ze(e.power_w, this.locale))}
        ${e.solar_w ? i(this.tr("sets.solar"), Ze(e.solar_w, this.locale).replace("+", "")) : C}
        ${i(this.tr("sets.inverter"), e.enclosure_temp === null ? "–" : `${this.num(e.enclosure_temp)} °C`)}
        ${i(this.tr("sets.last_full"), a)}
        ${i(this.tr("sets.switches"), e.relays_24h === null ? "–" : this.tr("sets.switches_n", { n: e.relays_24h }))}
        ${i(this.tr("sets.limits"), e.limits?.min != null && e.limits?.max != null ? `${this.num(e.limits.min)}–${this.num(e.limits.max)} %` : "–")}
      </dl>
      <div class="foot">
        <span>${t >= 3 ? this.tr("sets.max_sets") : ""}</span>
        ${t < 3 ? b`<a class="button" href="/config/integrations/integration/zephyr">${this.tr("sets.add")}</a>` : C}
      </div>
    </article>`;
	}
	renderPacks(e) {
		return e.packs.length ? b`<section
      class="card packs"
      aria-label=${this.tr("sets.in_set")}
    >
      <div class="head">
        <h2>${this.tr("sets.in_set")}</h2>
        <span class="muted">${this.tr("sets.pack_power_note")}</span>
      </div>
      <div class="grid">
        ${e.packs.map((t) => {
			let n = t.cell_status;
			return b`<div class="pack ${e.online ? "" : "off"}">
            <div class="ph">
              <strong>${kt(t, e.packs, this.uiLang)}</strong
              ><span class="muted"
                >${t.capacity_kwh ? A(t.capacity_kwh, this.locale, 2) : this.tr("sets.unknown_type")}</span
              >
            </div>
            <div class="big-row">
              <span class="mid">${j(t.soc, this.locale)}</span>
              ${t.energy_kwh === null ? C : b`<span class="muted">${A(t.energy_kwh, this.locale, 2)}</span>`}
            </div>
            <div class="bar thin">
              <div class="fill" style="width:${t.soc}%"></div>
            </div>
            <dl>
              <div>
                <dt>${this.tr("sets.power")}</dt>
                <dd>${Ze(t.power_w, this.locale)}</dd>
              </div>
              <div>
                <dt>${this.tr("sets.temp")}</dt>
                <dd>${t.temp === null ? "–" : `${this.num(t.temp)} °C`}</dd>
              </div>
              <div>
                <dt>${this.tr("sets.cells")}</dt>
                <dd>
                  ${t.cell_min_v === null || t.cell_max_v === null ? "–" : `${this.num(t.cell_min_v, 2)}–${this.num(t.cell_max_v, 2)} V`}
                </dd>
              </div>
              <div>
                <dt>${this.tr("sets.cell_delta")}</dt>
                <dd class="delta">
                  ${t.cell_delta_mv === null ? "–" : `${this.num(t.cell_delta_mv)} mV`}
                  ${n ? b`<span class="tag ${n}"
                          >${this.tr(`sets.cell.${n}`)}</span
                        >` : t.cell_delta_mv === null ? C : b`<span
                            class="tag none"
                            title=${this.tr("sets.not_judged_title")}
                            >${this.tr("sets.not_judged")}</span
                          >`}
                </dd>
              </div>
            </dl>
          </div>`;
		})}
      </div>
      <p class="text small">${this.tr("sets.cell_note")}</p>
    </section>` : b``;
	}
	renderDays(e) {
		let t = At(e.days, 80), n = (e) => this.num(e, 1), r = e.days[e.days.length - 1]?.date, i = (t, n, r) => b`<div class="tr" role="row">
        <span role="rowheader" class="rh"
          >${t}${n ? b`<small>${n}</small>` : C}</span
        >
        ${e.days.map((e) => {
			let t = e.quarters ? r(e) : "–";
			return b`<span
            role="cell"
            class="cell val ${t === "–" ? "empty" : ""}"
            >${t}</span
          >`;
		})}
      </div>`, a = e.week, o = e.days[0]?.date, s = (e) => N(`${e}T12:00:00Z`, this.locale, this.timeZone), c = [
			this.tr("sets.days_week_charged", {
				kwh: n(a.charged),
				solar: n(a.solar_battery),
				grid: n(a.grid_battery)
			}),
			this.tr("sets.days_week_delivered", { kwh: n(a.delivered) }),
			a.cycles === null ? null : this.tr("sets.days_week_cycles", { n: this.num(a.cycles, 1) }),
			a.efficiency === null ? null : this.tr("sets.days_week_efficiency", { pct: j(a.efficiency * 100, this.locale) }) + (a.efficiency_days && a.efficiency_days < 7 ? ` (${this.tr("sets.days_n", { n: a.efficiency_days })})` : ""),
			a.grid_price === null ? null : this.tr("sets.days_week_price", { price: O(a.grid_price, this.locale) })
		].filter((e) => e !== null);
		return b`<section class="card" aria-label=${this.tr("sets.days_title")}>
      <div class="head">
        <h2>${this.tr("sets.days_title")}</h2>
        <div class="legend">
          <span
            ><i style="background:var(--z-solar)"></i
            >${this.tr("sets.days_solar")}</span
          >
          <span
            ><i style="background:var(--z-charge)"></i
            >${this.tr("sets.days_grid")}</span
          >
          <span
            ><i style="background:var(--z-deliver)"></i
            >${this.tr("sets.days_house")}</span
          >
          <span
            ><i style="background:var(--z-export)"></i
            >${this.tr("sets.days_export")}</span
          >
        </div>
      </div>
      <span class="muted">${this.tr("sets.days_note")}</span>
      <div class="table" role="table">
        <div class="tr" role="row">
          <span role="columnheader"></span>
          ${e.days.map((e) => b`<span role="columnheader" class="dh ${e.date === r ? "today" : ""}">${s(e.date)}</span>`)}
        </div>
        <div class="tr bars" aria-hidden="true">
          <span class="rh axis"
            ><small>${this.tr("sets.days_up")}</small
            ><small>${this.tr("sets.days_down")}</small></span
          >
          ${t.map((t, n) => b`<div class="daybar" style="--half:${80}px">
                <div class="up">
                  <i style="height:${t.solar}px;background:var(--z-solar)"></i
                  ><i style="height:${t.grid}px;background:var(--z-charge)"></i>
                </div>
                <div class="dn">
                  <i style="height:${t.house}px;background:var(--z-deliver)"></i
                  ><i
                    style="height:${t.export}px;background:var(--z-export)"
                  ></i>
                </div>
                <span class="sr">${s(e.days[n].date)}</span>
              </div>`)}
        </div>
        ${i(this.tr("sets.days_charged"), this.tr("sets.days_charged_sub"), (e) => n(e.solar_battery + e.grid_battery))}
        ${i(this.tr("sets.days_delivered"), this.tr("sets.days_delivered_sub"), (e) => n(e.battery_house + e.battery_grid))}
        ${i(this.tr("sets.days_cycles"), null, (e) => e.cycles === null ? "–" : this.num(e.cycles, 2))}
        ${i(this.tr("sets.days_soc"), this.tr("sets.days_soc_sub"), (e) => e.soc_min === null || e.soc_max === null ? "–" : `${this.num(e.soc_min)}–${j(e.soc_max, this.locale)}`)}
      </div>
      <div class="week">
        <span class="rh"
          >${this.tr("sets.days_week")}<small
            >${o && r ? `${s(o)} – ${s(r)}` : ""}</small
          ></span
        >
        <span>${c.join(" · ")}</span>
      </div>
      <p class="text small">
        ${this.tr("sets.days_explain", { usable: e.usable_kwh === null ? "–" : n(e.usable_kwh) })}
      </p>
    </section>`;
	}
	renderActivity(e) {
		let t = new Date(e.now).getTime(), n = t - 864e5, r = (e) => Math.max(0, Math.min(100, (new Date(e).getTime() - n) / (t - n) * 100)), i = {
			charge: 0,
			deliver: 0
		};
		return b`<section
      class="card"
      aria-label=${this.tr("sets.activity_title")}
    >
      <div class="head">
        <h2>${this.tr("sets.activity_title")}</h2>
        <div class="legend">
          <span
            ><i style="background:${L("charge")}"></i
            >${this.tr("action.charge")}</span
          >
          <span
            ><i style="background:${L("deliver")}"></i
            >${this.tr("action.deliver")}</span
          >
          <span
            ><i style="background:${L("hold")}"></i
            >${this.tr("action.hold")}</span
          >
        </div>
      </div>
      <div class="activity" aria-hidden="true">
        ${e.activity_24h.map((e) => {
			e.action in i && (i[e.action] += 1);
			let t = r(e.start);
			return b`<div
            title="${M(e.start, this.locale, this.timeZone)}–${M(e.end, this.locale, this.timeZone)} · ${this.tr(`action.${e.action}`)}"
            style="left:${t}%;width:${r(e.end) - t}%;background:${L(e.action)}"
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
		].map((e) => b`<span>${M(new Date(n + e * 36e5).toISOString(), this.locale, this.timeZone)}</span>`)}
        <span>${this.tr("plan.now_short")}</span>
      </div>
      ${e.activity_24h.length ? C : b`<p class="text small">${this.tr("sets.no_activity")}</p>`}
    </section>`;
	}
	static {
		this.styles = s`
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
    .cell.val {
      background: var(--z-track);
      font-weight: 400;
      font-size: 14px;
    }
    .cell.val.empty {
      color: var(--z-muted);
    }
    .cell.val {
      white-space: nowrap;
    }
    .dh.today {
      color: var(--z-text);
      font-weight: 600;
    }
    .rh small {
      display: block;
      font-size: 12px;
      font-weight: 400;
      color: var(--z-muted);
    }
    .rh.axis {
      align-self: stretch;
      display: flex;
      flex-direction: column;
      justify-content: space-around;
    }
    .daybar {
      position: relative;
      height: calc(var(--half) * 2 + 8px);
      border-top: 0;
      background: linear-gradient(var(--z-border), var(--z-border)) 0
        calc(var(--half) + 4px) / 100% 1px no-repeat;
    }
    .daybar .up,
    .daybar .dn {
      position: absolute;
      left: 25%;
      right: 25%;
      display: flex;
    }
    .daybar .up {
      bottom: calc(var(--half) + 4px);
      flex-direction: column-reverse;
    }
    .daybar .dn {
      top: calc(var(--half) + 5px);
      flex-direction: column;
    }
    .daybar i {
      display: block;
    }
    .daybar .up i:last-child {
      border-radius: 4px 4px 0 0;
    }
    .daybar .dn i:last-child {
      border-radius: 0 0 4px 4px;
    }
    .sr {
      position: absolute;
      width: 1px;
      height: 1px;
      overflow: hidden;
      clip: rect(0 0 0 0);
    }
    .week {
      display: grid;
      grid-template-columns: 130px 1fr;
      gap: 6px;
      align-items: center;
      border-top: 1px solid var(--z-border);
      padding-top: 12px;
      font-size: 14px;
    }
    @media (max-width: 600px) {
      .tr {
        grid-template-columns: 84px repeat(7, minmax(64px, 1fr));
      }
      .week {
        grid-template-columns: 1fr;
      }
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
R([E({ attribute: !1 })], B.prototype, "days", void 0), R([E({ attribute: !1 })], B.prototype, "view", void 0), R([E({ attribute: !1 })], B.prototype, "uiLang", void 0), R([E()], B.prototype, "locale", void 0), R([E()], B.prototype, "timeZone", void 0), B = R([e("zephyr-sets")], B);
// node_modules/lit-html/directive.js
var Nt = {
	ATTRIBUTE: 1,
	CHILD: 2,
	PROPERTY: 3,
	BOOLEAN_ATTRIBUTE: 4,
	EVENT: 5,
	ELEMENT: 6
}, Pt = (e) => (...t) => ({
	_$litDirective$: e,
	values: t
}), Ft = class {
	constructor(e) {}
	get _$AU() {
		return this._$AM._$AU;
	}
	_$AT(e, t, n) {
		this._$Ct = e, this._$AM = t, this._$Ci = n;
	}
	_$AS(e, t) {
		return this.update(e, t);
	}
	update(e, t) {
		return this.render(...t);
	}
}, It = class extends Ft {
	constructor(e) {
		if (super(e), this.it = C, e.type !== Nt.CHILD) throw Error(this.constructor.directiveName + "() can only be used in child bindings");
	}
	render(e) {
		if (e === C || e == null) return this._t = void 0, this.it = e;
		if (e === S) return e;
		if (typeof e != "string") throw Error(this.constructor.directiveName + "() called with a non-string value");
		if (e === this.it) return this._t;
		this.it = e;
		let t = [e];
		return t.raw = t, this._t = {
			_$litType$: this.constructor.resultType,
			strings: t,
			values: []
		};
	}
};
It.directiveName = "unsafeHTML", It.resultType = 1;
// node_modules/lit-html/directives/unsafe-svg.js
var Lt = class extends It {};
Lt.directiveName = "unsafeSVG", Lt.resultType = 2;
var Rt = Pt(Lt);
// src/flow.ts
function zt(e, t, n, r = 0) {
	let i = Math.max(0, e ?? 0), a = t ?? 0, o = n ?? 0, s = Math.max(0, a + i - o), c = Math.max(0, o), l = Math.max(0, -o), u = Math.min(i, s), d = Math.min(i - u, c), f = Math.max(0, i - u - d), p = Math.min(l, s - u), m = Math.max(0, l - p), ee = Math.max(0, s - u - p), h = Math.max(0, c - d);
	return {
		solar: i,
		grid: a,
		battery: o,
		house: s,
		airco: Math.min(Math.max(0, r), s),
		paths: {
			solar_house: u,
			solar_battery: d,
			solar_grid: f,
			grid_house: ee,
			grid_battery: h,
			battery_house: p,
			battery_grid: m
		}
	};
}
var V = {
	solar: [320, 92],
	grid: [104, 250],
	house: [536, 250],
	battery: [320, 408]
}, H = [320, 250], Bt = 50;
function Vt(e, t) {
	let [n, r] = V[e], [i, a] = V[t], o = (e, t, n, r) => {
		let i = Math.hypot(n - e, r - t) || 1;
		return [e + (n - e) / i * 56, t + (r - t) / i * 56];
	}, [s, c] = o(n, r, H[0], H[1]), [l, u] = o(i, a, H[0], H[1]);
	return `M${s.toFixed(1)},${c.toFixed(1)} Q${H[0]},${H[1]} ${l.toFixed(1)},${u.toFixed(1)}`;
}
var Ht = {
	solar: "M12 7a5 5 0 1 0 0 10 5 5 0 0 0 0-10zm0-5v2.5m0 15V22M2 12h2.5m15 0H22M4.9 4.9l1.8 1.8m10.6 10.6 1.8 1.8M4.9 19.1l1.8-1.8m10.6-10.6 1.8-1.8",
	grid: "M9 2 6 22m9-20 3 20M5.5 8h13M4.5 14h15M12 2v20",
	house: "M3.5 11.5 12 4.5l8.5 7M6 10v9.5h12V10M10 19.5v-5h4v5",
	battery: "M8 5.5h8a1.5 1.5 0 0 1 1.5 1.5v12.5A1.5 1.5 0 0 1 16 21H8a1.5 1.5 0 0 1-1.5-1.5V7A1.5 1.5 0 0 1 8 5.5zM10 3h4"
}, Ut = class extends T {
	constructor(...e) {
		super(...e), this.uiLang = "en", this.locale = "en", this.narrow = !1, this.onMedia = () => this.narrow = !!this.media?.matches;
	}
	connectedCallback() {
		super.connectedCallback(), this.media = window.matchMedia("(max-width: 600px)"), this.media.addEventListener("change", this.onMedia), this.onMedia();
	}
	disconnectedCallback() {
		this.media?.removeEventListener("change", this.onMedia), super.disconnectedCallback();
	}
	tr(e, t = {}) {
		return F(this.uiLang, e, t);
	}
	render() {
		let e = this.now;
		if (!e) return b`<div class="skeleton"></div>`;
		let t = e.excluded?.active ? e.excluded.power_w ?? 0 : 0, n = zt(e.solar_w, e.grid_w, e.battery_w, t), r = n.paths, i = Math.max(500, ...Object.values(r)), a = (e, t, n, a) => {
			let o = r[e], s = Vt(t, n);
			if (o < 10) return x`<path d=${s} class="track"></path>`;
			let c = Math.min(1, o / i), l = 2 + Math.round(c * 3), u = (3.2 - c * 1.8).toFixed(2);
			return x`<path d=${s} class="track lit ${a}" style=${`stroke-width:${2 + c * 3}`}></path>
        ${Array.from({ length: l }, (e, t) => x`<circle r=${3 + c * 2.5} class=${`dot ${a}`}>
          <animateMotion dur=${`${u}s`} repeatCount="indefinite" begin=${`-${(t * Number(u) / l).toFixed(2)}s`} path=${s}></animateMotion>
        </circle>`)}`;
		}, o = e.soc, s = 2 * Math.PI * 46;
		return b`<section class="card" aria-labelledby="fl-title">
      <div class="head">
        <h2 id="fl-title">${this.tr("flow.title")}</h2>
        ${e.live ? C : b`<span class="chip">${this.tr("flow.shadow_chip")}</span>`}
      </div>
      <svg
        viewBox=${this.narrow ? "0 0 640 620" : "0 0 640 540"}
        class=${this.narrow ? "stage narrow" : "stage"}
        role="img"
        aria-label=${this.summary(n)}
      >
        <defs>
          <radialGradient id="glow" cx="50%" cy="50%" r="50%">
            <stop offset="0%" class="glow0"></stop>
            <stop offset="100%" class="glow1"></stop>
          </radialGradient>
        </defs>
        <circle cx=${H[0]} cy=${H[1]} r="150" fill="url(#glow)"></circle>
        ${a("solar_house", "solar", "house", "sun")}
        ${a("solar_battery", "solar", "battery", "sun")}
        ${a("solar_grid", "solar", "grid", "sun")}
        ${a("grid_house", "grid", "house", "grid")}
        ${a("grid_battery", "grid", "battery", "grid")}
        ${a("battery_house", "battery", "house", "bat")}
        ${a("battery_grid", "battery", "grid", "bat")}
        <circle cx=${H[0]} cy=${H[1]} r="5" class="hub"></circle>
        ${this.node("solar", this.tr("flow.solar"), k(n.solar, this.locale), e.curtail?.active && e.curtail.percent !== null ? this.tr("flow.curtailed", { pct: e.curtail.percent }) : e.curtail?.active && e.curtail.switch_on ? this.tr("flow.inverter_off") : n.solar < 10 ? this.tr("flow.none") : e.solar_estimated ? this.tr("flow.estimated") : "", n.solar >= 10)}
        ${this.node("grid", this.tr(Math.abs(n.grid) < 30 ? "flow.grid" : n.grid > 0 ? "flow.grid_in" : "flow.grid_out"), k(Math.abs(n.grid), this.locale), Math.abs(n.grid) < 30 ? this.tr("flow.balanced") : "", Math.abs(n.grid) >= 30)}
        ${this.node("house", this.tr("flow.house"), k(n.house, this.locale), n.airco >= 10 ? this.tr("flow.airco", { w: k(n.airco, this.locale) }) : "", !0)}
        ${this.node("battery", this.tr(n.battery > 10 ? "flow.charging" : n.battery < -10 ? "flow.delivering" : "flow.battery"), k(Math.abs(n.battery), this.locale), e.curtail?.export_blocked ? `${o === null ? "" : `${j(o, this.locale)} · `}${this.tr("flow.export_blocked")}` : o === null ? "" : j(o, this.locale), Math.abs(n.battery) > 10)}
        ${o === null ? C : x`<circle cx=${V.battery[0]} cy=${V.battery[1]} r=${46} class="socring"
              stroke-dasharray=${`${s * Math.max(0, Math.min(100, o)) / 100} ${s}`}
              transform=${`rotate(-90 ${V.battery[0]} ${V.battery[1]})`}></circle>`}
      </svg>
      <p class="sum">${this.summary(n)}</p>
    </section>`;
	}
	summary(e) {
		let t = [], n = e.paths, r = (e) => k(e, this.locale);
		if (n.solar_house >= 10 && t.push(this.tr("flow.s_solar_house", { w: r(n.solar_house) })), n.battery_house >= 10 && t.push(this.tr("flow.s_battery_house", { w: r(n.battery_house) })), n.grid_house >= 10 && t.push(this.tr("flow.s_grid_house", { w: r(n.grid_house) })), n.solar_battery >= 10 && t.push(this.tr("flow.s_solar_battery", { w: r(n.solar_battery) })), n.grid_battery >= 10 && t.push(this.tr("flow.s_grid_battery", { w: r(n.grid_battery) })), n.solar_grid + n.battery_grid >= 10 && t.push(this.tr("flow.s_export", { w: r(n.solar_grid + n.battery_grid) })), !t.length) return this.tr("flow.s_idle");
		let i = t.join("; ");
		return `${i.charAt(0).toUpperCase()}${i.slice(1)}.`;
	}
	node(e, t, n, r, i) {
		let [a, o] = V[e], s = this.narrow ? 1.7 : 1, c = e === "solar" && this.narrow, l = c ? a + Bt + 16 : a, u = c ? o - 30 : e === "solar" ? o - Bt - 44 : o + Bt + 26 * s, d = c ? "start" : "middle";
		return x`<g class=${`node ${e}${i ? " active" : ""}`} text-anchor=${d}>
      <circle cx=${a} cy=${o} r=${58} class="halo"></circle>
      <circle cx=${a} cy=${o} r=${Bt} class="disc"></circle>
      <circle cx=${a} cy=${o} r=${46} class="ring"></circle>
      <g transform=${`translate(${a - 22} ${o - 22}) scale(1.833)`}><path d=${Ht[e]} class="icon"></path></g>
      <text x=${l} y=${u} class="label" text-anchor=${d}>${t.toUpperCase()}</text>
      <text x=${l} y=${u + 26 * s} class="value" text-anchor=${d}>${n}</text>
      ${r ? x`<text x=${l} y=${u + 44 * s} class="sub" text-anchor=${d}>${r}</text>` : C}
    </g>`;
	}
	static {
		this.styles = s`
    :host {
      display: block;
      color: var(--z-text);
      font-family: var(--z-font);
    }
    .card {
      background: var(--z-card);
      border: 1px solid var(--z-border);
      border-radius: 20px;
      padding: 20px 24px 22px;
      display: flex;
      flex-direction: column;
      gap: 6px;
      max-width: 760px;
      margin: 0 auto;
    }
    .head {
      display: flex;
      justify-content: space-between;
      align-items: center;
      gap: 10px;
    }
    h2 {
      margin: 0;
      font-family: var(--z-font-head);
      font-size: 20px;
    }
    .chip {
      padding: 3px 10px;
      border-radius: 999px;
      background: var(--z-info-bg);
      font-size: 12px;
      color: var(--z-muted);
    }
    .stage {
      width: 100%;
      height: auto;
      overflow: visible;
    }
    .glow0 {
      stop-color: var(--z-charge);
      stop-opacity: 0.08;
    }
    .glow1 {
      stop-color: var(--z-charge);
      stop-opacity: 0;
    }
    .track {
      fill: none;
      stroke: var(--z-border);
      stroke-width: 2;
      stroke-linecap: round;
    }
    .track.lit {
      opacity: 0.55;
    }
    .track.sun,
    .dot.sun {
      stroke: var(--z-solar);
      fill: var(--z-solar);
    }
    .track.grid,
    .dot.grid {
      stroke: var(--z-hold-b, var(--z-muted));
      fill: var(--z-hold-b, var(--z-muted));
    }
    .track.bat,
    .dot.bat {
      stroke: var(--z-deliver);
      fill: var(--z-deliver);
    }
    .track.lit {
      fill: none;
    }
    .dot {
      stroke: none !important;
      filter: drop-shadow(0 0 3px rgba(0, 0, 0, 0.15));
    }
    .hub {
      fill: var(--z-border);
    }
    .halo {
      fill: none;
      stroke: transparent;
      stroke-width: 10;
    }
    .disc {
      fill: var(--z-card);
      stroke: var(--z-border);
      stroke-width: 1.5;
    }
    .ring {
      fill: none;
      stroke: var(--z-track);
      stroke-width: 5;
    }
    .solar.active .ring {
      stroke: var(--z-solar);
    }
    .grid.active .ring {
      stroke: var(--z-hold-b, var(--z-muted));
    }
    .house .ring {
      stroke: var(--z-charge);
    }
    .battery.active .ring {
      stroke: var(--z-track);
    }
    .solar.active .halo {
      stroke: var(--z-solar);
      opacity: 0.18;
    }
    .battery.active .halo {
      stroke: var(--z-deliver);
      opacity: 0.18;
    }
    .socring {
      fill: none;
      stroke: var(--z-export);
      stroke-width: 5;
      stroke-linecap: round;
    }
    .icon {
      fill: none;
      stroke: var(--z-text);
      stroke-width: 1.4;
      stroke-linecap: round;
      stroke-linejoin: round;
    }
    text {
      fill: var(--z-text);
    }
    .label {
      font-size: 12px;
      letter-spacing: 0.08em;
      fill: var(--z-muted);
      font-weight: 600;
    }
    .value {
      font-family: var(--z-font-head);
      font-size: 24px;
      font-weight: 700;
    }
    .sub {
      font-size: 13px;
      fill: var(--z-muted);
    }
    .sum {
      margin: 0;
      font-size: 14px;
      line-height: 1.5;
      color: var(--z-muted);
      text-align: center;
    }
    .skeleton {
      height: 420px;
      border-radius: 16px;
      background: var(--z-track);
    }
    @media (prefers-reduced-motion: reduce) {
      .dot {
        display: none;
      }
      .track.lit {
        opacity: 1;
      }
    }
    @media (max-width: 600px) {
      .card {
        padding: 14px;
      }
      /* The drawing shrinks with the screen; the text in it should not. */
      .label {
        font-size: 20px;
      }
      .value {
        font-size: 36px;
      }
      .sub {
        font-size: 20px;
      }
      .head {
        flex-wrap: wrap;
      }
    }
  `;
	}
};
R([E({ attribute: !1 })], Ut.prototype, "now", void 0), R([E({ attribute: !1 })], Ut.prototype, "uiLang", void 0), R([E()], Ut.prototype, "locale", void 0), R([D()], Ut.prototype, "narrow", void 0), Ut = R([e("zephyr-flow")], Ut);
// src/house.ts
var Wt = 1700, Gt = 1225, U = 920, Kt = {
	header: [
		20,
		16,
		420,
		96
	],
	bus: [[U, 96], [U, 1145]],
	battery: {
		box: [
			20,
			140,
			420,
			84
		],
		line: [
			[530, 165],
			[530, 96],
			[U, 96]
		],
		dot: [530, 165],
		label: [545, 140]
	},
	shedSolar: {
		box: [
			960,
			16,
			300,
			70
		],
		line: [
			[735, 150],
			[735, 112],
			[U, 112]
		],
		dot: [735, 150]
	},
	roof: {
		box: [
			20,
			340,
			262,
			80
		],
		line: [[600, 420], [U, 420]],
		dot: [600, 420],
		label: [700, 405]
	},
	grid: {
		box: [
			20,
			1075,
			300,
			100
		],
		line: [[320, 1145], [U, 1145]],
		label: [430, 1130]
	},
	ev: {
		box: [
			690,
			990,
			220,
			76
		],
		line: [[U, 972], [685, 972]],
		dot: [685, 972]
	},
	home: {
		box: [
			940,
			1060,
			330,
			110
		],
		line: [[U, 700], [705, 700]],
		dot: [705, 700],
		label: [730, 688]
	},
	floors: {
		attic: {
			box: [
				1378,
				265,
				316,
				80
			],
			line: [[U, 305], [1037, 305]]
		},
		first: {
			box: [
				1378,
				460,
				316,
				80
			],
			line: [[U, 500], [1024, 500]]
		},
		ground: {
			box: [
				1378,
				675,
				316,
				80
			],
			line: [[U, 715], [1009, 715]]
		},
		shed: {
			box: [
				1378,
				892,
				316,
				80
			],
			line: []
		}
	}
}, qt = {}, W = {
	sun: "#ffcf1f",
	batt: "#22d3b5",
	house: "#2f8cff",
	grid: "#ff4d4d",
	ev: "#a86bff",
	exp: "#ff3b3b"
};
Object.assign(qt, {
	sun: W.sun,
	batt: W.batt,
	grid: W.grid
});
var Jt = {
	sun: "<circle cx=\"12\" cy=\"12\" r=\"4\"/><path d=\"M12 2v2M12 20v2M2 12h2M20 12h2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4\"/>",
	batt: "<rect x=\"7\" y=\"4\" width=\"10\" height=\"17\" rx=\"2\"/><path d=\"M10 2h4M12 9v6M9 12h6\"/>",
	house: "<path d=\"M3 11l9-7 9 7M5 10v10h14V10M10 20v-5h4v5\"/>",
	ev: "<path d=\"M5 16l1.5-5a2 2 0 0 1 2-1.5h7a2 2 0 0 1 2 1.5L19 16M4 16h16v3H4zM7 19v2M17 19v2\"/>",
	grid: "<path d=\"M8 22L12 3l4 19M6 8h12M5 12h14M9.5 15h5M12 3V1\"/>",
	export: "<circle cx=\"12\" cy=\"12\" r=\"9\"/><path d=\"M8 15l8-6M12 9h4v4\"/>",
	wash: "<rect x=\"4\" y=\"3\" width=\"16\" height=\"18\" rx=\"2\"/><circle cx=\"12\" cy=\"13\" r=\"4.5\"/><path d=\"M7 6h3\"/>",
	leaf: "<path d=\"M4 20C4 10 10 4 20 4c0 10-6 16-16 16zM4 20l9-9\"/>"
};
function Yt(e) {
	let t = {};
	for (let n of e) n.shown && (t[n.floor] ??= []).push(n);
	return t;
}
var G = [
	"roof",
	"shed_solar",
	"battery",
	"grid",
	"ev",
	"home",
	"attic",
	"first",
	"ground",
	"shed"
];
function Xt(e, t, n = 50) {
	let r = Object.keys(e).reduce((t, n) => e[n] > e[t] ? n : t);
	return e[r] < 10 ? null : t && t !== r && e[r] < e[t] + n && e[t] >= 10 ? t : r;
}
function Zt(e) {
	let t = [], n = (n, r) => {
		let i = r.map(([t, n]) => [n, e[t] ?? 0]).filter(([, e]) => e >= 10);
		i.length && t.push({
			from: n,
			total: i.reduce((e, [, t]) => e + t, 0),
			to: i
		});
	};
	return n("sun", [
		["solar_house", "house"],
		["solar_battery", "battery"],
		["solar_grid", "grid"]
	]), n("batt", [["battery_house", "house"], ["battery_grid", "grid"]]), n("grid", [["grid_house", "house"], ["grid_battery", "battery"]]), t;
}
var Qt = [
	"attic",
	"first",
	"ground",
	"shed"
], $t = .24;
function en(e, t, n, r) {
	let i = Math.min(e[0], .76) * n, a = i + $t * n, o = e[1] * r + .035 * n, s = t[0] * n, c = t[1] * r, l = s < i ? i : s > a ? a : s;
	return l === s ? [[s, o], [s, c]] : [
		[l, o],
		[s, o],
		[s, c]
	];
}
function tn(e, t) {
	return e[0] === t[0] || e[1] === t[1] ? [e, t] : [
		e,
		[t[0], e[1]],
		t
	];
}
var K = class extends T {
	constructor(...e) {
		super(...e), this.uiLang = "en", this.locale = "en", this.base = "", this.dom = null, this.ownUrl = null, this.ownSigned = -1;
	}
	tr(e, t = {}) {
		return F(this.uiLang, e, t);
	}
	w(e) {
		return k(e ?? 0, this.locale);
	}
	render() {
		let e = this.now;
		if (!e) return b`<section class="card skeleton"></section>`;
		let t = this.view?.devices ?? [], n = e.excluded?.active ? e.excluded.power_w ?? 0 : 0, r = zt(e.solar_w, e.grid_w, e.battery_w, n), i = t.find((e) => e.kind === "ev") ?? null, a = this.items(e, t), o = this.view?.picture ?? null;
		return b`<section class="card" aria-label=${this.tr("house.title")}>
      ${o ? this.ownStage(o, a) : this.defaultStage(a)}
      ${this.bar(r, i)}
      ${this.list(t, Math.max(0, r.house - this.known(t)))}
    </section>`;
	}
	known(e) {
		return e.filter((e) => e.shown && e.kind !== "ev").reduce((e, t) => e + (t.power_w ?? 0), 0);
	}
	items(e, t) {
		let n = e.excluded?.active ? e.excluded.power_w ?? 0 : 0, r = zt(e.solar_w, e.grid_w, e.battery_w, n), i = t.find((e) => e.kind === "ev") ?? null, a = Yt(t.filter((e) => e.kind !== "ev")), o = Math.max(0, r.house - this.known(t)), s = e.solar_external_w ?? 0, c = e.solar_sets_w ?? 0, l = e.curtail?.active ? e.curtail : null, u = (e) => (a[e] ?? []).reduce((e, t) => e + (t.power_w ?? 0), 0), d = (t) => ({
			...this.floorItem(t, a[t] ?? [], null, e),
			power: t === "shed" ? 0 : u(t)
		});
		return {
			roof: {
				color: W.sun,
				icon: "sun",
				title: b`<b>${this.tr("house.roof")}</b>`,
				lines: [b`<b>${this.w(s)}</b
            >${l ? b` <span class="red">${this.curtailText(l)}</span>` : C}`],
				power: s
			},
			shed_solar: {
				color: W.sun,
				icon: "sun",
				title: b`<b>${this.tr("house.shed_solar")}</b>`,
				lines: [b`<b>${this.w(c)}</b>`],
				power: c
			},
			battery: {
				color: W.batt,
				icon: "batt",
				title: b`<b class="fit"
          >${this.view?.battery_label ?? this.tr("house.battery")}</b
        >`,
				lines: [b`${this.tr(r.battery > 10 ? "house.charging" : r.battery < -10 ? "house.delivering" : "house.idle")}
            <b
              >${Math.abs(r.battery) > 10 ? this.w(Math.abs(r.battery)) : ""}</b
            >
            ${e.soc === null ? C : b` | SoC ${j(e.soc, this.locale)}`}
            ${e.curtail?.export_blocked ? b` <span class="red">${this.tr("flow.export_blocked")}</span>` : C}`],
				power: Math.abs(r.battery)
			},
			grid: {
				color: W.grid,
				icon: "grid",
				title: b`<b>${this.tr("house.grid")}</b>`,
				lines: [b`${this.tr("house.import")}
            <b>${this.w(Math.max(0, r.grid))}</b>`, b`${this.tr("house.export")}
            <b>${this.w(Math.max(0, -r.grid))}</b>`],
				power: Math.abs(r.grid)
			},
			ev: {
				color: W.batt,
				icon: "ev",
				title: b`<b>${this.tr("house.ev")}</b>`,
				lines: [b`<b>${i ? this.w(i.power_w) : "–"}</b>`],
				active: !!i,
				power: i?.power_w ?? 0
			},
			home: {
				color: W.house,
				icon: "house",
				title: b`<b>${this.tr("house.home")}</b>`,
				lines: [b`${this.tr("house.total")} <b>${this.w(r.house)}</b>`, b`${this.tr("house.rest_of")} <b>${this.w(o)}</b>`],
				power: o
			},
			attic: d("attic"),
			first: d("first"),
			ground: d("ground"),
			shed: d("shed")
		};
	}
	mainColor(e) {
		let t = Xt({
			sun: e.solar - e.paths.solar_battery,
			batt: Math.max(0, -e.battery),
			grid: Math.max(0, e.grid)
		}, this.dom);
		return t !== this.dom && queueMicrotask(() => this.dom = t), t ? qt[t] : W.house;
	}
	defaultStage(e) {
		let t = Kt, n = this.now, r = n.excluded?.active ? n.excluded.power_w ?? 0 : 0, i = zt(n.solar_w, n.grid_w, n.battery_w, r), a = this.mainColor(i), o = (e, t) => t ? [...e].reverse() : e, s = i.battery, c = i.house >= 10 || Math.abs(s) >= 10 || Math.abs(i.grid) >= 10, l = (e, t, n, r) => r ? x`<text x=${e[0]} y=${e[1]} class="tag" fill=${n}>${t}</text>` : C, u = (e) => this.tr(`house.to_${e}`);
		return b`<div class="stage">
      <img src=${`${this.base}/house.webp`} alt="" draggable="false" />
      <svg viewBox="0 0 ${Wt} ${Gt}" aria-hidden="true">
        ${c ? this.line(t.bus, a, Math.max(i.house, Math.abs(s), Math.abs(i.grid))) : C}
        ${this.line(t.roof.line, W.sun, e.roof.power)}${this.dot(t.roof.dot, W.sun)}
        ${this.line(t.shedSolar.line, W.sun, e.shed_solar.power)}${this.dot(t.shedSolar.dot, W.sun)}
        ${this.line(o(t.battery.line, s > 0), W.batt, Math.abs(s))}${this.dot(t.battery.dot, W.batt)}
        ${this.line(o(t.grid.line, i.grid < 0), W.grid, Math.abs(i.grid))}
        ${e.ev.active ? x`${this.line(t.ev.line, W.batt, e.ev.power)}${this.dot(t.ev.dot, W.batt)}` : C}
        ${e.home.power >= 10 ? x`${this.line(t.home.line, a, e.home.power)}${this.dot(t.home.dot, a)}` : C}
        ${[
			"attic",
			"first",
			"ground"
		].map((n) => {
			let r = t.floors[n].line, i = r[r.length - 1];
			return e[n].power >= 10 ? x`${this.line(r, a, e[n].power)}${this.arrow(i[0], i[1], a)}` : C;
		})}
        ${c ? x`<circle cx=${U} cy="96" r="8" fill=${a}></circle><circle cx=${U} cy="1145" r="8" fill=${a}></circle>` : C}
        ${l(t.roof.label, this.w(e.roof.power), W.sun, e.roof.power >= 10)}
        ${l(t.battery.label, `${this.w(Math.abs(s))} ${u(s > 0 ? "battery" : "house")}`, W.batt, Math.abs(s) >= 10)}
        ${l(t.grid.label, `${this.w(Math.abs(i.grid))} ${u(i.grid > 0 ? "house" : "grid")}`, W.grid, Math.abs(i.grid) >= 10)}
        ${l(t.home.label, `${this.tr("house.rest")} ${this.w(e.home.power)}`, a, e.home.power >= 10)}
      </svg>
      <div class="boxes">
        ${this.box(t.header, this.header(i.paths))}
        ${this.box(t.roof.box, e.roof)}
        ${this.box(t.shedSolar.box, e.shed_solar)}
        ${this.box(t.battery.box, e.battery)} ${this.box(t.grid.box, e.grid)}
        ${this.box(t.ev.box, e.ev)}
        ${this.box(t.home.box, {
			...e.home,
			color: a
		})}
        ${Qt.map((n) => this.box(t.floors[n].box, e[n]))}
      </div>
    </div>`;
	}
	ownStage(e, t) {
		let n = e.width || 1600, r = e.height || 1200, i = G.filter((t) => !e.hidden.includes(t) && e.items[t]?.box), a = this.now, o = a.excluded?.active ? a.excluded.power_w ?? 0 : 0, s = zt(a.solar_w, a.grid_w, a.battery_w, o), c = (t) => {
			let a = e.items[t]?.point;
			return a && i.includes(t) ? [a[0] * n, a[1] * r] : null;
		}, l = c("home"), u = this.mainColor(s), d = l ? x`${[
			[
				"roof",
				W.sun,
				t.roof.power,
				!1
			],
			[
				"shed_solar",
				W.sun,
				t.shed_solar.power,
				!1
			],
			[
				"battery",
				W.batt,
				Math.abs(s.battery),
				s.battery > 0
			],
			[
				"grid",
				W.grid,
				Math.abs(s.grid),
				s.grid < 0
			]
		].map(([e, t, n, r]) => {
			let i = c(e);
			if (!i) return C;
			let a = tn(i, l);
			return this.line(r ? [...a].reverse() : a, t, n);
		})}
        ${[
			"ev",
			"attic",
			"first",
			"ground"
		].map((e) => {
			let n = c(e);
			return n && (e !== "ev" || t.ev.active) ? this.line(tn(n, l).reverse(), u, t[e].power) : C;
		})}
        ${this.dot(l, u)}` : C;
		return b`<div class="stage own" style=${`aspect-ratio:${n}/${r}`}>
      ${this.ownUrl ? b`<img src=${this.ownUrl} alt="" draggable="false" />` : C}
      <svg viewBox="0 0 ${n} ${r}" aria-hidden="true">
        ${d}
        ${i.map((i) => {
			let a = e.items[i];
			if (!a?.point || !a.box) return C;
			let o = en(a.box, a.point, n, r), s = o[o.length - 1], c = i === "home" ? u : t[i].color;
			return l ? x`<path d=${`M${o.map((e) => e.join(" ")).join(" L")}`} class="pointer" stroke=${c}></path>${this.dot(s, c)}` : x`${this.line(o, c, t[i].power)}${this.dot(s, c)}`;
		})}
      </svg>
      <div class="boxes">
        ${i.map((n) => {
			let [r, i] = e.items[n]?.box ?? [0, 0], a = n === "home" ? {
				...t.home,
				color: u,
				lines: [...t.home.lines, ...Zt(s.paths).length ? this.header(s.paths).lines : []]
			} : t[n];
			return this.placed(r, i, a);
		})}
      </div>
    </div>`;
	}
	willUpdate() {
		let e = this.view?.picture;
		e && this.sign && e.version !== this.ownSigned && (this.ownSigned = e.version, this.sign(`/api/zephyr/house_picture?v=${e.version}`).then((e) => this.ownUrl = e, () => this.ownSigned = -1));
	}
	header(e) {
		let t = (e) => this.tr(`house.src_${e}`), n = (e) => this.tr(`house.dst_${e}`), r = e ? Zt(e) : [];
		return {
			color: "#23435a",
			icon: "leaf",
			title: b`<b class="big">${this.tr("house.title")}</b>`,
			lines: r.length ? r.map((e) => e.to.length === 1 ? b`${t(e.from)} <b>${this.w(e.total)}</b> →
                  ${n(e.to[0][0])}` : b`${t(e.from)} <b>${this.w(e.total)}</b> →
                  ${e.to.map(([e, t], r) => b`${r ? " · " : ""}${n(e)} ${this.w(t)}`)}`) : [this.tr("house.sub")],
			power: 0
		};
	}
	curtailText(e) {
		return e.percent === null ? e.switch_on ? this.tr("flow.inverter_off") : "" : this.tr("flow.curtailed", { pct: e.percent });
	}
	floorItem(e, t, n, r) {
		let i = t.map((e) => b`${e.name ?? this.tr(`stroom.kind_${e.kind}`)}
          <b class=${(e.power_w ?? 0) >= 10 ? "" : "dim"}
            >${this.w(e.power_w)}</b
          >`);
		return n !== null && i.push(b`${this.tr("house.rest")} <b>${this.w(n)}</b>`), e === "shed" && !i.length && r.soc !== null && i.push(b`${this.tr("house.battery")}
          <b>${j(r.soc, this.locale)}</b>`), {
			color: e === "shed" ? W.batt : W.house,
			icon: e === "shed" ? "batt" : e === "attic" ? "wash" : "house",
			title: b`<b>${this.tr(`settings.floors.${e}`)}</b>`,
			lines: [i.length ? b`${i.map((e, t) => b`${t ? b`<span class="sep"> · </span>` : C}${e}`)}` : b`<span class="dim">–</span>`]
		};
	}
	placed(e, t, n) {
		let r = `left:${Math.min(e, .76) * 100}%;top:${t * 100}%;width:${$t * 100}%;--c:${n.color}`;
		return this.boxHtml(r, n);
	}
	box(e, t) {
		let [n, r, i, a] = e, o = `left:${n / Wt * 100}%;top:${r / Gt * 100}%;width:${i / Wt * 100}%;min-height:${a / Gt * 100}%;--c:${t.color}`;
		return this.boxHtml(o, t);
	}
	boxHtml(e, t) {
		return b`<div
      class=${t.active === !1 ? "box off" : "box"}
      style=${e}
    >
      <span class="ic"
        ><svg viewBox="0 0 24 24">${Rt(Jt[t.icon])}</svg></span
      >
      <span class="tx"
        >${t.title}${t.lines.map((e) => b`<span class="ln">${e}</span>`)}</span
      >
    </div>`;
	}
	line(e, t, n) {
		let r = `M${e.map((e) => e.join(" ")).join(" L")}`;
		return n < 10 ? C : x`<path d=${r} class="glow" stroke=${t}></path>
      <path d=${r} class="core" stroke=${t}></path>
      <path d=${r} class="dots" style=${`animation-duration:${Math.max(.5, 1.6 - n / 3e3)}s`}></path>`;
	}
	dot(e, t) {
		return x`<circle cx=${e[0]} cy=${e[1]} r="6" fill=${t}></circle>`;
	}
	arrow(e, t, n) {
		return x`<path d=${`M${e} ${t} l-16 -9 l0 18 z`} fill=${n}></path>`;
	}
	bar(e, t) {
		return b`<div class="bar">
      ${[
			[
				"sun",
				W.sun,
				this.tr("house.sun"),
				this.w(e.solar),
				this.tr("house.production"),
				e.solar >= 10
			],
			[
				"batt",
				W.batt,
				this.tr("house.battery"),
				this.w(Math.abs(e.battery)),
				this.tr(e.battery > 10 ? "house.charging_l" : e.battery < -10 ? "house.delivering_l" : "house.idle_l"),
				Math.abs(e.battery) >= 10
			],
			[
				"house",
				W.house,
				this.tr("house.consumers"),
				this.w(e.house),
				this.tr("house.house"),
				!0
			],
			[
				"ev",
				W.ev,
				this.tr("house.ev"),
				t ? this.w(t.power_w) : "–",
				this.tr("house.ev_sub"),
				!!t && (t.power_w ?? 0) >= 10
			],
			[
				"grid",
				W.grid,
				this.tr("house.grid"),
				this.w(Math.max(0, e.grid)),
				this.tr("house.import_l"),
				e.grid >= 10
			],
			[
				"export",
				W.exp,
				this.tr("house.export_t"),
				this.w(Math.max(0, -e.grid)),
				this.tr("house.export_l"),
				e.grid <= -10
			]
		].map(([e, t, n, r, i, a]) => b`<div class=${a ? "" : "off"}>
            <span class="bic" style="--c:${t}"
              ><svg viewBox="0 0 24 24">${Rt(Jt[e])}</svg></span
            >
            <span class="bt">${n}</span><b>${r}</b
            ><span class="bs">${i}</span>
          </div>`)}
    </div>`;
	}
	list(e, t) {
		return b`<ul class="list">
      ${e.filter((e) => e.shown).map((e) => b`<li>
            <span
              >${e.name ?? this.tr(`stroom.kind_${e.kind}`)}
              <small>${this.tr(`settings.floors.${e.floor}`)}</small></span
            ><b>${this.w(e.power_w)}</b>
          </li>`)}
      <li><span>${this.tr("house.rest")}</span><b>${this.w(t)}</b></li>
    </ul>`;
	}
	static {
		this.styles = s`
    :host {
      display: block;
      grid-column: 1 / -1;
      /* Picture plus totals bar fit in one screen: 1700/1225 is the default picture's aspect ratio. */
      --house-max: calc((100vh - 300px) * var(--house-ar, 1.3878) + 30px);
    }
    .card {
      container: house / inline-size;
      max-width: var(--house-max);
      margin: 0 auto;
      background: #0f1d27;
      border: 1px solid #1f3342;
      border-radius: 18px;
      padding: 14px;
      color: #eef2f5;
      font-family: var(--z-font);
      /* Next to the today cards: as high as they are, the bar at the bottom. */
      box-sizing: border-box;
      height: 100%;
      display: flex;
      flex-direction: column;
      justify-content: space-between;
      gap: 14px;
    }
    .skeleton {
      min-height: 400px;
    }
    .stage {
      position: relative;
      border-radius: 12px;
      overflow: hidden;
      container-type: inline-size;
    }
    img {
      display: block;
      width: 100%;
      user-select: none;
    }
    .stage > svg {
      position: absolute;
      inset: 0;
      width: 100%;
      height: 100%;
    }
    .glow {
      fill: none;
      stroke-width: 11;
      opacity: 0.16;
    }
    .core {
      fill: none;
      stroke-width: 3;
      opacity: 0.95;
    }
    .dots {
      fill: none;
      stroke: #fff;
      stroke-width: 3;
      stroke-linecap: round;
      stroke-dasharray: 3 14;
      opacity: 0.85;
      animation: run 1s linear infinite;
    }
    .stage > svg .pointer {
      fill: none;
      stroke-width: 2;
      opacity: 0.7;
    }
    .stage > svg text.tag {
      font: 700 26px var(--z-font);
      paint-order: stroke;
      stroke: #0b1620;
      stroke-width: 7px;
    }
    @keyframes run {
      to {
        stroke-dashoffset: -17;
      }
    }
    .boxes {
      position: absolute;
      inset: 0;
      font-size: max(11px, 1.15cqw);
    }
    .box {
      position: absolute;
      box-sizing: border-box;
      display: flex;
      align-items: center;
      gap: 0.8cqw;
      padding: 0.4cqw 1cqw;
      background: rgba(12, 26, 36, 0.93);
      border: 2px solid var(--c);
      border-radius: 1.1cqw;
      color: #dbe8f2;
      overflow: hidden;
    }
    .box.off {
      opacity: 0.6;
    }
    .ic {
      flex: none;
      width: max(18px, 2.6cqw);
      height: max(18px, 2.6cqw);
      color: var(--c);
    }
    .ic svg,
    .bic svg {
      width: 100%;
      height: 100%;
      fill: none;
      stroke: currentColor;
      stroke-width: 1.8;
      stroke-linecap: round;
      stroke-linejoin: round;
    }
    .tx {
      display: flex;
      flex-direction: column;
      min-width: 0;
      line-height: 1.3;
    }
    .tx > b {
      color: #fff;
      font-weight: 600;
      font-size: max(11.5px, 1.1cqw);
      overflow: hidden;
    }
    .ln b {
      white-space: nowrap;
    }
    .tx > b.fit {
      font-size: max(11px, 0.95cqw);
      white-space: normal;
    }
    .tx .big {
      font-size: max(16px, 1.9cqw);
      font-weight: 700;
    }
    .ln {
      font-size: max(11px, 1.05cqw);
      display: -webkit-box;
      -webkit-line-clamp: 2;
      -webkit-box-orient: vertical;
      overflow: hidden;
    }
    .ln b {
      color: #fff;
    }
    .ln b.dim,
    .dim {
      color: #8aa0b0;
      font-weight: 400;
    }
    .red {
      color: #ff8a8a;
      font-weight: 600;
    }
    .bar {
      display: flex;
      background: #0f1f2a;
      border: 1px solid #23435a;
      border-radius: 16px;
      padding: 14px 6px;
    }
    .bar > div {
      flex: 1;
      display: flex;
      flex-direction: column;
      align-items: center;
      text-align: center;
      border-right: 1px solid #23435a;
      padding: 0 6px;
      min-width: 0;
    }
    .bar > div:last-child {
      border: 0;
    }
    .bar > div.off {
      opacity: 0.55;
    }
    .bic {
      width: 44px;
      height: 44px;
      box-sizing: border-box;
      padding: 9px;
      border-radius: 50%;
      border: 2px solid var(--c);
      color: var(--c);
      box-shadow: 0 0 14px color-mix(in srgb, var(--c) 35%, transparent);
      margin-bottom: 6px;
    }
    .bt {
      font-weight: 600;
    }
    .bar b {
      font-size: 18px;
    }
    .bs {
      color: #9fb3c2;
      font-size: 12px;
    }
    .list {
      display: none;
      list-style: none;
      margin: 10px 0 0;
      padding: 0;
    }
    .list li {
      display: flex;
      justify-content: space-between;
      padding: 7px 2px;
      border-bottom: 1px solid #23435a;
    }
    .list small {
      color: #9fb3c2;
    }
    @container house (max-width: 680px) {
      .stage > svg,
      .boxes {
        display: none;
      }
      .list {
        display: block;
      }
    }
    @container house (max-width: 640px) {
      .bar {
        display: grid;
        grid-template-columns: repeat(3, minmax(0, 1fr));
        row-gap: 14px;
      }
      .bar > div {
        border: 0;
        min-width: 0;
      }
    }
  `;
	}
};
R([E({ attribute: !1 })], K.prototype, "now", void 0), R([E({ attribute: !1 })], K.prototype, "view", void 0), R([E({ attribute: !1 })], K.prototype, "uiLang", void 0), R([E()], K.prototype, "locale", void 0), R([E()], K.prototype, "base", void 0), R([E({ attribute: !1 })], K.prototype, "sign", void 0), R([D()], K.prototype, "dom", void 0), R([D()], K.prototype, "ownUrl", void 0), K = R([e("zephyr-house")], K);
// src/house-editor.ts
var nn = 1800, rn = {
	roof: W.sun,
	shed_solar: W.sun,
	battery: W.batt,
	grid: W.grid,
	ev: W.batt,
	home: W.house,
	attic: W.house,
	first: W.house,
	ground: W.house,
	shed: W.batt
};
async function an(e) {
	let t = await createImageBitmap(e), n = Math.min(1, nn / t.width), r = Math.round(t.width * n), i = Math.round(t.height * n), a = document.createElement("canvas");
	a.width = r, a.height = i, a.getContext("2d")?.drawImage(t, 0, 0, r, i);
	let o = await new Promise((e, t) => a.toBlob((n) => n ? e(n) : t(/* @__PURE__ */ Error("canvas")), "image/webp", .85)), s = new Uint8Array(await o.arrayBuffer()), c = "";
	for (let e = 0; e < s.length; e += 32768) c += String.fromCharCode(...s.subarray(e, e + 32768));
	return {
		data: btoa(c),
		width: r,
		height: i
	};
}
function on(e, t, n) {
	let r = n ? G.indexOf(n) + 1 : 0;
	for (let n = 0; n < G.length; n++) {
		let i = G[(r + n) % G.length];
		if (!t.includes(i) && !e[i]?.point) return i;
	}
	return null;
}
var q = class extends T {
	constructor(...e) {
		super(...e), this.picture = null, this.canEdit = !1, this.uiLang = "en", this.draft = null, this.selected = null, this.busy = !1, this.error = null, this.url = null, this.signed = -1, this.onFile = async (e) => {
			let t = e.target, n = t.files?.[0];
			if (t.value = "", n && this.call) {
				this.busy = !0, this.error = null;
				try {
					let e = await an(n);
					await this.call({
						type: "zephyr/house/picture/upload",
						...e
					}), this.draft = null, this.selected = on(this.picture?.items ?? {}, this.picture?.hidden ?? [], null), await this.changed?.();
				} catch (e) {
					this.error = e?.message ?? String(e);
				} finally {
					this.busy = !1;
				}
			}
		};
	}
	tr(e, t = {}) {
		return F(this.uiLang, e, t);
	}
	label(e) {
		return [
			"attic",
			"first",
			"ground",
			"shed"
		].includes(e) ? this.tr(`settings.floors.${e}`) : this.tr(`house.${e}`);
	}
	get current() {
		let e = this.picture;
		return this.draft ?? {
			custom: !!e?.custom,
			items: e?.items ?? {},
			hidden: e?.hidden ?? []
		};
	}
	willUpdate() {
		let e = this.picture;
		e?.has_image && this.sign && e.version !== this.signed && (this.signed = e.version, this.sign(`/api/zephyr/house_picture?v=${e.version}`).then((e) => this.url = e, () => this.signed = -1));
	}
	render() {
		let e = this.picture, t = this.current, n = this.canEdit && !this.busy;
		return b`<h3>${this.tr("picture.title")}</h3>
      <div class="choice" role="radiogroup">
        <button
          type="button"
          role="radio"
          aria-checked=${!t.custom}
          class=${t.custom ? "" : "on"}
          ?disabled=${!n}
          @click=${() => this.patch({ custom: !1 })}
        >
          ${this.tr("picture.default")}
        </button>
        <button
          type="button"
          role="radio"
          aria-checked=${t.custom}
          class=${t.custom ? "on" : ""}
          ?disabled=${!n}
          @click=${() => e?.has_image ? this.patch({ custom: !0 }) : this.pickFile()}
        >
          ${this.tr("picture.own")}
        </button>
      </div>
      <p class="muted">${this.tr("picture.note")}</p>
      ${this.busy ? b`<p class="muted" role="status">${this.tr("picture.uploading")}</p>` : C}
      ${this.error ? b`<p class="err" role="alert">${this.tr("picture.error", { msg: this.error })}</p>` : C}
      <input
        type="file"
        accept="image/jpeg,image/png,image/webp"
        hidden
        @change=${this.onFile}
      />
      ${t.custom && e?.has_image ? this.renderPlacing(e, t, n) : C}
      ${this.draft && this.canEdit ? b`<div class="row">
              <button
                type="button"
                class="primary"
                ?disabled=${this.busy}
                @click=${() => void this.save()}
              >
                ${this.tr("settings.save")}
              </button>
              <button
                type="button"
                class="ghost"
                @click=${() => (this.draft = null, this.selected = null)}
              >
                ${this.tr("settings.discard")}
              </button>
            </div>` : C}`;
	}
	renderPlacing(e, t, n) {
		let r = e.width || 1600, i = e.height || 1200, a = this.selected, o = a && t.items[a]?.box && !t.items[a]?.point ? "point" : "box", s = G.filter((e) => !t.hidden.includes(e) && t.items[e]?.box);
		return b`<p class="hint">
        ${a ? this.tr(`picture.step_${o}`, { item: this.label(a) }) : this.tr("picture.pick")}
      </p>
      <div
        class=${n && a ? "stage active" : "stage"}
        style=${`aspect-ratio:${r}/${i}`}
        @click=${(e) => n && this.tap(e)}
      >
        ${this.url ? b`<img src=${this.url} alt="" draggable="false" />` : C}
        <svg viewBox="0 0 ${r} ${i}" aria-hidden="true">
          ${s.map((e) => {
			let n = t.items[e];
			if (!n?.box || !n.point) return C;
			let a = en(n.box, n.point, r, i), o = a[a.length - 1];
			return x`<path d=${`M${a.map((e) => e.join(" ")).join(" L")}`} stroke=${rn[e]} stroke-width=${r / 300} fill="none"></path>
              <circle cx=${o[0]} cy=${o[1]} r=${r / 150} fill=${rn[e]}></circle>`;
		})}
        </svg>
        ${s.map((e) => {
			let [n, r] = t.items[e]?.box ?? [0, 0];
			return b`<span
            class=${e === a ? "tag sel" : "tag"}
            style=${`left:${Math.min(n, 1 - $t) * 100}%;top:${r * 100}%;width:${$t * 100}%;--c:${rn[e]}`}
            >${this.label(e)}</span
          >`;
		})}
      </div>
      <div class="chips">
        ${G.map((e) => {
			let r = t.hidden.includes(e), i = !!t.items[e]?.point;
			return b`<button
            type="button"
            class=${[
				"chip",
				e === a ? "sel" : "",
				i ? "done" : "",
				r ? "hid" : ""
			].join(" ")}
            ?disabled=${!n}
            title=${r ? this.tr("picture.hidden") : i ? "" : this.tr("picture.unplaced")}
            @click=${() => this.selected = e === a ? null : e}
          >
            ${i && !r ? "✓ " : ""}${this.label(e)}
          </button>`;
		})}
      </div>
      <div class="row">
        ${a ? b`<button
                  type="button"
                  ?disabled=${!n}
                  @click=${() => this.toggleHidden(a)}
                >
                  ${t.hidden.includes(a) ? this.tr("picture.show") : this.tr("picture.hide")}
                </button>
                <button
                  type="button"
                  ?disabled=${!n}
                  @click=${() => this.place(a, {})}
                >
                  ${this.tr("picture.reset")}
                </button>` : C}
        <button
          type="button"
          class="ghost"
          ?disabled=${!n}
          @click=${() => this.pickFile()}
        >
          ${this.tr("picture.replace")}
        </button>
        <button
          type="button"
          class="ghost"
          ?disabled=${!n}
          @click=${() => void this.removePicture()}
        >
          ${this.tr("picture.delete")}
        </button>
      </div>`;
	}
	patch(e) {
		this.draft = {
			...this.current,
			...e
		};
	}
	place(e, t) {
		this.patch({ items: {
			...this.current.items,
			[e]: t
		} });
	}
	toggleHidden(e) {
		let t = this.current.hidden;
		this.patch({ hidden: t.includes(e) ? t.filter((t) => t !== e) : [...t, e] });
	}
	tap(e) {
		let t = this.selected;
		if (!t) return;
		let n = e.currentTarget.getBoundingClientRect(), r = [Math.round((e.clientX - n.left) / n.width * 1e3) / 1e3, Math.round((e.clientY - n.top) / n.height * 1e3) / 1e3], i = this.current.items[t] ?? {};
		!i.box || i.point ? this.place(t, { box: r }) : (this.place(t, {
			box: i.box,
			point: r
		}), this.selected = on(this.current.items, this.current.hidden, t));
	}
	pickFile() {
		this.renderRoot.querySelector("input[type=file]")?.click();
	}
	async save() {
		let e = this.draft;
		if (e && this.call) {
			this.busy = !0;
			try {
				await this.call({
					type: "zephyr/house/picture",
					custom: e.custom,
					items: e.items,
					hidden: e.hidden
				}), this.draft = null, this.selected = null, await this.changed?.();
			} catch (e) {
				this.error = e?.message ?? String(e);
			} finally {
				this.busy = !1;
			}
		}
	}
	async removePicture() {
		if (this.call) {
			this.busy = !0;
			try {
				await this.call({ type: "zephyr/house/picture/delete" }), this.draft = null, this.selected = null, this.url = null, await this.changed?.();
			} finally {
				this.busy = !1;
			}
		}
	}
	static {
		this.styles = s`
    :host {
      display: block;
      margin: 8px 0 20px;
    }
    h3 {
      font-size: 15px;
      font-weight: 600;
      margin: 0 0 8px;
    }
    .muted,
    .hint {
      color: var(--z-muted);
      font-size: 13px;
      margin: 8px 0;
    }
    .hint {
      color: var(--z-text);
    }
    .err {
      color: var(--z-danger, #c62828);
      font-size: 13px;
    }
    .choice,
    .row,
    .chips {
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
    }
    .row {
      margin-top: 12px;
    }
    button {
      font: inherit;
      font-size: 13px;
      padding: 7px 12px;
      border-radius: 10px;
      border: 1px solid var(--z-border);
      background: var(--z-card);
      color: var(--z-text);
      cursor: pointer;
    }
    button:disabled {
      opacity: 0.6;
      cursor: not-allowed;
    }
    button.on,
    button.primary {
      background: var(--z-text);
      color: var(--z-card);
      border-color: var(--z-text);
    }
    button.ghost {
      border-color: transparent;
      text-decoration: underline;
    }
    .chip {
      padding: 4px 10px;
      border-radius: 999px;
    }
    .chip.done {
      border-color: #2e9e6a;
    }
    .chip.sel {
      outline: 2px solid #3b82f6;
    }
    .chip.hid {
      text-decoration: line-through;
      opacity: 0.6;
    }
    .stage {
      position: relative;
      width: 100%;
      max-width: 760px;
      border-radius: 12px;
      overflow: hidden;
      background: #0f1d27;
      margin: 8px 0 12px;
      user-select: none;
    }
    .stage.active {
      cursor: crosshair;
    }
    .stage img {
      display: block;
      width: 100%;
      height: 100%;
    }
    .stage svg {
      position: absolute;
      inset: 0;
      width: 100%;
      height: 100%;
      pointer-events: none;
    }
    .tag {
      position: absolute;
      box-sizing: border-box;
      padding: 4px 8px;
      font-size: 12px;
      color: #fff;
      background: rgba(12, 26, 36, 0.9);
      border: 2px solid var(--c);
      border-radius: 8px;
      pointer-events: none;
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
    }
    .tag.sel {
      box-shadow: 0 0 0 2px #3b82f6;
    }
  `;
	}
};
R([E({ attribute: !1 })], q.prototype, "picture", void 0), R([E({ attribute: !1 })], q.prototype, "canEdit", void 0), R([E({ attribute: !1 })], q.prototype, "uiLang", void 0), R([E({ attribute: !1 })], q.prototype, "call", void 0), R([E({ attribute: !1 })], q.prototype, "sign", void 0), R([E({ attribute: !1 })], q.prototype, "changed", void 0), R([D()], q.prototype, "draft", void 0), R([D()], q.prototype, "selected", void 0), R([D()], q.prototype, "busy", void 0), R([D()], q.prototype, "error", void 0), R([D()], q.prototype, "url", void 0), q = R([e("zephyr-house-editor")], q);
// src/settings-edit.ts
function sn(e, t) {
	let n = e.trim().replace(/\s/g, "");
	if (!n || (n = (new Intl.NumberFormat(t).format(1.5).includes(",") ? "," : ".") == "," ? n.replace(/\.(?=\d{3}(\D|$))/g, "").replace(",", ".") : n.replace(/,(?=\d{3}(\D|$))/g, ""), !/^[-+]?\d*\.?\d+$/.test(n))) return null;
	let r = Number(n);
	return Number.isFinite(r) ? r : null;
}
function cn(e, t, n) {
	return e ? Object.entries(e).filter(([e, r]) => e.startsWith(`${t}.`) && (!n || r.attributes?.device_class === n)).map(([e, t]) => ({
		id: e,
		name: String(t.attributes?.friendly_name ?? e)
	})).sort((e, t) => e.name.localeCompare(t.name) || e.id.localeCompare(t.id)) : [];
}
function ln(e, t) {
	let n = e.trim();
	if (!n) return null;
	let r = t.find((e) => e.id === n);
	if (r) return r.id;
	let i = /\(([a-z0-9_]+\.[a-z0-9_]+)\)$/.exec(n);
	if (i && t.some((e) => e.id === i[1])) return i[1];
	let a = t.filter((e) => e.name.toLowerCase() === n.toLowerCase());
	return a.length === 1 ? a[0].id : null;
}
function un(e) {
	return e.name === e.id ? e.id : `${e.name} (${e.id})`;
}
function dn(e, t) {
	return Array.isArray(e) && Array.isArray(t) ? e.length === t.length && e.every((e, n) => e === t[n]) : (e ?? null) === (t ?? null);
}
function fn(e, t, n) {
	let r = e.includes(t) ? e.filter((e) => e !== t) : [...e, t];
	return n.filter((e) => r.includes(e));
}
function pn(e, t) {
	return e < 90 ? `${Math.round(e)} s` : `${new Intl.NumberFormat(t, { maximumFractionDigits: 1 }).format(e / 60)} min`;
}
function mn(e, t, n = 8) {
	let r = t.toLowerCase().split(/[\s()]+/).filter(Boolean);
	if (!r.length) return e.slice(0, n);
	let i = [];
	for (let t of e) {
		let e = t.name.toLowerCase(), n = t.id.toLowerCase();
		if (!r.every((t) => e.includes(t) || n.includes(t))) continue;
		let a = r[0], o = e.startsWith(a) ? 0 : RegExp(`(^|[\\s._-])${a.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")}`).test(`${e} ${n}`) ? 1 : 2;
		i.push([o, t]);
	}
	return i.sort((e, t) => e[0] - t[0] || e[1].name.localeCompare(t[1].name)).slice(0, n).map(([, e]) => e);
}
function hn(e, t) {
	let n = /^([a-z_]+)\.[a-z0-9_]+$/.exec(e.trim());
	return n && n[1] !== t ? n[1] : null;
}
// src/settings.ts
var gn = Symbol("reset");
function _n(e, t) {
	if (!e.show_if) return !0;
	let n = t(e.show_if.key);
	return e.show_if.values.includes("*") ? Array.isArray(n) ? n.length > 0 : n != null && n !== "" : typeof n == "string" && e.show_if.values.includes(n);
}
function vn(e) {
	let t = [];
	for (let n of e) n.section && !t.includes(n.section) && t.push(n.section);
	return t;
}
function yn(e, t) {
	return Object.fromEntries(Object.entries(e).filter(([e]) => t(e)));
}
function bn(e, t, n) {
	let r = typeof t == "number" && t < 1 ? Math.min(5, Math.max(0, Math.ceil(-Math.log10(t) - 1e-9))) : t === "any" ? 5 : 0;
	return new Intl.NumberFormat(n, {
		minimumFractionDigits: 0,
		maximumFractionDigits: r
	}).format(e);
}
function xn(e, t) {
	return e.tariff && e.active === !1 && e.in_use !== void 0 && e.in_use !== null ? e.in_use : t;
}
var J = class extends T {
	constructor(...e) {
		super(...e), this.uiLang = "en", this.locale = "en", this.friendlyName = () => void 0, this.group = 0, this.openGroup = null, this.openedFor = null, this.tip = null, this.sectionOf = {}, this.draft = {}, this.errors = {}, this.busy = !1, this.saved = null, this.restarting = !1, this.houseDraft = null, this.vacUntil = null, this.domainErrors = {}, this.pickFor = null, this.pickQuery = "", this.pickIndex = 0;
	}
	applyOpenGroup(e) {
		if ((e.has("openGroup") || e.has("view")) && this.openGroup && this.view && this.openedFor !== this.openGroup) {
			let [e, t] = this.openGroup.split(":"), n = this.view.groups.findIndex((t) => t.key === e);
			n >= 0 && (this.group = n, t && (this.sectionOf = {
				...this.sectionOf,
				[e]: t
			}), this.openedFor = this.openGroup);
		}
	}
	willUpdate(e) {
		e.has("view") && e.get("view") !== void 0 && (this.restarting = !1), this.applyOpenGroup(e);
	}
	get editable() {
		return !!(this.view?.can_edit && this.save);
	}
	shown(e) {
		if (!(e.key in this.draft)) return e.value;
		let t = this.draft[e.key];
		return t === gn ? e.default : t;
	}
	isModified(e) {
		if (e.kind === "entity" || e.kind === "entities") return !1;
		if (!(e.key in this.draft)) return e.modified;
		let t = this.draft[e.key];
		return t !== gn && !dn(t, e.default) && (!e.optional || t !== null && t !== "");
	}
	change(e, t) {
		let { [e.key]: n, ...r } = this.errors;
		if (this.errors = r, e.reload) {
			let { [e.key]: n, ...r } = this.draft;
			this.draft = dn(t, e.value) ? r : {
				...r,
				[e.key]: t
			};
		} else dn(t, e.value) || this.send({ [e.key]: t }, [], e.key);
	}
	reset(e) {
		e.reload ? this.draft = {
			...this.draft,
			[e.key]: gn
		} : this.send({}, [e.key], e.key);
	}
	showErrorSection(e) {
		for (let t of e) {
			let e = this.fieldByKey(t), n = this.view?.groups.find((e) => e.fields.some((e) => e.key === t));
			if (e?.section && n) {
				this.sectionOf = {
					...this.sectionOf,
					[n.key]: e.section
				};
				return;
			}
		}
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
			}, this.showErrorSection(Object.keys(r.errors ?? {})), !1);
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
		let e = {}, t = [], n = (e) => {
			let t = this.fieldByKey(e);
			return !t || this.visible(t);
		};
		for (let [r, i] of Object.entries(yn(this.draft, n))) i === gn ? t.push(r) : e[r] = i;
		let { base: r, ...i } = this.errors;
		this.errors = i, await this.send(e, t, null) && (this.draft = {}, this.restarting = !0);
	}
	cancelDraft() {
		this.draft = {}, this.errors = {};
	}
	tr(e, t = {}) {
		return F(this.uiLang, e, t);
	}
	label(e) {
		return this.tr(`settings.fields.${e}.label`);
	}
	render() {
		let e = this.view;
		if (!e) return b`<div class="card skeleton" aria-hidden="true"></div>`;
		let t = Math.min(this.group, e.groups.length - 1), n = e.groups[t];
		return b`<div class="layout">
      <nav class="card groups" aria-label=${this.tr("settings.title")}>
        ${e.groups.map((e, n) => b`<button
              type="button"
              class=${n === t ? "on" : ""}
              aria-current=${n === t ? "true" : "false"}
              @click=${() => {
			this.group = n, this.tip = null;
		}}
            >
              <span>${this.tr(`settings.groups.${e.key}`)}</span>
              ${this.groupSub(e)}
            </button>`)}
      </nav>
      <section class="card fields" aria-labelledby="group-title">
        <div class="head">
          <h2 id="group-title">${this.tr(`settings.groups.${n.key}`)}</h2>
        </div>
        ${e.can_edit ? C : b`<p class="note">${this.tr("settings.readonly")}</p>`}
        ${this.restarting ? b`<p class="note" role="status">${this.tr("settings.restarting")}</p>` : C}
        ${n.fields.some((e) => e.reload) ? b`<p class="muted">${this.tr("settings.reload_note")}</p>` : C}
        ${n.key === "tariffs" && e.supplier !== "own" ? b`<p class="muted">
                ${this.tr("settings.supplier_note", { source: e.tariffs_source ?? "–" })}
              </p>` : C}
        ${n.key === "vacation" && e.vacation ? this.renderVacation(e.vacation, e.can_edit) : C}
        ${n.key === "house" ? b`<zephyr-house-editor
                .picture=${e.house_picture ?? null}
                .canEdit=${e.can_edit}
                .uiLang=${this.uiLang}
                .call=${this.houseCall}
                .sign=${this.sign}
                .changed=${this.reload}
              ></zephyr-house-editor>` : C}
        ${n.key === "house" ? this.renderHouse(e.house ?? [], e.can_edit) : C}
        ${this.renderSections(n)}
        <ul>
          ${this.sectionFields(n).map((e) => this.renderField(e))}
        </ul>
        ${this.renderBar()}
      </section>
    </div>`;
	}
	activeSection(e) {
		let t = vn(e.fields);
		if (!t.length) return null;
		let n = this.sectionOf[e.key];
		return n && t.includes(n) ? n : t[0];
	}
	sectionFields(e) {
		let t = this.activeSection(e);
		return t ? e.fields.filter((e) => e.section === t) : e.fields;
	}
	groupSub(e) {
		let t = vn(e.fields), n = t.length ? t.map((e) => this.tr(`settings.sections.${e}`).toLowerCase()).join(" · ") : this.tr(`settings.group_sub.${e.key}`);
		return n && n !== `settings.group_sub.${e.key}` ? b`<small>${n}</small>` : C;
	}
	renderSections(e) {
		let t = vn(e.fields);
		if (t.length < 2) return C;
		let n = this.activeSection(e);
		return b`<div
      class="subtabs"
      role="tablist"
      aria-label=${this.tr(`settings.groups.${e.key}`)}
    >
      ${t.map((t) => {
			let r = e.fields.some((e) => e.section === t && (this.isModified(e) || e.key in this.draft));
			return b`<button
          type="button"
          role="tab"
          aria-selected=${t === n ? "true" : "false"}
          class=${t === n ? "on" : ""}
          @click=${() => {
				this.sectionOf = {
					...this.sectionOf,
					[e.key]: t
				}, this.tip = null;
			}}
        >
          ${this.tr(`settings.sections.${t}`)}${r ? b`<i class="dot" aria-hidden="true"></i>` : C}
        </button>`;
		})}
    </div>`;
	}
	renderHouse(e, t) {
		if (!e.length) return b`<p class="muted">${this.tr("stroom.devices_hint")}</p>`;
		let n = new Map((this.appliances?.appliances ?? []).map((e) => [e.id, e])), r = (e) => (e ?? "").slice(0, 5), i = (e) => {
			let t = n.get(e.id);
			return {
				floor: e.floor,
				shown: e.shown,
				from: r(t?.window.from),
				until: r(t?.window.until),
				after: !!t?.after_washer
			};
		}, a = this.houseDraft ?? Object.fromEntries(e.map((e) => [e.id, i(e)])), o = (e, t) => {
			this.houseDraft = {
				...a,
				[e]: {
					...a[e],
					...t
				}
			};
		}, s = (e, t) => a[e.id][t] !== i(e)[t], c = e.some((e) => Object.keys(a[e.id]).some((t) => s(e, t))), l = [
			"attic",
			"first",
			"ground",
			"shed",
			"outside"
		], u = async () => {
			let t = e.filter((e) => n.has(e.id) && (s(e, "from") || s(e, "until") || s(e, "after"))).map((e) => ({
				id: e.id,
				window_from: a[e.id].from,
				window_until: a[e.id].until || "20:00",
				...n.get(e.id)?.kind.startsWith("dryer") ? { after_washer: a[e.id].after } : {}
			}));
			e.some((e) => s(e, "floor") || s(e, "shown")) && await this.saveHouse?.(Object.fromEntries(e.map((e) => [e.id, a[e.id].floor])), e.filter((e) => !a[e.id].shown).map((e) => e.id)), t.length && await this.saveAppliances?.(t), this.houseDraft = null;
		};
		return b`<p class="muted">${this.tr("settings.house_note")}</p>
      <ul class="house">
        ${e.map((e) => {
			let r = n.get(e.id), i = a[e.id];
			return b`<li>
            <div class="hname">
              <b>${e.name ?? this.tr(`stroom.kind_${e.kind}`)}</b>
              <small
                >${r ? r.profile === "learned" ? this.tr("settings.appl_learned", { n: r.runs_seen }) : this.tr("settings.appl_default") : this.tr("settings.appl_airco")}</small
              >
            </div>
            <div class="hfields">
              ${r ? b`<label
                        >${this.tr("settings.appl_from")}<input
                          type="time"
                          .value=${i.from}
                          ?disabled=${!t}
                          @input=${(t) => o(e.id, { from: t.target.value })}
                      /></label>
                      <label
                        >${this.tr("settings.appl_until")}<input
                          type="time"
                          .value=${i.until}
                          ?disabled=${!t}
                          @input=${(t) => o(e.id, { until: t.target.value })}
                      /></label>` : C}
              <label
                >${this.tr("settings.house_floor")}<select
                  .value=${i.floor}
                  ?disabled=${!t}
                  @change=${(t) => o(e.id, { floor: t.target.value })}
                >
                  ${l.map((e) => b`<option value=${e} ?selected=${e === i.floor}>${this.tr(`settings.floors.${e}`)}</option>`)}
                </select></label
              >
              <label class="check"
                ><input
                  type="checkbox"
                  .checked=${i.shown}
                  ?disabled=${!t}
                  @change=${(t) => o(e.id, { shown: t.target.checked })}
                />${this.tr("settings.appl_shown")}</label
              >
              ${r?.kind.startsWith("dryer") ? b`<label class="check wide"
                      ><input
                        type="checkbox"
                        .checked=${i.after}
                        ?disabled=${!t}
                        @change=${(t) => o(e.id, { after: t.target.checked })}
                      /><span
                        ><b>${this.tr("settings.appl_after")}</b> —
                        ${this.tr("settings.appl_after_help")}</span
                      ></label
                    >` : C}
            </div>
          </li>`;
		})}
      </ul>
      ${c && t ? b`<div class="vacrow">
              <button type="button" class="primary" @click=${() => void u()}>
                ${this.tr("settings.save")}
              </button>
              <button
                type="button"
                class="ghost"
                @click=${() => this.houseDraft = null}
              >
                ${this.tr("settings.discard")}
              </button>
            </div>` : C}`;
	}
	renderVacation(e, t) {
		let n = (e) => new Intl.DateTimeFormat(this.locale, {
			weekday: "short",
			day: "numeric",
			month: "long",
			hour: "2-digit",
			minute: "2-digit"
		}).format(new Date(e)), r = e.active ? e.auto ? this.tr("settings.vac_auto", { since: e.started ? n(e.started) : "–" }) : e.until ? this.tr("settings.vac_until", { until: n(e.until) }) : this.tr("settings.vac_open") : this.tr("settings.vac_off"), i = this.vacUntil ?? (e.until ? e.until.slice(0, 16) : "");
		return b`<div class=${e.active ? "vac on" : "vac"}>
      <div class="vachead">
        <span class="vacdot" aria-hidden="true"></span>
        <div>
          <strong
            >${this.tr(e.active ? "settings.vac_active" : "settings.vac_home")}</strong
          >
          <p>${r}</p>
        </div>
      </div>
      ${t ? b`<div class="vacrow">
                <label for="vac-until"
                  >${this.tr("settings.vac_until_label")}</label
                >
                <input
                  id="vac-until"
                  type="datetime-local"
                  .value=${i}
                  @change=${(e) => this.vacUntil = e.target.value || null}
                />
                ${e.active ? b`<button
                        type="button"
                        class="ghost"
                        @click=${() => void this.setVacation?.(!1, null)}
                      >
                        ${this.tr("settings.vac_stop")}
                      </button>` : b`<button
                        type="button"
                        class="primary"
                        @click=${() => void this.setVacation?.(!0, i || null)}
                      >
                        ${this.tr("settings.vac_start")}
                      </button>`}
              </div>
              <p class="muted">${this.tr("settings.vac_help")}</p>` : C}
    </div>`;
	}
	renderBar() {
		let e = Object.keys(yn(this.draft, (e) => {
			let t = this.fieldByKey(e);
			return !t || this.visible(t);
		})).length, t = this.errors.base;
		return !e && !t ? C : b`<div
      class="bar"
      role="region"
      aria-label=${this.tr("settings.pending", { n: e })}
    >
      ${t ? b`<p class="error" role="alert">${this.tr(`settings.errors.${t}`)}</p>` : C}
      ${e ? b`<div class="barrow">
              <span
                >${this.tr(e === 1 ? "settings.pending_one" : "settings.pending", { n: e })}</span
              >
              <span class="buttons">
                <button
                  type="button"
                  class="ghost"
                  ?disabled=${this.busy}
                  @click=${() => this.cancelDraft()}
                >
                  ${this.tr("settings.cancel")}
                </button>
                <button
                  type="button"
                  class="primary"
                  ?disabled=${this.busy}
                  @click=${() => void this.saveDraft()}
                >
                  ${this.tr(this.busy ? "settings.saving" : "settings.save_restart")}
                </button>
              </span>
            </div>` : C}
    </div>`;
	}
	fieldByKey(e) {
		return this.view?.groups.flatMap((e) => e.fields).find((t) => t.key === e);
	}
	visible(e) {
		return _n(e, (e) => {
			let t = this.fieldByKey(e);
			return t ? this.shown(t) : void 0;
		});
	}
	curtailWarning(e) {
		if (e.key !== "curtail_inverter_w" || !this.visible(e)) return !1;
		let t = this.view?.groups.flatMap((e) => e.fields).find((e) => e.key === "curtail_number");
		return !!t && !!this.shown(t) && !this.shown(e);
	}
	renderField(e) {
		let t = this.tip === e.key, n = `f-${e.key}`;
		return this.visible(e) ? b`${e.key === "curtail_switch" ? b`<li class="subhead">
              <b>${this.tr("settings.curtail_head")}</b>
            </li>` : C}
      <li class=${e.active === !1 ? "inactive" : ""}>
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
            ${this.isModified(e) ? b`<span class="dot" title=${this.defaultText(e)}></span>` : C}
            ${e.key in this.draft ? b`<span class="pending">${this.tr("settings.not_saved")}</span>` : C}
            ${this.saved === e.key ? b`<span class="saved" role="status">${this.tr("settings.saved")}</span>` : C}
          </div>
          <span class="help">${this.tr(`settings.fields.${e.key}.help`)}</span>
          ${t ? b`<div class="more" role="note">
                  ${this.tr(`settings.fields.${e.key}.more`, { in_use: e.in_use === void 0 || e.in_use === null ? "–" : this.display(e, e.in_use) })}
                </div>` : C}
          ${this.meta(e)}
          ${this.errors[e.key] ? b`<span class="error" role="alert">${this.errorText(e, this.errors[e.key])}</span>` : C}
          ${this.curtailWarning(e) ? b`<span class="warnline" role="note">${this.tr("settings.curtail_rated_missing")}</span>` : C}
        </div>
        <div class="control">${this.control(e, n)}</div>
      </li>` : b``;
	}
	errorText(e, t) {
		return t === "entity_domain" ? this.tr("settings.errors.entity_domain", { domain: this.domainErrors[e.key] ?? e.domain }) : t === "out_of_range" && e.min !== null && e.max !== null ? this.tr("settings.errors.range", {
			min: bn(e.min, e.step, this.locale),
			max: bn(e.max, e.step, this.locale),
			unit: e.unit ? ` ${e.unit}` : ""
		}) : this.tr(`settings.errors.${t}`);
	}
	defaultText(e) {
		return this.tr("settings.default", { value: this.display(e, e.default) });
	}
	display(e, t) {
		return t == null || t === "" || Array.isArray(t) && !t.length ? this.tr("settings.none") : e.kind === "bool" ? this.tr(t ? "settings.yes" : "settings.no") : e.kind === "number" ? `${bn(Number(t), e.step, this.locale)}${e.unit ? ` ${e.unit}` : ""}` : e.kind === "select" ? e.key === "tariff_supplier" ? e.choices?.find((e) => e.value === t)?.label ?? this.tr("settings.own") : Array.isArray(t) ? t.map((e) => this.tr(`settings.options.${e}`)).join(", ") : this.tr(`settings.options.${String(t)}`) : (Array.isArray(t) ? t : [String(t)]).map((e) => this.friendlyName(e) ?? e).join(", ");
	}
	meta(e) {
		let t = [], n = this.isModified(e);
		n && t.push(this.defaultText(e));
		let r = e.status;
		r && (r.state === "unset" ? t.push(this.tr("settings.status.unset")) : r.state === "missing" ? t.push(this.tr("settings.status.missing", { entities: (r.entities ?? []).join(", ") })) : r.state === "unavailable" ? t.push(this.tr("settings.status.unavailable")) : r.mode === void 0 ? r.no_step ? t.push(this.tr("settings.status.no_step")) : r.step_interval_s != null && r.step_kwh != null ? t.push(this.tr("settings.status.steps", {
			every: pn(r.step_interval_s, this.locale),
			kwh: bn(r.step_kwh, .01, this.locale)
		})) : r.interval_s == null ? r.price_slots == null ? t.push(this.tr("settings.status.ok")) : t.push(this.tr("settings.status.slots", { n: r.price_slots })) : t.push(this.tr("settings.status.interval", { s: bn(r.interval_s, .1, this.locale) })) : t.push(r.action ? this.tr("settings.status.climate", {
			mode: this.tr(`settings.options.${r.mode}`),
			action: this.tr(`settings.actions.${r.action}`)
		}) : this.tr(`settings.options.${r.mode}`)));
		let i = n && this.editable && !(e.key in this.draft && this.draft[e.key] === gn);
		return !t.length && !i ? C : b`<span class=${r && r.state !== "ok" && r.state !== "unset" ? "meta warn" : "meta"}
      >${t.join(" · ")}${i ? b` <button
              type="button"
              class="link"
              ?disabled=${this.busy}
              @click=${() => this.reset(e)}
            >
              ${this.tr("settings.reset")}
            </button>` : C}</span
    >`;
	}
	control(e, t) {
		let n = !this.editable || this.busy || e.active === !1 && e.tariff, r = xn(e, this.shown(e));
		switch (e.kind) {
			case "bool": return b`<button
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
			case "number": return b`<span class="num">
          <input
            id=${t}
            type="text"
            inputmode="decimal"
            .value=${r == null ? "" : bn(Number(r), e.step, this.locale)}
            ?disabled=${n}
            aria-invalid=${this.errors[e.key] ? "true" : "false"}
            @change=${(t) => this.numberChanged(e, t.target)}
            @keydown=${(e) => e.key === "Enter" && e.target.blur()}
          />${e.unit ? b`<span class="unit">${e.unit}</span>` : C}
        </span>`;
			case "select": return e.multiple ? this.multi(e, t, r ?? [], n) : b`<select
          id=${t}
          ?disabled=${n}
          @change=${(t) => this.change(e, t.target.value)}
        >
          ${(e.choices ?? e.options.map((e) => ({
				value: e,
				label: null
			}))).map((t) => b`<option value=${t.value} ?selected=${t.value === r}>
                ${t.label ?? (e.key === "tariff_supplier" ? this.tr("settings.own") : this.tr(`settings.options.${t.value}`))}
              </option>`)}
        </select>`;
			case "entities": return this.entities(e, t, r ?? [], n);
			default: return this.entity(e, t, r ?? null, n);
		}
	}
	numberChanged(e, t) {
		let n = sn(t.value, this.locale);
		n === null ? !t.value.trim() && e.optional ? this.change(e, null) : this.localError(e, t.value.trim() ? "not_a_number" : "required") : this.change(e, n);
	}
	multi(e, t, n, r) {
		return b`<div
      id=${t}
      class="chips"
      role="group"
      aria-label=${this.label(e.key)}
    >
      ${e.options.map((t) => b`<button
            type="button"
            class="chip"
            aria-pressed=${n.includes(t) ? "true" : "false"}
            ?disabled=${r}
            @click=${() => {
			let r = fn(n, t, e.options);
			r.length ? this.change(e, r) : this.localError(e, "choose_one");
		}}
          >
            ${this.tr(`settings.options.${t}`)}
          </button>`)}
    </div>`;
	}
	choices(e) {
		return cn(this.states, e.domain, e.device_class);
	}
	picker(e, t, n, r, i) {
		let a = this.choices(e), o = this.pickFor === t, s = o ? mn(a, this.pickQuery) : [], c = (t) => {
			this.pickFor = null;
			let n = hn(t, e.domain), r = ln(t, a);
			!r && n ? (this.domainErrors = {
				...this.domainErrors,
				[e.key]: e.domain
			}, this.localError(e, "entity_domain")) : i(r, t);
		}, l = (e) => {
			this.pickFor = null, i(e.id, e.id);
		};
		return b`<span class="pickwrap">
      <input
        id=${t}
        class="pick"
        type="text"
        role="combobox"
        aria-expanded=${o && s.length ? "true" : "false"}
        aria-controls=${`${t}-list`}
        aria-autocomplete="list"
        placeholder=${this.tr("settings.choose_entity")}
        autocomplete="off"
        .value=${o ? this.pickQuery : n}
        ?disabled=${r}
        aria-invalid=${this.errors[e.key] ? "true" : "false"}
        @focus=${(e) => {
			this.pickFor = t, this.pickQuery = "", this.pickIndex = 0, e.target.select();
		}}
        @input=${(e) => {
			this.pickQuery = e.target.value, this.pickIndex = 0;
		}}
        @keydown=${(e) => {
			if (o) {
				if (e.key === "ArrowDown") this.pickIndex = Math.min(s.length - 1, this.pickIndex + 1);
				else if (e.key === "ArrowUp") this.pickIndex = Math.max(0, this.pickIndex - 1);
				else if (e.key === "Enter") s[this.pickIndex] && this.pickQuery.trim() ? l(s[this.pickIndex]) : c(this.pickQuery);
				else if (e.key === "Escape") this.pickFor = null;
				else return;
				e.preventDefault();
			}
		}}
        @blur=${() => {
			if (this.pickFor !== t) return;
			let e = this.pickQuery;
			this.pickFor = null, e.trim() && c(e);
		}}
      />
      ${o && s.length ? b`<ul class="picklist" id=${`${t}-list`} role="listbox">
              ${s.map((e, t) => b`<li
                    role="option"
                    aria-selected=${t === this.pickIndex ? "true" : "false"}
                    class=${t === this.pickIndex ? "on" : ""}
                    @mousedown=${(t) => {
			t.preventDefault(), l(e);
		}}
                  >
                    <span>${e.name}</span><small>${e.id}</small>
                  </li>`)}
            </ul>` : C}
    </span>`;
	}
	entity(e, t, n, r) {
		let i = n ? this.choices(e).find((e) => e.id === n) ?? {
			id: n,
			name: this.friendlyName(n) ?? n
		} : null;
		return b`<span class="entityrow">
      ${this.picker(e, t, i ? un(i) : "", r, (t, n) => {
			t ? this.change(e, t) : n.trim() ? this.localError(e, "entity_missing") : e.optional ? this.change(e, null) : this.localError(e, "required");
		})}
      ${n && e.optional ? b`<button
              type="button"
              class="clear"
              ?disabled=${r}
              aria-label=${this.tr("settings.clear")}
              @click=${() => this.change(e, null)}
            >
              ×
            </button>` : C}
    </span>`;
	}
	entities(e, t, n, r) {
		return b`<div class="multi">
      ${n.length ? b`<ul class="chips">
              ${n.map((t) => b`<li class="chip on">
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
            </ul>` : C}
      ${this.picker(e, t, "", r, (t, r) => {
			t ? n.includes(t) || this.change(e, [...n, t]) : r.trim() && this.localError(e, "entity_missing");
		})}
    </div>`;
	}
	static {
		this.styles = s`
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
    .groups button {
      flex-direction: column;
      align-items: flex-start;
      justify-content: center;
      gap: 1px;
      text-align: left;
    }
    .groups small {
      font-size: 12px;
      font-weight: 400;
      color: var(--z-muted);
    }
    .groups button.on small {
      color: inherit;
      opacity: 0.7;
    }
    .subtabs {
      display: flex;
      gap: 2px;
      padding: 4px;
      align-self: flex-start;
      max-width: 100%;
      overflow-x: auto;
      border: 1px solid var(--z-border);
      border-radius: 999px;
      background: var(--z-track);
    }
    .subtabs button {
      display: flex;
      align-items: center;
      gap: 6px;
      min-height: 36px;
      padding: 0 16px;
      border: 0;
      border-radius: 999px;
      background: transparent;
      color: var(--z-text);
      font: inherit;
      font-weight: 600;
      white-space: nowrap;
      cursor: pointer;
    }
    .subtabs button.on {
      background: var(--z-text);
      color: var(--z-on-text);
    }
    .subtabs button:focus-visible {
      outline: 2px solid var(--z-charge);
      outline-offset: 2px;
    }
    .subtabs .dot {
      display: inline-block;
      width: 7px;
      height: 7px;
    }
    .groups button:focus-visible,
    .info:focus-visible {
      outline: 2px solid var(--z-charge);
      outline-offset: 2px;
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
    .vac {
      display: flex;
      flex-direction: column;
      gap: 10px;
      padding: 14px 16px;
      border-radius: 12px;
      border: 1px solid var(--z-border);
      background: var(--z-bg);
      margin-bottom: 8px;
    }
    .vac.on {
      border-color: var(--z-charge);
      background: var(--z-info-bg);
    }
    .vachead {
      display: flex;
      gap: 12px;
      align-items: flex-start;
    }
    .vachead p {
      margin: 2px 0 0;
      font-size: 13px;
      color: var(--z-muted);
    }
    .vacdot {
      width: 12px;
      height: 12px;
      margin-top: 4px;
      border-radius: 50%;
      background: var(--z-muted);
      flex: none;
    }
    .vac.on .vacdot {
      background: var(--z-charge);
    }
    .vacrow {
      display: flex;
      flex-wrap: wrap;
      align-items: center;
      gap: 8px 12px;
      font-size: 14px;
    }
    .vacrow input {
      min-width: 220px;
      min-height: 40px;
      padding: 0 10px;
      border: 1px solid var(--z-border);
      border-radius: 10px;
      background: var(--z-card);
      color: var(--z-text);
      font: inherit;
    }
    .vacrow button {
      min-height: 40px;
      padding: 0 16px;
      border-radius: 10px;
      font: inherit;
      font-size: 14px;
      font-weight: 600;
      cursor: pointer;
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
    ul.house {
      list-style: none;
      margin: 0 0 8px;
      padding: 0;
    }
    ul.house li {
      display: grid;
      grid-template-columns: 200px 1fr;
      gap: 10px 20px;
      padding: 14px 0;
      border-bottom: 1px solid var(--z-border);
    }
    .hname {
      display: flex;
      flex-direction: column;
      align-items: flex-start;
      text-align: left;
      justify-self: stretch;
      justify-content: flex-start;
    }
    .hname small {
      color: var(--z-muted);
      font-size: 12px;
      font-weight: 400;
    }
    .hfields {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
      gap: 10px 14px;
      align-items: end;
    }
    .hfields label {
      font-weight: 400;
      text-align: left;
      display: flex;
      flex-direction: column;
      gap: 4px;
      font-size: 12.5px;
      color: var(--z-muted);
    }
    .hfields input[type="time"] {
      min-height: 40px;
      padding: 0 10px;
      border: 1px solid var(--z-border);
      border-radius: 10px;
      background: var(--z-card);
      color: var(--z-text);
      font: inherit;
    }
    .hfields label.check {
      flex-direction: row;
      align-items: center;
      gap: 8px;
      min-height: 40px;
      color: var(--z-text);
      font-size: 13.5px;
    }
    .hfields label.wide {
      grid-column: 1 / -1;
    }
    .hfields input[type="checkbox"] {
      width: 20px;
      height: 20px;
      min-width: 0;
      min-height: 0;
      margin: 0;
      accent-color: var(--z-charge);
    }
    @media (max-width: 700px) {
      ul.house li {
        grid-template-columns: 1fr;
      }
    }
    .hfields select {
      min-height: 40px;
      padding: 0 10px;
      border: 1px solid var(--z-border);
      border-radius: 10px;
      background: var(--z-card);
      color: var(--z-text);
      font: inherit;
    }
    li.subhead {
      display: flex;
      flex-direction: column;
      gap: 2px;
      padding: 14px 0 0;
    }
    .warnline {
      color: var(--z-warn-text, #7a4a06);
      background: var(--z-warn-bg, #fdf0dc);
      border-radius: 8px;
      padding: 6px 10px;
      font-size: 12.5px;
    }
    .pickwrap {
      position: relative;
      display: inline-block;
      flex: 1 1 auto;
      min-width: 0;
    }
    .pickwrap .pick {
      width: 100%;
    }
    .picklist {
      position: absolute;
      z-index: 5;
      left: 0;
      right: 0;
      top: calc(100% + 4px);
      margin: 0;
      padding: 0;
      list-style: none;
      background: var(--z-card);
      border: 1px solid var(--z-border);
      border-radius: 10px;
      box-shadow: 0 8px 20px rgba(0, 0, 0, 0.12);
      max-height: 300px;
      overflow: auto;
    }
    .picklist li {
      display: flex;
      flex-direction: column;
      padding: 8px 10px;
      border-top: 1px solid var(--z-border);
      cursor: pointer;
    }
    .picklist li:first-child {
      border-top: 0;
    }
    .picklist li.on,
    .picklist li:hover {
      background: color-mix(in srgb, var(--z-charge) 10%, var(--z-card));
    }
    .picklist small {
      color: var(--z-muted);
      font-size: 11.5px;
      word-break: break-all;
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
      .groups small {
        display: none;
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
R([E({ attribute: !1 })], J.prototype, "view", void 0), R([E({ attribute: !1 })], J.prototype, "uiLang", void 0), R([E()], J.prototype, "locale", void 0), R([E({ attribute: !1 })], J.prototype, "friendlyName", void 0), R([E({ attribute: !1 })], J.prototype, "states", void 0), R([E({ attribute: !1 })], J.prototype, "save", void 0), R([D()], J.prototype, "group", void 0), R([E({ attribute: !1 })], J.prototype, "openGroup", void 0), R([D()], J.prototype, "tip", void 0), R([D()], J.prototype, "sectionOf", void 0), R([D()], J.prototype, "draft", void 0), R([D()], J.prototype, "errors", void 0), R([D()], J.prototype, "busy", void 0), R([D()], J.prototype, "saved", void 0), R([D()], J.prototype, "restarting", void 0), R([E({ attribute: !1 })], J.prototype, "houseCall", void 0), R([E({ attribute: !1 })], J.prototype, "sign", void 0), R([E({ attribute: !1 })], J.prototype, "reload", void 0), R([E({ attribute: !1 })], J.prototype, "saveHouse", void 0), R([D()], J.prototype, "houseDraft", void 0), R([E({ attribute: !1 })], J.prototype, "appliances", void 0), R([E({ attribute: !1 })], J.prototype, "saveAppliances", void 0), R([E({ attribute: !1 })], J.prototype, "setVacation", void 0), R([D()], J.prototype, "vacUntil", void 0), R([D()], J.prototype, "domainErrors", void 0), R([D()], J.prototype, "pickFor", void 0), R([D()], J.prototype, "pickQuery", void 0), R([D()], J.prototype, "pickIndex", void 0), J = R([e("zephyr-settings")], J);
// src/diag.ts
var Sn = [
	"charged",
	"discharged",
	"solar"
];
function Cn(e) {
	let t = 0, n = 0;
	for (let r of Sn) t += e.estimated[r] ?? 0, n += e.kwh[r] ?? 0;
	return {
		kwh: t,
		share: n > 0 ? t / n : null
	};
}
function wn(e) {
	return e.sets.flatMap((e, t) => e.gaps.map((n) => ({
		...n,
		set: e.set ?? t + 1
	}))).sort((e, t) => t.end.localeCompare(e.end));
}
function Tn(e, t) {
	let n = e.find((e) => e.day === t) ?? null, r = e.filter((e) => e.day !== t), i = r.length ? r : e;
	return {
		today: n,
		mean: i.length ? i.reduce((e, t) => e + t.kwh, 0) / i.length : null
	};
}
function En(e, t, n) {
	let r = (e) => new Intl.NumberFormat(n, {
		minimumFractionDigits: 1,
		maximumFractionDigits: 1
	}).format(e / 1e3);
	switch (e.kind) {
		case "reason": return e.text?.[t] ?? F(t, "diag.event.reason_code", { code: e.code ?? "?" });
		case "mode": return F(t, "diag.event.mode", { mode: F(t, `mode.${e.mode ?? ""}`) });
		case "test": return F(t, "diag.event.test", { power: new Intl.NumberFormat(n).format(e.power ?? 0) });
		case "excluded_on": return F(t, "diag.event.excluded_on", { kw: r(e.power ?? 0) });
		case "flash": return F(t, "diag.event.flash", {
			set: e.set ?? "?",
			cause: F(t, `diag.cause.${e.cause ?? ""}`)
		});
		default: return F(t, `diag.event.${e.kind}`);
	}
}
function Dn(e) {
	return e.kind === "mode" ? "mode" : e.kind === "live" || e.kind === "shadow" || e.kind === "test" || e.kind === "test_end" ? "live" : e.kind === "excluded_on" || e.kind === "excluded_off" ? "airco" : e.kind === "flash" ? "write" : e.kind === "second_controller" ? "warning" : "control";
}
var On = [
	[/^no P1 sensor chosen$/, "no_p1"],
	[/^P1 is not reporting$/, "p1_silent"],
	[/^no sets$/, "no_sets"],
	[/^set (\d+) is offline$/, "offline"],
	[/^set (\d+) reports a different serial number$/, "serial"],
	[/^set (\d+) reports an error$/, "fault"],
	[/^a write test is running$/, "test"]
];
function kn(e, t) {
	for (let [n, r] of On) {
		let i = n.exec(e);
		if (i) return F(t, `control.blocker.${r}`, { set: i[1] ?? "" });
	}
	return e;
}
function An(e) {
	let t = e.house.reduce((e, t) => e + t, 0), n = e.airco.reduce((e, t) => e + t, 0), r = Math.max(0, ...e.house.map((t, n) => t + (e.airco[n] ?? 0)));
	return {
		total: t,
		aircoTotal: n,
		top: Math.max(.5, Math.ceil(r * 2) / 2),
		learned: e.counts.filter((t) => t >= e.min_count).length
	};
}
function jn(e) {
	return Math.abs(e.expected) < .05 ? null : (e.actual - e.expected) / Math.abs(e.expected);
}
function Mn(e, t) {
	return e.planned.filter((e) => e.appliance === t).sort((e, t) => (e.best_start ?? "9999").localeCompare(t.best_start ?? "9999") || e.index - t.index);
}
function Nn(e, t) {
	return t >= (e === "washer" ? 2 : 1) ? "clear" : "plan";
}
var Pn = (e) => {
	let [t, n] = e.split(":").map(Number);
	return t * 60 + n;
};
function Fn(e, t, n, r) {
	let i = Je("en-GB", {
		timeZone: r,
		hour: "2-digit",
		minute: "2-digit",
		hourCycle: "h23"
	}), a = Math.max(1, t.minutes), o = t.profile_w && t.profile_w.length ? t.profile_w.map((e) => e / 6e4) : Array(a).fill(t.kwh / a), s = o.length, c = /* @__PURE__ */ new Map();
	for (let t of e) t.buy !== null && c.set(new Date(t.start).getTime(), t.buy);
	let l = t.window.from ? Pn(t.window.from) : null, u = Pn(t.window.until), d = (e) => l === null ? !0 : l <= u ? e >= l && e <= u : e >= l || e <= u, f = null;
	for (let t of e) {
		let e = new Date(t.start).getTime();
		if (e + 9e5 <= n || t.buy === null || l === null && e - n > 864e5) continue;
		let r = Pn(i.format(new Date(e)));
		if (!d(r) || !d((r + s) % 1440)) continue;
		let a = 0, u = !0;
		for (let t = 0; t < s; t++) {
			let n = e + t * 6e4, r = c.get(n - n % 9e5);
			if (r === void 0) {
				u = !1;
				break;
			}
			a += o[t] * r;
		}
		u && (f === null || a < f) && (f = a);
	}
	return f;
}
var Y = class extends T {
	constructor(...e) {
		super(...e), this.quarters = [], this.uiLang = "en", this.locale = "en", this.timeZone = "UTC", this.clockMs = Date.now(), this.busy = null;
	}
	tr(e, t = {}) {
		return F(this.uiLang, e, t);
	}
	when(e) {
		let t = P(e, this.clockMs, this.timeZone);
		return `${this.tr(t ? "appl.today" : "appl.tomorrow")} ${M(e, this.locale, this.timeZone)}`;
	}
	async tap(e, t) {
		if (!this.busy) {
			this.busy = e.id;
			try {
				Nn(e.kind, t) === "clear" ? await this.clear?.(e.id) : await this.plan?.(e.id, {});
			} finally {
				this.busy = null;
			}
		}
	}
	render() {
		let e = this.view;
		return !e || !e.appliances.length ? C : b`<div
      class="row"
      role="group"
      aria-label=${this.tr("appl.title")}
    >
      ${e.appliances.map((t) => this.button(t, Mn(e, t.id)))}
    </div>`;
	}
	button(e, t) {
		let n = t.length > 0, r = t.map((e) => e.fixed_start ?? e.best_start).filter((e) => !!e), i = t.reduce((e, t) => e + (t.cost ?? 0), 0), a = t.reduce((e, t) => e + (t.saving ?? 0), 0), o = t.find((e) => e.after)?.after ?? null, s, c = null;
		if (!n) {
			let t = Fn(this.quarters, e, this.clockMs, this.timeZone);
			s = t === null ? this.tr("appl.tap") : this.tr("appl.per_run", { euro: O(t, this.locale) });
		} else if (!r.length) s = this.tr("appl.calculating");
		else {
			let e = r.map((e, t) => t === 0 ? this.when(e) : M(e, this.locale, this.timeZone));
			s = `${this.tr("appl.start")} ${e.join(` ${this.tr("appl.and")} `)} · ${O(i, this.locale)}`, c = o ? this.tr("appl.after_wash") : a >= .01 ? this.tr("appl.cheaper", { euro: O(a, this.locale) }) : null;
		}
		let l = n ? `${e.name} ${t.length}×` : e.name, u = Nn(e.kind, t.length) === "clear" ? "appl.tap_clear" : n ? "appl.tap_more" : "appl.tap_plan";
		return b`<button
      type="button"
      class=${`b${n ? " on" : ""}`}
      aria-pressed=${n ? "true" : "false"}
      ?disabled=${this.busy === e.id}
      title=${this.tr(u)}
      @click=${() => void this.tap(e, t.length)}
    >
      <b
        >${l}${e.running ? b`<span class="dot" title=${this.tr("appl.running")}></span>` : C}</b
      >
      <span>${s}</span>
      ${c ? b`<em class=${o ? "muted" : ""}>${c}</em>` : C}
    </button>`;
	}
	static {
		this.styles = s`
    :host {
      display: block;
    }
    .row {
      display: flex;
      flex-wrap: wrap;
      gap: 10px;
      margin-top: 14px;
    }
    .b {
      display: flex;
      flex-direction: column;
      align-items: flex-start;
      gap: 1px;
      min-width: 150px;
      padding: 9px 16px;
      border-radius: 14px;
      border: 1px solid var(--z-border);
      background: var(--z-card);
      color: var(--z-text);
      font: inherit;
      text-align: left;
      cursor: pointer;
    }
    .b:disabled {
      opacity: 0.6;
      cursor: progress;
    }
    .b b {
      font-size: 15px;
      display: flex;
      align-items: center;
      gap: 6px;
    }
    .b span {
      font-size: 12.5px;
      color: var(--z-muted);
    }
    .b em {
      font-style: normal;
      font-size: 12px;
      font-weight: 600;
      color: var(--z-good-text);
    }
    .b em.muted {
      color: var(--z-muted);
    }
    .b.on {
      background: color-mix(in srgb, var(--z-charge) 10%, var(--z-card));
      border-color: color-mix(in srgb, var(--z-charge) 50%, var(--z-card));
    }
    .b.on b {
      color: var(--z-charge);
    }
    .b.on span {
      color: var(--z-text);
    }
    .dot {
      width: 8px;
      height: 8px;
      border-radius: 50%;
      background: var(--z-charge);
      display: inline-block;
      animation: pulse 1.6s ease-in-out infinite;
    }
    @keyframes pulse {
      50% {
        opacity: 0.3;
      }
    }
    @media (max-width: 600px) {
      .b {
        min-width: 0;
        flex: 1 1 100%;
      }
    }
  `;
	}
};
R([E({ attribute: !1 })], Y.prototype, "view", void 0), R([E({ attribute: !1 })], Y.prototype, "quarters", void 0), R([E({ attribute: !1 })], Y.prototype, "uiLang", void 0), R([E()], Y.prototype, "locale", void 0), R([E()], Y.prototype, "timeZone", void 0), R([E({ type: Number })], Y.prototype, "clockMs", void 0), R([E({ attribute: !1 })], Y.prototype, "plan", void 0), R([E({ attribute: !1 })], Y.prototype, "clear", void 0), R([D()], Y.prototype, "busy", void 0), Y = R([e("zephyr-appliances")], Y);
function In(e) {
	return e.startsWith("dryer") ? "dryer" : ["washer", "dishwasher"].includes(e) ? e : "other";
}
// src/diagnostics.ts
var Ln = 5, X = class extends T {
	constructor(...e) {
		super(...e), this.uiLang = "en", this.locale = "en", this.timeZone = "UTC", this.peakInfo = !1, this.allGapsOpen = !1, this.admin = !1, this.busy = null, this.note = null, this.dayKind = "workday", this.metric = "load";
	}
	tr(e, t = {}) {
		return F(this.uiLang, e, t);
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
		let e = this.view, t = this.planCheck || e?.profile || this.appliances;
		return b`<div class="layout">
      <section class="card tools">
        <div class="intro">
          <h2>${this.tr("diag.title")}</h2>
          <p class="muted">${this.tr("diag.intro")}</p>
        </div>
        <div class="buttons">
          <button
            type="button"
            class="primary"
            ?disabled=${!e || this.busy !== null}
            @click=${() => void this.run("download")}
          >
            ${this.tr(this.busy === "download" ? "diag.busy" : "diag.download")}
          </button>
          ${this.admin ? b`<button
                  type="button"
                  class="ghost"
                  ?disabled=${this.busy !== null}
                  @click=${() => void this.run("export")}
                >
                  ${this.tr(this.busy === "export" ? "diag.busy" : "diag.export")}
                </button>` : C}
        </div>
        ${this.note ? b`<p class=${this.note.error ? "note error" : "note"} role="status">${this.note.text}</p>` : C}
      </section>
      ${t ? b`<h2 class="sec">${this.tr("diag.sec_planner")}</h2>
              ${this.planCheck || e?.profile ? b`<div class="g2">
                      ${this.planCheck ? this.renderCheck(this.planCheck) : C}
                      ${e?.profile ? this.renderProfile(e.profile) : C}
                    </div>` : C}
              ${this.appliances ? this.renderAppliances(this.appliances) : C}` : C}
      <h2 class="sec">${this.tr("diag.sec_measure")}</h2>
      <div class="g2">
        ${e?.energy ? this.renderEnergy(e.energy) : C}
        <div class="col">
          ${e?.peaks ? this.renderPeaks(e.peaks) : C}
          <section class="card" aria-labelledby="wr-title">
            ${e ? this.renderCounters(e) : b`<div class="skeleton"></div>`}
          </section>
        </div>
      </div>
      <h2 class="sec">${this.tr("diag.sec_log")}</h2>
      <section class="card events" aria-labelledby="events-title">
        <div class="head">
          <h2 id="events-title">${this.tr("diag.events")}</h2>
          <button
            type="button"
            class="ghost small"
            @click=${() => this.refresh?.()}
          >
            ${this.tr("diag.refresh")}
          </button>
        </div>
        ${e ? this.renderEvents(e) : b`<div class="skeleton"></div>`}
      </section>
    </div>`;
	}
	renderCounters(e) {
		if (!e.sets.length) return b`<h2 id="wr-title">${this.tr("diag.counters")}</h2>
        <p class="muted">${this.tr("diag.no_sets")}</p>`;
		let t = (e) => e === null ? "–" : new Intl.NumberFormat(this.locale).format(e);
		return b`<h2 id="wr-title">
        ${this.tr(e.shadow ? "diag.counters_shadow" : "diag.counters")}
      </h2>
      ${e.shadow ? b`<p class="note">${this.tr("diag.shadow_counts")}</p>` : C}
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
          ${e.sets.map((e) => b`<tr>
                  <th scope="row">${e.number}</th>
                  <td>${t(e.ram_24h)}</td>
                  <td>${t(e.flash_24h)}</td>
                  <td>${t(e.relay_24h)}</td>
                  <td class=${e.failed_24h ? "bad" : ""}>${t(e.failed_24h)}</td>
                </tr>
                ${e.last_error ? b`<tr>
                        <td colspan="5" class="lasterror">
                          ${this.tr("diag.last_error", { error: e.last_error })}
                        </td>
                      </tr>` : C}`)}
        </tbody>
      </table>
      <p class="muted small">${this.tr("diag.counters_note")}</p>`;
	}
	renderPeaks(e) {
		let t = new Intl.DateTimeFormat("en-CA", { timeZone: this.timeZone }).format(/* @__PURE__ */ new Date()), n = Tn(e, t), r = Math.max(.05, ...e.map((e) => e.kwh)), i = (e) => A(e, this.locale, 2);
		return b`<section class="card" aria-labelledby="pk-title">
      <div class="head">
        <h2 id="pk-title">${this.tr("diag.peaks_title")}</h2>
        <button
          type="button"
          class="ghost small info"
          aria-expanded=${this.peakInfo ? "true" : "false"}
          @click=${() => this.peakInfo = !this.peakInfo}
        >
          i
        </button>
      </div>
      ${this.peakInfo ? b`<p class="note">${this.tr("diag.peaks_info")}</p>` : C}
      <p>
        ${this.tr("diag.peaks_line", {
			today: i(n.today?.kwh ?? 0),
			n: n.today?.holds ?? 0,
			mean: n.mean === null ? "–" : i(n.mean)
		})}
      </p>
      ${e.length ? b`<div
              class="pbars"
              role="img"
              aria-label=${this.tr("diag.peaks_bars")}
            >
              ${e.map((e) => b`<div
                    class="pb"
                    title=${`${e.day}: ${i(e.kwh)} (${e.holds}×)`}
                  >
                    <i
                      class=${e.day === t ? "today" : ""}
                      style="height:${Math.max(2, e.kwh / r * 100)}%"
                    ></i>
                    <span
                      >${new Intl.DateTimeFormat(this.locale, {
			day: "numeric",
			timeZone: "UTC"
		}).format(/* @__PURE__ */ new Date(`${e.day}T12:00:00Z`))}</span
                    >
                  </div>`)}
            </div>` : C}
      <p class="muted small">${this.tr("diag.peaks_note")}</p>
    </section>`;
	}
	renderAppliances(e) {
		return b`<section class="card" aria-labelledby="ap-title">
      <h2 id="ap-title">${this.tr("diag.appl_title")}</h2>
      ${e.appliances.length ? b`<ul class="appl">
              ${e.appliances.map((e) => this.applianceRow(e))}
            </ul>` : b`<p class="muted">${this.tr("diag.appl_empty")}</p>`}
    </section>`;
	}
	applianceRow(e) {
		let t = Math.floor(e.minutes / 60), n = e.minutes % 60, r = t ? `${t} ${this.uiLang === "nl" ? "u" : "h"}${n ? ` ${n} min` : ""}` : `${n} min`, i = [
			e.profile === "learned" ? this.tr("diag.appl_learned", { n: e.runs_seen }) : this.tr("diag.appl_default"),
			this.tr("diag.appl_per_run", {
				kwh: A(e.kwh, this.locale, 2),
				time: r
			}),
			this.tr(e.plug ? "diag.appl_plug" : "diag.appl_noplug")
		];
		return b`<li>
      <div class="ahead">
        <b>${e.name}</b>
        <span class="muted small"
          >${this.tr(`diag.kind_${In(e.kind)}`)}</span
        >
        ${e.running ? b`<span class="chip on">${this.tr("diag.appl_running")}</span>` : C}
      </div>
      <p class="muted small">${i.join(" · ")}</p>
      ${e.profile_w && e.profile_w.length ? this.profileChart(e.profile_w) : C}
    </li>`;
	}
	profileChart(e) {
		let t = Math.max(100, ...e), n = e.length, r = e.map((e, r) => `${(r / Math.max(1, n - 1) * 300).toFixed(1)},${(60 - e / t * 56).toFixed(1)}`).join(" ");
		return b`<svg
        class="aprof"
        viewBox="0 0 300 64"
        preserveAspectRatio="none"
        role="img"
        aria-label=${this.tr("diag.appl_chart", { max: Math.round(t) })}
      >
        <polygon points=${`0,60 ${r} 300,60`} class="area"></polygon>
        <polyline points=${r} class="line"></polyline>
      </svg>
      <div class="aaxis muted small">
        <span>0</span
        ><span>${this.tr("diag.appl_max", { w: Math.round(t) })}</span
        ><span>${Math.round(n)} min</span>
      </div>`;
	}
	renderEnergy(e) {
		let t = (e) => e === void 0 ? "–" : new Intl.NumberFormat(this.locale, {
			minimumFractionDigits: 2,
			maximumFractionDigits: 2
		}).format(e), n = (e) => new Date(e).toLocaleString(this.locale, {
			day: "numeric",
			month: "short",
			hour: "2-digit",
			minute: "2-digit",
			timeZone: this.timeZone
		}), r = (e) => e < 120 ? `${Math.round(e)} s` : e < 7200 ? `${Math.round(e / 60)} min` : `${(e / 3600).toLocaleString(this.locale, { maximumFractionDigits: 1 })} h`, i = wn(e), a = this.allGapsOpen ? i : i.slice(0, Ln), o = e.sets.length > 1;
		return b`<section class="card" aria-labelledby="en-title">
      <div>
        <h2 id="en-title">${this.tr("diag.energy_title")}</h2>
        <p class="muted">${this.tr("diag.energy_sub")}</p>
      </div>
      <table>
        <thead>
          <tr>
            <th scope="col">${this.tr("diag.set")}</th>
            ${Sn.map((e) => b`<th scope="col">${this.tr(`diag.energy_${e}`)}</th>`)}
            <th scope="col">${this.tr("diag.energy_estimated")}</th>
            <th scope="col">${this.tr("diag.energy_failed")}</th>
          </tr>
        </thead>
        <tbody>
          ${e.sets.map((e, r) => {
			let i = Cn(e);
			return b`<tr>
                <th scope="row">${e.set ?? r + 1}</th>
                ${Sn.map((n) => b`<td>${t(e.kwh[n])}</td>`)}
                <td>
                  ${t(i.kwh)}${i.share !== null && i.kwh > 0 ? b` <span class="muted">(${j(i.share * 100, this.locale)})</span>` : C}
                </td>
                <td class=${e.failed_reads ? "bad" : ""}>${e.failed_reads}</td>
              </tr>
              ${e.open_gap ? b`<tr>
                      <td colspan="6" class="lasterror">
                        ${this.tr(e.open_gap.restart ? "diag.energy_open_restart" : "diag.energy_open", { since: n(e.open_gap.start) })}
                      </td>
                    </tr>` : C}`;
		})}
          ${o ? b`<tr class="total">
                  <th scope="row">${this.tr("diag.energy_total")}</th>
                  ${Sn.map((n) => b`<td>${t(e.totals[n])}</td>`)}
                  <td></td>
                  <td></td>
                </tr>` : C}
        </tbody>
      </table>
      <h3>${this.tr("diag.energy_gaps")}</h3>
      ${a.length ? b`<ul class="gaps">
                ${a.map((e) => b`<li>
                      <span class="when"
                        >${n(e.start)} ·
                        ${r(e.seconds)}${o ? b` · ${this.tr("diag.set")} ${e.set}` : C}</span
                      >
                      <span
                        >${this.tr(`diag.energy_m_${[
			"none",
			"interpolate",
			"soc"
		].includes(e.method) ? e.method : "none"}`)}${e.restart ? ` · ${this.tr("diag.energy_restart")}` : ""}</span
                      >
                      <span class="muted"
                        >${Object.entries(e.kwh).filter(([e]) => Sn.includes(e)).map(([e, n]) => `${this.tr(`diag.energy_${e}`).toLowerCase()} ${t(n)} kWh`).join(" · ") || this.tr("diag.energy_nothing")}</span
                      >
                    </li>`)}
              </ul>
              ${i.length > Ln ? b`<button
                      type="button"
                      class="linkish"
                      aria-expanded=${this.allGapsOpen ? "true" : "false"}
                      @click=${() => this.allGapsOpen = !this.allGapsOpen}
                    >
                      ${this.allGapsOpen ? this.tr("diag.energy_gaps_less") : this.tr("diag.energy_gaps_all", { n: i.length })}
                    </button>` : C}` : b`<p class="muted">${this.tr("diag.energy_no_gaps")}</p>`}
      <p class="muted small">${this.tr("diag.energy_note")}</p>
    </section>`;
	}
	renderCheck(e) {
		let t = [
			"load",
			"solar",
			"import",
			"export",
			"cost"
		], n = (e, t, n = !1) => {
			let r = n && t > 0 ? "+" : t < 0 ? "−" : "", i = Math.abs(t);
			return e === "cost" ? `${r}€ ${new Intl.NumberFormat(this.locale, {
				minimumFractionDigits: 2,
				maximumFractionDigits: 2
			}).format(i)}` : `${r}${new Intl.NumberFormat(this.locale, {
				minimumFractionDigits: 1,
				maximumFractionDigits: 1
			}).format(i)} kWh`;
		}, r = e.days.filter((e) => e[this.metric]), i = Math.max(.1, ...r.flatMap((e) => [e[this.metric]?.expected ?? 0, e[this.metric]?.actual ?? 0].map(Math.abs))), a = (e) => new Intl.DateTimeFormat(this.locale, {
			weekday: "short",
			day: "numeric",
			timeZone: "UTC"
		}).format(/* @__PURE__ */ new Date(`${e}T12:00:00Z`));
		return b`<section class="card check" aria-labelledby="pc-title">
      <h2 id="pc-title">${this.tr("diag.check_title")}</h2>
      <p class="muted">
        ${this.tr("diag.check_intro", { n: e.summary.days })}
      </p>
      ${e.summary.days === 0 ? b`<p class="note">${this.tr("diag.check_none")}</p>` : b`<table class="ctable">
                <thead>
                  <tr>
                    <th scope="col"></th>
                    <th scope="col">${this.tr("diag.check_expected")}</th>
                    <th scope="col">${this.tr("diag.check_actual")}</th>
                    <th scope="col">${this.tr("diag.check_diff")}</th>
                    <th scope="col">${this.tr("diag.check_daily")}</th>
                  </tr>
                </thead>
                <tbody>
                  ${t.map((t) => {
			let r = e.summary[t];
			if (!r) return C;
			let i = jn(r);
			return b`<tr
                      class=${t === this.metric ? "on" : ""}
                      @click=${() => this.metric = t}
                    >
                      <th scope="row">
                        <button
                          type="button"
                          class="linkish"
                          aria-pressed=${t === this.metric ? "true" : "false"}
                        >
                          ${this.tr(`diag.m_${t}`)}
                        </button>
                      </th>
                      <td>${n(t, r.expected)}</td>
                      <td>${n(t, r.actual)}</td>
                      <td
                        class=${i !== null && Math.abs(i) > .15 ? "warnc" : ""}
                      >
                        ${n(t, r.diff, !0)}${i === null ? C : b` <small>(${i > 0 ? "+" : "−"}${Math.round(Math.abs(i) * 100)} %)</small>`}
                      </td>
                      <td>
                        ${r.mean_abs_day === void 0 ? "–" : n(t, r.mean_abs_day)}
                      </td>
                    </tr>`;
		})}
                </tbody>
              </table>
              <h3>
                ${this.tr("diag.check_per_day", { metric: this.tr(`diag.m_${this.metric}`).toLowerCase() })}
              </h3>
              <div
                class="cbars"
                role="img"
                aria-label=${this.tr("diag.check_per_day", { metric: this.tr(`diag.m_${this.metric}`) })}
              >
                ${r.map((e) => {
			let t = e[this.metric], r = e.quarters < e.of - 4;
			return b`<div
                    class="cday"
                    title=${`${a(e.date)}: ${this.tr("diag.check_expected").toLowerCase()} ${n(this.metric, t.expected)}, ${this.tr("diag.check_actual").toLowerCase()} ${n(this.metric, t.actual)}${r ? ` (${this.tr("diag.check_partial", {
				n: e.quarters,
				of: e.of
			})})` : ""}`}
                  >
                    <div class="cpair">
                      <i
                        class="exp"
                        style=${`height:${Math.abs(t.expected) / i * 100}%`}
                      ></i>
                      <i
                        class=${r ? "act part" : "act"}
                        style=${`height:${Math.abs(t.actual) / i * 100}%`}
                      ></i>
                    </div>
                    <span>${a(e.date)}</span>
                  </div>`;
		})}
              </div>
              <div class="plegend">
                <span
                  ><i class="sw exp"></i>${this.tr("diag.check_expected")}</span
                >
                <span
                  ><i class="sw act"></i>${this.tr("diag.check_actual")}</span
                >
              </div>`}
    </section>`;
	}
	renderProfile(e) {
		let t = e[this.dayKind], n = An(t), r = (e, t = 1) => new Intl.NumberFormat(this.locale, {
			minimumFractionDigits: t,
			maximumFractionDigits: t
		}).format(e), i = t.airco.some((e) => e > 0) || e.workday.airco.some((e) => e > 0);
		return b`<section class="card profile" aria-labelledby="profile-title">
      <div class="head">
        <h2 id="profile-title">${this.tr("diag.profile")}</h2>
        <div class="tabs" role="group">
          ${["workday", "weekend"].map((e) => b`<button
                type="button"
                class=${this.dayKind === e ? "on" : ""}
                aria-pressed=${this.dayKind === e ? "true" : "false"}
                @click=${() => this.dayKind = e}
              >
                ${this.tr(`diag.${e}`)}
              </button>`)}
        </div>
      </div>
      <p class="muted">
        ${this.tr("diag.profile_source", {
			source: e.source,
			hours: e.hours
		})}
      </p>
      ${n.learned === 0 ? b`<p class="note">
              ${this.tr(`diag.profile_empty_${this.dayKind}`, { mean: r(e.mean, 2) })}
            </p>` : b`<p class="sum">
                ${this.tr("diag.profile_total", { kwh: r(n.total) })}${i ? b` · ${this.tr("diag.profile_airco", { kwh: r(n.aircoTotal) })}` : C}
              </p>
              <div
                class="pchart"
                role="img"
                aria-label=${this.tr("diag.profile_total", { kwh: r(n.total) })}
              >
                <div class="paxis">
                  <span>${r(n.top)}</span><span>0</span>
                </div>
                <div class="pbars">
                  ${t.house.map((e, i) => {
			let a = t.airco[i] ?? 0;
			return b`<div
                      class=${t.counts[i] >= t.min_count ? "pcol" : "pcol none"}
                      title=${this.tr("diag.profile_hour", {
				hour: i,
				house: r(e, 2),
				airco: r(a, 2),
				n: t.counts[i]
			})}
                    >
                      ${a > 0 ? b`<i class="air" style="height:${a / n.top * 100}%"></i>` : C}
                      <i
                        class="house"
                        style="height:${e / n.top * 100}%"
                      ></i>
                    </div>`;
		})}
                </div>
                <div class="pticks">
                  ${[
			0,
			6,
			12,
			18,
			23
		].map((e) => b`<span style="left:${(e + .5) / 24 * 100}%">${String(e).padStart(2, "0")}</span>`)}
                </div>
              </div>
              <div class="plegend">
                <span
                  ><i class="sw house"></i
                  >${this.tr("diag.profile_house")}</span
                >
                ${i ? b`<span><i class="sw air"></i>${this.tr("diag.profile_airco_legend")}</span>` : C}
                <span
                  ><i class="sw house faint"></i
                  >${this.tr("diag.profile_learned", {
			n: n.learned,
			mean: r(e.mean, 2)
		})}</span
                >
              </div>`}
    </section>`;
	}
	renderEvents(e) {
		if (!e.events.length) return b`<p class="muted">${this.tr("diag.no_events")}</p>`;
		let t = (/* @__PURE__ */ new Date()).toISOString();
		return b`<ol>
      ${e.events.map((e) => {
			let n = Dn(e), r = P(e.time, t, this.timeZone) ? M(e.time, this.locale, this.timeZone) : `${N(e.time, this.locale, this.timeZone)} ${M(e.time, this.locale, this.timeZone)}`;
			return b`<li>
          <time datetime=${e.time}>${r}</time>
          <span class="kind k-${n}">${this.tr(`diag.kind.${n}`)}</span>
          <span class="text">${En(e, this.uiLang, this.locale)}</span>
        </li>`;
		})}
    </ol>`;
	}
	static {
		this.styles = s`
    :host {
      display: block;
      color: var(--z-text);
      font-family: var(--z-font);
    }
    .layout {
      display: flex;
      flex-direction: column;
      gap: 16px;
    }
    .g2 {
      display: grid;
      grid-template-columns: minmax(0, 1fr) minmax(0, 1fr);
      gap: 16px;
      align-items: stretch;
    }
    .col {
      display: flex;
      flex-direction: column;
      gap: 16px;
      min-width: 0;
    }
    h2.sec {
      margin: 10px 0 -6px;
      font-family: var(--z-font);
      font-size: 12px;
      font-weight: 600;
      letter-spacing: 0.08em;
      text-transform: uppercase;
      color: var(--z-muted);
    }
    .linkish {
      align-self: flex-start;
      background: none;
      border: 0;
      padding: 6px 0;
      min-height: 0;
      color: var(--z-text);
      font: inherit;
      font-size: 13px;
      font-weight: 600;
      text-decoration: underline;
      cursor: pointer;
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
      display: flex;
      flex-wrap: wrap;
      align-items: center;
      gap: 12px 24px;
    }
    .tools .intro {
      flex: 1 1 360px;
    }
    .tools .note {
      flex-basis: 100%;
    }
    .check {
      display: flex;
      flex-direction: column;
      gap: 10px;
    }
    .ctable td,
    .ctable th {
      padding: 8px 6px;
    }
    .ctable tbody tr {
      cursor: pointer;
    }
    .ctable tr.on {
      background: var(--z-info-bg);
    }
    .ctable small {
      color: var(--z-muted);
      font-weight: 400;
    }
    .warnc {
      color: var(--z-warn-text);
      font-weight: 700;
    }
    .linkish {
      min-height: 0;
      padding: 0;
      border: 0;
      background: none;
      color: inherit;
      font: inherit;
      font-weight: 600;
      cursor: pointer;
    }
    .cbars {
      display: flex;
      gap: 6px;
      height: 130px;
      align-items: stretch;
    }
    .cday {
      flex: 1 1 0;
      display: flex;
      flex-direction: column;
      gap: 4px;
      min-width: 0;
    }
    .cday span {
      font-size: 10px;
      color: var(--z-muted);
      text-align: center;
      white-space: nowrap;
      overflow: hidden;
    }
    .cpair {
      flex: 1;
      display: flex;
      align-items: flex-end;
      gap: 2px;
      border-bottom: 1px solid var(--z-border);
    }
    .cpair i {
      flex: 1;
      border-radius: 2px 2px 0 0;
    }
    i.exp,
    .sw.exp {
      background: transparent;
      border: 2px dashed var(--z-muted);
      border-bottom: 0;
      box-sizing: border-box;
    }
    i.act,
    .sw.act {
      background: var(--z-charge);
    }
    i.act.part {
      opacity: 0.45;
    }
    .profile {
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
      background: repeating-linear-gradient(
        45deg,
        var(--z-deliver) 0 2px,
        transparent 2px 5px
      );
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
      background: repeating-linear-gradient(
        45deg,
        var(--z-deliver) 0 2px,
        transparent 2px 4px
      );
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
    .pbars {
      display: flex;
      align-items: flex-end;
      gap: 4px;
      height: 80px;
      margin: 6px 0;
    }
    .pb {
      flex: 1 1 0;
      height: 100%;
      display: flex;
      flex-direction: column;
      justify-content: flex-end;
      align-items: center;
      gap: 2px;
    }
    .pb i {
      width: 100%;
      max-width: 22px;
      border-radius: 3px 3px 0 0;
      background: var(--z-bar);
    }
    .pb i.today {
      background: var(--z-deliver);
    }
    .pb span {
      font-size: 10px;
      color: var(--z-muted);
    }
    button.info {
      width: 28px;
      min-width: 28px;
      padding: 0;
      border-radius: 50%;
      font-style: italic;
      font-weight: 700;
    }
    ul.appl {
      list-style: none;
      margin: 0;
      padding: 0;
    }
    ul.appl li {
      display: block;
      padding: 12px 0;
      border-top: 1px solid var(--z-border);
    }
    ul.appl li:first-child {
      border-top: 0;
    }
    .ahead {
      display: flex;
      gap: 10px;
      align-items: baseline;
      flex-wrap: wrap;
    }
    ul.appl p {
      margin: 2px 0 6px;
    }
    .chip.on {
      font-size: 11.5px;
      font-weight: 600;
      color: var(--z-charge);
      background: color-mix(in srgb, var(--z-charge) 12%, transparent);
      border-radius: 99px;
      padding: 1px 8px;
    }
    .aprof {
      width: 100%;
      max-width: 420px;
      height: 64px;
      display: block;
    }
    .aprof .area {
      fill: color-mix(in srgb, var(--z-charge) 18%, transparent);
    }
    .aprof .line {
      fill: none;
      stroke: var(--z-charge);
      stroke-width: 1.5;
      vector-effect: non-scaling-stroke;
    }
    .aaxis {
      display: flex;
      justify-content: space-between;
      max-width: 420px;
    }
    .gaps {
      list-style: none;
      margin: 0;
      padding: 0;
      display: flex;
      flex-direction: column;
      gap: 8px;
      font-size: 13px;
    }
    .gaps li {
      display: flex;
      flex-wrap: wrap;
      gap: 2px 12px;
      border-bottom: 1px solid var(--z-border);
      padding-bottom: 6px;
    }
    .gaps .when {
      font-variant-numeric: tabular-nums;
      font-weight: 600;
    }
    tr.total th,
    tr.total td {
      border-top: 2px solid var(--z-border);
      font-weight: 600;
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
    @media (max-width: 900px) {
      .g2 {
        grid-template-columns: minmax(0, 1fr);
      }
    }
    @media (max-width: 700px) {
      .card {
        padding: 16px;
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
R([E({ attribute: !1 })], X.prototype, "view", void 0), R([E({ attribute: !1 })], X.prototype, "uiLang", void 0), R([E()], X.prototype, "locale", void 0), R([E()], X.prototype, "timeZone", void 0), R([E({ attribute: !1 })], X.prototype, "appliances", void 0), R([D()], X.prototype, "peakInfo", void 0), R([D()], X.prototype, "allGapsOpen", void 0), R([E({ type: Boolean })], X.prototype, "admin", void 0), R([E({ attribute: !1 })], X.prototype, "download", void 0), R([E({ attribute: !1 })], X.prototype, "exportCosts", void 0), R([E({ attribute: !1 })], X.prototype, "refresh", void 0), R([E({ attribute: !1 })], X.prototype, "planCheck", void 0), R([D()], X.prototype, "busy", void 0), R([D()], X.prototype, "note", void 0), R([D()], X.prototype, "dayKind", void 0), R([D()], X.prototype, "metric", void 0), X = R([e("zephyr-diagnostics")], X);
// src/savings.ts
var Rn, zn = (e) => e <= 0 ? 0 : Math.ceil(e * 2) / 2;
function Bn(e, t = !1) {
	let n = e.map((e) => (e.savings_battery ?? 0) + (t ? e.savings_solar ?? 0 : 0)), r = n.map(Math.abs).filter((e) => e > 0).sort((e, t) => e - t), i = r.length ? r[Math.floor(r.length * .75)] : .5, a = Math.max(.5, i * 2), o = Math.min(a, Math.max(0, ...n)), s = Math.max(-a, Math.min(0, ...n));
	return {
		top: Math.max(.5, zn(o)),
		bottom: -zn(-s)
	};
}
var Z = class extends T {
	static {
		Rn = this;
	}
	constructor(...e) {
		super(...e), this.uiLang = "en", this.locale = "en", this.timeZone = "UTC", this.admin = !1, this.period = "month", this.form = Rn.storedForm(), this.busy = !1, this.result = null, this.batteryOnly = !1;
	}
	tr(e, t = {}) {
		return F(this.uiLang, e, t);
	}
	render() {
		let e = this.view;
		if (!e) return b`<div class="skeleton"></div>`;
		let t = e.periods[this.period];
		return b`<div class="layout">
      <section class="card hero" aria-labelledby="sv-title">
        <div class="head">
          <h2 id="sv-title">
            ${this.tr(t.includes_solar ? "savings.title_solar" : "savings.title")}
          </h2>
          <div
            class="tabs"
            role="group"
            aria-label=${this.tr("savings.period")}
          >
            ${[
			"today",
			"week",
			"month",
			"year"
		].map((e) => b`<button
                  type="button"
                  class=${e === this.period ? "on" : ""}
                  aria-pressed=${e === this.period ? "true" : "false"}
                  @click=${() => this.period = e}
                >
                  <span class="long">${this.tr(`savings.p_${e}`)}</span
                  ><span class="short">${this.tr(`savings.ps_${e}`)}</span>
                </button>`)}
          </div>
        </div>
        ${this.renderHero(t)}
      </section>
      <section class="card split" aria-labelledby="sv-split">
        <h2 id="sv-split">
          ${this.tr("savings.split_title", { period: this.tr(`savings.p_${this.period}`).toLowerCase() })}
        </h2>
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
          ${e.periods[this.period].includes_solar ? b`<li>${this.tr("savings.note_solar")}</li>` : C}
          ${e.saldering_until ? b`<li>${this.tr("savings.note_saldering", { date: this.date(e.saldering_until) })}</li>` : C}
          ${e.backfilled_days && e.measured_since ? b`<li>
                  ${this.tr("savings.note_hourly", { date: this.date(e.measured_since) })}
                </li>` : C}
          ${e.since ? b`<li>${this.tr("savings.note_since", { date: this.date(e.since) })}</li>` : C}
        </ul>
      </section>
      ${this.admin && e.can_backfill ? this.renderBackfill(e) : C}
    </div>`;
	}
	choices(e, t = "sensor") {
		return cn(this.states, t, e);
	}
	picker(e, t, n, r, i) {
		let a = `bf-${e}`, o = r ? n.find((e) => e.id === r) ?? {
			id: r,
			name: r
		} : null;
		return b`<label class="field" for=${a}>
      <span
        >${t}${i ? b` <em>(${this.tr("savings.optional")})</em>` : C}</span
      >
      <input
        id=${a}
        type="text"
        list=${`${a}-list`}
        autocomplete="off"
        placeholder=${this.tr("savings.choose_entity")}
        .value=${o ? un(o) : ""}
        @change=${(t) => {
			let r = t.target.value;
			this.form = {
				...this.form,
				[e]: ln(r, n) ?? (r.trim() ? r.trim() : null)
			};
		}}
      />
      <datalist id=${`${a}-list`}>
        ${n.map((e) => b`<option value=${un(e)}></option>`)}
      </datalist>
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
				price_entity: t.price_entity,
				soc_entity: t.soc_entity
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
			price_entity: this.form.price_entity === void 0 ? e.defaults?.price_entity ?? null : this.form.price_entity,
			soc_entity: this.form.soc_entity ?? null
		}, r = !!(n.first && n.charge_entity && n.discharge_entity), i = this.result;
		return b`<section class="card backfill" aria-labelledby="sv-bf">
      <h2 id="sv-bf">${this.tr("savings.bf_title")}</h2>
      <p class="muted">
        ${this.tr("savings.bf_intro", { date: e.measured_since ? this.date(e.measured_since) : "–" })}
      </p>
      <div class="form">
        <label class="field" for="bf-first">
          <span>${this.tr("savings.bf_first")}</span>
          <input
            id="bf-first"
            type="date"
            .value=${n.first}
            max=${e.measured_since ?? ""}
            @change=${(e) => this.form = {
			...this.form,
			first: e.target.value
		}}
          />
        </label>
        ${this.picker("charge_entity", this.tr("savings.bf_charge"), t, n.charge_entity, !1)}
        ${this.picker("discharge_entity", this.tr("savings.bf_discharge"), t, n.discharge_entity, !1)}
        ${this.picker("solar_entity", this.tr("savings.bf_solar"), t, n.solar_entity, !0)}
        ${this.picker("soc_entity", this.tr("savings.bf_soc"), this.choices("battery"), n.soc_entity, !0)}
        <fieldset class="field price">
          <legend>${this.tr("savings.bf_price")}</legend>
          <label class="radio">
            <input
              type="radio"
              name="bf-price"
              .checked=${n.price_entity === "energyzero"}
              @change=${() => this.form = {
			...this.form,
			price_entity: "energyzero"
		}}
            />
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
          ${n.price_entity === "energyzero" ? C : this.picker("price_entity", this.tr("savings.bf_price_pick"), this.choices(null), n.price_entity, !1)}
        </fieldset>
      </div>
      <p class="muted small">${this.tr("savings.bf_help")}</p>
      <div class="buttons">
        <button
          type="button"
          class="primary"
          ?disabled=${!r || this.busy}
          @click=${() => void this.run(n)}
        >
          ${this.tr(this.busy ? "savings.bf_busy" : "savings.bf_run")}
        </button>
        ${e.backfilled_days ? b`<button
                type="button"
                class="ghost"
                ?disabled=${this.busy}
                @click=${() => void this.run(null)}
              >
                ${this.tr("savings.bf_clear", { n: e.backfilled_days })}
              </button>` : C}
      </div>
      ${i ? b`<p class=${i.ok ? "result" : "result bad"} role="status">
              ${i.ok ? i.removed === void 0 ? i.days ? this.tr("savings.bf_done", {
			n: i.days,
			first: this.date(i.first),
			last: this.date(i.last),
			skipped: i.skipped ?? 0,
			unpriced: (i.hours ?? 0) - (i.priced_hours ?? 0)
		}) + (i.price_failed_days ? ` ${this.tr("savings.bf_ez_failed", { n: i.price_failed_days })}` : "") + (i.warnings?.includes("pv_in_battery_counters") ? ` ${this.tr("savings.bf_warn_pv")}` : "") : this.tr("savings.bf_nothing") : this.tr("savings.bf_removed", { n: i.removed }) : this.tr(`savings.bf_err_${i.error}`, { entities: (i.entities ?? []).join(", ") })}
            </p>` : C}
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
		if (e.cost === null || e.cost_no_battery === null || e.savings_battery === null) return b`<p class="muted">${this.tr("savings.no_data")}</p>`;
		let t = e.includes_solar && e.savings_total != null && e.cost_no_solar != null, n = t ? e.savings_total : e.savings_battery, r = n < 0, i = Math.max(e.cost, e.cost_no_battery, t ? e.cost_no_solar : 0, .01);
		return b`<div class="big ${r ? "loss" : "win"}">
        <span class="amount"
          >${r ? "−" : ""}${O(Math.abs(n), this.locale)}</span
        >
        <span class="label"
          >${this.tr(r ? "savings.lost" : "savings.saved")}</span
        >
      </div>
      <div class="compare">
        ${t ? b`<div class="row">
                <span class="name">${this.tr("savings.without_both")}</span>
                <span class="bar"
                  ><i
                    class="ns"
                    style="width:${Math.max(0, e.cost_no_solar) / i * 100}%"
                  ></i
                ></span>
                <span class="val">${O(e.cost_no_solar, this.locale)}</span>
              </div>` : C}
        <div class="row">
          <span class="name">${this.tr("savings.without")}</span>
          <span class="bar"
            ><i
              class="nb"
              style="width:${Math.max(0, e.cost_no_battery) / i * 100}%"
            ></i
          ></span>
          <span class="val">${O(e.cost_no_battery, this.locale)}</span>
        </div>
        <div class="row">
          <span class="name">${this.tr("savings.paid")}</span>
          <span class="bar"
            ><i
              class="paid"
              style="width:${Math.max(0, e.cost) / i * 100}%"
            ></i
          ></span>
          <span class="val">${O(e.cost, this.locale)}</span>
        </div>
      </div>
      ${e.estimated_quarters ? b`<p class="info">
              ${this.tr("savings.estimated", {
			n: e.estimated_quarters,
			total: e.quarters
		})}${e.price_interpolated_quarters ? ` ${this.tr("savings.estimated_price", { n: e.price_interpolated_quarters })}` : ""}
            </p>` : C}
      ${e.incomplete_quarters ? b`<p class="warn">
              ${this.tr("savings.incomplete", {
			n: e.incomplete_quarters,
			total: e.quarters
		})}
            </p>` : C}`;
	}
	renderDays(e) {
		if (!e.length) return b`<p class="muted">${this.tr("savings.no_data")}</p>`;
		let t = !this.batteryOnly && e.some((e) => e.savings_solar != null), { top: n, bottom: r } = Bn(e, t), i = n - r, a = n / i * 100, o = (e) => new Intl.DateTimeFormat(this.locale, {
			weekday: "short",
			day: "numeric",
			month: "short",
			timeZone: "UTC"
		}).format(/* @__PURE__ */ new Date(`${e}T12:00:00Z`)), s = e.reduce((e, n) => e + (n.savings_battery ?? 0) + (t ? n.savings_solar ?? 0 : 0), 0);
		return b`${e.some((e) => e.savings_solar != null) ? b`<label class="only">
          <input
            type="checkbox"
            .checked=${this.batteryOnly}
            @change=${(e) => this.batteryOnly = e.target.checked}
          />
          ${this.tr("savings.battery_only")}
        </label>` : C}<p class="muted">
        ${this.tr("savings.days_total", {
			n: e.length,
			amount: O(s, this.locale)
		})}
      </p>
      <div class="dchart">
        <div class="daxis" aria-hidden="true">
          <span style="top:0">${O(n, this.locale)}</span>
          <span style="top:${a}%">€ 0</span>
          ${r < 0 ? b`<span style="top:100%">−${O(-r, this.locale)}</span>` : C}
        </div>
        <div class="dbars">
          <div class="zero" style="top:${a}%"></div>
          ${e.map((e) => {
			let s = e.savings_battery ?? 0, c = t ? Math.max(e.savings_solar ?? 0, 0) : 0, l = s + c, u = Math.max(r, Math.min(n, l)), d = u !== l, f = Math.abs(u) / i * 100, p = l >= 0 ? `top:${a - f}%;height:${f}%` : `top:${a}%;height:${f}%`, m = [
				t && e.savings_solar != null ? this.tr("savings.day_split", {
					sun: O(e.savings_solar, this.locale),
					bat: O(s, this.locale)
				}) : "",
				e.estimated ? this.tr("savings.day_estimated") : "",
				e.incomplete ? this.tr("savings.day_incomplete") : "",
				e.hourly ? this.tr("savings.day_hourly") : ""
			].filter(Boolean), ee = `${o(e.day)}: ${e.savings_battery === null ? this.tr("savings.unknown") : O(l, this.locale)}${m.length ? ` (${m.join(", ")})` : ""}`, h = t && c > 0 ? Math.min(c, n) / i * 100 : 0, te = s >= 0 ? Math.min(s, Math.max(n - c, 0)) : Math.max(s, r), ne = Math.abs(te) / i * 100, g = s >= 0 ? `top:${a - h - ne}%;height:${ne}%` : `top:${a}%;height:${ne}%`, _ = `${e.incomplete ? " part" : ""}${e.hourly || e.estimated ? " hourly" : ""}`;
			return b`<div class="dcol" title=${ee} aria-label=${ee}>
              ${t ? b`${h > 0 ? b`<i class=${`sun${_}`} style="top:${a - h}%;height:${h}%"></i>` : C}
                      <i class=${`${s >= 0 ? "win" : "loss"}${_}${d ? " cut" : ""}`} style=${g}></i>` : b`<i
                      class=${`${l >= 0 ? "win" : "loss"}${_}${d ? " cut" : ""}`}
                      style=${p}
                    ></i>`}
              ${d ? b`<span class=${l >= 0 ? "cutlabel up" : "cutlabel down"}>${l >= 0 ? "▲" : "▼"} ${O(l, this.locale)}</span>` : C}
            </div>`;
		})}
        </div>
        <div class="dticks" aria-hidden="true">
          ${e.map((t, n) => n % 7 == 0 && e.length - n > 3 ? b`<span style="left:${(n + .5) / e.length * 100}%"
                  >${new Intl.DateTimeFormat(this.locale, {
			day: "numeric",
			month: "short",
			timeZone: "UTC"
		}).format(/* @__PURE__ */ new Date(`${t.day}T12:00:00Z`))}</span
                >` : C)}
        </div>
      </div>
      <div class="legend">
        ${t ? b`<span><i class="sw sun"></i>${this.tr("savings.leg_sun")}</span>` : C}
        <span><i class="sw win"></i>${this.tr("savings.leg_win")}</span>
        <span><i class="sw loss"></i>${this.tr("savings.leg_loss")}</span>
        <span><i class="sw part"></i>${this.tr("savings.leg_part")}</span>
        ${e.some((e) => e.hourly) ? b`<span><i class="sw hourly"></i>${this.tr("savings.leg_hourly")}</span>` : C}
        ${e.some((e) => e.estimated) ? b`<span><i class="sw hourly"></i>${this.tr("savings.leg_estimated")}</span>` : C}
      </div>`;
	}
	renderSplit(e) {
		let t = e.savings_solar_via_battery, n = e.savings_trade, r = e.discharge_kwh > 0 && e.savings_battery !== null ? e.savings_battery / e.discharge_kwh : null, i = e.includes_solar && e.savings_solar != null;
		return b`${i ? b`<dl class="group">
            <div class="grouphead">
              <dt><i class="sw sun"></i>${this.tr("savings.sun_group")}</dt>
              <dd>${O(e.savings_solar, this.locale)}</dd>
            </div>
            <div>
              <dt>${this.tr("savings.sun_direct")}</dt>
              <dd>${O(e.solar_direct_value ?? 0, this.locale)}</dd>
              <p>${A(e.solar_direct_kwh ?? 0, this.locale)} · ${this.tr("savings.sun_direct_help")}</p>
            </div>
            <div>
              <dt>${this.tr("savings.sun_export")}</dt>
              <dd>${O(e.solar_export_value ?? 0, this.locale)}</dd>
              <p>
                ${this.tr("savings.sun_export_help")}${e.solar_bonus_value ? ` ${this.tr("savings.sun_bonus", { euro: O(e.solar_bonus_value, this.locale) })}` : ""}${this.view?.saldering_until && /* @__PURE__ */ new Date() >= new Date(this.view.saldering_until) ? ` ${this.tr("savings.sun_after_saldering")}` : ""}
              </p>
            </div>
          </dl>
          <h3 class="subhead"><i class="sw win"></i>${this.tr("savings.battery_group")}
            <span>${e.savings_battery === null ? "–" : O(e.savings_battery, this.locale)}</span></h3>` : C}<dl>
        <div>
          <dt><i class="sw solar"></i>${this.tr("savings.solar_part")}</dt>
          <dd>${t === null ? "–" : O(t, this.locale)}</dd>
          <p>${this.tr("savings.solar_part_help")}</p>
        </div>
        <div>
          <dt><i class="sw trade"></i>${this.tr("savings.trade_part")}</dt>
          <dd>${n === null ? "–" : O(n, this.locale)}</dd>
          <p>${this.tr("savings.trade_part_help")}</p>
        </div>
      </dl>
      <div class="facts">
        <span
          ><b>${A(e.charge_kwh, this.locale)}</b>
          ${this.tr("savings.charged")}</span
        >
        <span
          ><b>${A(e.discharge_kwh, this.locale)}</b>
          ${this.tr("savings.delivered")}</span
        >
        ${r === null ? C : b`<span><b>${O(r, this.locale)}</b> ${this.tr("savings.per_kwh")}</span>`}
        ${i && e.solar_kwh != null ? b`<span><b>${A(e.solar_kwh, this.locale)}</b> ${this.tr("savings.sun_total")}</span>` : C}
        ${i && e.self_consumption != null ? b`<span><b>${Math.round(e.self_consumption * 100)} %</b> ${this.tr("savings.self_consumption")}</span>` : C}
      </div>`;
	}
	static {
		this.styles = s`
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
    .bar .ns {
      background: var(--z-solar);
    }
    .info {
      margin: 0;
      padding: 8px 12px;
      border-radius: 10px;
      background: var(--z-track);
      color: var(--z-muted);
      font-size: 13px;
    }
    i.sun,
    .sw.sun {
      background: var(--z-solar);
    }
    .only {
      display: inline-flex;
      align-items: center;
      gap: 6px;
      font-size: 13px;
      color: var(--z-muted);
      align-self: flex-end;
    }
    .subhead {
      margin: 4px 0 0;
      display: flex;
      align-items: center;
      gap: 6px;
      font-size: 14px;
      justify-content: space-between;
    }
    .subhead span {
      font-variant-numeric: tabular-nums;
    }
    .grouphead dt,
    .grouphead dd {
      font-size: 15px;
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
      background-image: repeating-linear-gradient(
        135deg,
        rgba(255, 255, 255, 0.45) 0 2px,
        transparent 2px 5px
      );
    }
    .sw.hourly {
      background: var(--z-export)
        repeating-linear-gradient(
          135deg,
          rgba(255, 255, 255, 0.55) 0 2px,
          transparent 2px 4px
        );
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
      background: repeating-linear-gradient(
        45deg,
        var(--z-export) 0 2px,
        transparent 2px 4px
      );
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
R([E({ attribute: !1 })], Z.prototype, "view", void 0), R([E({ attribute: !1 })], Z.prototype, "uiLang", void 0), R([E()], Z.prototype, "locale", void 0), R([E()], Z.prototype, "timeZone", void 0), R([E({ type: Boolean })], Z.prototype, "admin", void 0), R([E({ attribute: !1 })], Z.prototype, "states", void 0), R([E({ attribute: !1 })], Z.prototype, "backfill", void 0), R([D()], Z.prototype, "period", void 0), R([D()], Z.prototype, "form", void 0), R([D()], Z.prototype, "busy", void 0), R([D()], Z.prototype, "result", void 0), R([D()], Z.prototype, "batteryOnly", void 0), Z = Rn = R([e("zephyr-savings")], Z);
// src/stroom.ts
function Vn(e, t) {
	return e.name ?? t(`stroom.kind_${e.kind}`);
}
function Hn(e, t) {
	let n = e.filter((e) => e.shown).map((e) => ({
		id: e.id,
		device: e,
		kwh: e.today_kwh
	})).sort((e, t) => (t.kwh ?? -1) - (e.kwh ?? -1));
	return t !== null && n.push({
		id: "rest",
		device: null,
		kwh: t
	}), n;
}
function Un(e, t, n) {
	let r = "", i = !1;
	for (let [a, o] of e) o === null ? i = !1 : (r += `${i ? "L" : "M"}${t(a).toFixed(1)},${n(o).toFixed(1)}`, i = !0);
	return r;
}
function Wn(e, t) {
	let n = Math.round(e);
	return `${n > 0 ? "+" : n < 0 ? "−" : ""}${Math.abs(n).toLocaleString(t)} W`;
}
function Gn(e) {
	let t = 200;
	for (let [, n, r] of e) n !== null && (t = Math.max(t, Math.abs(n - r)));
	return Math.ceil(t / 100) * 100;
}
var Kn = .8;
function qn(e) {
	if (!e) return "none";
	let [t, n, r, i] = e;
	return t < 30 ? "idle" : n / t >= .8 ? "good" : r >= i ? "import" : "export";
}
var Jn = [
	["solar", [
		["solar_house", "house"],
		["solar_battery", "battery"],
		["solar_grid", "grid"]
	]],
	["grid", [["grid_house", "house"], ["grid_battery", "battery"]]],
	["battery", [["battery_house", "house"], ["battery_grid", "grid"]]]
], Q = class extends T {
	constructor(...e) {
		super(...e), this.uiLang = "en", this.locale = "en", this.timeZone = "UTC", this.base = "";
	}
	tr(e, t = {}) {
		return F(this.uiLang, e, t);
	}
	render() {
		let e = this.view, t = e?.picture;
		return b`<div class="layout" style=${`--house-ar:${(t && t.width && t.height ? t.width / t.height : 1700 / 1225).toFixed(4)}`}>
      <zephyr-house
        .sign=${this.sign}
        .now=${this.now}
        .view=${e}
        .uiLang=${this.uiLang}
        .locale=${this.locale}
        .base=${this.base}
      ></zephyr-house>
      ${e ? this.renderRoutes(e.today) : b`<section class="card skeleton"></section>`}
      ${e && (e.devices?.length || e.airco_set) ? this.renderDevices(e) : C}
      ${e?.regulation ? this.renderRegulation(e.regulation, e.live) : C}
      ${e ? this.renderZero(e) : C}
    </div>`;
	}
	renderZero(e) {
		let t = e.zero, n = t?.score ?? null, r = n !== null && n >= .8;
		return b`<section class="card" aria-labelledby="zr-title">
      <div>
        <h2 id="zr-title">${this.tr("stroom.zero_title")}</h2>
        <p class="sub">
          ${this.tr("stroom.zero_sub", { band: t?.band_w ?? 50 })}
        </p>
      </div>
      ${n === null ? b`<p class="empty">
              ${this.tr(e.live ? "stroom.zero_empty" : "stroom.zero_shadow")}
            </p>` : b`<div class="row">
              <span class="big">${j(n * 100, this.locale)}</span>
              <span class=${r ? "pill good" : "pill warn"}
                >${this.tr(r ? "stroom.zero_good" : "stroom.zero_low", { goal: j(Kn * 100, this.locale) })}</span
              >
            </div>`}
      ${t ? this.strip(t) : C}
      <div class="legend">
        <span
          ><i class="k good"></i
          >${this.tr("stroom.zero_in", { band: t?.band_w ?? 50 })}</span
        >
        <span><i class="k import"></i>${this.tr("stroom.zero_import")}</span>
        <span><i class="k export"></i>${this.tr("stroom.zero_export")}</span>
        <span><i class="k idle"></i>${this.tr("stroom.zero_idle")}</span>
      </div>
      ${t && n !== null ? b`<div class="facts">
              <span
                ><span class="k-l">${this.tr("stroom.zero_imported")}</span
                ><b>${A(t.import_kwh, this.locale, 2)}</b></span
              >
              <span
                ><span class="k-l">${this.tr("stroom.zero_exported")}</span
                ><b>${A(t.export_kwh, this.locale, 2)}</b></span
              >
              <span
                ><span class="k-l">${this.tr("stroom.zero_mean")}</span
                ><b>${k(t.mean_dev_w ?? 0, this.locale)}</b></span
              >
            </div>` : C}
    </section>`;
	}
	strip(e) {
		let t = 360 / (e.buckets.length || 288), n = e.buckets.map((e, n) => {
			let r = qn(e);
			return r === "none" ? C : x`<rect x=${(n * t).toFixed(2)} y="2" width=${(t + .3).toFixed(2)} height="22" class=${`c ${r}`}></rect>`;
		});
		return b`<svg
      class="strip"
      viewBox="0 0 360 40"
      role="img"
      aria-label=${this.tr("stroom.zero_strip")}
    >
      <rect x="0" y="2" width="360" height="22" class="frame-bg"></rect>
      ${n}
      <rect x="0" y="2" width="360" height="22" rx="3" class="frame"></rect>
      ${[
			0,
			6,
			12,
			18,
			24
		].map((e) => x`<text x=${Math.min(358, Math.max(1, e * 15))} y="37" text-anchor=${e === 0 ? "start" : e === 24 ? "end" : "middle"}>${String(e).padStart(2, "0")}:00</text>`)}
    </svg>`;
	}
	renderRoutes(e) {
		let t = Math.max(.5, ...Object.values(e.routes)), n = e.last_quarter ? new Date(new Date(e.last_quarter).getTime() + 9e5).toLocaleTimeString(this.locale, {
			hour: "2-digit",
			minute: "2-digit",
			timeZone: this.timeZone
		}) : null;
		return b`<section class="card" aria-labelledby="rt-title">
      <div>
        <h2 id="rt-title">${this.tr("stroom.routes_title")}</h2>
        <p class="sub">
          ${n ? this.tr("stroom.routes_sub", { until: n }) : this.tr("stroom.routes_none")}
        </p>
      </div>
      ${Jn.map(([n, r]) => b`<div class="grp">${this.tr(`stroom.src_${n}`)}</div>
            ${r.map(([r, i]) => b`<div class="route">
                  <span>→ ${this.tr(`stroom.to_${i}`)}</span>
                  <div class="bar">
                    <div
                      class=${`fill ${n}`}
                      style=${`width:${Math.min(100, e.routes[r] / t * 100)}%`}
                    ></div>
                  </div>
                  <span class="num">${A(e.routes[r], this.locale)}</span>
                </div>`)}`)}
      <div class="facts">
        ${e.self_use === null ? C : b`<span
                ><span class="k-l">${this.tr("stroom.self_use")}</span
                ><b>${j(e.self_use * 100, this.locale)}</b></span
              >`}
        ${e.own_source === null ? C : b`<span
                ><span class="k-l">${this.tr("stroom.own_source")}</span
                ><b>${j(e.own_source * 100, this.locale)}</b></span
              >`}
        ${e.grid_battery_price === null ? C : b`<span
                ><span class="k-l">${this.tr("stroom.grid_battery_price")}</span
                ><b>${O(e.grid_battery_price, this.locale)}/kWh</b></span
              >`}
      </div>
    </section>`;
	}
	renderRegulation(e, t) {
		let n = typeof window < "u" && window.matchMedia?.("(max-width: 600px)").matches, r = n ? 360 : 760, i = n ? 50 : 52, a = r - 8, o = e.window_s, s = (e) => i + (e + o) / o * (a - i), c = Gn(e.samples), l = (e) => 69 - Math.max(-c, Math.min(c, e)) / c * 55, u = 0, d = 0;
		for (let [, , , t, n] of e.samples) u = Math.min(u, t, n ?? 0), d = Math.max(d, t, n ?? 0);
		let f = Math.max(500, Math.ceil((d - u) / 250) * 250), p = Math.floor(u / 250) * 250, m = (e) => 248 - (e - p) / f * 90, ee = Un(e.samples.map(([e, t, n]) => [e, t === null ? null : t - n]), s, l), h = Un(e.samples.map(([e, , , t]) => [e, t]), s, m), te = Un(e.samples.map(([e, , , , t]) => [e, t]), s, m), ne = [], g = null;
		e.samples.forEach(([t, , , , , n], r) => {
			let i = r === e.samples.length - 1;
			!n && g === null && (g = t), (n || i) && g !== null && (ne.push(x`<rect x=${s(g)} y=${14} width=${Math.max(1, s(t) - s(g))} height=${234} class="idle"></rect>`), g = null);
		});
		let _ = [
			p,
			p + f / 2,
			p + f
		], re = this.tr("stroom.reg_title");
		return b`<section class="card" aria-labelledby="rg-title">
      <div>
        <h2 id="rg-title">${re}</h2>
        <p class="sub">${this.tr("stroom.reg_sub")}</p>
      </div>
      ${e.samples.length < 2 ? b`<p class="empty">${this.tr("stroom.reg_empty")}</p>` : b`<svg
                class="reg"
                viewBox="0 0 ${r} ${270}"
                role="img"
                aria-label=${re}
              >
                ${ne}
                <rect
                  x=${i}
                  y=${l(e.band_w)}
                  width=${a - i}
                  height=${l(-e.band_w) - l(e.band_w)}
                  class="band"
                ></rect>
                <line
                  x1=${i}
                  x2=${a}
                  y1=${l(0)}
                  y2=${l(0)}
                  class="axis"
                ></line>
                ${[
			c,
			0,
			-c
		].map((e) => x`<text x=${i - 6} y=${l(e) + 3} text-anchor="end">${Wn(e, this.locale)}</text>`)}
                <text x=${i} y=${11} class="cap">
                  ${this.tr("stroom.reg_p1")}
                </text>
                <path d=${ee} class="dev"></path>
                ${_.map((e) => x`<line x1=${i} x2=${a} y1=${m(e)} y2=${m(e)} class="grid"></line>
                  <text x=${i - 6} y=${m(e) + 3} text-anchor="end">${Wn(e, this.locale)}</text>`)}
                <text x=${i} y=${153} class="cap">
                  ${this.tr("stroom.reg_battery")}
                </text>
                <path d=${h} class="sp"></path>
                <path d=${te} class="bat"></path>
                ${[
			[-o, this.tr("stroom.reg_ago", { m: Math.round(o / 60) })],
			[-o / 2, this.tr("stroom.reg_ago", { m: Math.round(o / 120) })],
			[0, this.tr("stroom.reg_now")]
		].map(([e, t]) => x`<text x=${s(e)} y=${264} text-anchor=${e === 0 ? "end" : e === -o ? "start" : "middle"}>${t}</text>`)}
              </svg>
              <div class="legend">
                <span><i class="k dev"></i>${this.tr("stroom.reg_dev")}</span>
                <span><i class="k band"></i>±${e.band_w} W</span>
                <span><i class="k sp"></i>${this.tr("stroom.reg_sp")}</span>
                <span><i class="k bat"></i>${this.tr("stroom.reg_bat")}</span>
                <span
                  ><i class="k idle"></i
                  >${this.tr(t ? "stroom.reg_idle" : "stroom.reg_shadow")}</span
                >
              </div>
              <div class="facts">
                <span
                  ><span class="k-l">${this.tr("stroom.reg_recovery")}</span
                  ><b
                    >${e.recovery_s === null ? "–" : this.tr("stroom.reg_seconds", { s: e.recovery_s.toLocaleString(this.locale) })}</b
                  ></span
                >
                <span
                  ><span class="k-l">${this.tr("stroom.reg_follow")}</span
                  ><b
                    >${e.follow_w === null ? "–" : k(e.follow_w, this.locale)}</b
                  ></span
                >
                <span
                  ><span class="k-l">${this.tr("stroom.reg_peaks")}</span
                  ><b>${e.peaks}</b></span
                >
              </div>`}
    </section>`;
	}
	renderDevices(e) {
		let t = (e) => this.tr(e), n = Hn(e.devices ?? [], e.rest_today_kwh ?? null), r = Math.max(.5, ...n.map((e) => e.kwh ?? 0)), i = e.today.airco;
		return b`<section class="card" aria-labelledby="dv-title">
      <div>
        <h2 id="dv-title">${this.tr("stroom.devices_title")}</h2>
        <p class="sub">${this.tr("stroom.devices_sub")}</p>
      </div>
      ${n.map((e) => b`<div class="route dev">
            <span
              >${e.device ? Vn(e.device, t) : this.tr("stroom.rest")}${e.device && e.device.power_w !== null && e.device.power_w >= 10 ? b` <span class="live"
                      >${k(e.device.power_w, this.locale)}</span
                    >` : C}</span
            >
            <div class="bar">
              <div
                class=${e.device ? "fill house" : "fill grid"}
                style=${`width:${Math.min(100, (e.kwh ?? 0) / r * 100)}%`}
              ></div>
            </div>
            <span class="num"
              >${e.kwh === null ? "–" : A(e.kwh, this.locale)}</span
            >
          </div>`)}
      <div class="facts">
        ${i ? b`<span
                ><span class="k-l">${this.tr("stroom.airco_not_battery")}</span
                ><b
                  >${this.tr("stroom.airco_fed_line", {
			solar: A(i.solar_kwh, this.locale),
			grid: A(i.grid_kwh, this.locale)
		})}${i.grid_cost === null ? "" : ` · ${O(i.grid_cost, this.locale)}`}</b
                ></span
              >` : C}
        <span
          ><span class="k-l">${this.tr("stroom.house_total")}</span
          ><b>${A(e.today.house_kwh, this.locale)}</b></span
        >
      </div>
      ${(e.devices ?? []).some((e) => e.kind !== "airco") ? C : b`<p class="muted small">${this.tr("stroom.devices_hint")}</p>`}
    </section>`;
	}
	static {
		this.styles = s`
    :host {
      display: block;
      container-type: inline-size;
      color: var(--z-text);
      font-family: var(--z-font);
    }
    .layout {
      display: grid;
      grid-template-columns: minmax(0, 1fr) minmax(0, 1fr);
      gap: 16px;
      align-items: start;
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
    .wide {
      grid-column: 1 / -1;
    }
    .reg {
      width: 100%;
      max-width: 1000px;
      display: block;
    }
    .reg text {
      font-size: 10px;
      fill: var(--z-muted);
      font-family: var(--z-font);
    }
    .reg .cap {
      font-size: 10.5px;
    }
    .reg .band,
    .k.band {
      fill: var(--z-good-bg);
      background: var(--z-good-bg);
    }
    .reg .idle {
      fill: var(--z-track);
      opacity: 0.45;
    }
    .reg .axis,
    .reg .grid {
      stroke: var(--z-border);
    }
    .reg path {
      fill: none;
      stroke-width: 1.8;
      stroke-linejoin: round;
    }
    .reg .dev {
      stroke: var(--z-bar);
    }
    .reg .sp {
      stroke: var(--z-charge);
      stroke-dasharray: 5 3;
    }
    .reg .bat {
      stroke: var(--z-deliver);
    }
    .k.dev {
      background: var(--z-bar);
    }
    .k.sp {
      background: var(--z-charge);
    }
    .k.bat {
      background: var(--z-deliver);
    }
    .skeleton {
      min-height: 220px;
    }
    h2 {
      margin: 0;
      font-family: var(--z-font-head);
      font-size: 18px;
    }
    .sub,
    .empty,
    .muted {
      margin: 2px 0 0;
      color: var(--z-muted);
      font-size: 13px;
    }
    .row {
      display: flex;
      gap: 14px;
      align-items: baseline;
      flex-wrap: wrap;
    }
    .big {
      font-family: var(--z-font-head);
      font-size: 40px;
      font-weight: 600;
      line-height: 1;
    }
    .pill {
      border-radius: 99px;
      padding: 2px 10px;
      font-size: 12px;
      font-weight: 600;
    }
    .pill.good {
      background: var(--z-good-bg);
      color: var(--z-good-text);
    }
    .pill.warn {
      background: var(--z-warn-bg);
      color: var(--z-warn-text);
    }
    .strip {
      width: 100%;
      max-width: 520px;
      display: block;
    }
    .strip text {
      font-size: 9.5px;
      fill: var(--z-muted);
      font-family: var(--z-font);
    }
    .frame-bg {
      fill: var(--z-bg);
    }
    .frame {
      fill: none;
      stroke: var(--z-border);
    }
    .c.good,
    .k.good {
      fill: var(--z-bar);
      background: var(--z-bar);
      opacity: 0.6;
    }
    .c.import,
    .k.import {
      fill: var(--z-deliver);
      background: var(--z-deliver);
    }
    .c.export,
    .k.export {
      fill: var(--z-export);
      background: var(--z-export);
    }
    .c.idle,
    .k.idle {
      fill: var(--z-track);
      background: var(--z-track);
    }
    .legend {
      display: flex;
      gap: 6px 14px;
      flex-wrap: wrap;
      font-size: 12px;
      color: var(--z-muted);
    }
    .legend .k {
      display: inline-block;
      width: 12px;
      height: 8px;
      border-radius: 2px;
      margin-right: 5px;
    }
    .facts {
      display: flex;
      gap: 8px 22px;
      flex-wrap: wrap;
      margin-top: 4px;
    }
    .facts > span {
      display: flex;
      flex-direction: column;
    }
    .k-l {
      color: var(--z-muted);
      font-size: 12px;
    }
    .grp {
      font-size: 11.5px;
      color: var(--z-muted);
      text-transform: uppercase;
      letter-spacing: 0.04em;
      margin-top: 4px;
    }
    .route {
      display: grid;
      grid-template-columns: 90px minmax(0, 1fr) 70px;
      gap: 8px;
      align-items: center;
      font-size: 13.5px;
    }
    .bar {
      height: 12px;
      border-radius: 6px;
      background: var(--z-track);
      overflow: hidden;
    }
    .fill {
      height: 100%;
      border-radius: 6px;
    }
    .fill.solar {
      background: var(--z-solar);
    }
    .fill.grid {
      background: var(--z-bar);
    }
    .fill.house {
      background: var(--z-charge);
    }
    .route.dev {
      grid-template-columns: 150px minmax(0, 1fr) 70px;
    }
    .live {
      color: var(--z-charge);
      font-size: 12px;
      font-weight: 600;
    }
    .small {
      font-size: 12px;
    }
    .fill.battery {
      background: var(--z-deliver);
    }
    .num {
      text-align: right;
      font-variant-numeric: tabular-nums;
    }
    @container (min-width: 1200px) {
      /* Wide panel: picture on the left (as high as the screen allows), today's cards next to it. */
      .layout {
        grid-template-columns: minmax(
            0,
            calc((100vh - 300px) * var(--house-ar, 1.3878) + 30px)
          ) minmax(360px, 1fr);
        grid-template-rows: auto 1fr;
        align-items: stretch;
      }
      zephyr-house {
        grid-column: 1;
        grid-row: 1 / span 2;
      }
    }
    @media (max-width: 900px) {
      .layout {
        grid-template-columns: minmax(0, 1fr);
      }
    }
    @media (max-width: 600px) {
      .card {
        padding: 16px;
      }
      .reg.narrow text {
        font-size: 9.5px;
      }
      .big {
        font-size: 34px;
      }
    }
  `;
	}
};
R([E({ attribute: !1 })], Q.prototype, "now", void 0), R([E({ attribute: !1 })], Q.prototype, "view", void 0), R([E({ attribute: !1 })], Q.prototype, "uiLang", void 0), R([E()], Q.prototype, "locale", void 0), R([E()], Q.prototype, "timeZone", void 0), R([E()], Q.prototype, "base", void 0), R([E({ attribute: !1 })], Q.prototype, "sign", void 0), Q = R([e("zephyr-stroom")], Q);
// src/now.ts
var Yn = /* @__PURE__ */ new Set([
	"delivering",
	"charging_solar",
	"plan_charge",
	"plan_hold",
	"plan_export"
]), Xn = /* @__PURE__ */ new Set([
	"p1_missing",
	"p1_lost",
	"p1_stale",
	"p1_too_slow",
	"no_set",
	"blocked",
	"temperature"
]);
function Zn(e) {
	return !e || Yn.has(e) ? "hide" : Xn.has(e) ? "warn" : "note";
}
function Qn(e) {
	if (!e) return null;
	for (let [t, n] of Object.entries(e)) if (t.startsWith("update.") && String(n.attributes?.release_url ?? "").toLowerCase().includes("github.com/cardinal808/zephyr/")) return n;
	return null;
}
var $n = (e) => String(e ?? "").replace(/^v/i, "");
function er(e, t) {
	let n = $n(e);
	if (!t) return {
		kind: "version",
		running: n
	};
	let r = $n(t.attributes.installed_version), i = $n(t.attributes.latest_version);
	return r && n && r !== n ? {
		kind: "restart",
		running: n,
		installed: r
	} : t.state === "on" && i && i !== n ? {
		kind: "update",
		running: n,
		latest: i,
		entity: t.entity_id,
		url: typeof t.attributes.release_url == "string" ? t.attributes.release_url : null,
		busy: t.attributes.in_progress === !0 || typeof t.attributes.in_progress == "number"
	} : {
		kind: "version",
		running: n
	};
}
function tr(e, t) {
	let n = Math.round(e), r = n > 0 ? "+" : n < 0 ? "−" : "", i = Math.abs(n) <= 50 ? "zero" : n > 0 ? "import" : "export";
	return {
		text: `${r}${Xe(Math.abs(n), t, 0)} W`,
		kind: i
	};
}
// src/zephyr-panel.ts
var nr = "/zephyr_static", rr = [
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
function ir(e) {
	let t = "zephyr-fonts";
	if (document.getElementById(t)) return;
	let n = document.createElement("style");
	n.id = t, n.textContent = rr.map(([t, n, r]) => `@font-face{font-family:"${t}";font-style:normal;font-weight:${n};font-display:swap;src:url("${e}/fonts/${r}") format("woff2");}`).join("\n"), document.head.appendChild(n);
}
var $ = class extends T {
	constructor(...e) {
		super(...e), this.narrow = !1, this.status = "loading", this.view = "plan", this.clockMs = Date.now(), this.batteryDaysAt = 0, this.period = Ot(), this.openGroup = null, this.appliancesFor = null, this.confirmLive = !1, this.confirmUpdate = !1, this.controlBusy = !1, this.controlError = null, this.pendingMode = null, this.planFor = "", this.planBusy = !1, this.subscribing = !1, this.onReady = () => {
			this.status = "loading", this.subscribe();
		}, this.onDisconnected = () => {
			this.unsubscribe = void 0, this.status = "disconnected";
		}, this.planAppliance = async (e, t) => {
			if (this.hass) try {
				this.appliancesView = await this.hass.callWS({
					type: "zephyr/appliances/plan",
					appliance: e,
					...t
				});
			} catch (e) {
				this.controlError = e?.message ?? String(e);
			}
		}, this.clearAppliance = async (e) => {
			if (this.hass) try {
				this.appliancesView = await this.hass.callWS({
					type: "zephyr/appliances/clear",
					appliance: e
				});
			} catch (e) {
				this.controlError = e?.message ?? String(e);
			}
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
		}, this.saveAppliances = async (e) => {
			if (this.hass) try {
				await this.hass.callWS({
					type: "zephyr/appliances/update",
					appliances: e
				}), this.appliancesFor = null;
			} catch (e) {
				this.controlError = e?.message ?? String(e);
			}
		}, this.signPath = async (e) => {
			if (!this.hass) throw Error("no hass");
			return (await this.hass.callWS({
				type: "auth/sign_path",
				path: e,
				expires: 86400
			})).path;
		}, this.houseCall = async (e) => {
			if (!this.hass) throw Error("no hass");
			return this.hass.callWS(e);
		}, this.saveHouse = async (e, t) => {
			if (this.hass) {
				try {
					await this.hass.callWS({
						type: "zephyr/house/layout",
						floors: e,
						hidden: t
					});
				} catch (e) {
					this.controlError = e?.message ?? String(e);
				}
				await this.loadSettings();
			}
		}, this.setVacation = async (e, t) => {
			let n = this.settingsView?.vacation?.entities;
			if (this.hass && n?.switch) {
				this.controlError = null;
				try {
					e && t && n.until && await this.hass.callWS({
						type: "call_service",
						domain: "datetime",
						service: "set_value",
						service_data: {
							entity_id: n.until,
							datetime: `${t.replace("T", " ")}:00`
						}
					}), await this.hass.callWS({
						type: "call_service",
						domain: "switch",
						service: e ? "turn_on" : "turn_off",
						service_data: { entity_id: n.switch }
					});
				} catch (e) {
					this.controlError = e?.message ?? String(e);
				}
				await this.loadSettings();
			}
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
		return this.panel?.config?.static ?? nr;
	}
	get uiLang() {
		return et(this.hass?.locale?.language ?? this.hass?.language);
	}
	get locale() {
		return this.hass?.locale?.language ?? this.hass?.language ?? "en";
	}
	get timeZone() {
		return this.hass?.config.time_zone ?? Intl.DateTimeFormat().resolvedOptions().timeZone;
	}
	tr(e, t = {}) {
		return F(this.uiLang, e, t);
	}
	connectedCallback() {
		super.connectedCallback(), ir(this.base), this.clockTimer = window.setInterval(() => this.clockMs = Date.now(), 3e4), this.planTimer = window.setInterval(() => void this.loadPlan(!0), 3e5), this.hass && this.subscribe();
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
	async loadBatteryDays() {
		if (!(!this.hass || Date.now() - this.batteryDaysAt < 9e5)) {
			this.batteryDaysAt = Date.now();
			try {
				this.batteryDays = await this.hass.callWS({ type: "zephyr/battery_days" }), this.batteryDaysAt = Date.now();
			} catch {}
		}
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
	async loadAppliances() {
		let e = this.now?.appliances_revision;
		if (this.hass && e != null && e !== this.appliancesFor) {
			this.appliancesFor = e;
			try {
				this.appliancesView = await this.hass.callWS({ type: "zephyr/appliances" });
			} catch {
				this.appliancesFor = null;
			}
		}
	}
	runInputs() {
		let e = this.appliancesView;
		if (!e) return [];
		let t = new Map(e.appliances.map((e) => [e.id, e]));
		return e.planned.flatMap((e) => {
			let n = e.fixed_start ?? e.best_start, r = t.get(e.appliance);
			return n && r ? [{
				name: r.name,
				start: n,
				minutes: e.minutes ?? r.minutes,
				fixed: e.fixed_start !== null
			}] : [];
		});
	}
	async loadSets() {
		if (this.hass && this.view === "sets") try {
			this.setsView = await this.hass.callWS({ type: "zephyr/sets" }), this.batteryDays = await this.hass.callWS({ type: "zephyr/battery_days" });
		} catch {}
	}
	async loadStroom() {
		if (this.hass && this.view === "stroom") try {
			this.stroomView = await this.hass.callWS({ type: "zephyr/stroom" });
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
			this.eventsView = await this.hass.callWS({ type: "zephyr/events" }), this.planCheck = await this.hass.callWS({
				type: "zephyr/plan_check",
				days: 14
			});
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
		this.view = e, window.clearInterval(this.setsTimer), e === "sets" ? (this.loadSets(), this.setsTimer = window.setInterval(() => void this.loadSets(), 1e4)) : e === "settings" ? this.loadSettings() : e === "savings" ? this.loadSavings() : e === "stroom" ? (this.loadStroom(), this.setsTimer = window.setInterval(() => void this.loadStroom(), 5e3)) : e === "diagnostics" && (this.loadEvents(), this.setsTimer = window.setInterval(() => void this.loadEvents(), 15e3));
	}
	retry(e) {
		window.clearTimeout(this.retryTimer), this.retryTimer = window.setTimeout(() => void this.subscribe(), e);
	}
	onEvent(e) {
		e.type === "now" ? (this.now = e.data, this.pendingMode === e.data.mode && (this.pendingMode = null), this.status = "ok", this.clockMs = Date.now(), this.loadPlan(), this.loadAppliances(), this.loadBatteryDays()) : e.type === "unloaded" && (this.unsubscribe = void 0, this.status = "reloading", this.retry(3e3));
	}
	render() {
		return b`
      <div class="page">
        ${this.renderHeader()}
        <main>${this.renderBanner()} ${this.renderView()}</main>
      </div>
    `;
	}
	renderHeader() {
		let e = this.now, t = [
			["plan", "menu.plan"],
			["stroom", "menu.stroom"],
			["sets", (e?.sets_total ?? 1) <= 1 ? "menu.battery" : "menu.sets"],
			["savings", "menu.savings"],
			["settings", "menu.settings"],
			["diagnostics", "menu.diagnostics"]
		];
		return b`
      <header>
        <div class="brand">
          <img src="${this.base}/logo.png" alt="" width="32" height="32" />
          <span>ZEPHYR</span>
        </div>
        <nav aria-label=${this.tr("menu.label")}>
          ${t.map(([e, t]) => b`<button
                type="button"
                class=${this.view === e ? "tab active" : "tab"}
                aria-current=${this.view === e ? "page" : "false"}
                @click=${() => this.show(e)}
              >
                ${this.tr(t)}
              </button>`)}
        </nav>
        <div class="meta">
          ${e ? this.renderControls(e) : C} ${this.renderVersion()}
        </div>
      </header>
    `;
	}
	renderControls(e) {
		let t = this.admin && !!e.entities?.mode, n = this.admin && !!e.entities?.live, r = this.tr(e.live ? "header.live" : "header.shadow"), i = this.tr(e.live ? "header.live_title" : "header.shadow_title");
		return b`${t ? b`<label class="chipselect">
            <span class="sr">${this.tr("control.mode")}</span>
            <select
              class="chip"
              ?disabled=${this.controlBusy}
              @change=${(e) => this.setMode(e.target.value)}
            >
              ${e.modes.map((t) => b`<option value=${t} ?selected=${t === e.mode}>${this.tr(`mode.${t}`)}</option>`)}
            </select>
          </label>` : b`<span class="chip">${this.tr(`mode.${e.mode}`)}</span>`}
    ${n ? b`<span class="livewrap">
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
            ${this.confirmLive && !e.live ? this.renderConfirmLive(e) : C}
          </span>` : b`<span class=${e.live ? "chip live" : "chip"} title=${i}
            >${r}</span
          >`}`;
	}
	renderVersion() {
		let e = this.panel?.config?.version;
		if (!e) return C;
		let t = er(e, Qn(this.hass?.states));
		return t.kind === "version" ? b`<span class="version">v${t.running}</span>` : t.kind === "restart" ? this.admin ? b`<span class="livewrap verwrap">
            <button
              type="button"
              class="chip warn"
              aria-expanded=${this.confirmUpdate ? "true" : "false"}
              @click=${() => this.confirmUpdate = !this.confirmUpdate}
            >
              ${this.tr("version.restart")}
            </button>
            ${this.confirmUpdate ? this.renderConfirm(this.tr("version.restart_title"), this.tr("version.restart_text", {
			running: t.running,
			installed: t.installed
		}), this.tr("version.restart_do"), () => this.callService("homeassistant", "restart", {})) : C}
          </span>` : b`<span class="version"
            >${this.tr("version.restart_other", { running: t.running })}</span
          >` : this.admin ? b`<span class="livewrap verwrap">
      <button
        type="button"
        class="chip update"
        aria-expanded=${this.confirmUpdate ? "true" : "false"}
        ?disabled=${t.busy}
        @click=${() => this.confirmUpdate = !this.confirmUpdate}
      >
        ${t.busy ? this.tr("version.busy") : this.tr("version.update", { latest: t.latest })}
      </button>
      ${this.confirmUpdate && !t.busy ? this.renderConfirm(this.tr("version.update_title", { latest: t.latest }), this.tr("version.update_text", { running: t.running }), this.tr("version.update_do"), () => this.callService("update", "install", { entity_id: t.entity }), t.url) : C}
    </span>` : b`<span class="version"
        >${this.tr("version.update_other", {
			running: t.running,
			latest: t.latest
		})}</span
      >`;
	}
	renderConfirm(e, t, n, r, i = null) {
		return b`<div class="popover" role="dialog" aria-label=${e}>
      <strong>${e}</strong>
      <p>${t}</p>
      ${i ? b`<p>
              <a href=${i} target="_blank" rel="noreferrer"
                >${this.tr("version.notes")}</a
              >
            </p>` : C}
      <div class="row">
        <button
          type="button"
          class="ghost"
          @click=${() => this.confirmUpdate = !1}
        >
          ${this.tr("control.cancel")}
        </button>
        <button
          type="button"
          class="primary"
          ?disabled=${this.controlBusy}
          @click=${async () => {
			await r(), this.confirmUpdate = !1;
		}}
        >
          ${n}
        </button>
      </div>
    </div>`;
	}
	renderConfirmLive(e) {
		let t = e.blockers.length > 0;
		return b`<div
      class="popover"
      role="dialog"
      aria-label=${this.tr("control.live_title")}
    >
      <strong>${this.tr("control.live_title")}</strong>
      <p>${this.tr(t ? "control.live_blocked" : "control.live_text")}</p>
      ${t ? b`<ul>
              ${e.blockers.map((e) => b`<li>${kn(e, this.uiLang)}</li>`)}
            </ul>` : C}
      <div class="row">
        <button
          type="button"
          class="ghost"
          @click=${() => this.confirmLive = !1}
        >
          ${this.tr("control.cancel")}
        </button>
        <button
          type="button"
          class="primary"
          ?disabled=${t || this.controlBusy}
          @click=${() => void this.setLive(!0)}
        >
          ${this.tr("control.live_start")}
        </button>
      </div>
    </div>`;
	}
	renderBanner() {
		if (this.controlError && this.status === "ok") return b`<div class="banner" role="alert">
        ${this.tr("control.failed", { error: this.controlError })}
        <button
          type="button"
          class="link"
          @click=${() => this.controlError = null}
        >
          ${this.tr("control.close")}
        </button>
      </div>`;
		switch (this.status) {
			case "not_loaded": return b`<div class="banner" role="status">
          ${this.tr("status.not_loaded")}
        </div>`;
			case "reloading": return b`<div class="banner info" role="status">
          ${this.tr("status.reloading")}
        </div>`;
			case "disconnected": return b`<div class="banner" role="status">
          ${this.tr("status.disconnected", { time: this.now ? M(this.now.updated_at, this.locale, this.timeZone) : "–" })}
        </div>`;
			default: return C;
		}
	}
	renderView() {
		return this.view === "plan" ? this.renderPlan() : this.view === "sets" ? b`<zephyr-sets
        class=${this.status === "ok" ? "" : "stale"}
        .view=${this.setsView}
        .days=${this.batteryDays}
        .uiLang=${this.uiLang}
        .locale=${this.locale}
        .timeZone=${this.timeZone}
      ></zephyr-sets>` : this.view === "settings" ? b`<zephyr-settings
        class=${this.status === "ok" ? "" : "stale"}
        .view=${this.settingsView}
        .uiLang=${this.uiLang}
        .locale=${this.locale}
        .friendlyName=${(e) => this.hass?.states?.[e]?.attributes?.friendly_name}
        .states=${this.hass?.states}
        .save=${this.saveSettings}
        .setVacation=${this.setVacation}
        .saveHouse=${this.saveHouse}
        .houseCall=${this.houseCall}
        .sign=${this.signPath}
        .reload=${() => this.loadSettings()}
        .openGroup=${this.openGroup}
        .appliances=${this.appliancesView}
        .saveAppliances=${this.saveAppliances}
      ></zephyr-settings>` : this.view === "stroom" ? b`<zephyr-stroom
        class=${this.status === "ok" ? "" : "stale"}
        .now=${this.now}
        .view=${this.stroomView}
        .base=${this.base}
        .sign=${this.signPath}
        .uiLang=${this.uiLang}
        .locale=${this.locale}
        .timeZone=${this.timeZone}
      ></zephyr-stroom>` : this.view === "savings" ? b`<zephyr-savings
        class=${this.status === "ok" ? "" : "stale"}
        .view=${this.savingsView}
        .uiLang=${this.uiLang}
        .locale=${this.locale}
        .timeZone=${this.timeZone}
        ?admin=${this.admin}
        .states=${this.hass?.states}
        .backfill=${this.backfillSavings}
      ></zephyr-savings>` : this.view === "diagnostics" ? b`<zephyr-diagnostics
        class=${this.status === "ok" ? "" : "stale"}
        .view=${this.eventsView}
        .uiLang=${this.uiLang}
        .locale=${this.locale}
        .timeZone=${this.timeZone}
        ?admin=${this.admin}
        .download=${this.downloadDiagnostics}
        .exportCosts=${this.exportCosts}
        .refresh=${() => void this.loadEvents()}
        .planCheck=${this.planCheck}
        .appliances=${this.appliancesView}
      ></zephyr-diagnostics>` : this.renderComing();
	}
	renderComing() {
		return b`<section class="card coming">
      ${this.tr("status.coming")}
    </section>`;
	}
	renderPlan() {
		let e = this.now;
		if (!e) return b`<section class="cards" aria-busy="true">
        ${[
			0,
			1,
			2
		].map(() => b`<div class="card skeleton" aria-hidden="true"></div>`)}
      </section>`;
		let t = this.status === "ok" ? "" : "stale";
		return b`<section
        class="cards ${t}"
        aria-label=${this.tr("now.title")}
      >
        ${this.renderNow(e)} ${this.renderBattery(e)}
        ${this.renderNext(e)}
      </section>
      ${e.price_entity ? this.renderPlanParts(e, t) : C}`;
	}
	renderPlanParts(e, t) {
		let n = null;
		return e.mode === "dynamic_forecasting" ? e.live || (n = this.tr("plan.shadow_note")) : n = this.tr("plan.mode_note", { mode: this.tr(`mode.${e.mode}`) }), b`${n ? b`<div class="banner info" role="note">${n}</div>` : C}
      <zephyr-prices-plan
        class=${t}
        .view=${this.planView}
        .uiLang=${this.uiLang}
        .locale=${this.locale}
        .timeZone=${this.timeZone}
        ?narrow=${this.narrow}
        .period=${this.period}
        .runs=${this.runInputs()}
        @zephyr-period=${(e) => this.period = e.detail}
        @zephyr-open-settings=${(e) => {
			this.openGroup = e.detail, this.show("settings");
		}}
        ><zephyr-appliances
          .view=${this.appliancesView}
          .quarters=${this.planView?.quarters ?? []}
          .uiLang=${this.uiLang}
          .locale=${this.locale}
          .timeZone=${this.timeZone}
          .clockMs=${this.clockMs}
          .plan=${this.planAppliance}
          .clear=${this.clearAppliance}
        ></zephyr-appliances
      ></zephyr-prices-plan>
      ${this.planView ? b`<section class="duo ${t}">${this.renderBlocks(this.planView)} ${this.renderWhy(this.planView)}</section>` : C}`;
	}
	range(e) {
		let t = M(e.start, this.locale, this.timeZone), n = M(e.end, this.locale, this.timeZone), r = `${this.tr("blocks.tomorrow")} `, i = P(e.start, this.clockMs, this.timeZone), a = P(new Date(e.end).getTime() - 1, this.clockMs, this.timeZone);
		return `${i ? "" : r}${t}–${i && !a ? r : ""}${n}`;
	}
	shownBlocks(e) {
		let t = st(e.quarters, this.timeZone)[1] ?? null;
		return yt(e.blocks, this.period, new Date(this.clockMs).toISOString(), t, this.timeZone);
	}
	renderBlocks(e) {
		let t = this.shownBlocks(e).slice(0, 12);
		return b`<article class="card">
      <h2>${this.tr(`blocks.title_${this.period}`)}</h2>
      ${t.length ? b`<ul class="blocks">
              ${t.map((e) => b`<li>
                    <span class="when">${this.range(e)}</span>
                    <span
                      class="swatch"
                      style="background:${L(e.action)}"
                    ></span>
                    <span class="what"
                      >${this.tr(`blocks.what_${e.action}`)}${e.indicative ? b` <em>(${this.tr("blocks.indicative")})</em>` : C}</span
                    >
                    <span class="detail"
                      >${this.tr(`blocks.${e.action}`, {
			kwh: A(e.kwh, this.locale),
			price: O(e.price, this.locale)
		})}</span
                    >
                  </li>`)}
            </ul>` : b`<p class="text">
              ${this.tr(this.period === "tomorrow" ? "blocks.none_tomorrow" : "blocks.none")}
            </p>`}
    </article>`;
	}
	renderWhy(e) {
		let t = [];
		e.reason && this.period !== "tomorrow" && t.push(e.reason[this.uiLang]);
		let n = this.shownBlocks(e).filter((e) => !e.indicative), r = n.filter((e) => e.action === "charge").sort((e, t) => e.price - t.price)[0];
		r ? t.push(this.tr("why.cheapest", {
			time: this.range(r),
			price: O(r.price, this.locale)
		})) : n.length && t.push(this.tr("why.no_charge"));
		let i = ct(e.quarters, this.period, this.timeZone).filter((e) => !e.past), a = ut(i)?.max;
		if (a && a.action === "deliver") {
			let e = `${P(a.start, this.clockMs, this.timeZone) ? "" : `${this.tr("blocks.tomorrow")} `}${M(a.start, this.locale, this.timeZone)}`;
			t.push(this.tr("why.peak", {
				time: e,
				price: O(a.buy, this.locale)
			}));
		}
		return i.some((e) => e.indicative) && t.push(this.tr("why.indicative")), b`<article class="card">
      <h2>${this.tr(`why.title_${this.period}`)}</h2>
      <ul class="why">
        ${t.map((e) => b`<li>${e}</li>`)}
      </ul>
    </article>`;
	}
	renderNow(e) {
		let t = e.action ?? "standby", n = e.battery_w !== null && Math.abs(e.battery_w) >= 10 ? ` · ${k(e.battery_w, this.locale)}` : "", r = e.grid_w === null ? [] : Zt(zt(e.solar_w, e.grid_w, e.battery_w).paths), i = (e) => this.tr(`house.src_${e}`), a = (e) => this.tr(`house.dst_${e}`), o = (e) => k(e, this.locale), s = Zn(e.reason_code);
		return b`<article class="card">
      <div class="label">
        <span class="dot" style="background:${L(t)}"></span
        >${this.tr("now.title")}
      </div>
      <div class="now-top">
        <div class="big">
          ${e.action ? this.tr(`action.${t}`) + n : this.tr("now.waiting")}
        </div>
        ${e.grid_w === null ? C : this.renderP1(e.grid_w)}
      </div>
      ${r.length ? b`<p class="flows">
              ${r.map((e) => b`<span
                    >${i(e.from)} ${o(e.total)} →
                    ${e.to.length === 1 ? a(e.to[0][0]) : e.to.map(([e, t], n) => b`${n ? " · " : ""}${a(e)} ${o(t)}`)}</span
                  >`)}
            </p>` : C}
      ${this.renderAirco(e)}
      ${s !== "hide" && e.reason ? b`<p class=${s === "warn" ? "nownote warn" : "nownote"}>
              ${e.reason[this.uiLang]}
            </p>` : C}
      ${e.live ? C : b`<div class="foot"><span>${this.tr("now.shadow_note")}</span></div>`}
    </article>`;
	}
	renderAirco(e) {
		let t = rt(e.excluded, this.uiLang, this.locale);
		if (!t) return C;
		let n = t.icon === "heat" ? x`<path d="M12 3c1 3 4 4.5 4 8.5a4 4 0 0 1-8 0c0-2 1-3 2-4 0 2 1 3 2 3 0-3-1-5 0-7.5Z"/>` : t.icon === "cool" ? x`<path d="M12 3v18M4.2 7.5l15.6 9M4.2 16.5l15.6-9M9.5 4.5 12 7l2.5-2.5M9.5 19.5 12 17l2.5 2.5"/>` : C;
		return b`<p class=${t.allowed ? "airco allowed" : "airco"}>
      ${t.icon ? b`<svg viewBox="0 0 24 24" aria-hidden="true">${n}</svg>` : C}
      <span
        >${t.text}${t.estimate ? b` <span
                class="estimate"
                tabindex="0"
                title=${t.estimate}
                aria-label=${`${this.tr("airco.estimate")}: ${t.estimate}`}
                >${this.tr("airco.estimate")}</span
              >` : C}</span
      >
    </p>`;
	}
	renderP1(e) {
		let t = tr(e, this.locale);
		return b`<div class="p1 ${t.kind}">
      <strong>${t.text}</strong>
      <span>${this.tr(`now.p1_${t.kind}`)}</span>
    </div>`;
	}
	renderBattery(e) {
		if (e.soc === null) return b`<article class="card">
        <div class="label">${this.tr("battery.title")}</div>
        <p class="text">${this.tr("battery.unknown")}</p>
      </article>`;
		let t = Math.max(0, Math.min(100, e.soc)), n = Math.max(0, e.buffer_pct), r = e.sets_total <= 1 ? e.sets_online >= 1 ? this.tr("battery.set") : this.tr("battery.set_offline") : this.tr("battery.sets", {
			online: e.sets_online,
			total: e.sets_total
		});
		return b`<article class="card">
      <div class="label">${this.tr("battery.title")}</div>
      <div class="big-row">
        <span class="big">${j(t, this.locale)}</span>
        ${e.energy_kwh !== null && e.capacity_kwh !== null ? b`<span class="muted"
                >${this.tr("battery.of", {
			energy: A(e.energy_kwh, this.locale),
			capacity: A(e.capacity_kwh, this.locale)
		})}</span
              >` : C}
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
        ${n > 0 ? b`<div
                class="buffer"
                style="left:${e.min_soc}%;width:${Math.min(n, 100 - e.min_soc)}%"
              ></div>` : C}
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
        ${this.renderRte()}
        <span>${r}</span>
      </div>
    </article>`;
	}
	renderRte() {
		let e = this.batteryDays?.week;
		if (!e) return C;
		let t = e.efficiency === null ? "–" : j(e.efficiency * 100, this.locale);
		return b`<span class="rte" title=${this.tr("battery.rte_title")}
      >${this.tr("battery.rte", { value: t })}
      <span class="muted"
        >· ${this.tr("sets.days_n", { n: e.efficiency_days ?? 7 })}</span
      ></span
    >`;
	}
	renderNext(e) {
		let t = e.plan, n = (e = "") => b`<div class="label">
        <span
          class="dot"
          style="background:${L(t?.next?.action)}"
        ></span
        >${this.tr("next.title")}${e}
      </div>`;
		if (!e.price_entity) return b`<article class="card">
        ${n()}
        <p class="text">${this.tr("next.no_price_source")}</p>
      </article>`;
		if (!t) return b`<article class="card">
        ${n()}
        <p class="text">${this.tr("status.loading")}</p>
      </article>`;
		if (t.state === "no_prices") {
			let e = t.no_prices_since ?? t.calculated_at;
			return b`<article class="card">
        ${n()}
        <p class="text warn">
          ${this.tr("next.no_prices", { time: e ? M(e, this.locale, this.timeZone) : "–" })}
        </p>
      </article>`;
		}
		let r = t.next, i = t.price_now ? b`<div class="foot">
          <span
            >${this.tr("next.price_now", { price: O(t.price_now.import, this.locale) })}</span
          >
        </div>` : C;
		if (!r) return b`<article class="card">
        ${n()}
        <p class="text">${this.tr("next.none")}</p>
        ${i}
      </article>`;
		let a = Qe(r.start, this.clockMs), o = a <= 0 ? this.tr("next.now") : this.tr("next.in", { time: a >= 60 ? this.tr("next.hours", {
			h: Math.floor(a / 60),
			m: a % 60
		}) : this.tr("next.minutes", { m: a }) }), s = M(r.start, this.locale, this.timeZone), c = this.tr(`action.${r.action}`), l = P(r.start, this.clockMs, this.timeZone) ? this.tr("next.at", {
			time: s,
			action: c
		}) : this.tr("next.tomorrow", {
			time: s,
			action: c
		});
		return b`<article class="card">
      ${n(` · ${o}`)}
      <div class="big">${l}</div>
      <p class="text">${this.detail(t)}</p>
      ${r.indicative ? b`<p class="text muted">${this.tr("next.indicative")}</p>` : C}
      ${i}
    </article>`;
	}
	detail(e) {
		let t = e.next;
		if (!t) return "";
		let n = {
			kwh: A(t.kwh, this.locale),
			price: O(t.price, this.locale)
		};
		return this.tr(`next.${t.action}`, n);
	}
	static {
		this.styles = [wt, s`
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
      .popover .row {
        display: flex;
        flex-wrap: wrap;
        gap: 8px;
        align-items: center;
      }
      .popover .row {
        justify-content: flex-end;
        margin-top: 8px;
      }
      .popover button {
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
      .version {
        color: var(--z-muted);
        font-size: 13px;
        font-variant-numeric: tabular-nums;
        white-space: nowrap;
      }
      .chip.update {
        background: var(--z-charge);
        border-color: var(--z-charge);
        color: #fff;
      }
      .chip.warn {
        background: var(--z-warn-bg);
        border-color: var(--z-warn-bg);
        color: var(--z-warn-text);
      }
      .popover a {
        color: inherit;
      }
      @media (max-width: 900px) {
        /* The header wraps: the version button can be at the left edge. */
        .verwrap .popover {
          right: auto;
          left: 0;
        }
      }
      .flows {
        margin: 0;
        display: flex;
        flex-direction: column;
        gap: 2px;
        line-height: 1.5;
      }
      .nownote {
        margin: 10px 0 0;
        font-size: 13px;
        color: var(--z-muted);
      }
      .nownote.warn {
        color: var(--z-warn-text);
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
        background: linear-gradient(
          90deg,
          var(--z-card),
          var(--z-track),
          var(--z-card)
        );
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
      .now-top {
        display: flex;
        flex-wrap: wrap;
        justify-content: space-between;
        align-items: center;
        gap: 12px;
      }
      .p1 {
        text-align: right;
        line-height: 1.15;
        white-space: nowrap;
      }
      .p1 strong {
        display: block;
        font-family: var(--z-font-head);
        font-size: 20px;
        font-variant-numeric: tabular-nums;
      }
      .p1 span {
        font-size: 12px;
        color: var(--z-muted);
      }
      .p1.import strong {
        color: var(--z-import);
      }
      .p1.export strong {
        color: var(--z-export);
      }
      .rte {
        color: var(--z-text);
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
        background: repeating-linear-gradient(
          45deg,
          var(--z-hold-a) 0 3px,
          transparent 3px 6px
        );
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
R([E({ attribute: !1 })], $.prototype, "hass", void 0), R([E({ type: Boolean })], $.prototype, "narrow", void 0), R([E({ attribute: !1 })], $.prototype, "panel", void 0), R([D()], $.prototype, "now", void 0), R([D()], $.prototype, "status", void 0), R([D()], $.prototype, "view", void 0), R([D()], $.prototype, "clockMs", void 0), R([D()], $.prototype, "planView", void 0), R([D()], $.prototype, "setsView", void 0), R([D()], $.prototype, "batteryDays", void 0), R([D()], $.prototype, "settingsView", void 0), R([D()], $.prototype, "period", void 0), R([D()], $.prototype, "eventsView", void 0), R([D()], $.prototype, "savingsView", void 0), R([D()], $.prototype, "stroomView", void 0), R([D()], $.prototype, "appliancesView", void 0), R([D()], $.prototype, "openGroup", void 0), R([D()], $.prototype, "planCheck", void 0), R([D()], $.prototype, "confirmLive", void 0), R([D()], $.prototype, "confirmUpdate", void 0), R([D()], $.prototype, "controlBusy", void 0), R([D()], $.prototype, "controlError", void 0), R([D()], $.prototype, "pendingMode", void 0), $ = R([e("zephyr-panel")], $);
export { $ as ZephyrPanel };
