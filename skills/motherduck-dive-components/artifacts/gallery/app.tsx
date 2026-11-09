// ---------------------------------------------------------------------------
// Component gallery: every kit component on sample data, with live theming.
// Assemble with:  python3 assemble.py gallery/app.tsx -o gallery/dive/index.tsx --extra examples/funnel.tsx
// It reads no databases; every block below is a hand-written spec block.
// ---------------------------------------------------------------------------

// @imports
import { createContext, useContext, useMemo, useRef, useState } from 'react';
import { useDiveState } from '@motherduck/react-sql-query';
import { Code2, Palette } from 'lucide-react';
// @imports-end

export const REQUIRED_DATABASES: any[] = [];

// ---- Sample data (deterministic) ----------------------------------------------------

function rng(seed: number) {
	let s = seed;
	return () => ((s = (s * 16807) % 2147483647) - 1) / 2147483646;
}
const r = rng(7);
const END = '2026-11-08';
const dayIso = (back: number) => new Date(Date.parse(END + 'T00:00:00Z') - back * 86400000).toISOString().slice(0, 10);

const DAILY = Array.from({ length: 182 }, (_, i) => {
	const back = 181 - i;
	const dow = new Date(Date.parse(dayIso(back) + 'T00:00:00Z')).getUTCDay();
	const base = 420 + i * 1.6 + (dow === 0 || dow === 6 ? -230 : 0);
	const spike = back < 9 ? 380 : 0;
	return { x: dayIso(back), visitors: Math.round(base + spike + r() * 90) };
});
const WEEKS = Array.from({ length: 16 }, (_, i) => dayIso(7 * (15 - i) + 6));
const CHANNELS = ['Google', 'Direct', 'Other', 'AI Chat', 'GitHub'];
const WEEKLY = WEEKS.map((w, i) => {
	const row: any = { x: w };
	row.Google = Math.round(900 + r() * 120 + (i === 4 ? 1400 : 0));
	row.Direct = Math.round(1100 + i * 40 + r() * 100);
	row.Other = Math.round(60 + r() * 30 + (i > 13 ? 2600 + i * 120 : 0));
	row['AI Chat'] = Math.round(120 + i * 18 + r() * 30);
	row.GitHub = Math.round(80 + r() * 25);
	return row;
});

const KPI = {
	id: 'kpi',
	type: 'kpi',
	title: 'Headline numbers',
	compare: 'previous_period',
	items: [
		{ key: 'docs.visitors', label: 'Docs visitors', value: 12480, prior: 8920, format: 'count', good: 'up', spark: WEEKLY.map((w) => w.Google + w.Direct + w.Other), spark_x: WEEKS, spark_grain: 'week' },
		{ key: 'docs.conversion_rate', label: 'Docs → app conversion', value: 0.0072, prior: 0.0098, format: 'pct', good: 'up', spark: WEEKLY.map((_, i) => 0.011 - i * 0.0003 + r() * 0.001), spark_x: WEEKS, spark_grain: 'week' },
		{ key: 'search.ctr', label: 'Google CTR', value: 0.031, prior: 0.034, format: 'pct', good: 'up', spark: WEEKLY.map(() => 0.03 + r() * 0.006), spark_x: WEEKS, spark_grain: 'week' },
		{ key: 'assistant.unanswered_rate', label: 'Unanswered rate', value: 0.082, prior: 0.11, format: 'pct', good: 'down', spark: WEEKLY.map((_, i) => 0.12 - i * 0.002 + r() * 0.01), spark_x: WEEKS, spark_grain: 'week' },
	],
};

const RATES = {
	id: 'rates',
	type: 'gauge',
	title: 'Quality rates',
	compare: 'previous_period',
	items: [
		{ key: 'search.ctr', label: 'Google CTR', value: 0.031, prior: 0.034, format: 'pct', good: 'up', max: 0.05 },
		{ key: 'assistant.unanswered_rate', label: 'Unanswered rate', value: 0.082, prior: 0.11, format: 'pct', good: 'down', max: 0.2 },
		{ key: 'feedback.helpful_rate', label: 'Pages rated helpful', value: 0.74, prior: 0.69, format: 'pct', good: 'up', max: 1 },
	],
};

