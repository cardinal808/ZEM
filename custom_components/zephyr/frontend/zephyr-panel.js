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
})(e) : e, { is: l, defineProperty: u, getOwnPropertyDescriptor: d, getOwnPropertyNames: ee, getOwnPropertySymbols: te, getPrototypeOf: ne } = Object, f = globalThis, p = f.trustedTypes, re = p ? p.emptyScript : "", ie = f.reactiveElementPolyfillSupport, m = (e, t) => e, h = {
	toAttribute(e, t) {
		switch (t) {
			case Boolean:
				e = e ? re : null;
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
}, g = (e, t) => !l(e, t), _ = {
	attribute: !0,
	type: String,
	converter: h,
	reflect: !1,
	useDefault: !1,
	hasChanged: g
};
Symbol.metadata ??= Symbol("metadata"), f.litPropertyMetadata ??= /* @__PURE__ */ new WeakMap();
var v = class extends HTMLElement {
	static addInitializer(e) {
		this._$Ei(), (this.l ??= []).push(e);
	}
	static get observedAttributes() {
		return this.finalize(), this._$Eh && [...this._$Eh.keys()];
	}
	static createProperty(e, t = _) {
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
		return this.elementProperties.get(e) ?? _;
	}
	static _$Ei() {
		if (this.hasOwnProperty(m("elementProperties"))) return;
		let e = ne(this);
		e.finalize(), e.l !== void 0 && (this.l = [...e.l]), this.elementProperties = new Map(e.elementProperties);
	}
	static finalize() {
		if (this.hasOwnProperty(m("finalized"))) return;
		if (this.finalized = !0, this._$Ei(), this.hasOwnProperty(m("properties"))) {
			let e = this.properties, t = [...ee(e), ...te(e)];
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
			let i = (n.converter?.toAttribute === void 0 ? h : n.converter).toAttribute(t, n.type);
			this._$Em = e, i == null ? this.removeAttribute(r) : this.setAttribute(r, i), this._$Em = null;
		}
	}
	_$AK(e, t) {
		let n = this.constructor, r = n._$Eh.get(e);
		if (r !== void 0 && this._$Em !== r) {
			let e = n.getPropertyOptions(r), i = typeof e.converter == "function" ? { fromAttribute: e.converter } : e.converter?.fromAttribute === void 0 ? h : e.converter;
			this._$Em = r;
			let a = i.fromAttribute(t, e.type);
			this[r] = a ?? this._$Ej?.get(r) ?? a, this._$Em = null;
		}
	}
	requestUpdate(e, t, n, r = !1, i) {
		if (e !== void 0) {
			let a = this.constructor;
			if (!1 === r && (i = this[e]), n ??= a.getPropertyOptions(e), !((n.hasChanged ?? g)(i, t) || n.useDefault && n.reflect && i === this._$Ej?.get(e) && !this.hasAttribute(a._$Eu(e, n)))) return;
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
v.elementStyles = [], v.shadowRootOptions = { mode: "open" }, v[m("elementProperties")] = /* @__PURE__ */ new Map(), v[m("finalized")] = /* @__PURE__ */ new Map(), ie?.({ ReactiveElement: v }), (f.reactiveElementVersions ??= []).push("2.1.2");
// node_modules/lit-html/lit-html.js
var y = globalThis, b = (e) => e, x = y.trustedTypes, S = x ? x.createPolicy("lit-html", { createHTML: (e) => e }) : void 0, ae = "$lit$", C = `lit$${Math.random().toFixed(9).slice(2)}$`, w = "?" + C, oe = `<${w}>`, T = document, E = () => T.createComment(""), D = (e) => e === null || typeof e != "object" && typeof e != "function", O = Array.isArray, se = (e) => O(e) || typeof e?.[Symbol.iterator] == "function", k = "[ 	\n\f\r]", A = /<(?:(!--|\/[^a-zA-Z])|(\/?[a-zA-Z][^>\s]*)|(\/?$))/g, j = /-->/g, ce = />/g, M = RegExp(`>|${k}(?:([^\\s"'>=/]+)(${k}*=${k}*(?:[^ \t\n\f\r"'\`<>=]|("|')|))|$)`, "g"), le = /'/g, ue = /"/g, N = /^(?:script|style|textarea|title)$/i, P = ((e) => (t, ...n) => ({
	_$litType$: e,
	strings: t,
	values: n
}))(1), F = Symbol.for("lit-noChange"), I = Symbol.for("lit-nothing"), L = /* @__PURE__ */ new WeakMap(), R = T.createTreeWalker(T, 129);
function z(e, t) {
	if (!O(e) || !e.hasOwnProperty("raw")) throw Error("invalid template strings array");
	return S === void 0 ? t : S.createHTML(t);
}
var de = (e, t) => {
	let n = e.length - 1, r = [], i, a = t === 2 ? "<svg>" : t === 3 ? "<math>" : "", o = A;
	for (let t = 0; t < n; t++) {
		let n = e[t], s, c, l = -1, u = 0;
		for (; u < n.length && (o.lastIndex = u, c = o.exec(n), c !== null);) u = o.lastIndex, o === A ? c[1] === "!--" ? o = j : c[1] === void 0 ? c[2] === void 0 ? c[3] !== void 0 && (o = M) : (N.test(c[2]) && (i = RegExp("</" + c[2], "g")), o = M) : o = ce : o === M ? c[0] === ">" ? (o = i ?? A, l = -1) : c[1] === void 0 ? l = -2 : (l = o.lastIndex - c[2].length, s = c[1], o = c[3] === void 0 ? M : c[3] === "\"" ? ue : le) : o === ue || o === le ? o = M : o === j || o === ce ? o = A : (o = M, i = void 0);
		let d = o === M && e[t + 1].startsWith("/>") ? " " : "";
		a += o === A ? n + oe : l >= 0 ? (r.push(s), n.slice(0, l) + ae + n.slice(l) + C + d) : n + C + (l === -2 ? t : d);
	}
	return [z(e, a + (e[n] || "<?>") + (t === 2 ? "</svg>" : t === 3 ? "</math>" : "")), r];
}, B = class e {
	constructor({ strings: t, _$litType$: n }, r) {
		let i;
		this.parts = [];
		let a = 0, o = 0, s = t.length - 1, c = this.parts, [l, u] = de(t, n);
		if (this.el = e.createElement(l, r), R.currentNode = this.el.content, n === 2 || n === 3) {
			let e = this.el.content.firstChild;
			e.replaceWith(...e.childNodes);
		}
		for (; (i = R.nextNode()) !== null && c.length < s;) {
			if (i.nodeType === 1) {
				if (i.hasAttributes()) for (let e of i.getAttributeNames()) if (e.endsWith(ae)) {
					let t = u[o++], n = i.getAttribute(e).split(C), r = /([.?@])?(.*)/.exec(t);
					c.push({
						type: 1,
						index: a,
						name: r[2],
						strings: n,
						ctor: r[1] === "." ? pe : r[1] === "?" ? me : r[1] === "@" ? he : U
					}), i.removeAttribute(e);
				} else e.startsWith(C) && (c.push({
					type: 6,
					index: a
				}), i.removeAttribute(e));
				if (N.test(i.tagName)) {
					let e = i.textContent.split(C), t = e.length - 1;
					if (t > 0) {
						i.textContent = x ? x.emptyScript : "";
						for (let n = 0; n < t; n++) i.append(e[n], E()), R.nextNode(), c.push({
							type: 2,
							index: ++a
						});
						i.append(e[t], E());
					}
				}
			} else if (i.nodeType === 8) {
				if (i.data === w) c.push({
					type: 2,
					index: a
				});
				else {
					let e = -1;
					for (; (e = i.data.indexOf(C, e + 1)) !== -1;) c.push({
						type: 7,
						index: a
					}), e += C.length - 1;
				}
			}
			a++;
		}
	}
	static createElement(e, t) {
		let n = T.createElement("template");
		return n.innerHTML = e, n;
	}
};
function V(e, t, n = e, r) {
	if (t === F) return t;
	let i = r === void 0 ? n._$Cl : n._$Co?.[r], a = D(t) ? void 0 : t._$litDirective$;
	return i?.constructor !== a && (i?._$AO?.(!1), a === void 0 ? i = void 0 : (i = new a(e), i._$AT(e, n, r)), r === void 0 ? n._$Cl = i : (n._$Co ??= [])[r] = i), i !== void 0 && (t = V(e, i._$AS(e, t.values), i, r)), t;
}
var fe = class {
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
		let { el: { content: t }, parts: n } = this._$AD, r = (e?.creationScope ?? T).importNode(t, !0);
		R.currentNode = r;
		let i = R.nextNode(), a = 0, o = 0, s = n[0];
		for (; s !== void 0;) {
			if (a === s.index) {
				let t;
				s.type === 2 ? t = new H(i, i.nextSibling, this, e) : s.type === 1 ? t = new s.ctor(i, s.name, s.strings, this, e) : s.type === 6 && (t = new ge(i, this, e)), this._$AV.push(t), s = n[++o];
			}
			a !== s?.index && (i = R.nextNode(), a++);
		}
		return R.currentNode = T, r;
	}
	p(e) {
		let t = 0;
		for (let n of this._$AV) n !== void 0 && (n.strings === void 0 ? n._$AI(e[t]) : (n._$AI(e, n, t), t += n.strings.length - 2)), t++;
	}
}, H = class e {
	get _$AU() {
		return this._$AM?._$AU ?? this._$Cv;
	}
	constructor(e, t, n, r) {
		this.type = 2, this._$AH = I, this._$AN = void 0, this._$AA = e, this._$AB = t, this._$AM = n, this.options = r, this._$Cv = r?.isConnected ?? !0;
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
		e = V(this, e, t), D(e) ? e === I || e == null || e === "" ? (this._$AH !== I && this._$AR(), this._$AH = I) : e !== this._$AH && e !== F && this._(e) : e._$litType$ === void 0 ? e.nodeType === void 0 ? se(e) ? this.k(e) : this._(e) : this.T(e) : this.$(e);
	}
	O(e) {
		return this._$AA.parentNode.insertBefore(e, this._$AB);
	}
	T(e) {
		this._$AH !== e && (this._$AR(), this._$AH = this.O(e));
	}
	_(e) {
		this._$AH !== I && D(this._$AH) ? this._$AA.nextSibling.data = e : this.T(T.createTextNode(e)), this._$AH = e;
	}
	$(e) {
		let { values: t, _$litType$: n } = e, r = typeof n == "number" ? this._$AC(e) : (n.el === void 0 && (n.el = B.createElement(z(n.h, n.h[0]), this.options)), n);
		if (this._$AH?._$AD === r) this._$AH.p(t);
		else {
			let e = new fe(r, this), n = e.u(this.options);
			e.p(t), this.T(n), this._$AH = e;
		}
	}
	_$AC(e) {
		let t = L.get(e.strings);
		return t === void 0 && L.set(e.strings, t = new B(e)), t;
	}
	k(t) {
		O(this._$AH) || (this._$AH = [], this._$AR());
		let n = this._$AH, r, i = 0;
		for (let a of t) i === n.length ? n.push(r = new e(this.O(E()), this.O(E()), this, this.options)) : r = n[i], r._$AI(a), i++;
		i < n.length && (this._$AR(r && r._$AB.nextSibling, i), n.length = i);
	}
	_$AR(e = this._$AA.nextSibling, t) {
		for (this._$AP?.(!1, !0, t); e !== this._$AB;) {
			let t = b(e).nextSibling;
			b(e).remove(), e = t;
		}
	}
	setConnected(e) {
		this._$AM === void 0 && (this._$Cv = e, this._$AP?.(e));
	}
}, U = class {
	get tagName() {
		return this.element.tagName;
	}
	get _$AU() {
		return this._$AM._$AU;
	}
	constructor(e, t, n, r, i) {
		this.type = 1, this._$AH = I, this._$AN = void 0, this.element = e, this.name = t, this._$AM = r, this.options = i, n.length > 2 || n[0] !== "" || n[1] !== "" ? (this._$AH = Array(n.length - 1).fill(/* @__PURE__ */ new String()), this.strings = n) : this._$AH = I;
	}
	_$AI(e, t = this, n, r) {
		let i = this.strings, a = !1;
		if (i === void 0) e = V(this, e, t, 0), a = !D(e) || e !== this._$AH && e !== F, a && (this._$AH = e);
		else {
			let r = e, o, s;
			for (e = i[0], o = 0; o < i.length - 1; o++) s = V(this, r[n + o], t, o), s === F && (s = this._$AH[o]), a ||= !D(s) || s !== this._$AH[o], s === I ? e = I : e !== I && (e += (s ?? "") + i[o + 1]), this._$AH[o] = s;
		}
		a && !r && this.j(e);
	}
	j(e) {
		e === I ? this.element.removeAttribute(this.name) : this.element.setAttribute(this.name, e ?? "");
	}
}, pe = class extends U {
	constructor() {
		super(...arguments), this.type = 3;
	}
	j(e) {
		this.element[this.name] = e === I ? void 0 : e;
	}
}, me = class extends U {
	constructor() {
		super(...arguments), this.type = 4;
	}
	j(e) {
		this.element.toggleAttribute(this.name, !!e && e !== I);
	}
}, he = class extends U {
	constructor(e, t, n, r, i) {
		super(e, t, n, r, i), this.type = 5;
	}
	_$AI(e, t = this) {
		if ((e = V(this, e, t, 0) ?? I) === F) return;
		let n = this._$AH, r = e === I && n !== I || e.capture !== n.capture || e.once !== n.once || e.passive !== n.passive, i = e !== I && (n === I || r);
		r && this.element.removeEventListener(this.name, this, n), i && this.element.addEventListener(this.name, this, e), this._$AH = e;
	}
	handleEvent(e) {
		typeof this._$AH == "function" ? this._$AH.call(this.options?.host ?? this.element, e) : this._$AH.handleEvent(e);
	}
}, ge = class {
	constructor(e, t, n) {
		this.element = e, this.type = 6, this._$AN = void 0, this._$AM = t, this.options = n;
	}
	get _$AU() {
		return this._$AM._$AU;
	}
	_$AI(e) {
		V(this, e);
	}
}, _e = y.litHtmlPolyfillSupport;
_e?.(B, H), (y.litHtmlVersions ??= []).push("3.3.3");
var ve = (e, t, n) => {
	let r = n?.renderBefore ?? t, i = r._$litPart$;
	if (i === void 0) {
		let e = n?.renderBefore ?? null;
		r._$litPart$ = i = new H(t.insertBefore(E(), e), e, void 0, n ?? {});
	}
	return i._$AI(e), i;
}, W = globalThis, G = class extends v {
	constructor() {
		super(...arguments), this.renderOptions = { host: this }, this._$Do = void 0;
	}
	createRenderRoot() {
		let e = super.createRenderRoot();
		return this.renderOptions.renderBefore ??= e.firstChild, e;
	}
	update(e) {
		let t = this.render();
		this.hasUpdated || (this.renderOptions.isConnected = this.isConnected), super.update(e), this._$Do = ve(t, this.renderRoot, this.renderOptions);
	}
	connectedCallback() {
		super.connectedCallback(), this._$Do?.setConnected(!0);
	}
	disconnectedCallback() {
		super.disconnectedCallback(), this._$Do?.setConnected(!1);
	}
	render() {
		return F;
	}
};
G._$litElement$ = !0, G.finalized = !0, W.litElementHydrateSupport?.({ LitElement: G });
var ye = W.litElementPolyfillSupport;
ye?.({ LitElement: G }), (W.litElementVersions ??= []).push("4.2.2");
// node_modules/@lit/reactive-element/decorators/custom-element.js
var be = (e) => (t, n) => {
	n === void 0 ? customElements.define(e, t) : n.addInitializer(() => {
		customElements.define(e, t);
	});
}, xe = {
	attribute: !0,
	type: String,
	converter: h,
	reflect: !1,
	hasChanged: g
}, Se = (e = xe, t, n) => {
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
function K(e) {
	return (t, n) => typeof n == "object" ? Se(e, t, n) : ((e, t, n) => {
		let r = t.hasOwnProperty(n);
		return t.constructor.createProperty(n, e), r ? Object.getOwnPropertyDescriptor(t, n) : void 0;
	})(e, t, n);
}
// node_modules/@lit/reactive-element/decorators/state.js
function q(e) {
	return K({
		...e,
		state: !0,
		attribute: !1
	});
}
// src/format.ts
var J = "−";
function Y(e, t, n) {
	return new Intl.NumberFormat(t, {
		minimumFractionDigits: n,
		maximumFractionDigits: n
	}).format(e);
}
function Ce(e, t) {
	let n = new Intl.NumberFormat(t, {
		style: "currency",
		currency: "EUR",
		minimumFractionDigits: 2,
		maximumFractionDigits: 2
	}).format(Math.abs(e));
	return e < 0 ? J + n : n;
}
function we(e, t) {
	let n = Math.abs(e);
	return n >= 1e3 ? `${Y(n / 1e3, t, 2)} kW` : `${Y(Math.round(n / 10) * 10, t, 0)} W`;
}
function Te(e, t) {
	return (e > 0 ? "+" : e < 0 ? J : "") + we(e, t);
}
function X(e, t, n = 1) {
	return `${Y(e, t, n)} kWh`;
}
function Ee(e, t) {
	return `${Y(Math.round(e), t, 0)} %`;
}
function Z(e, t, n) {
	return new Intl.DateTimeFormat(t, {
		hour: "2-digit",
		minute: "2-digit",
		hour12: !1,
		timeZone: n
	}).format(new Date(e));
}
function De(e, t) {
	return Math.max(0, Math.round((new Date(e).getTime() - t) / 6e4));
}
function Oe(e, t, n) {
	let r = new Intl.DateTimeFormat("en-CA", {
		year: "numeric",
		month: "2-digit",
		day: "2-digit",
		timeZone: n
	});
	return r.format(new Date(e)) === r.format(new Date(t));
}
// src/i18n.ts
var ke = {
	nl: {
		menu: {
			label: "Hoofdmenu",
			plan: "Plan",
			sets: "Sets",
			battery: "Accu",
			settings: "Instellingen",
			diagnostics: "Diagnose"
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
		}
	},
	en: {
		menu: {
			label: "Main menu",
			plan: "Plan",
			sets: "Sets",
			battery: "Battery",
			settings: "Settings",
			diagnostics: "Diagnostics"
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
		}
	}
};
function Ae(e) {
	return e?.toLowerCase().startsWith("nl") ? "nl" : "en";
}
function je(e, t, n = {}) {
	let r = (e) => {
		let n = e;
		for (let e of t.split(".")) {
			if (typeof n != "object" || !n) return;
			n = n[e];
		}
		return typeof n == "string" ? n : void 0;
	};
	return (r(ke[e]) ?? r(ke.en) ?? t).replace(/\{(\w+)\}/g, (e, t) => t in n ? String(n[t]) : e);
}
// src/theme.ts
var Me = o`
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
    --z-warn-bg: #fdebd5;
    --z-warn-text: #5c3300;
    --z-info-bg: #eef3fb;
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
    --z-warn-bg: #3a2a14;
    --z-warn-text: #f7d4a8;
    --z-info-bg: #1b2433;
  }
`;
function Ne(e) {
	switch (e) {
		case "charge": return "var(--z-charge)";
		case "deliver": return "var(--z-deliver)";
		case "export": return "var(--z-export)";
		case "hold": return "repeating-linear-gradient(45deg, var(--z-hold-a) 0 3px, var(--z-hold-b) 3px 6px)";
		default: return "var(--z-muted)";
	}
}
// \0@oxc-project+runtime@0.156.0/helpers/esm/decorate.js
function Q(e, t, n, r) {
	var i = arguments.length, a = i < 3 ? t : r === null ? r = Object.getOwnPropertyDescriptor(t, n) : r, o;
	if (typeof Reflect == "object" && typeof Reflect.decorate == "function") a = Reflect.decorate(e, t, n, r);
	else for (var s = e.length - 1; s >= 0; s--) (o = e[s]) && (a = (i < 3 ? o(a) : i > 3 ? o(t, n, a) : o(t, n)) || a);
	return i > 3 && a && Object.defineProperty(t, n, a), a;
}
// src/zephyr-panel.ts
var Pe = "/zephyr_static", Fe = [
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
function Ie(e) {
	let t = "zephyr-fonts";
	if (document.getElementById(t)) return;
	let n = document.createElement("style");
	n.id = t, n.textContent = Fe.map(([t, n, r]) => `@font-face{font-family:"${t}";font-style:normal;font-weight:${n};font-display:swap;src:url("${e}/fonts/${r}") format("woff2");}`).join("\n"), document.head.appendChild(n);
}
var $ = class extends G {
	constructor(...e) {
		super(...e), this.narrow = !1, this.status = "loading", this.view = "plan", this.clockMs = Date.now(), this.subscribing = !1, this.onReady = () => {
			this.status = "loading", this.subscribe();
		}, this.onDisconnected = () => {
			this.unsubscribe = void 0, this.status = "disconnected";
		};
	}
	get base() {
		return this.panel?.config?.static ?? Pe;
	}
	get uiLang() {
		return Ae(this.hass?.locale?.language ?? this.hass?.language);
	}
	get locale() {
		return this.hass?.locale?.language ?? this.hass?.language ?? "en";
	}
	get timeZone() {
		return this.hass?.config.time_zone ?? Intl.DateTimeFormat().resolvedOptions().timeZone;
	}
	tr(e, t = {}) {
		return je(this.uiLang, e, t);
	}
	connectedCallback() {
		super.connectedCallback(), Ie(this.base), this.clockTimer = window.setInterval(() => this.clockMs = Date.now(), 3e4), this.hass && this.subscribe();
	}
	disconnectedCallback() {
		super.disconnectedCallback(), window.clearInterval(this.clockTimer), window.clearTimeout(this.retryTimer), this.watch(void 0), this.stop();
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
	retry(e) {
		window.clearTimeout(this.retryTimer), this.retryTimer = window.setTimeout(() => void this.subscribe(), e);
	}
	onEvent(e) {
		e.type === "now" ? (this.now = e.data, this.status = "ok", this.clockMs = Date.now()) : e.type === "unloaded" && (this.unsubscribe = void 0, this.status = "reloading", this.retry(3e3));
	}
	render() {
		return P`
      <div class="page">
        ${this.renderHeader()}
        <main>${this.renderBanner()} ${this.view === "plan" ? this.renderPlan() : this.renderComing()}</main>
      </div>
    `;
	}
	renderHeader() {
		let e = this.now, t = [
			["plan", "menu.plan"],
			["sets", (e?.sets_total ?? 1) <= 1 ? "menu.battery" : "menu.sets"],
			["settings", "menu.settings"],
			["diagnostics", "menu.diagnostics"]
		];
		return P`
      <header>
        <div class="brand">
          <img src="${this.base}/logo.png" alt="" width="32" height="32" />
          <span>ZEPHYR</span>
        </div>
        <nav aria-label=${this.tr("menu.label")}>
          ${t.map(([e, t]) => P`<button
                type="button"
                class=${this.view === e ? "tab active" : "tab"}
                aria-current=${this.view === e ? "page" : "false"}
                @click=${() => this.view = e}
              >
                ${this.tr(t)}
              </button>`)}
        </nav>
        <div class="meta">
          ${e ? P`<span class="chip">${this.tr(`mode.${e.mode}`)}</span>
                <span class=${e.live ? "chip live" : "chip"} title=${this.tr(e.live ? "header.live_title" : "header.shadow_title")}
                  >${this.tr(e.live ? "header.live" : "header.shadow")}</span
                >` : I}
          <span class="time">${Z(new Date(this.clockMs).toISOString(), this.locale, this.timeZone)}</span>
        </div>
      </header>
    `;
	}
	renderBanner() {
		switch (this.status) {
			case "not_loaded": return P`<div class="banner" role="status">${this.tr("status.not_loaded")}</div>`;
			case "reloading": return P`<div class="banner info" role="status">${this.tr("status.reloading")}</div>`;
			case "disconnected": return P`<div class="banner" role="status">
          ${this.tr("status.disconnected", { time: this.now ? Z(this.now.updated_at, this.locale, this.timeZone) : "–" })}
        </div>`;
			default: return I;
		}
	}
	renderComing() {
		return P`<section class="card coming">${this.tr("status.coming")}</section>`;
	}
	renderPlan() {
		let e = this.now;
		return e ? P`<section class="cards ${this.status === "ok" ? "" : "stale"}" aria-label=${this.tr("now.title")}>
      ${this.renderNow(e)} ${this.renderBattery(e)} ${this.renderNext(e)}
    </section>` : P`<section class="cards" aria-busy="true">
        ${[
			0,
			1,
			2
		].map(() => P`<div class="card skeleton" aria-hidden="true"></div>`)}
      </section>`;
	}
	renderNow(e) {
		let t = e.action ?? "standby", n = e.battery_w !== null && Math.abs(e.battery_w) >= 10 ? ` · ${we(e.battery_w, this.locale)}` : "";
		return P`<article class="card">
      <div class="label"><span class="dot" style="background:${Ne(t)}"></span>${this.tr("now.title")}</div>
      <div class="big">${e.action ? this.tr(`action.${t}`) + n : this.tr("now.waiting")}</div>
      ${e.reason ? P`<p class="text">${e.reason[this.uiLang]}</p>` : I}
      <div class="foot">
        ${e.grid_w === null ? I : P`<span>${this.tr("now.grid", { value: Te(e.grid_w, this.locale) })}</span>`}
        ${e.live ? I : P`<span>${this.tr("now.shadow_note")}</span>`}
      </div>
    </article>`;
	}
	renderBattery(e) {
		if (e.soc === null) return P`<article class="card">
        <div class="label">${this.tr("battery.title")}</div>
        <p class="text">${this.tr("battery.unknown")}</p>
      </article>`;
		let t = Math.max(0, Math.min(100, e.soc)), n = Math.max(0, e.buffer_pct), r = e.sets_total <= 1 ? e.sets_online >= 1 ? this.tr("battery.set") : this.tr("battery.set_offline") : this.tr("battery.sets", {
			online: e.sets_online,
			total: e.sets_total
		});
		return P`<article class="card">
      <div class="label">${this.tr("battery.title")}</div>
      <div class="big-row">
        <span class="big">${Ee(t, this.locale)}</span>
        ${e.energy_kwh !== null && e.capacity_kwh !== null ? P`<span class="muted"
              >${this.tr("battery.of", {
			energy: X(e.energy_kwh, this.locale),
			capacity: X(e.capacity_kwh, this.locale)
		})}</span
            >` : I}
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
        ${n > 0 ? P`<div class="buffer" style="left:${e.min_soc}%;width:${Math.min(n, 100 - e.min_soc)}%"></div>` : I}
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
		let t = e.plan, n = (e = "") => P`<div class="label">
        <span class="dot" style="background:${Ne(t?.next?.action)}"></span>${this.tr("next.title")}${e}
      </div>`;
		if (!e.price_entity) return P`<article class="card">${n()}<p class="text">${this.tr("next.no_price_source")}</p></article>`;
		if (!t) return P`<article class="card">${n()}<p class="text">${this.tr("status.loading")}</p></article>`;
		if (t.state === "no_prices") {
			let e = t.no_prices_since ?? t.calculated_at;
			return P`<article class="card">
        ${n()}
        <p class="text warn">${this.tr("next.no_prices", { time: e ? Z(e, this.locale, this.timeZone) : "–" })}</p>
      </article>`;
		}
		let r = t.next, i = t.price_now ? P`<div class="foot"><span>${this.tr("next.price_now", { price: Ce(t.price_now.import, this.locale) })}</span></div>` : I;
		if (!r) return P`<article class="card">${n()}<p class="text">${this.tr("next.none")}</p>${i}</article>`;
		let a = De(r.start, this.clockMs), o = a <= 0 ? this.tr("next.now") : this.tr("next.in", { time: a >= 60 ? this.tr("next.hours", {
			h: Math.floor(a / 60),
			m: a % 60
		}) : this.tr("next.minutes", { m: a }) }), s = Z(r.start, this.locale, this.timeZone), c = this.tr(`action.${r.action}`), l = Oe(r.start, this.clockMs, this.timeZone) ? this.tr("next.at", {
			time: s,
			action: c
		}) : this.tr("next.tomorrow", {
			time: s,
			action: c
		});
		return P`<article class="card">
      ${n(` · ${o}`)}
      <div class="big">${l}</div>
      <p class="text">${this.detail(t)}</p>
      ${r.indicative ? P`<p class="text muted">${this.tr("next.indicative")}</p>` : I} ${i}
    </article>`;
	}
	detail(e) {
		let t = e.next;
		if (!t) return "";
		let n = {
			kwh: X(t.kwh, this.locale),
			price: Ce(t.price, this.locale)
		};
		return this.tr(`next.${t.action}`, n);
	}
	static {
		this.styles = [Me, o`
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
      .cards.stale {
        opacity: 0.6;
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
Q([K({ attribute: !1 })], $.prototype, "hass", void 0), Q([K({ type: Boolean })], $.prototype, "narrow", void 0), Q([K({ attribute: !1 })], $.prototype, "panel", void 0), Q([q()], $.prototype, "now", void 0), Q([q()], $.prototype, "status", void 0), Q([q()], $.prototype, "view", void 0), Q([q()], $.prototype, "clockMs", void 0), $ = Q([be("zephyr-panel")], $);
export { $ as ZephyrPanel };
