from flask import Flask, render_template_string, request, jsonify
import re

app = Flask(__name__)

PRODUCTS = [
    {"id":1,"name":"Wireless Bluetooth Headphones","category":"Electronics","price":1499,"original":2499,"emoji":"🎧","rating":4.5,"keywords":"headphones wireless bluetooth audio music"},
    {"id":2,"name":"Noise Wireless Earbuds","category":"Electronics","price":1299,"original":1999,"emoji":"🎵","rating":4.4,"keywords":"earbuds earphones wireless bluetooth buds"},
    {"id":3,"name":"Student Laptop 14-inch","category":"Electronics","price":32990,"original":39990,"emoji":"💻","rating":4.3,"keywords":"laptop computer students study"},
    {"id":4,"name":"Smart Watch","category":"Electronics","price":2499,"original":3999,"emoji":"⌚","rating":4.4,"keywords":"smartwatch watch fitness"},
    {"id":5,"name":"Running Sneakers","category":"Fashion","price":1799,"original":2999,"emoji":"👟","rating":4.6,"keywords":"shoes sneakers running footwear"},
    {"id":6,"name":"Air Fryer","category":"Home & Kitchen","price":3999,"original":6999,"emoji":"🍟","rating":4.3,"keywords":"air fryer kitchen cooking"},
    {"id":7,"name":"Backpack","category":"Fashion","price":999,"original":1599,"emoji":"🎒","rating":4.4,"keywords":"bag backpack school college"},
    {"id":8,"name":"Grocery Starter Pack","category":"Grocery","price":899,"original":1199,"emoji":"🛒","rating":4.2,"keywords":"groceries grocery rice cooking food"},
]
CART = []  # In-memory demo cart: resets when app restarts.

NATIVE_TERMS = {'headphones': ['हेडफोन', 'हेडफोन्स', 'హెడ్\u200cఫోన్స్', 'హెడ్\u200cఫోన్', 'ஹெட்போன்', 'हेडफोन्स', 'ಹೆಡ್\u200cಫೋನ್', 'ഹെഡ്ഫോൺ', 'হেডফোন'], 'laptops': ['लैपटॉप', 'ల్యాప్\u200cటాప్', 'லேப்டாப்', 'लॅपटॉप', 'ಲ್ಯಾಪ್\u200cಟಾಪ್', 'ലാപ്ടോപ്പ്', 'ল্যাপটপ'], 'watches': ['घड़ी', 'स्मार्टवॉच', 'వాచ్', 'గడియారం', 'கடிகாரம்', 'घड्याळ', 'ವಾಚ್', 'വാച്ച്', 'ঘড়ি'], 'earbuds': ['ईयरबड्स', 'ఇయర్\u200cబడ్స్', 'இயர்பட்ஸ்', 'ಇಯರ್\u200cಬಡ್ಸ್', 'ഇയർബഡ്സ്', 'ইয়ারবাড'], 'cart': ['कार्ट', 'కార్ట్', 'கார்ட்', 'कार्ट', 'ಕಾರ್ಟ್', 'കാർട്ട്', 'কার্ট']}
ADD_TERMS = ('जोड़', 'डाल', 'చేర్చ', 'వెయ్యి', 'சேர்', 'जोड', 'ಸೇರಿಸ', 'ചേർക്ക', 'যোগ')
COMPARE_TERMS = ('तुलना', 'పోల్చ', 'ஒப்பிட', 'तुलना', 'ಹೋಲಿಸ', 'താരതമ്യം', 'তুলনা')
def normalize_voice(text):
    result = text.lower()
    for english, variants in NATIVE_TERMS.items():
        for token in variants:
            result = result.replace(token.lower(), ' ' + english + ' ')
    if any(x in result for x in ('లోపు','కంటే తక్కువ','से कम','के अंदर','க்குள்','खाली','ಒಳಗೆ','കുറഞ്ഞ','মধ্যে')):
        result = ' under ' + result
    if any(x in result for x in ADD_TERMS):
        result = 'add to cart ' + result
    if any(x in result for x in COMPARE_TERMS):
        result = 'compare ' + result
    return result


def parse_budget(text):
    match = re.search(r'(?:under|below|less than|within|upto|up to)\s*(?:rs\.?|rupees|₹)?\s*([\d,]+)', text, re.I)
    if match:
        return int(match.group(1).replace(',', ''))
    native = re.search(r'([\d,]+)\s*(?:रुपये|रुपय|रूपये|రూపాయల|రూపాయలు|ரூபாய்|रुपयांच्या|ರೂಪಾಯಿ|രൂപ|টাকা)', text, re.I)
    return int(native.group(1).replace(',', '')) if native and 'under' in text.lower() else None

def match_products(command):
    lower = command.lower()
    budget = parse_budget(lower)
    stop = {'alexa','alexa+','smartbazaar','show','me','find','search','for','best','top','a','an','the','some','please','i','want','need','to','buy','compare','products','product','deals','deal','cheap','price','prices','under','below','less','than','within','up','rupees','rs','of','my','and','add','cart','order','recommend','good','student','students'}
    tokens = [x for x in re.findall(r'[a-z]+', lower) if x not in stop]
    budget_only = not tokens and budget is not None
    scored = []
    for p in PRODUCTS:
        hay = (p['name']+' '+p['category']+' '+p['keywords']).lower()
        score = sum(1 for token in tokens if token in hay)
        if (score or budget_only or not tokens) and (budget is None or p['price'] <= budget):
            scored.append((score,p))
    return [p for _,p in sorted(scored,key=lambda x:(-x[0],x[1]['price']))][:6]

def enriched_products(items):
    result = []
    for item in items:
        product = dict(item)
        product['discount_percent'] = round(100 * (product['original'] - product['price']) / product['original'])
        product['savings'] = product['original'] - product['price']
        result.append(product)
    return result


def recommend_products(category='All', budget=None, priority='balanced'):
    """Transparent, rule-based ranking over local demo products (no paid AI API)."""
    candidates = [p for p in enriched_products(PRODUCTS)
                  if (category == 'All' or p['category'] == category)
                  and (budget is None or p['price'] <= budget)]
    if not candidates:
        return []
    max_price = max(p['price'] for p in candidates) or 1
    for p in candidates:
        deal = p['discount_percent'] / 100
        quality = p['rating'] / 5
        affordability = 1 - p['price'] / max_price
        if priority == 'lowest-price':
            score = .75 * affordability + .15 * quality + .10 * deal
            reason = 'Budget-friendly choice'
        elif priority == 'top-rated':
            score = .75 * quality + .15 * deal + .10 * affordability
            reason = f'Highly rated: {p["rating"]}/5'
        elif priority == 'biggest-deal':
            score = .75 * deal + .15 * quality + .10 * affordability
            reason = f'Save {p["discount_percent"]}% on demo price'
        else:
            score = .45 * quality + .35 * deal + .20 * affordability
            reason = f'{p["rating"]}/5 rating and {p["discount_percent"]}% demo discount'
        p['recommendation_score'] = round(score * 100)
        p['why_recommended'] = reason
    return sorted(candidates, key=lambda p: (-p['recommendation_score'], p['price'], p['id']))