const LINE = {
	id: 'line',
	type: 'line',
	title: 'Weekly docs visitors by channel',
	x: { kind: 'time', grain: 'week' },
	series: CHANNELS.map((c) => ({ key: c, label: c, format: 'count' })),
	data: WEEKLY,
	annotations: [{ x: WEEKS[4], label: 'Google spike', series: 'Google' }, { x: WEEKS[14], label: 'Other surges', series: 'Other' }],
	insight: 'Other now brings more visitors than Google; check where it comes from before counting it as growth.',
	why: 'Shows where readers come from and how that is shifting.',
	about: { definitions: [{ term: 'Docs visitors', text: 'Unique people with at least one docs pageview in the week.' }, { term: 'Channel', text: "The entry referrer's channel: Google, Direct, AI Chat, GitHub, Other." }], why: 'Shows where readers come from and how that is shifting.' },
	source: { dataset: 'docs', measures: ['docs.visitors'], dimension: 'channel', window: 'last_6_months', filters: [], sql: ['SELECT week, channel, count(DISTINCT person_id) FROM docs_events GROUP BY ALL'] },
	points: [{ x: WEEKS[4], series: 'Google' }, { x: WEEKS[14], series: 'Other' }],
};

const CALENDAR = { id: 'cal', type: 'heatmap', mode: 'calendar', title: 'Daily docs visitors', x: { kind: 'time', grain: 'day' }, series: [{ key: 'visitors', label: 'Docs visitors', format: 'count' }], data: DAILY };

const BAR = {
	id: 'bar',
	type: 'bar',
	title: 'Conversion by docs section (%)',
	x: { kind: 'category' },
	series: [
		{ key: 'conversion_rate', label: 'Conversion', format: 'pct', good: 'up' },
		{ key: 'conversion_rate_prior', label: 'Previous period', format: 'pct', muted: true },
	],
	data: [
		['getting-started', 0.0127, 0.0182],
		['key-tasks', 0.0062, 0.0081],
		['integrations', 0.0041, 0.0049],
		['sql-reference', 0.0028, 0.0041],
		['concepts', 0.0035, 0.0032],
	].map(([x, a, b]) => ({ x, conversion_rate: a, conversion_rate_prior: b })),
	highlight: ['getting-started'],
	source: { dataset: 'docs', measures: ['docs.conversion_rate'], dimension: 'section', window: 'last_28_days', filters: [], sql: ['SELECT section, avg(converted) FROM docs_sessions GROUP BY 1'] },
};

// Questions a generated page asks its viewers. Answers become notes on every chart that shows the date or value.
const QUESTIONS = {
	id: 'questions',
	type: 'questions',
	title: 'Questions for you',
	items: [
		{ id: 'q1', kind: 'date', x: WEEKS[14], grain: 'week', label: `the week of ${fmtPeriod(WEEKS[14], 'week')}`, question: `What happened in the week of ${fmtPeriod(WEEKS[14], 'week')}? Other-channel visitors jumped twentyfold.`, options: ['Partner mention', 'Newsletter', 'Bot traffic', 'Tracking change'] },
		{ id: 'q2', kind: 'topic', dimension: 'section', value: 'getting-started', label: 'section getting-started', question: 'Why did getting-started convert fewer readers than last period?', options: ['Page redesign', 'New traffic source', 'Signup flow change'] },
	],
};

const PAGES = ['getting-started/connect', 'key-tasks/dives', 'key-tasks/flights', 'sql-reference/functions', 'integrations/dbt', 'integrations/python', 'concepts/hybrid-execution', 'key-tasks/sharing', 'sql-reference/attach', 'getting-started/cli'];
const TREE = {
	id: 'tree',
	type: 'treemap',
	title: 'Docs visitors by section and page',
	format: 'count',
	tree: {
		name: 'All',
		children: ['getting-started', 'key-tasks', 'sql-reference', 'integrations', 'concepts'].map((sec, i) => ({
			name: sec,
			children: PAGES.filter((p) => p.startsWith(sec)).map((p) => ({ name: p.split('/')[1], value: Math.round((3200 - i * 520) * (0.4 + r())) })).concat([{ name: 'other pages', value: Math.round(900 - i * 120) }]),
		})),
	},
};

const SANKEY_SRC = ['Google', 'Direct', 'Other', 'AI Chat'];
const SANKEY_DST = ['getting-started', 'key-tasks', 'sql-reference', 'integrations'];
const FLOWS = SANKEY_SRC.flatMap((s, i) => SANKEY_DST.map((d, j) => ({ source: i, target: SANKEY_SRC.length + j, value: Math.round((1800 - i * 350) * (0.15 + r()) * (j === 2 && s === 'Other' ? 4 : 1)) })));
const SANKEY = {
	id: 'sankey',
	type: 'sankey',
	title: 'Where each channel lands',
	format: 'count',
	source_label: 'Channel',
	target_label: 'Docs section',
	nodes: [...SANKEY_SRC.map((name) => ({ name, side: 'source' })), ...SANKEY_DST.map((name) => ({ name, side: 'target' }))],
	links: FLOWS,
	x: { kind: 'category' },
	series: [{ key: 'value', label: 'Visitors', format: 'count' }],
	data: FLOWS.map((f) => ({ x: `${SANKEY_SRC[f.source]} → ${SANKEY_DST[f.target - SANKEY_SRC.length]}`, value: f.value })),
};

