// Scene list for template.html, copied to SITE/video.js. This example is the agentpile 0.3.1 video (63 s, 1920x1080):
// logo.svg, overview.png and phoenix.png are copies of the project's README assets placed next to index.html.
// Durations are seconds; a terminal scene lasts as long as its typing and output take, plus `hold`.
// Patterns (focus.from, focus.to, notes[].at) are regular expressions matched against the scene's display lines.
window.VIDEO = {
  fade: 0.45,                                    // crossfade between scenes
  terminalTitle: "python3 · agentpile 0.3.1",
  theme: {accent: "#287887", mark: "#ED8D5A"},   // any CSS variable in template.html, without the leading --
  scenes: [
    {type: "title", name: "title", dur: 4.4, logo: "logo.svg", tagline: "From agent trajectory datasets and traces to the tools you already use."},
    {type: "figure", name: "overview", dur: 11.6, src: "overview.png", width: 1820, top: 40,
     reveal: [{x0: 0, x1: 0.35, at: 0.3, dur: 1.2}, {x0: 0.35, x1: 0.61, at: 2.9}, {x0: 0.61, x1: 1, at: 4.6, dur: 1.2}],
     captions: [{at: 0.4, until: 2.9, html: "<b>In:</b> 14 public datasets, trace and tool files, and live agent runs"},
                {at: 2.9, until: 4.6, html: "<b>One run record</b> for all of them, based on ATIF v1.7"},
                {at: 4.6, html: "<b>Out:</b> the tools you already use, to view, evaluate, train, audit and analyze"}]},
    {type: "terminal", name: "load", kicker: "ap.load · ap.show", title: "Load a dataset by name",
     subtitle: "14 public datasets. Every run keeps its steps, tool calls, outcome and the dataset's own labels.",
     hold: 5.4, focus: {from: "^\\s+1\\s+agent", to: "<- agent label", col0: 0, col1: 101, zoom: 1.3},
     notes: [{at: "<- agent label", dy: 1.75, col: 2, text: "Who&When's expert labels: the decisive mistake is step 1, by Excel_Expert"}]},
    {type: "terminal", name: "compare", kicker: "ap.to_pandas(runs, \"labels\")", title: "Compare failure labels across datasets",
     subtitle: "Who&When, TRAIL and MAST label failures differently. One labels table holds all three.",
     hold: 4.6, fs: 27, fit: true,
     notes: [{at: "^llm_judge", col: 40, text: "MAST, labelled by an LLM judge"},
             {at: "^trail", dy: 0.5, col: 40, text: "TRAIL: whole runs and error spans"},
             {at: "^who_and_when", dy: 1, col: 40, text: "Who&When: the agent and the step at fault"}]},
    {type: "terminal", name: "chat", kicker: "ap.to_chat(runs)", title: "Turn runs into chat rows",
     subtitle: "OpenAI-style messages for Hugging Face datasets, TRL, Ragas and DeepEval.",
     hold: 4.4, focus: {from: "'tool_calls'", to: "'tool_calls'", extra: 1, col0: 0, col1: 120},
     notes: [{at: "'tool_calls'", dy: 3.2, col: 2, text: "Tool calls stay OpenAI function calls, with their arguments"}]},
    {type: "terminal", name: "capture", kicker: "ap.capture(agent)", title: "Capture your own agent",
     subtitle: "Runs of Pydantic AI and OpenAI Agents SDK agents go into the same record.",
     hold: 3.8, paste: 3, focus: {from: "^\\s+1\\s+user", to: "^\\s+2\\s+agent", col0: 0, col1: 67},
     notes: [{at: "^\\s+2\\s+agent", col: 70, text: "The captured run, in the same record as the datasets"}]},
    {type: "image", name: "viewer", dur: 5.2, src: "phoenix.png", address: "Phoenix · localhost:6006 · a tau-bench run",
     kicker: "ap.to_otlp(run)", title: "Open any run in a viewer",
     subtitle: "Phoenix, Jaeger and MLflow through OTLP; Harbor and Inspect AI through the recipes."},
    {type: "end", name: "end", dur: 4.8, logo: "logo.svg", command: "pip install agentpile", url: "github.com/yzhao062/agentpile",
     fine: "Apache-2.0 · Python 3.9 to 3.13 · version 0.3.1"},
  ],
  // A project-specific scene: {type: "custom", name: "overview", dur: 11.6} with
  // custom: {overview: {build(spec, el) { ...; return spec.dur; }, async ready(spec, el) { /* await an iframe */ },
  //                     render(spec, el, lt) { /* set every animated property from lt alone */ }}}
  custom: {},
};