@app.route('/api/recommendations')
def recommendations():
    category = request.args.get('category', 'All')
    if category not in {'All', *(p['category'] for p in PRODUCTS)}:
        return jsonify(error='Invalid category'), 400
    priority = request.args.get('priority', 'balanced')
    if priority not in {'balanced', 'lowest-price', 'top-rated', 'biggest-deal'}:
        return jsonify(error='Invalid priority'), 400
    raw = request.args.get('budget', '').strip()
    if raw and (not raw.isdigit() or not 1 <= int(raw) <= 10000000):
        return jsonify(error='Budget must be between 1 and 10000000'), 400
    budget = int(raw) if raw else None
    ranked = recommend_products(category, budget, priority)
    return jsonify(products=ranked[:8], total=len(ranked), demo=True, algorithm='Transparent local demo ranking')


@app.route('/api/compare', methods=['POST'])
def compare():
    values = (request.get_json(silent=True) or {}).get('ids', [])
    if not isinstance(values, list) or len(values) != 2 or any(type(i) is not int for i in values) or values[0] == values[1]:
        return jsonify(error='Select two different products'), 400
    chosen = [next((p for p in enriched_products(PRODUCTS) if p['id'] == i), None) for i in values]
    if any(p is None for p in chosen):
        return jsonify(error='Product not found'), 404
    a, b = chosen
    cheaper = a if a['price'] <= b['price'] else b
    rated = a if a['rating'] >= b['rating'] else b
    return jsonify(products=chosen,
                   summary=f'{cheaper["name"]} costs less (₹{cheaper["price"]:,}). '
                           f'{rated["name"]} has the higher customer-style demo rating ({rated["rating"]}/5).',
                   demo=True)


@app.route('/')
def home():
    return render_template_string(HTML)

@app.route('/api/products')
def products():
    return jsonify(PRODUCTS)

@app.route('/api/voice', methods=['POST'])
def voice():
    command = str((request.get_json(silent=True) or {}).get('command','')).strip()[:250]
    if not command:
        return jsonify(reply='Please say a shopping command.',products=[],cart_count=len(CART))
    lower = normalize_voice(command)
    if 'cart' in lower and any(k in lower for k in ('show','view','open','what','my cart')):
        return jsonify(reply=f'Your demo cart contains {len(CART)} item(s).', products=CART,cart_count=len(CART),mode='cart')
    if 'clear cart' in lower:
        CART.clear()
        return jsonify(reply='Your demo cart has been cleared.',products=[],cart_count=0,mode='cart')
    if any(k in lower for k in ('add to cart','add the','buy this','add it')):
        possible = match_products(lower)
        if not possible:
            return jsonify(reply='No matching product to add. Please name a product.', products=[],cart_count=len(CART))
        product = possible[0]
        CART.append(product)
        return jsonify(reply=f'Added {product["name"]} to your demo cart for {product["price"]} rupees.',products=[product],cart_count=len(CART),mode='cart')
    results = match_products(lower)
    if not results:
        return jsonify(reply='I could not find matching demo products. Try a different keyword or budget.',products=[],cart_count=len(CART))
    intro = 'Here are the best matching demo products.'
    if 'compare' in lower:
        intro = 'Here are options to compare by price and rating.'
    elif 'deal' in lower:
        intro = 'Here are some deals from the demo catalog.'
    return jsonify(reply=intro+f' The first result is {results[0]["name"]} at {results[0]["price"]} rupees.',products=results,cart_count=len(CART))