const CHANGES = {
	id: 'changes',
	type: 'timeline',
	title: 'What moved since the baseline',
	timeline: { date: 'since', title: 'x' },
	x: { kind: 'category', label: 'metric' },
	series: [
		{ key: 'baseline', label: 'Aug-Sep', format: 'row' },
		{ key: 'latest', label: 'Last 4 weeks', format: 'row' },
		{ key: 'change', label: 'Change', format: 'delta_pct' },
		{ key: 'since', label: 'Shift detected', format: 'text' },
	],
	data: [
		{ x: 'Google clicks', baseline: 812, latest: 774, change: -0.05, since: '2026-09-14', _format: 'count', _good: 'up' },
		{ x: 'Assistant sessions', baseline: 2410, latest: 3620, change: 0.5, since: '2026-10-05', _format: 'count', _good: 'up' },
		{ x: 'Docs → app conversion', baseline: 0.0098, latest: 0.0072, change: -0.27, since: '2026-10-19', _format: 'pct', _good: 'up' },
		{ x: 'Docs visitors', baseline: 2230, latest: 3120, change: 0.4, since: '2026-10-26', _format: 'count', _good: 'up' },
	],
};

const FUNNEL = {
	id: 'funnel',
	type: 'funnel',
	title: 'From docs visit to app (custom component)',
	x: { kind: 'category' },
	series: [{ key: 'v', label: 'Visitors', format: 'count' }],
	data: [
		{ x: 'Visited docs', v: 12480 },
		{ x: 'Read 2+ pages', v: 5390 },
		{ x: 'Ran SQL in docs', v: 1020 },
		{ x: 'Clicked to app', v: 90 },
	],
};

const CALLOUTS = {
	id: 'callouts',
	type: 'callouts',
	title: 'Insights',
	items: [
		{ tone: 'critical', title: 'Traffic up, conversion down', body: 'Visitors rose 40% while conversion fell from 0.98% to 0.72%.', question: 'Why did conversion fall?', continuity: 'worsening', first_seen: '2026-10-19', times_seen: 3 },
		{ tone: 'warning', title: 'One referrer drives Other', body: 'partner-site.example sent 4,100 of 4,400 Other sessions, all Chrome desktop.', question: 'Is the partner-site.example traffic real?', continuity: 'new', first_seen: '2026-11-08', times_seen: 1 },
		{ tone: 'positive', title: 'Fewer unanswered questions', body: 'The assistant left 8.2% unanswered, down from 11%.', continuity: 'improving', first_seen: '2026-10-26', times_seen: 2 },
	],
};

// ---- Gallery ---------------------------------------------------------------------

const BRAND_FONTS: Record<string, string> = {
	'Helvetica': '"Helvetica Neue", Helvetica, Arial, sans-serif',
	'System': 'ui-sans-serif, system-ui, -apple-system, "Segoe UI", sans-serif',
	'Serif': 'Georgia, "Times New Roman", serif',
	'Mono': 'ui-monospace, "SFMono-Regular", Menlo, monospace',
};

const NarrowCtx = createContext(false);
// Notes viewers saved in the gallery, shared by every section (a Dive sends them to its Flight).
const NotesCtx = createContext<any>({ notes: [], annotate: () => {} });

