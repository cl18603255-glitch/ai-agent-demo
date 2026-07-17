"""MailPilot Pro v2.0"""
import os, csv, json
from datetime import datetime
from pathlib import Path
from flask import Flask, request, render_template, jsonify
from openai import OpenAI
from dotenv import load_dotenv
load_dotenv()
app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024
API_KEY = os.getenv("OPENAI_API_KEY") or os.getenv("DEEPSEEK_API_KEY")
BASE_URL = os.getenv("OPENAI_BASE_URL") or os.getenv("DEEPSEEK_BASE_URL") or "https://api.openai.com/v1"
MODEL = os.getenv("AI_MODEL", "gpt-4o-mini")
client = OpenAI(api_key=API_KEY, base_url=BASE_URL)
PRODUCT_DB_PATH = Path(__file__).parent / "products.csv"

def load_products():
    products = []
    if PRODUCT_DB_PATH.exists():
        with open(PRODUCT_DB_PATH, "r", encoding="utf-8-sig") as f:
            for row in csv.DictReader(f):
                products.append(row)
    return products

def call_llm(prompt, temperature=0.7, max_tokens=2000, timeout=90):
    try:
        r = client.chat.completions.create(model=MODEL, messages=[{"role":"user","content":prompt}], temperature=temperature, max_tokens=max_tokens, timeout=timeout)
        return r.choices[0].message.content
    except Exception as e:
        err = str(e).lower()
        if "frequency" in err or "rate" in err: return "AI服务繁忙，请稍后重试。"
        elif "quota" in err or "insufficient" in err: return "AI服务额度不足。"
        return "AI生成失败: " + str(e)[:100]

def parse_json_resp(text):
    try:
        text = text.strip()
        if "`" in text:
            text = text.split("`")[1]
            if text.startswith("json"): text = text[4:]
        if text.endswith("`"): text = text[:-3]
        return json.loads(text.strip())
    except: return None

def analyze_inquiry(text):
    jfmt = '{"customer_intent":"INTENT","priority":"HIGH/MED/LOW","key_requirements":["REQ1"],"missing_info":["INFO1"],"strategy":"STRATEGY"}'
    prompt = "分析询盘，返回JSON：\n询盘：" + text + "\n" + jfmt
    result = call_llm(prompt, temperature=0.3, max_tokens=500, timeout=60)
    parsed = parse_json_resp(result)
    if parsed: return parsed
    return {"customer_intent":"未知","priority":"中","key_requirements":[],"missing_info":[],"strategy":""}

def match_products(text, products):
    if not products: return {"matched_products":[],"total_matched":0}
    plist = "\n".join(["- "+p.get("name","")+" | "+p.get("category","") for p in products[:20]])
    jfmt = '{"matched_products":[{"name":"","match_reason":"","highlight":""}]}'
    prompt = "推荐匹配产品。询盘："+text+"\n产品库："+plist+"\n返回JSON："+jfmt
    result = call_llm(prompt, temperature=0.3, max_tokens=500, timeout=60)
    parsed = parse_json_resp(result)
    if parsed: return parsed
    return {"matched_products":[],"total_matched":0}

def gen_emails(analysis, matched, style="formal"):
    smap = {"formal":"正式专业","friendly":"友好亲切","concise":"简洁直接"}
    sdesc = smap.get(style, smap["formal"])
    intent = analysis.get("customer_intent","")
    reqs = ",".join(analysis.get("key_requirements",[]))
    prompt = "生成外贸邮件方案。\n客户分析：意图="+intent+", 需求="+reqs+"\n风格："+sdesc+"\n\n## 1.英文邮件\n## 2.中文版本\n## 3.WhatsApp话术\n## 4.销售建议\n## 5.Q&A"
    return call_llm(prompt, temperature=0.7, max_tokens=2500, timeout=90)

def gen_quote(text, products):
    plist = "\n".join(["- "+p.get("name","")+" | "+p.get("price","面议") for p in products[:15]])
    prompt = "生成专业英文报价单。询盘："+text+"\n产品参考："+(plist if plist else "")+"\n包含：编号、日期、产品表、价格条款、付款方式、交货期、有效期。附中文说明。"
    return call_llm(prompt, temperature=0.5, max_tokens=1500, timeout=90)

@app.route("/health")
def health():
    return jsonify({"status":"ok","timestamp":datetime.now().isoformat(),"model":MODEL}), 200

@app.route("/api/analyze", methods=["POST"])
def api_analyze():
    d = request.get_json(silent=True)
    if not d or not d.get("inquiry"): return jsonify({"error":"请输入询盘内容"}), 400
    return jsonify(analyze_inquiry(d["inquiry"]))

@app.route("/api/match-products", methods=["POST"])
def api_match():
    d = request.get_json(silent=True)
    return jsonify(match_products(d.get("inquiry","") if d else "", load_products()))

@app.route("/api/generate", methods=["POST"])
def api_generate():
    d = request.get_json(silent=True)
    inquiry = d.get("inquiry","") if d else ""
    style = d.get("style","formal") if d else "formal"
    if not inquiry: return jsonify({"error":"请输入询盘内容"}), 400
    analysis = analyze_inquiry(inquiry)
    matched = match_products(inquiry, load_products())
    emails = gen_emails(analysis, matched, style)
    return jsonify({"analysis":analysis,"matched_products":matched,"emails":emails})

@app.route("/api/quotation", methods=["POST"])
def api_quote():
    d = request.get_json(silent=True)
    inquiry = d.get("inquiry","") if d else ""
    if not inquiry: return jsonify({"error":"请输入询盘内容"}), 400
    return jsonify({"quotation": gen_quote(inquiry, load_products())})

@app.route("/api/products", methods=["GET"])
def api_products():
    prods = load_products()
    return jsonify({"products":prods,"count":len(prods)})

@app.route("/api/products", methods=["POST"])
def api_add_product():
    d = request.get_json(silent=True)
    if not d: return jsonify({"error":"无效请求"}), 400
    for field in ["name","category","price"]:
        if field not in d: return jsonify({"error":"缺少: "+field}), 400
    products = load_products()
    exists = False
    for p in products:
        if p.get("name") == d["name"]: products[products.index(p)] = d; exists = True; break
    if not exists: products.append(d)
    with open(PRODUCT_DB_PATH, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["name","category","price","moq","lead_time","features","hs_code"])
        w.writeheader(); w.writerows(products)
    return jsonify({"message":"产品已保存","products":products})

@app.route("/", methods=["GET","POST"])
def home():
    result, error, product, requirement, style = "", "", "", "", "formal"
    if request.method == "POST":
        product = (request.form.get("product") or "").strip()
        requirement = (request.form.get("requirement") or "").strip()
        style = request.form.get("style", "formal")
        if not product or not requirement:
            error = "请先补充产品和客户需求。"
        else:
            inquiry = "产品: "+product+"\n客户需求: "+requirement
            analysis = analyze_inquiry(inquiry)
            matched = match_products(inquiry, load_products())
            result = gen_emails(analysis, matched, style)
    return render_template("index.html", result=result, error=error, product=product, requirement=requirement, style=style, products=load_products())

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    print("\nMailPilot Pro v2.0 | Model: "+MODEL+" | Port: "+str(port)+"\n")
    app.run(host="0.0.0.0", port=port, debug=False)
