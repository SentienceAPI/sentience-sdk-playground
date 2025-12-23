# Google Search Demo: SDK vs Vision

*A fair, simple test to compare structured data vs vision approaches*

## The Challenge

Complete a basic Google search interaction:
1. Navigate to Google.com
2. Enter search query: "visiting japan"
3. Click any non-ad link from search results

**Goal**: Keep it simple, fair, and focused on core web interaction capabilities.

---

## Why This Test Is Fair

- **Simple task**: Just search and click - no complex forms or multi-step flows
- **Universal**: Everyone knows how Google works
- **Clear success criteria**: Did you click a real search result (not an ad)?
- **Realistic**: This is what people actually do every day
- **Non-commercial**: No purchasing/shopping policy issues with OpenAI

---

## Demo 1: SDK + LLM Approach

### Flow
```
1. Navigate to https://www.google.com
2. Take snapshot → Get structured JSON (using API, use_api=True)
3. LLM identifies search input (role="textbox", searchbox)
4. Type "visiting japan"
5. Press Enter or click search button
6. Take snapshot of results → Get structured JSON (using API)
7. LLM identifies first non-ad result link
   - Filter out elements with text containing "Ad" or "Sponsored"
   - Find role="link" in main results area
8. Click the selected link
9. Verify navigation (check URL changed)
```

### Element Filtering Strategy

**Scene 1 (Find search box)**:
- Exclude: `["img", "image", "button", "link", "span", "div", "svg", "path", "g", "rect", "circle"]`
- Keep: Only interactive inputs (combobox, textbox, searchbox)
- Expected elements: 1-2 (just the search input)

**Scene 3 (Select search result)**:
- Exclude: `["searchbox", "combobox", "button", "img", "image", "span", "div", "svg", "path", "g", "rect", "circle", "ul", "li"]`
- Keep: Only links and headings (link, h3)
- Filter by text: Exclude anything with "Ad", "Sponsored", "·"
- Expected elements: 7-10 organic result links

### Expected Advantages
- **Precision**: Can identify `role="link"` vs `role="button"` vs ads
- **Filtering**: Easy to exclude ads by text content
- **Token efficiency**: Small element count with filtering
- **Verification**: Can check element properties to confirm it's a real result

---

## Demo 2: Vision + LLM Approach

### Flow
```
1. Navigate to https://www.google.com
2. Take screenshot
3. Vision LLM identifies search box coordinates
4. Click and type "visiting japan"
5. Press Enter
6. Take screenshot of results
7. Vision LLM identifies first non-ad result
   - Must visually distinguish ads from organic results
   - Must identify clickable link area
8. Click the coordinates
9. Verify navigation
```

### Expected Challenges
- **Ad detection**: Vision model must visually identify "Ad" labels
- **Coordinate precision**: Clicking the right spot on a link
- **No semantic info**: Can't tell link vs button vs text from pixels
- **Token cost**: Full page screenshots are expensive

---

## Success Criteria

### Must Complete:
- ✅ Successfully navigate to Google
- ✅ Enter "visiting japan" in search box
- ✅ Load search results page
- ✅ Identify a non-ad result
- ✅ Click the result
- ✅ Navigate to the target website (URL changes)

### Bonus Points:
- 🎯 Avoid clicking ads
- 🎯 Select a high-quality result (e.g., official tourism sites)
- 🎯 Complete in minimal tokens
- 🎯 Handle edge cases (suggestions, "People also ask", etc.)

---

## Metrics to Track

| Metric | Description |
|--------|-------------|
| **Success Rate** | Did it complete all steps? (%) |
| **Token Usage** | Total tokens across all LLM calls |
| **Runtime** | Time from start to final click (seconds) |
| **Ad Avoidance** | Did it correctly avoid clicking ads? (yes/no) |
| **Result Quality** | What site did it click? (URL) |
| **Fallbacks Used** | How many retry/fallback attempts? |

---

## Expected Results Comparison

### Token Usage (Estimated)

**Demo 1 (SDK)**:
- Scene 1: Find search box → ~500-800 tokens
- Scene 2: Select result → ~1,500-2,500 tokens (with filtering)
- **Total**: ~2,000-3,300 tokens