function Section({ type, title, block, wide, children, variants = true }: any) {
	const t = useTheme();
	const narrow = useContext(NarrowCtx);
	const [v, setV] = useState(block?.type);
	const [showData, setShowData] = useState(false);
	const [ratings, setRatings] = useState<Record<string, string>>({});
	const { notes, annotate } = useContext(NotesCtx);
	const shown = block ? withNotes(block, notes) : block;
	// A stand-in for the Dive's page actions: Investigate does nothing here; ratings and notes are kept locally.
	const nav = {
		notes,
		annotate,
		noteFor: (item: any) => notes.find((n: any) => n.kind === item.kind && (item.kind === 'date' ? n.x === item.x : n.dimension === item.dimension && n.value === item.value)) || null,
		busy: false, investigate: () => {}, existing: () => null, running: () => false, open: () => {},
		rate: (kind: string, target: string, value: string) => setRatings({ ...ratings, [`${kind}|${target}`]: value }),
		rating: (kind: string, target: string) => ratings[`${kind}|${target}`] || '',
	};
	const opts = block ? variantsFor(block) : [];
	const entry = (MANIFEST as any)[type];
	return (
		<div style={{ gridColumn: wide || narrow ? 'span 12 / span 12' : 'span 6 / span 6', minWidth: 0 }}>
			<Card
				title={title}
				icon={componentIcon(v || type)}
				description={entry?.when}
				actions={
					<>
						{variants && opts.length > 1 && <Segmented options={opts.map((o: string) => ({ value: o, label: componentLabel(o) }))} value={v} onChange={setV} />}
						{block && (
							<Button variant="ghost" size="icon" title="Show the block's data" onClick={() => setShowData(!showData)}>
								<Code2 size={13} />
							</Button>
						)}
					</>
				}
				style={{ height: '100%' }}
			>
				{children || <BlockView block={shown} variant={v} nav={nav} />}
				{!children && <BlockInsight block={block} />}
				{!children && <NotesLine block={shown} />}
				{!children && block?.source && (
					<div className="mt-3 text-xs" style={{ color: t.muted }}>
						<SourceFooter block={block} />
					</div>
				)}
				{showData && (
					<pre className="mt-3 overflow-x-auto p-2 text-xs" style={{ maxHeight: 220, background: t.bg === '#ffffff' ? '#f7f7f7' : t.bg, border: `1px solid ${t.line}`, color: t.text }}>
						{JSON.stringify(block, (k, val) => (Array.isArray(val) && val.length > 6 ? [...val.slice(0, 6), `… ${val.length - 6} more`] : val), 2)}
					</pre>
				)}
				<div className="mt-2 text-xs" style={{ color: t.muted }}>
					<code>{v || type}</code>
				</div>
			</Card>
		</div>
	);
}

// What each component is for, from components.json (kept in sync by hand).
const MANIFEST: Record<string, { when: string }> = {
	gauge: { when: 'A rate against a bounded scale, with a tick at the previous value.' },
	kpi: { when: 'Headline numbers with change and sparkline. Switch to cards, compact stats or gauges.' },
	line: { when: 'A trend over time, with a "so what" line and an About panel (definitions, why it is here, source). Markers sit on the series they describe.' },
	heatmap: { when: 'Patterns by day: a calendar of daily activity, or a category against weeks.' },
	sankey: { when: 'How a count flows from one set of categories into another.' },
	treemap: { when: 'Part-to-whole of one additive measure. Click a group to zoom in.' },
	timeline: { when: 'Events in order. Here: the shifts the change detector found.' },
	bar: { when: 'A measure across categories against the previous period.' },
	funnel: { when: 'A custom component, registered from examples/funnel.tsx.' },
	callouts: { when: 'Findings that need attention: how each relates to earlier ones (new, ongoing, worsening, improving, resolved), an Investigate button and a rating.' },
	datepicker: { when: 'A date or range for the viewer to choose. Here it filters the chart below.' },
};

