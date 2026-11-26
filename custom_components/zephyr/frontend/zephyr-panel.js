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
})(e) : e, { is: l, defineProperty: u, getOwnPropertyDescriptor: d, getOwnPropertyNames: f, getOwnPropertySymbols: ee, getPrototypeOf: te } = Object, p = globalThis, ne = p.trustedTypes, re = ne ? ne.emptyScript : "", ie = p.reactiveElementPolyfillSupport, m = (e, t) => e, h = {
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
}, g = (e, t) => !l(e, t), ae = {
	attribute: !0,
	type: String,
	converter: h,
	reflect: !1,
	useDefault: !1,
	hasChanged: g
};
Symbol.metadata ??= Symbol("metadata"), p.litPropertyMetadata ??= /* @__PURE__ */ new WeakMap();
var _ = class extends HTMLElement {
	static addInitializer(e) {
		this._$Ei(), (this.l ??= []).push(e);
	}
	static get observedAttributes() {
		return this.finalize(), this._$Eh && [...this._$Eh.keys()];
	}
	static createProperty(e, t = ae) {
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
		return this.elementProperties.get(e) ?? ae;
	}
	static _$Ei() {
		if (this.hasOwnProperty(m("elementProperties"))) return;
		let e = te(this);
		e.finalize(), e.l !== void 0 && (this.l = [...e.l]), this.elementProperties = new Map(e.elementProperties);
	}
	static finalize() {
		if (this.hasOwnProperty(m("finalized"))) return;
		if (this.finalized = !0, this._$Ei(), this.hasOwnProperty(m("properties"))) {
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
_.elementStyles = [], _.shadowRootOptions = { mode: "open" }, _[m("elementProperties")] = /* @__PURE__ */ new Map(), _[m("finalized")] = /* @__PURE__ */ new Map(), ie?.({ ReactiveElement: _ }), (p.reactiveElementVersions ??= []).push("2.1.2");
// node_modules/lit-html/lit-html.js
var oe = globalThis, se = (e) => e, v = oe.trustedTypes, ce = v ? v.createPolicy("lit-html", { createHTML: (e) => e }) : void 0, le = "$lit$", y = `lit$${Math.random().toFixed(9).slice(2)}$`, ue = "?" + y, de = `<${ue}>`, b = document, x = () => b.createComment(""), S = (e) => e === null || typeof e != "object" && typeof e != "function", fe = Array.isArray, pe = (e) => fe(e) || typeof e?.[Symbol.iterator] == "function", C = "[ 	\n\f\r]", w = /<(?:(!--|\/[^a-zA-Z])|(\/?[a-zA-Z][^>\s]*)|(\/?$))/g, me = /-->/g, he = />/g, T = RegExp(`>|${C}(?:([^\\s"'>=/]+)(${C}*=${C}*(?:[^ \t\n\f\r"'\`<>=]|("|')|))|$)`, "g"), ge = /'/g, _e = /"/g, ve = /^(?:script|style|textarea|title)$/i, ye = (e) => (t, ...n) => ({
	_$litType$: e,
	strings: t,
	values: n
}), E = ye(1), be = ye(2), D = Symbol.for("lit-noChange"), O = Symbol.for("lit-nothing"), xe = /* @__PURE__ */ new WeakMap(), k = b.createTreeWalker(b, 129);
function Se(e, t) {
	if (!fe(e) || !e.hasOwnProperty("raw")) throw Error("invalid template strings array");
	return ce === void 0 ? t : ce.createHTML(t);
}
var Ce = (e, t) => {
	let n = e.length - 1, r = [], i, a = t === 2 ? "<svg>" : t === 3 ? "<math>" : "", o = w;
	for (let t = 0; t < n; t++) {
		let n = e[t], s, c, l = -1, u = 0;
		for (; u < n.length && (o.lastIndex = u, c = o.exec(n), c !== null);) u = o.lastIndex, o === w ? c[1] === "!--" ? o = me : c[1] === void 0 ? c[2] === void 0 ? c[3] !== void 0 && (o = T) : (ve.test(c[2]) && (i = RegExp("</" + c[2], "g")), o = T) : o = he : o === T ? c[0] === ">" ? (o = i ?? w, l = -1) : c[1] === void 0 ? l = -2 : (l = o.lastIndex - c[2].length, s = c[1], o = c[3] === void 0 ? T : c[3] === "\"" ? _e : ge) : o === _e || o === ge ? o = T : o === me || o === he ? o = w : (o = T, i = void 0);
		let d = o === T && e[t + 1].startsWith("/>") ? " " : "";
		a += o === w ? n + de : l >= 0 ? (r.push(s), n.slice(0, l) + le + n.slice(l) + y + d) : n + y + (l === -2 ? t : d);
	}
	return [Se(e, a + (e[n] || "<?>") + (t === 2 ? "</svg>" : t === 3 ? "</math>" : "")), r];
}, we = class e {
	constructor({ strings: t, _$litType$: n }, r) {
		let i;
		this.parts = [];
		let a = 0, o = 0, s = t.length - 1, c = this.parts, [l, u] = Ce(t, n);
		if (this.el = e.createElement(l, r), k.currentNode = this.el.content, n === 2 || n === 3) {
			let e = this.el.content.firstChild;
			e.replaceWith(...e.childNodes);
		}
		for (; (i = k.nextNode()) !== null && c.length < s;) {
			if (i.nodeType === 1) {
				if (i.hasAttributes()) for (let e of i.getAttributeNames()) if (e.endsWith(le)) {
					let t = u[o++], n = i.getAttribute(e).split(y), r = /([.?@])?(.*)/.exec(t);
					c.push({
						type: 1,
						index: a,
						name: r[2],
						strings: n,
						ctor: r[1] === "." ? De : r[1] === "?" ? Oe : r[1] === "@" ? ke : j
					}), i.removeAttribute(e);
				} else e.startsWith(y) && (c.push({
					type: 6,
					index: a
				}), i.removeAttribute(e));
				if (ve.test(i.tagName)) {
					let e = i.textContent.split(y), t = e.length - 1;
					if (t > 0) {
						i.textContent = v ? v.emptyScript : "";
						for (let n = 0; n < t; n++) i.append(e[n], x()), k.nextNode(), c.push({
							type: 2,
							index: ++a
						});
						i.append(e[t], x());
					}
				}
			} else if (i.nodeType === 8) {
				if (i.data === ue) c.push({
					type: 2,
					index: a
				});
				else {
					let e = -1;
					for (; (e = i.data.indexOf(y, e + 1)) !== -1;) c.push({
						type: 7,
						index: a
					}), e += y.length - 1;
				}
			}
			a++;
		}
	}
	static createElement(e, t) {
		let n = b.createElement("template");
		return n.innerHTML = e, n;
	}
};
function A(e, t, n = e, r) {
	if (t === D) return t;
	let i = r === void 0 ? n._$Cl : n._$Co?.[r], a = S(t) ? void 0 : t._$litDirective$;
	return i?.constructor !== a && (i?._$AO?.(!1), a === void 0 ? i = void 0 : (i = new a(e), i._$AT(e, n, r)), r === void 0 ? n._$Cl = i : (n._$Co ??= [])[r] = i), i !== void 0 && (t = A(e, i._$AS(e, t.values), i, r)), t;
}
var Te = class {
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
		let { el: { content: t }, parts: n } = this._$AD, r = (e?.creationScope ?? b).importNode(t, !0);
		k.currentNode = r;
		let i = k.nextNode(), a = 0, o = 0, s = n[0];
		for (; s !== void 0;) {
			if (a === s.index) {
				let t;
				s.type === 2 ? t = new Ee(i, i.nextSibling, this, e) : s.type === 1 ? t = new s.ctor(i, s.name, s.strings, this, e) : s.type === 6 && (t = new Ae(i, this, e)), this._$AV.push(t), s = n[++o];
			}
			a !== s?.index && (i = k.nextNode(), a++);
		}
		return k.currentNode = b, r;
	}
	p(e) {
		let t = 0;
		for (let n of this._$AV) n !== void 0 && (n.strings === void 0 ? n._$AI(e[t]) : (n._$AI(e, n, t), t += n.strings.length - 2)), t++;
	}
}, Ee = class e {
	get _$AU() {
		return this._$AM?._$AU ?? this._$Cv;
	}
	constructor(e, t, n, r) {
		this.type = 2, this._$AH = O, this._$AN = void 0, this._$AA = e, this._$AB = t, this._$AM = n, this.options = r, this._$Cv = r?.isConnected ?? !0;
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
		e = A(this, e, t), S(e) ? e === O || e == null || e === "" ? (this._$AH !== O && this._$AR(), this._$AH = O) : e !== this._$AH && e !== D && this._(e) : e._$litType$ === void 0 ? e.nodeType === void 0 ? pe(e) ? this.k(e) : this._(e) : this.T(e) : this.$(e);
	}
	O(e) {
		return this._$AA.parentNode.insertBefore(e, this._$AB);
	}
	T(e) {
		this._$AH !== e && (this._$AR(), this._$AH = this.O(e));
	}
	_(e) {
		this._$AH !== O && S(this._$AH) ? this._$AA.nextSibling.data = e : this.T(b.createTextNode(e)), this._$AH = e;
	}
	$(e) {
		let { values: t, _$litType$: n } = e, r = typeof n == "number" ? this._$AC(e) : (n.el === void 0 && (n.el = we.createElement(Se(n.h, n.h[0]), this.options)), n);
		if (this._$AH?._$AD === r) this._$AH.p(t);
		else {
			let e = new Te(r, this), n = e.u(this.options);
			e.p(t), this.T(n), this._$AH = e;
		}
	}
	_$AC(e) {
		let t = xe.get(e.strings);
		return t === void 0 && xe.set(e.strings, t = new we(e)), t;
	}
	k(t) {
		fe(this._$AH) || (this._$AH = [], this._$AR());
		let n = this._$AH, r, i = 0;
		for (let a of t) i === n.length ? n.push(r = new e(this.O(x()), this.O(x()), this, this.options)) : r = n[i], r._$AI(a), i++;
		i < n.length && (this._$AR(r && r._$AB.nextSibling, i), n.length = i);
	}
	_$AR(e = this._$AA.nextSibling, t) {
		for (this._$AP?.(!1, !0, t); e !== this._$AB;) {
			let t = se(e).nextSibling;
			se(e).remove(), e = t;
		}
	}
	setConnected(e) {
		this._$AM === void 0 && (this._$Cv = e, this._$AP?.(e));
	}
}, j = class {
	get tagName() {
		return this.element.tagName;
	}
	get _$AU() {
		return this._$AM._$AU;
	}
	constructor(e, t, n, r, i) {
		this.type = 1, this._$AH = O, this._$AN = void 0, this.element = e, this.name = t, this._$AM = r, this.options = i, n.length > 2 || n[0] !== "" || n[1] !== "" ? (this._$AH = Array(n.length - 1).fill(/* @__PURE__ */ new String()), this.strings = n) : this._$AH = O;
	}
	_$AI(e, t = this, n, r) {
		let i = this.strings, a = !1;
		if (i === void 0) e = A(this, e, t, 0), a = !S(e) || e !== this._$AH && e !== D, a && (this._$AH = e);
		else {
			let r = e, o, s;
			for (e = i[0], o = 0; o < i.length - 1; o++) s = A(this, r[n + o], t, o), s === D && (s = this._$AH[o]), a ||= !S(s) || s !== this._$AH[o], s === O ? e = O : e !== O && (e += (s ?? "") + i[o + 1]), this._$AH[o] = s;
		}
		a && !r && this.j(e);
	}
	j(e) {
		e === O ? this.element.removeAttribute(this.name) : this.element.setAttribute(this.name, e ?? "");
	}
}, De = class extends j {
	constructor() {
		super(...arguments), this.type = 3;
	}
	j(e) {
		this.element[this.name] = e === O ? void 0 : e;
	}
}, Oe = class extends j {
	constructor() {
		super(...arguments), this.type = 4;
	}
	j(e) {
		this.element.toggleAttribute(this.name, !!e && e !== O);
	}
}, ke = class extends j {
	constructor(e, t, n, r, i) {
		super(e, t, n, r, i), this.type = 5;
	}
	_$AI(e, t = this) {
		if ((e = A(this, e, t, 0) ?? O) === D) return;
		let n = this._$AH, r = e === O && n !== O || e.capture !== n.capture || e.once !== n.once || e.passive !== n.passive, i = e !== O && (n === O || r);
		r && this.element.removeEventListener(this.name, this, n), i && this.element.addEventListener(this.name, this, e), this._$AH = e;
	}
	handleEvent(e) {
		typeof this._$AH == "function" ? this._$AH.call(this.options?.host ?? this.element, e) : this._$AH.handleEvent(e);
	}
}, Ae = class {
	constructor(e, t, n) {
		this.element = e, this.type = 6, this._$AN = void 0, this._$AM = t, this.options = n;
	}
	get _$AU() {
		return this._$AM._$AU;
	}
	_$AI(e) {
		A(this, e);
	}
}, je = oe.litHtmlPolyfillSupport;
je?.(we, Ee), (oe.litHtmlVersions ??= []).push("3.3.3");
var Me = (e, t, n) => {
	let r = n?.renderBefore ?? t, i = r._$litPart$;
	if (i === void 0) {
		let e = n?.renderBefore ?? null;
		r._$litPart$ = i = new Ee(t.insertBefore(x(), e), e, void 0, n ?? {});
	}
	return i._$AI(e), i;
}, Ne = globalThis, M = class extends _ {
	constructor() {
		super(...arguments), this.renderOptions = { host: this }, this._$Do = void 0;
	}
	createRenderRoot() {
		let e = super.createRenderRoot();
		return this.renderOptions.renderBefore ??= e.firstChild, e;
	}
	update(e) {
		let t = this.render();
		this.hasUpdated || (this.renderOptions.isConnected = this.isConnected), super.update(e), this._$Do = Me(t, this.renderRoot, this.renderOptions);
	}
	connectedCallback() {
		super.connectedCallback(), this._$Do?.setConnected(!0);
	}
	disconnectedCallback() {
		super.disconnectedCallback(), this._$Do?.setConnected(!1);
	}
	render() {
		return D;
	}
};
M._$litElement$ = !0, M.finalized = !0, Ne.litElementHydrateSupport?.({ LitElement: M });
var Pe = Ne.litElementPolyfillSupport;
Pe?.({ LitElement: M }), (Ne.litElementVersions ??= []).push("4.2.2");
// node_modules/@lit/reactive-element/decorators/custom-element.js
var N = (e) => (t, n) => {
	n === void 0 ? customElements.define(e, t) : n.addInitializer(() => {
		customElements.define(e, t);
	});
}, Fe = {
	attribute: !0,
	type: String,
	converter: h,
	reflect: !1,
	hasChanged: g
}, Ie = (e = Fe, t, n) => {
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
function P(e) {
	return (t, n) => typeof n == "object" ? Ie(e, t, n) : ((e, t, n) => {
		let r = t.hasOwnProperty(n);
		return t.constructor.createProperty(n, e), r ? Object.getOwnPropertyDescriptor(t, n) : void 0;
	})(e, t, n);
}
// node_modules/@lit/reactive-element/decorators/state.js
function F(e) {
	return P({
		...e,
		state: !0,
		attribute: !1
	});
}
// src/format.ts
var Le = "−";
function I(e, t, n) {
	return new Intl.NumberFormat(t, {
		minimumFractionDigits: n,
		maximumFractionDigits: n
	}).format(e);
}
function L(e, t) {
	let n = new Intl.NumberFormat(t, {
		style: "currency",
		currency: "EUR",
		minimumFractionDigits: 2,
		maximumFractionDigits: 2
	}).format(Math.abs(e));
	return e < 0 ? Le + n : n;
}
function Re(e, t) {
	let n = Math.abs(e);
	return n >= 1e3 ? `${I(n / 1e3, t, 2)} kW` : `${I(Math.round(n / 10) * 10, t, 0)} W`;
}
function R(e, t) {
	return (e > 0 ? "+" : e < 0 ? Le : "") + Re(e, t);
}
function z(e, t, n = 1) {
	return `${I(e, t, n)} kWh`;
}
function B(e, t) {
	return `${I(Math.round(e), t, 0)} %`;
}
function V(e, t, n) {
	return new Intl.DateTimeFormat(t, {
		hour: "2-digit",
		minute: "2-digit",
		hour12: !1,
		timeZone: n
	}).format(new Date(e));
}
function H(e, t, n) {
	return new Intl.DateTimeFormat(t, {
		weekday: "short",
		day: "numeric",
		month: "short",
		timeZone: n
	}).format(new Date(e));
}
function ze(e, t) {
	return Math.max(0, Math.round((new Date(e).getTime() - t) / 6e4));
}
function U(e, t, n) {
	let r = new Intl.DateTimeFormat("en-CA", {
		year: "numeric",
		month: "2-digit",
		day: "2-digit",
		timeZone: n
	});
	return r.format(new Date(e)) === r.format(new Date(t));
}
// src/i18n.ts
var Be = {
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
			tip_energy: "Zon {solar} · verbruik {load}",
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
			tip_energy_past: "Zon {solar} · huis {load}"
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
			indicative: "indicatief"
		},
		why: {
			title: "Waarom dit plan",
			cheapest: "Goedkoopst laden: {time} (gemiddeld {price}).",
			peak: "Duurste moment: {time} ({price}). Daar levert de accu het meeste op.",
			no_charge: "Laden uit het net is in deze periode niet goedkoper dan wachten; de accu gebruikt wat er is.",
			indicative: "Morgen is nog indicatief; de prijzen komen meestal rond 13:00 en dan rekent het plan opnieuw."
		},
		sets: {
			none: "Nog geen set gevonden.",
			summary: "Samenvatting",
			batteries: "Accu's",
			all_online: "{n} · alle online",
			some_offline: "{n} · niet alle online",
			soc_spread: "SOC-spreiding",
			warmest: "Warmste accu",
			largest_delta: "Grootste celverschil",
			in_short: "In het kort:",
			line_ok: "alles in orde.",
			line_watch: "{pack} loopt iets achter ({mv} mV celverschil); dat trekt meestal bij na de volgende volle lading.",
			line_high: "het celverschil van {pack} is hoog ({mv} mV). Laat de set een keer helemaal vol laden, zodat hij de cellen kan balanceren.",
			line_edge: "alles in orde. Bij een (bijna) volle of lege accu lopen de celspanningen uit elkaar; dat is normaal en wordt niet beoordeeld (*).",
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
				watch: "Let op",
				high: "Hoog",
				edge: "niet beoordeeld",
				null: "–"
			},
			cell_note: "Celverschil = hoogste min laagste celspanning in de accu (de set meldt per 10 mV). Alleen beoordeeld tussen 20 en 90 % SOC: tot 30 mV is goed, tot 80 mV let op, daarboven hoog. Bij een (bijna) volle of lege accu lopen de cellen vanzelf uit elkaar. De set balanceert de cellen als hij vol is.",
			balance_title: "Celverschil per dag · afgelopen 7 dagen",
			balance_note: "Hoogste waarde tussen 20 en 90 % SOC · ▲ = dag met 100 %",
			no_judged: "Geen meting tussen 20 en 90 % SOC",
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
			}
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
			tip_energy: "Solar {solar} · consumption {load}",
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
			tip_energy_past: "Solar {solar} · house {load}"
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
			indicative: "indicative"
		},
		why: {
			title: "Why this plan",
			cheapest: "Cheapest charging: {time} ({price} on average).",
			peak: "Most expensive moment: {time} ({price}). That is where the battery saves the most.",
			no_charge: "Charging from the grid is not cheaper than waiting in this period; the battery uses what it has.",
			indicative: "Tomorrow is still indicative; prices usually come around 13:00 and the plan is then recalculated."
		},
		sets: {
			none: "No set found yet.",
			summary: "Summary",
			batteries: "Batteries",
			all_online: "{n} · all online",
			some_offline: "{n} · not all online",
			soc_spread: "SOC spread",
			warmest: "Warmest battery",
			largest_delta: "Largest cell difference",
			in_short: "In short:",
			line_ok: "all fine.",
			line_watch: "{pack} lags a little ({mv} mV cell difference); that usually evens out after the next full charge.",
			line_high: "the cell difference of {pack} is high ({mv} mV). Let the set charge fully once so it can balance the cells.",
			line_edge: "all fine. Near full or empty the cell voltages spread out; that is normal and not judged (*).",
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
				watch: "Watch",
				high: "High",
				edge: "not judged",
				null: "–"
			},
			cell_note: "Cell difference = highest minus lowest cell voltage in the battery (the set reports per 10 mV). Only judged between 20 and 90 % SOC: up to 30 mV is good, up to 80 mV watch, above that high. Near full or empty the cells spread out by themselves. The set balances the cells when it is full.",
			balance_title: "Cell difference per day · last 7 days",
			balance_note: "Highest value between 20 and 90 % SOC · ▲ = day with 100 %",
			no_judged: "No reading between 20 and 90 % SOC",
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
			}
		}
	}
};
function Ve(e) {
	return e?.toLowerCase().startsWith("nl") ? "nl" : "en";
}
function W(e, t, n = {}) {
	let r = (e) => {
		let n = e;
		for (let e of t.split(".")) {
			if (typeof n != "object" || !n) return;
			n = n[e];
		}
		return typeof n == "string" ? n : void 0;
	};
	return (r(Be[e]) ?? r(Be.en) ?? t).replace(/\{(\w+)\}/g, (e, t) => t in n ? String(n[t]) : e);
}
// src/plan.ts
var He = (e, t) => new Intl.DateTimeFormat("en-CA", {
	year: "numeric",
	month: "2-digit",
	day: "2-digit",
	timeZone: t
}).format(new Date(e));
function Ue(e, t) {
	let n = [];
	for (let r of e) {
		let e = He(r.start, t);
		n[n.length - 1] !== e && n.push(e);
	}
	return n;
}
function We(e, t, n) {
	if (t === "both") return e;
	let r = Ue(e, n)[t === "today" ? 0 : 1];
	return r ? e.filter((e) => He(e.start, n) === r) : [];
}
function G(e, t, n) {
	let r = Ue(e, n)[t];
	return r ? e.filter((e) => He(e.start, n) === r) : [];
}
function K(e) {
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
function q(e) {
	return e.findIndex((e) => !e.past);
}
function Ge(e) {
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
function Ke(e) {
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
function qe(e, t) {
	let n = t.hi - t.lo, r = Math.min(e, 0), i = Math.max(e, 0);
	return {
		bottom: (r - t.lo) / n * 100,
		height: Math.max((i - r) / n * 100, .8)
	};
}
function Je(e, t, n) {
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
function Ye(e, t) {
	let n = q(e), r = [];
	return n >= 0 && t !== null && r.push(`${n},${(100 - t).toFixed(1)}`), e.forEach((e, t) => {
		!e.past && e.soc !== null && r.push(`${t + 1},${(100 - e.soc).toFixed(1)}`);
	}), r.join(" ");
}
function Xe(e, t) {
	let n = q(e), r = [], i = [];
	return e.forEach((e, t) => {
		e.past && (e.soc === null ? (i.length && r.push(i), i = []) : i.push(`${t + 1},${(100 - e.soc).toFixed(1)}`));
	}), i.length && (n >= 0 && t !== null && i[i.length - 1].startsWith(`${n},`) && i.push(`${n},${(100 - t).toFixed(1)}`), r.push(i)), r.filter((e) => e.length > 1).map((e) => e.join(" "));
}
function Ze(e, t) {
	let n = new Date(t).getTime();
	return e.filter((e) => new Date(e.end).getTime() > n);
}
// src/theme.ts
var Qe = o`
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
function J(e) {
	switch (e) {
		case "charge": return "var(--z-charge)";
		case "deliver": return "var(--z-deliver)";
		case "export": return "var(--z-export)";
		case "hold": return "repeating-linear-gradient(45deg, var(--z-hold-a) 0 3px, var(--z-hold-b) 3px 6px)";
		default: return "var(--z-muted)";
	}
}
// \0@oxc-project+runtime@0.156.0/helpers/esm/decorate.js
function Y(e, t, n, r) {
	var i = arguments.length, a = i < 3 ? t : r === null ? r = Object.getOwnPropertyDescriptor(t, n) : r, o;
	if (typeof Reflect == "object" && typeof Reflect.decorate == "function") a = Reflect.decorate(e, t, n, r);
	else for (var s = e.length - 1; s >= 0; s--) (o = e[s]) && (a = (i < 3 ? o(a) : i > 3 ? o(t, n, a) : o(t, n)) || a);
	return i > 3 && a && Object.defineProperty(t, n, a), a;
}
// src/prices-plan.ts
var $e = "zephyr.period", et = [
	["today", "plan.today"],
	["tomorrow", "plan.tomorrow"],
	["both", "plan.both"]
];
function tt() {
	try {
		let e = window.localStorage.getItem($e);
		return e === "tomorrow" || e === "both" ? e : "today";
	} catch {
		return "today";
	}
}
var X = class extends M {
	constructor(...e) {
		super(...e), this.uiLang = "en", this.locale = "en", this.timeZone = "UTC", this.narrow = !1, this.period = tt(), this.sel = null, this.scrolledFor = "";
	}
	tr(e, t = {}) {
		return W(this.uiLang, e, t);
	}
	pick(e) {
		this.period = e, this.sel = null, this.scrolledFor = "";
		try {
			window.localStorage.setItem($e, e);
		} catch {}
	}
	updated(e) {
		let t = this.renderRoot.querySelector(".scroll"), n = this.visible(), r = `${this.period}|${this.view?.now ?? ""}`;
		if (!t || t.scrollWidth <= t.clientWidth || this.scrolledFor === r) return;
		this.scrolledFor = r;
		let i = q(n);
		i > 0 && (t.scrollLeft = Math.max(0, i - 8) / n.length * t.scrollWidth);
	}
	visible() {
		return this.view ? We(this.view.quarters, this.period, this.timeZone) : [];
	}
	render() {
		let e = this.view;
		if (!e) return E`<section class="card"><div class="skeleton" aria-hidden="true"></div></section>`;
		let t = this.visible(), n = G(e.quarters, 0, this.timeZone), r = G(e.quarters, 1, this.timeZone), i = K(n), a = K(r), o = q(e.quarters), s = o >= 0 ? e.quarters[o] : void 0, c = this.period === "today" ? "plan.title_today" : this.period === "tomorrow" ? "plan.title_tomorrow" : "plan.title_both";
		return E`<section class="card" aria-label=${this.tr("plan.title")}>
      <div class="head">
        <h2>${this.tr("plan.title")} · ${this.tr(c)}</h2>
        <div class="tabs" role="group" aria-label=${this.tr("plan.period")}>
          ${et.map(([e, t]) => E`<button
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
          <span class="cap">${this.tr("plan.now", { time: s ? V(s.start, this.locale, this.timeZone) : "–" })}</span>
          <span class="value">${s?.buy == null ? "–" : L(s.buy, this.locale)}</span>
          <span class="sub">${this.tr("plan.per_kwh")}</span>
        </div>
        ${this.statCell(n, i, "plan.today")} ${this.statCell(r, a, "plan.tomorrow", !0)}
      </div>
      ${this.notes(e, a)} ${t.length ? this.chart(t) : E`<p class="empty">${this.tr("plan.no_quarters")}</p>`}
      ${this.legend()}
    </section>`;
	}
	statCell(e, t, n, r = !1) {
		let i = e.length ? H(e[0].start, this.locale, this.timeZone) : "";
		if (!t) return E`<div class="cell">
        <span class="cap">${this.tr(n)} · ${i}</span>
        <span class="value small">${this.tr("plan.unknown")}</span>
        <span class="sub">${r ? this.tr("plan.expected_at") : ""}</span>
      </div>`;
		let a = r && this.view?.tomorrow_known_at ? ` · ${this.tr("plan.known_at", { time: V(this.view.tomorrow_known_at, this.locale, this.timeZone) })}` : "";
		return E`<div class="cell">
      <span class="cap">${this.tr(n)} · ${i}</span>
      <span class="value">${L(t.min.buy, this.locale)} – ${L(t.max.buy, this.locale)}</span>
      <span class="sub"
        >${this.tr("plan.stats", {
			avg: L(t.avg, this.locale),
			low: V(t.min.start, this.locale, this.timeZone),
			high: V(t.max.start, this.locale, this.timeZone)
		})}${a}</span
      >
    </div>`;
	}
	notes(e, t) {
		let n = [];
		return e.state === "no_prices" && n.push(E`<p class="note warn">${this.tr("plan.no_prices")}</p>`), e.state === "price_reserve" && n.push(E`<p class="note">${this.tr("plan.reserve")}</p>`), !t && this.period !== "today" && n.push(E`<p class="note">${this.tr("plan.indicative")}</p>`), n.length ? E`${n}` : O;
	}
	chart(e) {
		let t = e.length, n = Ke(e), r = q(e), i = (e) => `${(e / t * 100).toFixed(3)}%`, a = Ue(e, this.timeZone), o = a.length > 1 ? e.findIndex((t) => new Date(t.start).getTime() >= new Date(G(e, 1, this.timeZone)[0].start).getTime()) : -1, s = [];
		for (let t = 0; t < a.length; t++) {
			let n = K(G(e, t, this.timeZone));
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
		let c = Je(e, this.period === "both" ? 6 : 3, this.timeZone), l = this.sel !== null && this.sel < t ? this.sel : null, u = Ye(e, this.view?.soc_now ?? null), d = Xe(e, this.view?.soc_now ?? null), f = n.lo < 0 ? (0 - n.lo) / (n.hi - n.lo) * 100 : null;
		return E`<div class="scroll">
      <div class="chart ${t > 100 ? "wide" : ""}">
        <div class="axis left" aria-hidden="true">
          <span>${L(n.hi, this.locale)}</span><span>${L((n.hi + n.lo) / 2, this.locale)}</span><span>${L(n.lo, this.locale)}</span>
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
          ${f === null ? O : E`<div class="zero" style="bottom:${f}%"></div>`}
          ${e.map((e, t) => {
			if (e.buy === null) return O;
			let a = qe(e.buy, n);
			return E`<div class=${`bar${e.past ? " past" : ""}${e.indicative ? " ind" : ""}${t === r ? " cur" : ""}${t === l ? " focus" : ""}`} style="left:${i(t)};width:${i(1)};bottom:${a.bottom}%;height:${a.height}%"></div>`;
		})}
          <svg viewBox="0 0 ${t} 100" preserveAspectRatio="none" aria-hidden="true">
            ${d.map((e) => be`<polyline class="halo" points=${e}></polyline><polyline class="soc measured" points=${e}></polyline>`)}
            ${u ? be`<polyline class="halo" points=${u}></polyline><polyline class="soc" points=${u}></polyline>` : O}
          </svg>
          ${o > 0 ? E`<div class="split" style="left:${i(o)}"></div>
                <span class="dayname" style="left:calc(${i(o)} + 6px)">${H(e[o].start, this.locale, this.timeZone)}</span>` : O}
          ${s.map(({ q: e, i: r }) => {
			let i = Math.min(94, Math.max(6, (r + .5) / t * 100)), a = qe(e.buy, n);
			return E`<span class="mark" style="left:${i}%;bottom:calc(${a.bottom + a.height}% + 6px)"
              >${L(e.buy, this.locale)} · ${V(e.start, this.locale, this.timeZone)}</span
            >`;
		})}
          ${r >= 0 ? E`<div class="nowline" style="left:${i(r)}"></div>
                <span class="nowpill" style="left:${i(r)}">${this.tr("plan.now_short")}</span>` : O}
          ${l === null ? O : this.tooltip(e[l], l, t)}
        </div>
        <div class="band" aria-hidden="true">
          ${Ge(e).map((e) => E`<div
                class=${e.past ? "seg past" : "seg"}
                style="flex:${e.count} 1 0;background:${e.action ? J(e.action) : "transparent"}"
              ></div>`)}
        </div>
        <div class="ticks" aria-hidden="true">
          ${c.map((t) => E`<span style="left:${i(t)}">${V(e[t].start, this.locale, this.timeZone)}</span>`)}
        </div>
      </div>
    </div>`;
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
		return E`<div class="tip" role="status" style=${i}>
      <strong>${H(e.start, this.locale, this.timeZone)} ${V(e.start, this.locale, this.timeZone)}</strong>
      ${e.buy === null ? E`<span>${this.tr("plan.unknown")}</span>` : E`<span>${this.tr("plan.tip_buy", { price: L(e.buy, this.locale) })}</span>
            <span>${this.tr("plan.tip_sell", { price: L(e.sell, this.locale) })}</span>`}
      ${a ? E`<span>${a}</span>` : O}
      ${e.soc === null ? O : E`<span>${this.tr(e.past ? "plan.tip_soc_past" : "plan.tip_soc", { soc: B(e.soc, this.locale) })}</span>`}
      ${e.solar !== null && e.load !== null ? E`<span>${this.tr(e.past ? "plan.tip_energy_past" : "plan.tip_energy", {
			solar: z(e.solar, this.locale, 2),
			load: z(e.load, this.locale, 2)
		})}</span>` : O}
    </div>`;
	}
	summary(e) {
		let t = K(e);
		return t ? this.tr("plan.aria", {
			low: L(t.min.buy, this.locale),
			low_time: V(t.min.start, this.locale, this.timeZone),
			high: L(t.max.buy, this.locale),
			high_time: V(t.max.start, this.locale, this.timeZone)
		}) : this.tr("plan.title");
	}
	legend() {
		let e = (e, t, n = "sw") => E`<span class="li"><span class=${n} style="background:${e}"></span>${this.tr(t)}</span>`;
		return E`<div class="legend">
      ${e("var(--z-bar)", "plan.legend_price")} ${e(J("charge"), "action.charge")} ${e(J("deliver"), "action.deliver")}
      ${e(J("hold"), "action.hold")} ${e(J("export"), "action.export")}
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
Y([P({ attribute: !1 })], X.prototype, "view", void 0), Y([P({ attribute: !1 })], X.prototype, "uiLang", void 0), Y([P()], X.prototype, "locale", void 0), Y([P()], X.prototype, "timeZone", void 0), Y([P({ type: Boolean })], X.prototype, "narrow", void 0), Y([F()], X.prototype, "period", void 0), Y([F()], X.prototype, "sel", void 0), X = Y([N("zephyr-prices-plan")], X);
// src/sets.ts
function Z(e, t, n) {
	return e.built_in ? W(n, "sets.built_in") : e.model ? t.filter((t) => t.model === e.model).length > 1 ? `${e.model} ${e.number}` : e.model : W(n, "sets.pack", { n: e.index + 1 });
}
function nt(e) {
	let t = e.flatMap((e) => e.packs), n = t.map((e) => e.soc), r = t.map((e) => e.temp).filter((e) => e !== null), i = null;
	for (let e of t) e.cell_delta_mv !== null && e.cell_status !== null && e.cell_status !== "edge" && (!i || e.cell_delta_mv > i.mv) && (i = {
		pack: e,
		mv: e.cell_delta_mv,
		status: e.cell_status
	});
	let a = t.map((e) => e.cell_delta_mv).filter((e) => e !== null);
	return {
		packs: t.length,
		online: e.every((e) => e.online),
		socMin: n.length ? Math.min(...n) : null,
		socMax: n.length ? Math.max(...n) : null,
		warmest: r.length ? Math.max(...r) : null,
		worst: i,
		largest: a.length ? Math.max(...a) : null,
		offline: e.filter((e) => !e.online)
	};
}
var Q = class extends M {
	constructor(...e) {
		super(...e), this.uiLang = "en", this.locale = "en", this.timeZone = "UTC";
	}
	tr(e, t = {}) {
		return W(this.uiLang, e, t);
	}
	num(e, t = 0) {
		return new Intl.NumberFormat(this.locale, {
			minimumFractionDigits: t,
			maximumFractionDigits: t
		}).format(e);
	}
	render() {
		let e = this.view;
		if (!e) return E`<div class="card skeleton" aria-hidden="true"></div>`;
		if (!e.sets.length) return E`<section class="card"><p class="text">${this.tr("sets.none")}</p></section>`;
		let t = nt(e.sets), n = e.sets.flatMap((e) => e.packs);
		return E`
      ${this.renderSummary(t, e.sets)}
      ${e.sets.map((t) => E`<div class="row">
          ${this.renderSet(t, e.sets.length)} ${this.renderPacks(t)}
        </div>`)}
      ${n.length ? this.renderBalance(e.sets) : O} ${e.sets.length === 1 ? this.renderActivity(e) : O}
    `;
	}
	stat(e, t) {
		return E`<div class="stat"><span class="cap">${e}</span><span class="value">${t}</span></div>`;
	}
	renderSummary(e, t) {
		let n = t.flatMap((e) => e.packs), r;
		r = e.offline.length ? this.tr("sets.offline_line", { sets: e.offline.map((e) => this.tr("sets.set", { n: e.number })).join(", ") }) : e.worst?.status === "high" ? this.tr("sets.line_high", {
			pack: Z(e.worst.pack, n, this.uiLang),
			mv: e.worst.mv
		}) : e.worst?.status === "watch" ? this.tr("sets.line_watch", {
			pack: Z(e.worst.pack, n, this.uiLang),
			mv: e.worst.mv
		}) : !e.worst && e.largest !== null ? this.tr("sets.line_edge") : this.tr("sets.line_ok");
		let i = e.worst ? `${this.num(e.worst.mv)} mV` : e.largest === null ? "–" : `${this.num(e.largest)} mV*`;
		return E`<section class="card summary" aria-label=${this.tr("sets.summary")}>
      ${this.stat(this.tr("sets.batteries"), this.tr(e.online ? "sets.all_online" : "sets.some_offline", { n: e.packs }))}
      ${this.stat(this.tr("sets.soc_spread"), e.socMin === null ? "–" : e.socMin === e.socMax ? B(e.socMin, this.locale) : `${this.num(e.socMin)}–${B(e.socMax, this.locale)}`)}
      ${this.stat(this.tr("sets.warmest"), e.warmest === null ? "–" : `${this.num(e.warmest)} °C`)}
      ${this.stat(this.tr("sets.largest_delta"), i)}
      <p class="line"><strong>${this.tr("sets.in_short")}</strong> ${r}</p>
    </section>`;
	}
	renderSet(e, t) {
		let n = e.soc ?? 0, r = e.online ? e.status ?? "standby" : "offline", i = (e, t) => E`<div><dt>${e}</dt><dd>${t}</dd></div>`, a = e.last_full ? U(e.last_full, Date.now(), this.timeZone) ? `${this.tr("sets.today")} ${V(e.last_full, this.locale, this.timeZone)}` : H(e.last_full, this.locale, this.timeZone) : this.tr("sets.unknown");
		return E`<article class="card set">
      <div class="head">
        <div>
          <h2>${this.tr("sets.set", { n: e.number })}</h2>
          <span class="muted"
            >${e.model}${e.packs.length ? ` · ${this.tr("sets.packs_n", { n: e.packs.length })}` : ""}${e.capacity_kwh ? ` · ${z(e.capacity_kwh, this.locale)}` : ""}</span
          >
        </div>
        <span class="chip ${r}">${this.tr(`sets.status.${r}`)}</span>
      </div>
      ${e.soc === null ? E`<p class="text">${this.tr("battery.unknown")}</p>` : E`<div class="big-row">
              <span class="big">${B(n, this.locale)}</span>
              ${e.energy_kwh !== null && e.capacity_kwh ? E`<span class="muted">${this.tr("battery.of", {
			energy: z(e.energy_kwh, this.locale),
			capacity: z(e.capacity_kwh, this.locale)
		})}</span>` : O}
            </div>
            <div class="bar" role="meter" aria-valuemin="0" aria-valuemax="100" aria-valuenow=${Math.round(n)} aria-label=${this.tr("battery.title")}>
              <div class="fill" style="width:${n}%"></div>
              ${e.limits?.min == null ? O : E`<div class="mark" style="left:${e.limits.min}%"></div>`}
              ${e.limits?.max == null ? O : E`<div class="mark" style="left:${e.limits.max}%"></div>`}
            </div>`}
      <dl>
        ${i(this.tr("sets.power"), e.power_w === null ? "–" : R(e.power_w, this.locale))}
        ${e.solar_w ? i(this.tr("sets.solar"), R(e.solar_w, this.locale).replace("+", "")) : O}
        ${i(this.tr("sets.inverter"), e.enclosure_temp === null ? "–" : `${this.num(e.enclosure_temp)} °C`)}
        ${i(this.tr("sets.last_full"), a)}
        ${i(this.tr("sets.switches"), e.relays_24h === null ? "–" : this.tr("sets.switches_n", { n: e.relays_24h }))}
        ${i(this.tr("sets.limits"), e.limits?.min != null && e.limits?.max != null ? `${this.num(e.limits.min)}–${this.num(e.limits.max)} %` : "–")}
      </dl>
      <div class="foot">
        <span>${t >= 3 ? this.tr("sets.max_sets") : ""}</span>
        ${t < 3 ? E`<a class="button" href="/config/integrations/integration/zephyr">${this.tr("sets.add")}</a>` : O}
      </div>
    </article>`;
	}
	renderPacks(e) {
		return e.packs.length ? E`<section class="card packs" aria-label=${this.tr("sets.in_set")}>
      <div class="head">
        <h2>${this.tr("sets.in_set")}</h2>
        <span class="muted">${this.tr("sets.pack_power_note")}</span>
      </div>
      <div class="grid">
        ${e.packs.map((t) => {
			let n = t.cell_status;
			return E`<div class="pack ${e.online ? "" : "off"}">
            <div class="ph"><strong>${Z(t, e.packs, this.uiLang)}</strong><span class="muted">${t.capacity_kwh ? z(t.capacity_kwh, this.locale, 2) : this.tr("sets.unknown_type")}</span></div>
            <div class="big-row">
              <span class="mid">${B(t.soc, this.locale)}</span>
              ${t.energy_kwh === null ? O : E`<span class="muted">${z(t.energy_kwh, this.locale, 2)}</span>`}
            </div>
            <div class="bar thin"><div class="fill" style="width:${t.soc}%"></div></div>
            <dl>
              <div><dt>${this.tr("sets.power")}</dt><dd>${R(t.power_w, this.locale)}</dd></div>
              <div><dt>${this.tr("sets.temp")}</dt><dd>${t.temp === null ? "–" : `${this.num(t.temp)} °C`}</dd></div>
              <div>
                <dt>${this.tr("sets.cells")}</dt>
                <dd>${t.cell_min_v === null || t.cell_max_v === null ? "–" : `${this.num(t.cell_min_v, 2)}–${this.num(t.cell_max_v, 2)} V`}</dd>
              </div>
              <div>
                <dt>${this.tr("sets.cell_delta")}</dt>
                <dd class="delta">
                  ${t.cell_delta_mv === null ? "–" : `${this.num(t.cell_delta_mv)} mV`}
                  ${n ? E`<span class="tag ${n}">${this.tr(`sets.cell.${n}`)}</span>` : O}
                </dd>
              </div>
            </dl>
          </div>`;
		})}
      </div>
      <p class="text small">${this.tr("sets.cell_note")}</p>
    </section>` : E``;
	}
	renderBalance(e) {
		let t = e.find((e) => e.packs.length)?.packs[0]?.history ?? [];
		return E`<section class="card" aria-label=${this.tr("sets.balance_title")}>
      <div class="head">
        <h2>${this.tr("sets.balance_title")}</h2>
        <span class="muted">${this.tr("sets.balance_note")}</span>
      </div>
      <div class="table" role="table">
        <div class="tr" role="row">
          <span role="columnheader"></span>
          ${t.map((e) => E`<span role="columnheader" class="dh">${H(`${e.day}T12:00:00Z`, this.locale, this.timeZone)}</span>`)}
        </div>
        ${e.flatMap((t) => t.packs.map((n) => E`<div class="tr" role="row">
              <span role="rowheader" class="rh">${e.length > 1 ? `${t.number} · ` : ""}${Z(n, t.packs, this.uiLang)}</span>
              ${n.history.map((e) => E`<span
                  role="cell"
                  class="cell ${e.status ?? "none"}"
                  title=${e.max_mv === null ? this.tr("sets.no_judged") : `${e.max_mv} mV · ${this.tr(`sets.cell.${e.status}`)}`}
                  >${e.max_mv === null ? "–" : this.num(e.max_mv)}${e.full ? E` <span aria-label=${this.tr("sets.full_day")}>▲</span>` : O}</span
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
		return E`<section class="card" aria-label=${this.tr("sets.activity_title")}>
      <div class="head">
        <h2>${this.tr("sets.activity_title")}</h2>
        <div class="legend">
          <span><i style="background:${J("charge")}"></i>${this.tr("action.charge")}</span>
          <span><i style="background:${J("deliver")}"></i>${this.tr("action.deliver")}</span>
          <span><i style="background:${J("hold")}"></i>${this.tr("action.hold")}</span>
        </div>
      </div>
      <div class="activity" aria-hidden="true">
        ${e.activity_24h.map((e) => {
			e.action in i && (i[e.action] += 1);
			let t = r(e.start);
			return E`<div
            title="${V(e.start, this.locale, this.timeZone)}–${V(e.end, this.locale, this.timeZone)} · ${this.tr(`action.${e.action}`)}"
            style="left:${t}%;width:${r(e.end) - t}%;background:${J(e.action)}"
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
		].map((e) => E`<span>${V(new Date(n + e * 36e5).toISOString(), this.locale, this.timeZone)}</span>`)}
        <span>${this.tr("plan.now_short")}</span>
      </div>
      ${e.activity_24h.length ? O : E`<p class="text small">${this.tr("sets.no_activity")}</p>`}
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
    .tag.watch,
    .cell.watch {
      background: var(--z-warn-bg);
      color: var(--z-warn-text);
    }
    .tag.high,
    .cell.high {
      background: var(--z-bad-bg);
      color: var(--z-bad-text);
    }
    .tag.edge {
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
Y([P({ attribute: !1 })], Q.prototype, "view", void 0), Y([P({ attribute: !1 })], Q.prototype, "uiLang", void 0), Y([P()], Q.prototype, "locale", void 0), Y([P()], Q.prototype, "timeZone", void 0), Q = Y([N("zephyr-sets")], Q);
// src/zephyr-panel.ts
var rt = "/zephyr_static", it = [
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
function at(e) {
	let t = "zephyr-fonts";
	if (document.getElementById(t)) return;
	let n = document.createElement("style");
	n.id = t, n.textContent = it.map(([t, n, r]) => `@font-face{font-family:"${t}";font-style:normal;font-weight:${n};font-display:swap;src:url("${e}/fonts/${r}") format("woff2");}`).join("\n"), document.head.appendChild(n);
}
var $ = class extends M {
	constructor(...e) {
		super(...e), this.narrow = !1, this.status = "loading", this.view = "plan", this.clockMs = Date.now(), this.planFor = "", this.planBusy = !1, this.subscribing = !1, this.onReady = () => {
			this.status = "loading", this.subscribe();
		}, this.onDisconnected = () => {
			this.unsubscribe = void 0, this.status = "disconnected";
		};
	}
	get base() {
		return this.panel?.config?.static ?? rt;
	}
	get uiLang() {
		return Ve(this.hass?.locale?.language ?? this.hass?.language);
	}
	get locale() {
		return this.hass?.locale?.language ?? this.hass?.language ?? "en";
	}
	get timeZone() {
		return this.hass?.config.time_zone ?? Intl.DateTimeFormat().resolvedOptions().timeZone;
	}
	tr(e, t = {}) {
		return W(this.uiLang, e, t);
	}
	connectedCallback() {
		super.connectedCallback(), at(this.base), this.clockTimer = window.setInterval(() => this.clockMs = Date.now(), 3e4), this.planTimer = window.setInterval(() => void this.loadPlan(!0), 3e5), this.hass && this.subscribe();
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
	show(e) {
		this.view = e, window.clearInterval(this.setsTimer), e === "sets" && (this.loadSets(), this.setsTimer = window.setInterval(() => void this.loadSets(), 1e4));
	}
	retry(e) {
		window.clearTimeout(this.retryTimer), this.retryTimer = window.setTimeout(() => void this.subscribe(), e);
	}
	onEvent(e) {
		e.type === "now" ? (this.now = e.data, this.status = "ok", this.clockMs = Date.now(), this.loadPlan()) : e.type === "unloaded" && (this.unsubscribe = void 0, this.status = "reloading", this.retry(3e3));
	}
	render() {
		return E`
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
			["settings", "menu.settings"],
			["diagnostics", "menu.diagnostics"]
		];
		return E`
      <header>
        <div class="brand">
          <img src="${this.base}/logo.png" alt="" width="32" height="32" />
          <span>ZEPHYR</span>
        </div>
        <nav aria-label=${this.tr("menu.label")}>
          ${t.map(([e, t]) => E`<button
                type="button"
                class=${this.view === e ? "tab active" : "tab"}
                aria-current=${this.view === e ? "page" : "false"}
                @click=${() => this.show(e)}
              >
                ${this.tr(t)}
              </button>`)}
        </nav>
        <div class="meta">
          ${e ? E`<span class="chip">${this.tr(`mode.${e.mode}`)}</span>
                <span class=${e.live ? "chip live" : "chip"} title=${this.tr(e.live ? "header.live_title" : "header.shadow_title")}
                  >${this.tr(e.live ? "header.live" : "header.shadow")}</span
                >` : O}
          <span class="time">${V(new Date(this.clockMs).toISOString(), this.locale, this.timeZone)}</span>
        </div>
      </header>
    `;
	}
	renderBanner() {
		switch (this.status) {
			case "not_loaded": return E`<div class="banner" role="status">${this.tr("status.not_loaded")}</div>`;
			case "reloading": return E`<div class="banner info" role="status">${this.tr("status.reloading")}</div>`;
			case "disconnected": return E`<div class="banner" role="status">
          ${this.tr("status.disconnected", { time: this.now ? V(this.now.updated_at, this.locale, this.timeZone) : "–" })}
        </div>`;
			default: return O;
		}
	}
	renderView() {
		return this.view === "plan" ? this.renderPlan() : this.view === "sets" ? E`<zephyr-sets
        class=${this.status === "ok" ? "" : "stale"}
        .view=${this.setsView}
        .uiLang=${this.uiLang}
        .locale=${this.locale}
        .timeZone=${this.timeZone}
      ></zephyr-sets>` : this.renderComing();
	}
	renderComing() {
		return E`<section class="card coming">${this.tr("status.coming")}</section>`;
	}
	renderPlan() {
		let e = this.now;
		if (!e) return E`<section class="cards" aria-busy="true">
        ${[
			0,
			1,
			2
		].map(() => E`<div class="card skeleton" aria-hidden="true"></div>`)}
      </section>`;
		let t = this.status === "ok" ? "" : "stale";
		return E`<section class="cards ${t}" aria-label=${this.tr("now.title")}>
        ${this.renderNow(e)} ${this.renderBattery(e)} ${this.renderNext(e)}
      </section>
      ${e.price_entity ? this.renderPlanParts(e, t) : O}`;
	}
	renderPlanParts(e, t) {
		let n = null;
		return e.mode === "dynamic_forecasting" ? e.live || (n = this.tr("plan.shadow_note")) : n = this.tr("plan.mode_note", { mode: this.tr(`mode.${e.mode}`) }), E`${n ? E`<div class="banner info" role="note">${n}</div>` : O}
      <zephyr-prices-plan
        class=${t}
        .view=${this.planView}
        .uiLang=${this.uiLang}
        .locale=${this.locale}
        .timeZone=${this.timeZone}
        ?narrow=${this.narrow}
      ></zephyr-prices-plan>
      ${this.planView ? E`<section class="duo ${t}">${this.renderBlocks(this.planView)} ${this.renderWhy(this.planView)}</section>` : O}`;
	}
	range(e) {
		let t = V(e.start, this.locale, this.timeZone), n = V(e.end, this.locale, this.timeZone), r = `${this.tr("blocks.tomorrow")} `, i = U(e.start, this.clockMs, this.timeZone), a = U(new Date(e.end).getTime() - 1, this.clockMs, this.timeZone);
		return `${i ? "" : r}${t}–${i && !a ? r : ""}${n}`;
	}
	renderBlocks(e) {
		let t = Ze(e.blocks, new Date(this.clockMs).toISOString()).slice(0, 10);
		return E`<article class="card">
      <h2>${this.tr("blocks.title")}</h2>
      ${t.length ? E`<ul class="blocks">
            ${t.map((e) => E`<li>
                <span class="when">${this.range(e)}</span>
                <span class="swatch" style="background:${J(e.action)}"></span>
                <span class="what">${this.tr(`blocks.what_${e.action}`)}${e.indicative ? E` <em>(${this.tr("blocks.indicative")})</em>` : O}</span>
                <span class="detail">${this.tr(`blocks.${e.action}`, {
			kwh: z(e.kwh, this.locale),
			price: L(e.price, this.locale)
		})}</span>
              </li>`)}
          </ul>` : E`<p class="text">${this.tr("blocks.none")}</p>`}
    </article>`;
	}
	renderWhy(e) {
		let t = [];
		e.reason && t.push(e.reason[this.uiLang]);
		let n = Ze(e.blocks, new Date(this.clockMs).toISOString()).filter((e) => !e.indicative), r = n.filter((e) => e.action === "charge").sort((e, t) => e.price - t.price)[0];
		r ? t.push(this.tr("why.cheapest", {
			time: this.range(r),
			price: L(r.price, this.locale)
		})) : n.length && t.push(this.tr("why.no_charge"));
		let i = e.quarters.filter((e) => !e.past), a = K(i)?.max;
		if (a && a.action === "deliver") {
			let e = `${U(a.start, this.clockMs, this.timeZone) ? "" : `${this.tr("blocks.tomorrow")} `}${V(a.start, this.locale, this.timeZone)}`;
			t.push(this.tr("why.peak", {
				time: e,
				price: L(a.buy, this.locale)
			}));
		}
		return i.some((e) => e.indicative) && t.push(this.tr("why.indicative")), E`<article class="card">
      <h2>${this.tr("why.title")}</h2>
      <ul class="why">
        ${t.map((e) => E`<li>${e}</li>`)}
      </ul>
    </article>`;
	}
	renderNow(e) {
		let t = e.action ?? "standby", n = e.battery_w !== null && Math.abs(e.battery_w) >= 10 ? ` · ${Re(e.battery_w, this.locale)}` : "";
		return E`<article class="card">
      <div class="label"><span class="dot" style="background:${J(t)}"></span>${this.tr("now.title")}</div>
      <div class="big">${e.action ? this.tr(`action.${t}`) + n : this.tr("now.waiting")}</div>
      ${e.reason ? E`<p class="text">${e.reason[this.uiLang]}</p>` : O}
      <div class="foot">
        ${e.grid_w === null ? O : E`<span>${this.tr("now.grid", { value: R(e.grid_w, this.locale) })}</span>`}
        ${e.live ? O : E`<span>${this.tr("now.shadow_note")}</span>`}
      </div>
    </article>`;
	}
	renderBattery(e) {
		if (e.soc === null) return E`<article class="card">
        <div class="label">${this.tr("battery.title")}</div>
        <p class="text">${this.tr("battery.unknown")}</p>
      </article>`;
		let t = Math.max(0, Math.min(100, e.soc)), n = Math.max(0, e.buffer_pct), r = e.sets_total <= 1 ? e.sets_online >= 1 ? this.tr("battery.set") : this.tr("battery.set_offline") : this.tr("battery.sets", {
			online: e.sets_online,
			total: e.sets_total
		});
		return E`<article class="card">
      <div class="label">${this.tr("battery.title")}</div>
      <div class="big-row">
        <span class="big">${B(t, this.locale)}</span>
        ${e.energy_kwh !== null && e.capacity_kwh !== null ? E`<span class="muted"
              >${this.tr("battery.of", {
			energy: z(e.energy_kwh, this.locale),
			capacity: z(e.capacity_kwh, this.locale)
		})}</span
            >` : O}
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
        ${n > 0 ? E`<div class="buffer" style="left:${e.min_soc}%;width:${Math.min(n, 100 - e.min_soc)}%"></div>` : O}
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
		let t = e.plan, n = (e = "") => E`<div class="label">
        <span class="dot" style="background:${J(t?.next?.action)}"></span>${this.tr("next.title")}${e}
      </div>`;
		if (!e.price_entity) return E`<article class="card">${n()}<p class="text">${this.tr("next.no_price_source")}</p></article>`;
		if (!t) return E`<article class="card">${n()}<p class="text">${this.tr("status.loading")}</p></article>`;
		if (t.state === "no_prices") {
			let e = t.no_prices_since ?? t.calculated_at;
			return E`<article class="card">
        ${n()}
        <p class="text warn">${this.tr("next.no_prices", { time: e ? V(e, this.locale, this.timeZone) : "–" })}</p>
      </article>`;
		}
		let r = t.next, i = t.price_now ? E`<div class="foot"><span>${this.tr("next.price_now", { price: L(t.price_now.import, this.locale) })}</span></div>` : O;
		if (!r) return E`<article class="card">${n()}<p class="text">${this.tr("next.none")}</p>${i}</article>`;
		let a = ze(r.start, this.clockMs), o = a <= 0 ? this.tr("next.now") : this.tr("next.in", { time: a >= 60 ? this.tr("next.hours", {
			h: Math.floor(a / 60),
			m: a % 60
		}) : this.tr("next.minutes", { m: a }) }), s = V(r.start, this.locale, this.timeZone), c = this.tr(`action.${r.action}`), l = U(r.start, this.clockMs, this.timeZone) ? this.tr("next.at", {
			time: s,
			action: c
		}) : this.tr("next.tomorrow", {
			time: s,
			action: c
		});
		return E`<article class="card">
      ${n(` · ${o}`)}
      <div class="big">${l}</div>
      <p class="text">${this.detail(t)}</p>
      ${r.indicative ? E`<p class="text muted">${this.tr("next.indicative")}</p>` : O} ${i}
    </article>`;
	}
	detail(e) {
		let t = e.next;
		if (!t) return "";
		let n = {
			kwh: z(t.kwh, this.locale),
			price: L(t.price, this.locale)
		};
		return this.tr(`next.${t.action}`, n);
	}
	static {
		this.styles = [Qe, o`
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
      .cards.stale,
      .duo.stale,
      zephyr-prices-plan.stale,
      zephyr-sets.stale {
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
Y([P({ attribute: !1 })], $.prototype, "hass", void 0), Y([P({ type: Boolean })], $.prototype, "narrow", void 0), Y([P({ attribute: !1 })], $.prototype, "panel", void 0), Y([F()], $.prototype, "now", void 0), Y([F()], $.prototype, "status", void 0), Y([F()], $.prototype, "view", void 0), Y([F()], $.prototype, "clockMs", void 0), Y([F()], $.prototype, "planView", void 0), Y([F()], $.prototype, "setsView", void 0), $ = Y([N("zephyr-panel")], $);
export { $ as ZephyrPanel };