**Demo 2 (Vision)**:
- Scene 1: Find search box → ~1,200-1,500 tokens
- Scene 2: Select result → ~2,500-3,500 tokens
- **Total**: ~3,700-5,000 tokens

**Estimated savings**: 30-40% with SDK approach

### Ad Avoidance Accuracy

**Demo 1 (SDK)**:
- Can filter by text content ("Ad", "Sponsored")
- Can check element properties
- Expected accuracy: 95-100%

**Demo 2 (Vision)**:
- Must visually identify ad labels
- Prone to confusion with styled elements
- Expected accuracy: 70-85%

---

## Edge Cases to Handle

1. **Google's dynamic UI**
   - "People also ask" sections
   - Featured snippets
   - Knowledge panels
   - Image/video results

2. **Ad detection**
   - Sponsored results at top
   - Shopping ads
   - "Ad" labels vs "Sponsored" labels

3. **Link structure**
   - Some results are multi-line
   - URL preview vs title link
   - Nested links (title + URL)

---

## Fair Play Rules

To keep this comparison fair:

1. **Same browser/viewport**: Both demos use 1920x1080
2. **Same timing**: Same delays for page loads
3. **Same LLM**: Use GPT-4 Turbo for SDK, GPT-4o for Vision (their respective best models)
4. **No human intervention**: Fully automated, no manual debugging during runs
5. **Same search query**: "visiting japan" - neutral, non-commercial
6. **Same success criteria**: Must click a non-ad result

---

## Why Google Search Is a Good Test

### Pros:
- ✅ **Universal**: Everyone understands the task
- ✅ **Simple**: Just search and click
- ✅ **Clear pass/fail**: Either you clicked a result or you didn't
- ✅ **Real-world**: This is what people actually do
- ✅ **Policy-safe**: No shopping/automation concerns
- ✅ **Ad challenge**: Tests ability to distinguish content types

### Potential Issues:
- ⚠️ Google may show different results/layouts
- ⚠️ CAPTCHA risk (use real browser fingerprint)
- ⚠️ Regional differences (use consistent location)

---

## Implementation Checklist

### Setup
- [ ] Create `playground/demo_google_sdk/` directory
- [ ] Create `playground/demo_google_vision/` directory
- [ ] Reuse existing `token_tracker.py`, `llm_agent.py`, `vision_agent.py`
- [ ] Create `bbox_visualizer.py` for debugging (optional)

### Demo 1 (SDK)
- [ ] Scene 1: Navigate + find search box
- [ ] Scene 2: Type query + submit
- [ ] Scene 3: Select non-ad result
- [ ] Scene 4: Verify navigation
- [ ] Track tokens, capture screenshots
- [ ] Generate annotated screenshots with bboxes

### Demo 2 (Vision)
- [ ] Scene 1: Navigate + find search box
- [ ] Scene 2: Type query + submit
- [ ] Scene 3: Select non-ad result
- [ ] Scene 4: Verify navigation
- [ ] Track tokens, capture screenshots

### Comparison
- [ ] Run each demo 3 times
- [ ] Calculate average token usage
- [ ] Calculate success rate
- [ ] Document which sites were clicked
- [ ] Create comparison report

---

## Expected Outcome

**Prediction**: SDK will win, but the margin will be smaller than the Amazon demo.

**Why**:
- Google search is simpler than e-commerce
- Vision models might do okay on simple layouts
- Ad detection is the key differentiator

**Key differentiator**: Ad avoidance accuracy
- SDK can filter by text/properties → high accuracy
- Vision must visually identify ads → lower accuracy

---

## Timeline

- **Setup**: 30 minutes
- **Demo 1 (SDK)**: 1-2 hours
- **Demo 2 (Vision)**: 1-2 hours
- **Testing & comparison**: 1 hour
- **Total**: ~4-5 hours

Much faster than the Amazon demo since it's a simpler flow.

---

## Next Steps

1. Get approval for this plan
2. Set up project structure
3. Implement SDK demo first (validate approach)
4. Implement Vision demo
5. Run comparison tests (3 runs each)
6. Document results in `docs/GOOGLE_SEARCH_COMPARISON.md`

---

*Last updated: December 22, 2024*