export default function ComponentGallery() {
	const [base, setBase] = useDiveState<string>('base', 'swiss');
	const [brand, setBrand] = useDiveState<any>('brand', null);
	const [range, setRange] = useDiveState<any>('range', { from: dayIso(89), to: END });
	const theme = useMemo(() => makeTheme(brand ? { base, ...brand } : base), [base, brand]);
	const t = theme;
	const [notes, setNotes] = useState<any[]>([]);
	const notesCtx = useMemo(() => ({ notes, annotate: (n: any) => setNotes((prev) => [{ ...n, x: n.kind === 'date' ? n.x : n.value }, ...prev]) }), [notes]);
	const pageRef = useRef<HTMLDivElement>(null);
	const narrow = useWidth(pageRef) < 760;
	const daily = DAILY.filter((d) => d.x >= range.from && d.x <= range.to);
	const AREA = { id: 'area', type: 'area', title: 'Daily docs visitors', x: { kind: 'time', grain: 'day' }, series: [{ key: 'visitors', label: 'Docs visitors', format: 'count', good: 'up' }], data: daily };
	const input = { background: t.panel, color: t.text, border: `1px solid ${t.line}`, borderRadius: Math.min(t.radius, 6), padding: '2px 6px', fontSize: 12 };
	return (
		<ThemeCtx.Provider value={theme}>
			<div style={{ background: t.bg, color: t.text, fontFamily: t.font, minHeight: '100vh' }}>
				<NarrowCtx.Provider value={narrow}>
				<NotesCtx.Provider value={notesCtx}>
				<div ref={pageRef} className="mx-auto px-4 pb-16 pt-6 md:px-8" style={{ maxWidth: 1360 }}>
					<header className="mb-8 flex flex-wrap items-end justify-between gap-4">
						<div>
							<div className="text-xs font-bold uppercase" style={{ color: t.muted, letterSpacing: 1 }}>
								MotherDuck Dive components
							</div>
							<h1 className={t.flat ? 'text-4xl font-bold' : 'text-2xl font-semibold'} style={{ fontFamily: t.heading, letterSpacing: t.flat ? -1.2 : -0.3 }}>
								Component gallery
							</h1>
							<p className="mt-1 text-sm" style={{ color: t.muted, maxWidth: 720 }}>
								Every default component on sample data. Switch a block between the renderers that can show its data, open its data with the code button, and restyle everything below with a theme or your own brand.
							</p>
						</div>
						<div className="flex flex-wrap items-center gap-3">
							<Segmented options={Object.entries(THEMES).map(([k, v]: any) => ({ value: k, label: v.name }))} value={base} onChange={setBase} />
							<Button variant={brand ? 'primary' : 'outline'} size="sm" onClick={() => setBrand(brand ? null : { name: 'Brand', accent: '#0777b3', font: BRAND_FONTS.System, radius: 8 })}>
								<Palette size={13} /> {brand ? 'Brand on' : 'Try a brand'}
							</Button>
						</div>
					</header>

					{brand && (
						<div className="mb-8 flex flex-wrap items-center gap-4 text-xs" style={{ color: t.muted }}>
							<label className="inline-flex items-center gap-2">
								Accent <input type="color" value={brand.accent} onChange={(e) => setBrand({ ...brand, accent: e.target.value })} style={{ width: 34, height: 22, padding: 0, border: 'none', background: 'transparent' }} />
								<code>{brand.accent}</code>
							</label>
							<label className="inline-flex items-center gap-2">
								Font
								<select value={Object.keys(BRAND_FONTS).find((k) => BRAND_FONTS[k] === brand.font) || 'System'} onChange={(e) => setBrand({ ...brand, font: BRAND_FONTS[e.target.value], heading: BRAND_FONTS[e.target.value] })} style={input}>
									{Object.keys(BRAND_FONTS).map((k) => (
										<option key={k}>{k}</option>
									))}
								</select>
							</label>
							<label className="inline-flex items-center gap-2">
								Radius <input type="range" min={0} max={16} value={brand.radius ?? 8} onChange={(e) => setBrand({ ...brand, radius: Number(e.target.value) })} /> {brand.radius}px
							</label>
							<code style={{ color: t.text }}>makeTheme({JSON.stringify({ base, accent: brand.accent, radius: brand.radius })})</code>
						</div>
					)}

					<div className="grid" style={{ gridTemplateColumns: 'repeat(12, minmax(0, 1fr))', gap: narrow ? 24 : t.flat ? 40 : 16 }}>
						<Section type="kpi" title="Stats, metric cards, gauges" block={KPI} wide />
						<Section type="gauge" title="Gauges" block={RATES} wide />
						<Section type="callouts" title="Callouts" block={CALLOUTS} wide variants={false} />
						<Section type="questions" title="Questions and viewer notes" block={QUESTIONS} wide variants={false} />
						<Section type="line" title="Line" block={LINE} />
						<Section type="heatmap" title="Activity heatmap" block={CALENDAR} />
						<Section type="datepicker" title="Date picker + area chart" block={AREA} wide variants={false}>
							<div className="mb-3 flex flex-wrap items-center gap-3">
								<DatePicker mode="range" value={range} onChange={setRange} max={END} min={DAILY[0].x} />
								<DatePicker mode="single" value={range.to} onChange={(iso: string) => setRange({ ...range, to: iso })} max={END} label="As of" />
							</div>
							<BlockView block={AREA} />
						</Section>
						<Section type="sankey" title="Sankey" block={SANKEY} />
						<Section type="treemap" title="Treemap" block={TREE} />
						<Section type="timeline" title="Timeline" block={CHANGES} />
						<Section type="bar" title="Bar with comparison" block={BAR} />
						<Section type="funnel" title="Custom: funnel" block={FUNNEL} wide />
					</div>
				</div>
				</NotesCtx.Provider>
				</NarrowCtx.Provider>
			</div>
		</ThemeCtx.Provider>
	);
}