HTML = r'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>SmartBazaar AI | Voice Shopping</title>
<style>
:root{--dark:#07152f;--dark2:#0c2650;--blue:#176fff;--orange:#ff8c1a;--ink:#15233d;--muted:#60718f;--bg:#f2f7fe}*{box-sizing:border-box}body{margin:0;font-family:Inter,Segoe UI,Arial,sans-serif;background:var(--bg);color:var(--ink)}header{display:flex;align-items:center;justify-content:space-between;padding:18px max(5%,20px);background:var(--dark);color:white;gap:16px;flex-wrap:wrap}.brand{font-weight:850;font-size:26px;letter-spacing:-1px}.brand span{color:var(--orange)}.top{display:flex;gap:18px;font-size:14px;align-items:center}.cart{padding:10px 16px;border:1px solid #526482;border-radius:30px}main{max-width:1360px;margin:auto;padding:28px 24px}.hero{background:radial-gradient(circle at 78% 45%,#245eb8 0,transparent 33%),linear-gradient(115deg,#06152d 10%,#0e2a57 100%);min-height:410px;border-radius:24px;color:white;display:grid;grid-template-columns:1.05fr .95fr;align-items:center;padding:52px;gap:20px;box-shadow:0 18px 48px #0b316130}.eyebrow{color:#9cc9ff;font-size:13px;font-weight:750;letter-spacing:2px;text-transform:uppercase}.hero h1{font-size:clamp(32px,4.2vw,59px);line-height:1.09;margin:18px 0}.hero h1 em{color:var(--orange);font-style:normal}.hero p{color:#c7d9f3;font-size:18px;line-height:1.6;max-width:535px}.cta{border:0;border-radius:14px;background:linear-gradient(110deg,#ff9b28,#ff6c0c);color:#081a34;font-size:17px;font-weight:800;padding:17px 27px;cursor:pointer;box-shadow:0 7px 25px #ff7b203a}.cta:hover{filter:brightness(1.09)}.hero-visual{text-align:center}.orb{width:210px;height:210px;margin:0 auto 25px;border-radius:50%;background:radial-gradient(circle at 34% 24%,#52647a,#0b1426 63%);box-shadow:inset -25px -30px 42px #020815,0 28px 40px #030e25;position:relative}.orb:after{content:'';position:absolute;left:10%;right:10%;bottom:18px;height:9px;border-radius:50%;background:#00d6ff;box-shadow:0 0 21px #00baff,0 0 32px #0087ff}.mic-status{display:inline-block;padding:13px 23px;border-radius:40px;background:#0d3973;border:1px solid #4b94ff;color:#ebf5ff;font-weight:700}.speech{color:#c5e4ff;font-size:14px;margin-top:14px}.section{margin-top:29px}.section h2{font-size:23px;margin:0 0 15px}.commands{display:grid;grid-template-columns:repeat(4,1fr);gap:14px}.command{background:white;border:1px solid #dce7f4;padding:19px;text-align:left;border-radius:15px;cursor:pointer;font-size:14px;line-height:1.5;box-shadow:0 5px 20px #0b2a4a09;min-height:113px}.command strong{display:block;color:#0a4db7;margin-bottom:8px}.command:hover{border-color:#2774f8;transform:translateY(-2px)}.resultbar{display:flex;gap:14px;justify-content:space-between;align-items:center;flex-wrap:wrap}.status{background:#e1ecff;color:#21559c;border-radius:30px;padding:10px 14px;font-size:13px}.products{display:grid;grid-template-columns:repeat(4,1fr);gap:15px;margin-top:16px}.product{background:white;border:1px solid #dce6f3;border-radius:17px;overflow:hidden;box-shadow:0 8px 25px #1734520b}.product .picture{height:135px;background:linear-gradient(145deg,#f5f9ff,#dceaff);display:grid;place-items:center;font-size:68px}.product .info{padding:16px}.product strong{font-size:15px}.price{font-size:22px;font-weight:850;margin:9px 0}.price s{font-weight:400;color:#8191a8;font-size:14px;margin-left:6px}.muted{font-size:13px;color:#64809f}.product button{padding:9px 14px;margin-top:13px;color:white;background:#ef7b13;border:0;border-radius:9px;cursor:pointer}.response{padding:17px 20px;background:#eaf3ff;border-left:5px solid #1576ed;border-radius:12px;line-height:1.5}.how{display:grid;grid-template-columns:repeat(4,1fr);gap:14px}.step{padding:20px;border-radius:15px;background:white;border:1px solid #dfebf9}.step b{color:#0767c9}.note{font-size:13px;color:#61718a;line-height:1.65;margin:28px 0}.mobile-only{display:none}@media(max-width:950px){.hero{grid-template-columns:1fr;padding:35px}.commands,.products,.how{grid-template-columns:repeat(2,1fr)}.orb{width:150px;height:150px}.top{display:none}}@media(max-width:550px){main{padding:16px}.hero{padding:27px}.hero h1{font-size:34px}.commands,.products,.how{grid-template-columns:1fr}.brand{font-size:22px}.hero p{font-size:16px}.product .picture{height:115px}}
.recommend-panel{background:white;border:1px solid #dce7f4;border-radius:20px;padding:23px;box-shadow:0 8px 25px #1734520b}.filters{display:flex;flex-wrap:wrap;gap:12px;align-items:end}.field{display:flex;flex-direction:column;gap:6px;flex:1;min-width:155px}.field label{font-size:12px;font-weight:750;color:#405a7b}.field select,.field input{background:#f8fbff;border:1px solid #c9d9ec;border-radius:10px;padding:12px;font-size:14px;color:#15233d;width:100%}.secondary-btn{background:#1165d8;color:#fff;border:0;border-radius:10px;font-weight:750;padding:12px 18px;cursor:pointer}.secondary-btn:disabled{opacity:.45;cursor:not-allowed}.reco-products{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:14px;margin-top:18px}.reco-card{border:1px solid #dce6f3;border-radius:15px;padding:15px;background:#fbfdff;min-width:0}.reco-icon{font-size:44px;text-align:center;background:#eaf2ff;border-radius:12px;padding:15px}.reco-card h3{font-size:15px;margin:13px 0 7px}.why{color:#1464c5;font-size:12px;min-height:35px}.reco-card .price{font-size:20px}.reco-card button{padding:9px 12px;background:#082b60;color:white;border:0;border-radius:8px;cursor:pointer}.compare-panel{padding:17px;background:#edf5ff;border:1px solid #cbdff8;border-radius:14px;margin-top:18px}.compare-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:12px}.compare-cell{background:white;border-radius:11px;padding:14px}.help-copy{color:#61718a;font-size:13px;line-height:1.5;margin-top:10px}@media(max-width:950px){.reco-products{grid-template-columns:repeat(2,minmax(0,1fr))}}@media(max-width:550px){.reco-products,.compare-grid{grid-template-columns:1fr}}.hero-search{display:flex;align-items:center;gap:9px;background:white;padding:7px 7px 7px 16px;border-radius:14px;max-width:560px;margin:22px 0 4px;box-shadow:0 8px 25px #0010224d}.hero-search .search-icon{font-size:26px;color:#52739e;line-height:1}.hero-search input{flex:1;min-width:0;border:0;outline:0;background:white;color:#10233e;font:inherit;font-size:15px;padding:12px 3px}.hero-search button{border:0;background:#ff891a;color:#06172e;font-weight:800;font-size:15px;border-radius:10px;padding:13px 19px;cursor:pointer}.hero-search button:hover{background:#ffab49}.hero .search-helper{font-size:13px;margin:5px 0 17px;color:#a9cffc}.sr-only{position:absolute;width:1px;height:1px;padding:0;margin:-1px;overflow:hidden;clip:rect(0,0,0,0);white-space:nowrap;border:0}@media(max-width:550px){.hero-search{padding:5px 5px 5px 10px}.hero-search input{font-size:13px}.hero-search button{font-size:13px;padding:12px}}</style></head><body>
<header><div class="brand">🛒 Smart<span>Bazaar</span> AI</div><div class="top"><label for="langSelect" id="langLabel" style="font-weight:700">Language</label><select id="langSelect" aria-label="Language" onchange="changeLanguage(this.value)" style="border-radius:9px;padding:8px;background:#fff;color:#091b36"><option value="en-IN">English</option><option value="hi-IN">हिन्दी</option><option value="te-IN">తెలుగు</option><option value="ta-IN">தமிழ்</option><option value="mr-IN">मराठी</option><option value="kn-IN">ಕನ್ನಡ</option><option value="ml-IN">മലയാളം</option><option value="bn-IN">বাংলা</option></select><span id="navVoice">🎙️ Voice Shopping</span><span id="navReco">✨ AI Recommendations</span><span class="cart"><span id="navCart">🛒 Demo Cart</span> <b id="cartCount">0</b></span></div></header>
<main><section class="hero"><div><div class="eyebrow">Amazon Developer Hackathon · Voice-first demo</div><h1><span id="heroStart">Shop Smarter with</span> <em id="heroAccent">Alexa+ Voice</em></h1><p><span id="heroDescription">Say what you want. Discover products, compare prices and add items to your demo cart — all through voice.</span></p><form class="hero-search" id="productSearchForm" onsubmit="searchProducts(event)" role="search"><label class="sr-only" for="productSearchInput" id="productSearchLabel">Search products</label><span class="search-icon" aria-hidden="true">⌕</span><input type="search" id="productSearchInput" autocomplete="off" placeholder="Search products, e.g. headphones under 2000" required maxlength="150"><button type="submit" id="productSearchButton">Search</button></form><p class="search-helper" id="searchHelper">Type a product or budget here, or shop using your voice.</p><button class="cta" id="listenBtn" onclick="listen()"><span id="listenText">🎙️ Start Voice Shopping</span></button><p style="font-size:13px">Or choose a sample voice command below.</p></div><div class="hero-visual"><div class="orb"></div><div class="mic-status" id="micStatus">🎙️ Ready to listen</div><div class="speech" id="heard">“Find headphones under 2000 rupees”</div></div></section>
<section class="section"><h2><span id="commandsTitle">🎙️ Popular Voice Commands</span></h2><div class="commands"><button class="command" onclick="runCommand('Find headphones under 2000 rupees')"><strong><span id="cmdTitle0">Search by voice</span></strong>“Find headphones under 2000 rupees”</button><button class="command" onclick="runCommand('Compare laptops for students')"><strong><span id="cmdTitle1">Compare products</span></strong>“Compare laptops for students”</button><button class="command" onclick="runCommand('Show best deals on smart watches')"><strong><span id="cmdTitle2">Discover deals</span></strong>“Show best deals on smart watches”</button><button class="command" onclick="runCommand('Add headphones to cart')"><strong><span id="cmdTitle3">Voice cart</span></strong>“Add headphones to cart”</button></div></section>
<section class="section"><div class="resultbar"><h2><span id="resultsTitle">🔎 Live Voice Search Results</span></h2><span class="status" id="queryLabel">Sample demo catalog</span></div><div class="response" aria-live="polite" id="reply">Welcome to SmartBazaar AI! Tap the microphone to start shopping with your voice.</div><div class="products" id="products"></div></section>
<section class="section" id="recommendations"><h2><span id="recoTitle">✨ Smart Product Recommendations</span></h2><div class="recommend-panel"><div class="filters"><div class="field"><label for="category">Product category</label><select id="category"><option>All</option><option>Electronics</option><option>Fashion</option><option>Home &amp; Kitchen</option><option>Grocery</option></select></div><div class="field"><label for="budget">Maximum budget (₹, optional)</label><input id="budget" type="number" min="1" max="10000000" placeholder="e.g. 2000"></div><div class="field"><label for="priority">What matters most?</label><select id="priority"><option value="balanced">Best overall value</option><option value="lowest-price">Lowest price</option><option value="top-rated">Highest rating</option><option value="biggest-deal">Biggest discount</option></select></div><button class="secondary-btn" onclick="loadRecommendations()"><span id="picksText">✨ Find My Picks</span></button></div><p class="help-copy" id="reco-status">Ranked from our demo product catalog. Recommendations use transparent price, discount and rating scores.</p><div class="reco-products" id="reco-products"></div><div class="compare-panel"><strong><span id="compareTitle">⚖️ Compare two products</span></strong><p class="help-copy">Select two products using “Compare” on their cards.</p><button id="compareBtn" class="secondary-btn" onclick="runCompare()" disabled>Compare selected (0/2)</button><div id="compareResults" aria-live="polite"></div></div></div></section>
<section class="section"><h2><span id="howTitle">⚡ How voice shopping works</span></h2><div class="how"><div class="step"><b>01 · Speak</b><p>Tell SmartBazaar AI what you need.</p></div><div class="step"><b>02 · Understand</b><p>Your voice is transcribed by your browser.</p></div><div class="step"><b>03 · Discover</b><p>A simple product matcher finds demo products.</p></div><div class="step"><b>04 · Add to cart</b><p>Use your voice to add a matching item to a demo cart.</p></div></div></section>
<p class="note"><b>Hackathon demo disclosure:</b> This one-file prototype uses browser SpeechRecognition and speech synthesis, Flask, and sample local product data. It is <b>not</b> connected to the Amazon Alexa+ service, Amazon's live shopping catalog, payments or real order placement. Browser microphone access generally requires localhost or HTTPS. Chrome/Edge support varies; the sample-command buttons work without a microphone.</p></main>
<script>

const I18N = {"en-IN": {"language": "English", "voice": "Voice Shopping", "recommendations": "AI Recommendations", "cart": "Demo Cart", "heroStart": "Shop Smarter with", "heroAccent": "Alexa+ Voice", "heroDescription": "Say what you want. Discover products, compare prices and add items to your demo cart — all through voice.", "start": "Start Voice Shopping", "commands": "Popular Voice Commands", "search": "Search by voice", "compare": "Compare products", "deals": "Discover deals", "voiceCart": "Voice cart", "results": "Live Voice Search Results", "smartReco": "Smart Product Recommendations", "category": "Product category", "budget": "Maximum budget (₹, optional)", "priority": "What matters most?", "picks": "Find My Picks", "compareTwo": "Compare two products", "compareSelected": "Compare selected", "how": "How voice shopping works", "speak": "Speak", "understand": "Understand", "discover": "Discover", "add": "Add to cart", "ready": "Ready to listen", "welcome": "Welcome to SmartBazaar AI! Choose a sample command or use your microphone.", "selectLanguage": "Select language", "noProducts": "No matching products in this demo catalog.", "addByVoice": "Add by voice command", "processing": "Processing request", "nextReady": "Ready for next command"}, "hi-IN": {"language": "हिन्दी", "voice": "वॉइस शॉपिंग", "recommendations": "AI सुझाव", "cart": "डेमो कार्ट", "heroStart": "समझदारी से खरीदारी करें", "heroAccent": "Alexa+ वॉइस से", "heroDescription": "बोलकर उत्पाद खोजें, कीमतों की तुलना करें और डेमो कार्ट में जोड़ें।", "start": "वॉइस शॉपिंग शुरू करें", "commands": "लोकप्रिय वॉइस कमांड", "search": "आवाज़ से खोजें", "compare": "उत्पाद तुलना", "deals": "ऑफ़र खोजें", "voiceCart": "वॉइस कार्ट", "results": "वॉइस खोज के नतीजे", "smartReco": "स्मार्ट उत्पाद सुझाव", "category": "उत्पाद श्रेणी", "budget": "अधिकतम बजट (₹)", "priority": "आपकी प्राथमिकता?", "picks": "मेरे लिए चुनें", "compareTwo": "दो उत्पादों की तुलना", "compareSelected": "चुने हुए की तुलना", "how": "वॉइस शॉपिंग कैसे काम करती है", "speak": "बोलें", "understand": "समझें", "discover": "खोजें", "add": "कार्ट में जोड़ें", "ready": "सुनने के लिए तैयार", "welcome": "SmartBazaar AI में आपका स्वागत है! कोई नमूना कमांड चुनें।", "selectLanguage": "भाषा चुनें", "noProducts": "इस डेमो में कोई उत्पाद नहीं मिला।", "addByVoice": "कार्ट में जोड़ने का आदेश", "processing": "अनुरोध जारी है", "nextReady": "अगले आदेश के लिए तैयार"}, "te-IN": {"language": "తెలుగు", "voice": "వాయిస్ షాపింగ్", "recommendations": "AI సిఫార్సులు", "cart": "డెమో కార్ట్", "heroStart": "తెలివిగా షాపింగ్ చేయండి", "heroAccent": "Alexa+ వాయిస్‌తో", "heroDescription": "మాట్లాడి ఉత్పత్తులు వెతకండి, ధరలు పోల్చండి, డెమో కార్ట్‌లో చేర్చండి.", "start": "వాయిస్ షాపింగ్ ప్రారంభించండి", "commands": "ప్రసిద్ధ వాయిస్ ఆదేశాలు", "search": "వాయిస్‌తో వెతకండి", "compare": "ఉత్పత్తులను పోల్చండి", "deals": "ఆఫర్లు చూడండి", "voiceCart": "వాయిస్ కార్ట్", "results": "వాయిస్ శోధన ఫలితాలు", "smartReco": "స్మార్ట్ ఉత్పత్తి సిఫార్సులు", "category": "ఉత్పత్తి వర్గం", "budget": "గరిష్ఠ బడ్జెట్ (₹)", "priority": "మీ ప్రాధాన్యత?", "picks": "నాకు సరిపడేవి చూపండి", "compareTwo": "రెండు ఉత్పత్తులను పోల్చండి", "compareSelected": "ఎంచుకున్నవి పోల్చండి", "how": "వాయిస్ షాపింగ్ విధానం", "speak": "మాట్లాడండి", "understand": "అర్థం చేసుకోండి", "discover": "కనుగొనండి", "add": "కార్ట్‌లో చేర్చండి", "ready": "వినడానికి సిద్ధం", "welcome": "SmartBazaar AIకి స్వాగతం! నమూనా ఆదేశాన్ని ఎంచుకోండి.", "selectLanguage": "భాష ఎంచుకోండి", "noProducts": "ఈ డెమోలో సరిపడే ఉత్పత్తులు లేవు.", "addByVoice": "కార్ట్‌లో చేర్చే ఆదేశం", "processing": "అభ్యర్థన ప్రాసెస్ అవుతోంది", "nextReady": "తదుపరి ఆదేశానికి సిద్ధం"}, "ta-IN": {"language": "தமிழ்", "voice": "குரல் ஷாப்பிங்", "recommendations": "AI பரிந்துரைகள்", "cart": "டெமோ கார்ட்", "heroStart": "புத்திசாலித்தனமாக வாங்குங்கள்", "heroAccent": "Alexa+ குரலுடன்", "heroDescription": "பேசி பொருட்களைத் தேடி, விலையை ஒப்பிட்டு கார்டில் சேருங்கள்.", "start": "குரல் ஷாப்பிங்கைத் தொடங்கு", "commands": "பிரபலமான குரல் கட்டளைகள்", "search": "குரலில் தேடு", "compare": "பொருட்களை ஒப்பிடு", "deals": "சலுகைகளைக் காண்", "voiceCart": "குரல் கார்ட்", "results": "குரல் தேடல் முடிவுகள்", "smartReco": "சிறந்த பொருள் பரிந்துரைகள்", "category": "பொருள் வகை", "budget": "அதிகபட்ச பட்ஜெட் (₹)", "priority": "முக்கியத்துவம் எதற்கு?", "picks": "எனக்கான தேர்வுகள்", "compareTwo": "இரண்டு பொருட்களை ஒப்பிடு", "compareSelected": "தேர்ந்தவற்றை ஒப்பிடு", "how": "குரல் ஷாப்பிங் எப்படி வேலை செய்கிறது", "speak": "பேசுங்கள்", "understand": "புரிந்துகொள்ளுங்கள்", "discover": "கண்டறியுங்கள்", "add": "கார்டில் சேருங்கள்", "ready": "கேட்கத் தயார்", "welcome": "SmartBazaar AIக்கு வரவேற்கிறோம்! மாதிரி கட்டளையைத் தேர்வு செய்யுங்கள்.", "selectLanguage": "மொழியைத் தேர்வு செய்", "noProducts": "பொருந்தும் பொருட்கள் இல்லை.", "addByVoice": "கார்டில் சேர்க்கும் கட்டளை", "processing": "செயலாக்கம் நடைபெறுகிறது", "nextReady": "அடுத்த கட்டளைக்குத் தயார்"}, "mr-IN": {"language": "मराठी", "voice": "व्हॉइस शॉपिंग", "recommendations": "AI शिफारसी", "cart": "डेमो कार्ट", "heroStart": "स्मार्ट खरेदी करा", "heroAccent": "Alexa+ आवाजासह", "heroDescription": "बोलून उत्पादने शोधा, किमतींची तुलना करा आणि कार्टमध्ये जोडा.", "start": "व्हॉइस शॉपिंग सुरू करा", "commands": "लोकप्रिय व्हॉइस कमांड", "search": "आवाजाने शोधा", "compare": "उत्पादन तुलना", "deals": "ऑफर्स शोधा", "voiceCart": "व्हॉइस कार्ट", "results": "व्हॉइस शोध निकाल", "smartReco": "स्मार्ट उत्पादन शिफारसी", "category": "उत्पादन प्रकार", "budget": "कमाल बजेट (₹)", "priority": "तुमची प्राथमिकता?", "picks": "माझ्यासाठी निवडा", "compareTwo": "दोन उत्पादनांची तुलना", "compareSelected": "निवडलेल्यांची तुलना", "how": "व्हॉइस शॉपिंग कसे चालते", "speak": "बोला", "understand": "समजून घ्या", "discover": "शोधा", "add": "कार्टमध्ये जोडा", "ready": "ऐकण्यासाठी तयार", "welcome": "SmartBazaar AI मध्ये स्वागत! नमुना कमांड निवडा.", "selectLanguage": "भाषा निवडा", "noProducts": "जुळणारी उत्पादने नाहीत.", "addByVoice": "कार्टमध्ये जोडण्याची कमांड", "processing": "प्रक्रिया सुरू आहे", "nextReady": "पुढील आदेशासाठी तयार"}, "kn-IN": {"language": "ಕನ್ನಡ", "voice": "ಧ್ವನಿ ಶಾಪಿಂಗ್", "recommendations": "AI ಶಿಫಾರಸುಗಳು", "cart": "ಡೆಮೊ ಕಾರ್ಟ್", "heroStart": "ಸ್ಮಾರ್ಟ್ ಶಾಪಿಂಗ್ ಮಾಡಿ", "heroAccent": "Alexa+ ಧ್ವನಿಯೊಂದಿಗೆ", "heroDescription": "ಮಾತಿನ ಮೂಲಕ ಉತ್ಪನ್ನಗಳನ್ನು ಹುಡುಕಿ, ಬೆಲೆ ಹೋಲಿಸಿ, ಕಾರ್ಟ್‌ಗೆ ಸೇರಿಸಿ.", "start": "ಧ್ವನಿ ಶಾಪಿಂಗ್ ಪ್ರಾರಂಭಿಸಿ", "commands": "ಜನಪ್ರಿಯ ಧ್ವನಿ ಆಜ್ಞೆಗಳು", "search": "ಧ್ವನಿಯಿಂದ ಹುಡುಕಿ", "compare": "ಉತ್ಪನ್ನ ಹೋಲಿಕೆ", "deals": "ಆಫರ್‌ಗಳನ್ನು ಹುಡುಕಿ", "voiceCart": "ಧ್ವನಿ ಕಾರ್ಟ್", "results": "ಧ್ವನಿ ಹುಡುಕಾಟ ಫಲಿತಾಂಶಗಳು", "smartReco": "ಸ್ಮಾರ್ಟ್ ಉತ್ಪನ್ನ ಶಿಫಾರಸುಗಳು", "category": "ಉತ್ಪನ್ನ ವರ್ಗ", "budget": "ಗರಿಷ್ಠ ಬಜೆಟ್ (₹)", "priority": "ನಿಮ್ಮ ಆದ್ಯತೆ?", "picks": "ನನಗೆ ತೋರಿಸಿ", "compareTwo": "ಎರಡು ಉತ್ಪನ್ನ ಹೋಲಿಸಿ", "compareSelected": "ಆಯ್ಕೆಯ ಹೋಲಿಕೆ", "how": "ಧ್ವನಿ ಶಾಪಿಂಗ್ ಹೇಗೆ ಕೆಲಸ ಮಾಡುತ್ತದೆ", "speak": "ಮಾತನಾಡಿ", "understand": "ಅರ್ಥಮಾಡಿಕೊಳ್ಳಿ", "discover": "ಹುಡುಕಿ", "add": "ಕಾರ್ಟ್‌ಗೆ ಸೇರಿಸಿ", "ready": "ಕೇಳಲು ಸಿದ್ಧ", "welcome": "SmartBazaar AIಗೆ ಸ್ವಾಗತ! ಮಾದರಿ ಆಜ್ಞೆ ಆಯ್ಕೆಮಾಡಿ.", "selectLanguage": "ಭಾಷೆ ಆಯ್ಕೆ", "noProducts": "ಹೊಂದುವ ಉತ್ಪನ್ನಗಳಿಲ್ಲ.", "addByVoice": "ಕಾರ್ಟ್‌ಗೆ ಸೇರಿಸುವ ಆಜ್ಞೆ", "processing": "ಪ್ರಕ್ರಿಯೆ ನಡೆಯುತ್ತಿದೆ", "nextReady": "ಮುಂದಿನ ಆಜ್ಞೆಗೆ ಸಿದ್ಧ"}, "ml-IN": {"language": "മലയാളം", "voice": "വോയ്സ് ഷോപ്പിംഗ്", "recommendations": "AI ശുപാർശകൾ", "cart": "ഡെമോ കാർട്ട്", "heroStart": "സ്മാർട്ടായി ഷോപ്പ് ചെയ്യൂ", "heroAccent": "Alexa+ വോയ്സിലൂടെ", "heroDescription": "പറഞ്ഞ് ഉൽപ്പന്നങ്ങൾ തിരയൂ, വില താരതമ്യം ചെയ്ത് കാർട്ടിൽ ചേർക്കൂ.", "start": "വോയ്സ് ഷോപ്പിംഗ് തുടങ്ങൂ", "commands": "ജനപ്രിയ വോയ്സ് കമാൻഡുകൾ", "search": "ശബ്ദത്തിൽ തിരയൂ", "compare": "ഉൽപ്പന്ന താരതമ്യം", "deals": "ഓഫറുകൾ കണ്ടെത്തൂ", "voiceCart": "വോയ്സ് കാർട്ട്", "results": "വോയ്സ് തിരയൽ ഫലങ്ങൾ", "smartReco": "സ്മാർട്ട് ഉൽപ്പന്ന ശുപാർശകൾ", "category": "ഉൽപ്പന്ന വിഭാഗം", "budget": "പരമാവധി ബജറ്റ് (₹)", "priority": "നിങ്ങളുടെ മുൻഗണന?", "picks": "എനിക്ക് തിരഞ്ഞെടുക്കൂ", "compareTwo": "രണ്ട് ഉൽപ്പന്നങ്ങൾ താരതമ്യം", "compareSelected": "തിരഞ്ഞെടുത്തവ താരതമ്യം", "how": "വോയ്സ് ഷോപ്പിംഗ് എങ്ങനെ പ്രവർത്തിക്കുന്നു", "speak": "പറയൂ", "understand": "മനസ്സിലാക്കൂ", "discover": "കണ്ടെത്തൂ", "add": "കാർട്ടിൽ ചേർക്കൂ", "ready": "കേൾക്കാൻ തയ്യാർ", "welcome": "SmartBazaar AIയിലേക്ക് സ്വാഗതം! മാതൃക കമാൻഡ് തിരഞ്ഞെടുക്കൂ.", "selectLanguage": "ഭാഷ തിരഞ്ഞെടുക്കൂ", "noProducts": "ചേരുന്ന ഉൽപ്പന്നങ്ങളില്ല.", "addByVoice": "കാർട്ടിൽ ചേർക്കാനുള്ള കമാൻഡ്", "processing": "പ്രക്രിയ നടക്കുന്നു", "nextReady": "അടുത്ത കമാൻഡിന് തയ്യാർ"}, "bn-IN": {"language": "বাংলা", "voice": "ভয়েস শপিং", "recommendations": "AI সুপারিশ", "cart": "ডেমো কার্ট", "heroStart": "স্মার্টভাবে কেনাকাটা করুন", "heroAccent": "Alexa+ ভয়েস দিয়ে", "heroDescription": "কথা বলে পণ্য খুঁজুন, দাম তুলনা করুন এবং কার্টে যোগ করুন।", "start": "ভয়েস শপিং শুরু করুন", "commands": "জনপ্রিয় ভয়েস কমান্ড", "search": "কণ্ঠে খুঁজুন", "compare": "পণ্য তুলনা", "deals": "অফার খুঁজুন", "voiceCart": "ভয়েস কার্ট", "results": "ভয়েস অনুসন্ধানের ফল", "smartReco": "স্মার্ট পণ্য সুপারিশ", "category": "পণ্যের বিভাগ", "budget": "সর্বোচ্চ বাজেট (₹)", "priority": "কোনটি গুরুত্বপূর্ণ?", "picks": "আমার জন্য বাছুন", "compareTwo": "দুটি পণ্যের তুলনা", "compareSelected": "নির্বাচিত পণ্যের তুলনা", "how": "ভয়েস শপিং কীভাবে কাজ করে", "speak": "বলুন", "understand": "বুঝুন", "discover": "খুঁজুন", "add": "কার্টে যোগ করুন", "ready": "শোনার জন্য প্রস্তুত", "welcome": "SmartBazaar AI-তে স্বাগতম! একটি নমুনা কমান্ড বেছে নিন।", "selectLanguage": "ভাষা বেছে নিন", "noProducts": "এই ডেমোতে মেলানো পণ্য নেই।", "addByVoice": "কার্টে যোগের কমান্ড", "processing": "অনুরোধ চলছে", "nextReady": "পরবর্তী কমান্ডের জন্য প্রস্তুত"}};
const DEMOS = {
 'en-IN':['Find headphones under 2000 rupees','Compare laptops for students','Show best deals on smart watches','Add headphones to cart'],
 'hi-IN':['2000 रुपये से कम के हेडफोन दिखाओ','लैपटॉप की तुलना करो','स्मार्टवॉच पर ऑफर दिखाओ','हेडफोन कार्ट में जोड़ो'],
 'te-IN':['2000 రూపాయల లోపు హెడ్‌ఫోన్స్ చూపించు','ల్యాప్‌టాప్‌లను పోల్చు','వాచ్ ఆఫర్లు చూపించు','హెడ్‌ఫోన్స్ కార్ట్‌లో చేర్చు'],
 'ta-IN':['2000 ரூபாய்க்குள் ஹெட்போன் காட்டு','லேப்டாப் ஒப்பிடு','கடிகாரம் சலுகைகள் காட்டு','ஹெட்போன் கார்டில் சேர்'],
 'mr-IN':['2000 रुपयांच्या आत हेडफोन्स दाखवा','लॅपटॉप तुलना करा','घड्याळ ऑफर दाखवा','हेडफोन्स कार्टमध्ये जोडा'],
 'kn-IN':['2000 ರೂಪಾಯಿಗಿಂತ ಕಡಿಮೆ ಹೆಡ್‌ಫೋನ್ ತೋರಿಸಿ','ಲ್ಯಾಪ್‌ಟಾಪ್ ಹೋಲಿಸಿ','ವಾಚ್ ಆಫರ್ ತೋರಿಸಿ','ಹೆಡ್‌ಫೋನ್ ಕಾರ್ಟ್‌ಗೆ ಸೇರಿಸಿ'],
 'ml-IN':['2000 രൂപയ്ക്കുള്ളിൽ ഹെഡ്ഫോൺ കാണിക്കൂ','ലാപ്ടോപ്പ് താരതമ്യം ചെയ്യൂ','വാച്ച് ഓഫറുകൾ കാണിക്കൂ','ഹെഡ്ഫോൺ കാർട്ടിൽ ചേർക്കൂ'],
 'bn-IN':['2000 টাকার মধ্যে হেডফোন দেখাও','ল্যাপটপ তুলনা করো','ঘড়ির অফার দেখাও','হেডফোন কার্টে যোগ করো']
};
let currentLanguage='en-IN';
function t(key){return (I18N[currentLanguage]||I18N['en-IN'])[key]||I18N['en-IN'][key]||key}
function translateDemoReply(data){
 if(data.mode==='cart')return t('cart')+': '+data.cart_count+'. '+(data.products&&data.products[0]?data.products[0].name:'');
 if(!data.products||!data.products.length)return t('noProducts');
 return t('results')+': '+data.products[0].name+' — '+money(data.products[0].price);
}
const SEARCH_COPY={
'en-IN':['Search products, e.g. headphones under 2000','Search','Type a product or budget here, or shop using your voice.','Search products'],
'hi-IN':['उत्पाद खोजें, जैसे 2000 से कम हेडफोन','खोजें','उत्पाद या बजट लिखें, या बोलकर खरीदारी करें।','उत्पाद खोजें'],
'te-IN':['ఉత్పత్తులు వెతకండి, ఉదా. 2000 లోపు హెడ్‌ఫోన్స్','వెతకండి','ఉత్పత్తి పేరు లేదా బడ్జెట్ టైప్ చేయండి, లేదా మాట్లాడండి.','ఉత్పత్తులు వెతకండి'],
'ta-IN':['பொருட்களைத் தேடுங்கள், எ.கா. 2000க்குள் ஹெட்போன்','தேடு','பொருள் அல்லது பட்ஜெட்டை உள்ளிடுங்கள், அல்லது பேசுங்கள்.','பொருட்களைத் தேடு'],
'mr-IN':['उत्पादने शोधा, उदा. 2000 खाली हेडफोन','शोधा','उत्पादन किंवा बजेट टाइप करा, किंवा बोला.','उत्पादने शोधा'],
'kn-IN':['ಉತ್ಪನ್ನಗಳನ್ನು ಹುಡುಕಿ, ಉದಾ. 2000 ಒಳಗೆ ಹೆಡ್‌ಫೋನ್','ಹುಡುಕಿ','ಉತ್ಪನ್ನ ಅಥವಾ ಬಜೆಟ್ ಟೈಪ್ ಮಾಡಿ, ಅಥವಾ ಮಾತನಾಡಿ.','ಉತ್ಪನ್ನಗಳನ್ನು ಹುಡುಕಿ'],
'ml-IN':['ഉൽപ്പന്നങ്ങൾ തിരയൂ, ഉദാ. 2000-ന് താഴെ ഹെഡ്ഫോൺ','തിരയൂ','ഉൽപ്പന്നമോ ബജറ്റോ ടൈപ്പ് ചെയ്യൂ, അല്ലെങ്കിൽ സംസാരിക്കൂ.','ഉൽപ്പന്നങ്ങൾ തിരയൂ'],
'bn-IN':['পণ্য খুঁজুন, যেমন ২০০০ টাকার মধ্যে হেডফোন','খুঁজুন','পণ্য বা বাজেট লিখুন, অথবা কথা বলুন।','পণ্য খুঁজুন']};
function searchProducts(event){event.preventDefault();const query=document.getElementById('productSearchInput').value.trim();if(!query)return;runCommand(query);document.getElementById('resultsTitle').scrollIntoView({behavior:'smooth',block:'center'});}
function changeLanguage(lang){
 if(!I18N[lang])lang='en-IN';currentLanguage=lang;document.documentElement.lang=lang.split('-')[0];
 const ids={langLabel:'selectLanguage',navVoice:'voice',navReco:'recommendations',navCart:'cart',heroStart:'heroStart',heroAccent:'heroAccent',heroDescription:'heroDescription',listenText:'start',commandsTitle:'commands',resultsTitle:'results',recoTitle:'smartReco',howTitle:'how',picksText:'picks',compareTitle:'compareTwo'};
 for(const [id,key] of Object.entries(ids)){const el=document.getElementById(id);if(el)el.textContent=t(key)}
 const titles=['search','compare','deals','voiceCart'];titles.forEach((key,i)=>{const el=document.getElementById('cmdTitle'+i);if(el)el.textContent=t(key)});
 document.querySelectorAll('.command').forEach((el,i)=>{el.onclick=()=>runCommand(DEMOS[currentLanguage][i]); const nodes=el.childNodes;for(let j=nodes.length-1;j>=0;j--){if(nodes[j].nodeType===3)nodes[j].remove()}el.append(document.createTextNode('“'+DEMOS[currentLanguage][i]+'”'))});
 const sc=SEARCH_COPY[lang]||SEARCH_COPY['en-IN'];document.getElementById('productSearchInput').placeholder=sc[0];document.getElementById('productSearchButton').textContent=sc[1];document.getElementById('searchHelper').textContent=sc[2];document.getElementById('productSearchLabel').textContent=sc[3];
 document.getElementById('langSelect').value=lang;document.getElementById('micStatus').textContent=t('ready');document.getElementById('reply').textContent=t('welcome');
 document.getElementById('heard').textContent='“'+DEMOS[currentLanguage][0]+'”';document.getElementById('queryLabel').textContent='Demo catalog';
 document.querySelector('label[for="category"]').textContent=t('category');document.querySelector('label[for="budget"]').textContent=t('budget');document.querySelector('label[for="priority"]').textContent=t('priority');
 showProducts(window.lastProducts||[]);
}

const money=x=>'₹'+Number(x).toLocaleString('en-IN');
const fmt=p=>`<article class="product"><div class="picture">${p.emoji}</div><div class="info"><strong>${p.name}</strong><div class="price">${money(p.price)} <s>${money(p.original)}</s></div><div class="muted">⭐ ${p.rating} · ${p.category}</div><button onclick="runCommand('Add ${p.name.replace(/'/g,'')} to cart')">${t("addByVoice")}</button></div></article>`;
function showProducts(arr){window.lastProducts=arr;document.getElementById('products').innerHTML=arr.length?arr.map(fmt).join(''):'<p>'+t('noProducts')+'</p>'}
function say(text){if('speechSynthesis' in window){speechSynthesis.cancel();let u=new SpeechSynthesisUtterance(text);u.lang=currentLanguage;u.rate=1;speechSynthesis.speak(u)}}
async function runCommand(cmd){document.getElementById('heard').textContent='“'+cmd+'”';document.getElementById('queryLabel').textContent=cmd;document.getElementById('micStatus').textContent=t('processing');try{let res=await fetch('/api/voice',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({command:cmd})});if(!res.ok)throw new Error('Server returned '+res.status);let data=await res.json();document.getElementById('reply').textContent='🤖 '+(currentLanguage==='en-IN'?data.reply:translateDemoReply(data));document.getElementById('cartCount').textContent=data.cart_count;showProducts(data.products||[]);document.getElementById('micStatus').textContent=t('nextReady');say(currentLanguage==='en-IN'?data.reply:translateDemoReply(data))}catch(err){document.getElementById('reply').textContent='Could not reach the Flask backend. Check that Python app.py is running. '+err.message;document.getElementById('micStatus').textContent='⚠️ Connection failed'}}
function listen(){const R=window.SpeechRecognition||window.webkitSpeechRecognition;if(!R){document.getElementById('reply').textContent='This browser does not support speech recognition. Try Google Chrome or Microsoft Edge, or use a sample command above.';return}const recognition=new R();recognition.lang=currentLanguage;recognition.interimResults=false;recognition.maxAlternatives=1;recognition.onstart=()=>{document.getElementById('micStatus').textContent='🎙️ Listening...';document.getElementById('listenBtn').textContent='🔴 Listening...'};recognition.onresult=(e)=>runCommand(e.results[0][0].transcript);recognition.onerror=(e)=>{document.getElementById('reply').textContent='Microphone error: '+e.error+'. Check browser microphone permission.';document.getElementById('micStatus').textContent='⚠️ Microphone unavailable'};recognition.onend=()=>{document.getElementById('listenBtn').textContent=t('start');if(document.getElementById('micStatus').textContent.includes('Listening'))document.getElementById('micStatus').textContent='🎙️ Ready to listen'};recognition.start()}
const selectedComparison=new Set();
async function loadRecommendations(){
 const container=document.getElementById('reco-products'),status=document.getElementById('reco-status');
 const params=new URLSearchParams({category:document.getElementById('category').value,priority:document.getElementById('priority').value});
 const budget=document.getElementById('budget').value.trim();if(budget)params.set('budget',budget);
 status.textContent='Finding your best matches...';
 try{const res=await fetch('/api/recommendations?'+params.toString());const data=await res.json();if(!res.ok)throw new Error(data.error||'Request failed');
 status.textContent=data.total?`Showing ${data.products.length} of ${data.total} ranked demo products. No live prices or external AI service used.`:'No demo products match these filters. Try a higher budget or another category.';
 container.innerHTML=data.products.map(p=>`<article class="reco-card"><div class="reco-icon">${p.emoji}</div><h3>${p.name}</h3><div class="price">${money(p.price)} <s>${money(p.original)}</s></div><div class="muted">⭐ ${p.rating} · Save ${p.discount_percent}%</div><p class="why">✨ ${p.why_recommended}</p><button onclick="toggleComparison(${p.id},this)">${selectedComparison.has(p.id)?'✓ Selected':'⚖️ Compare'}</button></article>`).join('');
 }catch(e){status.textContent='Recommendation error: '+e.message;container.innerHTML='';}
}
function toggleComparison(id){if(selectedComparison.has(id)){selectedComparison.delete(id)}else if(selectedComparison.size<2){selectedComparison.add(id)}else{alert('Select only two products; deselect one first.');return}document.getElementById('compareBtn').disabled=selectedComparison.size!==2;document.getElementById('compareBtn').textContent=`Compare selected (${selectedComparison.size}/2)`;document.querySelectorAll('.reco-card button').forEach(b=>{const found=b.getAttribute('onclick').match(/\d+/);if(found){const n=Number(found[0]);b.textContent=selectedComparison.has(n)?'✓ Selected':'⚖️ Compare'}})}
async function runCompare(){try{const res=await fetch('/api/compare',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({ids:[...selectedComparison]})});const data=await res.json();if(!res.ok)throw Error(data.error||'Comparison failed');document.getElementById('compareResults').innerHTML=`<div class="compare-grid">${data.products.map(p=>`<div class="compare-cell"><strong>${p.emoji} ${p.name}</strong><p>Price: ${money(p.price)}<br>Demo rating: ⭐ ${p.rating}/5<br>Discount: ${p.discount_percent}%<br>Save: ${money(p.savings)}</p></div>`).join('')}</div><p>${data.summary}</p>`}catch(e){document.getElementById('compareResults').textContent=e.message}}
changeLanguage('en-IN');
loadRecommendations();
fetch('/api/products').then(r=>r.json()).then(p=>showProducts(p.slice(0,4))).catch(()=>{});
</script></body></html>'''

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5000, debug=True)
